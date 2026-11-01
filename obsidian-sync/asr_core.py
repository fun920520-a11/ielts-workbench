# -*- coding: utf-8 -*-
"""
雅思备考工作台 · 本地 ASR 内核

职责单一：把一段本机音频转成「带时间戳的英文句子」。
被 obsidian_sync.py 调用，不单独运行。

设计要点：
1. 模型目录优先复用 podcast-bridge/models（那边已经下过就不重复下 145MB）；
2. huggingface.co 在国内常直连不通 —— 启动时探测，不通自动切 hf-mirror.com；
3. 自己实现下载（进度 / 断点续传 / 重试），不依赖 huggingface_hub 的缓存机制
   （它在 Windows 上会出现只写 blob、不建 snapshot 的问题）；
4. 用 **词级时间戳** 切句：句子的 st/et 落在真实词边界上，点句跳转更准。
"""
import io
import os
import re
import sys
import time
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)

MODEL_FILES = ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]
MODEL_MB = {"base.en": 145, "small.en": 480, "tiny.en": 75, "medium.en": 1500}

# 候选模型目录：播客桥的下好的模型可以直接借用
CAND_DIRS = [
    os.path.join(HERE, "models"),
    os.path.join(PARENT, "podcast-bridge", "models"),
]

_HF_EP = None
_ENGINE = {"model": None, "key": ""}


def log(msg):
    print("[asr] %s" % msg, flush=True)


# ---------------------------------------------------------------- 模型源
def _reachable(url, timeout=4):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "ielts-bridge"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 500
    except Exception:
        return False


def apply_hf_env(aconf=None):
    """HF_ENDPOINT 必须在 import faster_whisper 之前写好（huggingface_hub 导入即固化）

    探测结果会缓存到 .hf_endpoint，避免每次请求都卡 4 秒去试 huggingface.co。
    """
    global _HF_EP
    if _HF_EP:
        return _HF_EP
    aconf = aconf or {}
    ep = (aconf.get("hf_endpoint") or os.environ.get("HF_ENDPOINT") or "").strip()
    if not ep:
        cache = os.path.join(HERE, ".hf_endpoint")
        if os.path.isfile(cache):
            try:
                with open(cache, "r", encoding="utf-8") as f:
                    ep = f.read().strip()
            except Exception:
                ep = ""
    if not ep:
        ep = "https://huggingface.co" if _reachable("https://huggingface.co", 2) \
            else "https://hf-mirror.com"
        try:
            with open(os.path.join(HERE, ".hf_endpoint"), "w", encoding="utf-8") as f:
                f.write(ep)
        except Exception:
            pass
    ep = ep.rstrip("/")
    os.environ["HF_ENDPOINT"] = ep
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    _HF_EP = ep
    return ep


# ---------------------------------------------------------------- 模型文件
def _complete(d):
    for f in MODEL_FILES:
        p = os.path.join(d, f)
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            return False
    return True


def find_model(name):
    """返回已存在的完整模型目录，找不到返回 ''"""
    for base in CAND_DIRS:
        d = os.path.join(base, name)
        if _complete(d):
            return d
    return ""


def model_cached(name):
    return bool(find_model(name))


def _download(url, dst, job=None, label="", tries=3):
    tmp = dst + ".part"
    last = None
    for k in range(tries):
        try:
            pos = os.path.getsize(tmp) if os.path.isfile(tmp) else 0
            hdr = {"User-Agent": "ielts-bridge"}
            if pos:
                hdr["Range"] = "bytes=%d-" % pos
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=45) as r:
                total = int(r.headers.get("Content-Length") or 0)
                mode = "ab" if (pos and r.status == 206) else "wb"
                if mode == "wb":
                    pos, total = 0, int(r.headers.get("Content-Length") or 0)
                base, done = pos, pos
                t0 = time.time()
                with open(tmp, mode) as f:
                    while True:
                        buf = r.read(262144)
                        if not buf:
                            break
                        f.write(buf)
                        done += len(buf)
                        if job:
                            mb = done / 1048576.0
                            sp = (done - base) / 1048576.0 / max(0.001, time.time() - t0)
                            if total:
                                job["msg"] = ("首次使用，下载模型 %s · %.0f%%（%.0f / %.0f MB · %.1f MB/s）"
                                              % (label, done * 100.0 / total, mb,
                                                 (base + total) / 1048576.0, sp))
                            else:
                                job["msg"] = "首次使用，下载模型 %s · %.1f MB（%.1f MB/s）" % (label, mb, sp)
            if os.path.getsize(tmp) == 0:
                raise RuntimeError("下载得到 0 字节")
            os.replace(tmp, dst)
            return dst
        except Exception as e:
            last = e
            if k < tries - 1:
                log("下载 %s 第 %d 次失败（%s），2 秒后重试" % (label, k + 1, e))
                time.sleep(2)
    raise RuntimeError("下载模型文件 %s 失败：%s" % (label, last))


def ensure_model(name, aconf=None, job=None):
    d = find_model(name)
    if d:
        return d
    ep = apply_hf_env(aconf)
    target = os.path.join(HERE, "models", name)
    os.makedirs(target, exist_ok=True)
    repo = "Systran/faster-whisper-%s" % name
    if job:
        job["msg"] = "首次使用，准备从 %s 下载模型 %s（约 %d MB）…" % (
            ep.replace("https://", ""), name, MODEL_MB.get(name, 145))
    for f in MODEL_FILES:
        p = os.path.join(target, f)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            continue
        _download("%s/%s/resolve/main/%s" % (ep, repo, f), p, job, f)
    log("模型就绪：%s" % target)
    return target


# ---------------------------------------------------------------- 依赖补丁
def patch_av_open():
    """PyAV 19 去掉了 av.open(metadata_errors=...)，而 faster-whisper 还在传"""
    try:
        import av
    except Exception:
        return False
    if getattr(av, "_ielts_patched", False):
        return True
    try:
        av.open(os.path.join(HERE, "__probe__"), metadata_errors="ignore")
        return True
    except TypeError:
        pass
    except Exception:
        return True
    orig = av.open

    def _open(*a, **kw):
        kw.pop("metadata_errors", None)
        return orig(*a, **kw)

    av.open = _open
    av._ielts_patched = True
    log("PyAV 版本较新，已补 metadata_errors 兼容层")
    return True


def status(aconf=None):
    aconf = aconf or {}
    name = aconf.get("model") or "base.en"
    apply_hf_env(aconf)
    try:
        import faster_whisper  # noqa: F401
    except Exception:
        return {"ok": False, "installed": False, "model": name}
    return {"ok": True, "installed": True, "backend": "faster-whisper",
            "model": name, "modelCached": model_cached(name),
            "endpoint": _HF_EP, "device": aconf.get("device") or "cpu"}


# ---------------------------------------------------------------- 时长
def probe_duration(path):
    try:
        import av
        patch_av_open()
        with av.open(path) as c:
            if c.duration:
                return round(float(c.duration) / 1e6, 2)
            st = c.streams.audio[0] if c.streams.audio else None
            if st and st.duration and st.time_base:
                return round(float(st.duration * st.time_base), 2)
    except Exception:
        pass
    return 0.0


# ---------------------------------------------------------------- 切句
SENT_END = re.compile(r"[.!?。！？]['\")\]]*$")
MAX_SEC = 12.0        # 单句最长 12 秒，超过强制断开（长句跟读很难用）
MAX_WORDS = 22        # 或超过 22 词


def _clean(t):
    return re.sub(r"\s+", " ", (t or "").replace("\n", " ")).strip()


def words_to_cues(words):
    """词级时间戳 → 句子级 cue，句首句尾落在真实词边界"""
    cues, cur = [], []
    for w in words:
        tok = (getattr(w, "word", "") or "")
        if not tok.strip():
            continue
        cur.append(w)
        txt = "".join((getattr(x, "word", "") or "") for x in cur).strip()
        dur = cur[-1].end - cur[0].start
        if SENT_END.search(tok.strip()) or dur >= MAX_SEC or len(cur) >= MAX_WORDS:
            cues.append({"st": round(cur[0].start, 3), "et": round(cur[-1].end, 3), "en": _clean(txt)})
            cur = []
    if cur:
        cues.append({"st": round(cur[0].start, 3), "et": round(cur[-1].end, 3),
                     "en": _clean("".join((getattr(x, "word", "") or "") for x in cur))})
    return cues


JUNK_RE = re.compile(r"^[\W\d_]+$")          # 只有数字/符号
ABBR_TAIL = re.compile(r"(mr|mrs|ms|dr|prof|st|vs|etc|eg|ie)\.$", re.I)


def keep_segment(s):
    """丢掉 whisper 在静音/噪声尾巴上编出来的低置信段。

    判据（同时满足才丢，避免误伤小声说话的真句子）：
      avg_logprob 很低  且  (该段多半不是人声  或  内容短得可疑)
    """
    text = _clean(getattr(s, "text", "") or "")
    if not text:
        return False
    logp = float(getattr(s, "avg_logprob", 0) or 0)
    nsp = float(getattr(s, "no_speech_prob", 0) or 0)
    if logp < -1.0 and (nsp > 0.3 or len(text) <= 4):
        return False
    return True


def seg_to_cues(seg):
    """无词级时间戳时的兜底：按标点比例分配"""
    text = _clean(getattr(seg, "text", "") or "")
    st, et = float(seg.start), float(seg.end)
    if not text:
        return []
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if len(parts) <= 1:
        return [{"st": round(st, 3), "et": round(et, 3), "en": text}]
    weights = [max(1, len(p.split())) for p in parts]
    total = float(sum(weights))
    cur, out = st, []
    for p, w in zip(parts, weights):
        d = (et - st) * w / total
        out.append({"st": round(cur, 3), "et": round(cur + d, 3), "en": p.strip()})
        cur += d
    return out


def tidy_cues(cues, dur=0.0):
    """去重 / 修零长 / 保单调 / 越界裁剪 / 清掉尾部碎片"""
    out = []
    for c in cues:
        c["en"] = _clean(c.get("en") or "")
        if not c["en"] or JUNK_RE.match(c["en"]):
            continue                       # 纯数字/符号的幻觉段
        if ABBR_TAIL.search(c["en"]) and len(c["en"].split()) <= 1:
            continue                       # 光秃秃一个 "Mr."
        if c["et"] <= c["st"]:
            c["et"] = round(c["st"] + 1.0, 3)
        out.append(c)
    out.sort(key=lambda c: c["st"])
    for i, c in enumerate(out):
        nxt = out[i + 1] if i + 1 < len(out) else None
        if nxt and c["et"] - nxt["st"] > 0.05:
            c["et"] = round(max(c["st"] + 0.3, nxt["st"] - 0.02), 3)
        if dur and c["et"] > dur:
            c["et"] = round(dur, 3)
        if dur and c["st"] > dur - 0.1:
            c["et"] = c["st"]
            continue
    # 丢掉被裁没的尾巴
    out = [c for c in out if c["et"] - c["st"] > 0.05]
    # 尾部碎片：最后一个词、时长 < 0.45s，多半是 whisper 编的
    while len(out) >= 2:
        last = out[-1]
        if len(last["en"].split()) <= 1 and last["et"] - last["st"] < 0.45:
            out.pop()
        else:
            break
    for i, c in enumerate(out):
        c["i"] = i
        c["zh"] = c.get("zh") or ""
    return out


# ---------------------------------------------------------------- 主流程
def load_model(name, aconf=None, job=None):
    """模型带缓存：同一进程内只加载一次"""
    d = ensure_model(name, aconf, job)
    key = "%s|%s|%s" % (d, aconf.get("device") or "cpu", aconf.get("compute_type") or "int8")
    if _ENGINE["model"] is not None and _ENGINE["key"] == key:
        return _ENGINE["model"]
    apply_hf_env(aconf)                 # 必须在 import 之前
    from faster_whisper import WhisperModel
    patch_av_open()
    if job:
        job["msg"] = "加载本地模型 %s…" % name
    m = WhisperModel(d, device=aconf.get("device") or "cpu",
                     compute_type=aconf.get("compute_type") or "int8")
    _ENGINE["model"], _ENGINE["key"] = m, key
    return m


def transcribe(path, aconf=None, job=None):
    """转写 → 返回 (cues, info)；cues = [{st, et, en}]，时间为秒"""
    aconf = aconf or {}
    name = aconf.get("model") or "base.en"
    model = load_model(name, aconf, job)
    if job:
        job["msg"] = "开始转写（词级时间戳）…"
    seg_iter, info = model.transcribe(
        path,
        language=aconf.get("language") or "en",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
        beam_size=int(aconf.get("beam_size") or 5),
        condition_on_previous_text=False,   # 防止长音频陷入重复幻觉
        word_timestamps=True,
        no_speech_threshold=0.6,
        log_prob_threshold=-1.0,
        compression_ratio_threshold=2.4,
    )
    total = float(getattr(info, "duration", 0) or 0)
    raw = []
    dropped = 0
    for s in seg_iter:
        if not keep_segment(s):
            dropped += 1
            continue
        ws = getattr(s, "words", None) or []
        raw.extend(words_to_cues(ws) if ws else seg_to_cues(s))
        if job and total:
            p = min(0.97, max(0.0, float(s.end) / total))
            job["progress"] = round(p, 3)
            job["msg"] = "转写中 %d%%（已到 %s）" % (int(p * 100), _fmt(s.end))
    cues = tidy_cues(raw, total or probe_duration(path))
    return cues, {"duration": total, "language": getattr(info, "language", "en"),
                  "droppedSegments": dropped}


def _fmt(t):
    t = float(t or 0)
    return "%02d:%05.2f" % (int(t // 60), t % 60)


if __name__ == "__main__":
    # 自查：python asr_core.py <音频> [模型]
    p = sys.argv[1] if len(sys.argv) > 1 else ""
    if not p:
        print("用法: python asr_core.py <音频文件> [模型名]")
        raise SystemExit(1)
    job = {}
    cues, info = transcribe(p, {"model": sys.argv[2] if len(sys.argv) > 2 else "base.en"}, job)
    print(json.dumps({"info": info, "cues": cues}, ensure_ascii=False, indent=1)[:4000])