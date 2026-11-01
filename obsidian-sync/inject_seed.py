# -*- coding: utf-8 -*-
"""把 data.json 重新注入页面的内置快照 <script id="obs-seed">。"""
import io, json, re, sys

PAGE = r"C:\Users\24277\WorkBuddy\2026-10-17-16-23-57\雅思备考工作台.html"
DATA = r"C:\Users\24277\WorkBuddy\2026-10-17-16-23-57\obsidian-sync\data.json"

sys.stdout.reconfigure(encoding="utf-8")
s = io.open(PAGE, encoding="utf-8").read()
d = json.load(io.open(DATA, encoding="utf-8"))
seed = json.dumps(d, ensure_ascii=False, separators=(",", ":"))

m = re.search(r'(<script[^>]*id="obs-seed"[^>]*>)(.*?)(</script>)', s, re.S)
assert m, "找不到 obs-seed"
old_len = len(m.group(2))
s = s[:m.start(2)] + seed + s[m.end(2):]
io.open(PAGE, "w", encoding="utf-8", newline="\n").write(s)

# 校验
d2 = json.loads(seed)
print("seed: %d -> %d 字节 | 页面: %d 字符" % (old_len, len(seed), len(s)))
print("词数校验:", len(d2["words"]), "| 组数:", len(set(w["grp"] for w in d2["words"])),
      "| reviewPlan 日期:", len(d2.get("reviewPlan", {})))
