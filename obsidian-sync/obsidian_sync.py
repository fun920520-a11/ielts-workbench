# -*- coding: utf-8 -*-
"""
Obsidian -> 雅思备考工作台 · 本地同步桥

用法（双击「启动同步桥.bat」等价于 serve）：
    python obsidian_sync.py serve            # 启动本地桥（默认 127.0.0.1:8787）
    python obsidian_sync.py once             # 只解析一次，写出 data.json
    python obsidian_sync.py serve --port 8800

接口：
    GET  /api/ping     健康检查
    GET  /api/status   同步状态（指纹、上次同步时间、词数/集数）
    GET  /api/sync     触发重新解析（内容未变则复用缓存）  ?force=1 强制
    GET  /api/data     返回完整数据（单词 + 听力）
"""
import os
import re
import sys
import json
import time
import uuid
import hashlib
import argparse
import datetime
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obsidian_parse as op  # noqa: E402

DATA_FILE = os.path.join(HERE, "data.json")


def resolve_page():
    """探测工作台页面文件。

    部署到 GitHub Pages 时首页必须是 index.html，所以老文件名
    「雅思备考工作台.html」已改名为 index.html。这里按优先级探测，
    两个名字都认，避免脚本抱着旧路径报「工作台页面不存在」。
    """
    base = os.path.dirname(HERE)
    for name in ("index.html", "雅思备考工作台.html"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return os.path.join(base, "index.html")


PAGE_FILE = resolve_page()
LOCK = threading.Lock()
STATE = {"payload": None, "lastSync": None, "lastWrite": None, "mtime": 0.0}


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)


def load_cache():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log("缓存读取失败: %s" % e)
    return None


def current_payload():
    """取当前数据；data.json 被外部重写过（mtime 变了）就重新载入。

    否则桥会一直抱着启动时读进内存的旧词表 —— 表现为「笔记里明明有第 11 组，
    页面上还是 10 组」，而且只有重启桥才好。这里按文件时间自动跟上。
    """
    p = STATE["payload"]
    try:
        m = os.path.getmtime(DATA_FILE)
    except OSError:
        m = 0.0
    if p is None:
        p = load_cache()
        STATE["payload"] = p
        STATE["mtime"] = m
        return p
    if m and m > (STATE.get("mtime") or 0) + 0.0005:
        disk = load_cache()
        if disk and disk.get("fingerprint") != p.get("fingerprint"):
            p = disk
            STATE["payload"] = p
            STATE["lastSync"] = p.get("generatedAt")
            log("data.json 被外部更新 → 已重新载入 %s 词 / %s 集（无需重启桥）"
                % ((p.get("counts") or {}).get("words", "?"), (p.get("counts") or {}).get("episodes", "?")))
        STATE["mtime"] = m
    return p


def do_sync(force=False, persist=True):
    """重新解析 Obsidian；内容未变则直接复用缓存"""
    with LOCK:
        old = STATE["payload"] or load_cache()
        fresh = op.build()
        fp = fresh["fingerprint"]
        # 防呆：解析出 0 词但历史有词 → 多半是笔记结构变了（词表搬家/标题层级变了），拒绝覆盖
        old_n = ((old or {}).get("counts") or {}).get("words") or 0
        new_n = (fresh.get("counts") or {}).get("words") or 0
        if old and old_n and not new_n:
            log("⚠️ 解析得到 0 词，但历史有 %d 词 —— 已拒绝覆盖缓存。" % old_n)
            log("   请检查：每日词汇/ 分册是否存在、组标题是否为「## 第 N 组 · YYYY-MM-DD」")
            return {"ok": False, "unchanged": True, "fingerprint": old.get("fingerprint"),
                    "counts": old.get("counts"), "lastSync": old.get("generatedAt"),
                    "error": "解析得到 0 词，已拒绝覆盖缓存", "payload": old}
        changed = (not old) or old.get("fingerprint") != fp
        if not changed and not force:
            STATE["payload"] = old
            _c = old.get("counts") or {}
            log("内容未变（指纹 %s）—— 笔记没改动，数据已是最新：%s 词 / %s 集。"
                "这一行不是报错，页面照样可以同步"
                % (fp, _c.get("words", "?"), _c.get("episodes", "?")))
            return {"ok": True, "unchanged": True, "fingerprint": fp,
                    "counts": old.get("counts"), "lastSync": STATE["lastSync"] or old.get("generatedAt"),
                    "payload": old}
        fresh["generatedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        STATE["payload"] = fresh
        STATE["lastSync"] = fresh["generatedAt"]
        if persist:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(fresh, f, ensure_ascii=False, indent=1)
            os.replace(tmp, DATA_FILE)
            STATE["lastWrite"] = fresh["generatedAt"]
            try:
                STATE["mtime"] = os.path.getmtime(DATA_FILE)
            except OSError:
                pass
        log("同步完成：%d 词 / %d 集，指纹 %s，%s" % (
            fresh["counts"]["words"], fresh["counts"]["episodes"], fp,
            "已写入缓存" if (changed or force) else ""))
        return {"ok": True, "unchanged": False, "fingerprint": fp,
                "counts": fresh["counts"], "lastSync": fresh["generatedAt"],
                "payload": fresh}


def status():
    p = current_payload()
    if not p:
        return {"ok": True, "ready": False, "lastSync": None,
                "message": "尚未同步过，点一次「同步 Obsidian」即可"}
    return {
        "ok": True, "ready": True,
        "lastSync": STATE["lastSync"] or p.get("generatedAt"),
        "fingerprint": p.get("fingerprint"),
        "counts": p.get("counts"),
        "sources": p.get("sources"),
    }


# ==================================================================== 本地 ASR
# 音频与字幕存这里：audio/<id>.<ext> + audio/<id>.json
AUDIO_DIR = os.path.join(HERE, "audio")
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".webm", ".mp4"}
MIME = {".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".mp4": "audio/mp4",
        ".wav": "audio/wav", ".ogg": "audio/ogg", ".opus": "audio/ogg",
        ".flac": "audio/flac", ".aac": "audio/aac", ".webm": "audio/webm"}
WEB_MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
            ".ico": "image/x-icon", ".json": "application/json; charset=utf-8",
            ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
            ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}
# 只开放这几个子目录给页面读取，避免把整个项目目录暴露出去
STATIC_DIRS = ("img",)
JOBS = {}
ASR_CONF = {"model": "base.en", "device": "cpu", "compute_type": "int8", "beam_size": 5}


def asr_conf():
    """asr-config.json 可覆盖默认（模型档位 / device / 下载源）"""
    p = os.path.join(HERE, "asr-config.json")
    conf = dict(ASR_CONF)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8-sig") as f:
                conf.update(json.load(f))
        except Exception as e:
            log("asr-config.json 读取失败，用默认值：%s" % e)
    return conf


def _audio_path(aid, ext=None):
    if ext:
        return os.path.join(AUDIO_DIR, aid + ext)
    for e in AUDIO_EXT:
        p = os.path.join(AUDIO_DIR, aid + e)
        if os.path.isfile(p):
            return p
    return ""


def _safe_aid(aid):
    return re.match(r"^[0-9a-f]{8,32}$", aid or "") is not None


def audio_meta(aid):
    p = os.path.join(AUDIO_DIR, aid + ".json")
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def save_meta(aid, meta):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    p = os.path.join(AUDIO_DIR, aid + ".json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    os.replace(tmp, p)


def list_audio():
    out = []
    if not os.path.isdir(AUDIO_DIR):
        return out
    for fn in os.listdir(AUDIO_DIR):
        if not fn.endswith(".json"):
            continue
        aid = fn[:-5]
        m = audio_meta(aid)
        if not m:
            continue
        ap = _audio_path(aid)
        out.append({"id": aid, "name": m.get("name") or (os.path.basename(ap) if ap else aid),
                    "dur": m.get("dur") or 0, "cues": len(m.get("cues") or []),
                    "createdAt": m.get("createdAt") or 0,
                    "hasFile": bool(ap)})
    out.sort(key=lambda x: -(x.get("createdAt") or 0))
    return out


def start_asr_job(aid):
    job = {"id": uuid.uuid4().hex[:10], "aid": aid, "state": "running",
           "progress": 0.0, "msg": "准备中…", "error": "", "startedAt": time.time()}
    JOBS[job["id"]] = job

    def run():
        try:
            import asr_core as A
            conf = asr_conf()
            path = _audio_path(aid)
            if not path:
                raise RuntimeError("音频文件不存在（可能被删了），请重新导入")
            meta = audio_meta(aid) or {"id": aid, "name": os.path.basename(path)}
            dur = meta.get("dur") or A.probe_duration(path)
            cues, info = A.transcribe(path, conf, job)
            for c in cues:
                c.pop("zh", None)
            meta.update({"id": aid, "dur": dur or info.get("duration") or 0,
                         "cues": cues, "engine": "faster-whisper",
                         "model": conf.get("model"), "transcribedAt": time.time()})
            save_meta(aid, meta)
            job.update({"state": "done", "progress": 1.0,
                        "msg": "完成：%d 句 / %s" % (len(cues), _fmt_sec(dur)), "cues": len(cues)})
            log("ASR 完成 %s：%d 句" % (meta.get("name"), len(cues)))
        except Exception as e:
            job.update({"state": "error", "msg": "失败", "error": str(e)})
            log("ASR 失败 %s：%s" % (aid, e))

    threading.Thread(target=run, daemon=True).start()
    return job


def _fmt_sec(t):
    t = float(t or 0)
    return "%d 分 %02d 秒" % (int(t // 60), int(t % 60))


def _range_send(handler, path, ctype):
    """支持 Range 的音频流（拖进度条才不用等整个文件）"""
    size = os.path.getsize(path)
    rng = handler.headers.get("Range") or ""
    start, end = 0, size - 1
    code = 200
    if rng.startswith("bytes="):
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        if m:
            if m.group(1):
                start = int(m.group(1))
                if m.group(2):
                    end = min(int(m.group(2)), size - 1)
            elif m.group(2):
                start = max(0, size - int(m.group(2)))
            if start >= size:
                handler.send_response(416)
                handler.send_header("Content-Range", "bytes */%d" % size)
                handler._cors()
                handler.send_header("Content-Length", "0")
                handler.end_headers()
                return
            code = 206
    handler.send_response(code)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(end - start + 1))
    if code == 206:
        handler.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
    handler.send_header("Cache-Control", "no-store")
    handler._cors()
    handler.end_headers()
    with open(path, "rb") as f:
        f.seek(start)
        left = end - start + 1
        while left > 0:
            buf = f.read(min(262144, left))
            if not buf:
                break
            handler.wfile.write(buf)
            left -= len(buf)


class Handler(BaseHTTPRequestHandler):
    server_version = "ObsidianBridge/1.1"

    def _cors(self):
        origin = self.headers.get("Origin") or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "false")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Vary", "Origin")

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        """把项目根目录 img/ 下的图片和 panels.json 发给页面。

        之前桥只认 / 和 /api/*，本机直连版打开时所有插图都是 404，
        表现就是「用桥打开，图全没了、翻页卡也不出来」。
        """
        base = os.path.dirname(HERE)
        rel = os.path.normpath(path.lstrip("/").replace("\\", "/"))
        if rel.startswith("..") or os.path.isabs(rel):
            return self._json({"ok": False, "error": "非法路径"}, 400)
        top = rel.replace("\\", "/").split("/", 1)[0]
        if top not in STATIC_DIRS:
            return self._json({"ok": False, "error": "not found"}, 404)
        full = os.path.join(base, rel)
        if not os.path.isfile(full):
            return self._json({"ok": False, "error": "文件不存在"}, 404)
        ext = os.path.splitext(full)[1].lower()
        ctype = WEB_MIME.get(ext) or MIME.get(ext) or "application/octet-stream"
        try:
            with open(full, "rb") as f:
                body = f.read()
        except Exception as e:
            return self._json({"ok": False, "error": str(e)}, 500)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=300")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query or "")
        try:
            if path == "/api/ping":
                return self._json({"ok": True, "service": "obsidian-bridge", "ts": int(time.time())})
            if path == "/api/status":
                return self._json(status())
            if path == "/api/data":
                p = current_payload()
                if not p:
                    r = do_sync()
                    p = r["payload"]
                return self._json(p)
            if path == "/api/sync":
                force = q.get("force", ["0"])[0] in ("1", "true", "yes")
                r = do_sync(force=force)
                p = r.pop("payload")
                r["counts"] = r.get("counts") or p.get("counts")
                r["sources"] = p.get("sources")
                r["generatedAt"] = p.get("generatedAt")
                return self._json(r)
            if path in ("/", "/index", "/index.html", "/bench"):
                # 同源直连版：页面和接口同源，浏览器不会拦截
                page = resolve_page()
                if os.path.exists(page):
                    with open(page, "rb") as f:
                        body = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self._cors()
                    self.end_headers()
                    self.wfile.write(body)
                    return
                return self._json({"ok": False, "error": "工作台页面不存在: %s（应在项目根目录放 index.html）" % page}, 404)

            # ---------------- 本地 ASR（听力页用） ----------------
            if path == "/api/asr/status":
                try:
                    import asr_core as A
                    st = A.status(asr_conf())
                    st["stored"] = len(list_audio())
                    return self._json(st)
                except Exception as e:
                    return self._json({"ok": False, "installed": False, "error": str(e)})
            if path == "/api/asr/list":
                return self._json({"ok": True, "items": list_audio()})
            if path == "/api/asr/jobs":
                jid = (q.get("id", [""])[0] or "").strip()
                j = JOBS.get(jid)
                if not j:
                    return self._json({"ok": False, "error": "任务不存在（桥可能重启过，请重新生成）"}, 404)
                return self._json(j)
            if path == "/api/asr/cues":
                aid = (q.get("id", [""])[0] or "").strip()
                if not _safe_aid(aid):
                    return self._json({"ok": False, "error": "id 非法"}, 400)
                m = audio_meta(aid)
                if not m:
                    return self._json({"ok": False, "error": "还没有这个音频的字幕"}, 404)
                return self._json(m)
            if path == "/api/asr/audio":
                aid = (q.get("id", [""])[0] or "").strip()
                if not _safe_aid(aid):
                    return self._json({"ok": False, "error": "id 非法"}, 400)
                p = _audio_path(aid)
                if not p:
                    return self._json({"ok": False, "error": "音频不存在，请重新导入"}, 404)
                return _range_send(self, p, MIME.get(os.path.splitext(p)[1].lower(), "application/octet-stream"))
            if path.startswith("/img/"):
                return self._static(path)
            return self._json({"ok": False, "error": "not found"}, 404)
        except SystemExit as e:
            return self._json({"ok": False, "error": str(e)}, 500)
        except Exception as e:
            log("请求出错: %r" % e)
            return self._json({"ok": False, "error": str(e)}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query or "")

        # ---------------- 上传音频（裸二进制，前端直接 fetch） ----------------
        if path == "/api/asr/upload":
            try:
                name = (q.get("name", [""])[0] or "audio").strip()
                ext = os.path.splitext(name)[1].lower()
                if ext not in AUDIO_EXT:
                    return self._json({"ok": False, "error": "不支持的格式：%s（可 mp3/m4a/wav/ogg/flac）" % (ext or "未知")}, 400)
                ln = int(self.headers.get("Content-Length") or 0)
                if ln <= 0:
                    return self._json({"ok": False, "error": "空文件"}, 400)
                if ln > 300 * 1024 * 1024:
                    return self._json({"ok": False, "error": "文件超过 300MB，请先压缩或切段"}, 400)
                os.makedirs(AUDIO_DIR, exist_ok=True)
                tmp = os.path.join(AUDIO_DIR, "_up.tmp")
                h = hashlib.sha1()
                left = ln
                with open(tmp, "wb") as f:
                    while left > 0:
                        buf = self.rfile.read(min(262144, left))
                        if not buf:
                            break
                        h.update(buf)
                        f.write(buf)
                        left -= len(buf)
                aid = h.hexdigest()[:16]
                dst = os.path.join(AUDIO_DIR, aid + ext)
                os.replace(tmp, dst)
                # 同名不同后缀的旧文件清掉，避免 _audio_path 撞车
                for e in AUDIO_EXT:
                    p = os.path.join(AUDIO_DIR, aid + e)
                    if p != dst and os.path.isfile(p):
                        os.remove(p)
                meta = audio_meta(aid) or {"id": aid, "cues": []}
                dur = 0
                try:
                    import asr_core as A
                    dur = A.probe_duration(dst)
                except Exception:
                    pass
                meta.update({"id": aid, "name": name, "dur": dur or meta.get("dur") or 0,
                             "createdAt": meta.get("createdAt") or time.time(),
                             "bytes": os.path.getsize(dst)})
                save_meta(aid, meta)
                log("收到音频 %s（%.1f MB，%s 秒）→ %s" % (name, ln / 1048576.0, dur, aid))
                return self._json({"ok": True, "id": aid, "name": name, "dur": meta["dur"],
                                   "cues": len(meta.get("cues") or [])})
            except Exception as e:
                log("上传失败: %r" % e)
                return self._json({"ok": False, "error": "上传失败：%s" % e}, 500)

        # ---------------- 发起转写 ----------------
        if path == "/api/asr/jobs":
            try:
                ln = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(ln).decode("utf-8") or "{}")
            except Exception as e:
                return self._json({"ok": False, "error": "请求体不是合法 JSON：%s" % e}, 400)
            aid = (body.get("id") or "").strip()
            if not _safe_aid(aid) or not _audio_path(aid):
                return self._json({"ok": False, "error": "音频不存在，请重新导入"}, 404)
            try:
                import asr_core as A
                st = A.status(asr_conf())
            except Exception as e:
                return self._json({"ok": False, "error": "ASR 内核加载失败：%s" % e}, 500)
            if not st.get("installed"):
                return self._json({"ok": False, "error":
                                   "本机还没装语音识别引擎。双击 podcast-bridge/install-asr.bat 安装一次即可"}, 400)
            j = start_asr_job(aid)
            return self._json({"ok": True, "jobId": j["id"], "state": j["state"]})

        # ---------------- 保存（用户改过的）字幕 ----------------
        if path == "/api/asr/cues":
            try:
                ln = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(ln).decode("utf-8") or "{}")
            except Exception as e:
                return self._json({"ok": False, "error": "请求体不是合法 JSON：%s" % e}, 400)
            aid = (body.get("id") or "").strip()
            if not _safe_aid(aid) or not audio_meta(aid):
                return self._json({"ok": False, "error": "没有这个音频"}, 404)
            m = audio_meta(aid)
            cues = body.get("cues")
            if isinstance(cues, list):
                m["cues"] = cues
            if isinstance(body.get("zhLines"), str):
                m["zhLines"] = body["zhLines"]
            save_meta(aid, m)
            return self._json({"ok": True, "cues": len(m.get("cues") or [])})

        # ---------------- 删除 ----------------
        if path == "/api/asr/del":
            try:
                ln = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(ln).decode("utf-8") or "{}")
            except Exception:
                body = {}
            aid = (body.get("id") or q.get("id", [""])[0] or "").strip()
            if not _safe_aid(aid):
                return self._json({"ok": False, "error": "id 非法"}, 400)
            for e in list(AUDIO_EXT) + [".json"]:
                p = os.path.join(AUDIO_DIR, aid + e)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            return self._json({"ok": True})

        return self.do_GET()

    def log_message(self, fmt, *args):
        return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="serve", choices=["serve", "once", "status"])
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--open", default="", help="启动后自动打开的页面地址")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if a.cmd == "once":
        r = do_sync(force=a.force)
        print(json.dumps({k: v for k, v in r.items() if k != "payload"}, ensure_ascii=False, indent=1))
        return

    if a.cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return

    # serve
    do_sync()
    if a.open:
        import webbrowser
        threading.Timer(1.2, lambda: webbrowser.open(a.open)).start()

    def warm_asr():
        """预热：引擎首次 import 要 3-5 秒，先吃掉，页面点开就能用"""
        try:
            import asr_core as A
            conf = asr_conf()
            st = A.status(conf)
            if st.get("installed"):
                log("本地 ASR 就绪：%s · 模型%s · 源 %s"
                    % (st.get("model"), "已在本地" if st.get("modelCached") else "未下载（首次识别时自动下）",
                       st.get("endpoint")))
            else:
                log("本地 ASR 未启用：没装 faster-whisper（双击 podcast-bridge/install-asr.bat 可开）")
        except Exception as e:
            log("本地 ASR 预热失败（不影响同步）：%s" % e)

    threading.Thread(target=warm_asr, daemon=True).start()

    httpd = ThreadingHTTPServer((a.host, a.port), Handler)
    log("同步桥已启动: http://%s:%d" % (a.host, a.port))
    log("数据源: %s" % op.VAULT)
    log("按 Ctrl+C 停止")
    log("")
    _cnt = (STATE["payload"] or {}).get("counts") or {}
    log("下一步：回到工作台页面 → 按 Ctrl+F5 强刷 → 点「🔄 同步 Obsidian」")
    log("        正常会显示「已同步 %s 词 / %s 集」；若提示连不上，先点「🩺 测试连接」"
        % (_cnt.get("words", "?"), _cnt.get("episodes", "?")))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("已停止")


if __name__ == "__main__":
    main()
