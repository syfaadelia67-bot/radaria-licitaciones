(() => {
  const config = window.TenderSignalLeadConfig || {};
  const formIdPattern = /^[A-Za-z0-9_-]{4,32}$/;
  const configured = config.enabled === true && formIdPattern.test(String(config.formId || ""));

  function buildLeadUrl(trigger) {
    const url = new URL(`https://tally.so/r/${config.formId}`);
    url.searchParams.set("source", trigger.dataset.source || "website");
    url.searchParams.set("originPage", window.location.pathname);
    url.searchParams.set("offer", trigger.dataset.offer || "founder-validation");
    const opportunityId = new URLSearchParams(window.location.search).get("opportunityId");
    if (opportunityId) url.searchParams.set("opportunityId", opportunityId);
    return url.toString();
  }

  function setStatus(message, mode) {
    document.querySelectorAll("[data-lead-status]").forEach(node => {
      node.textContent = message;
      node.dataset.mode = mode;
    });
  }

  function initializeTrigger(trigger) {
    if (configured) {
      trigger.href = buildLeadUrl(trigger);
      trigger.target = "_blank";
      trigger.rel = "noopener noreferrer";
      trigger.removeAttribute("aria-disabled");
      trigger.dataset.captureState = "ready";
      return;
    }

    trigger.removeAttribute("href");
    trigger.setAttribute("aria-disabled", "true");
    trigger.dataset.captureState = "pending";
    trigger.addEventListener("click", event => event.preventDefault());
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-lead-trigger]").forEach(initializeTrigger);
    if (configured) {
      setStatus("Application intake is active. Responses are transmitted securely to the form provider.", "ready");
    } else {
      setStatus("Application intake is being activated. No information has been sent or stored by TenderSignal.", "pending");
    }
  });
})();
