# 排障

[English](../TROUBLESHOOTING.md) · `中文`

## `curl: (35) schannel: failed to receive handshake`

在有过滤的网络里，直连绝大多数境外站点都会这样。换 PowerShell——`Invoke-WebRequest` 走系统代理：

```bash
powershell -NoProfile -Command "Invoke-WebRequest -Uri '<URL>' -UseBasicParsing -OutFile 'out'"
```

如果确实要让 ffmpeg 自己取东西，它认 `-http_proxy http://127.0.0.1:<端口>`。

## 没装 ffmpeg

别 `pip install` 一个包装层。下静态包，直接用二进制：

```bash
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -UseBasicParsing -OutFile 'ffmpeg.zip'; Expand-Archive ffmpeg.zip -DestinationPath ff -Force"
```

## 每句话都出现两遍

分段重叠没去掉。确认 `vtt_to_cues.py` 跑过，且它报的数量比原始 cue 少。

## 单连接下载后时间全错

ffmpeg 跨一次卡死的 TLS 会话重试后丢了时间对齐。解法就是分段下载加拼接；编码前先核拼接后的时长与源片一致。

## 验收帧不管给什么时间都显示片头字幕

`-ss` 放在 `-i` 前面会重置 PTS，`subtitles` 滤镜就从零开始读。抽帧时 `-ss` 必须放在 `-i` **后面**。

## 英文长行或中文断在词中间

换行函数按 token 切，且拒绝在英文单词内部断。改过 `build_bilingual_srt.py` 就重跑 `check_srt.py`——任何超长行都会让它失败。

## 首行字幕乱码

SRT 没带 BOM。所有脚本都用 `utf-8-sig` 写；自己写的话照做。

## `missing translations: [..]`

某个块 id 被漏掉或重编号了。`check_zh.py` 会报 id；在 `zh/chunk_NN.txt` 里按 `[id] 中文` 补上。

## 编码跑到一半被杀

前台工具的超时（默认 120 秒）切断了它。改用 `run_in_background`，超时给到片长的数倍；1080p 大约是实时的 2 倍。

## 发布时报 `Resource not accessible by personal access token`

没有 **Administration: write** 的细粒度 token 建不了仓库。要么在浏览器里手动建空仓库，要么补上这个权限，再推。

## 二次发布

先看片源许可。下载和重编码不带来任何权利；字幕文本属于讲者。
