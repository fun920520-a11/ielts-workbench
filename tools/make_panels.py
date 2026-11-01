# -*- coding: utf-8 -*-
"""为短文记词生成「图文翻页卡」规划 + ImageGen 提示词。
读 obsidian-sync/passages.json（15 篇短文）和 obsidian-sync/data.json（22 组词），
为每组切句、分 5-6 页、均匀分配该组 30 词，输出 tools/panel_plan.json。
页面 JS（pcRender）按 img/caption/zh/hl 渲染，无需改动。
"""
import json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PS = os.path.join(ROOT, 'obsidian-sync', 'passages.json')
DATA = os.path.join(ROOT, 'obsidian-sync', 'data.json')
OUT = os.path.join(HERE, 'panel_plan.json')

passages = json.load(open(PS, encoding='utf-8'))['passages']
data = json.load(open(DATA, encoding='utf-8'))
words = data['words']

zh_of = {}
for w in words:
    zh_of[str(w.get('w', '')).lower()] = w.get('zh', '')
words_by_grp = {}
for w in words:
    words_by_grp.setdefault(w['grp'], []).append(w['w'])

# 每组主题定调（英文，仅用于 ImageGen 提示词定调，不展示给用户）
THEME = {
    2:  "Anna, a part-time worker, struggling to balance a second job with her own health",
    3:  "a young person leaving a quiet rural village to start a new life in the busy city",
    4:  "a careful budget traveler planning a cheap trip with very limited money",
    5:  "a cozy rainy Sunday cooking class where beginners learn to cook together",
    6:  "a person moving into a newly rented flat and setting up their first home",
    7:  "an outdoor art festival happening in the rain, with stalls and performances",
    8:  "an elderly grandmother learning to use the internet and modern technology",
    9:  "a family happily celebrating the traditional Lantern Festival at night",
    10: "a bilingual witness helping the police with a case using two languages",
    11: "a news story about a fake luxury bag that was sold and made the headlines",
    12: "Maria's busy Tuesday, running errands and working through a full day",
    13: "a charity marathon where runners raise money for a good cause",
    14: "a farmer's son moving from the fields to the city to find work",
    15: "an engineer volunteering to protect wildlife in a nature sanctuary",
}

def split_sents(en):
    return [s.strip() for s in re.split(r'(?<=[.!?])', en) if s.strip()]

def split_zh(zh):
    return [s.strip() for s in re.split(r'(?<=[。！？])', zh) if s.strip()]

def partition(items, n):
    if n <= 0:
        return [items]
    k, m = divmod(len(items), n)
    res, idx = [], 0
    for i in range(n):
        size = k + (1 if i < m else 0)
        res.append(items[idx:idx + size])
        idx += size
    return res

def first_zh(z):
    """取中文释义的第一个义项，避免多义项堆叠"""
    if not z:
        return ''
    for sep in ['；', '·', ',', '，', '/']:
        if sep in z:
            z = z.split(sep)[0]
    return z.strip()

def build_prompt(theme, sents, hl):
    # 去掉英文句子里的双引号/弯引号，避免破坏 ImageGen 的 JSON 参数结构
    caption_text = ' '.join(sents).replace('"', '').replace('“', '').replace('”', '').replace('‘', '').replace('’', '')
    # 图内高亮前 4 个，避免太挤；卡片底部仍显示全部 hl
    hl_img = hl[:4]
    hl_text = ', '.join(hl_img)
    return (
        "Flat cartoon storybook illustration, warm colors, " + theme + ". "
        "[Instruction for the illustrator, do NOT write this instruction text into the image: "
        "emphasize these keywords in bold red inside the caption: " + hl_text + "] "
        "Caption text at the bottom in a clean rounded speech area: " + caption_text + " "
        "16:9 wide composition, soft lighting, no watermark. Avoid small decorative text labels in the scene."
    )

plan = {"groups": {}}
for it in passages:
    g = it['g']
    if g == 1:
        continue  # 第 1 组已手工完成
    en = it['en']
    zh = it['zh']
    sents = split_sents(en)
    n = 5 if len(sents) <= 15 else 6
    s_chunks = partition(sents, n)
    wlist = words_by_grp.get(g, [])
    w_chunks = partition(wlist, n)
    zh_sents = split_zh(zh)
    z_chunks = partition(zh_sents, n)
    theme = THEME.get(g, it['title'])
    pages = []
    for i in range(n):
        hl = w_chunks[i]
        cap_words = [first_zh(zh_of.get(str(w).lower(), '')) for w in hl[:2] if zh_of.get(str(w).lower())]
        caption = '·'.join(cap_words) if cap_words else it['title']
        zh_text = ''.join(z_chunks[i]) if i < len(z_chunks) else ''
        prompt = build_prompt(theme, s_chunks[i], hl)
        pages.append({
            "page": i + 1,
            "sents": s_chunks[i],
            "hl": hl,
            "caption": caption,
            "zh": zh_text,
            "prompt": prompt,
            "img": "g%d/g%d-%d.webp" % (g, g, i + 1),
        })
    plan["groups"][str(g)] = {"title": it['title'], "theme": theme, "pages": pages}

json.dump(plan, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# 汇总
total = sum(len(v['pages']) for v in plan['groups'].values())
print("已生成规划：组 2-15，共 %d 篇，%d 页（张）图" % (len(plan['groups']), total))
for g, v in plan['groups'].items():
    print("  组%-2s %-34s 页=%d" % (g, v['title'][:34], len(v['pages'])))
