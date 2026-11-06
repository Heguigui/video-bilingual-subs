"""把细碎的 cue 合并成句子级翻译块, 并切成翻译批次。

用法: python build_blocks.py <cues.json> <blocks.json> <to_translate.txt>
"""
import json
import re
import sys

END = re.compile(r'[.!?]["\')\]]?$')
MAXC = 380


def main(cues_path, blocks_path, txt_path):
    cues = json.load(open(cues_path, encoding='utf-8'))

    blocks = []
    cur = None
    for st, en, t in cues:
        if cur is None:
            cur = {'start': st, 'end': en, 'text': t}
        else:
            cur['text'] += ' ' + t
            cur['end'] = en
        if (END.search(t) and len(cur['text']) >= 90) or len(cur['text']) >= MAXC:
            txt = cur['text']
            if len(txt) >= MAXC:
                cut = max(txt.rfind('. '), txt.rfind('? '), txt.rfind('! '))
                if cut > 60:
                    head, tail = txt[:cut + 1], txt[cut + 2:]
                    frac = len(head) / len(txt)
                    mid = cur['start'] + (cur['end'] - cur['start']) * frac
                    blocks.append({'start': cur['start'], 'end': mid, 'text': head})
                    cur = {'start': mid, 'end': cur['end'], 'text': tail}
                    continue
            blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)

    # 去重复句 (分段重叠残留)
    out = []
    for b in blocks:
        if out and (out[-1]['text'] == b['text'] or out[-1]['text'].endswith(b['text'])):
            continue
        out.append(b)
    for i, b in enumerate(out):
        b['id'] = i

    json.dump(out, open(blocks_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    lines, size = [], 0
    for b in out:
        if size == 0:
            lines.append('=== CHUNK ===')
        lines.append(f"[{b['id']}] {b['text']}")
        size += len(b['text'])
        if size > 3800:
            size = 0
    open(txt_path, 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'blocks {len(out)}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
