# Sponsored-message test content

Static JSON fixture for end-to-end testing the iOS app's `SponsoredMessageStore`
without standing up the Spotboard backend. The iOS code fetches
`<baseURL>/api/v1/messages.php` and decodes the Spotboard wire format
(see `DBTransport-iOS/DBTransport/Models/SponsoredMessageStore.swift`).

## Wiring

Set the iOS constants in `SponsoredMessageStore.swift` to:

```swift
private static let baseURL: String = "https://raw.githubusercontent.com/schnalz-digital/db-transport/redesign-1.1.2/sponsored-test"
private static let apiKey:  String = "test"
```

Toggle **Settings → Content → Sponsored messages** on. The row appears at
the bottom of the root route list after the next poll
(≤ `poll_interval_seconds`, clamped server-side to 60 s).

## Editing the message

Modify `api/v1/messages.php`, commit, push. The iOS app re-polls after
the configured interval. GitHub raw caches for ~5 min — bump
`impression_id` to a new value to force the widget to refresh on the
next poll (the id is the SwiftUI view identity).

## Field reference

| Field | Required | Notes |
|---|---|---|
| `impression_id` | yes | Int, unique per message |
| `text` | yes | Row body |
| `cta_url` | no | Tap destination; omit / null for non-clickable |
| `display_seconds` | no | Advisory; stored but not auto-dismissed |
| `poll_interval_seconds` | yes | Clamped to `max(60, …)` client-side |
