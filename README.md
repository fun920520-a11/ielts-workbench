# 雅思备考工作台

一个单文件、零依赖的雅思备考工作台。所有 CSS / JS / 图标 / 数据全部内联在一个 `index.html` 里，
双击就能用，不联网、不装任何东西。

> 当前版本：词汇 22 组 · 660 词 · 每词配插画 · 15 篇 30 词短文 · 朗读 / 记笔记 / 默写 / 答错记忆法提示

---

## 在线访问

部署在 GitHub Pages 上：

```
https://fun920520-a11.github.io/ielts-workbench/
```

手机浏览器打开 → 分享 → 「添加到主屏幕」，就能当 APP 用。

---

## 本地使用

直接用浏览器打开 `index.html` 即可，无需服务器。

**注意**：`index.html` 是唯一维护源，改功能就改它。`archive/` 里是历史快照，只作备份，不再维护。

---

## 数据存储（重要）

页面数据存在**浏览器本地**（localStorage），不上传任何服务器。这带来两个结果：

| 场景 | 表现 |
|---|---|
| 换浏览器 / 换设备打开 | 看到的是**全新数据**（预置示例），不是你在别处的进度 |
| 清浏览器缓存 / 无痕模式 | 数据会**丢** |
| 同一台电脑同一浏览器 | 一直保留，刷新关闭都不丢 |

**迁移数据**：页面内有「导出 JSON 备份」和「导入恢复」按钮。换设备时先导出、再在新设备导入。

> 如果以后要做「手机电脑进度同步」，需要接入云端存储 —— 这是接下来要做的事（见下方规划）。

---

## 目录说明

```
index.html                  ← 工作台本体（唯一维护源）
img/                        ← 单词插画（640 张 WebP）+ imgmap.json 映射表
├── words/                  ← 只放本项目用到的图，按单词命名
└── imgmap.json             ← 词条 id → 图片文件名
tools/                      ← 配图生成与注入脚本
├── make_thumbs.py          ← 为词表匹配插画、复制图片、生成映射
└── inject_imgmap.py        ← 把映射表注入 index.html 的 imgmap-seed 区块
obsidian-sync/              ← 把 Obsidian 词汇笔记同步进页面的工具链
├── obsidian_parse.py       ← 解析 Obsidian 的 Markdown（词表 + 短文）
├── build_passages.py       ← 合并各组短文，生成 passages.json
├── check_passages.py       ← 校验短文覆盖率（目标词是否全中）
├── inject_passages.py      ← 把短文注入 index.html
├── obsidian_sync.py        ← 词汇数据同步主入口
└── README.md               ← 同步流程说明
archive/                    ← 历史版本快照（不进仓库）
```

---

## 单词配图

单词本里每行左边有一张插画，点开可看大图（放大层里能直接朗读）。

- 工具栏的 **🖼 插画** 按钮可以随时关掉，关掉后回到原来的紧凑列表
- 「看词选义」题也会显示插画；「听音辨义」「听音拼写」不显示（否则等于送答案）
- 少数词匹配不到图，用首字母色块占位，不掉版

**新增词条后补图**：把新词加进 Obsidian → 同步 → 重跑下面两步 → 提交推送。

```bash
python tools/make_thumbs.py     # 重新匹配、复制图片
python tools/inject_imgmap.py   # 注入映射表
```

匹配规则：单词小写后非字母数字转连字符精确命中 → 复数/时态等规则变形 → 词性后缀剥离后词根**完整等于**图名（不做前缀模糊，避免 `apparel` 配到 `apparent` 这种错图）→ 手工映射兜底。

---

## 短文同步流程

词汇数据源头在 Obsidian：`D:/学习笔记/灵感笔记/09 英语学习/每日词汇/*.md`

1. 在 Obsidian 里按现有格式写好新的一组词和短文
   （`### 📖 学以致用 · 30 词短文` → `#### 标题（N words）` / `#### 中文对照` / `#### 🪝 记忆钩子`）
2. 跑 `obsidian_parse.py` 解析、`build_passages.py` 合并
3. `check_passages.py` 核对 30/30 覆盖率
4. `inject_passages.py` 写回 `index.html`
5. 提交推送，GitHub Pages 自动更新

页面的读取优先级：**页面内手动修改 > Obsidian 同步 > 内置种子数据**。

---

## 部署

GitHub Pages，`main` 分支根目录直出。推送到 `main` 后约 1 分钟自动生效。

```bash
git add -A && git commit -m "更新内容" && git push
```

---

## 后续规划

- [ ] **数据云同步**：接入云端存储（如 Supabase / WorkBuddy 云服务），实现多设备进度同步
- [ ] **网站化**：拆分模块，支持分享给他人使用、多用户配置
- [ ] **微信小程序**：迁移为小程序（朗读需换 `wx` 音频接口，localStorage 换 `wx.setStorageSync`）
      —— 注意：小程序不能直接跑 HTML，需要重写视图层，但业务逻辑和数据结构可以复用

---

## 技术约束

- 单文件、全内联、**零外部依赖**（不引 CDN / 框架 / 字体 / 图表库）
- 图标全部内联 SVG，图表内联 SVG 手写
- 语音朗读走浏览器 `speechSynthesis` 本地音色（离线可用，无需密钥）
- 唯一的外部资源是 `img/words/` 里的插画（相对路径，同仓库托管，不走 CDN）

---

## 素材授权

单词插画来自开源项目 **Word Atlas（词光）** 的开放数据集，授权 **CC BY 4.0**（署名即可商用）：

- 仓库：https://github.com/designfuchen/word-atlas
- 只使用了 `public/atlas/thumb` 下的插画（256×256 WebP），未使用其应用代码

本项目其余部分（页面代码、调度与复习逻辑、Obsidian 同步工具链）为原创。
