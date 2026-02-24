<script setup>
import { computed } from 'vue'
import { useFlockStore } from '../stores/flock'

const store = useFlockStore()

const members = computed(() => {
  return Object.values(store.flock)
    .filter(m => m.name)
    .sort((a, b) => b.count - a.count)
})

function tmdbImage(member) {
  return member.profile_path
    ? `https://image.tmdb.org/t/p/w92${member.profile_path}`
    : null
}

function addAsPerson(member) {
  store.addSearchResult({
    id: member.id,
    name: member.name,
    media_type: 'person',
    profile_path: member.profile_path,
    known_for_department: member.known_for_department,
  })
}
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
        @click="addAsPerson(member)"
      >
        <v-avatar :size="56" class="mb-1" color="background">
          <v-img v-if="tmdbImage(member)" :src="tmdbImage(member)" cover />
          <v-icon v-else icon="mdi-account" size="28" />
        </v-avatar>
        <span class="member-name text-caption text-center">{{ member.name }}</span>
        <v-chip size="x-small" variant="tonal" color="info" class="mt-1">
          {{ member.known_for_department || 'Crew' }}
        </v-chip>
        <v-tooltip activator="parent" location="bottom">
          Click to add {{ member.name }} to your selection
        </v-tooltip>
      </div>
    </div>
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
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
</style>
