import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'
const USER_ID_KEY = 'flickflock_uid'

function generateId() {
  return crypto.randomUUID?.() || (
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
    })
  )
}

export const useBookmarkStore = defineStore('bookmarks', () => {
  const userId = ref('')
  const listId = ref('')
  const items = ref([])
  const loading = ref(false)

  const bookmarkedIds = computed(() =>
    new Set(items.value.map(b => `${b.media_type}:${b.id}`))
  )

  function isBookmarked(mediaId, mediaType) {
    return bookmarkedIds.value.has(`${mediaType}:${mediaId}`)
  }

  function ensureUserId() {
    if (userId.value) return userId.value
    let stored = localStorage.getItem(USER_ID_KEY)
    if (!stored) {
      stored = generateId()
      localStorage.setItem(USER_ID_KEY, stored)
    }
    userId.value = stored
    return stored
  }

  function authHeaders() {
    return { 'X-User-Id': ensureUserId() }
  }

  async function fetchBookmarks() {
    ensureUserId()
    loading.value = true
    try {
      const res = await axios.get(`${BASE_URL}/bookmarks`, { headers: authHeaders() })
      listId.value = res.data.list_id
      items.value = res.data.items
    } catch (err) {
      console.error('fetchBookmarks error:', err)
    } finally {
      loading.value = false
    }
  }

  async function addBookmark(item) {
    ensureUserId()
    // Optimistic update
    if (isBookmarked(item.id, item.media_type)) return
    items.value.push(item)

    try {
      const res = await axios.post(`${BASE_URL}/bookmarks`, { item }, { headers: authHeaders() })
      listId.value = res.data.list_id
      items.value = res.data.items
    } catch (err) {
      console.error('addBookmark error:', err)
      // Revert optimistic update
      items.value = items.value.filter(
        b => !(b.id === item.id && b.media_type === item.media_type)
      )
    }
  }

  async function removeBookmark(mediaId, mediaType) {
    ensureUserId()
    // Optimistic update
    const prev = [...items.value]
    items.value = items.value.filter(
      b => !(b.id === mediaId && b.media_type === mediaType)
    )

    try {
      const res = await axios.delete(
        `${BASE_URL}/bookmarks/${mediaType}/${mediaId}`,
        { headers: authHeaders() },
      )
      listId.value = res.data.list_id
      items.value = res.data.items
    } catch (err) {
      console.error('removeBookmark error:', err)
      items.value = prev  // revert
    }
  }

  function toggleBookmark(item) {
    if (isBookmarked(item.id, item.media_type)) {
      return removeBookmark(item.id, item.media_type)
    } else {
      return addBookmark(item)
    }
  }

  async function fetchPublicList(publicListId) {
    loading.value = true
    try {
      const res = await axios.get(`${BASE_URL}/bookmarks/${publicListId}`)
      return res.data
    } catch (err) {
      console.error('fetchPublicList error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  function shareUrl() {
    return `${window.location.origin}/bookmarks/${listId.value}`
  }

  function init() {
    ensureUserId()
    fetchBookmarks()
  }

  return {
    userId,
    listId,
    items,
    loading,
    bookmarkedIds,
    isBookmarked,
    fetchBookmarks,
    addBookmark,
    removeBookmark,
    toggleBookmark,
    fetchPublicList,
    shareUrl,
    init,
  }
})
