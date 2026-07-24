const state = {
  opportunities: [],
  profile: {
    keywords: ["software", "cloud", "cybersecurity"],
    category: "",
    country: "",
    capacity: 250000,
  },
  language: "en",
};

const translations = {
  en: {
    nav_opportunities: "Opportunities", nav_how: "How it works", eyebrow: "AI-ranked public procurement",
    hero_title: "Stop reading every tender. Find the ones worth pursuing.",
    hero_subtitle: "Describe what your company sells. TenderSignal scores public opportunities by fit, urgency and commercial value.",
    build_profile: "Build my supplier profile", browse_demo: "Browse demo opportunities",
    demo_disclaimer: "Prototype: all opportunities shown are synthetic demonstration records, not active tenders.",
    strong_fit: "Strong fit", preview_title: "Cloud security assessment", preview_1: "Keyword match: cloud, security",
    preview_2: "Preferred market: United Kingdom", preview_3: "Deadline: 21 days", profile_eyebrow: "Your matching criteria",
    profile_title: "Create a lightweight supplier profile", reset: "Reset", keywords: "Products, services or keywords",
    preferred_category: "Preferred category", any_category: "Any category", preferred_country: "Preferred market",
    any_country: "Any country", capacity: "Maximum contract size", no_limit: "No limit", rank_opportunities: "Rank opportunities",
    market_feed: "Market feed", opportunities_title: "Ranked opportunities", search: "Search", all_countries: "All countries",
    all_categories: "All categories", any_deadline: "Any deadline", next_14: "Next 14 days", next_30: "Next 30 days",
    next_60: "Next 60 days", empty_title: "No matching opportunities", empty_body: "Broaden the filters or update your supplier profile.",
    transparent_scoring: "Transparent scoring", how_title: "A recommendation you can audit", step1_title: "Normalize",
    step1_body: "Convert official notices from different markets into one consistent schema.", step2_title: "Match",
    step2_body: "Compare keywords, category, market, value and deadline with your profile.", step3_title: "Explain",
    step3_body: "Show exactly which factors increased or reduced each relevance score.", founder_access: "Founder access",
    alert_title: "Get the weekly ranked opportunity report", alert_body: "Join the validation list. No payment is collected in this prototype.",
    join_list: "Join validation list", value: "Value", deadline: "Deadline", source: "Source", visit_source: "Visit official portal",
    footer_note: "Built as a zero-capital AI company experiment.", results: "opportunities shown", saved: "Saved locally for prototype validation.",
    keyword_match: "keyword match", category_match: "category match", market_match: "preferred market", within_capacity: "within capacity",
    near_deadline: "deadline approaching", broad_fit: "broad profile fit"
  },
  es: {
    nav_opportunities: "Oportunidades", nav_how: "Cómo funciona", eyebrow: "Contratación pública clasificada por IA",
    hero_title: "Dejá de leer cada licitación. Encontrá las que vale la pena perseguir.",
    hero_subtitle: "Describí lo que vende tu empresa. TenderSignal puntúa oportunidades públicas por encaje, urgencia y valor comercial.",
    build_profile: "Crear perfil proveedor", browse_demo: "Ver oportunidades demo",
    demo_disclaimer: "Prototipo: todas las oportunidades son registros sintéticos de demostración, no licitaciones activas.",
    strong_fit: "Alta compatibilidad", preview_title: "Evaluación de seguridad cloud", preview_1: "Coincidencia: cloud, seguridad",
    preview_2: "Mercado preferido: Reino Unido", preview_3: "Vencimiento: 21 días", profile_eyebrow: "Criterios de coincidencia",
    profile_title: "Creá un perfil liviano de proveedor", reset: "Restablecer", keywords: "Productos, servicios o palabras clave",
    preferred_category: "Categoría preferida", any_category: "Cualquier categoría", preferred_country: "Mercado preferido",
    any_country: "Cualquier país", capacity: "Tamaño máximo del contrato", no_limit: "Sin límite", rank_opportunities: "Ordenar oportunidades",
    market_feed: "Flujo de mercado", opportunities_title: "Oportunidades ordenadas", search: "Buscar", all_countries: "Todos los países",
    all_categories: "Todas las categorías", any_deadline: "Cualquier vencimiento", next_14: "Próximos 14 días", next_30: "Próximos 30 días",
    next_60: "Próximos 60 días", empty_title: "No hay oportunidades coincidentes", empty_body: "Ampliá los filtros o actualizá tu perfil.",
    transparent_scoring: "Puntuación transparente", how_title: "Una recomendación que podés auditar", step1_title: "Normalizar",
    step1_body: "Convertir avisos oficiales de distintos mercados en un esquema consistente.", step2_title: "Comparar",
    step2_body: "Cruzar palabras clave, categoría, mercado, valor y fecha con tu perfil.", step3_title: "Explicar",
    step3_body: "Mostrar qué factores aumentaron o redujeron cada puntuación.", founder_access: "Acceso fundador",
    alert_title: "Recibí el informe semanal de oportunidades", alert_body: "Sumate a la lista de validación. Este prototipo no cobra pagos.",
    join_list: "Unirme a la lista", value: "Valor", deadline: "Vencimiento", source: "Fuente", visit_source: "Visitar portal oficial",
    footer_note: "Construido como experimento de empresa IA con capital cero.", results: "oportunidades mostradas", saved: "Guardado localmente para validar el prototipo.",
    keyword_match: "coincidencia de palabras", category_match: "categoría coincidente", market_match: "mercado preferido", within_capacity: "dentro de capacidad",
    near_deadline: "vencimiento cercano", broad_fit: "encaje general"
  }
};

const $ = (selector) => document.querySelector(selector);
const elements = {
  grid: $("#opportunityGrid"), template: $("#opportunityTemplate"), empty: $("#emptyState"), summary: $("#resultSummary"),
  search: $("#searchInput"), country: $("#countryFilter"), category: $("#categoryFilter"), deadline: $("#deadlineFilter"),
  minValue: $("#minValueFilter"), profileForm: $("#profileForm"), profileKeywords: $("#profileKeywords"),
  profileCategory: $("#profileCategory"), profileCountry: $("#profileCountry"), profileCapacity: $("#profileCapacity"),
  resetProfile: $("#resetProfile"), language: $("#languageButton"), alertForm: $("#alertForm"), alertMessage: $("#alertMessage")
};

function t(key) { return translations[state.language][key] || translations.en[key] || key; }
function unique(values) { return [...new Set(values)].sort((a, b) => a.localeCompare(b)); }
function tokenize(text) { return String(text).toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean); }
function daysUntil(date) { return Math.ceil((new Date(date) - new Date()) / 86400000); }
function formatMoney(value, currency) {
  return new Intl.NumberFormat(state.language === "es" ? "es-AR" : "en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}
function formatDate(value) {
  return new Intl.DateTimeFormat(state.language === "es" ? "es-AR" : "en-GB", { year: "numeric", month: "short", day: "numeric" }).format(new Date(value));
}

function calculateScore(opportunity) {
  let score = 18;
  const reasons = [];
  const opportunityTokens = new Set(tokenize(`${opportunity.title} ${opportunity.description} ${opportunity.keywords.join(" ")}`));
  const matchedKeywords = state.profile.keywords.filter(keyword => tokenize(keyword).some(token => opportunityTokens.has(token)));
  if (state.profile.keywords.length) {
    const keywordPoints = Math.min(40, matchedKeywords.length * 14);
    score += keywordPoints;
    if (matchedKeywords.length) reasons.push(`${t("keyword_match")}: ${matchedKeywords.slice(0, 3).join(", ")}`);
  }
  if (state.profile.category && opportunity.category === state.profile.category) { score += 18; reasons.push(t("category_match")); }
  if (state.profile.country && opportunity.country === state.profile.country) { score += 14; reasons.push(t("market_match")); }
  if (state.profile.capacity === 0 || opportunity.value <= state.profile.capacity) { score += 7; reasons.push(t("within_capacity")); }
  const remaining = daysUntil(opportunity.deadline);
  if (remaining >= 7 && remaining <= 35) { score += 3; reasons.push(t("near_deadline")); }
  if (!reasons.length) reasons.push(t("broad_fit"));
  return { score: Math.max(0, Math.min(100, score)), reasons };
}

function passesFilters(opportunity) {
  const query = elements.search.value.trim().toLowerCase();
  const searchable = `${opportunity.title} ${opportunity.description} ${opportunity.country} ${opportunity.category} ${opportunity.keywords.join(" ")}`.toLowerCase();
  const deadlineWindow = Number(elements.deadline.value);
  return (!query || searchable.includes(query))
    && (!elements.country.value || opportunity.country === elements.country.value)
    && (!elements.category.value || opportunity.category === elements.category.value)
    && (!deadlineWindow || (daysUntil(opportunity.deadline) >= 0 && daysUntil(opportunity.deadline) <= deadlineWindow))
    && (!Number(elements.minValue.value) || opportunity.value >= Number(elements.minValue.value));
}

function render() {
  elements.grid.innerHTML = "";
  const ranked = state.opportunities
    .filter(passesFilters)
    .map(opportunity => ({ ...opportunity, relevance: calculateScore(opportunity) }))
    .sort((a, b) => b.relevance.score - a.relevance.score || new Date(a.deadline) - new Date(b.deadline));

  ranked.forEach(opportunity => {
    const fragment = elements.template.content.cloneNode(true);
    fragment.querySelector(".score-value").textContent = opportunity.relevance.score;
    fragment.querySelector(".country").textContent = opportunity.country;
    fragment.querySelector(".category").textContent = opportunity.category;
    fragment.querySelector(".title").textContent = opportunity.title;
    fragment.querySelector(".description").textContent = opportunity.description;
    fragment.querySelector(".value").textContent = formatMoney(opportunity.value, opportunity.currency);
    fragment.querySelector(".deadline").textContent = formatDate(opportunity.deadline);
    fragment.querySelector(".source").textContent = opportunity.source;
    fragment.querySelector(".score-explanation").textContent = opportunity.relevance.reasons.join(" · ");
    const link = fragment.querySelector(".source-link");
    link.href = opportunity.source_url;
    elements.grid.appendChild(fragment);
  });

  elements.empty.hidden = ranked.length > 0;
  elements.summary.textContent = `${ranked.length} ${t("results")}`;
  applyTranslations(elements.grid);
}

function populateSelect(select, values, initialLabelKey) {
  const current = select.value;
  select.innerHTML = `<option value="">${t(initialLabelKey)}</option>`;
  values.forEach(value => select.add(new Option(value, value)));
  select.value = current;
}

function applyTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach(node => {
    const key = node.dataset.i18n;
    if (translations[state.language][key]) node.textContent = translations[state.language][key];
  });
  elements.search.placeholder = state.language === "es" ? "Buscar oportunidades" : "Search opportunities";
  elements.minValue.placeholder = state.language === "es" ? "Valor mínimo" : "Minimum value";
}

function updateLanguage() {
  applyTranslations();
  elements.language.textContent = state.language === "en" ? "ES" : "EN";
  populateSelect(elements.country, unique(state.opportunities.map(item => item.country)), "all_countries");
  populateSelect(elements.category, unique(state.opportunities.map(item => item.category)), "all_categories");
  populateSelect(elements.profileCountry, unique(state.opportunities.map(item => item.country)), "any_country");
  populateSelect(elements.profileCategory, unique(state.opportunities.map(item => item.category)), "any_category");
  render();
}

function saveProfile() { localStorage.setItem("tendersignal-profile", JSON.stringify(state.profile)); }
function loadProfile() {
  try { Object.assign(state.profile, JSON.parse(localStorage.getItem("tendersignal-profile")) || {}); } catch (_) {}
  elements.profileKeywords.value = state.profile.keywords.join(", ");
  elements.profileCategory.value = state.profile.category;
  elements.profileCountry.value = state.profile.country;
  elements.profileCapacity.value = String(state.profile.capacity);
}

function bindEvents() {
  [elements.search, elements.country, elements.category, elements.deadline, elements.minValue].forEach(element => element.addEventListener("input", render));
  elements.profileForm.addEventListener("submit", event => {
    event.preventDefault();
    state.profile = {
      keywords: elements.profileKeywords.value.split(",").map(value => value.trim()).filter(Boolean),
      category: elements.profileCategory.value,
      country: elements.profileCountry.value,
      capacity: Number(elements.profileCapacity.value),
    };
    saveProfile();
    render();
    document.querySelector("#opportunities").scrollIntoView({ behavior: "smooth" });
  });
  elements.resetProfile.addEventListener("click", () => {
    localStorage.removeItem("tendersignal-profile");
    state.profile = { keywords: ["software", "cloud", "cybersecurity"], category: "", country: "", capacity: 250000 };
    loadProfile(); render();
  });
  elements.language.addEventListener("click", () => { state.language = state.language === "en" ? "es" : "en"; updateLanguage(); });
  elements.alertForm.addEventListener("submit", event => {
    event.preventDefault();
    const email = $("#emailInput").value.trim();
    const signups = JSON.parse(localStorage.getItem("tendersignal-signups") || "[]");
    if (!signups.includes(email)) signups.push(email);
    localStorage.setItem("tendersignal-signups", JSON.stringify(signups));
    elements.alertMessage.textContent = t("saved");
    elements.alertForm.reset();
  });
}

async function init() {
  try {
    const response = await fetch("data/opportunities.json");
    if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
    state.opportunities = await response.json();
    updateLanguage();
    loadProfile();
    bindEvents();
    render();
  } catch (error) {
    console.error(error);
    elements.summary.textContent = "Unable to load demonstration data. Run the site through a local web server.";
  }
}

init();
