<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { trackStructEvent } from '@snowplow/browser-tracker'
import { useFlockStore } from '../stores/flock'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const store = useFlockStore()

const searchQuery = ref('')
const searchResults = ref([])
const isLoading = ref(false)
const isVisible = ref(false)

let debounceTimer = null

watch(searchQuery, (val) => {
  clearTimeout(debounceTimer)
  if (!val || val.length < 1) {
    searchResults.value = []
    isVisible.value = false
    return
  }
  if (val.length > 2) {
    debounceTimer = setTimeout(() => getResults(), 500)
  }
})

async function getResults() {
  isLoading.value = true
  isVisible.value = true
  try {
    const res = await axios.get(`${BASE_URL}/search?q=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = res.data
    trackStructEvent({
      category: 'search',
      action: 'getResults',
      label: `numResults:${res.data.length}`,
      property: searchQuery.value,
    })
  } catch (err) {
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

function addItem(item) {
  store.addSearchResult(item)
  isVisible.value = false
  searchResults.value = []
  searchQuery.value = ''
  trackStructEvent({
    category: 'search',
    action: 'addResult',
    label: searchQuery.value,
    property: `${item.media_type}:${item.id}`,
  })
}

function tmdbImage(item) {
  const path = item.profile_path || item.poster_path
  return path ? `https://image.tmdb.org/t/p/w92${path}` : null
}

function itemLabel(item) {
  if (item.media_type === 'person') return item.known_for_department || 'Person'
  return item.media_type === 'movie' ? 'Movie' : 'TV'
}
</script>

<template>
  <v-text-field
    v-model="searchQuery"
    placeholder="Search for a movie, show, or actor..."
    clearable
    variant="outlined"
    hide-details
    density="comfortable"
    @input="isVisible = true"
    @click:clear="searchResults = []; isVisible = false"
  >
    <template v-slot:prepend-inner>
      <v-icon icon="mdi-magnify" color="primary" />
    </template>
    <template v-slot:append-inner>
      <v-progress-circular v-if="isLoading" color="info" indeterminate size="20" />
    </template>
  </v-text-field>

  <v-card
    v-if="isVisible && searchResults.length > 0"
    class="search-dropdown"
    elevation="8"
  >
    <v-list density="compact" bg-color="surface">
      <v-list-item
        v-for="item in searchResults"
        :key="`${item.media_type}-${item.id}`"
        @click="addItem(item)"
        class="py-2"
      >
        <template v-slot:prepend>
          <v-avatar :size="40" rounded="lg" color="background">
            <v-img v-if="tmdbImage(item)" :src="tmdbImage(item)" cover />
            <v-icon v-else :icon="item.media_type === 'person' ? 'mdi-account' : 'mdi-movie'" />
          </v-avatar>
        </template>
        <v-list-item-title class="text-body-2 font-weight-medium">
          {{ item.name || item.title }}
        </v-list-item-title>
        <v-list-item-subtitle class="text-caption">
          {{ itemLabel(item) }}
          <span v-if="item.release_date"> &middot; {{ item.release_date?.slice(0, 4) }}</span>
          <span v-if="item.first_air_date"> &middot; {{ item.first_air_date?.slice(0, 4) }}</span>
        </v-list-item-subtitle>
        <template v-slot:append>
          <v-icon icon="mdi-plus-circle-outline" color="info" size="20" />
        </template>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<style scoped>
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 9999;
  max-height: 400px;
  overflow-y: auto;
}
</style>
