# -*- coding: utf-8 -*-
"""
Obsidian -> 雅思备考工作台 同步器（解析层）
只读不写 Obsidian：
  1) 09 英语学习/每日词汇/*.md               -> 单词（2026-10-18 起重构成 5 组一册的分册）
  2) 09 英语学习/雅思备考·阶段1 基础重建期.md  -> 背词规则 + 复习排期
  3) 09 英语学习/BBC 6分钟英语 精听笔记.md      -> 听力 + 口语素材
"""
import os
import re
import io
import json
import hashlib
import datetime

VAULT = r"D:/学习笔记/灵感笔记/09 英语学习"
VOCAB_DIR = "每日词汇"
F_WORDS = "雅思备考·阶段1 基础重建期.md"   # 仅规则 + 复习排期
F_LISTEN = "BBC 6分钟英语 精听笔记.md"


def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_md(s):
    s = s or ""
    s = s.replace("**", "")
    s = re.sub(r"[⚠️]{1,2}", "", s)
    s = s.replace("`", "")
    return s.strip()


def split_row(line):
    """拆 markdown 表格行 -> cells"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_sep(cells):
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells)


# ---------------------------------------------------------------- 单词解析
# 兼容两种结构：
#   旧：阶段1 笔记里 ### 第 N 组 · 日期 / #### 第X类：xxx
#   新（2026-10-18 起）：每日词汇/第01-05组.md 里 ## 第 N 组 · 日期（30 词）/ ### 第一类：xxx
GROUP_RE = re.compile(r"^#{2,3}(?!#)\s*第\s*(\d+)\s*组\s*[·・]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})(.*)$")
CAT_RE = re.compile(r"^#{3,4}(?!#)\s*(?:第[一二三四五六七八九十]+类[:：]|[一二三四五六七八九十]+[、.．])\s*(.+)$")
ANY_HEAD_RE = re.compile(r"^#{1,3}(?!#)\s")


def parse_words(path):
    lines = read_text(path).splitlines()
    words = []
    grp_no, grp_date, cat = 0, "", ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = GROUP_RE.match(ln)
        if m:
            grp_no = int(m.group(1))
            grp_date = m.group(2)
            cat = ""
            i += 1
            continue
        mc = CAT_RE.match(ln)
        if mc:
            cat = re.sub(r"[（(][^）)]*[)）]\s*$", "", strip_md(mc.group(1))).strip()
            i += 1
            continue
        if re.match(r"^#(?!#)\s", ln):
            # 一级标题 = 册级标题（如「# 第 06-10 组（150 词…）」）：离开当前组
            grp_no, grp_date, cat = 0, "", ""
            i += 1
            continue
        if ANY_HEAD_RE.match(ln):
            # 组内其它小节（学之前提醒 / 发音预警 / 拼写分块表 / 词根网络…）：
            # 只清分类，保留组号 —— 否则像「## 第 10 组」下面紧跟「### 学之前」时整组词会丢
            cat = ""
            i += 1
            continue
        # 单词表只出现在「第X类：/一、二、」分类小节下，用 cat 做门禁防误抓其它表格
        if grp_no and cat and ln.strip().startswith("|"):
            cells = split_row(ln)
            if len(cells) >= 7 and not is_sep(cells) and cells[1] not in ("单词", ""):
                raw_word = cells[1]
                flag = "⚠️" if ("⚠" in raw_word) else ""
                w = strip_md(raw_word)
                ipa = strip_md(cells[2])
                pos = strip_md(cells[3])
                zh = strip_md(cells[4])
                chunk = strip_md(cells[5])
                mn = strip_md(cells[6])
                if w and re.search(r"[A-Za-z]", w) and ipa.startswith("/"):
                    slug = re.sub(r"[^a-z0-9]+", "-", w.lower()).strip("-") or ("w%03d" % (len(words) + 1))
                    words.append({
                        "id": "w:" + slug,
                        "w": w,
                        "ipa": ipa.strip("/"),
                        "pos": pos,
                        "zh": zh,
                        "chunk": chunk,
                        "mn": mn,
                        "grp": grp_no,
                        "gdate": grp_date,
                        "cat": cat,
                        "flag": flag,
                    })
        i += 1
    return words


def list_vocab_files(vault=VAULT):
    """每日词汇/ 下的分册（按文件名排序）"""
    d = os.path.join(vault, VOCAB_DIR)
    if not os.path.isdir(d):
        return []
    fs = [os.path.join(d, n) for n in sorted(os.listdir(d))
          if n.lower().endswith(".md") and "第" in n]
    return fs


def parse_words_multi(paths):
    """多册合并，按 id 去重（同词重复出现在不同组时保留首次）"""
    out, seen = [], set()
    for p in paths:
        for w in parse_words(p):
            if w["id"] in seen:
                continue
            seen.add(w["id"])
            out.append(w)
    out.sort(key=lambda x: (x["grp"], ))
    return out


# ---------------------------------------------------------------- 听力解析
EP_RE = re.compile(r"^##\s*Ep\.\s*(\d+)\s*[·・]\s*(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
H4_RE = re.compile(r"^####\s+(.+?)\s*$")
SPK_RE = re.compile(r"^\*\*(.+?)([:：])\*\*\s*(.*)$")


def split_sections(block):
    """把一集切成 {小节名: [行]}"""
    secs, cur = {}, None
    for ln in block:
        m = H3_RE.match(ln)
        if m:
            cur = m.group(1)
            secs[cur] = []
            continue
        if cur is not None:
            secs[cur].append(ln)
    return secs


def find_sec(secs, key):
    for k in secs:
        if key in k:
            return secs[k]
    return []


def parse_meta(block):
    meta = {}
    head = []
    for ln in block:
        if H3_RE.match(ln):
            break
        head.append(ln)
    for ln in head:
        if ln.strip().startswith("|") and "**" in ln:
            cells = split_row(ln)
            if len(cells) >= 2:
                k = strip_md(cells[0])
                v = strip_md("|".join(cells[1:]))
                if k and v:
                    meta[k] = v
    return meta


def parse_pairs(lines):
    pairs, pending = [], None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith(">"):
            continue
        m = SPK_RE.match(s)
        if not m:
            if pending and pending.get("en") and not pending.get("zh"):
                # 续行并入英文
                pending["en"] += " " + strip_md(s)
            continue
        sp, colon, text = m.group(1).strip(), m.group(2), strip_md(m.group(3))
        is_zh = (colon == "：") or bool(re.search(r"[\u4e00-\u9fff]", text))
        if is_zh:
            if pending and not pending.get("zh"):
                pending["zh"] = text
            elif pending:
                pairs.append(pending)
                pending = {"sp": sp, "en": "", "zh": text}
            else:
                pending = {"sp": sp, "en": "", "zh": text}
        else:
            if pending and pending.get("en") and not pending.get("zh"):
                pairs.append(pending)
            pending = {"sp": sp, "en": text, "zh": ""}
            pairs.append(pending)
            pending = pairs[-1]
            continue
        if pending not in pairs:
            pairs.append(pending)
    # 合并：只保留有英文的
    out, by_en = [], set()
    for p in pairs:
        en = (p.get("en") or "").strip()
        if not en or en in by_en:
            continue
        by_en.add(en)
        out.append({"sp": p.get("sp", ""), "en": en, "zh": (p.get("zh") or "").strip()})
    return out


def parse_vocab(secs):
    lines = find_sec(secs, "重点词汇")
    out, header, core = [], None, False
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            if s.startswith("####"):
                header = None
                core = ("核心" in s) or ("必背" in s)
            continue
        cells = split_row(s)
        if is_sep(cells):
            continue
        plain = [strip_md(c) for c in cells]
        if "单词" in plain:
            header = plain
            continue
        idx = {h: k for k, h in enumerate(header or [])}

        def g(k):
            j = idx.get(k)
            return plain[j] if (j is not None and j < len(plain)) else ""

        if not header:
            # 无表头的表：单词 音标 词性 中文 记忆法
            if len(plain) >= 5 and plain[0]:
                out.append({"w": plain[0], "ipa": plain[1].strip("/"), "pos": plain[2],
                            "zh": plain[3], "mn": plain[4], "core": core})
            continue
        w = g("单词")
        if not w:
            continue
        out.append({"w": w, "ipa": g("音标").strip("/"), "pos": g("词性"),
                    "zh": g("中文"), "mn": g("记忆法"), "core": core})
    return out


def parse_quotes(secs):
    lines = find_sec(secs, "摘句")
    blocks, cur = [], None
    for ln in lines:
        m = H4_RE.match(ln)
        if m:
            cur = {"title": strip_md(m.group(1)), "raw": []}
            blocks.append(cur)
            continue
        if cur is not None:
            cur["raw"].append(ln)
    out = []
    for b in blocks:
        q = [strip_md(x.lstrip(">").strip()) for x in b["raw"] if x.strip().startswith(">")]
        q = [x for x in q if x]
        en = q[0] if q else ""
        zh = q[1] if len(q) > 1 else ""
        src = q[2] if len(q) > 2 else ""
        gram, tpl, mock = [], "", ""
        for x in b["raw"]:
            t = re.sub(r"^[-*\s]+", "", strip_md(x))
            if t.startswith("语法拆解"):
                continue
            if t.startswith("可迁移模板"):
                tpl = t.split("：", 1)[-1].strip()
                continue
            if t.startswith("仿写"):
                mock = t.split("：", 1)[-1].strip()
                continue
            if x.strip().startswith("  - ") or x.strip().startswith("  -") or (
                    x.startswith("  ") and x.strip().startswith("-")):
                gram.append(strip_md(x.strip()[1:]))
        out.append({"title": b["title"], "en": en, "zh": zh, "from": src,
                    "grammar": gram, "tpl": tpl, "mock": mock})
    return out


def parse_rhythm(secs):
    lines = find_sec(secs, "断句谱")
    out, cur = [], None
    for ln in lines:
        m = H4_RE.match(ln)
        if m:
            t = strip_md(m.group(1))
            if t.startswith("0") or "符号说明" in t:
                cur = None
                continue
            cur = {"title": t, "lines": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        s = ln.rstrip()
        if not s.strip() or s.strip() in ("---",):
            continue
        if s.strip().startswith("|") or s.strip().startswith(">"):
            continue
        cur["lines"].append(s)
    return [x for x in out if x["lines"]]


def parse_episode(no, title, block):
    meta = parse_meta(block)
    secs = split_sections(block)
    pairs = parse_pairs(find_sec(secs, "中英对照"))
    vocab = parse_vocab(secs)
    quotes = parse_quotes(secs)
    rhythm = parse_rhythm(secs)

    # 本周问题 + 选项 + 答案
    q_text = ""
    for k in meta:
        if "本周问题" in k or "问题" == k:
            q_text = meta[k]
            break
    ans_raw = ""
    for k in meta:
        if "答案" in k:
            ans_raw = meta[k]
            break
    opts = []
    for p in pairs:
        m = re.search(r"Is it[:：]?\s*(.+)", p["en"])
        if m:
            opts = [x[1].strip() for x in re.findall(r"([a-d])\)\s*([^,?.]+)", m.group(1))]
            break
    if not opts:
        m = re.search(r"[Aa]nswers?\s+are\s*(.+)", " ".join(p["en"] for p in pairs))
    ans_idx = 0
    ans_val = re.sub(r"[（(].*?[)）]", "", strip_md(ans_raw)).strip()
    if opts:
        norm = lambda s: re.sub(r"[^0-9a-z]", "", s.lower())
        for i, o in enumerate(opts):
            if norm(o) and norm(o) in norm(ans_val):
                ans_idx = i
                break

    quiz = []
    if q_text and opts:
        quiz.append({"q": q_text, "o": opts, "a": ans_idx})

    script_lines = []
    for p in pairs:
        tag = (p["sp"] or "").split()[0] if p["sp"] else ""
        script_lines.append((tag + ": " if tag else "") + p["en"])

    date_raw = meta.get("播出", "")
    m = re.search(r"([0-9]{4}-[0-9]{2}-[0-9]{2})", date_raw)
    date = m.group(1) if m else ""

    return {
        "id": "ep%02d" % no,
        "code": "Ep.%02d" % no,
        "title": strip_md(title),
        "date": date,
        "hosts": meta.get("主持人", ""),
        "guest": meta.get("嘉宾", ""),
        "topic": meta.get("话题", ""),
        "question": q_text,
        "answer": ans_val,
        "pairs": pairs,
        "script": " ".join(script_lines),
        "quiz": quiz,
        "vocab": vocab,
        "quotes": quotes,
        "rhythm": rhythm,
        "diff": "A类",
        "meta": meta,
    }


def parse_episodes(path):
    text = read_text(path)
    lines = text.splitlines()
    idxs = []
    for i, ln in enumerate(lines):
        m = EP_RE.match(ln)
        if m:
            idxs.append((i, int(m.group(1)), m.group(2)))
    eps = []
    for k, (i, no, title) in enumerate(idxs):
        end = idxs[k + 1][0] if k + 1 < len(idxs) else len(lines)
        eps.append(parse_episode(no, title, lines[i + 1:end]))
    return eps


# ---------------------------------------------------------------- 背词规则解析
def parse_rules(path):
    """从「阶段1」抓背词规则 + 艾宾浩斯复习法（页面只做引用展示）"""
    lines = read_text(path).splitlines()
    out = {"items": [], "notes": [], "intro": [], "times": [], "four": [], "pitfalls": []}

    # ① 背词规则 8 条：📚 学习记录（词汇） 与 🔁 艾宾浩斯 之间的引用块
    st = next((i for i, l in enumerate(lines) if "学习记录（词汇）" in l), None)
    en = next((i for i, l in enumerate(lines)
               if l.startswith("###") and "艾宾浩斯复习法" in l), len(lines))
    if st is not None:
        for l in lines[st:en]:
            s = l.strip()
            if not s.startswith(">"):
                continue
            body = s.lstrip(">").strip()
            if not body:
                continue
            has_no = bool(re.match(r"^\d+\.", body))
            t = re.sub(r"^\d+\.\s*", "", body)
            t = t.replace("**", "").replace("⚠️", "").strip()
            if not t:
                continue
            if has_no:
                out["items"].append(t)
            elif t.startswith("📌") or t.startswith("⚠"):
                out["notes"].append(t)

    # ② 艾宾浩斯复习法
    es = next((i for i, l in enumerate(lines)
               if l.startswith("###") and "艾宾浩斯复习法" in l), None)
    if es is not None:
        seg = lines[es: es + 130]
        for l in seg:
            s = l.strip()
            if s.startswith(">") and ("来源" in s or "对策" in s):
                out["intro"].append(s.lstrip(">").strip().replace("**", ""))

        intable = False
        for l in seg:
            s = l.strip()
            if s.startswith("|"):
                cells = split_row(l)
                if is_sep(cells):
                    continue
                if cells and cells[0] == "类型":
                    intable = True
                    continue
                if intable and len(cells) >= 3 and cells[1]:
                    out["times"].append({"type": strip_md(cells[0]),
                                         "point": strip_md(cells[1]),
                                         "note": strip_md(cells[2])})
            else:
                if intable and out["times"] and s and not s.startswith(">"):
                    intable = False

        i2 = next((i for i, l in enumerate(seg) if "每次复习怎么做" in l), None)
        if i2 is not None:
            for l in seg[i2:i2 + 26]:
                m = re.match(r"^\s*(\d+)\.\s*(.+)$", l)
                if m:
                    out["four"].append({"no": int(m.group(1)),
                                        "text": m.group(2).replace("**", "").strip()})

        for l in seg:
            s = l.strip()
            if s.startswith(">") and ("⚠️" in s or "📌" in s):
                t = s.lstrip(">").strip().replace("**", "")
                if t not in out["pitfalls"]:
                    out["pitfalls"].append(t)
    return out


GRP_TASK_RE = re.compile(r"第\s*(\d+)\s*组(?:前半|后半)?\s*(?:[（(](\d+d)[）)])?")
DATE_ROW_RE = re.compile(r"^\s*\|\s*(\d{1,2})/(\d{1,2})\s*\|\s*第\s*\d+\s*组.*?\|\s*(.+?)\s*\|\s*$")
TODAY_LINE_RE = re.compile(r"\*\*当[日今]复习任务\*\*[：:]\s*(.+)")


def parse_review_plan(path):
    """解析「当日复习任务」排期：优先学习计划表格行，其次各组内的当日复习任务行。
    返回 {"MM-DD": [{"g": 组号, "tag": "7d"}]}，按组号去重、升序。"""
    plan = {}

    def add(key, g, tag):
        lst = plan.setdefault(key, [])
        if not any(x["g"] == int(g) for x in lst):
            lst.append({"g": int(g), "tag": tag or ""})

    cur_date = None  # 当前组标题的日期（YYYY-MM-DD）
    for raw in read_text(path).splitlines():
        m = GROUP_RE.match(raw.strip())
        if m:
            cur_date = m.group(2)
            continue
        if ANY_HEAD_RE.match(raw.strip()):
            if not CAT_RE.match(raw.strip()):
                cur_date = None          # 进入非分组小节，避免把任务归错日期
            continue
        m = DATE_ROW_RE.match(raw)
        if m:
            key = "%02d-%02d" % (int(m.group(1)), int(m.group(2)))
            for g, tag in GRP_TASK_RE.findall(m.group(3)):
                add(key, g, tag)
            continue
        m = TODAY_LINE_RE.search(raw)
        if m and cur_date:
            key = cur_date[5:]  # MM-DD
            for g, tag in GRP_TASK_RE.findall(m.group(1)):
                add(key, g, tag)

    for k in plan:
        plan[k].sort(key=lambda x: x["g"])
    return plan


# ---------------------------------------------------------------- 30 词短文解析
# 结构（2026-10-25 起，第 12 组开始改用「一篇短文」代替 5 个句子）：
#   ## 第 12 组 · 2026-10-21（30 词）
#   ### 📖 学以致用 · 30 词短文
#   > 规则说明引用块（可无）
#   #### Maria's Tuesday（183 words）
#   英文段落…（目标词在笔记里是 **加粗** 的）
#   #### 中文对照
#   中文段落…
#   #### 🪝 记忆钩子
#   钩子正文 + 「覆盖核对」一行
PASSAGE_H3_RE = re.compile(r"^###\s*(?!#).*30\s*词短文")
PASSAGE_H4_RE = re.compile(r"^####\s*(?!#)\s*(.+?)\s*$")
WORDS_CNT_RE = re.compile(r"[（(]\s*\d[\d\s,~、-]*\s*words?\s*[)）]\s*$", re.I)


def _join_paras(lines, drop_cover=False):
    """拼回段落；丢掉引用块和「覆盖核对」这类元信息，去掉 markdown 加粗"""
    out = []
    for l in lines:
        s = l.rstrip()
        if s.startswith(">"):
            continue
        if drop_cover and re.match(r"^\s*(?:\*\*)?覆盖核对", s):
            continue
        out.append(s)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return strip_md(txt)


def parse_passages(paths):
    """从「每日词汇」分册里提取 30 词短文 -> [{g,title,hook,en,zh}]

    只认带「30 词短文」字样的三级标题，所以早期只有「5 个句子」的组不会被误抓，
    组 1-11 的内置短文仍以 pages 里硬编码的那份为准。
    """
    out = []
    for path in paths:
        try:
            lines = read_text(path).splitlines()
        except Exception:
            continue
        cur_g = 0
        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            mg = GROUP_RE.match(line)
            if mg:
                cur_g = int(mg.group(1))
                i += 1
                continue
            if cur_g and PASSAGE_H3_RE.match(line):
                title, mode = "", None
                en_l, zh_l, hook_l = [], [], []
                j = i + 1
                while j < n:
                    l = lines[j]
                    if re.match(r"^#{2,3}\s", l):        # 下一个二级/三级标题 -> 本块结束
                        break
                    mh = PASSAGE_H4_RE.match(l)
                    if mh:
                        head = mh.group(1)
                        if "中文对照" in head:
                            mode = "zh"
                        elif "记忆钩子" in head:
                            mode = "hook"
                        elif not title:
                            title = WORDS_CNT_RE.sub("", head).strip()
                            mode = "en"
                        else:
                            mode = None                  # 其它小节（发音预警等）忽略
                        j += 1
                        continue
                    if mode == "en":
                        en_l.append(l)
                    elif mode == "zh":
                        zh_l.append(l)
                    elif mode == "hook":
                        hook_l.append(l)
                    j += 1
                en = _join_paras(en_l)
                zh = _join_paras(zh_l)
                hook = _join_paras(hook_l, drop_cover=True)
                if en and len(en) >= 80:                 # 太短多半是解析偏了，宁可不要
                    out.append({"g": cur_g, "title": title or ("第 %d 组短文" % cur_g),
                                "hook": hook, "en": en, "zh": zh})
                i = j
                continue
            i += 1
    dedup = {}
    for p in out:
        dedup[p["g"]] = p
    return [dedup[k] for k in sorted(dedup)]


def build(vault=VAULT):
    pw = os.path.join(vault, F_WORDS)          # 规则 + 复习排期
    pl = os.path.join(vault, F_LISTEN)         # 听力 / 口语素材
    vocab_files = list_vocab_files(vault)      # 每日词汇/第01-05组.md …
    if not os.path.exists(pw):
        raise SystemExit("找不到源文件: %s" % pw)
    if not os.path.exists(pl):
        raise SystemExit("找不到源文件: %s" % pl)
    if not vocab_files:
        # 兜底：分册目录不存在时，仍按旧结构在阶段1 里找词表
        vocab_files = [pw]
    words = parse_words_multi(vocab_files)
    eps = parse_episodes(pl)
    rules = parse_rules(pw)
    passages = parse_passages(vocab_files)      # 组 12 起：笔记里写了「30 词短文」的组
    review_plan = parse_review_plan(pw)
    for vf in vocab_files:
        if vf == pw:
            continue
        for k, v in parse_review_plan(vf).items():
            plan = review_plan.setdefault(k, [])
            for item in v:
                if not any(x["g"] == item["g"] for x in plan):
                    plan.append(item)
            plan.sort(key=lambda x: x["g"])
    srcs = []
    order = [(pw, "rules"), (pl, "listen")] + [(v, "vocab") for v in vocab_files if v != pw]
    for p, kind in order:
        srcs.append({
            "kind": kind,
            "name": os.path.basename(p),
            "path": p.replace("\\", "/"),
            "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
            "bytes": os.path.getsize(p),
            "sha256": sha256_of(p),
        })
    fp_src = "|".join(s["sha256"] for s in srcs)
    payload = {
        "version": 1,
        "generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fingerprint": hashlib.sha256(fp_src.encode()).hexdigest()[:16],
        "sources": srcs,
        "words": words,
        "episodes": eps,
        "rules": rules,
        "reviewPlan": review_plan,
        "passages": passages,
        "counts": {"words": len(words), "episodes": len(eps),
                   "groups": len(set(w["grp"] for w in words)),
                   "passages": len(passages),
                   "vocabFiles": len([p for p in vocab_files if p != pw])},
    }
    return payload


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    d = build()
    print(json.dumps(d["counts"], ensure_ascii=False))
    print("fingerprint", d["fingerprint"], "at", d["generatedAt"])
    for s in d["sources"]:
        print(" ", s["name"], s["bytes"], "B", s["mtime"])
    print("--- 前 3 词 ---")
    for w in d["words"][:3]:
        print(json.dumps(w, ensure_ascii=False))
    print("--- 末 2 词 ---")
    for w in d["words"][-2:]:
        print(json.dumps(w, ensure_ascii=False))
    print("--- 组别分布 ---")
    from collections import Counter
    print(Counter([w["grp"] for w in d["words"]]))
    print("--- 集 ---")
    for e in d["episodes"]:
        print(e["code"], e["title"], "| pairs", len(e["pairs"]), "| vocab", len(e["vocab"]),
              "| quiz", len(e["quiz"]), "| quotes", len(e["quotes"]), "| rhythm", len(e["rhythm"]))
        print("   Q:", e["question"][:40], "| 选项", e["quiz"][0]["o"] if e["quiz"] else None,
              "| ans", e["answer"], "-> idx", e["quiz"][0]["a"] if e["quiz"] else None)
        if e["pairs"]:
            print("   pair0:", json.dumps(e["pairs"][0], ensure_ascii=False)[:160])
        if e["vocab"]:
            print("   vocab0:", json.dumps(e["vocab"][0], ensure_ascii=False)[:160])
        if e["quotes"]:
            print("   quote0:", json.dumps(e["quotes"][0], ensure_ascii=False)[:200])
