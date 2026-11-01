# -*- coding: utf-8 -*-
"""为雅思工作台的 660 个词匹配插画（来自 Word Atlas 开放数据集，CC BY 4.0）。

匹配顺序：
  1. 单词归一化（小写、非字母数字转 -）后精确命中
  2. 复数/时态等规则变形
  3. 词性派生后缀剥离后，词根**完整等于**某个图名（不做前缀模糊，避免 apparel→apparent 这类错配）
  4. MANUAL 手工映射兜底
输出 imgmap.json（id -> 文件名）并把用到的图复制到项目 img/words/
"""
import json, io, os, re, shutil, sys

SRC_JSON = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/obsidian-sync/data.json'
POOL     = 'C:/Users/24277/WorkBuddy/word-desk/img'
OUT_IMG  = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/img/words'
OUT_MAP  = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/img/imgmap.json'

# 光靠规则救不回来的，人工指定（语义对得上才写进来）
MANUAL = {
    'promotion': 'promote',
    'enthusiastic': 'enthusiasm',
    'festive': 'festival',
    'editorial': 'editor',
    'propaganda': 'propagate',
    'memorial': 'memory',
    'ageing': 'age',
    'dependency': 'dependent',
    'immigrant': 'immigration',
    'refugee': 'refuge',
    'integration': 'integrate',
    'charitable': 'charity',
    'beneficiary': 'benefit',
    'precision': 'precise',
    'profitable': 'profit',
    'tolerance': 'tolerate',
    'durability': 'durable',
    'automate': 'automatic',
    'perception': 'perceptible',
    'perceive': 'perceptible',
    'trendy': 'trend',
    'synthetic': 'synthesis',
    'wholesale': 'wholesaler',
    'addiction': 'addict',
    'healthcare': 'health',
    'memorize': 'memory',
    'awareness': 'aware',
    'itinerary': 'travel',
    'fry': 'cook',
    'rhythm': 'music',
    'ritual': 'ceremony',
    'theft': 'thief',
    'trial': 'court',
    'witness': 'court',
    'censorship': 'censor',
    'rumour': 'gossip',
    'scandal': 'gossip',
    'longevity': 'long',
    'caregiver': 'nurse',
    'demographic': 'population',
    'frailty': 'fragile',
    'workforce': 'worker',
    'ethnic': 'tribe',
    'multicultural': 'culture',
    'philanthropist': 'donate',
    'altruism': 'generous',
    'compassion': 'sympathy',
    'empathy': 'sympathy',
    'marathon': 'run',
    'doping': 'drug',
    'opponent': 'competitor',
    'venue': 'stadium',
    'disqualify': 'referee',
    'density': 'crowd',
    'amenity': 'facility',
    'landmark': 'monument',
    'skyline': 'city',
    'revitalise': 'renew',
    'apparatus': 'equipment',
    'precision': 'precise',
    'endangered': 'extinct',
    'biodiversity': 'species',
    'sanctuary': 'shelter',
    'enterprise': 'business',
    'revenue': 'money',
    'shareholder': 'share',
    'calibration': 'measure',
    'mould': 'mold',
    'tsunami': 'wave',
    'evacuation': 'escape',
    'intuition': 'instinct',
    'subconscious': 'unconscious',
    'mindset': 'mind',
    'algorithm': 'code',
    'surveillance': 'camera',
    'encryption': 'password',
    'encrypt': 'password',
    'breach': 'leak',
    'hacker': 'hack',
    'firewall': 'wall',
    'phishing': 'fraud',
    'malware': 'virus',
    'bandwidth': 'network',
    'grid': 'electricity',
    'gravity': 'weight',
    'boutique': 'shop',
    'apparel': 'clothes',
    'vintage': 'retro',
    'runway': 'fashion',
    'polyester': 'fabric',
    'dye': 'colour',
    'seam': 'sew',
    'premium': 'luxury',
    'asset': 'property',
    'artefact': 'antique',
    'manuscript': 'manuscript',
    'prehistoric': 'prehistoric',
    'inscription': 'carve',
    'dynasty': 'emperor',
    'prompt': 'quick',
    'infrastructure': 'bridge',
    'spacious': 'space',
    'addiction': 'addict',
    'pension': 'retire',
    'mortality': 'death',
    'fertile': 'farm',
    'referee': 'whistle',
    'coverage': 'news',
    'circulation': 'newspaper',
    'credibility': 'trust',
    'civilisation': 'civilization',
    'comfortable': 'comfort',
}

SUFFIX = ['ations','ation','ition','tions','tion','sion','ments','ment',
          'ances','ance','ences','ence','ities','ity','ness','less','ful',
          'ers','er','ors','or','ists','ist','ism','ives','ive','ous',
          'ally','ly','ing','ed','al','ic','s']

def norm(w):
    s = re.sub(r'[^a-z0-9]+', '-', w.strip().lower())
    return s.strip('-')

def candidates(w):
    n = norm(w)
    out = [n]
    for suf in SUFFIX:
        if n.endswith(suf) and len(n) - len(suf) >= 4:
            base = n[:-len(suf)]
            out += [base, base + 'e', base + 'y']
    m = re.match(r'^(.*?)([a-z])\\2(ing|ed)$', n)
    if m:
        out.append(m.group(1) + m.group(2))
    seen, res = set(), []
    for c in out:
        c = c.strip('-')
        if c and c not in seen:
            seen.add(c); res.append(c)
    return res

def main():
    rows = json.load(io.open(SRC_JSON, encoding='utf-8'))['words']
    pool = set(f[:-5] for f in os.listdir(POOL) if f.endswith('.webp'))
    os.makedirs(OUT_IMG, exist_ok=True)

    mapping, report = {}, {'exact': 0, 'rule': 0, 'manual': 0, 'none': 0}
    missed = []
    for r in rows:
        wid, w = r['id'], r['w']
        hit, how = None, None
        if norm(w) in pool:
            hit, how = norm(w), 'exact'
        else:
            for c in candidates(w):
                if c in pool:
                    hit, how = c, 'rule'
                    break
        if not hit and w.lower() in MANUAL:
            m = MANUAL[w.lower()]
            if m in pool:
                hit, how = m, 'manual'
        if hit:
            mapping[wid] = {'f': hit, 'w': w}
            report[how] += 1
        else:
            report['none'] += 1
            missed.append(w)

    # 复制图片（按 id 去重后按文件名复制一次）
    used = sorted(set(v['f'] for v in mapping.values()))
    for f in used:
        src = os.path.join(POOL, f + '.webp')
        dst = os.path.join(OUT_IMG, f + '.webp')
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    io.open(OUT_MAP, 'w', encoding='utf-8').write(
        json.dumps(mapping, ensure_ascii=False, separators=(',', ':')))

    print('总词数:', len(rows))
    print('  精确命中:', report['exact'])
    print('  规则派生:', report['rule'])
    print('  手工映射:', report['manual'])
    print('  无图    :', report['none'])
    print('  覆盖率  : %.1f%%' % ((len(mapping) / len(rows)) * 100))
    print('复制图片:', len(used), '张')
    if missed:
        print('\n无图清单:')
        for i in range(0, len(missed), 6):
            print('  ' + '  '.join(x.ljust(15) for x in missed[i:i+6]))

if __name__ == '__main__':
    main()
