/* global API */

(function () {
  "use strict";

  const state = {
    view: "dashboard",
    user: null,
    users: [],
    fields: [],
    regions: [],
    satellites: [],
    cropCycles: [],
    observations: [],
    weather: [],
    alerts: [],
    bandValues: [],
    derivedMetrics: [],
    loading: false,
  };

  const VIEWS = {
    dashboard: { title: "Dashboard", subtitle: "🌻 Overview & quick actions", emoji: "📊" },
    profile: { title: "Profile", subtitle: "🪪 Your account, photo, and preferences", emoji: "🪪" },
    fields: { title: "Fields", subtitle: "🌾 Parcels, soil, and coordinates", emoji: "🌾" },
    crop_cycles: { title: "Crop cycles", subtitle: "🌱 Planting, harvest, and yield", emoji: "🌱" },
    regions: { title: "Regions", subtitle: "🗺️ Climate zones", emoji: "🗺️" },
    satellites: { title: "Satellites", subtitle: "🛰️ Imagery sources", emoji: "🛰️" },
    observations: { title: "Observations", subtitle: "👁️ Satellite passes & cloud cover", emoji: "👁️" },
    weather: { title: "Weather", subtitle: "☀️🌧️ Field-level weather records", emoji: "☁️" },
    alerts: { title: "Alerts", subtitle: "🚨 Risks and field warnings", emoji: "🚨" },
    band_values: { title: "Band values", subtitle: "🎚️ Raw spectral bands", emoji: "🎚️" },
    derived_metrics: { title: "Derived metrics", subtitle: "📈 NDVI, EVI, soil moisture", emoji: "📈" },
    users: { title: "Users", subtitle: "👥 People & roles (RBAC)", emoji: "👥" },
  };

  const APP_BRAND = "HarvestHUB";
  const THEME_KEY = "harvesthub_theme";

  function applyBranding() {
    document.title = APP_BRAND + " — Smart Agriculture Console";
    document.querySelectorAll(".sidebar-brand h2, .auth-brand h1, .harvest-intro__title").forEach((el) => {
      el.textContent = APP_BRAND;
    });
  }

  function getTheme() {
    const v = localStorage.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : "dark";
  }

  function setTheme(theme) {
    const t = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", t);
    try {
      localStorage.setItem(THEME_KEY, t);
    } catch (_) {
      /* ignore */
    }
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.setAttribute("aria-label", t === "dark" ? "Switch to light mode" : "Switch to dark mode");
      btn.title = t === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }
  }

  function initTheme() {
    setTheme(getTheme());
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", () => {
        setTheme(getTheme() === "dark" ? "light" : "dark");
      });
    }
  }

  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function displayName(user) {
    if (!user) return "User";
    return user.name || user.email || "User";
  }

  function initialsFromName(name) {
    const parts = String(name || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2);
    if (!parts.length) return "?";
    return parts.map((part) => part[0]).join("").toUpperCase();
  }

  function avatarUrl(user) {
    return user && user.avatar_url ? API.resolveUrl(user.avatar_url) : "";
  }

  function setAvatarContent(el, user, fallbackName) {
    if (!el) return;
    const src = avatarUrl(user);
    if (src) {
      el.classList.add("has-image");
      el.innerHTML = `<img src="${escapeHtml(src)}" alt="${escapeHtml(fallbackName || "User avatar")}" />`;
      return;
    }
    el.classList.remove("has-image");
    el.textContent = initialsFromName(fallbackName || displayName(user));
  }

  function persistCurrentUser() {
    if (!state.user) return;
    localStorage.setItem(API.STORAGE_USER, JSON.stringify(state.user));
  }

  function syncUserCaches(updatedUser) {
    if (!updatedUser) return;
    state.user = { ...state.user, ...updatedUser };
    const idx = state.users.findIndex((user) => user.user_id === updatedUser.user_id);
    if (idx >= 0) {
      state.users[idx] = { ...state.users[idx], ...updatedUser };
    }
    persistCurrentUser();
    updateUserChip();
  }

  function formatTimestamp(value) {
    if (!value) return "Recently";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  function valueOrDash(value) {
    return value === undefined || value === null || value === "" ? "—" : value;
  }

  function uid() {
    return state.user && state.user.user_id;
  }

  function isAdmin() {
    return state.user && state.user.role === "admin";
  }
  function isAgronomist() {
    return state.user && state.user.role === "agronomist";
  }
  function isFarmer() {
    return state.user && state.user.role === "farmer";
  }

  function canCreateField() {
    return isAdmin();
  }
  function canCreateCropCycle() {
    return isAdmin() || isAgronomist();
  }
  function canCreateRegion() {
    return isAdmin();
  }
  function canCreateSatellite() {
    return isAdmin();
  }
  function canCreateObservation() {
    return isAdmin();
  }
  function canCreateWeather() {
    return isAdmin();
  }
  function canCreateAlert() {
    return isAdmin() || isAgronomist();
  }
  function canResolveAlert() {
    return isAdmin() || isAgronomist();
  }
  function canCreateBandValue() {
    return isAdmin();
  }
  function canCreateDerivedMetric() {
    return isAdmin();
  }
  function canManageAdminResource() {
    return isAdmin();
  }
  function canEditField(f) {
    if (!f) return false;
    if (isAdmin() || isAgronomist()) return true;
    return isFarmer() && f.user_id === uid();
  }
  function canDeleteField(f) {
    if (!f) return false;
    if (isAgronomist()) return false;
    if (isAdmin()) return true;
    return isFarmer() && f.user_id === uid();
  }
  function canDeleteCropCycle(c) {
    if (!c) return false;
    if (isAgronomist()) return false;
    if (isAdmin()) return true;
    if (!isFarmer()) return false;
    const field = state.fields.find((x) => x.id === c.field_id);
    return field && field.user_id === uid();
  }
  function canEditCropCycle(c) {
    if (!c) return false;
    if (isAdmin() || isAgronomist()) return true;
    if (!isFarmer()) return false;
    const field = state.fields.find((x) => x.id === c.field_id);
    return field && field.user_id === uid();
  }

  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    const c = document.getElementById("toast-container");
    c.appendChild(el);
    setTimeout(() => {
      el.remove();
    }, 4200);
  }

  function omitEmpty(obj) {
    const o = {};
    Object.entries(obj).forEach(([k, v]) => {
      if (v === "" || v === undefined || v === null) return;
      o[k] = v;
    });
    return o;
  }

  function showAuth() {
    document.getElementById("auth-screen").classList.remove("hidden");
    document.getElementById("app-shell").classList.add("hidden");
  }

  function showApp() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
  }

  function closeModal() {
    const root = document.getElementById("modal-root");
    root.classList.add("hidden");
    document.getElementById("modal-body").innerHTML = "";
    document.getElementById("modal-footer").innerHTML = "";
  }

  function openModal(title, bodyHtml, footerHtml) {
    document.getElementById("modal-title").textContent = title;
    document.getElementById("modal-body").innerHTML = bodyHtml;
    document.getElementById("modal-footer").innerHTML = footerHtml || "";
    document.getElementById("modal-root").classList.remove("hidden");
  }

  document.getElementById("modal-root").addEventListener("click", (e) => {
    if (e.target.dataset.close) closeModal();
  });

  function updateUserChip() {
    const u = state.user;
    const nameEl = document.getElementById("user-name");
    const roleEl = document.getElementById("user-role");
    const av = document.getElementById("user-avatar");
    if (!u) {
      nameEl.textContent = "—";
      roleEl.textContent = "—";
      av.classList.remove("has-image");
      av.textContent = "?";
      return;
    }
    const full = state.users.find((x) => x.user_id === u.user_id);
    const resolvedUser = full ? { ...u, ...full } : u;
    const resolvedName = displayName(resolvedUser);
    nameEl.textContent = resolvedName;
    roleEl.textContent = u.role || "";
    setAvatarContent(av, resolvedUser, resolvedName);
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === view);
    });
    const meta = VIEWS[view] || VIEWS.dashboard;
    document.getElementById("view-title").textContent = meta.title;
    document.getElementById("view-subtitle").textContent = meta.subtitle;

    const newBtn = document.getElementById("new-btn");
    const newLabel = document.getElementById("new-btn-label");
    const map = {
      fields: ["New field", canCreateField()],
      regions: ["New region", canCreateRegion()],
      crop_cycles: ["New crop cycle", canCreateCropCycle()],
      satellites: ["New satellite", canCreateSatellite()],
      observations: ["New observation", canCreateObservation()],
      weather: ["New weather", canCreateWeather()],
      alerts: ["New alert", canCreateAlert()],
      band_values: ["New band value", canCreateBandValue()],
      derived_metrics: ["New metric", canCreateDerivedMetric()],
    };
    const cfg = map[view];
    if (cfg && cfg[1]) {
      newBtn.classList.remove("hidden");
      newLabel.textContent = cfg[0];
    } else {
      newBtn.classList.add("hidden");
    }
    renderView();
  }

  async function bootstrapSession() {
    const token = localStorage.getItem(API.STORAGE_TOKEN);
    const raw = localStorage.getItem(API.STORAGE_USER);
    if (!token || !raw) {
      showAuth();
      return;
    }
    try {
      state.user = JSON.parse(raw);
      await refreshProfile();
      showApp();
      setView(state.view || "dashboard");
    } catch {
      localStorage.removeItem(API.STORAGE_TOKEN);
      localStorage.removeItem(API.STORAGE_USER);
      showAuth();
    }
  }

  function dismissHarvestIntro(immediate) {
    const el = document.getElementById("harvest-intro");
    if (!el || el.dataset.dismissed === "1") return Promise.resolve();
    el.dataset.dismissed = "1";
    el.setAttribute("aria-hidden", "true");
    if (immediate) {
      el.classList.add("harvest-intro--gone");
      return Promise.resolve();
    }
    el.classList.add("harvest-intro--exiting");
    return new Promise((resolve) => {
      const done = () => {
        el.classList.add("harvest-intro--gone");
        resolve();
      };
      el.addEventListener("transitionend", done, { once: true });
      setTimeout(done, 900);
    });
  }

  async function runHarvestIntroThenBootstrap() {
    const token = localStorage.getItem(API.STORAGE_TOKEN);
    const raw = localStorage.getItem(API.STORAGE_USER);
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (token && raw) {
      await dismissHarvestIntro(true);
      await bootstrapSession();
      return;
    }

    const holdMs = reduced ? 800 : 2800;
    await new Promise((r) => setTimeout(r, holdMs));
    await dismissHarvestIntro(reduced);
    await bootstrapSession();
  }

  async function refreshProfile() {
    if (!state.user || !state.user.user_id) return;
    try {
      const profile = await API.request("/api/users/me");
      syncUserCaches(profile);
    } catch {
      /* keep login payload */
    }
    updateUserChip();
  }

  async function loadUsersList() {
    const res = await API.request("/api/users/");
    state.users = res.users || [];
  }

  async function loadFields() {
    const res = await API.request("/api/fields/");
    state.fields = res.fields || [];
  }

  async function loadRegions() {
    const res = await API.request("/api/regions/");
    state.regions = res.regions || [];
  }

  async function loadSatellites() {
    const res = await API.request("/api/satellites/");
    state.satellites = res.satellites || [];
  }

  async function loadCropCycles() {
    const res = await API.request("/api/crop-cycles/");
    state.cropCycles = res.crop_cycles || [];
  }

  async function loadObservations() {
    const res = await API.request("/api/observations/");
    state.observations = res.observations || [];
  }

  async function loadWeather() {
    const res = await API.request("/api/weather/");
    state.weather = res.weather || [];
  }

  async function loadAlerts() {
    const res = await API.request("/api/alerts/");
    state.alerts = res.alerts || [];
    const unr = state.alerts.filter((a) => !a.is_resolved).length;
    const badge = document.getElementById("alert-badge");
    if (unr > 0) {
      badge.hidden = false;
      badge.textContent = unr > 99 ? "99+" : String(unr);
    } else {
      badge.hidden = true;
    }
  }

  async function loadBandValues() {
    const res = await API.request("/api/band-values/");
    state.bandValues = res.band_values || [];
  }

  async function loadDerivedMetrics() {
    const res = await API.request("/api/derived-metrics/");
    state.derivedMetrics = res.derived_metrics || [];
  }

  function regionName(id) {
    const r = state.regions.find((x) => x.id === id);
    return r ? r.region_name : id;
  }

  function fieldLabel(id) {
    const f = state.fields.find((x) => x.id === id);
    return f ? `${f.field_name} (#${f.id})` : `#${id}`;
  }

  /* ---------- Modals: forms ---------- */

  async function openFieldCreateModal() {
    try {
      await loadUsersList();
      await loadRegions();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.users.length) {
      toast("No users found — register a user first.", "error");
      return;
    }
    if (!state.regions.length) {
      toast("Create at least one region before adding fields.", "error");
      return;
    }
    const userOpts = state.users
      .map(
        (u) =>
          `<option value="${u.user_id}">${escapeHtml(u.name)} (${escapeHtml(u.email)})</option>`
      )
      .join("");
    const regOpts = state.regions
      .map((r) => `<option value="${r.id}">${escapeHtml(r.region_name)}</option>`)
      .join("");
    openModal(
      "Create field",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field name</span><input name="field_name" required placeholder="North plot" /></label>
        <label class="field"><span>Owner (user)</span><select name="user_id" required>${userOpts}</select></label>
        <label class="field"><span>Region</span><select name="region_id" required>${regOpts}</select></label>
        <label class="field"><span>Latitude</span><input name="latitude" type="number" step="any" required /></label>
        <label class="field"><span>Longitude</span><input name="longitude" type="number" step="any" required /></label>
        <label class="field"><span>Area (ha)</span><input name="area" type="number" step="any" required /></label>
        <label class="field full"><span>Soil type</span><input name="soil_type" required placeholder="loamy" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        field_name: fd.get("field_name"),
        user_id: Number(fd.get("user_id")),
        region_id: Number(fd.get("region_id")),
        latitude: Number(fd.get("latitude")),
        longitude: Number(fd.get("longitude")),
        area: Number(fd.get("area")),
        soil_type: fd.get("soil_type"),
      };
      try {
        await API.request("/api/fields/", { method: "POST", body: JSON.stringify(body) });
        toast("Field created", "success");
        closeModal();
        await loadFields();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  function openFieldEditModal(field) {
    openModal(
      `Edit field #${field.id}`,
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field name</span><input name="field_name" value="${escapeHtml(
          field.field_name
        )}" /></label>
        <label class="field"><span>Area</span><input name="area" type="number" step="any" value="${escapeHtml(
          field.area
        )}" /></label>
        <label class="field full"><span>Soil type</span><input name="soil_type" value="${escapeHtml(
          field.soil_type
        )}" /></label>
        <label class="field"><span>Latitude</span><input name="latitude" type="number" step="any" value="${escapeHtml(
          field.latitude
        )}" /></label>
        <label class="field"><span>Longitude</span><input name="longitude" type="number" step="any" value="${escapeHtml(
          field.longitude
        )}" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Save</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = omitEmpty({
        field_name: fd.get("field_name"),
        area: fd.get("area") ? Number(fd.get("area")) : undefined,
        soil_type: fd.get("soil_type") || undefined,
        latitude: fd.get("latitude") !== "" ? Number(fd.get("latitude")) : undefined,
        longitude: fd.get("longitude") !== "" ? Number(fd.get("longitude")) : undefined,
      });
      try {
        await API.request(`/api/fields/${field.id}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        toast("Field updated", "success");
        closeModal();
        await loadFields();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  function openRegionCreateModal() {
    openModal(
      "Create region",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Region name</span><input name="region_name" required /></label>
        <label class="field full"><span>Climate type</span><input name="climate_type" required placeholder="temperate" /></label>
        <label class="field"><span>Latitude (opt)</span><input name="latitude" type="number" step="any" /></label>
        <label class="field"><span>Longitude (opt)</span><input name="longitude" type="number" step="any" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = omitEmpty({
        region_name: fd.get("region_name"),
        climate_type: fd.get("climate_type"),
        latitude: fd.get("latitude") !== "" ? Number(fd.get("latitude")) : undefined,
        longitude: fd.get("longitude") !== "" ? Number(fd.get("longitude")) : undefined,
      });
      try {
        await API.request("/api/regions/", { method: "POST", body: JSON.stringify(body) });
        toast("Region created", "success");
        closeModal();
        await loadRegions();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openCropCycleCreateModal() {
    try {
      await loadFields();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.fields.length) {
      toast("No fields available.", "error");
      return;
    }
    const fopts = state.fields
      .map((f) => `<option value="${f.id}">${escapeHtml(f.field_name)} (#${f.id})</option>`)
      .join("");
    openModal(
      "New crop cycle",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field</span><select name="field_id" required>${fopts}</select></label>
        <label class="field full"><span>Crop name</span><input name="crop_name" required placeholder="wheat" /></label>
        <label class="field"><span>Start date</span><input name="start_date" required placeholder="2025-03-01" /></label>
        <label class="field"><span>Expected harvest</span><input name="expected_harvest_date" required placeholder="2025-08-01" /></label>
        <label class="field full"><span>Yield prediction</span><input name="yield_prediction" type="number" step="any" required value="0" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        field_id: Number(fd.get("field_id")),
        crop_name: fd.get("crop_name"),
        start_date: fd.get("start_date"),
        expected_harvest_date: fd.get("expected_harvest_date"),
        yield_prediction: Number(fd.get("yield_prediction") || 0),
      };
      try {
        await API.request("/api/crop-cycles/", { method: "POST", body: JSON.stringify(body) });
        toast("Crop cycle created", "success");
        closeModal();
        await loadCropCycles();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  function openCropCycleEditModal(c) {
    openModal(
      `Update cycle #${c.id}`,
      `<form id="dyn-form" class="form-grid">
        <label class="field"><span>Status</span><input name="status" placeholder="active" value="${escapeHtml(
          c.status || ""
        )}" /></label>
        <label class="field"><span>Actual harvest date</span><input name="actual_harvest_date" value="${escapeHtml(
          c.actual_harvest_date || ""
        )}" /></label>
        <label class="field full"><span>Actual yield</span><input name="actual_yield" type="number" step="any" value="${
          c.actual_yield != null ? escapeHtml(c.actual_yield) : ""
        }" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Save</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = omitEmpty({
        status: fd.get("status") || undefined,
        actual_harvest_date: fd.get("actual_harvest_date") || undefined,
        actual_yield:
          fd.get("actual_yield") !== "" && fd.get("actual_yield") != null
            ? Number(fd.get("actual_yield"))
            : undefined,
      });
      try {
        await API.request(`/api/crop-cycles/${c.id}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        toast("Crop cycle updated", "success");
        closeModal();
        await loadCropCycles();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  function openSatelliteCreateModal() {
    openModal(
      "New satellite",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Name</span><input name="satellite_name" required /></label>
        <label class="field"><span>Provider</span><input name="provider" required placeholder="NASA" /></label>
        <label class="field"><span>Resolution (m)</span><input name="resolution" type="number" step="any" required /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        satellite_name: fd.get("satellite_name"),
        provider: fd.get("provider"),
        resolution: Number(fd.get("resolution")),
      };
      try {
        await API.request("/api/satellites/", { method: "POST", body: JSON.stringify(body) });
        toast("Satellite created", "success");
        closeModal();
        await loadSatellites();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openObservationCreateModal() {
    try {
      await loadFields();
      await loadSatellites();
      await loadCropCycles();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.fields.length || !state.satellites.length || !state.cropCycles.length) {
      toast("Need at least one field, satellite, and crop cycle.", "error");
      return;
    }
    const fopts = state.fields.map((f) => `<option value="${f.id}">#${f.id} ${escapeHtml(f.field_name)}</option>`).join("");
    const sopts = state.satellites
      .map((s) => `<option value="${s.id}">${escapeHtml(s.satellite_name)}</option>`)
      .join("");
    const copts = state.cropCycles.map((c) => `<option value="${c.id}">#${c.id} ${escapeHtml(c.crop_name)}</option>`).join("");
    openModal(
      "New observation",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field</span><select name="field_id" required>${fopts}</select></label>
        <label class="field full"><span>Satellite</span><select name="satellite_id" required>${sopts}</select></label>
        <label class="field full"><span>Crop cycle</span><select name="cycle_id" required>${copts}</select></label>
        <label class="field"><span>Observation date</span><input name="observation_date" required placeholder="2025-05-01" /></label>
        <label class="field"><span>Cloud cover (0–1)</span><input name="cloud_cover" type="number" step="any" required value="0.1" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        field_id: Number(fd.get("field_id")),
        satellite_id: Number(fd.get("satellite_id")),
        cycle_id: Number(fd.get("cycle_id")),
        observation_date: fd.get("observation_date"),
        cloud_cover: Number(fd.get("cloud_cover")),
      };
      try {
        await API.request("/api/observations/", { method: "POST", body: JSON.stringify(body) });
        toast("Observation created", "success");
        closeModal();
        await loadObservations();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openWeatherCreateModal() {
    try {
      await loadFields();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.fields.length) {
      toast("No fields available.", "error");
      return;
    }
    const fopts = state.fields.map((f) => `<option value="${f.id}">#${f.id} ${escapeHtml(f.field_name)}</option>`).join("");
    openModal(
      "New weather record",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field</span><select name="field_id" required>${fopts}</select></label>
        <label class="field"><span>Date</span><input name="date" required placeholder="2025-05-01" /></label>
        <label class="field"><span>Temperature</span><input name="temperature" required placeholder="28C" /></label>
        <label class="field"><span>Rainfall</span><input name="rainfall" required placeholder="0mm" /></label>
        <label class="field"><span>Humidity</span><input name="humidity" required placeholder="65%" /></label>
        <label class="field"><span>Wind speed</span><input name="wind_speed" placeholder="12" /></label>
        <label class="field"><span>Wind direction</span><input name="wind_direction" placeholder="NE" /></label>
        <label class="field full"><span>Pressure</span><input name="pressure" placeholder="1013" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = omitEmpty({
        field_id: Number(fd.get("field_id")),
        date: fd.get("date"),
        temperature: fd.get("temperature"),
        rainfall: fd.get("rainfall"),
        humidity: fd.get("humidity"),
        wind_speed: fd.get("wind_speed") || undefined,
        wind_direction: fd.get("wind_direction") || undefined,
        pressure: fd.get("pressure") || undefined,
      });
      try {
        await API.request("/api/weather/", { method: "POST", body: JSON.stringify(body) });
        toast("Weather saved", "success");
        closeModal();
        await loadWeather();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openAlertCreateModal() {
    try {
      await loadFields();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.fields.length) {
      toast("No fields available.", "error");
      return;
    }
    const fopts = state.fields.map((f) => `<option value="${f.id}">#${f.id} ${escapeHtml(f.field_name)}</option>`).join("");
    openModal(
      "New alert",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Field</span><select name="field_id" required>${fopts}</select></label>
        <label class="field"><span>Alert type</span><input name="alert_type" required placeholder="WATER_STRESS" /></label>
        <label class="field"><span>Severity</span><input name="severity" required placeholder="HIGH" /></label>
        <label class="field full"><span>Message</span><textarea name="message" required rows="3"></textarea></label>
        <label class="field full"><span>Observation ID (optional)</span><input name="observation_id" type="number" placeholder="leave empty if none" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const oid = fd.get("observation_id");
      const body = omitEmpty({
        field_id: Number(fd.get("field_id")),
        alert_type: fd.get("alert_type"),
        severity: fd.get("severity"),
        message: fd.get("message"),
        observation_id: oid ? Number(oid) : undefined,
      });
      try {
        await API.request("/api/alerts/", { method: "POST", body: JSON.stringify(body) });
        toast("Alert created", "success");
        closeModal();
        await loadAlerts();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openBandValueCreateModal() {
    try {
      await loadObservations();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.observations.length) {
      toast("Create an observation first.", "error");
      return;
    }
    const oopts = state.observations.map((o) => `<option value="${o.id}">#${o.id} field ${o.field_id}</option>`).join("");
    openModal(
      "New band value",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Observation</span><select name="observation_id" required>${oopts}</select></label>
        <label class="field"><span>Band name</span><input name="band_name" required placeholder="NIR" /></label>
        <label class="field"><span>Value</span><input name="band_value" type="number" step="any" required /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        observation_id: Number(fd.get("observation_id")),
        band_name: fd.get("band_name"),
        band_value: Number(fd.get("band_value")),
      };
      try {
        await API.request("/api/band-values/", { method: "POST", body: JSON.stringify(body) });
        toast("Band value created", "success");
        closeModal();
        await loadBandValues();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function openDerivedMetricCreateModal() {
    try {
      await loadObservations();
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!state.observations.length) {
      toast("Create an observation first.", "error");
      return;
    }
    const oopts = state.observations.map((o) => `<option value="${o.id}">#${o.id}</option>`).join("");
    openModal(
      "New derived metrics row",
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Observation</span><select name="observation_id" required>${oopts}</select></label>
        <label class="field"><span>NDVI</span><input name="ndvi" type="number" step="any" required value="0.5" /></label>
        <label class="field"><span>EVI</span><input name="evi" type="number" step="any" required value="0.4" /></label>
        <label class="field"><span>Soil moisture</span><input name="soil_moisture" type="number" step="any" required value="0.3" /></label>
        <label class="field full"><span>Crop health score</span><input name="crop_health_score" type="number" step="any" required value="0.8" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Create</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = {
        observation_id: Number(fd.get("observation_id")),
        ndvi: Number(fd.get("ndvi")),
        evi: Number(fd.get("evi")),
        soil_moisture: Number(fd.get("soil_moisture")),
        crop_health_score: Number(fd.get("crop_health_score")),
      };
      try {
        await API.request("/api/derived-metrics/", { method: "POST", body: JSON.stringify(body) });
        toast("Derived metric created", "success");
        closeModal();
        await loadDerivedMetrics();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  function openUserEditModal(u) {
    openModal(
      `Edit user #${u.user_id}`,
      `<form id="dyn-form" class="form-grid">
        <label class="field full"><span>Name</span><input name="name" value="${escapeHtml(u.name)}" /></label>
        <label class="field full"><span>Email</span><input name="email" type="email" value="${escapeHtml(u.email)}" /></label>
      </form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Save</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      const fd = new FormData(document.getElementById("dyn-form"));
      const body = omitEmpty({ name: fd.get("name") || undefined, email: fd.get("email") || undefined });
      try {
        await API.request(`/api/users/${u.user_id}`, { method: "PUT", body: JSON.stringify(body) });
        toast("User updated", "success");
        closeModal();
        await loadUsersList();
        await refreshProfile();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function showJsonModal(title, promise) {
    openModal(title, `<pre class="muted" style="margin:0;font-size:0.78rem;white-space:pre-wrap;max-height:60vh;overflow:auto;">Loading…</pre>`, `<button type="button" class="btn btn-secondary" data-close="1">Close</button>`);
    const pre = document.querySelector("#modal-body pre");
    try {
      const data = await promise;
      pre.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      pre.textContent = e.message;
    }
  }

  function renderModalField(field, value) {
    const cls = field.full ? "field full" : "field";
    if (field.type === "checkbox") {
      return `<label class="${cls}"><span>${field.label}</span><input name="${field.name}" type="checkbox" ${
        value ? "checked" : ""
      } /></label>`;
    }
    const type = field.type || "text";
    const step = field.step ? ` step="${field.step}"` : "";
    const placeholder = field.placeholder ? ` placeholder="${escapeHtml(field.placeholder)}"` : "";
    const safeValue = value == null ? "" : escapeHtml(value);
    return `<label class="${cls}"><span>${field.label}</span><input name="${field.name}" type="${type}"${step}${placeholder} value="${safeValue}" /></label>`;
  }

  function normalizeFieldValue(field, value) {
    if (field.type === "checkbox") return Boolean(value);
    if (field.type === "number") {
      if (value === "" || value == null) return undefined;
      return Number(value);
    }
    return value == null ? "" : String(value);
  }

  function readModalFieldValue(field, formEl) {
    const input = formEl.querySelector(`[name="${field.name}"]`);
    if (!input) return undefined;
    if (field.type === "checkbox") return input.checked;
    if (input.value === "") return undefined;
    return field.type === "number" ? Number(input.value) : input.value;
  }

  async function patchRecordCells(basePath, recordId, fields, originalRecord, formEl) {
    const changes = [];
    fields.forEach((field) => {
      const nextValue = readModalFieldValue(field, formEl);
      const prevValue = normalizeFieldValue(field, originalRecord[field.name]);
      if (JSON.stringify(nextValue) === JSON.stringify(prevValue)) return;
      if (nextValue === undefined && prevValue === undefined) return;
      changes.push({ column_name: field.name, value: nextValue });
    });

    for (const change of changes) {
      await API.request(`${basePath}/${recordId}/cell`, {
        method: "PATCH",
        body: JSON.stringify(change),
      });
    }
    return changes.length;
  }

  function openAdminCellEditModal(config) {
    const { title, record, basePath, fields, successMessage, reload } = config;
    openModal(
      title,
      `<form id="dyn-form" class="form-grid">${fields
        .map((field) => renderModalField(field, record[field.name]))
        .join("")}</form>`,
      `<button type="button" class="btn btn-secondary" data-close="1">Cancel</button>
       <button type="button" class="btn btn-primary" id="dyn-submit">Save</button>`
    );
    document.getElementById("dyn-submit").onclick = async () => {
      try {
        const formEl = document.getElementById("dyn-form");
        const changeCount = await patchRecordCells(basePath, record.id, fields, record, formEl);
        if (!changeCount) {
          toast("No changes to save", "info");
          return;
        }
        toast(successMessage, "success");
        closeModal();
        await reload();
        renderView();
      } catch (e) {
        toast(e.message, "error");
      }
    };
  }

  async function deleteAdminResource(path, confirmMessage, successMessage, reload) {
    if (!confirm(confirmMessage)) return;
    try {
      await API.request(path, { method: "DELETE" });
      toast(successMessage, "success");
      await reload();
      renderView();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  function openRegionEditModal(region) {
    openAdminCellEditModal({
      title: `Edit region #${region.id}`,
      record: region,
      basePath: "/api/regions",
      fields: [
        { name: "region_name", label: "Region name", full: true },
        { name: "climate_type", label: "Climate type", full: true },
        { name: "latitude", label: "Latitude", type: "number", step: "any" },
        { name: "longitude", label: "Longitude", type: "number", step: "any" },
      ],
      successMessage: "Region updated",
      reload: loadRegions,
    });
  }

  function openSatelliteEditModal(satellite) {
    openAdminCellEditModal({
      title: `Edit satellite #${satellite.id}`,
      record: satellite,
      basePath: "/api/satellites",
      fields: [
        { name: "satellite_name", label: "Name", full: true },
        { name: "provider", label: "Provider", full: true },
        { name: "resolution", label: "Resolution (m)", type: "number", step: "any" },
      ],
      successMessage: "Satellite updated",
      reload: loadSatellites,
    });
  }

  function openObservationEditModal(observation) {
    openAdminCellEditModal({
      title: `Edit observation #${observation.id}`,
      record: observation,
      basePath: "/api/observations",
      fields: [
        { name: "observation_date", label: "Observation date", full: true },
        { name: "cloud_cover", label: "Cloud cover", type: "number", step: "any" },
        { name: "processed", label: "Processed", type: "checkbox" },
      ],
      successMessage: "Observation updated",
      reload: loadObservations,
    });
  }

  function openWeatherEditModal(weather) {
    openAdminCellEditModal({
      title: `Edit weather #${weather.id}`,
      record: weather,
      basePath: "/api/weather",
      fields: [
        { name: "date", label: "Date" },
        { name: "temperature", label: "Temperature" },
        { name: "rainfall", label: "Rainfall" },
        { name: "humidity", label: "Humidity" },
        { name: "wind_speed", label: "Wind speed" },
        { name: "wind_direction", label: "Wind direction" },
        { name: "pressure", label: "Pressure" },
      ],
      successMessage: "Weather updated",
      reload: loadWeather,
    });
  }

  function openBandValueEditModal(bandValue) {
    openAdminCellEditModal({
      title: `Edit band value #${bandValue.id}`,
      record: bandValue,
      basePath: "/api/band-values",
      fields: [
        { name: "band_name", label: "Band name", full: true },
        { name: "band_value", label: "Value", type: "number", step: "any" },
      ],
      successMessage: "Band value updated",
      reload: loadBandValues,
    });
  }

  function openDerivedMetricEditModal(metric) {
    openAdminCellEditModal({
      title: `Edit metric #${metric.id}`,
      record: metric,
      basePath: "/api/derived-metrics",
      fields: [
        { name: "ndvi", label: "NDVI", type: "number", step: "any" },
        { name: "evi", label: "EVI", type: "number", step: "any" },
        { name: "soil_moisture", label: "Soil moisture", type: "number", step: "any" },
        { name: "crop_health_score", label: "Crop health score", type: "number", step: "any", full: true },
      ],
      successMessage: "Derived metric updated",
      reload: loadDerivedMetrics,
    });
  }

  /* ---------- Renderers ---------- */

  function renderTable(headers, rowsHtml, emptyMsg) {
    if (!rowsHtml) {
      return `<div class="empty-state"><span class="empty-art" aria-hidden="true">🌱</span><p>${emptyMsg}</p></div>`;
    }
    return `<div class="table-wrap"><table class="data-table"><thead><tr>${headers
      .map((h) => `<th>${h}</th>`)
      .join("")}</tr></thead><tbody>${rowsHtml}</tbody></table></div>`;
  }

  function roleTag(role) {
    const r = String(role || "").toLowerCase();
    const cls =
      r === "admin" ? "tag-admin" : r === "agronomist" ? "tag-agronomist" : "tag-farmer";
    return `<span class="tag ${cls}">${escapeHtml(role)}</span>`;
  }

  async function saveProfileDetails() {
    const form = document.getElementById("profile-form");
    const fd = new FormData(form);
    const body = omitEmpty({
      name: fd.get("name") || undefined,
      email: fd.get("email") || undefined,
    });
    if (!Object.keys(body).length) {
      toast("No profile changes to save", "info");
      return;
    }
    const res = await API.request(`/api/users/${uid()}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
    syncUserCaches(res.user || {});
    toast("Profile updated", "success");
    renderView();
  }

  async function uploadProfileAvatar() {
    const input = document.getElementById("profile-avatar-file");
    const file = input && input.files ? input.files[0] : null;
    if (!file) {
      toast("Choose an image first", "error");
      return;
    }
    const formData = new FormData();
    formData.append("avatar", file);
    const res = await API.request("/api/users/me/avatar", {
      method: "POST",
      body: formData,
    });
    syncUserCaches(res.user || {});
    toast("Profile photo updated", "success");
    renderView();
  }

  async function removeProfileAvatar() {
    const res = await API.request("/api/users/me/avatar", { method: "DELETE" });
    syncUserCaches(res.user || {});
    toast("Profile photo removed", "success");
    renderView();
  }

  function renderProfile(container) {
    const user = state.user || {};
    const memberSince = formatTimestamp(user.created_at);
    container.innerHTML = `
      <div class="profile-grid">
        <section class="panel profile-hero">
          <div class="profile-hero__content">
            <div class="avatar avatar-lg" id="profile-avatar-preview"></div>
            <div class="profile-hero__text">
              <p class="eyebrow">Your account</p>
              <h3>${escapeHtml(displayName(user))}</h3>
              <div class="profile-meta">
                ${roleTag(user.role || "user")}
                <span>${escapeHtml(user.email || "")}</span>
                <span>Member since ${escapeHtml(memberSince)}</span>
              </div>
            </div>
          </div>
          <div class="profile-hero__actions">
            <button type="button" class="btn btn-secondary" id="profile-refresh-btn">Refresh profile</button>
          </div>
        </section>

        <section class="panel profile-panel">
          <div class="panel-header"><h3><span class="emoji">🖼️</span>Profile photo</h3></div>
          <div class="panel-body profile-panel__body">
            <p class="muted">Upload a JPG, PNG, WEBP, or GIF image up to 5MB.</p>
            <div class="profile-upload">
              <input type="file" id="profile-avatar-file" accept="image/png,image/jpeg,image/webp,image/gif" />
              <div class="profile-upload__actions">
                <button type="button" class="btn btn-primary" id="profile-avatar-upload-btn">Upload photo</button>
                <button type="button" class="btn btn-secondary" id="profile-avatar-remove-btn"${
                  user.avatar_url ? "" : " disabled"
                }>Remove photo</button>
              </div>
            </div>
          </div>
        </section>

        <section class="panel profile-panel">
          <div class="panel-header"><h3><span class="emoji">✍️</span>Personal details</h3></div>
          <div class="panel-body profile-panel__body">
            <form id="profile-form" class="form-grid">
              <label class="field full"><span>Full name</span><input name="name" value="${escapeHtml(
                user.name || ""
              )}" /></label>
              <label class="field full"><span>Email</span><input name="email" type="email" value="${escapeHtml(
                user.email || ""
              )}" /></label>
              <label class="field"><span>Role</span><input value="${escapeHtml(user.role || "")}" disabled /></label>
              <label class="field"><span>User ID</span><input value="${escapeHtml(user.user_id || "")}" disabled /></label>
            </form>
            <div class="profile-form-actions">
              <button type="button" class="btn btn-primary" id="profile-save-btn">Save profile</button>
            </div>
          </div>
        </section>

        <section class="panel profile-panel">
          <div class="panel-header"><h3><span class="emoji">🎨</span>Appearance</h3></div>
          <div class="panel-body profile-panel__body">
            <p class="muted">Choose the look that feels best while keeping the same HarvestHUB layout.</p>
            <div class="theme-choice-group">
              <button type="button" class="btn btn-secondary theme-choice" data-theme-choice="dark">Dark mode</button>
              <button type="button" class="btn btn-secondary theme-choice" data-theme-choice="light">Light mode</button>
            </div>
          </div>
        </section>
      </div>`;

    setAvatarContent(document.getElementById("profile-avatar-preview"), user, displayName(user));
    document.getElementById("profile-refresh-btn").onclick = async () => {
      await refreshProfile();
      toast("Profile refreshed", "success");
      renderView();
    };
    document.getElementById("profile-save-btn").onclick = async () => {
      try {
        await saveProfileDetails();
      } catch (e) {
        toast(e.message, "error");
      }
    };
    document.getElementById("profile-avatar-upload-btn").onclick = async () => {
      try {
        await uploadProfileAvatar();
      } catch (e) {
        toast(e.message, "error");
      }
    };
    document.getElementById("profile-avatar-remove-btn").onclick = async () => {
      try {
        await removeProfileAvatar();
      } catch (e) {
        toast(e.message, "error");
      }
    };
    container.querySelectorAll("[data-theme-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        setTheme(btn.dataset.themeChoice);
        toast("Theme updated", "success");
      });
    });
  }

  async function renderDashboard(container) {
    container.innerHTML = `<div class="stats-grid" id="dash-stats"><div class="stat-card"><span class="label">Loading…</span></div></div>
    <div class="panel"><div class="panel-header"><h3><span class="emoji">📄</span>Reports</h3></div><div class="panel-body" style="padding:1rem;">
      <p class="muted" style="margin-top:0">Download the farmer report as CSV.</p>
      <div style="margin-top:1rem;display:flex;gap:0.5rem;flex-wrap:wrap;">
        <button type="button" class="btn btn-primary" id="btn-export">Download farmer report (CSV)</button>
      </div>
    </div></div>
    <div id="dashboard-analytics"><div class="panel"><div class="panel-body" style="padding:1rem;"><span class="muted">Loading analytics…</span></div></div></div>`;
    document.getElementById("btn-export").onclick = () => {
      API.exportFarmerReport();
      toast("Opened CSV export in a new tab", "info");
    };

    const stats = document.getElementById("dash-stats");
    const analyticsRoot = document.getElementById("dashboard-analytics");
    const safeCount = async (fn) => {
      try {
        const d = await fn();
        if (typeof d.count === "number") return d.count;
        if (Array.isArray(d.fields)) return d.fields.length;
        if (Array.isArray(d.regions)) return d.regions.length;
        if (Array.isArray(d.crop_cycles)) return d.crop_cycles.length;
        if (Array.isArray(d.alerts)) return d.alerts.length;
        return "—";
      } catch {
        return "—";
      }
    };

    const safeData = async (fn, fallback) => {
      try {
        return await fn();
      } catch {
        return fallback;
      }
    };

    const [fieldsC, regionsC, cyclesC, alertsC, obsC, weatherC, activeCycles, yieldAnalysis, healthDashboard, weatherTrends, farmerPerformance] = await Promise.all([
      safeCount(() => API.request("/api/fields/")),
      safeCount(() => API.request("/api/regions/")),
      safeCount(() => API.request("/api/crop-cycles/")),
      safeCount(() => API.request("/api/alerts/")),
      safeCount(() => API.request("/api/observations/")),
      safeCount(() => API.request("/api/weather/")),
      safeData(() => API.request("/api/crop-cycles/analytics/active"), { crop_cycles: [] }),
      safeData(() => API.request("/api/crop-cycles/analytics/yield-analysis"), { data: [] }),
      safeData(() => API.request("/api/analytics/dashboard/health"), { data: [] }),
      safeData(() => API.request("/api/analytics/weather-trends"), { data: [] }),
      isFarmer() ? Promise.resolve({ data: [] }) : safeData(() => API.request("/api/analytics/farmer-performance"), { data: [] }),
    ]);

    stats.innerHTML = `
      <div class="stat-card"><span class="emoji">🌾</span><div class="label">Fields</div><div class="value">${fieldsC}</div><div class="hint">RBAC-filtered list</div></div>
      <div class="stat-card"><span class="emoji">🗺️</span><div class="label">Regions</div><div class="value">${regionsC}</div><div class="hint">Climate reference</div></div>
      <div class="stat-card"><span class="emoji">🌱</span><div class="label">Crop cycles</div><div class="value">${cyclesC}</div><div class="hint">Seasons & yield</div></div>
      <div class="stat-card"><span class="emoji">🚨</span><div class="label">Alerts</div><div class="value">${alertsC}</div><div class="hint">All severities</div></div>
      <div class="stat-card"><span class="emoji">🛰️</span><div class="label">Observations</div><div class="value">${obsC}</div><div class="hint">Satellite-linked</div></div>
      <div class="stat-card"><span class="emoji">☀️</span><div class="label">Weather rows</div><div class="value">${weatherC}</div><div class="hint">Per field</div></div>`;

    const healthRows = (healthDashboard.data || [])
      .slice(0, 8)
      .map(
        (row) => `<tr>
          <td>${escapeHtml(valueOrDash(row.field_name))}</td>
          <td>${escapeHtml(valueOrDash(row.farmer_name))}</td>
          <td>${escapeHtml(valueOrDash(row.current_crop))}</td>
          <td>${escapeHtml(valueOrDash(row.region))}</td>
          <td>${escapeHtml(valueOrDash(row.health_score))}</td>
          <td>${escapeHtml(valueOrDash(row.active_alerts))}</td>
        </tr>`
      )
      .join("");

    const yieldRows = (yieldAnalysis.data || [])
      .slice(0, 8)
      .map(
        (row) => `<tr>
          <td>${escapeHtml(valueOrDash(row.crop_name))}</td>
          <td>${escapeHtml(valueOrDash(row.total_cycles))}</td>
          <td>${escapeHtml(valueOrDash(row.average_yield))}</td>
          <td>${escapeHtml(valueOrDash(row.best_yield))}</td>
          <td>${escapeHtml(valueOrDash(row.total_yield))}</td>
        </tr>`
      )
      .join("");

    const trendRows = (weatherTrends.data || [])
      .slice(0, 8)
      .map(
        (row) => `<tr>
          <td>${escapeHtml(valueOrDash(row.region))}</td>
          <td>${escapeHtml(valueOrDash(row.month))}</td>
          <td>${escapeHtml(valueOrDash(row.avg_temperature))}</td>
          <td>${escapeHtml(valueOrDash(row.avg_rainfall))}</td>
          <td>${escapeHtml(valueOrDash(row.data_points))}</td>
        </tr>`
      )
      .join("");

    const farmerRows = (farmerPerformance.data || [])
      .slice(0, 8)
      .map(
        (row) => `<tr>
          <td>${escapeHtml(valueOrDash(row.farmer_name))}</td>
          <td>${escapeHtml(valueOrDash(row.total_fields))}</td>
          <td>${escapeHtml(valueOrDash(row.total_cycles))}</td>
          <td>${escapeHtml(valueOrDash(row.avg_yield))}</td>
          <td>${escapeHtml(valueOrDash(row.active_cycles))}</td>
          <td>${escapeHtml(valueOrDash(row.high_alerts))}</td>
        </tr>`
      )
      .join("");

    const activeCycleCards = (activeCycles.crop_cycles || [])
      .slice(0, 3)
      .map(
        (cycle) => `<div class="mini-stat">
          <span class="mini-stat__label">${escapeHtml(valueOrDash(cycle.crop_name))}</span>
          <strong>${escapeHtml(fieldLabel(cycle.field_id))}</strong>
          <span class="mini-stat__hint">Status: ${escapeHtml(valueOrDash(cycle.status))}</span>
        </div>`
      )
      .join("");

    analyticsRoot.innerHTML = `
      <div class="dashboard-mini-grid">
        <div class="panel">
          <div class="panel-header"><h3><span class="emoji">🌿</span>Active cycles snapshot</h3></div>
          <div class="panel-body dashboard-mini-body">
            ${activeCycleCards || `<p class="muted">No active crop cycles right now.</p>`}
          </div>
        </div>
      </div>
      <div class="dashboard-analytics-grid">
        <div class="panel">
          <div class="panel-header"><h3><span class="emoji">🩺</span>Field health dashboard</h3></div>
          <div class="panel-body">
            ${renderTable(["Field", "Farmer", "Crop", "Region", "Health", "Alerts"], healthRows, "No health dashboard data available.")}
          </div>
        </div>
        <div class="panel">
          <div class="panel-header"><h3><span class="emoji">📊</span>Yield analysis</h3></div>
          <div class="panel-body">
            ${renderTable(["Crop", "Cycles", "Avg yield", "Best", "Total"], yieldRows, "No completed crop yield analysis yet.")}
          </div>
        </div>
        <div class="panel">
          <div class="panel-header"><h3><span class="emoji">🌦️</span>Regional weather trends</h3></div>
          <div class="panel-body">
            ${renderTable(["Region", "Month", "Avg temp", "Avg rain", "Points"], trendRows, "No regional weather trend data available.")}
          </div>
        </div>
        ${
          isFarmer()
            ? ""
            : `<div class="panel">
          <div class="panel-header"><h3><span class="emoji">🏅</span>Farmer performance</h3></div>
          <div class="panel-body">
            ${renderTable(["Farmer", "Fields", "Cycles", "Avg yield", "Active", "High alerts"], farmerRows, "No farmer performance data available.")}
          </div>
        </div>`
        }
      </div>`;
  }

  function renderFields(container) {
    const rows = state.fields
      .map((f) => {
        const actions = [];
        actions.push(
          `<button type="button" class="btn btn-sm btn-secondary" data-act="fdet" data-id="${f.id}">Details</button>`
        );
        actions.push(
          `<button type="button" class="btn btn-sm btn-secondary" data-act="fcrop" data-id="${f.id}">Crops</button>`
        );
        if (canEditField(f))
          actions.push(`<button type="button" class="btn btn-sm btn-primary" data-act="fedt" data-id="${f.id}">Edit</button>`);
        if (canDeleteField(f))
          actions.push(`<button type="button" class="btn btn-sm btn-danger" data-act="fdel" data-id="${f.id}">Delete</button>`);
        return `<tr>
        <td>${f.id}</td>
        <td>${escapeHtml(f.field_name)}</td>
        <td>${f.user_id}</td>
        <td>${escapeHtml(regionName(f.region_id))}</td>
        <td>${escapeHtml(f.latitude)}</td>
        <td>${escapeHtml(f.longitude)}</td>
        <td>${escapeHtml(f.area)}</td>
        <td>${escapeHtml(f.soil_type)}</td>
        <td class="actions">${actions.join("")}</td>
      </tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🌾</span>Your accessible fields</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Name", "User", "Region", "Lat", "Lng", "Area", "Soil", "Actions"],
        rows,
        "No fields yet — create one as admin."
      )}
    </div></div>`;
  }

  function renderCropCycles(container) {
    const rows = state.cropCycles
      .map((c) => {
        const actions = [];
        if (canEditCropCycle(c))
          actions.push(`<button type="button" class="btn btn-sm btn-primary" data-act="cedt" data-id="${c.id}">Edit</button>`);
        if (canDeleteCropCycle(c))
          actions.push(`<button type="button" class="btn btn-sm btn-danger" data-act="cdel" data-id="${c.id}">Delete</button>`);
        return `<tr>
        <td>${c.id}</td>
        <td>${c.field_id}</td>
        <td>${escapeHtml(c.crop_name)}</td>
        <td>${escapeHtml(c.start_date)}</td>
        <td>${escapeHtml(c.expected_harvest_date)}</td>
        <td>${escapeHtml(c.status)}</td>
        <td>${escapeHtml(c.yield_prediction)}</td>
        <td class="actions">${actions.join("")}</td>
      </tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🌱</span>Crop cycles</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Field", "Crop", "Start", "Harvest (est)", "Status", "Yield pred.", "Actions"],
        rows,
        "No crop cycles."
      )}
    </div></div>`;
  }

  function renderRegions(container) {
    const showActions = canManageAdminResource();
    const rows = state.regions
      .map((r) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="redt" data-id="${r.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="rdel" data-id="${r.id}">Delete</button>`
          : "";
        return `<tr><td>${r.id}</td><td>${escapeHtml(r.region_name)}</td><td>${escapeHtml(
          r.climate_type
        )}</td><td>${escapeHtml(r.latitude ?? "")}</td><td>${escapeHtml(r.longitude ?? "")}</td>${
          showActions ? `<td class="actions">${actions}</td>` : ""
        }</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🗺️</span>Regions</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Name", "Climate", "Lat", "Lng"].concat(showActions ? ["Actions"] : []),
        rows,
        "No regions."
      )}
    </div></div>`;
  }

  function renderSatellites(container) {
    const showActions = canManageAdminResource();
    const rows = state.satellites
      .map((s) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="sedt" data-id="${s.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="sdel" data-id="${s.id}">Delete</button>`
          : "";
        return `<tr><td>${s.id}</td><td>${escapeHtml(s.satellite_name)}</td><td>${escapeHtml(
          s.provider
        )}</td><td>${escapeHtml(s.resolution)}</td>${showActions ? `<td class="actions">${actions}</td>` : ""}</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🛰️</span>Satellites</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Name", "Provider", "Res (m)"].concat(showActions ? ["Actions"] : []),
        rows,
        "No satellites."
      )}
    </div></div>`;
  }

  function renderObservations(container) {
    const showActions = canManageAdminResource();
    const rows = state.observations
      .map((o) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="oedt" data-id="${o.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="odel" data-id="${o.id}">Delete</button>`
          : "";
        return `<tr><td>${o.id}</td><td>${o.field_id}</td><td>${o.satellite_id}</td><td>${o.cycle_id}</td><td>${escapeHtml(
          o.observation_date
        )}</td><td>${escapeHtml(o.cloud_cover)}</td>${showActions ? `<td class="actions">${actions}</td>` : ""}</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">👁️</span>Observations</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Field", "Satellite", "Cycle", "Date", "Cloud"].concat(showActions ? ["Actions"] : []),
        rows,
        "No observations."
      )}
    </div></div>`;
  }

  function renderWeather(container) {
    const showActions = canManageAdminResource();
    const rows = state.weather
      .map((w) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="wedt" data-id="${w.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="wdel" data-id="${w.id}">Delete</button>`
          : "";
        return `<tr><td>${w.id}</td><td>${w.field_id}</td><td>${escapeHtml(w.date)}</td><td>${escapeHtml(
          w.temperature
        )}</td><td>${escapeHtml(w.rainfall)}</td><td>${escapeHtml(w.humidity)}</td>${
          showActions ? `<td class="actions">${actions}</td>` : ""
        }</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">☀️</span>Weather</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Field", "Date", "Temp", "Rain", "Humidity"].concat(showActions ? ["Actions"] : []),
        rows,
        "No weather rows."
      )}
    </div></div>`;
  }

  function renderAlerts(container) {
    const rows = state.alerts
      .map((a) => {
        const sev = (a.severity || "").toLowerCase();
        const tag = `<span class="tag tag-severity-${sev}">${escapeHtml(a.severity)}</span>`;
        const resolveBtn =
          canResolveAlert() && !a.is_resolved
            ? `<button type="button" class="btn btn-sm btn-primary" data-act="ares" data-id="${a.id}">Resolve</button>`
            : a.is_resolved
            ? `<span class="muted">resolved</span>`
            : "";
        return `<tr>
        <td>${a.id}</td>
        <td>${a.field_id} ${escapeHtml(fieldLabel(a.field_id))}</td>
        <td>${escapeHtml(a.alert_type)}</td>
        <td>${tag}</td>
        <td>${escapeHtml(a.message)}</td>
        <td class="actions">${resolveBtn}</td>
      </tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🚨</span>Alerts</h3></div><div class="panel-body">
      ${renderTable(["ID", "Field", "Type", "Severity", "Message", "Actions"], rows, "No alerts.")}
    </div></div>`;
  }

  function renderBandValues(container) {
    const showActions = canManageAdminResource();
    const rows = state.bandValues
      .map((b) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="bedt" data-id="${b.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="bdel" data-id="${b.id}">Delete</button>`
          : "";
        return `<tr><td>${b.id}</td><td>${b.observation_id}</td><td>${escapeHtml(b.band_name)}</td><td>${escapeHtml(
          b.band_value
        )}</td>${showActions ? `<td class="actions">${actions}</td>` : ""}</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">🎚️</span>Band values</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Observation", "Band", "Value"].concat(showActions ? ["Actions"] : []),
        rows,
        "No band values."
      )}
    </div></div>`;
  }

  function renderDerived(container) {
    const showActions = canManageAdminResource();
    const rows = state.derivedMetrics
      .map((m) => {
        const actions = showActions
          ? `<button type="button" class="btn btn-sm btn-primary" data-act="dedt" data-id="${m.id}">Edit</button>
             <button type="button" class="btn btn-sm btn-danger" data-act="ddel" data-id="${m.id}">Delete</button>`
          : "";
        return `<tr><td>${m.id}</td><td>${m.observation_id}</td><td>${escapeHtml(m.ndvi)}</td><td>${escapeHtml(
          m.evi
        )}</td><td>${escapeHtml(m.soil_moisture)}</td><td>${escapeHtml(m.crop_health_score)}</td>${
          showActions ? `<td class="actions">${actions}</td>` : ""
        }</tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">📈</span>Derived metrics</h3></div><div class="panel-body">
      ${renderTable(
        ["ID", "Obs.", "NDVI", "EVI", "Moisture", "Health"].concat(showActions ? ["Actions"] : []),
        rows,
        "No metrics."
      )}
    </div></div>`;
  }

  function renderUsers(container) {
    const rows = state.users
      .map((u) => {
        const actions = [];
        if (isAdmin() && u.user_id !== uid())
          actions.push(`<button type="button" class="btn btn-sm btn-primary" data-act="uedt" data-id="${u.user_id}">Edit</button>`);
        if (isAdmin() && u.user_id !== uid())
          actions.push(`<button type="button" class="btn btn-sm btn-danger" data-act="udel" data-id="${u.user_id}">Delete</button>`);
        return `<tr>
        <td>${u.user_id}</td>
        <td>${escapeHtml(u.name)}</td>
        <td>${escapeHtml(u.email)}</td>
        <td>${roleTag(u.role)}</td>
        <td>${u.is_active ? "yes" : "no"}</td>
        <td class="actions">${actions.join("")}</td>
      </tr>`;
      })
      .join("");
    container.innerHTML = `<div class="panel"><div class="panel-header"><h3><span class="emoji">👥</span>Users</h3></div><div class="panel-body">
      ${renderTable(["ID", "Name", "Email", "Role", "Active", "Actions"], rows, "No users returned.")}
    </div></div>`;
  }

  async function renderView() {
    const container = document.getElementById("view-container");
    container.innerHTML = `<div class="loading-row"><span class="spinner"></span> Loading…</div>`;
    try {
      if (state.view === "dashboard") {
        await renderDashboard(container);
        return;
      }
      if (state.view === "profile") {
        await refreshProfile();
        renderProfile(container);
        return;
      }
      if (state.view === "fields") {
        await loadRegions();
        await loadFields();
        renderFields(container);
        return;
      }
      if (state.view === "crop_cycles") {
        await loadFields();
        await loadCropCycles();
        renderCropCycles(container);
        return;
      }
      if (state.view === "regions") {
        await loadRegions();
        renderRegions(container);
        return;
      }
      if (state.view === "satellites") {
        await loadSatellites();
        renderSatellites(container);
        return;
      }
      if (state.view === "observations") {
        await loadFields();
        await loadSatellites();
        await loadCropCycles();
        await loadObservations();
        renderObservations(container);
        return;
      }
      if (state.view === "weather") {
        await loadFields();
        await loadWeather();
        renderWeather(container);
        return;
      }
      if (state.view === "alerts") {
        await loadFields();
        await loadAlerts();
        renderAlerts(container);
        return;
      }
      if (state.view === "band_values") {
        await loadObservations();
        await loadBandValues();
        renderBandValues(container);
        return;
      }
      if (state.view === "derived_metrics") {
        await loadObservations();
        await loadDerivedMetrics();
        renderDerived(container);
        return;
      }
      if (state.view === "users") {
        await loadUsersList();
        renderUsers(container);
        return;
      }
      container.innerHTML = `<p class="muted">Unknown view</p>`;
    } catch (e) {
      container.innerHTML = `<div class="empty-state"><p>${escapeHtml(e.message)}</p><p class="muted">Check API URL and that you are logged in with a role that can access this resource.</p></div>`;
      toast(e.message, "error");
    }
  }

  /* ---------- Delegated clicks ---------- */

  document.getElementById("view-container").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const act = btn.dataset.act;
    if (act === "fdet") {
      showJsonModal(`Field #${id} details`, API.request(`/api/fields/${id}/details`));
    }
    if (act === "fcrop") {
      showJsonModal(`Field #${id} crops`, API.request(`/api/fields/${id}/crops`));
    }
    if (act === "fedt") {
      const f = state.fields.find((x) => x.id === id);
      if (f) openFieldEditModal(f);
    }
    if (act === "fdel") {
      if (!confirm("Soft-delete this field?")) return;
      try {
        await API.request(`/api/fields/${id}`, { method: "DELETE" });
        toast("Field deleted", "success");
        await loadFields();
        renderView();
      } catch (err) {
        toast(err.message, "error");
      }
    }
    if (act === "cedt") {
      const c = state.cropCycles.find((x) => x.id === id);
      if (c) openCropCycleEditModal(c);
    }
    if (act === "cdel") {
      if (!confirm("Delete this crop cycle?")) return;
      try {
        await API.request(`/api/crop-cycles/${id}`, { method: "DELETE" });
        toast("Deleted", "success");
        await loadCropCycles();
        renderView();
      } catch (err) {
        toast(err.message, "error");
      }
    }
    if (act === "redt") {
      const region = state.regions.find((x) => x.id === id);
      if (region) openRegionEditModal(region);
    }
    if (act === "rdel") {
      await deleteAdminResource(`/api/regions/${id}`, "Delete this region?", "Region deleted", loadRegions);
    }
    if (act === "sedt") {
      const satellite = state.satellites.find((x) => x.id === id);
      if (satellite) openSatelliteEditModal(satellite);
    }
    if (act === "sdel") {
      await deleteAdminResource(`/api/satellites/${id}`, "Delete this satellite?", "Satellite deleted", loadSatellites);
    }
    if (act === "oedt") {
      const observation = state.observations.find((x) => x.id === id);
      if (observation) openObservationEditModal(observation);
    }
    if (act === "odel") {
      await deleteAdminResource(`/api/observations/${id}`, "Delete this observation?", "Observation deleted", loadObservations);
    }
    if (act === "wedt") {
      const weather = state.weather.find((x) => x.id === id);
      if (weather) openWeatherEditModal(weather);
    }
    if (act === "wdel") {
      await deleteAdminResource(`/api/weather/${id}`, "Delete this weather record?", "Weather deleted", loadWeather);
    }
    if (act === "ares") {
      try {
        await API.request(`/api/alerts/${id}/resolve`, { method: "PATCH" });
        toast("Alert resolved", "success");
        await loadAlerts();
        renderView();
      } catch (err) {
        toast(err.message, "error");
      }
    }
    if (act === "bedt") {
      const bandValue = state.bandValues.find((x) => x.id === id);
      if (bandValue) openBandValueEditModal(bandValue);
    }
    if (act === "bdel") {
      await deleteAdminResource(`/api/band-values/${id}`, "Delete this band value?", "Band value deleted", loadBandValues);
    }
    if (act === "dedt") {
      const metric = state.derivedMetrics.find((x) => x.id === id);
      if (metric) openDerivedMetricEditModal(metric);
    }
    if (act === "ddel") {
      await deleteAdminResource(`/api/derived-metrics/${id}`, "Delete this derived metric?", "Derived metric deleted", loadDerivedMetrics);
    }
    if (act === "uedt") {
      const u = state.users.find((x) => x.user_id === id);
      if (u) openUserEditModal(u);
    }
    if (act === "udel") {
      if (!confirm("Delete this user permanently?")) return;
      try {
        await API.request(`/api/users/${id}`, { method: "DELETE" });
        toast("User deleted", "success");
        await loadUsersList();
        renderView();
      } catch (err) {
        toast(err.message, "error");
      }
    }
  });

  document.getElementById("new-btn").addEventListener("click", async () => {
    const v = state.view;
    if (v === "fields" && canCreateField()) await openFieldCreateModal();
    else if (v === "regions" && canCreateRegion()) openRegionCreateModal();
    else if (v === "crop_cycles" && canCreateCropCycle()) await openCropCycleCreateModal();
    else if (v === "satellites" && canCreateSatellite()) openSatelliteCreateModal();
    else if (v === "observations" && canCreateObservation()) await openObservationCreateModal();
    else if (v === "weather" && canCreateWeather()) await openWeatherCreateModal();
    else if (v === "alerts" && canCreateAlert()) await openAlertCreateModal();
    else if (v === "band_values" && canCreateBandValue()) await openBandValueCreateModal();
    else if (v === "derived_metrics" && canCreateDerivedMetric()) await openDerivedMetricCreateModal();
  });

  document.getElementById("refresh-btn").addEventListener("click", () => {
    renderView();
    toast("Refreshed", "info");
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem(API.STORAGE_TOKEN);
    localStorage.removeItem(API.STORAGE_USER);
    state.user = null;
    showAuth();
    toast("Signed out", "info");
  });

  document.getElementById("user-pill").addEventListener("click", () => {
    if (state.user) setView("profile");
  });
  document.getElementById("user-pill").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" || ev.key === " ") {
      ev.preventDefault();
      if (state.user) setView("profile");
    }
  });

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });

  /* ---------- Auth forms ---------- */

  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const name = tab.dataset.tab;
      document.getElementById("login-form").classList.toggle("hidden", name !== "login");
      document.getElementById("register-form").classList.toggle("hidden", name !== "register");
    });
  });

  document.getElementById("login-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const body = { email: fd.get("email"), password: fd.get("password") };
    try {
      const res = await API.request("/api/auth/login", { method: "POST", body: JSON.stringify(body), auth: false });
      if (!res || !res.access_token) {
        throw new Error("Login response missing access_token. Restart the backend so the latest code is loaded.");
      }
      localStorage.setItem(API.STORAGE_TOKEN, res.access_token);
      localStorage.setItem(API.STORAGE_USER, JSON.stringify(res.user || {}));
      state.user = res.user || {};
      await refreshProfile();
      toast("Welcome back", "success");
      showApp();
      setView("dashboard");
    } catch (e) {
      toast(e.message, "error");
    }
  });

  document.getElementById("register-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const body = {
      name: fd.get("name"),
      email: fd.get("email"),
      password: fd.get("password"),
      role: fd.get("role"),
    };
    try {
      await API.request("/api/auth/register", { method: "POST", body: JSON.stringify(body), auth: false });
      toast("Account created — you can sign in now.", "success");
      document.querySelector('.auth-tab[data-tab="login"]').click();
      ev.target.reset();
    } catch (e) {
      toast(e.message, "error");
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
    applyBranding();
    initTheme();
    runHarvestIntroThenBootstrap();
  });
})();
