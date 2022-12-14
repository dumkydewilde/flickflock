<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute} from 'vue-router'
import { useDisplay } from 'vuetify'
import { trackStructEvent, enableActivityTracking } from '@snowplow/browser-tracker'

const { mdAndUp } = useDisplay()

</script>

<template>
  <v-app id="flickflock">
    <v-app-bar dark prominent dense extension-height="600" :extended="searchActive"
      class="bg-background pa-3 overflow-y-visible elevation-6">  
        <Search @addSearchResult="handleAddSearchResult" @searchActive="(b) => searchActive = b"/>
        <v-spacer></v-spacer>
        <v-btn variant="tonal" prepend-icon="mdi-bird" class="mt-3" href="/">New</v-btn>
      </v-app-bar>
    <v-main>
      <v-container
      class="pa-3 fill-height" fluid 
      >      
        
        <v-row justify="start" class="mt-6 fill-height"> 
          <v-col cols="12" lg="4" class="bg-primary mx-0 overflow-y-hidden" id="selection">
            <header class="ml-4 text-white" >
              <h3 class="text-overline">Your favourite movies and actors</h3>
              <h2 class="text-h5">Selection </h2>
            </header>
              <MoviesPeopleList 
                :list-items="selection"
                transparent
                inverseColor
                />
                <v-alert
                  v-if="selection.length < 2"
                  
                  variant="tonal"
                  dense
                  type="info"
                  
                  color="surface"
                  class="ma-3"
                >
                Add two or more movies or actors to your selection to discover more of their work and the people they've worked with!
              </v-alert>
              
          </v-col>
          <v-col lg="4" sm="12" id="myflock">
            <header class="ml-4" >
              <h3 class="text-overline">{{ flockId || 'flock ID' }}</h3>
              <h2 class="text-h5">My Flock 
                <v-progress-circular
                  v-if="flockLoading"
                  color="info"
                  indeterminate
                  size="24"
                ></v-progress-circular>
              </h2>
            </header>
              <MoviesPeopleList 
                :list-items="Object.values(flock)"
                mediaType="person"
                transparent
                sorted
                />

                <v-alert
                  v-if="Object.values(flock).length == 0 && !flockLoading"
                  
                  variant="tonal"
                  
                  type="info"
                  
                  color="white"
                  class="ma-3"
                >
                Your flock contains people who've collaborated together on movies and shows you like.
              </v-alert>
          </v-col>

          <v-col lg="4" cols="12" class="bg-surface" id="flockresults">
            <header class="ml-4" >
              <h3 class="text-overline">Content you might enjoy!</h3>
              <h2 class="text-h5">Flock Results
                <v-progress-circular
                  v-if="flockWorksLoading"
                  color="info"
                  indeterminate
                  size="24"
                ></v-progress-circular>
              </h2>
            </header>
              <MoviesPeopleList 
                :list-items="flockWorks"
                linkOut
                transparent
                sorted
                />
          </v-col>
        </v-row>
      </v-container>
      <v-bottom-navigation v-if="!mdAndUp">
        <v-btn href="#selection">
          <v-icon>mdi-cursor-pointer</v-icon>

          Selection
        </v-btn>

        <v-btn href="#myflock">
          <v-icon>mdi-bird</v-icon>

          My Flock
        </v-btn>

        <v-btn href="#flockresults">
          <v-icon>mdi-playlist-check</v-icon>

          Results
        </v-btn>
      </v-bottom-navigation>
    </v-main>
  </v-app>
</template>

<script>
  import axios from 'axios'
  import Search from './components/Search.vue'
  import MoviesPeopleList from './components/MoviesPeopleList.vue';
  import _debounce from 'lodash/debounce'

  export default {
    inject: ["baseUrlApi", "trackerEndpoint"],
    data () {
      return {
        baseUrl: this.baseUrlApi,
        flock: {},
        flockId: "",
        flockLoading: false,
        flockWorksLoading: false,
        flockWorks: [],
        selection: [],
        searchActive: false
      }
    },
    watch: {
      flock: function(newVal, oldVal) {
        },
        flockId: function(newVal, oldVal) {
          if (newVal != oldVal && newVal) {
            this.setURLParam("flockId", newVal)
          }
        }
    },
    methods: {
      getURLParam (param) {
          const urlSearchParams = new URLSearchParams(window.location.search)
          const params = Object.fromEntries(urlSearchParams.entries())
          return params[param]
      },
      setURLParam (param, value) {
          if (this.getURLParam('flockId') == undefined || this.getURLParam('flockId').length < 1) {
            const urlSearchParams = new URLSearchParams(window.location.search)
            const params = Object.fromEntries(urlSearchParams.entries())
            if (params[param] == undefined || params[param].length == 0) {
              urlSearchParams.set(param, value);
              const newurl = window.location.origin + window.location.pathname + '?' + urlSearchParams.toString()
              window.history.pushState({path:newurl},'',newurl);
            }
          }
          
      },
      handleAddSearchResult (data) {
        if (this.selection.map(el => el.id).indexOf(data.id) < 0) {
          this.selection.push(data)

          if (this.selection.length == 2) {
            this.addToFlock(this.selection)
          } else if (this.selection.length > 2) {
            this.addToFlock(this.selection[this.selection.length -1])
          }
        }
        
      }, 
      addToFlock (data) {
          this.flockLoading = true
          if ('id' in data) {
            data = [data]
          }

          axios.post(`${this.baseUrl}/flock/${this.flockId}`, {
            "data" : data
          })
          .then(res => {
            this.flockId = res.data.flock_id
            this.getFlock()

            trackStructEvent({
              category: 'flock',
              action: 'addToFlock',
              label: `flockId:${this.flockId}`,
              property: `${data.media_type}:${data.id}`
            });
          })
          .catch(err => console.log(err));
      },
      getFlock () {
          trackStructEvent({
              category: 'flock',
              action: 'getFlockStart',
              label: `flockId:${this.flockId}`,
            });
          this.flockLoading = true
          axios.get(`${this.baseUrl}/flock/${this.flockId}/details`)
          .then(res => {
            this.flock = res.data.flock
              this.selection = res.data.selection

            this.flockLoading = false
            trackStructEvent({
              category: 'flock',
              action: 'getFlockFinishedLoading',
              label: `flockId:${this.flockId}`,
            });
            if (!this.flockWorksLoading) {
              this.getFlockWorks()
            }
          })
          .catch(err => {
            console.log(err)
            this.flockLoading = false
          });

      },
      getFlockWorks () {
          this.flockWorksLoading = true
          axios.get(`${this.baseUrl}/flock/${this.flockId}/results`)
          .then(res => {
            this.flockWorks = res.data.flock_works
            this.selection = res.data.selection
            this.flockWorksLoading = false
            trackStructEvent({
              category: 'flock',
              action: 'flockResultsLoaded',
              label: `flockId:${this.flockId}`,
              property: `selectionLength:${this.selection.length};flockLength:${Object.keys(this.flock).length};resultLength:${this.flockWorks.length}`
            });
          })
          .catch(err => {
            console.log(err)
            this.flockWorksLoading = false
          });

      }
    },
    mounted() {
      this.flockId = this.getURLParam('flockId')
      console.log(this.flockId)
      if (this.flockId) {
        this.getFlock()
      } else {
        this.flockId = ""
      }

      enableActivityTracking({
        minimumVisitLength: 30,
        heartbeatDelay: 10
    });

      
    },
    components: {
      Search,
      MoviesPeopleList
    }
  }
</script>