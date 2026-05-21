# ios-widget

iOS Home Screen widget (planned, not started yet).

Data source: `docs/api.md` (shared contract with the other targets).

## Plan

- WidgetKit widget in Swift, lifted from an existing project
- System-driven refresh via timelines (no daemon)
- Layouts: `systemSmall` (top 1–2 lines) and `systemMedium` (4 lines + weather)
- Freshness indicator when the last data is older than 5 min (see `docs/api.md`)

## Notes to document later

- Bundle ID, App Group, etc.
- Cache strategy if the host app does the fetching and shares data with the widget
