# Roadmap

`English` · [中文](zh-CN/ROADMAP.md)

Ordered by value, not by effort. Nothing here is dated; the shipped pipeline is step 0 of all of it.

## 1. Bidirectional mode — 中文 → 英文

Today the pipeline assumes an English-speaking source: English is the subtitle track, Chinese is the translation, and the layout is Chinese-over-English.

That ordering is a convention, not a constraint. The next version adds a `--direction en-zh | zh-en` switch:

- **zh-en** is the mirror slice: Chinese caption track (or transcript) becomes the timeline, English becomes the translation, and the stack flips to **English over Chinese** — the reader's eye should hit the target language first, whichever that is.
- The alignment code is already language-agnostic; it needs the ratio model parametrised (Chinese runs ~0.55× the character count of its English counterpart, the reverse direction is ~1.8× and needs a tighter cap than 44).
- Line-length and wrap rules become per-script instead of hard-coded to the Chinese/Latin pair: CJK 24/uphold, Latin 44, and a per-script table so a third language does not need new code.

**Why now:** most of the demand in this direction comes from Chinese conference talks, course recordings and internal training material that have no captions at all, and where the audience wants an English reading track for non-Chinese colleagues.

## 2. Bidirectional round-trip QA — 回译校验

Once both directions exist, a translation can be checked by sending the Chinese back to English and diffing it against the source text. Not a similarity score on the whole file — a per-cue flag on cues whose back-translation diverges beyond a threshold, sorted worst-first for the human.

This catches the failure mode a one-way read never shows: a plausible Chinese sentence that quietly inverted a number, a negation, or *who* is doing the action.

Ships as an audit report, never as an auto-fix. Rewriting a cue from a back-translation makes the text match the checker instead of the audio.

## 3. Summaries and chapters — 摘要与章节

Subtitles make a video searchable; a summary makes it skimmable. Same blocks, same alignment, a second deliverable: `summary.zh-en.md` with a TL;DR, a timestamped outline, key points, and pull quotes that link back to the moment they came from.

Why this belongs in a subtitle tool rather than a separate one:

- The summary is built from the **corrected** blocks, not the raw auto-caption. Speech-recognition garble is already fixed upstream; a summariser reading raw captions inherits every error.
- Every claim carries its timestamp, and the timestamp is the actual cue — the reader can jump to the proof in one click instead of trusting the abstract.
- Bilingual summaries follow the same stacking rule as the subtitles: Chinese above, English below, so a two-language audience reads one document.

Rules the pass must hold: never introduce a fact that no cue states, quote speakers verbatim inside quotation marks, and mark anything inferred as inference. A summary that says "he argued X" when he only asked a question is worse than no summary.

Chapters are the same data in a different shape: ffmetadata chapter markers written during the burn (`-map_metadata`, `-map_chapters`), so players show a jump list instead of a single flat timeline. Twelve to twenty chapters for an hour — dense enough to navigate, sparse enough to lift from the table of contents.

## 4. Transcription fallback

Sources with no caption track are currently a manual step. A Whisper pass (local `whisper.cpp`, `large-v3`, word timestamps) makes them routine, with the VAD split at sentence boundaries feeding the same cue format.

Word timestamps matter less than sentence boundaries: the aligner already does the cutting, so word-level timing only buys better snap points at the ends of blocks.

## 5. Sidecar-only delivery

`--subs-only` runs steps 1–6 of the pipeline and stops. Useful when the caller wants subtitles for an existing file, or is re-cutting the video elsewhere and will mux the SRT themselves.

## 6. Style presets

Named `force_style` presets — `lecture`, `podcast`, `bilingual-compact` — plus an optional contact sheet: six frames at fixed offsets, subtitles burned, tiled into one PNG, so a style can be judged in a single glance instead of a 45-minute re-encode.

## 7. Non-Mux sources

YouTube (`yt-dlp` for the media, its own caption API for the timeline), Vimeo, self-hosted `<video src>`. Each is a resolver in front of the same pipeline; none of them touch the burn or verify stages.

## 8. Glossary files

A `glossary.toml` per project mapping recurring terms to fixed translations, injected into the translation prompt and checked after it. Domain vocabulary is where machine translation degrades first, and where a single drift is most expensive.

## Non-goals

- **Dubbing.** Voice remains another pipeline's problem.
- **Auto-publishing.** The skill produces files; upload stays manual.
- **Long-form > 3 h.** Works in principle; nobody has run it, and the encode cost stops being reasonable.
