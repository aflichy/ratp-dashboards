// @ts-nocheck
// Scriptable widget mirroring antoineflichy.fr/transport on the home screen.
// Install: see ./README.md
//
// Fetches the public dashboard JSON and renders next departures, vélib counts,
// weather, and a disruption badge. Refreshes ~every 10 min and falls back to a
// cached payload (up to 1 h old) when the network is unreachable.

const API_URL = "https://antoineflichy.fr/api/spring/transport";
const DASHBOARD_URL = "https://antoineflichy.fr/transport";
const CACHE_FILE = "transport-dashboard.json";
const REFRESH_INTERVAL_MIN = 10;
const STALE_CACHE_LIMIT_MIN = 60;
const REQUEST_TIMEOUT_SEC = 8;
const MEDIUM_MAX_LINES = 3;

// Tokens kept in sync with frontend/src/index.css. color3 is theme-invariant,
// every other slot flips between the light and dark site palettes.
const COLORS = {
  background: Color.dynamic(new Color("#ffffff"), new Color("#131313")),
  foreground: Color.dynamic(new Color("#1f1d1b"), new Color("#e5e5e5")),
  muted: Color.dynamic(new Color("#6b6660"), new Color("#737373")),
  accent: new Color("#e85d3c"),
  danger: Color.dynamic(new Color("#c93b1e"), new Color("#e85d3c")),
  warning: Color.dynamic(new Color("#b97a00"), new Color("#e0a83a")),
};

// ─── data ─────────────────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const req = new Request(API_URL);
    req.timeoutInterval = REQUEST_TIMEOUT_SEC;
    const payload = await req.loadJSON();
    writeCache(payload);
    return { payload, fromCache: false, cachedAt: null };
  } catch (err) {
    const cached = readCache();
    if (cached) return { payload: cached.payload, fromCache: true, cachedAt: cached.savedAt };
    throw err;
  }
}

function cachePath() {
  const fm = FileManager.local();
  return fm.joinPath(fm.cacheDirectory(), CACHE_FILE);
}

function writeCache(payload) {
  const fm = FileManager.local();
  const envelope = { savedAt: new Date().toISOString(), payload };
  fm.writeString(cachePath(), JSON.stringify(envelope));
}

function readCache() {
  const fm = FileManager.local();
  const path = cachePath();
  if (!fm.fileExists(path)) return null;
  try {
    const env = JSON.parse(fm.readString(path));
    const savedAt = new Date(env.savedAt);
    const ageMin = (Date.now() - savedAt.getTime()) / 60_000;
    if (ageMin > STALE_CACHE_LIMIT_MIN) return null;
    return { payload: env.payload, savedAt };
  } catch {
    return null;
  }
}

// ─── formatters ───────────────────────────────────────────────────────────

const fmtTime = (iso) =>
  new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

// WMO 4677 codes — same mapping as Transport.tsx.
function weatherIcon(code, isDay) {
  if (code === 0) return isDay ? "☀️" : "🌙";
  if (code === 1) return isDay ? "🌤️" : "🌙";
  if (code === 2) return "⛅";
  if (code === 3) return "☁️";
  if (code === 45 || code === 48) return "🌫️";
  if (code >= 51 && code <= 55) return "🌦️";
  if (code >= 61 && code <= 65) return "🌧️";
  if (code >= 71 && code <= 75) return "🌨️";
  if (code >= 80 && code <= 82) return "🌧️";
  if (code >= 95 && code <= 99) return "⛈️";
  return "☁️";
}

const disruptionGlyph = (severity) => (severity === "closed" ? "⛔" : "ℹ️");
const disruptionColor = (severity) => (severity === "closed" ? COLORS.danger : COLORS.warning);

function pickWorstDisruption(disruptions) {
  const closed = disruptions.find((d) => d.severity === "closed");
  return closed ?? disruptions[0];
}

// ─── text primitive ───────────────────────────────────────────────────────

function addText(target, value, opts = {}) {
  const { size = 12, color, mono = false, bold = false, lineLimit } = opts;
  const t = target.addText(value);
  if (mono) {
    t.font = new Font(bold ? "Menlo-Bold" : "Menlo", size);
  } else {
    t.font = bold ? Font.boldSystemFont(size) : Font.systemFont(size);
  }
  if (color) t.textColor = color;
  if (lineLimit != null) t.lineLimit = lineLimit;
  return t;
}

// ─── medium layout ────────────────────────────────────────────────────────

function buildMedium(widget, data, fromCache, cachedAt) {
  widget.setPadding(12, 14, 12, 14);
  widget.spacing = 5;

  const header = widget.addStack();
  header.layoutHorizontally();
  header.centerAlignContent();
  header.spacing = 4;

  addText(header, "$", { size: 12, color: COLORS.accent, mono: true });
  addText(header, "curl /transport", { size: 12, color: COLORS.muted, mono: true });
  header.addSpacer();

  addText(header, fmtTime(data.generatedAt), { size: 12, color: COLORS.muted, mono: true });
  if (data.weather) {
    header.addSpacer(8);
    addText(header, weatherIcon(data.weather.weatherCode, data.weather.isDay), { size: 13 });
    addText(header, ` ${Math.round(data.weather.temperatureC)}°`, {
      size: 13,
      color: COLORS.foreground,
      mono: true,
    });
  }

  for (const line of data.lines.slice(0, MEDIUM_MAX_LINES)) {
    addLineRow(widget, line);
  }

  widget.addSpacer(2);
  addVelibRow(widget, data.velib);

  if (data.disruptions.length > 0) {
    addDisruptionRow(widget, pickWorstDisruption(data.disruptions));
  }

  if (fromCache) {
    addText(widget, `cache ${fmtTime(cachedAt.toISOString())}`, {
      size: 9,
      color: COLORS.muted,
      mono: true,
    });
  }
}

function addLineRow(widget, line) {
  const row = widget.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();
  row.spacing = 6;

  const codeStack = row.addStack();
  codeStack.size = new Size(42, 0);
  addText(codeStack, line.line, { size: 12, color: COLORS.accent, mono: true, bold: true });

  addText(row, `→ ${line.direction}`, {
    size: 12,
    color: COLORS.foreground,
    mono: true,
    lineLimit: 1,
  });
  row.addSpacer();

  const minutes = line.nextDeparturesMinutes.slice(0, 3);
  minutes.forEach((m, i) => {
    addText(row, `${m}′`, {
      size: 12,
      color: i === 0 ? COLORS.accent : COLORS.muted,
      mono: true,
      bold: i === 0,
    });
  });
}

function addVelibRow(widget, velib) {
  const row = widget.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();
  row.spacing = 6;

  const codeStack = row.addStack();
  codeStack.size = new Size(42, 0);
  addText(codeStack, "vélib", { size: 11, color: COLORS.accent, mono: true, bold: true });

  addText(row, velib.stationName, {
    size: 11,
    color: COLORS.muted,
    mono: true,
    lineLimit: 1,
  });
  row.addSpacer();
  addText(row, `${velib.mechanical} méca`, { size: 11, color: COLORS.foreground, mono: true });
  row.addSpacer(8);
  addText(row, `${velib.electrical} élec`, { size: 11, color: COLORS.foreground, mono: true });
}

function addDisruptionRow(widget, d) {
  const row = widget.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();
  row.spacing = 4;
  addText(row, disruptionGlyph(d.severity), { size: 10 });
  addText(row, d.line, {
    size: 10,
    color: disruptionColor(d.severity),
    mono: true,
    bold: true,
  });
  addText(row, d.message, { size: 10, color: COLORS.muted, mono: true, lineLimit: 1 });
}

// ─── small layout ─────────────────────────────────────────────────────────

function buildSmall(widget, data, fromCache, cachedAt) {
  widget.setPadding(12, 12, 12, 12);
  widget.spacing = 3;

  const header = widget.addStack();
  header.layoutHorizontally();
  header.centerAlignContent();
  addText(header, "🚍", { size: 13 });
  header.addSpacer(4);
  addText(header, fmtTime(data.generatedAt), { size: 10, color: COLORS.muted, mono: true });
  header.addSpacer();
  if (data.weather) {
    addText(header, weatherIcon(data.weather.weatherCode, data.weather.isDay), { size: 11 });
    addText(header, ` ${Math.round(data.weather.temperatureC)}°`, {
      size: 11,
      color: COLORS.foreground,
      mono: true,
    });
  }

  widget.addSpacer(4);

  const top = data.lines[0];
  if (top) {
    addText(widget, top.line, { size: 18, color: COLORS.accent, mono: true, bold: true });
    addText(widget, `→ ${top.direction}`, {
      size: 11,
      color: COLORS.foreground,
      mono: true,
      lineLimit: 1,
    });
    addText(widget, top.stop, { size: 9, color: COLORS.muted, mono: true, lineLimit: 1 });
    widget.addSpacer(3);
    const minRow = widget.addStack();
    minRow.layoutHorizontally();
    minRow.spacing = 8;
    top.nextDeparturesMinutes.slice(0, 3).forEach((m, i) => {
      addText(minRow, `${m}′`, {
        size: 16,
        color: i === 0 ? COLORS.accent : COLORS.muted,
        mono: true,
        bold: i === 0,
      });
    });
  } else {
    addText(widget, "Pas de prochain départ", { size: 11, color: COLORS.muted });
  }

  widget.addSpacer();

  if (data.disruptions.length > 0) {
    const d = pickWorstDisruption(data.disruptions);
    const row = widget.addStack();
    row.layoutHorizontally();
    row.spacing = 3;
    addText(row, disruptionGlyph(d.severity), { size: 9 });
    addText(row, d.line, {
      size: 9,
      color: disruptionColor(d.severity),
      mono: true,
      bold: true,
    });
  }

  if (fromCache) {
    addText(widget, `cache ${fmtTime(cachedAt.toISOString())}`, {
      size: 8,
      color: COLORS.muted,
      mono: true,
    });
  }
}

// ─── error fallback ───────────────────────────────────────────────────────

function buildError(widget, err) {
  widget.setPadding(14, 14, 14, 14);
  addText(widget, "🚍 Transport", { size: 13, color: COLORS.muted, bold: true });
  widget.addSpacer(6);
  addText(widget, "Impossible de joindre /transport", { size: 11, color: COLORS.foreground });
  widget.addSpacer(4);
  addText(widget, String(err.message ?? err), {
    size: 9,
    color: COLORS.muted,
    mono: true,
    lineLimit: 2,
  });
}

// ─── entry ────────────────────────────────────────────────────────────────

async function main() {
  const widget = new ListWidget();
  widget.backgroundColor = COLORS.background;
  widget.url = DASHBOARD_URL;
  widget.refreshAfterDate = new Date(Date.now() + REFRESH_INTERVAL_MIN * 60_000);

  try {
    const { payload, fromCache, cachedAt } = await loadDashboard();
    const family = config.widgetFamily ?? "medium";
    if (family === "small") buildSmall(widget, payload, fromCache, cachedAt);
    else buildMedium(widget, payload, fromCache, cachedAt);
  } catch (err) {
    buildError(widget, err);
  }

  if (config.runsInWidget) {
    Script.setWidget(widget);
  } else {
    await widget.presentMedium();
  }
  Script.complete();
}

await main();
