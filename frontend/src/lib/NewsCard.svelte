<script>
  import { timeAgo } from './api.js';

  let { article, onopen } = $props();

  function open(e) {
    e.preventDefault();
    onopen?.(article);
  }
</script>

<div class="card news-card">
  <div class="card-body d-flex flex-column">
    <div class="d-flex justify-content-between align-items-center mb-2 small text-secondary">
      <span class="badge text-bg-secondary">{article.source_name}</span>
      <span title={new Date(article.published).toLocaleString('ru-RU')}>
        {timeAgo(article.published)}
      </span>
    </div>
    <h6 class="card-title">
      <a href="/article/{article.id}" onclick={open}>{article.title}</a>
    </h6>
    {#if article.summary}
      <p class="card-text summary text-secondary mb-0">{article.summary}</p>
    {/if}
    <div class="mt-auto pt-2 d-flex gap-2">
      <button class="btn btn-sm btn-outline-primary" onclick={open}>
        Читать
      </button>
      <a
        class="btn btn-sm btn-outline-secondary"
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        title="Открыть оригинал"
      >
        <i class="bi bi-box-arrow-up-right"></i>
      </a>
    </div>
  </div>
</div>
