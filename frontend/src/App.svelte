<script>
  import { fetchNews, fetchSources, fetchStats } from './lib/api.js';
  import Header from './lib/Header.svelte';
  import Filters from './lib/Filters.svelte';
  import NewsCard from './lib/NewsCard.svelte';
  import ArticlePage from './lib/ArticlePage.svelte';
  import { tick } from 'svelte';

  const PAGE_SIZE = 24;
  const AUTO_REFRESH_MS = 120_000;

  function parseRoute(path) {
    const m = path.match(/^\/article\/([0-9a-f]+)\/?$/);
    return m ? { name: 'article', id: m[1] } : { name: 'feed' };
  }

  let route = $state(parseRoute(location.pathname));
  let openedArticle = $state(null);
  let savedScroll = 0;

  function openArticle(article) {
    savedScroll = window.scrollY;
    openedArticle = article;
    history.pushState({}, '', `/article/${article.id}`);
    route = { name: 'article', id: article.id };
  }

  function goBack() {
    if (history.state !== null) {
      history.back();
    } else {
      history.replaceState({}, '', '/');
      route = { name: 'feed' };
    }
  }

  async function onpopstate() {
    route = parseRoute(location.pathname);
    if (route.name === 'feed') {
      openedArticle = null;
      await tick();
      window.scrollTo(0, savedScroll);
    }
  }

  let articles = $state([]);
  let sources = $state([]);
  let stats = $state(null);
  let selectedSource = $state(null);
  let loading = $state(false);
  let loadingMore = $state(false);
  let error = $state('');
  let hasMore = $state(true);

  async function loadMeta() {
    try {
      [sources, stats] = await Promise.all([fetchSources(), fetchStats()]);
    } catch {
      /* not fatal for the feed */
    }
  }

  async function loadFeed({ reset = true } = {}) {
    error = '';
    if (reset) loading = true;
    else loadingMore = true;
    try {
      const offset = reset ? 0 : articles.length;
      const batch = await fetchNews({
        source: selectedSource,
        limit: PAGE_SIZE,
        offset,
      });
      if (reset) {
        articles = batch;
      } else {
        const seen = new Set(articles.map((a) => a.id));
        articles = [...articles, ...batch.filter((a) => !seen.has(a.id))];
      }
      hasMore = batch.length === PAGE_SIZE;
    } catch (e) {
      error = e.message || 'Не удалось загрузить ленту';
    } finally {
      loading = false;
      loadingMore = false;
    }
  }

  function onFiltersChange({ source }) {
    selectedSource = source;
    loadFeed({ reset: true });
  }

  function refresh() {
    loadMeta();
    loadFeed({ reset: true });
  }

  $effect(() => {
    refresh();
    const timer = setInterval(refresh, AUTO_REFRESH_MS);
    return () => clearInterval(timer);
  });
</script>

<svelte:window {onpopstate} />

{#if route.name === 'article'}
  <ArticlePage id={route.id} initial={openedArticle} onback={goBack} />
{:else}
  <Header {stats} onrefresh={refresh} />

  <main class="container pb-5">
    <Filters {sources} {selectedSource} onchange={onFiltersChange} />

    {#if error}
      <div class="alert alert-danger d-flex align-items-center gap-2">
        <i class="bi bi-exclamation-triangle"></i>
        {error}
        <button class="btn btn-sm btn-outline-danger ms-auto" onclick={refresh}>Повторить</button>
      </div>
    {/if}

    {#if loading && articles.length === 0}
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="mt-3 text-secondary">Загружаем новости…</p>
      </div>
    {:else if articles.length === 0 && !error}
      <div class="text-center py-5 text-secondary">
        <i class="bi bi-inbox display-4 d-block mb-3"></i>
        Пока пусто. Воркер собирает новости — загляните через минуту.
      </div>
    {:else}
      <div class="row g-3 row-cols-1 row-cols-md-2 row-cols-lg-3">
        {#each articles as article (article.id)}
          <div class="col">
            <NewsCard {article} onopen={openArticle} />
          </div>
        {/each}
      </div>

      {#if hasMore}
        <div class="text-center mt-4">
          <button class="btn btn-outline-primary" onclick={() => loadFeed({ reset: false })} disabled={loadingMore}>
            {#if loadingMore}
              <span class="spinner-border spinner-border-sm me-2"></span>
            {/if}
            Загрузить ещё
          </button>
        </div>
      {/if}
    {/if}
  </main>

  <footer class="border-top py-3">
    <div class="container small text-secondary d-flex justify-content-between flex-wrap gap-2">
      <span>NewsHub — агрегатор СМИ с открытым исходным кодом</span>
      <span><a href="https://github.com/newshub" target="_blank" rel="noopener noreferrer">Исходный код</a></span>
    </div>
  </footer>
{/if}
