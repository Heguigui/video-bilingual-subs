# video-bilingual-subs

一个 [Claude Code](https://claude.com/claude-code) 技能：把任意视频做成**中文在上、英文在下**的双字幕 MP4——硬字幕、时间轴对得上，并保留一条可开关的英文软字幕轨。

[English](README.md) · `中文`

```
输入：网页 URL · .m3u8 · .mp4 · 本地文件
输出：1080p H.264 · 中文硬字幕（上） · 英文硬字幕（下） · 英文字幕软轨
```

## 为什么做这个

手动加字幕有四个没人爱干的活：从播放器后面把视频挖出来、拿到可信的时间轴、对着时间轴翻译、再把样式调得在代码编辑器和深色幻灯片上也看得清。前三个机械活交给技能，翻译留在 agent 手里——判断归判断，但术语、行宽、cue 对齐有硬规则兜着。

## 安装

```bash
git clone https://github.com/Heguigui/video-bilingual-subs.git \
  ~/.claude/skills/video-bilingual-subs
```

重启 Claude Code 即自动加载；用 `/video-bilingual-subs` 触发，或者直接说「给这个视频加中文字幕」。

## 用法

```
/video-bilingual-subs https://example.com/talk
/video-bilingual-subs /path/to/talk.mp4
```

流程见 [`SKILL.md`](SKILL.md)，九步：抓页面定位播放器 → 缺 ffmpeg 就装 → 取原片自带字幕做时间轴 → 并行下载分段并拼接 → 切成翻译块 → **逐块翻中文**（agent 干，不是脚本）→ 合成双语 SRT（中文在上、英文在下、按句对齐）→ libass 烧录并保留英文软轨 → ffprobe 加抽帧验收。

两种交付都支持：烧死成片，或者只要 `.srt` 不重编码。

## 输出契约

- 中文每行 ≤ 24 字、英文 ≤ 44 字符、一屏最多 5 行
- 中文不在英文单词中间断行，中文断点落标点
- 无叠时、无空行，`utf-8-sig` 写入，播放器不会把首行显示成乱码
- 成片时长必须与源片一致（差几秒内）；差得多说明分段有缺口，不算完

## 目录

```
SKILL.md                  给 agent 走的主流程
scripts/
  hls_fetch.ps1           并行分段下载（PowerShell，走系统代理）
  vtt_to_cues.py          VTT → cue，去掉 HLS 分段重叠
  concat_segments.py      生成 ffmpeg concat 清单
  build_blocks.py         cue → 句子级翻译块
  check_zh.py             译文覆盖率校验
  build_bilingual_srt.py  句子对齐 + 双语排版
  check_srt.py            叠时 / 超长体检
docs/
  zh-CN/                   以下四份的中文版
  USAGE.md  PIPELINE.md  TROUBLESHOOTING.md  ROADMAP.md
examples/
  sample.zh-en.srt        输出格式样例
```

## 文档

- [用法](docs/zh-CN/USAGE.md) —— 输入、交付方式、什么才算完成
- [流程](docs/zh-CN/PIPELINE.md) —— 九个步骤，以及每一步为什么存在
- [排障](docs/zh-CN/TROUBLESHOOTING.md) —— 你真会撞上的那些故障
- [路线图](docs/zh-CN/ROADMAP.md) —— 双向模式、回译校验、转写兜底

English: [README](README.md) · [docs](docs)

## 环境要求

- Windows（下载器是 PowerShell，其余可移植）
- Python 3.9+
- FFmpeg —— 没有会自动下载
- 能访问片源；遵循系统代理

## 路线图

方向，不是承诺——见 [docs/zh-CN/ROADMAP.md](docs/zh-CN/ROADMAP.md)。

- **双向模式**（计划中）：中译外 / 外译中可切换，版式随目标语言翻转
- 只出字幕、不重编码
- 无字幕轨时用 Whisper 兜底
- ASS 样式预设与预览缩略图

## 许可

MIT —— 见 [LICENSE](LICENSE)。
