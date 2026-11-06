# Troubleshooting

`English` · [中文](zh-CN/TROUBLESHOOTING.md)

## `curl: (35) schannel: failed to receive handshake`

Direct `curl` to most non-domestic hosts fails behind a filtered network. Use PowerShell instead — `Invoke-WebRequest` goes through the system proxy:

```bash
powershell -NoProfile -Command "Invoke-WebRequest -Uri '<URL>' -UseBasicParsing -OutFile 'out'"
```

FFmpeg honours `-http_proxy http://127.0.0.1:<port>` if it must fetch anything itself.

## ffmpeg is not installed

Do not `pip install` a wrapper. Fetch the static build and use the binary:

```bash
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -UseBasicParsing -OutFile 'ffmpeg.zip'; Expand-Archive ffmpeg.zip -DestinationPath ff -Force"
```

## Every sentence appears twice

The HLS segment overlap was not removed. Confirm `vtt_to_cues.py` ran and its reported count is lower than the raw cue count.

## Subtitle timings are wrong after a single-connection download

ffmpeg retried across a stalled TLS session and lost alignment. Segmented download plus concat is the fix; check that the concatenated duration matches the source before encoding.

## Verification frames show the opening subtitles no matter the timestamp

`-ss` before `-i` resets presentation timestamps, so the `subtitles` filter starts reading at zero. Put `-ss` **after** `-i` when sampling.

## A long line of English or a Chinese break lands mid-word

The wrapping helpers split on tokens and refuse to break inside a Latin word. If you edited `build_bilingual_srt.py`, re-run `check_srt.py` — it fails on any line over the limit.

## Mojibake on the first subtitle line

The SRT was written without a BOM. All scripts write `utf-8-sig`; match that if you write your own.

## `missing translations: [..]`

A block id was skipped or renumbered. `check_zh.py` reports the ids; fill them in `zh/chunk_NN.txt` as `[id] 中文`.

## Encode killed mid-way

The foreground tool timeout (120 s by default) cut it. Run with `run_in_background` and a timeout several times the video length; ~2× realtime is expected on 1080p.

## `Resource not accessible by personal access token` when publishing

Fine-grained tokens without **Administration: write** cannot create repositories. Create the empty repo in the browser, or grant the scope, then push.

## Re-publishing a derived video

Check the source's licence. Downloading and re-encoding does not transfer rights; caption text belongs to the speaker.
