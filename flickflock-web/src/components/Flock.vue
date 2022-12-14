<template>  
    <v-container
    class="overflow-y-visible pa-0 justify-center mx-2" 
    height="75"
    >
      <v-text-field
      v-model="searchQuery"
      placeholder="Search for your favourite movie or actor..."
      clearable 
      variant="outlined"
      hide-details="auto"
      @click:clear="this.searchResults = []"
    >
    <template v-slot:append-inner>
      <v-fade-transition leave-absolute>
        <v-progress-circular
          v-if="isLoading"
          color="info"
          indeterminate
          size="24"
        ></v-progress-circular>
      </v-fade-transition>                  
    </template>
    <template v-slot:prepend-inner>
      <v-icon icon="mdi-magnify" color="primary"></v-icon>
    </template>
  </v-text-field>
    <v-container 
    class="d-inline-flex flex-column overflow-y-hidden h-75 mt-n1 py-0"
    style="position: fixed;z-index:99999">
     <MoviesPeopleList 
      :search-results="searchResults" 
      addButton
      @addListItem="handleAddListItem" />
    </v-container>
  </v-container>
</template>

<script>
import axios from 'axios';
import _debounce from 'lodash/debounce'
import MoviesPeopleList from './MoviesPeopleList.vue';
export default {
    name: "Search",
    data() {
        return {
            searchResults: [],
            searchQuery: "",
            isLoading: false
        };
    },
    watch: {
        searchQuery: _debounce(function (newVal) {
            console.log(newVal);
            if (newVal.length > 2) {
                this.getResults();
            }
            if (newVal.length < 1) {
                this.searchResults = [];
            }
            return
        }, 600),
    },
    methods: {
        getResults() {
            this.isLoading = true;
            const baseUrl = "/api/search";
            axios.get(`${baseUrl}?q=${this.searchQuery}`)
                .then(res => {
                this.searchResults = res.data;
                this.isLoading = false;
            })
                .catch(err => {
                console.log(err);
                this.isLoading = false;
            });
        },
        handleAddListItem(data) {
          console.log(data)
          this.$emit('addSearchResult', data)
        }
    },
    components: { MoviesPeopleList }
}
</script>