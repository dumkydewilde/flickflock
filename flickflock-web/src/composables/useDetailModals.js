import { ref } from 'vue'

// Module-level refs are shared as singletons across all components
const openPersonRequest = ref(null)
const openMediaRequest = ref(null)

export function useDetailModals() {
  function openPerson(person) {
    // Timestamp ensures watch triggers even for the same person twice
    openPersonRequest.value = { ...person, _ts: Date.now() }
  }

  function openMedia(work) {
    openMediaRequest.value = { ...work, _ts: Date.now() }
  }

  return { openPersonRequest, openMediaRequest, openPerson, openMedia }
}
