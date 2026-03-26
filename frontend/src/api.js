const API_BASE = '';

export function getToken() {
  return localStorage.getItem('volunteer_plus_token');
}

export function setToken(token) {
  localStorage.setItem('volunteer_plus_token', token);
}

export function clearToken() {
  localStorage.removeItem('volunteer_plus_token');
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

const api = {
  login: (password) => request('POST', '/api/auth/login', { password }),
  getVolunteers: () => request('GET', '/api/volunteers'),
  getVolunteer: (id) => request('GET', `/api/volunteers/${id}`),
  getEvents: () => request('GET', '/api/events'),
  createEvent: (data) => request('POST', '/api/events', data),
  updateEvent: (id, data) => request('PATCH', `/api/events/${id}`, data),
  getStats: () => request('GET', '/api/stats'),
  getLeaderboard: () => request('GET', '/api/leaderboard'),
  getAchievements: () => request('GET', '/api/achievements'),
  getActivity: () => request('GET', '/api/activity'),
  getChartData: () => request('GET', '/api/stats/charts'),
  toggleVolunteerStatus: (id) => request('PATCH', `/api/volunteers/${id}/status`),
};

export default api;
