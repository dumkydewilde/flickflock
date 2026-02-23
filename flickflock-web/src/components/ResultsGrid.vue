<script setup>
import { useFlockStore } from '../stores/flock'

const store = useFlockStore()

function posterUrl(item) {
  return item.poster_path
    ? `https://image.tmdb.org/t/p/w300${item.poster_path}`
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
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
