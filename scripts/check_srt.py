"""SRT 体检: 叠时、超长行、空行、总条数。

用法: python check_srt.py <file.srt> [max_line_chars]
超长或叠时以退出码 1 结束。
"""
import re
import sys

path = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

TS = re.compile(r'(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)')
blocks = [b for b in open(path, encoding='utf-8-sig').read().strip().split('\n\n') if b.strip()]

prev_end, overlaps, long_lines, empty = -1, 0, [], 0
for b in blocks:
    lines = b.split('\n')
    m = TS.search(lines[1]) if len(lines) > 1 else None
    if not m:
        empty += 1
        continue
    g = m.groups()
    st = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
    en = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
    if st < prev_end - 0.001:
        overlaps += 1
    prev_end = en
    for t in lines[2:]:
        if not t.strip():
            empty += 1
        elif len(t) > limit:
            long_lines.append(t)

print(f'cues {len(blocks)} overlaps {overlaps} long_lines {len(long_lines)} empty {empty}')
for t in long_lines[:10]:
    print(f'  {len(t)}: {t}')
if overlaps or long_lines:
    sys.exit(1)
