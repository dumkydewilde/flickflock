import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { trackStructEvent } from '@snowplow/browser-tracker'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const useFlockStore = defineStore('flock', () => {
  const flockId = ref('')
  const selection = ref([])
  const flock = ref({})
  const flockWorks = ref([])
  const flockLoading = ref(false)
  const flockWorksLoading = ref(false)
  const snackbar = ref({ show: false, text: '', color: 'info' })

  // Filters
  const mediaTypeFilter = ref('all') // 'all', 'movie', 'tv'
  const sortBy = ref('relevance') // 'relevance', 'popularity', 'date'

  const filteredFlockWorks = computed(() => {
    let works = [...flockWorks.value]

    if (mediaTypeFilter.value !== 'all') {
      works = works.filter(w => w.media_type === mediaTypeFilter.value)
    }

    if (sortBy.value === 'popularity') {
      works.sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
    } else if (sortBy.value === 'date') {
      works.sort((a, b) => {
        const dateA = a.release_date || a.first_air_date || ''
        const dateB = b.release_date || b.first_air_date || ''
        return dateB.localeCompare(dateA)
      })
    }
    // 'relevance' keeps the backend sort (by count)

    return works
  })

  function getURLParam(param) {
    const urlSearchParams = new URLSearchParams(window.location.search)
    return urlSearchParams.get(param)
  }

  function setURLParam(param, value) {
    const current = getURLParam(param)
    if (!current || current.length === 0) {
      const urlSearchParams = new URLSearchParams(window.location.search)
      urlSearchParams.set(param, value)
      const newurl = window.location.origin + window.location.pathname + '?' + urlSearchParams.toString()
      window.history.pushState({ path: newurl }, '', newurl)
    }
  }

  async function addSearchResult(item) {
    if (selection.value.some(s => s.id === item.id)) return

    selection.value.push(item)

    if (selection.value.length >= 2) {
      const toSend = selection.value.length === 2
        ? selection.value
        : [item]
      await addToFlock(toSend)
    }
  }

  async function addToFlock(data) {
    flockLoading.value = true
    if (!Array.isArray(data)) data = [data]

    try {
      const url = flockId.value
        ? `${BASE_URL}/flock/${flockId.value}`
        : `${BASE_URL}/flock`
      const res = await axios.post(url, { data })
      flockId.value = res.data.flock_id
      setURLParam('flockId', flockId.value)

      trackStructEvent({
        category: 'flock',
        action: 'addToFlock',
        label: `flockId:${flockId.value}`,
        property: data.map(d => `${d.media_type}:${d.id}`).join(','),
      })

      await fetchFlock()
    } catch (err) {
      console.error('addToFlock error:', err)
      snackbar.value = { show: true, text: 'Failed to create flock — check console', color: 'error' }
      flockLoading.value = false
    }
  }

  async function removeSelection(selectionId) {
    if (!flockId.value) return

    try {
      const res = await axios.post(`${BASE_URL}/flock/${flockId.value}/remove`, {
        selection_id: selectionId,
      })
      selection.value = res.data.selection

      trackStructEvent({
        category: 'flock',
        action: 'removeFromFlock',
        label: `flockId:${flockId.value}`,
        property: `removed:${selectionId}`,
      })

      if (selection.value.length >= 2) {
        await fetchFlock()
      } else {
        flock.value = {}
        flockWorks.value = []
      }
    } catch (err) {
      console.error('removeSelection error:', err)
    }
  }

  async function fetchFlock() {
    if (!flockId.value) return

    trackStructEvent({
      category: 'flock',
      action: 'getFlockStart',
      label: `flockId:${flockId.value}`,
    })

    flockLoading.value = true
    flockWorksLoading.value = true

    try {
      const [detailsRes, worksRes] = await Promise.all([
        axios.get(`${BASE_URL}/flock/${flockId.value}/details`),
        axios.get(`${BASE_URL}/flock/${flockId.value}/results`),
      ])

      flock.value = detailsRes.data.flock
      selection.value = detailsRes.data.selection
      flockLoading.value = false

      trackStructEvent({
        category: 'flock',
        action: 'getFlockFinishedLoading',
        label: `flockId:${flockId.value}`,
      })

      flockWorks.value = worksRes.data.flock_works
      flockWorksLoading.value = false

      trackStructEvent({
        category: 'flock',
        action: 'flockResultsLoaded',
        label: `flockId:${flockId.value}`,
        property: `selectionLength:${selection.value.length};flockLength:${Object.keys(flock.value).length};resultLength:${flockWorks.value.length}`,
      })
    } catch (err) {
      console.error('fetchFlock error:', err)
      flockLoading.value = false
      flockWorksLoading.value = false
    }
  }

  async function fetchFlockWorks() {
    if (!flockId.value) return

    flockWorksLoading.value = true
    try {
      const res = await axios.get(`${BASE_URL}/flock/${flockId.value}/results`)
      flockWorks.value = res.data.flock_works
      selection.value = res.data.selection
      flockWorksLoading.value = false

      trackStructEvent({
        category: 'flock',
        action: 'flockResultsLoaded',
        label: `flockId:${flockId.value}`,
        property: `selectionLength:${selection.value.length};flockLength:${Object.keys(flock.value).length};resultLength:${flockWorks.value.length}`,
      })
    } catch (err) {
      console.error('fetchFlockWorks error:', err)
      flockWorksLoading.value = false
    }
  }

  function init() {
    const savedId = getURLParam('flockId')
    if (savedId) {
      flockId.value = savedId
      fetchFlock()
    }
  }

  async function copyShareUrl() {
    const url = `${window.location.origin}?flockId=${flockId.value}`
    try {
      await navigator.clipboard.writeText(url)
      snackbar.value = { show: true, text: 'Link copied to clipboard', color: 'info' }
    } catch {
      snackbar.value = { show: true, text: 'Could not copy link', color: 'error' }
    }
  }

  return {
    flockId,
    selection,
    flock,
    flockWorks,
    flockLoading,
    flockWorksLoading,
    mediaTypeFilter,
    sortBy,
    filteredFlockWorks,
    snackbar,
    addSearchResult,
    removeSelection,
    fetchFlock,
    fetchFlockWorks,
    init,
    copyShareUrl,
  }
})
