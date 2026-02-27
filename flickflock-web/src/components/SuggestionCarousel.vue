<script setup>
import { ref, computed } from 'vue'

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

const visibleSuggestions = computed(() => {
  const start = currentPage.value * 3
  return suggestions.slice(start, start + 3)
})

function nextPage() {
  currentPage.value = (currentPage.value + 1) % totalPages.value
}

function tmdbImage(item) {
  const path = item.profile_path || item.poster_path
  return path ? `https://image.tmdb.org/t/p/w185${path}` : null
}
</script>

<template>
  <div class="suggestion-carousel">
    <TransitionGroup name="suggestions" tag="div" class="suggestions-grid">
      <v-card
        v-for="suggestion in visibleSuggestions"
        :key="suggestion.label"
        class="suggestion-card"
        variant="tonal"
        color="surface"
        hover
        @click="$emit('select', suggestion)"
      >
        <div class="suggestion-images">
          <v-avatar size="56" rounded="lg" class="suggestion-img suggestion-img-1">
            <v-img :src="tmdbImage(suggestion.items[0])" cover />
          </v-avatar>
          <v-avatar size="56" rounded="lg" class="suggestion-img suggestion-img-2">
            <v-img :src="tmdbImage(suggestion.items[1])" cover />
          </v-avatar>
        </div>
        <div class="suggestion-text">
          <div class="text-body-2 font-weight-medium">{{ suggestion.label }}</div>
          <div class="text-caption text-medium-emphasis">{{ suggestion.tagline }}</div>
        </div>
      </v-card>
    </TransitionGroup>

    <div class="text-center mt-4">
      <v-btn
        variant="text"
        size="small"
        color="primary"
        prepend-icon="mdi-shuffle-variant"
        @click="nextPage"
      >
        Show me more
      </v-btn>
      <div class="page-dots mt-1">
        <span
          v-for="page in totalPages"
          :key="page"
          class="dot"
          :class="{ active: page - 1 === currentPage }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 640px;
  margin: 0 auto;
}

@media (max-width: 600px) {
  .suggestions-grid {
    grid-template-columns: 1fr;
    max-width: 320px;
  }
}

.suggestion-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px 12px;
  text-align: center;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.suggestion-card:hover {
  transform: translateY(-2px);
}

.suggestion-images {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.suggestion-img {
  border: 2px solid rgba(228, 163, 58, 0.3);
}

.suggestion-img-2 {
  margin-left: -12px;
}

.suggestion-text {
  line-height: 1.3;
}

.page-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transition: background 0.2s ease;
}

.dot.active {
  background: #E4A33A;
}

.suggestions-enter-active,
.suggestions-leave-active {
  transition: opacity 0.2s ease;
}

.suggestions-enter-from,
.suggestions-leave-to {
  opacity: 0;
}
</style>
