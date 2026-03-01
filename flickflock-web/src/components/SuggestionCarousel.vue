<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDisplay } from 'vuetify'
import axios from 'axios'

const { mdAndUp } = useDisplay()

const BASE_URL = import.meta.env.VITE_API_URL || '/api'
const emit = defineEmits(['select'])

const allSuggestions = [
  // --- Mind-bending & meta ---
  {
    label: 'Charlie Kaufman + Nicolas Cage',
    tagline: 'From the minds behind Adaptation',
    items: [
      { id: 202, name: 'Charlie Kaufman', media_type: 'person', profile_path: '/75aOpLBpvdtQM3BkWGFUvMs6LvH.jpg', known_for_department: 'Writing' },
      { id: 2963, name: 'Nicolas Cage', media_type: 'person', profile_path: '/y1RtezurZYveYkVNRht7CwEgSYY.jpg', known_for_department: 'Acting' },
    ],
  },
  {
    label: 'Eternal Sunshine + Memento',
    tagline: 'Mind-bending masterpieces',
    items: [
      { id: 38, title: 'Eternal Sunshine of the Spotless Mind', media_type: 'movie', poster_path: '/5MwkWH9tYHv3mV9OdYTMR5qreIz.jpg' },
      { id: 77, title: 'Memento', media_type: 'movie', poster_path: '/fKTPH2WvH8nHTXeBYBVhawtRqtR.jpg' },
    ],
  },
  // --- Classic Hollywood ---
  {
    label: 'Sean Connery + Harrison Ford',
    tagline: 'Legends of the silver screen',
    items: [
      { id: 738, name: 'Sean Connery', media_type: 'person', profile_path: '/hbB676mW62gjsh0f51ICYE11niG.jpg', known_for_department: 'Acting' },
      { id: 3, name: 'Harrison Ford', media_type: 'person', profile_path: '/zVnHagUvXkR2StdOtquEwsiwSVt.jpg', known_for_department: 'Acting' },
    ],
  },
  {
    label: 'Casablanca + 12 Angry Men',
    tagline: 'Golden age cinema',
    items: [
      { id: 289, title: 'Casablanca', media_type: 'movie', poster_path: '/lGCEKlJo2CnWydQj7aamY7s1S7Q.jpg' },
      { id: 389, title: '12 Angry Men', media_type: 'movie', poster_path: '/ow3wq89wM8qd5X7hWKxiRfsFf9C.jpg' },
    ],
  },
  // --- Harlan Coben thrillers ---
  {
    label: 'Safe + The Stranger',
    tagline: "Harlan Coben's Netflix universe",
    items: [
      { id: 72792, name: 'Safe', media_type: 'tv', poster_path: '/lrA2SSoWp3zzb0MBdjWKCVN0qEF.jpg' },
      { id: 96608, name: 'The Stranger', media_type: 'tv', poster_path: '/qKtjZ6f8ip6M7pYiDcVs0QXUAly.jpg' },
    ],
  },
  // --- Psychological thriller ---
  {
    label: 'Get Out + Black Swan',
    tagline: 'Psychological thrillers with a twist',
    items: [
      { id: 419430, title: 'Get Out', media_type: 'movie', poster_path: '/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg' },
      { id: 44214, title: 'Black Swan', media_type: 'movie', poster_path: '/viWheBd44bouiLCHgNMvahLThqx.jpg' },
    ],
  },
  // --- Crime ---
  {
    label: 'Fargo + No Country for Old Men',
    tagline: 'Crime in the American heartland',
    items: [
      { id: 60622, name: 'Fargo', media_type: 'tv', poster_path: '/6U9CPeD8obHzweikFhiLhpc7YBT.jpg' },
      { id: 6977, title: 'No Country for Old Men', media_type: 'movie', poster_path: '/6d5XOczc226jECq0LIX0siKtgHR.jpg' },
    ],
  },
  // --- NBC comedy ---
  {
    label: '30 Rock + Andy Samberg',
    tagline: 'Comedy gold from NBC and beyond',
    items: [
      { id: 4608, name: '30 Rock', media_type: 'tv', poster_path: '/eYYQWACx7ttUzRwTNYuo6zveqpE.jpg' },
      { id: 62861, name: 'Andy Samberg', media_type: 'person', profile_path: '/jMXU5oG3i93SH1yhkpbBGskFiJl.jpg', known_for_department: 'Acting' },
    ],
  },
  // --- Nolan sci-fi ---
  {
    label: 'Inception + Interstellar',
    tagline: "Nolan's mind-bending epics",
    items: [
      { id: 27205, title: 'Inception', media_type: 'movie', poster_path: '/ljsZTbVsrQSqZgWeep2B1QiDKuh.jpg' },
      { id: 157336, title: 'Interstellar', media_type: 'movie', poster_path: '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg' },
    ],
  },
  // --- Studio Ghibli / anime ---
  {
    label: 'Spirited Away + Princess Mononoke',
    tagline: "Miyazaki's animated masterpieces",
    items: [
      { id: 129, title: 'Spirited Away', media_type: 'movie', poster_path: '/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg' },
      { id: 128, title: 'Princess Mononoke', media_type: 'movie', poster_path: '/cMYCDADoLKLbB83g4WnJegaZimC.jpg' },
    ],
  },
  // --- Korean cinema ---
  {
    label: 'Parasite + Oldboy',
    tagline: 'Korean cinema at its finest',
    items: [
      { id: 496243, title: 'Parasite', media_type: 'movie', poster_path: '/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg' },
      { id: 670, title: 'Oldboy', media_type: 'movie', poster_path: '/pWDtjs568ZfOTMbURQBYuT4Qxka.jpg' },
    ],
  },
  // --- Mob classics ---
  {
    label: 'The Godfather + Goodfellas',
    tagline: 'The mob movie hall of fame',
    items: [
      { id: 238, title: 'The Godfather', media_type: 'movie', poster_path: '/3bhkrj58Vtu7enYsRolD1fZdja1.jpg' },
      { id: 769, title: 'Goodfellas', media_type: 'movie', poster_path: '/9OkCLM73MIU2CrKZbqiT8Ln1wY2.jpg' },
    ],
  },
  // --- Iconic suspense thrillers ---
  {
    label: 'Alien + The Silence of the Lambs',
    tagline: 'Genre-defining suspense',
    items: [
      { id: 348, title: 'Alien', media_type: 'movie', poster_path: '/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg' },
      { id: 274, title: 'The Silence of the Lambs', media_type: 'movie', poster_path: '/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg' },
    ],
  },
  // --- Prestige TV drama ---
  {
    label: 'Breaking Bad + The Wire',
    tagline: 'Peak prestige television',
    items: [
      { id: 1396, name: 'Breaking Bad', media_type: 'tv', poster_path: '/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg' },
      { id: 1438, name: 'The Wire', media_type: 'tv', poster_path: '/4lbclFySvugI51fwsyxBTOm4DqK.jpg' },
    ],
  },
  // --- Pixar emotional journeys ---
  {
    label: 'Coco + Inside Out',
    tagline: "Pixar's emotional masterpieces",
    items: [
      { id: 354912, title: 'Coco', media_type: 'movie', poster_path: '/6Ryitt95xrO8KXuqRGm1fUuNwqF.jpg' },
      { id: 150540, title: 'Inside Out', media_type: 'movie', poster_path: '/2H1TmgdfNtsKlU9jKdeNyYL5y8T.jpg' },
    ],
  },
  // --- Multiverse action ---
  {
    label: 'Everything Everywhere + The Matrix',
    tagline: 'Reality is what you make it',
    items: [
      { id: 545611, title: 'Everything Everywhere All at Once', media_type: 'movie', poster_path: '/u68AjlvlutfEIcpmbYpKcdi09ut.jpg' },
      { id: 603, title: 'The Matrix', media_type: 'movie', poster_path: '/p96dm7sCMn4VYAStA6siNz30G1r.jpg' },
    ],
  },
  // --- Music and obsession ---
  {
    label: 'La La Land + Whiplash',
    tagline: 'Music, dreams, and obsession',
    items: [
      { id: 313369, title: 'La La Land', media_type: 'movie', poster_path: '/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg' },
      { id: 244786, title: 'Whiplash', media_type: 'movie', poster_path: '/7fn624j5lj3xTme2SgiLCeuedmO.jpg' },
    ],
  },
  // --- Villeneuve sci-fi ---
  {
    label: 'Dune + Blade Runner 2049',
    tagline: "Villeneuve's sci-fi visions",
    items: [
      { id: 438631, title: 'Dune', media_type: 'movie', poster_path: '/d5NXSklXo0qyIYkgV94XAgMIckC.jpg' },
      { id: 335984, title: 'Blade Runner 2049', media_type: 'movie', poster_path: '/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg' },
    ],
  },
  // --- Modern horror ---
  {
    label: 'Hereditary + Midsommar',
    tagline: 'Ari Aster will haunt your dreams',
    items: [
      { id: 493922, title: 'Hereditary', media_type: 'movie', poster_path: '/hjlZSXM86wJrfCv5VKfR5DI2VeU.jpg' },
      { id: 530385, title: 'Midsommar', media_type: 'movie', poster_path: '/7LEI8ulZzO5gy9Ww2NVCrKmHeDZ.jpg' },
    ],
  },
  // --- Surreal mystery TV ---
  {
    label: 'Twin Peaks + Dark',
    tagline: 'Nothing is what it seems',
    items: [
      { id: 1920, name: 'Twin Peaks', media_type: 'tv', poster_path: '/lA9CNSdo50iQPZ8A2fyVpMvJZAf.jpg' },
      { id: 70523, name: 'Dark', media_type: 'tv', poster_path: '/7CFCzWIZZcnxHke3yAQiGPWXHwF.jpg' },
    ],
  },
  // --- Powerful Black cinema ---
  {
    label: 'Moonlight + 12 Years a Slave',
    tagline: 'Unforgettable, essential cinema',
    items: [
      { id: 376867, title: 'Moonlight', media_type: 'movie', poster_path: '/qLnfEmPrDjJfPyyddLJPkXmshkp.jpg' },
      { id: 76203, title: '12 Years a Slave', media_type: 'movie', poster_path: '/xdANQijuNrJaw1HA61rDccME4Tm.jpg' },
    ],
  },
  // --- Power and privilege ---
  {
    label: 'Succession + The Crown',
    tagline: 'The weight of power',
    items: [
      { id: 76331, name: 'Succession', media_type: 'tv', poster_path: '/z0XiwdrCQ9yVIr4O0pxzaAYRxdW.jpg' },
      { id: 65494, name: 'The Crown', media_type: 'tv', poster_path: '/1DDE0Z2Y805rqfkEjPbZsMLyPwa.jpg' },
    ],
  },
  // --- Boundary-pushing comedy ---
  {
    label: 'Fleabag + Atlanta',
    tagline: 'Comedy that breaks all the rules',
    items: [
      { id: 67070, name: 'Fleabag', media_type: 'tv', poster_path: '/27vEYsRKa3eAniwmoccOoluEXQ1.jpg' },
      { id: 65495, name: 'Atlanta', media_type: 'tv', poster_path: '/8HZyGMnPLVVb00rmrh6A2SbK9NX.jpg' },
    ],
  },
  // --- Indian cinema ---
  {
    label: 'RRR + 3 Idiots',
    tagline: 'Bollywood blockbusters',
    items: [
      { id: 579974, title: 'RRR', media_type: 'movie', poster_path: '/u0XUBNQWlOvrh0Gd97ARGpIkL0.jpg' },
      { id: 20453, title: '3 Idiots', media_type: 'movie', poster_path: '/66A9MqXOyVFCssoloscw79z8Tew.jpg' },
    ],
  },
  // --- East Asian art cinema ---
  {
    label: 'The Handmaiden + In the Mood for Love',
    tagline: 'Exquisite East Asian cinema',
    items: [
      { id: 290098, title: 'The Handmaiden', media_type: 'movie', poster_path: '/dLlH4aNHdnmf62umnInL8xPlPzw.jpg' },
      { id: 843, title: 'In the Mood for Love', media_type: 'movie', poster_path: '/iYypPT4bhqXfq1b6EnmxvRt6b2Y.jpg' },
    ],
  },
  // --- Greta Gerwig ---
  {
    label: 'Lady Bird + Barbie',
    tagline: "Greta Gerwig's world",
    items: [
      { id: 391713, title: 'Lady Bird', media_type: 'movie', poster_path: '/gl66K7zRdtNYGrxyS2YDUP5ASZd.jpg' },
      { id: 346698, title: 'Barbie', media_type: 'movie', poster_path: '/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg' },
    ],
  },
  // --- Feel-good comedy ---
  {
    label: "Schitt's Creek + Ted Lasso",
    tagline: 'Heartwarming feel-good comedy',
    items: [
      { id: 61662, name: "Schitt's Creek", media_type: 'tv', poster_path: '/iRfSzrPS5VYWQv7KVSEg2BZZL6C.jpg' },
      { id: 97546, name: 'Ted Lasso', media_type: 'tv', poster_path: '/5fhZdwP1DVJ0FyVH6vrFdHwpXIn.jpg' },
    ],
  },
  // --- World cinema classics ---
  {
    label: 'Seven Samurai + City of God',
    tagline: 'World cinema titans',
    items: [
      { id: 346, title: 'Seven Samurai', media_type: 'movie', poster_path: '/lOMGc8bnSwQhS4XyE1S99uH8NXf.jpg' },
      { id: 598, title: 'City of God', media_type: 'movie', poster_path: '/k7eYdWvhYQyRQoU2TB2A2Xu2TfD.jpg' },
    ],
  },
  // --- European fantasy ---
  {
    label: "Pan's Labyrinth + Amélie",
    tagline: 'European enchantment',
    items: [
      { id: 1417, title: "Pan's Labyrinth", media_type: 'movie', poster_path: '/z7xXihu5wHuSMWymq5VAulPVuvg.jpg' },
      { id: 194, title: 'Amélie', media_type: 'movie', poster_path: '/nSxDa3M9aMvGVLoItzWTepQ5h5d.jpg' },
    ],
  },
  // --- International thriller TV ---
  {
    label: 'Squid Game + Money Heist',
    tagline: 'International TV phenomena',
    items: [
      { id: 93405, name: 'Squid Game', media_type: 'tv', poster_path: '/1QdXdRYfktUSONkl1oD5gc6Be0s.jpg' },
      { id: 71446, name: 'Money Heist', media_type: 'tv', poster_path: '/reEMJA1uzscCbkpeRJeTT2bjqUp.jpg' },
    ],
  },
  // --- Wes Anderson ---
  {
    label: 'Wes Anderson + Grand Budapest Hotel',
    tagline: 'Meticulously crafted whimsy',
    items: [
      { id: 5655, name: 'Wes Anderson', media_type: 'person', profile_path: '/oKDlhTjORiTQriqoUFJMTgGiwPg.jpg', known_for_department: 'Directing' },
      { id: 120467, title: 'The Grand Budapest Hotel', media_type: 'movie', poster_path: '/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg' },
    ],
  },
  // --- Action spectacle ---
  {
    label: 'Mad Max: Fury Road + John Wick',
    tagline: 'Pure adrenaline cinema',
    items: [
      { id: 76341, title: 'Mad Max: Fury Road', media_type: 'movie', poster_path: '/hA2ple9q4qnwxp3hKVNhroipsir.jpg' },
      { id: 245891, title: 'John Wick', media_type: 'movie', poster_path: '/wXqWR7dHncNRbxoEGybEy7QTe9h.jpg' },
    ],
  },
  // --- Classic horror ---
  {
    label: 'The Shining + Pulp Fiction',
    tagline: 'Iconic auteur cinema',
    items: [
      { id: 694, title: 'The Shining', media_type: 'movie', poster_path: '/uAR0AWqhQL1hQa69UDEbb2rE5Wx.jpg' },
      { id: 680, title: 'Pulp Fiction', media_type: 'movie', poster_path: '/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg' },
    ],
  },
  // --- Japanese anime ---
  {
    label: "Your Name + Howl's Moving Castle",
    tagline: 'Anime magic and wonder',
    items: [
      { id: 372058, title: 'Your Name', media_type: 'movie', poster_path: '/q719jXXEzOoYaps6babgKnONONX.jpg' },
      { id: 4935, title: "Howl's Moving Castle", media_type: 'movie', poster_path: '/13kOl2v0nD2OLbVSHnHk8GUFEhO.jpg' },
    ],
  },
  // --- Sci-fi mystery TV ---
  {
    label: 'Stranger Things + Viola Davis',
    tagline: 'From the Upside Down to the Oscars',
    items: [
      { id: 66732, name: 'Stranger Things', media_type: 'tv', poster_path: '/uOOtwVbSr4QDjAGIifLDwpb2Pdl.jpg' },
      { id: 19492, name: 'Viola Davis', media_type: 'person', profile_path: '/xDssw6vpYNRjsybvMPRE30e0dPN.jpg', known_for_department: 'Acting' },
    ],
  },
]

// Fisher-Yates shuffle for random order on each page load
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

const suggestions = ref(shuffle(allSuggestions))

const currentPage = ref(0)
const totalPages = computed(() => Math.ceil(suggestions.value.length / 3))
const carouselEl = ref(null)
const trackEl = ref(null)

// Pages as groups of 3
const pages = computed(() => {
  const result = []
  for (let i = 0; i < suggestions.value.length; i += 3) {
    result.push(suggestions.value.slice(i, i + 3))
  }
  return result
})

// Drag state
const dragOffset = ref(0)
const isDragging = ref(false)
let touchStartX = 0
let touchStartY = 0
let touchStartTime = 0
let directionLocked = false
let isHorizontal = false

const trackTransform = computed(() => {
  const pageOffset = currentPage.value * 100
  return `translateX(calc(-${pageOffset}% + ${dragOffset.value}px))`
})

function goToPage(page) {
  currentPage.value = page
}

function nextPage() {
  currentPage.value = Math.min(currentPage.value + 1, totalPages.value - 1)
}

function prevPage() {
  currentPage.value = Math.max(currentPage.value - 1, 0)
}

function onTouchStart(e) {
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
  touchStartTime = Date.now()
  directionLocked = false
  isHorizontal = false
  isDragging.value = true
  dragOffset.value = 0
}

function onTouchMove(e) {
  if (!isDragging.value) return

  const dx = e.touches[0].clientX - touchStartX
  const dy = e.touches[0].clientY - touchStartY

  // Lock direction after a small movement
  if (!directionLocked && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
    directionLocked = true
    isHorizontal = Math.abs(dx) > Math.abs(dy)
  }

  if (!directionLocked || !isHorizontal) return

  // Prevent vertical scroll while swiping horizontally
  e.preventDefault()

  // Apply resistance at edges
  let offset = dx
  if ((currentPage.value === 0 && dx > 0) ||
      (currentPage.value === totalPages.value - 1 && dx < 0)) {
    offset = dx * 0.3
  }

  dragOffset.value = offset
}

function onTouchEnd() {
  if (!isDragging.value) return
  isDragging.value = false

  if (!isHorizontal) {
    dragOffset.value = 0
    return
  }

  const dx = dragOffset.value
  const elapsed = Date.now() - touchStartTime
  const velocity = Math.abs(dx) / elapsed

  // Snap to next/prev if dragged far enough or fast enough
  if (Math.abs(dx) > 60 || velocity > 0.4) {
    if (dx < 0) nextPage()
    else prevPage()
  }

  dragOffset.value = 0
}

// Keyboard navigation
function onKeyDown(e) {
  if (e.key === 'ArrowRight') nextPage()
  else if (e.key === 'ArrowLeft') prevPage()
}

// Pre-warm the backend TMDB cache for all suggestion items
function precacheSuggestions() {
  const items = allSuggestions.flatMap(s => s.items)
  items.forEach((item, i) => {
    // Stagger requests to avoid hammering the backend
    setTimeout(() => {
      const url = item.media_type === 'person'
        ? `${BASE_URL}/person/${item.id}`
        : `${BASE_URL}/${item.media_type}/${item.id}/details`
      axios.get(url).catch(() => {})
    }, i * 100)
  })
}

onMounted(() => {
  carouselEl.value?.addEventListener('keydown', onKeyDown)
  precacheSuggestions()
})

onUnmounted(() => {
  carouselEl.value?.removeEventListener('keydown', onKeyDown)
})

function tmdbImage(item) {
  const path = item.profile_path || item.poster_path
  return path ? `https://image.tmdb.org/t/p/w342${path}` : null
}
</script>

<template>
  <div
    ref="carouselEl"
    class="suggestion-carousel"
    tabindex="0"
    @touchstart.passive="onTouchStart"
    @touchmove="onTouchMove"
    @touchend.passive="onTouchEnd"
  >
    <div class="carousel-outer">
      <button
        v-if="mdAndUp"
        class="carousel-arrow carousel-arrow-left"
        :disabled="currentPage === 0"
        aria-label="Previous"
        @click="prevPage"
      >
        <v-icon icon="mdi-chevron-left" size="28" />
      </button>

      <div class="carousel-viewport">
      <div
        ref="trackEl"
        class="carousel-track"
        :class="{ snapping: !isDragging }"
        :style="{ transform: trackTransform }"
      >
        <div
          v-for="(page, pageIndex) in pages"
          :key="pageIndex"
          class="carousel-page"
        >
          <div
            v-for="suggestion in page"
            :key="suggestion.label"
            class="suggestion-item"
            @click="$emit('select', suggestion)"
          >
            <div class="poster-pair">
              <div class="poster poster-1">
                <v-img
                  :src="tmdbImage(suggestion.items[0])"
                  cover
                  :aspect-ratio="2/3"
                >
                  <template #placeholder>
                    <div class="poster-placeholder">
                      <v-icon :icon="suggestion.items[0].media_type === 'person' ? 'mdi-account' : 'mdi-movie'" size="28" />
                    </div>
                  </template>
                </v-img>
              </div>
              <div class="poster-plus">+</div>
              <div class="poster poster-2">
                <v-img
                  :src="tmdbImage(suggestion.items[1])"
                  cover
                  :aspect-ratio="2/3"
                >
                  <template #placeholder>
                    <div class="poster-placeholder">
                      <v-icon :icon="suggestion.items[1].media_type === 'person' ? 'mdi-account' : 'mdi-movie'" size="28" />
                    </div>
                  </template>
                </v-img>
              </div>
            </div>
            <div class="suggestion-label text-body-2 font-weight-medium mt-3">{{ suggestion.label }}</div>
            <div class="suggestion-tagline text-caption text-medium-emphasis">{{ suggestion.tagline }}</div>
          </div>
        </div>
      </div>
    </div>

      <button
        v-if="mdAndUp"
        class="carousel-arrow carousel-arrow-right"
        :disabled="currentPage === totalPages - 1"
        aria-label="Next"
        @click="nextPage"
      >
        <v-icon icon="mdi-chevron-right" size="28" />
      </button>
    </div>

    <div class="carousel-controls mt-5">
      <div class="page-dots">
        <button
          v-for="page in totalPages"
          :key="page"
          class="dot"
          :class="{ active: page - 1 === currentPage }"
          :aria-label="`Go to page ${page}`"
          @click="goToPage(page - 1)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.suggestion-carousel {
  outline: none;
  user-select: none;
}

.carousel-outer {
  display: flex;
  align-items: center;
  max-width: 800px;
  margin: 0 auto;
}

.carousel-arrow {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(43, 33, 49, 0.6);
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, opacity 0.2s;
}

.carousel-arrow:hover:not(:disabled) {
  background: rgba(228, 163, 58, 0.2);
  border-color: rgba(228, 163, 58, 0.4);
}

.carousel-arrow:disabled {
  opacity: 0.25;
  cursor: default;
}

.carousel-arrow-left {
  margin-right: 12px;
}

.carousel-arrow-right {
  margin-left: 12px;
}

.carousel-viewport {
  overflow: hidden;
  max-width: 700px;
  margin: 0 auto;
  flex: 1;
  min-width: 0;
}

.carousel-track {
  display: flex;
  will-change: transform;
}

.carousel-track.snapping {
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.carousel-page {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  flex: 0 0 100%;
  min-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
  padding: 0 16px;
}

.suggestion-item {
  cursor: pointer;
  text-align: center;
  transition: transform 0.15s ease;
}

.suggestion-item:hover {
  transform: translateY(-3px);
}

.poster-pair {
  display: flex;
  align-items: center;
  justify-content: center;
}

.poster {
  width: 80px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.poster-1 {
  transform: rotate(-3deg);
}

.poster-2 {
  transform: rotate(3deg);
}

.suggestion-item:hover .poster-1 {
  transform: rotate(-5deg);
}

.suggestion-item:hover .poster-2 {
  transform: rotate(5deg);
}

.poster-plus {
  font-size: 16px;
  font-weight: 600;
  color: rgba(228, 163, 58, 0.7);
  margin: 0 6px;
  flex-shrink: 0;
}

.poster-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: rgba(255, 255, 255, 0.05);
}

.suggestion-label {
  line-height: 1.3;
}

.suggestion-tagline {
  line-height: 1.3;
}

.carousel-controls {
  display: flex;
  justify-content: center;
  align-items: center;
}

.page-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  padding: 0;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
}

.dot:hover {
  background: rgba(255, 255, 255, 0.4);
  transform: scale(1.3);
}

.dot.active {
  background: #E4A33A;
}

@media (max-width: 600px) {
  .carousel-page {
    gap: 8px;
    padding: 0;
  }

  .poster {
    width: 44px;
  }

  .poster-plus {
    font-size: 12px;
    margin: 0 2px;
  }

  .suggestion-label {
    font-size: 11px;
  }

  .suggestion-tagline {
    font-size: 10px;
  }
}
</style>
