# Usage

`English` · [中文](zh-CN/USAGE.md)

## Invocation

```
/video-bilingual-subs <url-or-path> [output-path]
```

Without an output path the result lands next to the working directory as `<name>.zh-en.mp4`, with `zh-en.srt` and `en.srt` beside it.

## Inputs

| Input | Behaviour |
|---|---|
| Page URL | Page is fetched with PowerShell (`Invoke-WebRequest`, honours the system proxy); the player is located in the markup |
| Direct `.m3u8` | Used as-is; a rendition is chosen from the master playlist |
| Direct `.mp4` | Downloaded; no segmenting |
| Local file | No download step |

Authenticated pages work when the fetch carries the same cookies the browser has. Paywalled players that mint short-lived signed URLs must be captured while the URL is fresh.

## Pick a rendition

Highest first: 1080p → 720p. Above 1080p only when the user asks; the burn re-encode roughly doubles the wall clock and 4K gains nothing for subtitles.

## Delivery modes

- **Default — burned file.** Chinese over English, English soft track embedded, `+faststart`.
- **Sidecar only.** Run steps 1–6, hand over `zh_en.srt`. No re-encode, no quality loss, the player does the styling.
- **Summary + chapters** *(planned)*. A timestamped `summary.zh-en.md` and player chapter markers, built from the same corrected blocks.

## Quality rules the agent must hold

- Terminology is fixed before the first line and does not drift. Product names stay as-is; domain terms follow the glossary decided up front.
- Speech stays speech. Contractions and fillers may go; information may not.
- Code, commands and UI strings are copied verbatim, never translated.
- A block may split into several Chinese cues or merge, but never attaches to a neighbouring block's id.

## What "done" means

1. `ffprobe` duration matches the source within seconds.
2. Sampled frames at the head, quarter, middle, three-quarters and tail show subtitles on screen, Chinese above English, nothing clipped.
3. A spot-checked SRT cue matches what is actually said at that timestamp.
4. `check_srt.py` reports zero overlaps and zero over-long lines.

Reporting completion without 1–4 is guessing.

## Attribution

The skill downloads and re-encodes third-party video. Check the source's terms before republishing; caption text is the speaker's, not yours.
