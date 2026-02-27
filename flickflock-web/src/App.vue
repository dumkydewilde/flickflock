<script setup>
import { onMounted, computed } from 'vue'
import { useDisplay } from 'vuetify'
import { useRoute } from 'vue-router'
import { enableActivityTracking } from '@snowplow/browser-tracker'
import { useFlockStore } from './stores/flock'
import { useBookmarkStore } from './stores/bookmarks'
import Search from './components/Search.vue'
import SuggestionCarousel from './components/SuggestionCarousel.vue'
import SelectionList from './components/SelectionList.vue'
import FlockMembers from './components/FlockMembers.vue'
import ResultsGrid from './components/ResultsGrid.vue'

const { mdAndUp } = useDisplay()
const route = useRoute()
const store = useFlockStore()
const bookmarkStore = useBookmarkStore()

const isHome = computed(() => route.name === 'home')

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadSuggestion(suggestion) {
  for (const item of suggestion.items) {
    await store.addSearchResult(item)
  }
}

onMounted(() => {
  store.init()
  bookmarkStore.init()
  enableActivityTracking({
    minimumVisitLength: 30,
    heartbeatDelay: 10,
  })
})
</script>

<template>
  <v-app id="flickflock">
    <!-- Top bar -->
    <v-app-bar flat color="background" class="px-3" density="comfortable" :extension-height="40">
      <v-app-bar-title>
        <router-link to="/" style="text-decoration: none; color: inherit;">
          <span class="text-primary font-weight-bold">Flick</span><span class="font-weight-light">Flock</span>
        </router-link>
      </v-app-bar-title>

      <template #extension>
        <v-btn v-if="!isHome" icon="mdi-arrow-left" variant="text" size="small" to="/" />
        <v-btn
          v-if="store.flockId"
          variant="text"
          size="small"
          prepend-icon="mdi-share-variant"
          @click="store.copyShareUrl()"
        >
          Share
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          prepend-icon="mdi-bookmark-multiple-outline"
          to="/bookmarks"
        >
          Bookmarks
          <v-badge
            v-if="bookmarkStore.items.length"
            :content="bookmarkStore.items.length"
            color="primary"
            inline
            class="ml-1"
          />
        </v-btn>
        <v-btn variant="tonal" size="small" prepend-icon="mdi-bird" href="/">New</v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <!-- Home page content -->
      <v-container v-if="isHome" fluid class="pa-4">
        <!-- Search bar -->
        <div class="search-wrapper mb-6" style="position: relative;">
          <Search />
        </div>

        <!-- Onboarding (before any selections) -->
        <div v-if="store.selection.length === 0 && !store.flockLoading && !store.flockId" class="onboarding text-center py-8 px-2">
          <v-icon icon="mdi-bird" size="64" color="primary" class="mb-4" />
          <h2 class="text-h5 mb-2">Discover your next watch</h2>
          <p class="text-body-1 text-medium-emphasis mb-6" style="max-width: 480px; margin: 0 auto;">
            FlickFlock finds the people behind your favourite films and shows,
            then discovers what else they've made together.
          </p>
          <p class="text-body-2 text-medium-emphasis mb-4">Try a suggestion:</p>
          <SuggestionCarousel @select="loadSuggestion" />
        </div>

        <!-- Main content (after selections) -->
        <template v-else>
          <!-- Selection chips -->
          <section id="selection" class="mb-6">
            <h3 class="text-overline text-medium-emphasis mb-2">Your selection</h3>
            <SelectionList />
            <p v-if="store.selection.length < 2" class="text-caption text-medium-emphasis mt-2">
              Add one more to start building your flock.
            </p>
          </section>

          <v-row>
            <!-- Flock members -->
            <v-col cols="12" :md="4">
              <section id="myflock">
                <h3 class="text-overline text-medium-emphasis mb-2">
                  Your Flock
                  <v-progress-circular
                    v-if="store.flockLoading"
                    color="info"
                    indeterminate
                    size="16"
                    width="2"
                    class="ml-2"
                  />
                </h3>
                <FlockMembers />
              </section>
            </v-col>

            <!-- Results -->
            <v-col cols="12" :md="8">
              <section id="results">
                <h3 class="text-overline text-medium-emphasis mb-2">
                  Recommended for you
                  <v-progress-circular
                    v-if="store.flockWorksLoading"
                    color="info"
                    indeterminate
                    size="16"
                    width="2"
                    class="ml-2"
                  />
                </h3>
                <ResultsGrid />
              </section>
            </v-col>
          </v-row>
        </template>
      </v-container>

      <!-- Other routes (bookmarks, etc.) -->
      <router-view v-if="!isHome" />
    </v-main>

    <!-- Mobile bottom nav -->
    <v-bottom-navigation v-if="!mdAndUp && store.selection.length > 0" grow>
      <v-btn @click="scrollTo('selection')">
        <v-icon>mdi-cursor-pointer</v-icon>
        Selection
      </v-btn>
      <v-btn @click="scrollTo('myflock')">
        <v-icon>mdi-bird</v-icon>
        Flock
      </v-btn>
      <v-btn @click="scrollTo('results')">
        <v-icon>mdi-playlist-check</v-icon>
        Results
      </v-btn>
      <v-btn to="/bookmarks">
        <v-icon>mdi-bookmark-multiple-outline</v-icon>
        Bookmarks
      </v-btn>
    </v-bottom-navigation>

    <v-snackbar v-model="store.snackbar.show" :color="store.snackbar.color" :timeout="3000">
      {{ store.snackbar.text }}
    </v-snackbar>
  </v-app>
</template>

<style>
.search-wrapper {
  max-width: 640px;
  margin: 0 auto;
}

.onboarding {
  margin-top: 10vh;
}
</style>
