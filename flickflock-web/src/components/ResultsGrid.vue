<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useFlockStore } from '../stores/flock'
import { useDetailModals } from '../composables/useDetailModals'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const store = useFlockStore()
const { openMediaRequest, openPersonRequest, openPerson, openMedia } = useDetailModals()

// Modal state
const showModal = ref(false)
const modalLoading = ref(false)
const mediaDetail = ref(null)

function posterUrl(item, size = 'w300') {
  return item.poster_path
    ? `https://image.tmdb.org/t/p/${size}${item.poster_path}`
    : null
}

function profileUrl(person) {
  return person.profile_path
    ? `https://image.tmdb.org/t/p/w92${person.profile_path}`
    : null
}

function releaseYear(item) {
  const date = item.release_date || item.first_air_date
  return date ? date.slice(0, 4) : ''
}

function tmdbUrl(item) {
  const type = item.media_type || 'movie'
  return `https://www.themoviedb.org/${type}/${item.id}`
}

async function openMediaModal(work, event) {
  if (event) event.preventDefault()
  mediaDetail.value = null
  showModal.value = true
  modalLoading.value = true

  try {
    const type = work.media_type || 'movie'
    const res = await axios.get(`${BASE_URL}/${type}/${work.id}/details`)
    mediaDetail.value = res.data
  } catch (err) {
    console.error('Failed to fetch media details:', err)
  } finally {
    modalLoading.value = false
  }
}

const runtime = computed(() => {
  if (!mediaDetail.value) return ''
  const mins = mediaDetail.value.runtime || mediaDetail.value.episode_run_time?.[0]
  if (!mins) return ''
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
})

function addPersonToFlock(person) {
  store.addSearchResult({
    id: person.id,
    name: person.name,
    media_type: 'person',
    profile_path: person.profile_path,
    known_for_department: person.known_for_department,
  })
}

function openPersonDetail(person) {
  showModal.value = false
  openPerson(person)
}

function isPersonSelected(person) {
  return store.selection.some(s => s.id === person.id)
}

// Cross-modal navigation: another component requests opening a media modal
watch(openMediaRequest, (req) => {
  if (req) openMediaModal(req)
})

// Close this modal when person modal is opening
watch(openPersonRequest, () => {
  showModal.value = false
})
</script>

<template>
  <div class="results-container">
    <!-- Filters -->
    <div class="filters-row mb-4">
      <v-btn-toggle
        v-model="store.mediaTypeFilter"
        mandatory
        density="compact"
        variant="outlined"
        divided
        color="primary"
      >
        <v-btn value="all" size="small">All</v-btn>
        <v-btn value="movie" size="small">Movies</v-btn>
        <v-btn value="tv" size="small">TV</v-btn>
      </v-btn-toggle>

      <v-select
        v-model="store.sortBy"
        :items="[
          { title: 'Relevance', value: 'relevance' },
          { title: 'Popularity', value: 'popularity' },
          { title: 'Release date', value: 'date' },
        ]"
        variant="outlined"
        density="compact"
        hide-details
        class="sort-select"
      />
    </div>

    <!-- Empty state -->
    <div v-if="store.filteredFlockWorks.length === 0 && !store.flockWorksLoading" class="text-center pa-6">
      <v-icon icon="mdi-movie-search-outline" size="48" color="info" class="mb-3 d-block mx-auto" />
      <p class="text-body-2 text-medium-emphasis">
        Recommendations will appear here once your flock has enough connections.
      </p>
    </div>

    <!-- Results grid -->
    <div class="results-grid" v-else>
      <a
        v-for="work in store.filteredFlockWorks"
        :key="work.id"
        :href="tmdbUrl(work)"
        target="_blank"
        rel="noopener"
        class="result-card text-decoration-none"
        @click="openMediaModal(work, $event)"
      >
        <div class="poster-wrapper">
          <v-img
            v-if="posterUrl(work)"
            :src="posterUrl(work)"
            :alt="work.title"
            cover
            class="poster-img"
            :aspect-ratio="2/3"
          />
          <div v-else class="poster-placeholder d-flex align-center justify-center">
            <v-icon icon="mdi-movie-outline" size="40" color="primary" />
          </div>
          <v-chip
            class="score-badge"
            size="x-small"
            variant="flat"
            :color="work.count >= 5 ? 'secondary' : work.count >= 2 ? 'primary' : 'surface'"
          >
            {{ work.count }}
          </v-chip>
          <v-chip
            class="type-badge"
            size="x-small"
            variant="flat"
            color="background"
          >
            {{ work.media_type === 'tv' ? 'TV' : 'Film' }}
          </v-chip>
        </div>
        <div class="card-info pa-2">
          <span class="text-caption font-weight-medium card-title">{{ work.title }}</span>
          <span class="text-caption text-medium-emphasis">{{ releaseYear(work) }}</span>
        </div>
      </a>
    </div>

    <!-- Media detail modal -->
    <v-dialog v-model="showModal" max-width="520" scrollable>
      <v-card color="surface">
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          class="modal-close-btn"
          @click="showModal = false"
        />

        <v-card-text class="pa-0">
          <div v-if="modalLoading" class="text-center py-12">
            <v-progress-circular color="primary" indeterminate />
          </div>

          <template v-else-if="mediaDetail">
            <!-- Backdrop / poster header -->
            <div class="modal-header" :style="mediaDetail.backdrop_path ? { backgroundImage: `linear-gradient(to bottom, transparent 30%, rgb(var(--v-theme-surface)) 100%), url(https://image.tmdb.org/t/p/w780${mediaDetail.backdrop_path})` } : {}">
              <div class="d-flex pa-4 pt-12 ga-4" style="position: relative;">
                <v-img
                  v-if="posterUrl(mediaDetail, 'w185')"
                  :src="posterUrl(mediaDetail, 'w185')"
                  :aspect-ratio="2/3"
                  cover
                  class="rounded-lg flex-shrink-0"
                  width="100"
                />
                <div>
                  <h2 class="text-h6 mb-1">{{ mediaDetail.title || mediaDetail.name }}</h2>
                  <div class="d-flex flex-wrap ga-2 align-center mb-2">
                    <span class="text-caption text-medium-emphasis">{{ releaseYear(mediaDetail) }}</span>
                    <span v-if="runtime" class="text-caption text-medium-emphasis">{{ runtime }}</span>
                    <v-chip v-if="mediaDetail.vote_average" size="x-small" variant="tonal" color="primary">
                      {{ mediaDetail.vote_average.toFixed(1) }}
                    </v-chip>
                  </div>
                  <div v-if="mediaDetail.genres" class="d-flex flex-wrap ga-1">
                    <v-chip v-for="g in mediaDetail.genres.slice(0, 3)" :key="g.id" size="x-small" variant="outlined">
                      {{ g.name }}
                    </v-chip>
                  </div>
                </div>
              </div>
            </div>

            <div class="px-4 pb-4">
              <p v-if="mediaDetail.overview" class="text-body-2 mb-4" style="line-height: 1.5;">
                {{ mediaDetail.overview }}
              </p>

              <!-- Crew -->
              <div v-if="mediaDetail.top_crew?.length" class="mb-3">
                <div v-for="person in mediaDetail.top_crew" :key="`crew-${person.id}-${person.job}`" class="text-caption">
                  <span class="text-medium-emphasis">{{ person.job }}:</span> {{ person.name }}
                </div>
              </div>

              <!-- Cast -->
              <div v-if="mediaDetail.top_cast?.length" class="mb-2">
                <p class="text-overline text-medium-emphasis mb-2">Cast</p>
                <div class="cast-row">
                  <div
                    v-for="person in mediaDetail.top_cast"
                    :key="person.id"
                    class="cast-item"
                    @click="openPersonDetail(person)"
                  >
                    <v-avatar :size="40" color="background">
                      <v-img v-if="profileUrl(person)" :src="profileUrl(person)" cover />
                      <v-icon v-else icon="mdi-account" size="20" />
                    </v-avatar>
                    <div class="cast-info">
                      <span class="text-caption font-weight-medium">{{ person.name }}</span>
                      <span class="text-caption text-medium-emphasis">{{ person.character }}</span>
                    </div>
                    <v-spacer />
                    <v-btn
                      v-if="!isPersonSelected(person)"
                      icon="mdi-plus"
                      size="x-small"
                      variant="tonal"
                      color="primary"
                      @click.stop="addPersonToFlock(person)"
                    />
                    <v-icon
                      v-else
                      icon="mdi-check-circle"
                      size="20"
                      color="info"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
        </v-card-text>

        <v-card-actions class="pa-4 pt-0">
          <v-btn
            v-if="mediaDetail"
            variant="text"
            :href="tmdbUrl(mediaDetail)"
            target="_blank"
            size="small"
          >
            TMDB
            <v-icon end icon="mdi-open-in-new" size="14" />
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="showModal = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.filters-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.sort-select {
  max-width: 160px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
}

.result-card {
  border-radius: 8px;
  overflow: hidden;
  background: rgba(43, 33, 49, 0.6);
  transition: transform 0.2s, box-shadow 0.2s;
  color: inherit;
}

.result-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.poster-wrapper {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
}

.poster-img {
  width: 100%;
  height: 100%;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(21, 16, 24, 0.8);
}

.score-badge {
  position: absolute;
  top: 6px;
  right: 6px;
}

.type-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  opacity: 0.85;
}

.card-info {
  display: flex;
  flex-direction: column;
}

.card-title {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.modal-close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
}

.modal-header {
  background-size: cover;
  background-position: center top;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.cast-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.cast-item:hover {
  background-color: rgba(228, 163, 58, 0.1);
}

.cast-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.cast-info span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
