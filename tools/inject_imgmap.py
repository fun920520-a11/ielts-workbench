# -*- coding: utf-8 -*-
"""把 img/imgmap.json 注入 index.html 的 <script id="imgmap-seed"> 区块。
可重复执行：已存在则替换，不存在则插在 obs-seed 之前。"""
import json, io, re, sys

HTML = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html'
MAP  = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/img/imgmap.json'

raw = json.load(io.open(MAP, encoding='utf-8'))
slim = {k: v['f'] for k, v in raw.items()}
payload = json.dumps(slim, ensure_ascii=False, separators=(',', ':'))

s = io.open(HTML, encoding='utf-8').read()
block = '<script type="application/json" id="imgmap-seed">%s</script>' % payload

pat = re.compile(r'<script type="application/json" id="imgmap-seed">.*?</script>', re.S)
if pat.search(s):
    s2, n = pat.subn(block, s, count=1)
    print('替换已有区块')
else:
    anchor = '<script type="application/json" id="obs-seed">'
    i = s.index(anchor)
    s2 = s[:i] + block + '\n' + s[i:]
    print('插入新区块')

io.open(HTML, 'w', encoding='utf-8', newline='\n').write(s2)
print('映射条目:', len(slim), '| 区块字节:', len(block))
