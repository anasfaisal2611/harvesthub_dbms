/**
 * HarvestHUB API client — talks to FastAPI on port 5000 by default.
 * Set localStorage key "harvesthub_api_base" to override (e.g. http://localhost:8000).
 */
(function (global) {
  const STORAGE_TOKEN = "harvesthub_token";
  const STORAGE_USER = "harvesthub_user";
  const STORAGE_API_BASE = "harvesthub_api_base";

  // One-time migration from the previous "cropdbms_*" keys so existing sessions survive the rename.
  try {
    const migrate = (oldKey, newKey) => {
      const v = localStorage.getItem(oldKey);
      if (v && !localStorage.getItem(newKey)) localStorage.setItem(newKey, v);
      if (v) localStorage.removeItem(oldKey);
    };
    migrate("cropdbms_token", STORAGE_TOKEN);
    migrate("cropdbms_user", STORAGE_USER);
    migrate("cropdbms_api_base", STORAGE_API_BASE);
  } catch (_) {
    /* ignore storage errors */
  }

  function getApiBase() {
    const b = localStorage.getItem(STORAGE_API_BASE);
    if (b && b.trim()) return b.trim().replace(/\/+$/, "");
    if (typeof window !== "undefined") {
      const { origin, hostname, pathname, protocol } = window.location;
      if (pathname.startsWith("/app")) return origin.replace(/\/+$/, "");
      if (
        /^https?:$/i.test(protocol) &&
        hostname &&
        hostname !== "localhost" &&
        hostname !== "127.0.0.1"
      ) {
        return origin.replace(/\/+$/, "");
      }
    }
    return "http://127.0.0.1:5000";
  }

  function setApiBase(url) {
    const u = String(url || "").trim().replace(/\/+$/, "");
    if (u) localStorage.setItem(STORAGE_API_BASE, u);
    else localStorage.removeItem(STORAGE_API_BASE);
  }

  function parseErrorDetail(data) {
    if (data == null) return "Request failed";
    if (typeof data === "string") return data.slice(0, 500);
    if (typeof data === "object") {
      if (data.detail != null) {
        const d = data.detail;
        if (Array.isArray(d))
          return d
            .map((x) => (typeof x === "object" ? x.msg || JSON.stringify(x) : String(x)))
            .join("; ");
        return String(d);
      }
      if (data.message) return String(data.message);
      if (data.error) return String(data.error);
    }
    return "Request failed";
  }

  function resolveUrl(path) {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    const base = getApiBase().replace(/\/+$/, "");
    if (path.startsWith("/")) return `${base}${path}`;
    return `${base}/${path.replace(/^\/+/, "")}`;
  }

  /**
   * @param {string} path - e.g. /api/health
   * @param {RequestInit & { auth?: boolean }} options
   */
  async function request(path, options = {}) {
    const base = getApiBase().replace(/\/+$/, "");
    const p = path.startsWith("/") ? path : `/${path}`;
    const url = path.startsWith("http") ? path : `${base}${p}`;

    const headers = { Accept: "application/json", ...(options.headers || {}) };
    const token = localStorage.getItem(STORAGE_TOKEN);
    if (token && options.auth !== false) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (
      options.body != null &&
      !(options.body instanceof FormData) &&
      !headers["Content-Type"]
    ) {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(url, { ...options, headers });
    const ct = res.headers.get("content-type") || "";

    let data = null;
    if (ct.includes("application/json")) {
      data = await res.json().catch(() => null);
    } else {
      data = await res.text().catch(() => null);
    }

    if (!res.ok) {
      const err = new Error(parseErrorDetail(data));
      err.status = res.status;
      err.data = data;
      throw err;
    }
    if (
      Array.isArray(data) &&
      data.length === 2 &&
      typeof data[0] === "object" &&
      typeof data[1] === "number"
    ) {
      return data[0];
    }
    return data;
  }

  /** CSV export (no auth on this route in backend). */
  function exportFarmerReport() {
    const base = getApiBase().replace(/\/+$/, "");
    window.open(`${base}/api/export/farmer-report`, "_blank");
  }

  global.API = {
    getApiBase,
    setApiBase,
    resolveUrl,
    request,
    exportFarmerReport,
    STORAGE_TOKEN,
    STORAGE_USER,
  };
})(typeof window !== "undefined" ? window : globalThis);
