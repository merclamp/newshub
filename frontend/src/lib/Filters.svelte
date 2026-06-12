<script>
  let { sources = [], selectedSource, onchange } = $props();

  function pickSource(id) {
    onchange({ source: id });
  }

  function handleWheel(e) {
    const el = e.currentTarget;
    const atStart = el.scrollLeft === 0 && e.deltaY < 0;
    const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth && e.deltaY > 0;
    if (!atStart && !atEnd) {
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    }
  }
</script>

<div class="my-3">
  <div class="source-chips" onwheel={handleWheel}>
    <button
      class="btn btn-sm {selectedSource === null ? 'btn-primary' : 'btn-outline-secondary'}"
      onclick={() => pickSource(null)}
    >
      Все источники
    </button>
    {#each sources as s (s.id)}
      <button
        class="btn btn-sm {selectedSource === s.id ? 'btn-primary' : 'btn-outline-secondary'}"
        onclick={() => pickSource(s.id)}
        title="{s.article_count} материалов"
      >
        {s.name}
      </button>
    {/each}
  </div>
</div>
