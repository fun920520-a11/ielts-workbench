# -*- coding: utf-8 -*-
"""把某组的 PNG 转成 webp 并删除原 PNG。用法: python tools/imgconv.py <grp>"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FF = "C:/Users/24277/bin/ffmpeg"
grp = sys.argv[1]
d = os.path.join(ROOT, 'img', 'passages', 'g' + grp)

if not os.path.isdir(d):
    print("目录不存在:", d); sys.exit(1)

pngs = sorted([f for f in os.listdir(d) if f.lower().endswith('.png')])
if not pngs:
    print("无 PNG 可处理:", d); sys.exit(0)

total = 0
for f in pngs:
    src = os.path.join(d, f)
    dst = os.path.join(d, f[:-4] + '.webp')
    r = subprocess.run([FF, '-y', '-i', src, '-vf', 'scale=1280:-2', '-quality', '82', dst],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode == 0 and os.path.exists(dst):
        os.remove(src)
        total += 1
        print("  %s -> %s  (%.0fKB)" % (f, os.path.basename(dst), os.path.getsize(dst)/1024))
    else:
        print("  [失败] %s" % f)
print("组 %s 处理完成: %d 张 webp" % (grp, total))
