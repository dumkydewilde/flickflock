<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useFlockStore } from '../stores/flock'
import { useDetailModals } from '../composables/useDetailModals'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const store = useFlockStore()
const { openPersonRequest, openMediaRequest, openPerson, openMedia } = useDetailModals()

const members = computed(() => {
  return Object.values(store.flock)
    .filter(m => m.name)
    .sort((a, b) => b.count - a.count)
})

// Modal state
const showModal = ref(false)
const modalLoading = ref(false)
const personDetail = ref(null)
const selectedMember = ref(null)

function tmdbImage(member, size = 'w92') {
  return member.profile_path
    ? `https://image.tmdb.org/t/p/${size}${member.profile_path}`
    : null
}

async function openPersonModal(member) {
  selectedMember.value = member
  personDetail.value = null
  showModal.value = true
  modalLoading.value = true

  try {
    const res = await axios.get(`${BASE_URL}/person/${member.id}`)
    personDetail.value = res.data
  } catch (err) {
    console.error('Failed to fetch person details:', err)
  } finally {
    modalLoading.value = false
  }
}

function addAndClose() {
  if (!selectedMember.value) return
  store.addSearchResult({
    id: selectedMember.value.id,
    name: selectedMember.value.name,
    media_type: 'person',
    profile_path: selectedMember.value.profile_path,
    known_for_department: selectedMember.value.known_for_department,
  })
  showModal.value = false
}

function addWorkToFlock(work) {
  store.addSearchResult({
    id: work.id,
    name: work.title || work.name,
    title: work.title || work.name,
    media_type: work.media_type || 'movie',
    poster_path: work.poster_path,
  })
}

function openWorkDetail(work) {
  showModal.value = false
  // Delay so Vuetify's dialog close transition completes before opening the next
  setTimeout(() => openMedia(work), 200)
}

// TMDB TV genre IDs to exclude (talk shows, news) — same as backend
const EXCLUDED_TV_GENRE_IDS = new Set([10767, 10763])

const knownFor = computed(() => {
  if (!personDetail.value) return []
  const cast = personDetail.value.cast || []
  const crew = personDetail.value.crew || []
  const all = [...cast, ...crew]
  // Deduplicate by id, skip talk/news shows, and take top 6 by popularity
  const seen = new Set()
  return all
    .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
    .filter(w => {
      if (seen.has(w.id)) return false
      seen.add(w.id)
      const genres = w.genre_ids || []
      if (genres.some(id => EXCLUDED_TV_GENRE_IDS.has(id))) return false
      return true
    })
    .slice(0, 6)
})

const isAlreadySelected = computed(() => {
  if (!selectedMember.value) return false
  return store.selection.some(s => s.id === selectedMember.value.id)
})

function isWorkSelected(work) {
  return store.selection.some(s => s.id === work.id)
}

// Cross-modal navigation: another component requests opening a person modal
watch(openPersonRequest, (req) => {
  if (req) openPersonModal(req)
})

// Close this modal when media modal is opening
watch(openMediaRequest, () => {
  showModal.value = false
})
</script>

<template>
  <div class="flock-members">
    <div v-if="members.length === 0 && !store.flockLoading" class="text-center pa-6">
      <v-icon icon="mdi-account-group-outline" size="48" color="info" class="mb-3 d-block mx-auto" />
      <p class="text-body-2 text-medium-emphasis">
        Your flock contains people who've collaborated on the movies and shows you like.
      </p>
    </div>

    <div class="members-grid" v-else>
      <div
        v-for="member in members"
        :key="member.id"
        class="member-card"
        @click="openPersonModal(member)"
      >
        <v-avatar :size="56" class="mb-1" color="background">
          <v-img v-if="tmdbImage(member)" :src="tmdbImage(member)" cover />
          <v-icon v-else icon="mdi-account" size="28" />
        </v-avatar>
        <span class="member-name text-caption text-center">{{ member.name }}</span>
        <v-chip size="x-small" variant="tonal" color="info" class="mt-1">
          {{ member.known_for_department || 'Crew' }}
        </v-chip>
      </div>
    </div>

    <!-- Person detail modal -->
    <v-dialog v-model="showModal" max-width="480" scrollable>
      <v-card color="surface">
        <v-card-title class="d-flex align-center pa-4">
          <span class="text-h6">{{ selectedMember?.name }}</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" size="small" @click="showModal = false" />
        </v-card-title>

        <v-card-text class="pa-4 pt-0">
          <div v-if="modalLoading" class="text-center py-8">
            <v-progress-circular color="primary" indeterminate />
          </div>

          <template v-else-if="personDetail">
            <div class="d-flex ga-4 mb-4">
              <v-avatar :size="100" rounded="lg" color="background">
                <v-img v-if="tmdbImage(selectedMember, 'w185')" :src="tmdbImage(selectedMember, 'w185')" cover />
                <v-icon v-else icon="mdi-account" size="48" />
              </v-avatar>
              <div>
                <v-chip size="small" variant="tonal" color="info" class="mb-2">
                  {{ personDetail.known_for_department || 'Crew' }}
                </v-chip>
                <div v-if="personDetail.birthday" class="text-caption text-medium-emphasis">
                  Born {{ personDetail.birthday }}
                </div>
                <div v-if="personDetail.place_of_birth" class="text-caption text-medium-emphasis">
                  {{ personDetail.place_of_birth }}
                </div>
              </div>
            </div>

            <p v-if="personDetail.biography" class="text-body-2 mb-4 biography">
              {{ personDetail.biography.slice(0, 300) }}{{ personDetail.biography.length > 300 ? '...' : '' }}
            </p>

            <div v-if="knownFor.length" class="mb-2">
              <p class="text-overline text-medium-emphasis mb-2">Known for</p>
              <div class="known-for-grid">
                <div v-for="work in knownFor" :key="work.id" class="known-for-item" @click="openWorkDetail(work)">
                  <div class="known-for-poster">
                    <v-img
                      v-if="work.poster_path"
                      :src="`https://image.tmdb.org/t/p/w92${work.poster_path}`"
                      :aspect-ratio="2/3"
                      cover
                      class="rounded"
                      width="64"
                    />
                    <div v-else class="poster-placeholder-sm rounded d-flex align-center justify-center">
                      <v-icon icon="mdi-movie-outline" size="20" />
                    </div>
                    <v-btn
                      v-if="!isWorkSelected(work)"
                      icon="mdi-plus"
                      size="x-small"
                      variant="flat"
                      color="primary"
                      class="add-btn"
                      @click.stop="addWorkToFlock(work)"
                    />
                    <v-icon
                      v-else
                      icon="mdi-check-circle"
                      size="18"
                      color="info"
                      class="added-icon"
                    />
                  </div>
                  <span class="text-caption known-for-title">{{ work.title || work.name }}</span>
                </div>
              </div>
            </div>
          </template>
        </v-card-text>

        <v-card-actions class="pa-4 pt-0">
          <v-btn
            variant="text"
            :href="`https://www.themoviedb.org/person/${selectedMember?.id}`"
            target="_blank"
            size="small"
          >
            TMDB
            <v-icon end icon="mdi-open-in-new" size="14" />
          </v-btn>
          <v-spacer />
          <v-btn
            v-if="!isAlreadySelected"
            variant="flat"
            color="primary"
            prepend-icon="mdi-plus"
            @click="addAndClose"
          >
            Add to selection
          </v-btn>
          <v-chip v-else variant="tonal" color="info" prepend-icon="mdi-check">
            Already selected
          </v-chip>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.members-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.member-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 80px;
  cursor: pointer;
  padding: 8px 4px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.member-card:hover {
  background-color: rgba(228, 163, 58, 0.1);
}

.member-name {
  max-width: 76px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.2;
  text-align: center;
  word-break: break-word;
}

.biography {
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.8);
}

.known-for-grid {
  display: flex;
  gap: 10px;
  overflow-x: auto;
}

.known-for-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 68px;
  flex-shrink: 0;
  cursor: pointer;
}

.known-for-item:hover .known-for-poster {
  opacity: 0.85;
}

.known-for-poster {
  position: relative;
  transition: opacity 0.2s;
}

.known-for-title {
  max-width: 68px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  text-align: center;
  margin-top: 4px;
  line-height: 1.3;
}

.add-btn {
  position: absolute;
  bottom: 2px;
  right: -2px;
  width: 22px !important;
  height: 22px !important;
}

.added-icon {
  position: absolute;
  bottom: 4px;
  right: 0;
}

.poster-placeholder-sm {
  width: 64px;
  aspect-ratio: 2 / 3;
  background: rgba(21, 16, 24, 0.8);
}
</style>
