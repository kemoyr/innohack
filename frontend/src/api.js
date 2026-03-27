const API_BASE = '';

export function getToken() {
  return localStorage.getItem('volunteer_plus_token');
}

export function setToken(token) {
  localStorage.setItem('volunteer_plus_token', token);
}

export function clearToken() {
  localStorage.removeItem('volunteer_plus_token');
  localStorage.removeItem('volunteer_plus_user');
}

export function getUser() {
  const raw = localStorage.getItem('volunteer_plus_user');
  return raw ? JSON.parse(raw) : null;
}

export function setUser(user) {
  localStorage.setItem('volunteer_plus_user', JSON.stringify(user));
}

function authHeaders() {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request(method, path, body = null) {
  const options = {
    method,
    headers: authHeaders(),
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${path}`, options);

  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `HTTP ${res.status}`);
  }

  return res.json();
}

async function publicRequest(method, path, body = null) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  const token = getToken();
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  if (body) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function uploadRequest(method, path, formData) {
  const token = getToken();
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: formData,
  });
  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

const api = {
  // Auth
  login: ({ email, password }) => publicRequest('POST', '/api/auth/login', { email, password }),
  register: (data) => publicRequest('POST', '/api/auth/register', data),
  getMe: () => request('GET', '/api/auth/me'),

  // Public
  getEvents: () => publicRequest('GET', '/api/events'),
  getStats: () => publicRequest('GET', '/api/stats'),
  getLeaderboard: () => publicRequest('GET', '/api/leaderboard'),
  getAchievements: () => publicRequest('GET', '/api/achievements'),
  getActivity: () => publicRequest('GET', '/api/activity'),
  getChartData: () => publicRequest('GET', '/api/stats/charts'),

  // Authenticated
  getVolunteers: () => request('GET', '/api/volunteers'),
  getVolunteer: (id) => publicRequest('GET', `/api/volunteers/${id}`),
  createEvent: (data) => request('POST', '/api/events', data),
  updateEvent: (id, data) => request('PATCH', `/api/events/${id}`, data),
  toggleVolunteerStatus: (id) => request('PATCH', `/api/volunteers/${id}/status`),

  // Volunteer events
  getMyEvents: () => request('GET', '/api/events/my/list'),
  uploadVerification: (eventId, formData) => uploadRequest('POST', `/api/events/${eventId}/verify`, formData),
  getVerification: (eventId) => request('GET', `/api/events/${eventId}/verification`),

  // Applications
  applyToEvent: (eventId, data) => request('POST', `/api/events/${eventId}/apply`, data),
  getMyApplications: () => request('GET', '/api/events/my/applications'),
  getMyApplication: (eventId) => request('GET', `/api/events/${eventId}/my-application`),
  getMyReview: (eventId) => request('GET', `/api/events/${eventId}/my-review`),
  getEventApplications: (eventId) => request('GET', `/api/events/${eventId}/applications`),

  // Reviews
  reviewEvent: (eventId, data) => request('POST', `/api/events/${eventId}/review`, data),
  getEventReviews: (eventId) => publicRequest('GET', `/api/events/${eventId}/reviews`),
  getVolunteerReviews: (volunteerId) => publicRequest('GET', `/api/volunteers/${volunteerId}/reviews`),

  // Moderation (coordinator)
  getModerationQueue: () => request('GET', '/api/moderation/queue'),
  getModerationHistory: () => request('GET', '/api/moderation/history'),
  moderateEvent: (eventId, data) => request('POST', `/api/moderation/${eventId}/decide`, data),
};

export default api;
