<script>
  let { stats = null, onrefresh } = $props();

  let theme = $state(localStorage.getItem('theme') || 'dark');

  $effect(() => {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);
  });

  function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
  }
</script>

<nav class="navbar navbar-expand sticky-top bg-body-tertiary border-bottom shadow-sm">
  <div class="container">
    <span class="navbar-brand fw-bold">
      <i class="bi bi-newspaper me-2"></i>NewsHub
    </span>
    {#if stats}
      <span class="navbar-text d-none d-md-inline small text-secondary">
        {stats.total} материалов · {stats.articles} статей · {stats.videos} видео
      </span>
    {/if}
    <div class="d-flex gap-2">
      <button class="btn btn-outline-secondary btn-sm" onclick={onrefresh} title="Обновить ленту">
        <i class="bi bi-arrow-clockwise"></i>
      </button>
      <button class="btn btn-outline-secondary btn-sm" onclick={toggleTheme} title="Сменить тему">
        <i class="bi {theme === 'dark' ? 'bi-sun' : 'bi-moon'}"></i>
      </button>
    </div>
  </div>
</nav>
