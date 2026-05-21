# ios-widget

iPhone Home Screen widget that mirrors the [`/transport` dashboard](https://antoineflichy.fr/transport) — next departures, Vélib counts, weather, and a disruption badge. Data contract in [`docs/api.md`](../docs/api.md).

Two implementation tracks coexist:

| Track                 | Status   | Stack                            |
|-----------------------|----------|----------------------------------|
| **Scriptable (JS)**   | shipped  | [`transport.js`](./transport.js) |
| **WidgetKit (Swift)** | planned  | Swift · WidgetKit                |

The Scriptable script is what's running on the phone today. The WidgetKit version is the long-term target if/when the Scriptable approach hits a wall (e.g. tighter integration with iOS, better refresh, complications).

## Scriptable (current)

### Install

1. Install [Scriptable](https://scriptable.app) on your iPhone.
2. Open Scriptable, tap `+`, paste the contents of [`transport.js`](./transport.js), and save the script as **Transport**.
3. On the home screen, long-press → `+` → search **Scriptable** → pick **Medium** (or **Small**).
4. Tap the placeholder, set **Script** = **Transport**, **When Interacting** = **Run Script**, and dismiss.

Tapping the widget opens `/transport` in the browser.

### Sizes

- **Medium** — header, first three lines with next departures, Vélib row, top disruption badge.
- **Small** — first line + next three departures + compact weather. Disruption badge if any.

### Refresh & offline

The widget asks iOS to refresh every ~10 min; iOS itself decides the real cadence (usually 5–15 min). The last successful payload is cached for 1 h. If the network is unreachable and the cache is still fresh, the widget renders cached data with a `cache HH:MM` footer; otherwise it shows an error.

### Theming

Follows the iOS appearance setting (light / dark) via `Color.dynamic`. The palette mirrors the site's own light/dark theme so the widget feels of-a-piece.

## WidgetKit (planned)

- WidgetKit widget in Swift, lifted from an existing project
- System-driven refresh via timelines (no daemon)
- Layouts: `systemSmall` (top 1–2 lines) and `systemMedium` (4 lines + weather)
- Freshness indicator when the last data is older than 5 min (see `docs/api.md`)

### Notes to document later

- Bundle ID, App Group, etc.
- Cache strategy if the host app does the fetching and shares data with the widget
