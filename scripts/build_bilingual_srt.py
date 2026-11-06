"""合成中英双语 SRT (中文在上, 英文在下), 同时导出纯英文 SRT 供软轨使用。

用法: python build_bilingual_srt.py <blocks.json> <zhdir> <out_zh_en.srt>

对齐方式: 以英文句子为单位切分, 中文按字符占比切到对应位置, 切点落标点后。
"""
import json
import os
import re
import sys

LINE_ZH = 24     # 中文每行字数上限
LINE_EN = 44     # 英文每行字符上限
PUNCT = '，。！？、：；,.!?'

TOK_ZH = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’.\-/]*\s?|\s+|.", re.S)


def wrap_zh(p):
    if len(p) <= LINE_ZH:
        return p
    toks = TOK_ZH.findall(p)
    total, acc, best, bestscore = len(p), 0, 0, None
    for i, tk in enumerate(toks[:-1]):
        acc += len(tk)
        if acc < 4 or total - acc < 4:
            continue
        score = abs(acc - total / 2)
        # 不在英文单词中间断开
        if re.match(r'[A-Za-z0-9]', toks[i + 1]) and tk[-1:].isspace():
            score += 20
        if bestscore is None or score < bestscore:
            best, bestscore = i + 1, score
    if not best:
        return p
    return ''.join(toks[:best]).rstrip() + '\n' + ''.join(toks[best:]).lstrip()


def wrap_en(t):
    words, lines, buf = t.split(), [], ''
    for w in words:
        cand = (buf + ' ' + w).strip()
        if buf and len(cand) > LINE_EN:
            lines.append(buf)
            buf = w
        else:
            buf = cand
    if buf:
        lines.append(buf)
    return '\n'.join(lines)


def split_sentences(t):
    return [x.strip() for x in re.split(r'(?<=[.!?])\s+', t) if x.strip()] or [t]


def split_zh_by_ratio(t, ratios):
    """按给定比例切中文, 切点尽量落在标点之后"""
    total = sum(ratios) or 1
    acc, prev, bounds = 0, 0, []
    for r in ratios[:-1]:
        acc += r
        target = len(t) * acc / total
        cand = [p + 1 for p, ch in enumerate(t) if ch in PUNCT and p + 1 > prev + 3]
        cut = min(cand, key=lambda p: abs(p - target)) if cand else int(round(target))
        cut = max(cut, prev + 1)
        bounds.append(cut)
        prev = cut
    segs, last = [], 0
    for b in bounds + [len(t)]:
        segs.append(t[last:b])
        last = b
    return segs


def fmt(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main(blocks_path, zhdir, out_path):
    blocks = json.load(open(blocks_path, encoding='utf-8'))
    zh = {}
    for f in sorted(os.listdir(zhdir)):
        for line in open(os.path.join(zhdir, f), encoding='utf-8'):
            m = re.match(r'\[(\d+)\]\s*(.*)', line.strip())
            if m and m.group(2).strip():
                zh[int(m.group(1))] = m.group(2).strip()

    missing = [b['id'] for b in blocks if b['id'] not in zh]
    if missing:
        sys.exit(f'missing translations: {missing[:20]}')

    cues = []
    for b in blocks:
        es = []
        for s in split_sentences(b['text'].strip()):
            words = s.split()
            while len(' '.join(words)) > 90:
                es.append(' '.join(words[:18]))
                words = words[18:]
            if words:
                es.append(' '.join(words))
        es = es[:6]

        zs = split_zh_by_ratio(zh[b['id']], [len(e) for e in es])
        zs += [''] * (len(es) - len(zs))

        pairs = []
        for z, e in zip(zs, es):
            if z.strip() or not pairs:
                pairs.append([z, e])
            else:
                pairs[-1][1] += ' ' + e

        step = max(b['end'] - b['start'], 1.2) / len(pairs)
        cur = b['start']
        for z, e in pairs:
            cues.append([cur, min(cur + step, b['end']), wrap_zh(z.strip()), wrap_en(e)])
            cur += step

    for i in range(len(cues) - 1):
        if cues[i][1] > cues[i + 1][0] - 0.04:
            cues[i][1] = max(cues[i][0] + 0.4, cues[i + 1][0] - 0.05)

    bi, en_only = [], []
    for i, (st, en, z, e) in enumerate(cues, 1):
        stamp = f'{fmt(st)} --> {fmt(en)}'
        bi.append(f'{i}\n{stamp}\n{z}\n{e}\n')
        en_only.append(f'{i}\n{stamp}\n{e}\n')

    open(out_path, 'w', encoding='utf-8-sig').write('\n'.join(bi))
    en_path = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'en.srt')
    open(en_path, 'w', encoding='utf-8-sig').write('\n'.join(en_only))
    print(f'cues {len(cues)} -> {out_path} , {en_path}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
