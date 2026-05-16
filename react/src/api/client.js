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

  chat: (trail, stats, pois, history, message) =>
    req('POST', '/chat', { trail, stats, pois, history, message }),

  saveTrail: (user_id, trail, profile) =>
    req('POST', '/trails/save', { user_id, trail, profile }),

  getSavedTrails: (user_id) => req('GET', `/trails/saved?user_id=${user_id}`),

  removeTrail: (user_id, trail_name) =>
    req('DELETE', '/trails/saved', { user_id, trail_name }),

  listUsers: () => req('GET', '/auth/users'),

  signup: (data) => req('POST', '/auth/signup', data),

  signin: (user_id, password) => req('POST', '/auth/signin', { user_id, password }),
}
