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
      @input="isVisible = true"
      @click:clear="searchResults = []; isVisible = false"
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
    class="d-inline-flex flex-column overflow-y-hidden h-100 py-0 ml-n4"
    style="position: fixed;z-index:99999">
     <MoviesPeopleList 
      :list-items="searchResults" 
      transparent
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
    inject: ["baseUrlApi"],
    name: "Search",
    data() {
        return {
            searchResults: [],
            searchQuery: "",
            isLoading: false,
            isVisible: false
        };
    },
    watch: {
        searchQuery: _debounce(function (newVal) {
            if (newVal == null || newVal.length < 1) {
                this.searchResults = [];
                this.isVisible = false
            } else if (newVal.length > 2) {
                this.getResults();
            }            
            return
        }, 600),
        isVisible: function(newVal, oldVal) {
          if (newVal !== oldVal) {
            this.$emit('searchActive', newVal)
          }
        }
    },
    methods: {
        getResults() {
            this.isLoading = true;
            axios.get(`${this.baseUrlApi}/search?q=${this.searchQuery}`)
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
          this.$emit('addSearchResult', data)
          this.isVisible = false
        }
    },
    components: { MoviesPeopleList }
}
</script>