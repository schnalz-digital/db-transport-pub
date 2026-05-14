#!/usr/bin/env python3
"""
Fill in missing locale fields in `sponsored-test/api/v1/messages.php`
using the MyMemory translation API.

- For each message, if `text_zh_hant` or `text_zh_hans` is missing /
  empty / null, calls MyMemory with the English `text` and writes the
  translation back.
- Manually-populated translations are left untouched (the script only
  fills BLANKS — never overwrites). If MyMemory's auto-translation is
  clunky, just hand-edit the field; future runs will skip it.
- Quiet exit when no translations are needed — the workflow's
  follow-up `git diff` check decides whether to commit.

MyMemory: https://mymemory.translated.net/doc/spec.php
- 5000 chars/day anonymous (more than enough for our use).
- No account / key required.
- Language codes used: zh-TW for Traditional, zh-CN for Simplified.

JSON formatting preserved as 2-space indent, no ASCII escape, trailing
newline — matches what the file already looks like.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

FIXTURE = Path("messages/api/v1/messages.php")

# Field name in JSON  -> MyMemory language code
LANG_FIELDS: dict[str, str] = {
    "text_zh_hant": "zh-TW",
    "text_zh_hans": "zh-CN",
}

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
# Conservative — MyMemory rate-limits but doesn't document the threshold.
# Sleeping briefly between calls avoids hitting "TOO MANY REQUESTS" on
# busy days even with the modest size of our message pool.
PER_REQUEST_DELAY_S = 0.4


def translate(text: str, target: str) -> str | None:
    """Translate `text` from English to `target` via MyMemory.

    Returns the translated string on success, or `None` on any failure
    (network error, rate-limit, invalid response). Caller is expected
    to skip the field rather than crash — a missing translation is
    handled gracefully by the iOS-side `localizedText(for:)` fallback
    to English.
    """
    params = urllib.parse.urlencode({
        "q": text,
        "langpair": f"en|{target}",
    })
    url = f"{MYMEMORY_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=12) as resp:
            data = json.load(resp)
    except Exception as exc:
        print(f"  ! request failed for {target}: {exc}", file=sys.stderr)
        return None

    # MyMemory's `responseStatus` mirrors HTTP status; 200 = OK.
    status = data.get("responseStatus")
    if status != 200 and status != "200":
        print(f"  ! API status {status} for {target}: "
              f"{data.get('responseDetails')}", file=sys.stderr)
        return None

    translated = data.get("responseData", {}).get("translatedText", "")
    # MyMemory sometimes echoes upstream errors as the translation
    # body ("MYMEMORY WARNING ..." or "INVALID ..."). Treat those as
    # a no-op so a fluke doesn't ship as the user-facing copy.
    if not translated or translated.upper().startswith(("MYMEMORY ", "INVALID ", "PLEASE ")):
        print(f"  ! sentinel response for {target}: {translated!r}",
              file=sys.stderr)
        return None
    return translated


def main() -> int:
    raw = FIXTURE.read_text(encoding="utf-8")
    payload = json.loads(raw)
    messages = payload.get("messages", [])

    changes = 0
    for msg in messages:
        en = msg.get("text", "").strip()
        if not en:
            continue
        impr = msg.get("impression_id")
        for field, lang_code in LANG_FIELDS.items():
            existing = msg.get(field)
            if isinstance(existing, str) and existing.strip():
                continue  # already populated — leave manual edits intact
            print(f"impression {impr} -> {field}: translating…",
                  file=sys.stderr)
            translated = translate(en, lang_code)
            time.sleep(PER_REQUEST_DELAY_S)
            if translated:
                msg[field] = translated
                changes += 1
                print(f"  + {translated}", file=sys.stderr)

    if changes == 0:
        print("No translations to add.", file=sys.stderr)
        return 0

    # Pretty-print with 2-space indent matching the existing file.
    # `ensure_ascii=False` keeps the Chinese characters readable in the
    # commit diff rather than the JSON-escape `\uXXXX` form.
    FIXTURE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Added {changes} translation(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
