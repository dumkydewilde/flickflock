<template>
    <v-list v-if="(listItems.length > 0)"
        :class="{'elevation-3' : !transparent}"
        :style="{backgroundColor: (transparent ? 'transparent' : null)}"
        >
        <v-list-item 
        v-for="result in listItems"
        :key="result.id"
        :value="result"
        @click="result.clicked = !result.clicked"
        class="my-3 py-3 mx-0"
        >
            <template v-slot:prepend>
            <v-avatar rounded="0" :size="mdAndUp ? 96 : 48" class="rounded-lg">
                <v-img 
                    max-width="100" 
                    cover
                    :src="(result.profile_path || result.poster_path) ? `https://image.tmdb.org/t/p/w200${result.profile_path ? result.profile_path : result.poster_path}` : 'assets/logo.svg'"
                ></v-img>
            </v-avatar>
            </template>
            <template v-slot:append>
            <v-btn
                v-if="addButton"
                @click="$emit('addListItem', result)"
                icon="mdi-plus" variant="text"
            ></v-btn>
            <v-btn
                v-if="linkOut"
                :href="`https://www.themoviedb.org/${(result.media_type || this.mediaType)}/${result.id}`"
                icon="mdi-open-in-new" variant="text"
            ></v-btn>
            </template>
        <div class="fill-height align-self-start" :class="{'text-background': inverseColor}">
        <v-list-item-subtitle>
            <h3 class="text-overline">
            {{ result.known_for_department ? result.known_for_department.toUpperCase() : (result.media_type || this.mediaType).toUpperCase() }} 
            <v-icon icon="mdi-star" size="16px"></v-icon>
            {{ result.popularity }}
            </h3>
        </v-list-item-subtitle>
        <v-list-item-title>
            <a
            class="text-decoration-none"
            :class="{'text-background': inverseColor}"
            :href="`https://www.themoviedb.org/${(result.media_type || this.mediaType)}/${result.id}`"> 
                {{ result.name ? result.name : result.title }}
            </a>
        </v-list-item-title>
        <v-list-item-content v-if="mediaType == 'person'" >
            <span class="text-disabled">{{ result.birthday }} —</span>{{ result.biography ? (result.biography.slice(0,result.clicked ? undefined : 300) + (result.biography.length > 399 ? '...' : '')) : ""}}
        </v-list-item-content>
        <v-list-item-content v-else>
        {{ result.known_for ? `Known for: ${result.known_for.map(e => e.title).join(", ")}` : (result.overview ? (result.overview.slice(0,300) + (result.overview.length > 399 && result.clicked == false ? '...' : '')) : '') }}
        </v-list-item-content>
        </div>

        </v-list-item>
    </v-list>

</template>
<script>
import { useDisplay } from 'vuetify'
export default {
    name: 'MoviesPeopleList',
    props: {
        listItems: {
            type: Array,
            default: [{}]
        },
        mediaType: String,
        addButton: Boolean,
        linkOut: Boolean,
        transparent: Boolean,
        inverseColor: Boolean
    },
    data() {
      return {
        flockDialog: false
      }
    },
    setup() {
        const { xs, mdAndUp } = useDisplay()
        return { xs, mdAndUp }
    }
}
</script>