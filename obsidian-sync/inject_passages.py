# -*- coding: utf-8 -*-
"""把 passages.json 注入页面（<script type="application/json" id="passage-seed">）。

新增一组词时：写好短文 → build_passages.py → inject_passages.py → 重新发布页面。
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.abspath(os.path.join(HERE, "..", "雅思备考工作台.html"))
data = json.load(io.open(os.path.join(HERE, "passages.json"), encoding="utf-8"))
slug = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
block = '<script type="application/json" id="passage-seed">%s</script>' % slug

html = io.open(PAGE, encoding="utf-8").read()
pat = re.compile(r'<script type="application/json" id="passage-seed">.*?</script>', re.S)
if pat.search(html):
    html = pat.sub(lambda m: block, html, count=1)
    action = "替换"
else:
    m = re.search(r'<script type="application/json" id="obs-seed">.*?</script>', html, re.S)
    assert m, "找不到 obs-seed，无法定位插入点"
    html = html[:m.end()] + "\n" + block + html[m.end():]
    action = "插入"

io.open(PAGE, "w", encoding="utf-8", newline="").write(html)
n = len(data["passages"])
words = sum(len(re.findall(r"[A-Za-z][A-Za-z'-]*", p["en"])) for p in data["passages"])
print("%s内置短文：%d 篇 / %d 英文词 / seed %d 字符 → 页面 %d 字符" % (action, n, words, len(slug), len(html)))
