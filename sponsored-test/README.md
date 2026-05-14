# DB Transport — sponsored / announcement messages

Static JSON pool consumed by the iOS app's `SponsoredMessageStore`.
The app polls `api/v1/messages.php`, decodes the Spotboard-compatible
wire format, and rotates the messages locally on a `display_seconds`
timer.

## **Rule: every message must include all three language fields**

Every entry in `messages[]` must populate:

- `text` — English (the fallback for any locale not separately listed)
- `text_zh_hant` — Traditional Chinese (Hong Kong, Taiwan)
- `text_zh_hans` — Simplified Chinese (mainland China, Singapore)

The iOS-side `SponsoredMessage.localizedText(for:)` silently falls
back to `text` when a translation is missing. That means an
English-only message would ship to Chinese-locale TestFlight / App
Store users mid-app without any visible warning. **Don't skip the
translations, even temporarily.**

## Terminology — keep consistent with the rest of the app's L10n

| Concept | Hant | Hans |
|---|---|---|
| Settings | 設定 | 设置 |
| Wallpaper | 桌布 | 壁纸 |
| Photo | 相片 | 照片 |
| Tip / reward the developer | 打賞 | 打赏 |
| Favourites | 我的最愛 | 收藏 |
| Routes | 路線 | 路线 |

## Field reference

```json
{
  "messages": [
    {
      "impression_id": <int>,        // unique, monotonically increasing
      "text": "<English copy>",
      "text_zh_hant": "<繁體中文>",
      "text_zh_hans": "<简体中文>",
      "cta_url": null | "<https://...>",  // null → first-party, URL → third-party
      "display_seconds": <int>       // clamped 3..60 client-side
    }
  ],
  "poll_interval_seconds": <int>     // clamped to ≥60 client-side
}
```

## Caption logic (driven by `cta_url`)

The iOS app picks the caption automatically:

- `cta_url: null` → **Announcement / 公告 / 公告** (first-party content
  — tip-jar callouts, feature announcements, etc.)
- `cta_url: "<external URL>"` → **Sponsored / 贊助 / 赞助** (paid
  third-party placement)

This switch keeps the App Store Review §2.3 / §3.2.2 "accurate
metadata / no deceptive practices" line clean — self-promotional
content isn't mislabeled as sponsored.

## Wiring (iOS app side)

`SponsoredMessageStore.swift` ships with the production constants
already pointing at this repo:

```swift
private static let baseURL: String =
    "https://raw.githubusercontent.com/schnalz-digital/db-transport-pub/main/sponsored-test"
private static let apiKey:  String = "test"
```

User toggles **Settings → Content → Sponsored messages** to opt in
(off by default).

## Iteration cadence

iOS polls at most every `max(60, poll_interval_seconds)` seconds.
GitHub raw's CDN edge caches `~5 min`. To force a refresh on-device:

- Bump every `impression_id` to a new value (forces the carousel to
  treat the pool as fresh — bypasses on-device dedup against the
  previously-seen IDs).
- Or kill + relaunch the app (skips `nextRefreshAt` throttle).
