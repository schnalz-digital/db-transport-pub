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

The apps' `Announcement.localizedText` silently falls back to `text`
when a translation is missing. That means an English-only message
would ship to Chinese-locale App Store / Play users mid-app without
any visible warning. **Don't skip the translations, even temporarily.**

**Translate into Traditional and Simplified Chinese only.** Every other
language reads the English `text`. (Owner's rule since 2026-11-03.)

### `texts` (the tip-jar message only)

The tip-jar message (impression_id 10) also carries `texts`: the app's
other 33 languages, keyed by the app's own language codes (`ar ca cs
da de el es es-MX fi fr fr-CA he hi hr hu id it ja ko ms nb nl pl pt-BR
pt-PT ro ru sk sv th tr uk vi`). The app shows the language it is set
to (Settings › Language, else the phone's): that language's entry,
else its base language's (`fr` for `fr-CA`), else `text`. Chinese
stays in the two fields above, never in `texts`. Versions before the
field ignore it and show `text`. Don't add `texts` to new messages.

### Two lines, on the smallest iPhone

The row shows two lines and cuts the rest off with "…". On a 375-pt
iPhone (SE, 12/13 mini) a line holds about 205 pt of 15-pt text
(roughly 28 Latin characters or 13 Chinese characters); an iPhone 17
holds about 227 pt. Keep every field within two such lines. In
Chinese, put each sentence on its own line with `\n` (each at most 13
characters) so the break never splits a word.

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
      "texts": { "de": "<Deutsch>", "fr-CA": "<français>", … },  // optional
      "cta_url": null | "<https://...>",  // null → first-party, URL → third-party
      "deep_link": null | "dbtransport://settings",  // optional, in-app destination
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
    "https://raw.githubusercontent.com/schnalz-digital/db-transport-pub/main/messages"
private static let apiKey:  String = "test"
```

**Visibility: always on for every user.** There is no Settings toggle.
Every message you publish in this fixture reaches every installed
copy of the app — write copy with that in mind (no debug strings, no
half-finished drafts). A planned future IAP will let users buy
"remove announcements" if they want to silence the row.

## Iteration cadence

iOS polls at most every `max(60, poll_interval_seconds)` seconds.
GitHub raw's CDN edge caches `~5 min`. To force a refresh on-device:

- Bump every `impression_id` to a new value (forces the carousel to
  treat the pool as fresh — bypasses on-device dedup against the
  previously-seen IDs).
- Or kill + relaunch the app (skips `nextRefreshAt` throttle).

## Closing a message (the ×)

The × hides that `impression_id` for good on that device (the app
keeps the last 20 closed IDs; reinstalling clears them). Only messages
with an ID the person hasn't closed show up on the route list. So:

- Fixing copy under the **same** ID reaches everyone who hasn't
  closed it, and stays hidden for those who have.
- A **new** ID is a new message: it shows to everyone, including
  people who closed the old one.
