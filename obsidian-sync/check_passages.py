# -*- coding: utf-8 -*-
"""校验 passages.json：每组 30 词必须全部在英文短文中出现（允许常见词形变化）。"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
passages = json.load(open(os.path.join(HERE, "passages.json"), encoding="utf-8"))["passages"]
data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))

groups = {}
for w in data["words"]:
    groups.setdefault(w["grp"], []).append(w["w"])

def tokens(text):
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())

def match(tok, w):
    w = w.lower()
    if tok == w:
        return True
    if len(w) <= 3:                      # 太短的词要求原形
        return tok in (w, w + "s", w + "es")
    if tok.startswith(w.rstrip("e")) and len(w.rstrip("e")) >= 4:
        return True                      # decorate → decorating / decorated
    if tok.startswith(w) or tok == w + "s" or tok == w + "es":
        return True
    if w.endswith("y") and tok.startswith(w[:-1]):
        return True                      # study → studies / studied
    stem = w[:max(4, len(w) - 2)]
    return tok.startswith(stem)          # benefit → benefited / regulation → regulations

bad = 0
for p in passages:
    g = p["g"]
    toks = set(tokens(p["en"]))
    missing = []
    for w in groups.get(g, []):
        if not any(match(t, w) for t in toks):
            missing.append(w)
    n = len(groups.get(g, []))
    cov = n - len(missing)
    flag = "✅" if not missing else "❌"
    print("%s 第%2d组 %-34s %2d/%2d 词 · 英文 %d 词 · 中文 %d 字" % (
        flag, g, p["title"], cov, n, len(tokens(p["en"])), len(p["zh"])))
    if missing:
        bad += 1
        print("     缺词：", ", ".join(missing))
        # 提示文中出现的近似词，方便改
        for m in missing:
            near = [t for t in toks if t[:4] == m[:4]]
            if near:
                print("       近似：%s → %s" % (m, ", ".join(sorted(near)[:6])))

if len(passages) != len(groups):
    print("⚠️ 篇数 %d ≠ 组数 %d" % (len(passages), len(groups)))
    bad += 1
print("\n%s 共 %d 篇，%d 篇需补词" % ("🎉" if not bad else "⚠️", len(passages), bad))
sys.exit(1 if bad else 0)
