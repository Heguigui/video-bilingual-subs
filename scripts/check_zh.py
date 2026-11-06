"""校验中文译文覆盖了全部 block id。

用法: python check_zh.py <blocks.json> <zhdir>
"""
import json
import os
import re
import sys

blocks = json.load(open(sys.argv[1], encoding='utf-8'))
zhdir = sys.argv[2]

zh = {}
for f in sorted(os.listdir(zhdir)):
    for line in open(os.path.join(zhdir, f), encoding='utf-8'):
        m = re.match(r'\[(\d+)\]\s*(.*)', line.strip())
        if m and m.group(2).strip():
            zh[int(m.group(1))] = m.group(2).strip()

missing = [b['id'] for b in blocks if b['id'] not in zh]
extra = [i for i in zh if i >= len(blocks)]
print(f'blocks {len(blocks)} translated {len(zh)} missing {len(missing)} extra {extra}')
if missing:
    print('missing ids:', missing[:60])
    sys.exit(1)
