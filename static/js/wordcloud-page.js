(function () {
  const form = document.getElementById("category-form");
  const categoryInput = document.getElementById("category-input");
  const topInput = document.getElementById("top-input");
  const minLengthInput = document.getElementById("min-length-input");
  const refreshInput = document.getElementById("refresh-input");
  const paletteInput = document.getElementById("palette-input");
  const palettePreview = document.getElementById("palette-preview");
  const generateBtn = document.getElementById("generate-btn");
  const statusEl = document.getElementById("status");
  const statsEl = document.getElementById("stats");
  const cloudWrap = document.querySelector(".cloud-wrap");
  const canvas = document.getElementById("wordcloud-canvas");
  const placeholder = document.getElementById("cloud-placeholder");

  const statCategory = document.getElementById("stat-category");
  const statPages = document.getElementById("stat-pages");
  const statUnique = document.getElementById("stat-unique");
  const statSource = document.getElementById("stat-source");

  const palettesDataEl = document.getElementById("palettes-data");
  const popularDataEl = document.getElementById("popular-categories-data");
  const suggestionsList = document.getElementById("category-suggestions");
  const combobox = document.getElementById("category-combobox");

  const PALETTE_OPTIONS = palettesDataEl
    ? JSON.parse(palettesDataEl.textContent)
    : [];
  const POPULAR_CATEGORIES = popularDataEl
    ? JSON.parse(popularDataEl.textContent)
    : [];

  const palettesByName = Object.fromEntries(
    PALETTE_OPTIONS.map((p) => [p.name, p.colors])
  );

  let activeColors = palettesByName[paletteInput?.value] || [
    "#60a5fa", "#34d399", "#a78bfa", "#f472b6", "#fbbf24", "#38bdf8",
  ];
  let lastWords = null;

  let suggestionItems = [];
  let activeSuggestionIndex = -1;
  let suggestTimer = null;
  let suggestRequestId = 0;

  function hideSuggestions() {
    if (!suggestionsList) return;
    suggestionsList.hidden = true;
    suggestionsList.innerHTML = "";
    suggestionItems = [];
    activeSuggestionIndex = -1;
    categoryInput.setAttribute("aria-expanded", "false");
  }

  function showSuggestions(items, hint) {
    if (!suggestionsList) return;
    suggestionsList.innerHTML = "";
    suggestionItems = [];

    if (hint) {
      const hintEl = document.createElement("li");
      hintEl.className = "is-hint";
      hintEl.textContent = hint;
      hintEl.setAttribute("role", "presentation");
      suggestionsList.appendChild(hintEl);
    }

    items.forEach((label, index) => {
      const li = document.createElement("li");
      li.textContent = label;
      li.setAttribute("role", "option");
      li.id = "category-option-" + index;
      li.addEventListener("mousedown", function (e) {
        e.preventDefault();
        selectSuggestion(label);
      });
      suggestionsList.appendChild(li);
      suggestionItems.push(li);
    });

    suggestionsList.hidden = items.length === 0 && !hint;
    categoryInput.setAttribute(
      "aria-expanded",
      suggestionsList.hidden ? "false" : "true"
    );
  }

  function highlightSuggestion(index) {
    suggestionItems.forEach((li, i) => {
      li.classList.toggle("is-active", i === index);
      if (i === index) {
        categoryInput.setAttribute("aria-activedescendant", li.id);
      }
    });
    activeSuggestionIndex = index;
  }

  function selectSuggestion(value) {
    categoryInput.value = value;
    hideSuggestions();
    categoryInput.focus();
  }

  function filterPopular(query) {
    const q = query.trim().toLowerCase();
    if (!q) return POPULAR_CATEGORIES.slice();
    return POPULAR_CATEGORIES.filter((cat) => cat.toLowerCase().includes(q));
  }

  async function fetchSuggestions(query) {
    const q = query.trim();
    if (q.length < 2) {
      const popular = filterPopular(q);
      showSuggestions(
        popular,
        popular.length ? "Popular categories" : null
      );
      return;
    }

    const requestId = ++suggestRequestId;
    try {
      const params = new URLSearchParams({ q: q, limit: "10" });
      const res = await fetch("/api/category-suggestions?" + params.toString());
      const data = await res.json();
      if (requestId !== suggestRequestId) return;

      if (!res.ok) {
        showSuggestions(filterPopular(q), "Could not load suggestions");
        return;
      }

      const items = data.suggestions || [];
      showSuggestions(
        items,
        items.length ? "Wikipedia categories" : "No matching categories"
      );
    } catch (_err) {
      if (requestId !== suggestRequestId) return;
      showSuggestions(filterPopular(q), "Offline — showing popular categories");
    }
  }

  function scheduleSuggestions() {
    clearTimeout(suggestTimer);
    suggestTimer = setTimeout(function () {
      fetchSuggestions(categoryInput.value);
    }, 280);
  }

  function setupCategoryAutocomplete() {
    if (!categoryInput || !suggestionsList) return;

    categoryInput.addEventListener("input", function () {
      scheduleSuggestions();
    });

    categoryInput.addEventListener("focus", function () {
      fetchSuggestions(categoryInput.value);
    });

    categoryInput.addEventListener("blur", function () {
      setTimeout(hideSuggestions, 150);
    });

    categoryInput.addEventListener("keydown", function (e) {
      const selectable = suggestionItems;
      if (!selectable.length) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = activeSuggestionIndex < selectable.length - 1
          ? activeSuggestionIndex + 1
          : 0;
        highlightSuggestion(next);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = activeSuggestionIndex > 0
          ? activeSuggestionIndex - 1
          : selectable.length - 1;
        highlightSuggestion(prev);
      } else if (e.key === "Enter" && activeSuggestionIndex >= 0) {
        e.preventDefault();
        selectSuggestion(selectable[activeSuggestionIndex].textContent);
      } else if (e.key === "Escape") {
        hideSuggestions();
      }
    });

    document.addEventListener("click", function (e) {
      if (combobox && !combobox.contains(e.target)) {
        hideSuggestions();
      }
    });
  }

  function setStatus(message, kind) {
    statusEl.textContent = message;
    statusEl.className = "status" + (kind ? " status--" + kind : "");
  }

  function updatePalettePreview() {
    if (!palettePreview) return;
    palettePreview.innerHTML = "";
    activeColors.forEach((hex) => {
      const swatch = document.createElement("span");
      swatch.className = "palette-swatch";
      swatch.style.backgroundColor = hex;
      swatch.title = hex;
      palettePreview.appendChild(swatch);
    });
  }

  function applyPalette(name) {
    if (palettesByName[name]) {
      activeColors = palettesByName[name];
      updatePalettePreview();
    }
  }

  function sourceLabel(data) {
    if (data.source === "results_cache") {
      return "Cached frequencies (.wikicache/results)";
    }
    if (data.retrieval === "retrieval_cache") {
      return "Computed from cached page text";
    }
    if (data.retrieval === "mixed") {
      return "Computed (partial cache + API)";
    }
    return "Computed from Wikipedia API";
  }

  function buildWordList(words) {
    if (!words.length) return [];
    const counts = words.map((w) => w.count);
    const max = Math.max(...counts);
    const min = Math.min(...counts);
    const minSize = 14;
    const maxSize = 72;

    return words.map((entry) => {
      let size;
      if (max === min) {
        size = (minSize + maxSize) / 2;
      } else {
        const t = (entry.count - min) / (max - min);
        size = minSize + t * (maxSize - minSize);
      }
      return [entry.word, Math.round(size)];
    });
  }

  function renderWordCloud(words) {
    if (typeof WordCloud === "undefined") {
      setStatus("Word cloud library failed to load.", "error");
      return;
    }

    const list = buildWordList(words);
    const rect = cloudWrap.getBoundingClientRect();
    const width = Math.max(640, Math.floor(rect.width));
    const height = Math.max(400, Math.min(560, Math.floor(width * 0.55)));

    canvas.width = width;
    canvas.height = height;

    WordCloud(canvas, {
      list: list,
      gridSize: Math.round(8 * (width / 1024)),
      weightFactor: 1,
      fontFamily: "Segoe UI, system-ui, sans-serif",
      color: function () {
        return activeColors[Math.floor(Math.random() * activeColors.length)];
      },
      rotateRatio: 0.35,
      rotationSteps: 2,
      backgroundColor: "#1a2332",
      shrinkToFit: true,
      drawOutOfBound: false,
    });

    cloudWrap.classList.add("has-cloud");
    placeholder.hidden = true;
  }

  async function loadFrequencies() {
    const category = categoryInput.value.trim();
    if (!category) {
      setStatus("Please enter a category name.", "error");
      return;
    }

    const params = new URLSearchParams({
      category: category,
      top: topInput.value || "120",
      min_length: minLengthInput.value || "2",
    });
    if (refreshInput.checked) {
      params.set("refresh", "1");
    }

    generateBtn.disabled = true;
    setStatus("Loading frequencies… This may take a while on first run.");

    try {
      const res = await fetch("/api/frequencies?" + params.toString());
      const data = await res.json();

      if (!res.ok) {
        setStatus(data.error || "Request failed.", "error");
        statsEl.hidden = true;
        return;
      }

      statCategory.textContent = data.category;
      statPages.textContent = String(data.pages_analyzed);
      statUnique.textContent = String(data.unique_words);
      statSource.textContent = sourceLabel(data);
      statsEl.hidden = false;

      setStatus(
        "Showing " + data.words.length + " words (" +
        data.total_occurrences.toLocaleString() + " total occurrences).",
        "ok"
      );

      lastWords = data.words;
      renderWordCloud(lastWords);
    } catch (err) {
      setStatus("Network error: " + err.message, "error");
      statsEl.hidden = true;
    } finally {
      generateBtn.disabled = false;
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    loadFrequencies();
  });

  if (paletteInput) {
    paletteInput.addEventListener("change", function () {
      applyPalette(paletteInput.value);
      if (lastWords) {
        renderWordCloud(lastWords);
      }
    });
    applyPalette(paletteInput.value);
  }

  setupCategoryAutocomplete();

  if (categoryInput.value.trim()) {
    loadFrequencies();
  }
})();
