<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['select'])

const suggestions = [
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
  {
    label: 'Safe + The Stranger',
    tagline: "Harlan Coben's Netflix universe",
    items: [
      { id: 72792, name: 'Safe', media_type: 'tv', poster_path: '/lrA2SSoWp3zzb0MBdjWKCVN0qEF.jpg' },
      { id: 96608, name: 'The Stranger', media_type: 'tv', poster_path: '/qKtjZ6f8ip6M7pYiDcVs0QXUAly.jpg' },
    ],
  },
  {
    label: 'Get Out + Black Swan',
    tagline: 'Psychological thrillers with a twist',
    items: [
      { id: 419430, title: 'Get Out', media_type: 'movie', poster_path: '/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg' },
      { id: 44214, title: 'Black Swan', media_type: 'movie', poster_path: '/viWheBd44bouiLCHgNMvahLThqx.jpg' },
    ],
  },
  {
    label: 'Fargo + No Country for Old Men',
    tagline: 'Crime in the American heartland',
    items: [
      { id: 60622, name: 'Fargo', media_type: 'tv', poster_path: '/6U9CPeD8obHzweikFhiLhpc7YBT.jpg' },
      { id: 6977, title: 'No Country for Old Men', media_type: 'movie', poster_path: '/6d5XOczc226jECq0LIX0siKtgHR.jpg' },
    ],
  },
  {
    label: '30 Rock + Andy Samberg',
    tagline: 'Comedy gold from NBC and beyond',
    items: [
      { id: 4608, name: '30 Rock', media_type: 'tv', poster_path: '/k3RbNzPEPW0cmkFkn1xVCTk3Qde.jpg' },
      { id: 154, name: 'Andy Samberg', media_type: 'person', profile_path: '/5MNbRsUzdhOHbiPYGosBUpsKYMR.jpg', known_for_department: 'Acting' },
    ],
  },
  {
    label: 'Inception + Interstellar',
    tagline: "Nolan's mind-bending epics",
    items: [
      { id: 27205, title: 'Inception', media_type: 'movie', poster_path: '/ljsZTbVsrQSqZgWeep2B1QiDKuh.jpg' },
      { id: 157336, title: 'Interstellar', media_type: 'movie', poster_path: '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg' },
    ],
  },
]

const currentPage = ref(0)
const totalPages = computed(() => Math.ceil(suggestions.length / 3))
const carouselEl = ref(null)

const visibleSuggestions = computed(() => {
  const start = currentPage.value * 3
  return suggestions.slice(start, start + 3)
})

function goToPage(page) {
  currentPage.value = page
}

function nextPage() {
  currentPage.value = (currentPage.value + 1) % totalPages.value
}

function prevPage() {
  currentPage.value = (currentPage.value - 1 + totalPages.value) % totalPages.value
}

// Swipe handling
let touchStartX = 0
let touchStartY = 0
let swiping = false

function onTouchStart(e) {
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
  swiping = true
}

function onTouchEnd(e) {
  if (!swiping) return
  swiping = false

  const dx = e.changedTouches[0].clientX - touchStartX
  const dy = e.changedTouches[0].clientY - touchStartY

  // Only trigger if horizontal swipe is dominant and long enough
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
    if (dx < 0) nextPage()
    else prevPage()
  }
}

// Keyboard navigation
function onKeyDown(e) {
  if (e.key === 'ArrowRight') nextPage()
  else if (e.key === 'ArrowLeft') prevPage()
}

onMounted(() => {
  carouselEl.value?.addEventListener('keydown', onKeyDown)
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
    @touchend.passive="onTouchEnd"
  >
    <div class="suggestions-grid">
      <div
        v-for="suggestion in visibleSuggestions"
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
        <div class="suggestion-label text-body-2 font-weight-medium mt-2">{{ suggestion.label }}</div>
        <div class="suggestion-tagline text-caption text-medium-emphasis">{{ suggestion.tagline }}</div>
      </div>
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
  touch-action: pan-y;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 640px;
  margin: 0 auto;
}

@media (max-width: 600px) {
  .suggestions-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
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
  gap: 0;
}

.poster {
  width: 80px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: transform 0.15s ease;
}

.suggestion-item:hover .poster-1 {
  transform: rotate(-2deg);
}

.suggestion-item:hover .poster-2 {
  transform: rotate(2deg);
}

.poster-plus {
  font-size: 16px;
  font-weight: 600;
  color: rgba(228, 163, 58, 0.7);
  margin: 0 4px;
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
  .poster {
    width: 60px;
  }

  .poster-plus {
    font-size: 14px;
    margin: 0 2px;
  }
}
</style>
