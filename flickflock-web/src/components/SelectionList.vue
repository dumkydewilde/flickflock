<script setup>
import { useFlockStore } from '../stores/flock'

const store = useFlockStore()

function tmdbImage(item) {
  const path = item.profile_path || item.poster_path
  return path ? `https://image.tmdb.org/t/p/w92${path}` : null
}

function itemLabel(item) {
  if (item.media_type === 'person') return item.known_for_department || 'Person'
  return item.media_type === 'movie' ? 'Movie' : 'TV Show'
}
</script>

<template>
  <div class="selection-list">
    <v-chip
      v-for="item in store.selection"
      :key="`sel-${item.id}`"
      closable
      variant="flat"
      color="primary"
      class="ma-1"
      size="large"
      @click:close="store.removeSelection(item.id)"
    >
      <template v-slot:prepend>
        <v-avatar start :size="28" rounded="lg">
          <v-img v-if="tmdbImage(item)" :src="tmdbImage(item)" cover />
          <v-icon v-else :icon="item.media_type === 'person' ? 'mdi-account' : 'mdi-movie'" size="16" />
        </v-avatar>
      </template>
      {{ item.name || item.title }}
      <v-tooltip activator="parent" location="bottom">{{ itemLabel(item) }}</v-tooltip>
    </v-chip>
  </div>
</template>

<style scoped>
.selection-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
