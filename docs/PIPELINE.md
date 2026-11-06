# Pipeline

`English` · [中文](zh-CN/PIPELINE.md)

Nine steps, three of which are load-bearing and easy to get wrong: the timeline, the alignment, the verification.

```
page ──► media URLs ──► subtitle track ──► cues ──► blocks ──► Chinese ──► bilingual SRT ──► burn ──► verify
                              │                                                 │
                              └── segment overlap removed                      └── sentence-aligned, never word-split
```

## 1. Resolve the source

The player sits in the page markup, usually as a playback id or an `.m3u8`. For Mux, `https://stream.mux.com/<playbackId>.m3u8` is the master. The master also carries `#EXT-X-MEDIA:TYPE=SUBTITLES` when captions exist — keep that whole line, it is the timeline.

## 2. Timeline before translation

`vtt_to_cues.py` parses the caption segments into `[start, end, text]` and drops duplicates. **HLS segments overlap by design**: the tail cues of segment *n* reappear at the head of *n+1*. Skipping the dedupe produces a film where every sentence is said twice.

Sources without a caption track fall back to embedded subtitle streams, then to transcription. Transcription never calls step 5–7 into question; the timeline shape is identical.

## 3. Video

One `ffmpeg -i master.m3u8` is a single TCP stream that stalls and dies. Instead the skill enumerates segments, fetches them with ten parallel workers, and concats. Signed URLs are used verbatim — reordering query parameters invalidates them.

A duration gap after concat means missing segments, not a finished download. Refill and re-concat.

## 4. Blocks

Cues arrive 2–4 seconds long and broken mid-sentence. `build_blocks.py` merges them to sentence boundaries and caps a block at ~380 characters, then groups blocks into ~3.8k-character translation batches.

## 5. Translation

Done by the agent, block by block, keyed by id. The rules live in `SKILL.md`; the summary is: keep speech speech, fix auto-caption garble by meaning, keep identifiers verbatim, hold the glossary.

## 6. Alignment

English is split at sentence boundaries; Chinese is cut by character ratio and snapped to the nearest punctuation after that ratio. Both sides stay in the same block, so no cue ever says something the other language is not saying.

This is also why word-count splitting fails: Chinese runs ~0.55× the character count of the English it translates, so ratio-free splitting drifts within two or three cues.

## 7. Layout

Chinese ≤ 24 chars per line above English ≤ 44 chars, five lines per screen maximum, balanced breaks that never land inside a Latin word. Written `utf-8-sig` so the first line is not mojibake in older players.

## 8. Burn

libass via the `subtitles` filter, Microsoft YaHei, white fill with a black outline, bottom aligned. `-c:a copy` — audio is never touched. The English track is muxed as `mov_text` so viewers can switch the burned text off.

`-movflags +faststart` puts the moov atom first for streaming playback.

## 9. Verify

`ffprobe` for duration; five sampled frames for presence, stacking and clipping; one SRT cue against its timestamp for sync; `check_srt.py` for structural faults.

## Derived artifacts (planned)

Summaries and chapters branch off after step 6, before the burn: the paired blocks are already sentence-aligned and corrected, so the summary writer reads proof, not guesses. Each bullet carries the cue timestamp it came from; chapters are the same data collapsed to 12–20 anchors and written as ffmetadata during the encode. See [ROADMAP](ROADMAP.md#3-summaries-and-chapters--摘要与章节).

## Cost model

Wall clock is dominated by the re-encode at roughly 1–2× realtime. A 45-minute 1080p talk is a 30–45 minute encode — long enough that the job must run in the background with a timeout that outlives it.
