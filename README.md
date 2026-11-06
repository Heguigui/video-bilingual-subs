# video-bilingual-subs

A [Claude Code](https://claude.com/claude-code) skill that turns any video into a **Chinese-over-English dual-subtitle MP4** — burned-in, correctly timed, with the original English track kept as a toggleable soft subtitle.

`中文` · [中文说明](README.zh-CN.md)

```
input:  page URL · .m3u8 · .mp4 · local file
output: 1080p H.264 · 中文硬字幕（上） · 英文硬字幕（下） · 英文字幕软轨
```

## Why

Adding subtitles by hand means four jobs nobody enjoys: finding the video behind a player, getting a trustworthy timeline, translating against that timeline, and styling the result so it stays readable over code editors and dark slides. This skill does the mechanical three, and keeps the translation in the agent's hands where judgement belongs — with hard rules for terminology, line length and cue alignment.

## Install

```bash
git clone https://github.com/Heguigui/video-bilingual-subs.git \
  ~/.claude/skills/video-bilingual-subs
```

Restart Claude Code. The skill is picked up automatically; invoke it with `/video-bilingual-subs` or just ask "add Chinese subtitles to this video".

## Usage

```
/video-bilingual-subs https://example.com/talk
/video-bilingual-subs /path/to/talk.mp4
```

The skill walks the pipeline in [`SKILL.md`](SKILL.md):

1. fetch the page, locate the player (Mux / HLS / mp4)
2. fetch ffmpeg if missing
3. pull the source's own subtitle track for the timeline
4. download video segments in parallel and concat
5. cut the timeline into translation blocks
6. **translate block by block** (the agent does this, not a script)
7. build the bilingual SRT — Chinese above, English below, sentence-aligned
8. burn with libass, keep the English soft track, `+faststart`
9. verify with `ffprobe` plus sampled frames

Works for both delivery styles: burned file, or `.srt` sidecars only if the user wants subtitles without a re-encode.

## Output contract

- Chinese line ≤ 24 chars, English ≤ 44 chars, max 5 lines on screen
- Chinese never breaks inside an English word; Chinese breaks land on punctuation
- No overlapping cues, no empty cues, `utf-8-sig` so players do not show a garbled first line
- Duration must match the source within seconds — a gap means missing segments, not a finished file

## Layout

```
SKILL.md                  pipeline the agent follows
scripts/
  hls_fetch.ps1           parallel segment downloader (PowerShell, system proxy)
  vtt_to_cues.py          VTT → cues, removes HLS segment overlap
  concat_segments.py      builds the ffmpeg concat list
  build_blocks.py         cues → sentence-level translation blocks
  check_zh.py             translation coverage check
  build_bilingual_srt.py  sentence alignment + bilingual layout
  check_srt.py            overlap / line-length audit
docs/
  USAGE.md  PIPELINE.md  TROUBLESHOOTING.md  ROADMAP.md
  zh-CN/                   Chinese mirrors of the four docs above
examples/
  sample.zh-en.srt        excerpt of the output format
```

## Docs

- [Usage](docs/USAGE.md) — inputs, delivery modes, what "done" means
- [Pipeline](docs/PIPELINE.md) — the nine steps and why each exists
- [Troubleshooting](docs/TROUBLESHOOTING.md) — the failures you will actually hit
- [Roadmap](docs/ROADMAP.md) — bidirectional mode, round-trip QA, summaries and chapters, transcription fallback

Chinese: [README](README.zh-CN.md) · [docs/zh-CN](docs/zh-CN)

## Requirements

- Windows (the downloader is PowerShell; the rest is portable)
- Python 3.9+
- FFmpeg — fetched automatically if absent
- Network access to the source; a system proxy is honoured

## Roadmap

Direction, not promises — see [docs/ROADMAP.md](docs/ROADMAP.md).

- **Bidirectional mode** (planned): source language and target language become switchable, layout flips with the target
- **Bilingual summary + chapter markers** (planned): timestamped TL;DR, outline and quotes built from the corrected blocks
- Sidecar-only mode without re-encode
- Whisper fallback for sources with no caption track
- ASS styling presets and a preview contact sheet

## License

MIT — see [LICENSE](LICENSE).
