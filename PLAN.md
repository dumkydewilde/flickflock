# FlickFlock Revival Plan

## Current State Assessment

FlickFlock is a film/series discovery app that builds a "flock" of people based on
user-selected movies, shows, and actors, then recommends content those people worked on
together. The core idea is sound — it's a people-network-based recommender — but both the
scoring algorithm and the interface need significant work.

### Existing Bugs & Issues

1. **Caching is broken**: `tmdb.py:37` uses `self.cache.set[request_id]` (subscript on a
   method) instead of `self.cache.set(request_id, ...)`. Cached writes silently fail, so
   every TMDB request hits the API every time.
2. **Test is broken**: `test_flock.py:54` asserts `flock.name` but the attribute is
   `flock.flock_name`.
3. **`/api/flock/create` is a stub**: Returns `None` with no response body.
4. **`/api/flock/<id>/details` has dead logic**: Both branches of the `if/else` on line 81-83
   do the same thing. Also references `person_details_func` which makes N+1 API calls.
5. **`get_person_relations` is an API bomb**: For a person with 50 credits, it makes 50
   additional API calls (one per credit to get *all* cast/crew of each). This is extremely
   slow and can hit TMDB rate limits.
6. **`is not` vs `!=`**: `main.py:65` uses `is not` for integer comparison instead of `!=`.
7. **No cache TTL**: Cached data never expires — stale data persists forever.
8. **API key printed to stdout**: `tmdb.py:44` prints the API key during authentication.

---

## Phase 1: Fix Bugs & Stabilize (Foundation)

Before improving anything, make the existing system actually work correctly.

### 1.1 Fix the caching bug in `tmdb.py`
- Change `self.cache.set[request_id] = {...}` to `self.cache.set(request_id, {...})`.
- Add a TTL (e.g., 7 days) to cached requests so data doesn't go stale forever.

### 1.2 Fix broken test
- Change `flock.name` to `flock.flock_name` in `test_flock.py`.

### 1.3 Fix `is not` → `!=` in `main.py:65`
- Integer identity comparison is unreliable; use value equality.

### 1.4 Remove API key logging
- Delete `print(self.api_key)` from `tmdb.py:44`.

### 1.5 Fix `/api/flock/<id>/details` dead branch
- Remove the redundant if/else that does the same thing in both branches.

### 1.6 Remove or implement `/api/flock/create` stub
- Either implement it or remove the dead endpoint.

---

## Phase 2: Improve the Scoring Algorithm

The current algorithm is a plain frequency counter: each person's "score" is just how many
times their ID appears across all flock entries. This has several problems:

**Current algorithm problems:**
- A gaffer who worked on 1 selected movie counts the same as the lead actor
- People who work on everything (prolific producers) float to the top without being
  meaningfully connected to the user's taste
- Adding a person directly (e.g., "Andy Samberg") triggers `get_person_relations` which
  fetches every cast/crew member of every project they've been in — extremely slow and noisy
- No distinction between a director (high creative influence) and a caterer
- The multiplicative boost in `get_flock_works` (works × person_count) over-amplifies
  already-popular people

### 2.1 Department-weighted scoring

Not all credits are equal. A director or lead actor shapes a film's identity far more than
a grip or production assistant.

```python
DEPARTMENT_WEIGHTS = {
    "Directing": 5.0,
    "Writing": 4.0,
    "Acting": 3.0,        # further weighted by cast order below
    "Production": 2.0,
    "Sound": 1.5,         # composers matter
    "Camera": 1.0,
    "Editing": 1.0,
    "Art": 0.5,
    "Crew": 0.3,
    "default": 0.5
}
```

For actors specifically, weight by `cast_order` (TMDB provides this): lead actors
(order 0-2) get full weight, supporting cast get diminishing weight.

### 2.2 TF-IDF inspired scoring

The current system rewards people who appear frequently. But someone who appears in
*everything* (e.g., a prolific producer with 500 credits) isn't a meaningful signal.

Apply inverse-document-frequency logic:
- **TF** (term frequency) = how many of the user's selections this person appears in
- **IDF** (inverse document frequency) = log(total_credits / person_total_credits)
- People with fewer total credits who still appear in multiple selections are *more*
  meaningful signals

### 2.3 Two-tier person expansion (direct vs. transitive)

Currently `get_person_relations` fetches the full cast/crew of every project a person has
been in. For someone like Andy Samberg (100+ credits), that's 100+ API calls returning
thousands of people. The fix isn't to blindly limit — it depends on *how* the person entered
the flock.

**Direct selections (user explicitly adds a person like "Andy Samberg"):**
- Fetch their **full filmography** — this is the point. The user *wants* to discover the
  long tail: the indie film, the voice role, the one-off directing credit.
- All of their works feed into the results, including obscure ones. This is where FlickFlock
  surfaces hidden gems.
- However, when expanding *outward* from those works (finding collaborators), apply the
  filtered approach below — we want Andy's deep cuts, but we don't need every grip from
  every one of his 100 projects.

**Transitive connections (people discovered via a selected movie/show):**
- These are indirect — the user didn't ask for them specifically.
- Limit expansion to top N most popular/relevant works (e.g., top 10 by TMDB popularity).
- Only include cast with `cast_order < 15` and key crew departments (Directing, Writing,
  Production, Sound/composer).
- Cache aggressively (these results are stable).

This means: "I like Andy Samberg" → you see *everything* Andy has done, including the weird
stuff → but the flock of *collaborators* is built smartly from his key projects, not by
crawling every person on every set he ever walked onto.

### 2.4 Normalize per-selection contribution

Currently, a movie with 200 crew members contributes 200 entries while a movie with 20
contributes 20. The larger movie dominates the flock disproportionately.

Normalize: each selection contributes a fixed "budget" of score (e.g., 1.0), distributed
among its people weighted by department/role.

### 2.5 Score works more intelligently

Currently `get_flock_works` multiplies a person's works by their flock count, which
double-amplifies popular people. Instead:

- Score each work based on *how many distinct flock members* worked on it (not weighted by
  flock count — that's already baked into which people are in the flock)
- Boost works where multiple *top flock members* collaborated (the "reunion" signal)
- **Long-tail surfacing for direct selections**: When someone is directly selected, their
  full filmography enters the results pool. A niche Andy Samberg indie film might only have
  1 flock member (Andy himself), but it should still appear because the user explicitly
  expressed interest in Andy. Give directly-selected people a baseline "trust" score so
  their obscure works aren't drowned out by blockbusters that happen to have 10 flock
  members.
- Penalize works the user has already selected (they already know about these)
- Optionally filter by genre affinity derived from the user's selections

---

## Phase 3: Interface Improvements

The current UI is functional but feels like a prototype. Three columns of text-heavy lists
don't invite exploration.

### 3.1 Visual design overhaul

- **Card-based layout for results**: Replace the text list with poster cards showing the
  movie/show artwork prominently. Film discovery is visual — posters matter.
- **People as chips/avatars**: In the flock panel, show people as circular avatar chips with
  their name and a relevance indicator, rather than a plain list.
- **Better color hierarchy**: The current gold/dark-purple scheme is decent but the three
  columns blend together. Give each panel a clearer visual identity.

### 3.2 Interaction improvements

- **Remove items from selection**: Currently there's no way to remove a selection once added.
  Add a remove/X button on each selection item.
- **Clickable flock members**: Clicking a flock member should show their filmography and
  let you add them as a direct selection.
- **Filter results**: Add filter chips for genre (Comedy, Drama, Sci-Fi, etc.) and media type
  (Movies only, TV only, Both).
- **Sort options**: Let users sort results by relevance score, release date, or popularity.

### 3.3 Onboarding & empty states

- Replace the plain text alert with an engaging empty state: show example selections
  ("Try: 30 Rock + Andy Samberg → ...") that users can click to auto-populate.
- Add a brief explainer of the concept: "FlickFlock finds the people behind your favourite
  films and shows, then discovers what else they've made together."

### 3.4 URL sharing & persistence

- The flock ID is already in the URL params. Make sharing explicit: add a "Share this flock"
  button that copies the URL.
- Show a flock name that users can edit.

### 3.5 Mobile experience

- The bottom nav exists but the stacked single-column layout isn't great. Consider a
  step-by-step flow on mobile: Search → Review Flock → Browse Results.
- Swipeable cards for results on mobile.

### 3.6 Technical frontend improvements

- **Migrate to Composition API**: The app mixes `<script setup>` and Options API. Standardize
  on Composition API with `<script setup>`.
- **State management**: Move shared state (selection, flock, flockWorks) into a Pinia store
  instead of managing it all in App.vue.
- **Update dependencies**: Vue 3.2 → 3.4+, Vuetify 3.0 → 3.4+, Vite 3 → 5.

---

## Phase 4: Backend Robustness

### 4.1 Rate limiting & error handling
- Add TMDB API rate limiting (TMDB allows 40 requests/10 seconds)
- Return proper HTTP error codes and messages instead of bare strings
- Add request validation

### 4.2 Background processing for flock computation
- Computing a flock with person relations is slow (many API calls). Return a flock ID
  immediately and compute in the background, letting the frontend poll or use SSE.

### 4.3 Smarter caching
- Cache person data and credits separately (credits change rarely)
- Add cache warming for popular entities
- Add cache TTL (7 days for credits, 30 days for person details)

---

## Suggested Implementation Order

| Priority | Task | Impact | Effort |
|----------|------|--------|--------|
| 1 | Phase 1: Bug fixes | High — things are broken | Low |
| 2 | Phase 2.1-2.3: Core scoring improvements | High — directly improves recommendations | Medium |
| 3 | Phase 3.1-3.2: Visual overhaul + interactions | High — makes the app usable and appealing | Medium |
| 4 | Phase 2.4-2.5: Advanced scoring | Medium — refinement | Medium |
| 5 | Phase 3.3-3.4: Onboarding & sharing | Medium — growth/retention | Low |
| 6 | Phase 4: Backend robustness | Medium — reliability | Medium |
| 7 | Phase 3.5-3.6: Mobile + tech debt | Low-Medium — polish | Medium |
