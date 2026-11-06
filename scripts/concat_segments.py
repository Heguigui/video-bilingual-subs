"""给 ffmpeg -f concat 生成清单, 顺序按文件名(已零填充)。

用法: python concat_segments.py <segdir> <list.txt>
"""
import glob
import os
import sys

segdir, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(segdir, '*.ts')))
if not files:
    sys.exit('no .ts segments')
with open(out, 'w', encoding='utf-8') as fh:
    for f in files:
        fh.write("file '%s'\n" % os.path.abspath(f).replace('\\', '/').replace("'", r"'\''"))
print(f'{len(files)} segments')
