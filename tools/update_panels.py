# -*- coding: utf-8 -*-
"""把某组的分镜数据从 panel_plan.json 增量写入 img/passages/panels.json。
用法: python tools/update_panels.py <grp>"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
plan = json.load(open(os.path.join(HERE, 'panel_plan.json'), encoding='utf-8'))
pp_path = os.path.join(ROOT, 'img', 'passages', 'panels.json')
pp = json.load(open(pp_path, encoding='utf-8'))

grp = sys.argv[1]
v = plan['groups'].get(grp)
if not v:
    print("plan 中无组", grp); sys.exit(1)

pages = []
for pg in v['pages']:
    pages.append({
        'img': pg['img'],
        'caption': pg['caption'],
        'en': pg['sents'],
        'hl': pg['hl'],
        'zh': pg['zh'],
    })
pp['panels'][grp] = {'title': v['title'], 'pages': pages}
json.dump(pp, open(pp_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print("panels.json 已写入组 %s (%d 页)" % (grp, len(pages)))
