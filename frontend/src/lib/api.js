const BASE = '/api';

async function getJSON(path, params = {}) {
  const url = new URL(BASE + path, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      url.searchParams.set(key, value);
    }
  }
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`API ${path}: HTTP ${resp.status}`);
  }
  return resp.json();
}

export function fetchNews({ source = null, kind = null, limit = 24, offset = 0 } = {}) {
  return getJSON('/news', { source, kind, limit, offset });
}

export function fetchArticle(id) {
  return getJSON(`/news/${id}`);
}

export function fetchSources() {
  return getJSON('/sources');
}

export function fetchStats() {
  return getJSON('/stats');
}

const rtf = new Intl.RelativeTimeFormat('ru', { numeric: 'auto' });

export function timeAgo(iso) {
  const date = new Date(iso);
  const diffSec = (date.getTime() - Date.now()) / 1000;
  const abs = Math.abs(diffSec);
  if (abs < 60) return 'только что';
  if (abs < 3600) return rtf.format(Math.round(diffSec / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(diffSec / 3600), 'hour');
  if (abs < 86400 * 7) return rtf.format(Math.round(diffSec / 86400), 'day');
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}
