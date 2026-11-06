---
name: video-bilingual-subs
description: Turn any video (page URL, HLS/m3u8, mp4 or local file) into a Chinese-over-English dual-subtitle video. Use when the user asks to add Chinese subtitles to a video, make bilingual subtitles, or transcribe + translate a video.
---

# 视频双语字幕流水线

把视频做成「中文在上、英文在下」的硬字幕成片，并保留一条可开关的英文软字幕轨。

全程两个铁律：

1. **先拿时间轴，再翻译**。时间轴来自视频自带字幕轨（首选）或语音转写，绝不靠猜。
2. **每步都验**。抽帧看字幕有没有烧上、对不对得上；ffprobe 核对时长；不自查就说"做完了"等于没做。

## 输入形态

按顺序判定，命中即停：

| 输入 | 做法 |
|---|---|
| 本地视频文件 | 跳过下载，直接进「取时间轴」 |
| 直链 `.m3u8` / `.mp4` | 直接进「取视频」 |
| 网页 URL | 抓 HTML（第 0 步），找 m3u8 / mp4 / 播放器 id |

## 第 0 步 抓页面、抽媒体地址

内网/国内网络下 `curl` 常见 `(35) schannel handshake failed`，**用 PowerShell 而不是 curl**（走系统代理）：

```bash
mkdir -p "$WORK"
powershell -NoProfile -Command "Invoke-WebRequest -Uri '<PAGE_URL>' -UseBasicParsing -TimeoutSec 60 -OutFile '$WORK/page.html'"
```

然后在 `page.html` 里找播放器。常见是 Mux（`muxPlaybackId":"XXXX"`）、YouTube、Vimeo、直链 mp4。Mux 的成片地址是：

```
https://stream.mux.com/<PLAYBACK_ID>.m3u8
```

（靠 `<script>` 里的 `muxPlaybackId` 或 `videoResource` 字段定位。页面里通常还有现成的英文字幕，Mux 的 master playlist 里会出现 `#EXT-X-MEDIA:TYPE=SUBTITLES` 一整行——**把这行整条留下来**，它是后面时间轴的来源。）

## 第 1 步 准备 ffmpeg

系统没装就下静态包，别用 pip 版本：

```bash
powershell -NoProfile -Command "\$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -UseBasicParsing -TimeoutSec 300 -OutFile '$WORK/ffmpeg.zip'; Expand-Archive -Path '$WORK/ffmpeg.zip' -DestinationPath '$WORK/ff' -Force"
FF=$(find "$WORK/ff" -name ffmpeg.exe | head -1)
```

## 第 2 步 下载英文字幕（时间轴）

master playlist 里有 SUBTITLES 行时：

```bash
SUB_URL=$(grep -o 'URI="[^"]*"' "$WORK/master.m3u8" | sed 's/URI="//;s/"$//')
powershell -NoProfile -Command "Invoke-WebRequest -Uri '$SUB_URL' -UseBasicParsing -OutFile '$WORK/subs.m3u8'"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hls_fetch.ps1 -Playlist "$WORK/subs.m3u8" -OutDir "$WORK/subseg" -Ext vtt -Workers 8
python scripts/vtt_to_cues.py "$WORK/subseg" "$WORK/cues.json"
```

**HLS 分段之间有重叠**，同一条字幕会在两段里各出现一次。`vtt_to_cues.py` 已按 `(起始时间, 文本)` 去重，不要自己跳过这步，否则成片会看到每句话重复一遍。

没有字幕轨时：`ffmpeg -i in.mp4 -map 0:s:0 subs.srt` 抽内嵌轨；再没有就转写（whisper / 站方转写），转出来照样走后面的流程。

## 第 3 步 下载视频

`ffmpeg -i <m3u8>` 单连接很慢且会因 TLS 抖动中断，**按分段并行抓再拼**：

```bash
# 从 master 里挑一档（1080p 优先；没有就拿 master 直连让 ffmpeg 选）
grep -A1 'RESOLUTION=1920x1080' master.m3u8 | grep '^http' > rend.txt
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hls_fetch.ps1 -PlaylistFile rend.txt -OutDir "$WORK/seg" -Ext ts -Workers 10
python scripts/concat_segments.py "$WORK/seg" "$WORK/list.txt"
"$FF" -hide_banner -loglevel error -f concat -safe 0 -i "$WORK/list.txt" -c copy -y "$WORK/src.mp4"
"$FF" -v error -show_entries format=duration -of default=nw=1 "$WORK/src.mp4"
```

时长要跟原片对得上（差几秒内）。差太多说明分段有缺口，重跑缺失段。

## 第 4 步 切成翻译块

```bash
python scripts/build_blocks.py "$WORK/cues.json" "$WORK/blocks.json" "$WORK/to_translate.txt"
```

`to_translate.txt` 每行 `[id] 英文`，按 `=== CHUNK n ===` 分块（约 3.8k 字符一块）。

## 第 5 步 自己翻成中文

一块一块读、一块一块写，写到 `$WORK/zh/chunk_NN.txt`，格式 **`[id] 中文`**，id 必须一一对应、不增不减。

要点：

- 口语照口语翻，别翻成书面语；语气词、停顿可以省，信息不能丢。
- 专有名词三选一：保留原文（`Claude Code`、`Ralph loop`）、按约定译（`ghost lesson` → 幽灵课时、`materialize` → 具体化）、或音译。**全文一致**，先扫一眼全文定术语表。
- 代码、命令行、界面文案原样留着，别翻译。
- 一句英文块拆成两句中文没关系，合并成一个 id 也行，但别串到别的 id 上。
- 自动字幕有口误和重复，按语义修顺，别逐字硬搬。

写完全量自检有没有漏 id：

```bash
python scripts/check_zh.py "$WORK/blocks.json" "$WORK/zh"
```

## 第 6 步 合成双语 SRT

```bash
python scripts/build_bilingual_srt.py "$WORK/blocks.json" "$WORK/zh" "$WORK/zh_en.srt"
python scripts/check_srt.py "$WORK/zh_en.srt"     # 叠时 / 超长 / 空行
```

排版规则（脚本已内置，改之前先想清楚）：中文 24 字换行、英文 44 字符换行、中文在上、一屏最多 5 行、英文不断词、中文断点落标点、过短提示合并。

## 第 7 步 烧字幕

```bash
"$FF" -hide_banner -loglevel error -stats \
  -i "$WORK/src.mp4" -i "$WORK/en.srt" \
  -map 0:v:0 -map 0:a:0 -map 1:0 \
  -vf "subtitles='$WORK/zh_en.srt':force_style='FontName=Microsoft YaHei,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=28,Alignment=2'" \
  -c:v libx264 -crf 20 -preset veryfast -c:a copy -c:s mov_text \
  -metadata:s:s:0 language=eng -metadata:s:s:0 title=English \
  -movflags +faststart -y "<输出.mp4>"
```

耗时大约是时长的 1~2 倍。**必须后台跑并给足超时**（前台 120s 会被拦腰砍断），跑完再验。

字号参考：1080p 用 14、720p 用 11；`MarginV` 28~32。

## 第 8 步 验收

```bash
"$FF" -v error -show_entries format=duration -of default=nw=1 "<输出.mp4>"   # 时长须与原片一致
for t in 30 600 1800 2600; do
  "$FF" -hide_banner -loglevel error -ss $t -i "<输出.mp4>" -frames:v 1 -vf scale=960:-1 -y "$WORK/chk_$t.png"
done
```

逐张看图：字幕在、中文在上英文在下、没有被裁切、内容和该时间点说的话对得上。再抽一条 SRT 提示词和原文 cue 比对确认没串行。

## 坑

- **`-ss` 放在 `-i` 前面**会让 PTS 归零，`subtitles` 滤镜从 0 秒开始取字幕，抽出来的帧显示的是开头的字幕，不是 `-ss` 那里的。验收抽帧一律 `-ss` 放在 `-i` 之后。
- 直接 `curl` 外网站点多半握手失败；PowerShell `Invoke-WebRequest` 走系统代理正常。
- 分段并行抓时 URL 是带签名的，**别改参数顺序**；失败重试 5 次仍失败就单独补那几段。
- SRT 用 `utf-8-sig` 写，不然部分播放器把首行当乱码。
- 中英对齐按英文句子边界走，中文按字数比例切到对应位置；按字数硬切会让两条语言各说各的。
- 保留英文原轨（`-map 1:0` + `mov_text`），观众能关掉中文看原声。
- 成片和 `.srt` 一起交付；只要字幕不要视频时只跑第 1、4、5、6 步。
