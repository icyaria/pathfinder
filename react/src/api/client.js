const BASE = '/api'

async function req(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  getFeaturedTrails: (n = 3) => req('GET', `/trails/featured?n=${n}`),

  searchTrails: (profile) => req('POST', '/search', profile),

  getTrailStats: (trail) => req('POST', '/trail/stats', { trail }),

  getTrailPOIs: (lat, lon) => req('POST', '/trail/pois', { lat, lon }),

  getTrailWeather: (lat, lon, date = '') => req('POST', '/trail/weather', { lat, lon, date }),

  getTrailBiodiversity: (lat, lon) => req('POST', '/trail/biodiversity', { lat, lon }),

  getTrailRating: (trail_name) => req('GET', `/trail/rating?trail_name=${encodeURIComponent(trail_name)}`),

  getMyRating: (user_id, trail_name) => req('GET', `/trail/my-rating?user_id=${encodeURIComponent(user_id)}&trail_name=${encodeURIComponent(trail_name)}`),

  rateTrail: (user_id, trail_name, rating) => req('POST', '/trail/rate', { user_id, trail_name, rating }),

  chat: (trail, stats, pois, history, message) =>
    req('POST', '/chat', { trail, stats, pois, history, message }),

  saveTrail: (user_id, trail, profile) =>
    req('POST', '/trails/save', { user_id, trail, profile }),

  getSavedTrails: (user_id) => req('GET', `/trails/saved?user_id=${user_id}`),

  removeTrail: (user_id, trail_name) =>
    req('DELETE', '/trails/saved', { user_id, trail_name }),

  listUsers: () => req('GET', '/auth/users'),

  signup: (data) => req('POST', '/auth/signup', data),

  signin: (email, password) => req('POST', '/auth/signin', { email, password }),

  registerInterest: (trail_name) => req('POST', '/trails/interest', { trail_name }),

  getLiveInterests: () => req('GET', '/trails/interest'),

  discoverTrails: (region_id = null, n = 40) => {
    const qs = new URLSearchParams({ n })
    if (region_id) qs.set('region_id', region_id)
    return req('GET', `/trails/discover?${qs}`)
  },

  surpriseMe: (mood, region_id, preferences = {}) =>
    req('POST', '/surprise', { mood, region_id: region_id || null, preferences }),

  getUserGroups: (user_id) => req('GET', `/groups?user_id=${encodeURIComponent(user_id)}`),

  getGroupMessages: (trail_name, limit = 50) =>
    req('GET', `/groups/messages?trail_name=${encodeURIComponent(trail_name)}&limit=${limit}`),

  sendGroupMessage: (trail_name, user_id, user_name, text) =>
    req('POST', '/groups/messages', { trail_name, user_id, user_name, text }),

  leaveGroup: (trail_name, user_id) =>
    req('POST', '/groups/leave', { trail_name, user_id }),
}
