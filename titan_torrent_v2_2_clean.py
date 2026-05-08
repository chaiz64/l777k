# @title 🧲 TITAN TORRENT v2 — BitTorrent Client for Google Colab
# ==============================================================================
# Run this cell ONCE. Re-run is safe (singleton guard prevents double-init).
# Features: Magnet Links · .torrent Files · Real-time Stats · Google Drive Export
# ==============================================================================

# ── 1. INSTALL ────────────────────────────────────────────────────────────────
import subprocess, sys

def _pip(*pkgs):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *pkgs], check=False)

try:
    import libtorrent as lt
except ImportError:
    _pip("libtorrent")
    try:
        import libtorrent as lt
    except ImportError:
        _pip("python-libtorrent")
        import libtorrent as lt

try:
    import ipywidgets as widgets
except ImportError:
    _pip("ipywidgets")
    import ipywidgets as widgets

# ── 2. STDLIB ─────────────────────────────────────────────────────────────────
import os, time, shutil, threading, queue
from datetime import datetime
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum, auto
from IPython.display import display, HTML, clear_output, Javascript

# ── 3. SINGLETON GUARD ────────────────────────────────────────────────────────
# Prevents duplicate engines / threads when the cell is re-run accidentally.
from IPython.display import clear_output
_TITAN_INSTANCE_KEY = "__titan_torrent_v2__"
if _TITAN_INSTANCE_KEY in globals() and globals()[_TITAN_INSTANCE_KEY] is not None:
    _old = globals()[_TITAN_INSTANCE_KEY]
    try:
        _old.shutdown()
    except Exception:
        pass
    globals()[_TITAN_INSTANCE_KEY] = None
    clear_output(wait=True)
    print("♻️  Previous Titan Torrent instance shut down cleanly.")

# ── 4. CONSTANTS ──────────────────────────────────────────────────────────────
DOWNLOAD_DIR     = "/content/torrent_downloads"
RESUME_DIR       = "/content/torrent_resume"
MONITOR_INTERVAL = 1.0   # seconds between stat polls
LOG_MAXLINES     = 200   # rotate log after N lines

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(RESUME_DIR,   exist_ok=True)

# ── 5. DATA CLASSES ───────────────────────────────────────────────────────────
class TorrentStatus(Enum):
    QUEUED     = auto()
    CHECKING   = auto()
    METADATA   = auto()
    DOWNLOADING= auto()
    FINISHED   = auto()
    SEEDING    = auto()
    PAUSED     = auto()
    ERROR      = auto()

@dataclass
class TorrentStats:
    name:          str           = ""
    progress:      float         = 0.0
    download_rate: float         = 0.0
    upload_rate:   float         = 0.0
    num_peers:     int           = 0
    num_seeds:     int           = 0
    total_size:    int           = 0
    downloaded:    int           = 0
    uploaded:      int           = 0
    eta_seconds:   float         = 0.0
    status:        TorrentStatus = TorrentStatus.QUEUED
    error_msg:     str           = ""

    @property
    def pct(self) -> float:
        return self.progress * 100

    @property
    def eta_fmt(self) -> str:
        s = self.eta_seconds
        if s <= 0 or s > 86400 * 7:
            return "--:--"
        m, s = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def _fmt_bytes(n: int) -> str:
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def _fmt_speed(n: float) -> str:
    if n < 1024:         return f"{n:.0f} B/s"
    if n < 1024**2:      return f"{n/1024:.1f} KB/s"
    return f"{n/1024**2:.2f} MB/s"

def _fmt_dur(secs: float) -> str:
    h, r = divmod(int(secs), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── 6. ENGINE ─────────────────────────────────────────────────────────────────
class TitanEngine:
    """
    Thin wrapper around libtorrent.session.
    All monitoring is done externally (TitanDashboard._loop).
    This class is intentionally stateless w.r.t. UI.
    """

    def __init__(self, download_dir: str = DOWNLOAD_DIR):
        self.download_dir = download_dir
        self.handles: Dict[str, lt.torrent_handle] = {}
        self.session  = self._make_session()

    # ── session ───────────────────────────────────────────────────────────────
    @staticmethod
    def _make_session() -> lt.session:
        cfg = {
            "user_agent":             "TitanTorrent/2.0 libtorrent/2.0",
            "listen_interfaces":      "0.0.0.0:6881,[::]:6881",
            "download_rate_limit":    0,
            "upload_rate_limit":      100 * 1024,
            "active_downloads":       3,
            "active_seeds":           2,
            "active_limit":           5,
            "cache_size":             2048,
            "enable_dht":             True,
            "enable_lsd":             True,
            "enable_upnp":            True,
            "enable_natpmp":          True,
            "prefer_rc4":             True,
            "announce_to_all_trackers": True,
            "announce_to_all_tiers":    True,
            "dht_bootstrap_nodes":
                "router.bittorrent.com:6881,"
                "router.utorrent.com:6881,"
                "dht.transmissionbt.com:6881",
        }
        return lt.session(cfg)

    # ── add ───────────────────────────────────────────────────────────────────
    def add_magnet(self, uri: str) -> Optional[str]:
        try:
            p = lt.parse_magnet_uri(uri)
            p.save_path = self.download_dir
            h = self.session.add_torrent(p)
            ih = str(h.info_hash())
            self.handles[ih] = h
            return ih
        except Exception as e:
            return None

    def add_file(self, path: str) -> Optional[str]:
        try:
            info = lt.torrent_info(path)
            p = lt.add_torrent_params()
            p.ti = info
            p.save_path = self.download_dir
            h = self.session.add_torrent(p)
            ih = str(h.info_hash())
            self.handles[ih] = h
            return ih, info.name()
        except Exception as e:
            return None

    def add_url(self, url: str) -> Optional[str]:
        import urllib.request
        tmp = os.path.join(RESUME_DIR, "fetched.torrent")
        urllib.request.urlretrieve(url, tmp)
        return self.add_file(tmp)

    # ── control ───────────────────────────────────────────────────────────────
    def pause(self, ih: str):
        if ih in self.handles: self.handles[ih].pause()

    def resume(self, ih: str):
        if ih in self.handles: self.handles[ih].resume()

    def remove(self, ih: str, del_files=False):
        if ih in self.handles:
            self.session.remove_torrent(self.handles[ih], del_files)
            del self.handles[ih]

    def pause_all(self):
        for h in self.handles.values(): h.pause()

    def resume_all(self):
        for h in self.handles.values(): h.resume()

    # ── stats ─────────────────────────────────────────────────────────────────
    def get_stats(self, ih: str) -> Optional[TorrentStats]:
        if ih not in self.handles: return None
        h  = self.handles[ih]
        st = h.status()
        s  = TorrentStats()

        if st.has_metadata:
            s.name = h.torrent_file().name()
        else:
            s.name = f"⏳ Fetching metadata… ({st.num_peers} peers)"

        s.progress      = st.progress
        s.download_rate = st.download_rate
        s.upload_rate   = st.upload_rate
        s.num_peers     = st.num_peers
        s.num_seeds     = st.num_seeds
        s.total_size    = st.total_wanted
        s.downloaded    = st.total_wanted_done
        s.uploaded      = st.total_upload

        if s.download_rate > 0:
            remaining = s.total_size - s.downloaded
            s.eta_seconds = remaining / s.download_rate

        _map = {
            lt.torrent_status.queued_for_checking:  TorrentStatus.QUEUED,
            lt.torrent_status.checking_files:       TorrentStatus.CHECKING,
            lt.torrent_status.downloading_metadata: TorrentStatus.METADATA,
            lt.torrent_status.downloading:          TorrentStatus.DOWNLOADING,
            lt.torrent_status.finished:             TorrentStatus.FINISHED,
            lt.torrent_status.seeding:              TorrentStatus.SEEDING,
        }
        s.status = _map.get(st.state, TorrentStatus.DOWNLOADING)
        if st.paused:           s.status = TorrentStatus.PAUSED
        if st.errc.value() != 0:
            s.status = TorrentStatus.ERROR
            s.error_msg = st.errc.message()
        return s

    def get_all_stats(self) -> List[TorrentStats]:
        return [x for ih in list(self.handles) if (x := self.get_stats(ih))]

    def pop_alerts(self):
        return self.session.pop_alerts()

    def shutdown(self):
        self.session.pause()

# ── 7. DASHBOARD ──────────────────────────────────────────────────────────────
class TitanDashboard:
    """
    Single-thread monitoring loop.  Widget mutations happen on the background
    thread — this is fine in Colab/Jupyter because ipywidgets uses comm objects
    that are inherently async-safe for value updates (not create/display).
    Log lines are queued and flushed inside the loop to avoid Output widget
    reentrancy issues.
    """

    # ── init ──────────────────────────────────────────────────────────────────
    def __init__(self):
        self.engine       = TitanEngine()
        self._log_q:  queue.Queue = queue.Queue()
        self._running     = False
        self._thread: Optional[threading.Thread] = None
        self._session_start = datetime.now()
        self._iter        = 0
        self._build_ui()
        self._wire()

    # ── UI build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── styles ────────────────────────────────────────────────────────────
        self._css = widgets.HTML("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;600;800&display=swap');

.tt-root * { box-sizing: border-box; }

.tt-hdr {
  font-family:'Barlow Condensed',sans-serif;
  font-weight:800; font-size:32px; letter-spacing:3px;
  background:linear-gradient(90deg,#ff6b35 0%,#ffd166 60%,#ff6b35 100%);
  background-size:200% auto;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  text-align:center;
  animation: shimmer 3s linear infinite;
}
@keyframes shimmer { to { background-position: 200% center; } }

.tt-sub {
  font-family:'Share Tech Mono',monospace;
  color:#4a4a6a; text-align:center; font-size:11px;
  letter-spacing:2px; margin-bottom:18px;
  text-transform:uppercase;
}

.tt-card {
  background:rgba(255,107,53,0.07);
  border:1px solid rgba(255,107,53,0.25);
  border-radius:10px; padding:12px 14px; margin:6px 0;
  transition:border-color 0.3s;
}
.tt-card.active { border-color:rgba(0,255,136,0.5); }

.tt-name {
  font-family:'Barlow Condensed',sans-serif;
  font-size:15px; font-weight:600;
  color:#ff9055; margin-bottom:7px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}

.tt-bar-wrap {
  background:#1e1e2e; height:8px; border-radius:4px;
  overflow:hidden; margin:4px 0 8px;
}
.tt-bar-fill {
  height:100%; border-radius:4px;
  background:linear-gradient(90deg,#ff6b35,#ffd166);
  transition:width 0.4s ease;
}
.tt-bar-fill.glow { box-shadow:0 0 8px #ff6b35aa; }

.tt-meta {
  font-family:'Share Tech Mono',monospace;
  font-size:11px; color:#666; display:flex; flex-wrap:wrap; gap:12px;
}
.tt-meta .hi  { color:#ff9055; font-weight:bold; }
.tt-meta .spd { color:#00ff88; }
.tt-meta .dim { color:#555; }

.tt-stat-box {
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:8px; padding:10px 14px; text-align:center; min-width:90px;
}
.tt-stat-val {
  font-family:'Barlow Condensed',sans-serif;
  font-weight:700; font-size:20px; color:#ff6b35;
}
.tt-stat-lbl {
  font-family:'Share Tech Mono',monospace;
  font-size:9px; color:#555; text-transform:uppercase; letter-spacing:1px;
}

.tt-tip {
  background:rgba(255,107,53,0.08);
  border-left:3px solid #ff6b35;
  border-radius:0 8px 8px 0;
  padding:10px 14px; margin:10px 0;
  font-family:'Share Tech Mono',monospace;
  font-size:11px; color:#aaa; line-height:1.8;
}
</style>
""")

        # ── header ────────────────────────────────────────────────────────────
        self._hdr = widgets.HTML("""
<div class="tt-hdr">🧲 TITAN TORRENT</div>
<div class="tt-sub">BitTorrent Client · Google Colab · v2.1 GodTier</div>
""")

        # ── input ─────────────────────────────────────────────────────────────
        self._input = widgets.Textarea(
            placeholder=(
                "📋 วาง magnet links หรือ URL ของ .torrent (หนึ่งต่อบรรทัด)\n\n"
                "magnet:?xt=urn:btih:...\nhttps://example.com/file.torrent"
            ),
            layout=widgets.Layout(width="100%", height="90px"),
        )

        self._upload_lbl = widgets.HTML(
            '<div style="font-family:\'Share Tech Mono\',monospace;'
            'color:#555;font-size:11px;margin:6px 0 2px;">— หรือ อัปโหลด .torrent จากเครื่อง —</div>'
        )
        self._upload = widgets.FileUpload(
            accept=".torrent", multiple=True,
            description="📁 Upload .torrent",
            layout=widgets.Layout(width="100%"),
        )

        # ── live stats row ────────────────────────────────────────────────────
        def _stat_box(val, lbl):
            w = widgets.HTML(
                f'<div class="tt-stat-box">'
                f'<div class="tt-stat-val">{val}</div>'
                f'<div class="tt-stat-lbl">{lbl}</div>'
                f'</div>'
            )
            return w

        self._s_dl   = _stat_box("0 B/s",   "Download")
        self._s_ul   = _stat_box("0 B/s",   "Upload")
        self._s_peer = _stat_box("0",        "Peers")
        self._s_live = _stat_box("⏸",        "Status")
        self._stats_row = widgets.HBox(
            [self._s_dl, self._s_ul, self._s_peer, self._s_live],
            layout=widgets.Layout(justify_content="space-around", margin="12px 0"),
        )

        # ── buttons ───────────────────────────────────────────────────────────
        _btn = lambda desc, style, w="90px": widgets.Button(
            description=desc, button_style=style,
            layout=widgets.Layout(width=w, height="38px"),
        )
        self._btn_add       = _btn("➕ ADD",        "success", "90px")
        self._btn_upload    = _btn("📁 UPLOAD",     "info",    "100px")
        self._btn_refresh   = _btn("🔄 REFRESH",    "",        "100px")
        self._btn_pause     = _btn("⏸️ PAUSE ALL",  "warning", "110px")
        self._btn_resume    = _btn("▶️ RESUME",     "info",    "100px")
        self._btn_clear_dl  = _btn("🗑️ CLEAR",      "danger",  "85px")
        self._btn_drive     = _btn("💾 → Drive",    "",        "105px")

        self._controls = widgets.HBox(
            [self._btn_add, self._btn_upload, self._btn_refresh, self._btn_pause,
             self._btn_resume, self._btn_clear_dl, self._btn_drive],
            layout=widgets.Layout(justify_content="center", gap="6px", margin="12px 0", flex_wrap="wrap"),
        )

        # ── session / keep-alive bar ──────────────────────────────────────────
        self._keep_alive = widgets.ToggleButton(
            value=True, description="🔥 Keep Alive", button_style="success",
            tooltip="ป้องกัน Colab หลุด",
            layout=widgets.Layout(width="125px"),
        )
        self._auto_refresh = widgets.ToggleButton(
            value=True, description="⚡ Auto Stats", button_style="info",
            tooltip="อัปเดตสถานะอัตโนมัติทุก 1 วินาที",
            layout=widgets.Layout(width="125px"),
        )
        self._session_lbl = widgets.HTML(
            '<span style="font-family:\'Share Tech Mono\',monospace;'
            'color:#555;font-size:11px;">Session: 00:00:00</span>'
        )
        self._heartbeat = widgets.HTML(
            '<span style="font-family:\'Share Tech Mono\',monospace;'
            'color:#333;font-size:11px;">●</span>'
        )
        self._alive_bar = widgets.HBox(
            [self._keep_alive, self._auto_refresh,
             self._session_lbl, self._heartbeat],
            layout=widgets.Layout(
                padding="8px 12px", gap="10px",
                border="1px solid rgba(0,255,136,0.15)",
                border_radius="8px", margin="10px 0",
                align_items="center",
            ),
        )

        # ── torrent list ──────────────────────────────────────────────────────
        self._dl_lbl = widgets.HTML(
            '<div style="font-family:\'Barlow Condensed\',sans-serif;'
            'font-size:15px;font-weight:600;color:#ff6b35;margin:8px 0 2px;">'
            '📥 Active Torrents</div>'
        )
        self._torrent_list = widgets.HTML(
            value='<div style="color:#555;text-align:center;padding:20px;font-family:Share Tech Mono;">No active torrents</div>',
            layout=widgets.Layout(width="100%", max_height="280px", overflow_y="auto"),
        )

        # ── log ───────────────────────────────────────────────────────────────
        self._log_lbl = widgets.HTML(
            '<div style="font-family:\'Barlow Condensed\',sans-serif;'
            'font-size:15px;font-weight:600;color:#ff6b35;margin:8px 0 2px;">'
            '📋 Event Log</div>'
        )
        self._log_out = widgets.Output(
            layout=widgets.Layout(
                height="140px", overflow_y="auto",
                border="1px solid rgba(255,107,53,0.15)",
                border_radius="8px", padding="8px",
            )
        )
        self._btn_clr_log = widgets.Button(
            description="🗑️ Clear Log",
            layout=widgets.Layout(width="100px", height="30px"),
        )
        self._log_footer = widgets.HBox(
            [self._btn_clr_log],
            layout=widgets.Layout(justify_content="flex-end"),
        )

        # ── tip box ───────────────────────────────────────────────────────────
        self._tips = widgets.HTML("""
<div class="tt-tip">
  <b style="color:#ff9055;">💡 วิธีใช้งาน</b><br>
  🧲 วาง <b>magnet link</b> หรือ <b>URL .torrent</b> แล้วกด <b>ADD</b><br>
  📁 หรือ อัปโหลดไฟล์ .torrent แล้วกด <b>UPLOAD</b><br>
  🔥 เปิด <b>Keep Alive</b> ค้างไว้เพื่อป้องกัน session หลุด<br>
  💾 กด <b>→ Drive</b> เพื่อ export ไฟล์ที่ดาวน์โหลดเสร็จไป Google Drive
</div>
""")

        # ── root container ────────────────────────────────────────────────────
        self.root = widgets.VBox(
            [
                self._css, self._hdr,
                self._input,
                self._upload_lbl, self._upload,
                self._stats_row,
                self._controls,
                self._alive_bar,
                self._dl_lbl,    self._torrent_list,
                self._log_lbl,   self._log_out, self._log_footer,
                self._tips,
            ],
            layout=widgets.Layout(
                padding="20px",
                border="2px solid rgba(255,107,53,0.25)",
                border_radius="16px",
                width="820px",
            ),
        )

        # ── register JS auto-refresh (ทำงานใน main thread 100%) ───────────────
        try:
            from google.colab import output
            output.register_callback('titan.refresh', self._js_refresh)
            self._js_enabled = True
        except Exception:
            self._js_enabled = False

    # ── wire callbacks ────────────────────────────────────────────────────────
    def _wire(self):
        self._btn_add.on_click(self._on_add)
        self._btn_upload.on_click(self._on_upload)
        self._btn_refresh.on_click(self._on_refresh)
        self._btn_pause.on_click(lambda _: self.engine.pause_all()  or self._q("⏸️ All paused"))
        self._btn_resume.on_click(lambda _: self.engine.resume_all() or self._q("▶️ All resumed"))
        self._btn_clear_dl.on_click(self._on_clear)
        self._btn_drive.on_click(self._on_drive)
        self._btn_clr_log.on_click(lambda _: self._log_out.clear_output())

    # ── log helpers ───────────────────────────────────────────────────────────
    def _on_refresh(self, _):
        """Manual refresh - ทำงานใน main thread ปลอดภัย 100%"""
        try:
            stats = self.engine.get_all_stats()
            self._update_ui(stats)
            self._q(f"🔄 Refreshed {len(stats)} torrent(s)")
        except Exception as e:
            self._q(f"❌ Refresh error: {e}")

    def _js_refresh(self):
        """ถูกเรียกจาก JavaScript ทุก 1 วินาที"""
        try:
            if self._auto_refresh.value:
                stats = self.engine.get_all_stats()
                self._update_ui(stats)
        except Exception:
            pass

    def _q(self, msg: str):
        """Queue a log line to be printed in the background loop."""
        self._log_q.put(msg)

    def _flush_log(self):
        """Drain the log queue — call only from the monitor thread."""
        lines = []
        while not self._log_q.empty():
            try:
                lines.append(self._log_q.get_nowait())
            except queue.Empty:
                break
        if lines:
            ts = datetime.now().strftime("%H:%M:%S")
            text = "\n".join(f"[{ts}] {l}" for l in lines) + "\n"
            # append_stdout ปลอดภัยจาก background thread (ipywidgets 8+)
            try:
                self._log_out.append_stdout(text)
            except Exception:
                # fallback สำหรับเวอร์ชันเก่า
                with self._log_out:
                    print(text, end="")

    # ── button handlers ───────────────────────────────────────────────────────
    def _on_add(self, _):
        raw = self._input.value.strip()
        if not raw:
            self._q("⚠️ ยังไม่ได้ใส่ magnet link หรือ URL")
            return
        added = 0
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            if line.startswith("magnet:"):
                ih = self.engine.add_magnet(line)
                if ih:
                    self._q(f"🧲 Magnet added → {ih[:16]}…")
                    added += 1
                else:
                    self._q(f"❌ ไม่สามารถเพิ่ม magnet: {line[:40]}…")
            elif line.startswith("http"):
                try:
                    res = self.engine.add_url(line)
                    if res:
                        ih, name = res
                        self._q(f"📡 Torrent URL added → {name}")
                        added += 1
                    else:
                        self._q(f"❌ ดาวน์โหลด torrent ไม่ได้: {line[:40]}…")
                except Exception as e:
                    self._q(f"❌ Error: {e}")
            else:
                self._q(f"⚠️ รูปแบบไม่รู้จัก: {line[:50]}…")
        if added:
            self._input.value = ""

    def _on_upload(self, _):
        uv = self._upload.value
        if not uv:
            self._q("⚠️ กรุณาเลือกไฟล์ .torrent ก่อน")
            return

        # Support both ipywidgets 7.x (tuple) and 8.x (dict) API
        if isinstance(uv, dict):
            items = [(fname, fdata["content"]) for fname, fdata in uv.items()]
        else:
            items = [
                (f["name"] if isinstance(f, dict) else f.name,
                 f["content"] if isinstance(f, dict) else f.content)
                for f in uv
            ]

        count = 0
        for fname, content in items:
            try:
                tmp = os.path.join(RESUME_DIR, fname)
                with open(tmp, "wb") as fh:
                    fh.write(content)
                res = self.engine.add_file(tmp)
                if res:
                    _, name = res
                    self._q(f"📁 Loaded: {name}")
                    count += 1
                else:
                    self._q(f"❌ ไม่สามารถโหลด: {fname}")
            except Exception as e:
                self._q(f"❌ {fname}: {e}")

        if count:
            self._q(f"✅ เพิ่มสำเร็จ {count} ไฟล์")

        # Reset upload widget (value is read-only)
        new_up = widgets.FileUpload(
            accept=".torrent", multiple=True,
            description="📁 Upload .torrent",
            layout=widgets.Layout(width="100%"),
        )
        kids = list(self.root.children)
        for i, c in enumerate(kids):
            if c is self._upload:
                kids[i] = new_up
                break
        self.root.children = tuple(kids)
        self._upload = new_up

    def _on_clear(self, _):
        for ih in list(self.engine.handles):
            self.engine.remove(ih, del_files=False)
        self._q("🗑️ Removed all torrents (files kept)")

    def _on_drive(self, _):
        try:
            from google.colab import drive
            drive.mount("/content/drive", force_remount=False)
            dest = "/content/drive/MyDrive/TitanTorrent"
            os.makedirs(dest, exist_ok=True)
            n = 0
            for item in os.listdir(DOWNLOAD_DIR):
                src = os.path.join(DOWNLOAD_DIR, item)
                dst = os.path.join(dest, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    n += 1
                elif os.path.isdir(src):
                    if os.path.exists(dst): shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    n += 1
            self._q(f"💾 Exported {n} item(s) → /MyDrive/TitanTorrent/")
        except Exception as e:
            self._q(f"⚠️ Drive error: {e}")

    # ── UI update (called from monitor thread) ────────────────────────────────
    def _update_ui(self, all_stats: List[TorrentStats]):
        now    = datetime.now()
        elapsed = (now - self._session_start).total_seconds()
        pulse  = ("🟢" if self._iter % 2 == 0 else "🔵") \
                 if any(s.status == TorrentStatus.DOWNLOADING for s in all_stats) \
                 else "⚪"

        # ── aggregate stats ────────────────────────────────────────────────
        t_dl   = sum(s.download_rate for s in all_stats)
        t_ul   = sum(s.upload_rate   for s in all_stats)
        t_peer = sum(s.num_peers     for s in all_stats)
        active = sum(1 for s in all_stats if s.status == TorrentStatus.DOWNLOADING)

        def _box(val, lbl):
            return (
                f'<div class="tt-stat-box">'
                f'<div class="tt-stat-val">{val}</div>'
                f'<div class="tt-stat-lbl">{lbl}</div>'
                f'</div>'
            )

        self._s_dl.value   = _box(f"{pulse} {_fmt_speed(t_dl)}",  "Download")
        self._s_ul.value   = _box(_fmt_speed(t_ul),               "Upload")
        self._s_peer.value = _box(str(t_peer),                    "Peers")
        self._s_live.value = _box(
            f"{active}/{len(all_stats)}",
            f"Active · {now.strftime('%H:%M:%S')}"
        )

        # ── session timer ──────────────────────────────────────────────────
        self._session_lbl.value = (
            f'<span style="font-family:\'Share Tech Mono\',monospace;'
            f'color:#00cc66;font-size:11px;">Session: {_fmt_dur(elapsed)}</span>'
        )
        hb_col = "#00ff88" if self._keep_alive.value else "#333"
        self._heartbeat.value = (
            f'<span style="color:{hb_col};font-size:14px;">'
            f'{"●" if self._iter % 2 == 0 else "○"}</span>'
        )

        # ── torrent cards ──────────────────────────────────────────────────
        if not all_stats:
            self._torrent_list.children = (
                widgets.HTML(
                    '<div style="font-family:\'Share Tech Mono\',monospace;'
                    'color:#333;text-align:center;padding:20px;">'
                    'No active torrents</div>'
                ),
            )
            return

        ICONS = {
            TorrentStatus.SEEDING:    "⬆️",
            TorrentStatus.FINISHED:   "✅",
            TorrentStatus.PAUSED:     "⏸️",
            TorrentStatus.CHECKING:   "🔍",
            TorrentStatus.METADATA:   "📡",
            TorrentStatus.ERROR:      "❌",
            TorrentStatus.QUEUED:     "⏳",
        }
        tick = self._iter % 2

        cards = []
        for s in all_stats:
            if s.status == TorrentStatus.DOWNLOADING:
                icon = "⬇️" if tick == 0 else "📥"
            elif s.status == TorrentStatus.METADATA:
                icon = "📡" if tick == 0 else "🔍"
            else:
                icon = ICONS.get(s.status, "⏳")

            is_active = s.status == TorrentStatus.DOWNLOADING
            border    = "rgba(0,255,136,0.5)" if is_active else "rgba(255,107,53,0.25)"
            glow      = "tt-bar-fill glow"    if is_active else "tt-bar-fill"
            spd_cls   = "spd"                  if is_active else "dim"

            name_safe = (s.name[:60] + "…") if len(s.name) > 60 else s.name

            html = f"""
<div class="tt-card {'active' if is_active else ''}"
     style="border-color:{border};">
  <div class="tt-name">{icon} {name_safe}</div>
  <div class="tt-bar-wrap">
    <div class="{glow}" style="width:{s.pct:.1f}%;"></div>
  </div>
  <div class="tt-meta">
    <span class="hi">📊 {s.pct:.2f}%</span>
    <span class="{spd_cls}">⬇️ {_fmt_speed(s.download_rate)}</span>
    <span>⬆️ {_fmt_speed(s.upload_rate)}</span>
    <span>👥 {s.num_peers}</span>
    <span>⏱️ {s.eta_fmt}</span>
    <span class="dim">{_fmt_bytes(s.downloaded)} / {_fmt_bytes(s.total_size)}</span>
  </div>
  {f'<div style="color:#ff4444;font-size:11px;margin-top:4px;">⚠️ {s.error_msg}</div>' if s.error_msg else ''}
</div>
"""
            cards.append(widgets.HTML(html))

        self._torrent_list.children = tuple(cards)

    # ── monitoring loop (ONE thread, replaces both old loops) ─────────────────
    def _loop(self):
        hb_interval   = 60   # heartbeat print every 1 min (บ่อยขึ้นเพื่อกัน Colab หลับ)
        last_stats_time = 0
        while self._running:
            try:
                self._iter += 1

                # ── flush log queue first ─────────────────────────────────
                self._flush_log()

                # ── collect libtorrent alerts ─────────────────────────────
                try:
                    alerts = self.engine.pop_alerts()
                    for alert in alerts:
                        if isinstance(alert, lt.torrent_finished_alert):
                            self._q(f"✅ Download complete: {alert.torrent_name}")
                        elif isinstance(alert, lt.torrent_error_alert):
                            self._q(f"❌ Error: {alert.message()}")
                except Exception:
                    pass

                # ── UI update ถูกจัดการโดย JavaScript แล้ว ไม่ต้องทำใน thread
                pass

                # ── console heartbeat ─────────────────────────────────────
                if self._keep_alive.value and self._iter % hb_interval == 0:
                    elapsed = (datetime.now() - self._session_start).total_seconds()
                    # พิมพ์เพื่อกัน Colab ตัดการเชื่อมต่อ
                    print(f"[{datetime.now():%H:%M:%S}] 🔥 Titan Alive · Session: {_fmt_dur(elapsed)} · Torrents: {len(self.engine.handles)}")

            except Exception as exc:
                # Never let the loop die silently
                try:
                    self._q(f"⚠️ Loop error: {exc}")
                except:
                    pass

            time.sleep(MONITOR_INTERVAL)

    # ── public API ────────────────────────────────────────────────────────────
    def start(self):
        if self._running:
            return
        self._running = True
        # ใช้ daemon=False เพื่อให้ thread อยู่รอดหลัง cell จบ (Colab จะไม่ฆ่า)
        self._thread  = threading.Thread(target=self._loop, daemon=False)
        self._thread.start()
        self._q("🧲 Titan Torrent v2.3 พร้อมใช้งาน!")
        self._q("💡 วาง magnet link แล้วกด ADD · หรืออัปโหลดไฟล์ .torrent")
        self._q("🔄 กด REFRESH เพื่ออัปเดตสถานะ · เปิด Auto Stats เพื่ออัปเดตอัตโนมัติ")

    def shutdown(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        try:
            self.engine.shutdown()
        except Exception:
            pass

    def show(self):
        display(self.root)
        if getattr(self, '_js_enabled', False):
            js = """
            // Titan auto-refresh ทุก 1 วินาที
            if (window.titanInterval) clearInterval(window.titanInterval);
            window.titanInterval = setInterval(() => {
                google.colab.kernel.invokeFunction('titan.refresh', [], {});
            }, 1000);
            """
            display(Javascript(js))
            self._q("⚡ Auto-refresh ผ่าน JavaScript เปิดใช้งาน")

# ── 8. LAUNCH (singleton-guarded) ─────────────────────────────────────────────
_app = TitanDashboard()
_app.start()
_app.show()

# Register in globals so re-run can shut down cleanly
globals()[_TITAN_INSTANCE_KEY] = _app

print(f"\n✅ Titan Torrent v2 started · {datetime.now():%Y-%m-%d %H:%M:%S}")
print(f"📂 Download dir: {DOWNLOAD_DIR}")
print("─" * 50)
print("Re-running this cell will cleanly restart the instance.")
