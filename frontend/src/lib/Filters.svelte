<script>
  let { sources = [], selectedSource, selectedKind, onchange } = $props();

  const kinds = [
    { value: null, label: 'Все', icon: 'bi-collection' },
    { value: 'article', label: 'Статьи', icon: 'bi-file-text' },
    { value: 'video', label: 'Видео', icon: 'bi-youtube' },
  ];

  // When a kind is selected, show only sources of that kind in the chip row.
  let visibleSources = $derived(
    selectedKind ? sources.filter((s) => s.kind === selectedKind) : sources
  );

  function pickKind(kind) {
    const src = selectedSource && kind
      ? (sources.find((s) => s.id === selectedSource)?.kind === kind ? selectedSource : null)
      : selectedSource;
    onchange({ source: kind ? src : selectedSource, kind });
  }

  function pickSource(id) {
    onchange({ source: id, kind: selectedKind });
  }
</script>

<div class="my-3">
  <ul class="nav nav-pills mb-2">
    {#each kinds as k (k.label)}
      <li class="nav-item">
        <button
          class="nav-link py-1 {selectedKind === k.value ? 'active' : ''}"
          onclick={() => pickKind(k.value)}
        >
          <i class="bi {k.icon} me-1"></i>{k.label}
        </button>
      </li>
    {/each}
  </ul>

  <div class="source-chips">
    <button
      class="btn btn-sm {selectedSource === null ? 'btn-primary' : 'btn-outline-secondary'}"
      onclick={() => pickSource(null)}
    >
      Все источники
    </button>
    {#each visibleSources as s (s.id)}
      <button
        class="btn btn-sm {selectedSource === s.id ? 'btn-primary' : 'btn-outline-secondary'}"
        onclick={() => pickSource(s.id)}
        title="{s.article_count} материалов"
      >
        {#if s.kind === 'video'}<i class="bi bi-youtube me-1"></i>{/if}{s.name}
      </button>
    {/each}
  </div>
</div>
