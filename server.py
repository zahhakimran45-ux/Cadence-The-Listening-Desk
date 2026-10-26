#!/usr/bin/env python3
"""
CADENCE — local server.

Serves the self-contained index.html and adds three small API routes that
unlock the "live" half of the app:

  GET /api/search?q=...     -> iTunes Search API (with a Deezer fallback)
  GET /api/preview?q=...    -> best 30-second preview URL for a song
  GET /api/audio?url=...    -> same-origin proxy of that preview clip
  GET /api/health           -> diagnostics

Run:  python3 server.py           (then open http://localhost:8000)
"""
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
UA = "Mozilla/5.0 (compatible; CadenceListeningDesk/1.0)"

_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 600


def cached(key, producer):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = producer()
    with _cache_lock:
        _cache[key] = (now, value)
        if len(_cache) > 300:
            for k in list(_cache)[:100]:
                _cache.pop(k, None)
    return value


def get_json(url, timeout=9):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def clean(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def from_itunes(q, limit=10):
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": q, "entity": "song", "limit": limit, "country": "US"})
    data = get_json(url)
    out, seen = [], set()
    for r in data.get("results", []):
        if r.get("wrapperType") != "track" or not r.get("previewUrl"):
            continue
        title, artist = r.get("trackName", ""), r.get("artistName", "")
        k = clean(title) + "|" + clean(artist)
        if k in seen:
            continue
        seen.add(k)
        art = (r.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
        out.append({
            "id": "it" + str(r.get("trackId")),
            "title": title, "artist": artist,
            "year": int((r.get("releaseDate") or "2020")[:4]),
            "genre": r.get("primaryGenreName") or "Pop",
            "duration": round((r.get("trackTimeMillis") or 210000) / 1000),
            "artwork": art,
            "previewUrl": r.get("previewUrl"),
            "trackViewUrl": r.get("trackViewUrl"),
            "source": "itunes",
        })
    return out


def from_deezer(q, limit=10):
    url = "https://api.deezer.com/search?" + urllib.parse.urlencode({"q": q, "limit": limit})
    data = get_json(url)
    out = []
    for r in data.get("data", [])[:limit]:
        if not r.get("preview"):
            continue
        out.append({
            "id": "dz" + str(r.get("id")),
            "title": r.get("title", ""),
            "artist": (r.get("artist") or {}).get("name", ""),
            "year": int((r.get("release_date") or "2020")[:4]),
            "genre": "World",
            "duration": int(r.get("duration") or 210),
            "artwork": "https://e-cdns-images.dzcdn.net/images/cover/{}/500x500-000000-80-0-0.jpg".format(r.get("md5_image", "")),
            "previewUrl": r.get("preview"),
            "trackViewUrl": r.get("link"),
            "source": "deezer",
        })
    return out


def search(q):
    def produce():
        try:
            rows = from_itunes(q)
        except Exception as e:
            print("[warn] iTunes lookup failed:", e, file=sys.stderr)
            rows = []
        if not rows:
            try:
                rows = from_deezer(q)
            except Exception as e:
                print("[warn] Deezer lookup failed:", e, file=sys.stderr)
        return {"query": q, "results": rows[:8]}
    return cached("search:" + q.lower(), produce)


def deezer_preview(q):
    """Deezer serves MP3 clips — decodable in every browser's Web Audio API."""
    url = "https://api.deezer.com/search?" + urllib.parse.urlencode({"q": q, "limit": 8})
    data = get_json(url)
    words = set(clean(q).split())
    best, best_score = None, -1
    for r in data.get("data", []):
        if not r.get("preview"):
            continue
        t = clean(r.get("title", ""))
        a = clean((r.get("artist") or {}).get("name", ""))
        sc = len(words & set((t + " " + a).split())) * 3
        if t and t in clean(q):
            sc += 4
        sc -= min(6, abs(len(t.split()) - 3))
        if sc > best_score:
            best, best_score = r, sc
    return (best or {}).get("preview")


def best_preview(q):
    """Return an MP3 first (broad codec support), an AAC clip as fallback."""
    mp3 = None
    try:
        mp3 = cached("dzprev:" + q.lower(), lambda: deezer_preview(q))
    except Exception as e:
        print("[warn] Deezer preview failed:", e, file=sys.stderr)

    rows = search(q).get("results", [])
    target = clean(q)
    def score(r):
        t = clean(r["title"])
        if t == target:
            return 100
        if t and (t in target or target in t):
            return 70
        return 20
    rows = sorted(rows, key=score, reverse=True)
    aac = rows[0]["previewUrl"] if rows else None
    return {
        "previewUrl": mp3 or aac,
        "fallback": aac if mp3 and aac != mp3 else None,
        "format": "mp3" if mp3 else ("aac" if aac else None),
        "title": rows[0]["title"] if rows else q,
        "artist": rows[0]["artist"] if rows else "",
    }


ALLOWED_HOSTS = (
    "audio-ssl.itunes.apple.com", "audio.itunes.apple.com", "aod.itunes.apple.com",
    "is1-ssl.mzstatic.com", "cdnt-preview.dzcdn.net", "api.deezer.com",
)


def fetch_audio(url):
    p = urllib.parse.urlparse(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise PermissionError("Host not allowed: " + host)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "audio/*"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read(4 * 1024 * 1024)
        ctype = r.headers.get("Content-Type", "audio/mp4")
    if len(data) < 5000:
        raise ValueError("Preview too small")
    return data, ctype


class Handler(BaseHTTPRequestHandler):
    server_version = "Cadence/1.0"

    def log_message(self, fmt, *args):
        if os.environ.get("VERBOSE"):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        try:
            if p.path in ("/api/health",):
                return self._send(200, json.dumps({"ok": True, "catalog": True, "live": True}))
            if p.path == "/api/search":
                q = (qs.get("q") or [""])[0].strip()
                if not q:
                    return self._send(400, json.dumps({"error": "missing q"}))
                return self._send(200, json.dumps(search(q), ensure_ascii=False))
            if p.path == "/api/preview":
                q = (qs.get("q") or [""])[0].strip()
                if not q:
                    return self._send(400, json.dumps({"error": "missing q"}))
                return self._send(200, json.dumps(best_preview(q), ensure_ascii=False))
            if p.path == "/api/audio":
                url = (qs.get("url") or [""])[0]
                if not url:
                    return self._send(400, json.dumps({"error": "missing url"}))
                try:
                    data, ctype = cached("audio:" + url, lambda: fetch_audio(url))
                except PermissionError as e:
                    return self._send(403, json.dumps({"error": str(e)}))
                except Exception as e:
                    return self._send(502, json.dumps({"error": "upstream: " + str(e)}))
                return self._send(200, data, ctype, {"Accept-Ranges": "none"})
        except Exception as e:
            print("[error]", e, file=sys.stderr)
            return self._send(500, json.dumps({"error": str(e)}))

        # static
        rel = "index.html" if p.path in ("/", "/index.html") else p.path.lstrip("/")
        path = os.path.normpath(os.path.join(ROOT, rel))
        if not path.startswith(ROOT) or not os.path.isfile(path):
            return self._send(404, "Not found", "text/plain; charset=utf-8")
        ext = os.path.splitext(path)[1].lower()
        ctype = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
                 ".svg": "image/svg+xml", ".png": "image/png"}.get(ext, "application/octet-stream")
        with open(path, "rb") as fh:
            self._send(200, fh.read(), ctype)


if __name__ == "__main__":
    if not os.path.isfile(os.path.join(ROOT, "index.html")):
        print("index.html missing — run: python3 build.py", file=sys.stderr)
        sys.exit(1)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    print("CADENCE — The Listening Desk")
    print("  http://localhost:%d   (catalog: 220 songs, live search: on)" % PORT)
    print("  Ctrl+C to stop.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBye.")
        srv.server_close()
