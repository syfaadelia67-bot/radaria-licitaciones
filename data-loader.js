(() => {
  const nativeFetch = window.fetch.bind(window);
  const state = { mode: "demo", metadata: null, data: null };
  window.tenderSignalData = state;

  async function resolveDataMode() {
    try {
      const [metadataResponse, liveResponse] = await Promise.all([
        nativeFetch("data/live/metadata.json", { cache: "no-store" }),
        nativeFetch("data/live/opportunities.json", { cache: "no-store" }),
      ]);
      if (!metadataResponse.ok || !liveResponse.ok) return;
      const metadata = await metadataResponse.json();
      const data = await liveResponse.json();
      if (metadata.status === "live" && Array.isArray(data) && data.length > 0) {
        state.mode = "live";
        state.metadata = metadata;
        state.data = data;
      }
    } catch (error) {
      console.warn("Live data unavailable; using demonstration records.", error);
    }
  }

  const ready = resolveDataMode();

  window.fetch = async (input, init) => {
    const url = typeof input === "string" ? input : input?.url;
    if (url && /(^|\/)data\/opportunities\.json(?:\?|$)/.test(url)) {
      await ready;
      if (state.mode === "live") {
        return new Response(JSON.stringify(state.data), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
    }
    return nativeFetch(input, init);
  };

  function updateLabels() {
    const disclaimer = document.querySelector(".disclaimer");
    if (disclaimer) {
      if (state.mode === "live") {
        const timestamp = state.metadata?.retrieved_at
          ? new Date(state.metadata.retrieved_at).toLocaleString()
          : "unknown";
        disclaimer.textContent = `LIVE DATA · ${state.data.length} official TED notices · Last verified update: ${timestamp}`;
      } else {
        disclaimer.textContent = "DEMO DATA · Live TED data is not available yet. All records shown are synthetic demonstrations.";
      }
    }
    document.querySelectorAll(".demo-badge").forEach(badge => {
      badge.textContent = state.mode === "live" ? "LIVE" : "DEMO";
      badge.dataset.mode = state.mode;
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await ready;
    updateLabels();
    const grid = document.querySelector("#opportunityGrid");
    if (grid) new MutationObserver(updateLabels).observe(grid, { childList: true, subtree: true });
  });
})();
