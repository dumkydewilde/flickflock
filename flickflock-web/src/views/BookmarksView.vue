<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useBookmarkStore } from '../stores/bookmarks'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const route = useRoute()
const bookmarkStore = useBookmarkStore()

const listData = ref(null)
const loading = ref(true)
const isOwnList = ref(false)

function posterUrl(item, size = 'w300') {
  return item.poster_path
    ? `https://image.tmdb.org/t/p/${size}${item.poster_path}`
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

const displayItems = computed(() => {
  if (isOwnList.value) return bookmarkStore.items
  return listData.value?.items || []
})

async function copyShareUrl() {
  const id = route.params.listId || bookmarkStore.listId
  if (!id) return
  const url = `${window.location.origin}/bookmarks/${id}`
  try {
    await navigator.clipboard.writeText(url)
  } catch {
    // fallback ignored
  }
}

onMounted(async () => {
  const listId = route.params.listId

  if (listId) {
    // Viewing a specific public list
    isOwnList.value = listId === bookmarkStore.listId
    if (isOwnList.value) {
      listData.value = { items: bookmarkStore.items }
    } else {
      listData.value = await bookmarkStore.fetchPublicList(listId)
    }
  } else {
    // Viewing own bookmarks
    isOwnList.value = true
    if (!bookmarkStore.items.length) {
      await bookmarkStore.fetchBookmarks()
    }
    listData.value = { items: bookmarkStore.items }
  }

  loading.value = false
})
</script>

<template>
  <v-app>
    <v-app-bar flat color="background" class="px-3" density="comfortable">
      <v-app-bar-title>
        <router-link to="/" class="text-decoration-none" style="color: inherit;">
          <span class="text-primary font-weight-bold">Flick</span><span class="font-weight-light">Flock</span>
        </router-link>
      </v-app-bar-title>
      <v-spacer />
      <v-btn
        v-if="bookmarkStore.listId && isOwnList"
        variant="text"
        size="small"
        prepend-icon="mdi-share-variant"
        @click="copyShareUrl()"
      >
        Share
      </v-btn>
      <v-btn variant="tonal" size="small" prepend-icon="mdi-bird" to="/">New flock</v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-4" style="max-width: 960px;">
        <h2 class="text-h5 mb-1">
          <v-icon icon="mdi-bookmark-multiple" class="mr-2" color="primary" />
          {{ isOwnList ? 'My Bookmarks' : 'Shared Bookmarks' }}
        </h2>
        <p class="text-body-2 text-medium-emphasis mb-6">
          {{ isOwnList ? 'Movies and shows you want to watch.' : 'A curated list of movies and shows.' }}
        </p>

        <div v-if="loading" class="text-center py-12">
          <v-progress-circular color="primary" indeterminate />
        </div>

        <div v-else-if="displayItems.length === 0" class="text-center pa-8">
          <v-icon icon="mdi-bookmark-outline" size="64" color="primary" class="mb-4 d-block mx-auto" />
          <p class="text-body-1 text-medium-emphasis">No bookmarks yet.</p>
          <p v-if="isOwnList" class="text-body-2 text-medium-emphasis mt-2">
            Browse recommendations and tap the bookmark icon to save movies here.
          </p>
          <v-btn v-if="isOwnList" variant="tonal" color="primary" class="mt-4" to="/">
            Start discovering
          </v-btn>
        </div>

        <div v-else class="bookmarks-grid">
          <a
            v-for="item in displayItems"
            :key="`${item.media_type}-${item.id}`"
            :href="tmdbUrl(item)"
            target="_blank"
            rel="noopener"
            class="bookmark-card text-decoration-none"
          >
            <div class="poster-wrapper">
              <v-img
                v-if="posterUrl(item)"
                :src="posterUrl(item)"
                :alt="item.title"
                cover
                class="poster-img"
                :aspect-ratio="2/3"
              />
              <div v-else class="poster-placeholder d-flex align-center justify-center">
                <v-icon icon="mdi-movie-outline" size="40" color="primary" />
              </div>
              <v-chip
                class="type-badge"
                size="x-small"
                variant="flat"
                color="background"
              >
                {{ item.media_type === 'tv' ? 'TV' : 'Film' }}
              </v-chip>
              <v-btn
                v-if="isOwnList"
                class="remove-btn"
                icon="mdi-bookmark-remove"
                size="x-small"
                variant="flat"
                color="secondary"
                @click.prevent="bookmarkStore.removeBookmark(item.id, item.media_type)"
              />
            </div>
            <div class="card-info pa-2">
              <span class="text-caption font-weight-medium card-title">{{ item.title }}</span>
              <span class="text-caption text-medium-emphasis">{{ releaseYear(item) }}</span>
            </div>
          </a>
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
.bookmarks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.bookmark-card {
  border-radius: 8px;
  overflow: hidden;
  background: rgba(43, 33, 49, 0.6);
  transition: transform 0.2s, box-shadow 0.2s;
  color: inherit;
}

.bookmark-card:hover {
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

.type-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  opacity: 0.85;
}

.remove-btn {
  position: absolute;
  bottom: 6px;
  right: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.bookmark-card:hover .remove-btn {
  opacity: 1;
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
</style>
