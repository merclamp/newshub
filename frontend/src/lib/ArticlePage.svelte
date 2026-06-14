<script>
  import { fetchArticle, timeAgo } from './api.js';

  let { id, initial = null, onback } = $props();

  // svelte-ignore state_referenced_locally
  let article = $state(initial);
  // svelte-ignore state_referenced_locally
  let loading = $state(!article || !article.content);
  let error = $state('');

  $effect(() => {
    if (!article || article.id !== id || !article.content) {
      loading = true;
      error = '';
      fetchArticle(id)
        .then((a) => (article = a))
        .catch(() => {
          if (!article) error = 'Материал не найден или устарел';
        })
        .finally(() => (loading = false));
    }
  });

  $effect(() => {
    document.title = article ? `${article.title} — NewsHub` : 'NewsHub';
    window.scrollTo(0, 0);
    return () => {
      document.title = 'NewsHub — агрегатор новостей';
    };
  });
</script>

<nav class="navbar sticky-top bg-body-tertiary border-bottom shadow-sm">
  <div class="container">
    <button class="btn btn-outline-secondary btn-sm" onclick={onback}>
      <i class="bi bi-arrow-left me-1"></i>К ленте
    </button>
    <span class="navbar-brand fw-bold mb-0">
      <i class="bi bi-newspaper me-2"></i>NewsHub
    </span>
  </div>
</nav>

<main class="container pb-5">
  <div class="reader-column">
    {#if error}
      <div class="alert alert-warning mt-4 d-flex align-items-center gap-2">
        <i class="bi bi-exclamation-triangle"></i>
        {error}
      </div>
      <button class="btn btn-outline-secondary" onclick={onback}>
        <i class="bi bi-arrow-left me-1"></i>Вернуться к ленте
      </button>
    {:else if !article}
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
      </div>
    {:else}
      <div class="d-flex align-items-center gap-2 small mt-4 mb-3">
        <span class="badge text-bg-secondary">{article.source_name}</span>
        <span class="text-secondary" title={new Date(article.published).toLocaleString('ru-RU')}>
          {timeAgo(article.published)}
        </span>
      </div>

      <h1 class="mb-4">{article.title}</h1>

      {#if loading && !article.content}
        <div class="text-center py-5">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="mt-3 text-secondary">Загружаем полный текст…</p>
        </div>
      {:else if article.content}
        <div class="article-content">
          {@html article.content}
        </div>
      {:else}
        {#if article.summary}
          <p>{article.summary}</p>
        {/if}
        <div class="alert alert-secondary d-flex align-items-center gap-2 small">
          <i class="bi bi-info-circle"></i>
          Полный текст недоступен — откройте оригинал по ссылке ниже.
        </div>
      {/if}

      <hr class="my-4" />
      <div class="d-flex flex-wrap gap-2 justify-content-between">
        <a class="btn btn-primary" href={article.url} target="_blank" rel="noopener noreferrer">
          <i class="bi bi-box-arrow-up-right me-1"></i>Читать оригинал
        </a>
        <button class="btn btn-outline-secondary" onclick={onback}>
          <i class="bi bi-arrow-left me-1"></i>К ленте
        </button>
      </div>
    {/if}
  </div>
</main>
