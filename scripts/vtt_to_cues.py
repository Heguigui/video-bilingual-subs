"""把 HLS 字幕分段里的 VTT 汇总成 cue 列表, 去掉分段重叠造成的重复。

用法: python vtt_to_cues.py <segdir> <out.json>
输出: [[start_sec, end_sec, text], ...]  按时间排序
"""
import glob
import json
import os
import re
import sys

TS = re.compile(
    r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})'
)


def sec(g):
    return int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000.0


def main(segdir, out):
    cues = []
    for f in sorted(glob.glob(os.path.join(segdir, '*.vtt'))):
        lines = open(f, encoding='utf-8-sig', errors='replace').read().splitlines()
        i = 0
        while i < len(lines):
            m = TS.search(lines[i])
            if not m:
                i += 1
                continue
            g = m.groups()
            st, en = sec(g[:4]), sec(g[4:])
            i += 1
            buf = []
            while i < len(lines) and lines[i].strip() and not TS.search(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            text = re.sub(r'<[^>]+>', '', ' '.join(buf)).strip()
            if text:
                cues.append([st, en, text])

    cues.sort(key=lambda c: c[0])

    # 分段重叠: 同一 (时间, 文本) 会出现两次
    seen, uniq = set(), []
    for st, en, t in cues:
        key = (round(st, 1), t)
        if key in seen:
            continue
        seen.add(key)
        uniq.append([st, en, t])

    # 句子被截断后重复的尾巴
    out_cues = []
    for c in uniq:
        if out_cues and (c[2] == out_cues[-1][2] or out_cues[-1][2].endswith(c[2])):
            continue
        out_cues.append(c)

    json.dump(out_cues, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'cues {len(cues)} -> {len(out_cues)}')
    if not out_cues:
        sys.exit('no cues parsed')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
