(() => {
  const nativeFetch = window.fetch.bind(window);
  const state = { mode: "demo", metadata: null, data: null };
  const DATA_TIMEOUT_MS = 6000;
  window.tenderSignalData = state;

  async function fetchWithTimeout(url, init = {}, timeoutMs = DATA_TIMEOUT_MS) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    const upstreamSignal = init.signal;
    const abortFromUpstream = () => controller.abort();

    if (upstreamSignal) {
      if (upstreamSignal.aborted) controller.abort();
      else upstreamSignal.addEventListener("abort", abortFromUpstream, { once: true });
    }

    try {
      return await nativeFetch(url, { ...init, signal: controller.signal });
    } finally {
      window.clearTimeout(timer);
      upstreamSignal?.removeEventListener("abort", abortFromUpstream);
    }
  }

  async function resolveDataMode() {
    try {
      const [metadataResponse, liveResponse] = await Promise.all([
        fetchWithTimeout("data/live/metadata.json", { cache: "no-store" }),
        fetchWithTimeout("data/live/opportunities.json", { cache: "no-store" }),
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

  function recordKey(title, country) {
    return `${String(title || "").trim()}\u0000${String(country || "").trim()}`;
  }

  function translationPresentation(record) {
    const status = record?.translation?.status;
    if (status === "machine_translated") {
      return { label: "LIVE · EN AI", title: "English machine translation; original preserved on the detail page" };
    }
    if (status === "source_english") {
      return { label: "LIVE · EN", title: "Original TED content is in English" };
    }
    return { label: "LIVE · ORIGINAL", title: "Original-language content; English translation not available yet" };
  }

  function linkLiveCards() {
    if (state.mode !== "live" || !Array.isArray(state.data)) return;
    const records = new Map(state.data.map(record => [recordKey(record.title, record.country), record]));
    document.querySelectorAll(".opportunity-card").forEach(card => {
      const title = card.querySelector(".title")?.textContent;
      const country = card.querySelector(".country")?.textContent;
      const record = records.get(recordKey(title, country));
      if (!record) return;

      const badge = card.querySelector(".demo-badge");
      if (badge) {
        const presentation = translationPresentation(record);
        if (badge.textContent !== presentation.label) badge.textContent = presentation.label;
        if (badge.title !== presentation.title) badge.title = presentation.title;
        if (badge.dataset.mode !== "live") badge.dataset.mode = "live";
        if (badge.dataset.translation !== record?.translation?.status) {
          badge.dataset.translation = record?.translation?.status || "original_only";
        }
      }

      let detailLink = card.querySelector(".detail-link");
      if (!detailLink) {
        detailLink = document.createElement("a");
        detailLink.className = "source-link detail-link";
        detailLink.textContent = "View TenderSignal detail page";
        const officialLink = card.querySelector(".source-link");
        card.insertBefore(detailLink, officialLink || null);
      }
      const nextHref = `opportunities/${encodeURIComponent(record.id)}/`;
      if (detailLink.getAttribute("href") !== nextHref) detailLink.href = nextHref;
    });
  }

  function updateLabels() {
    const disclaimer = document.querySelector(".disclaimer");
    if (disclaimer) {
      let nextText;
      if (state.mode === "live") {
        const timestamp = state.metadata?.retrieved_at
          ? new Date(state.metadata.retrieved_at).toLocaleString()
          : "unknown";
        const englishCount = state.data.filter(item => ["machine_translated", "source_english"].includes(item?.translation?.status)).length;
        nextText = `LIVE DATA · ${state.data.length} official TED notices · ${englishCount} available in English · Last verified update: ${timestamp}`;
      } else {
        nextText = "DEMO DATA · Live TED data is not available yet. All records shown are synthetic demonstrations.";
      }
      if (disclaimer.textContent !== nextText) disclaimer.textContent = nextText;
    }

    if (state.mode === "demo") {
      document.querySelectorAll(".demo-badge").forEach(badge => {
        if (badge.textContent !== "DEMO") badge.textContent = "DEMO";
        if (badge.dataset.mode !== "demo") badge.dataset.mode = "demo";
      });
    }
    linkLiveCards();
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await ready;
    updateLabels();
    const grid = document.querySelector("#opportunityGrid");
    if (grid) {
      const observer = new MutationObserver(() => updateLabels());
      observer.observe(grid, { childList: true, subtree: true });
    }
  });
})();
