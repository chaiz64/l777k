# @title 🧲 TITAN TORRENT v3 — Rich Live Edition for Google Colab
# ============================================================
#  Auto-Work Operation System (Rich Live)
#  Titan Torrent v3.0 — BitTorrent Client
#  Built with: libtorrent + Rich
# ============================================================

# ── Step 0: Install dependencies ──────────
import subprocess, sys

def _pip(pkg: str):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

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
    import rich
except ImportError:
    _pip("rich")

# ── Core imports ─────────────────────────
import os, time, shutil, threading, logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn
from rich.align import Align
from rich.text import Text
from rich import box

# ════════════════════════════════════════════════════════════
@dataclass
class TorrentConfig:
    download_dir: Path = Path("/content/torrent_downloads")
    drive_export_dir: Path = Path("/content/drive/MyDrive/TitanTorrent")
    max_connections: int = 200
    upload_limit_kbps: int = 100
    enable_dht: bool = True

# ════════════════════════════════════════════════════════════
@dataclass
class TorrentInfo:
    info_hash: str
    name: str = ""
    progress: float = 0.0
    dl_speed: float = 0.0
    ul_speed: float = 0.0
    peers: int = 0
    seeds: int = 0
    size: int = 0
    downloaded: int = 0
    state: str = "queued"
    eta: int = 0

# ════════════════════════════════════════════════════════════
class TitanEngine:
    def __init__(self, config: TorrentConfig):
        self.config = config
        self.config.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = self._make_session()
        self.handles: Dict[str, lt.torrent_handle] = {}
        self._lock = threading.Lock()

    def _make_session(self) -> lt.session:
        settings = {
            'listen_interfaces': '0.0.0.0:6881',
            'enable_dht': self.config.enable_dht,
            'enable_lsd': True,
            'enable_upnp': True,
            'enable_natpmp': True,
            'upload_rate_limit': self.config.upload_limit_kbps * 1024,
            'connections_limit': self.config.max_connections,
        }
        ses = lt.session(settings)
        ses.add_dht_router('router.bittorrent.com', 6881)
        ses.add_dht_router('router.utorrent.com', 6881)
        return ses

    def add_magnet(self, uri: str) -> Optional[str]:
        try:
            params = lt.parse_magnet_uri(uri)
            params.save_path = str(self.config.download_dir)
            handle = self.session.add_torrent(params)
            ih = str(handle.info_hash())
            with self._lock:
                self.handles[ih] = handle
            return ih
        except Exception:
            return None

    def add_torrent_file(self, path: Path) -> Optional[str]:
        try:
            info = lt.torrent_info(str(path))
            params = lt.add_torrent_params()
            params.ti = info
            params.save_path = str(self.config.download_dir)
            handle = self.session.add_torrent(params)
            ih = str(handle.info_hash())
            with self._lock:
                self.handles[ih] = handle
            return ih
        except Exception:
            return None

    def get_all_info(self) -> List[TorrentInfo]:
        infos = []
        with self._lock:
            handles = list(self.handles.items())
        
        for ih, h in handles:
            try:
                s = h.status()
                info = TorrentInfo(info_hash=ih)
                
                if s.has_metadata:
                    info.name = h.get_torrent_info().name() if h.get_torrent_info() else f"Torrent {ih[:8]}"
                else:
                    info.name = f"Fetching metadata... ({s.num_peers} peers)"
                
                info.progress = s.progress
                info.dl_speed = s.download_rate
                info.ul_speed = s.upload_rate
                info.peers = s.num_peers
                info.seeds = s.num_seeds
                info.size = s.total_wanted
                info.downloaded = s.total_wanted_done
                info.state = str(s.state).split('.')[-1]
                
                if s.download_rate > 0:
                    remaining = s.total_wanted - s.total_wanted_done
                    info.eta = int(remaining / s.download_rate)
                
                infos.append(info)
            except Exception:
                continue
        return infos

    def remove_all(self):
        with self._lock:
            for h in self.handles.values():
                self.session.remove_torrent(h, False)
            self.handles.clear()

# ════════════════════════════════════════════════════════════
class TitanUI:
    BANNER = """
╔════════════════════════════════════════╗
║   🧲 TITAN TORRENT v3.0 — Rich Live   ║
║   BitTorrent Client for Google Colab   ║
╚════════════════════════════════════════╝
"""

    def __init__(self, engine: TitanEngine):
        self.engine = engine
        self.console = Console()
        self.running = True

    def _format_bytes(self, n: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if n < 1024: return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    def _format_speed(self, n: float) -> str:
        return self._format_bytes(int(n)) + "/s"

    def _make_table(self, infos: List[TorrentInfo]) -> Table:
        table = Table(box=box.SIMPLE_HEAVY, expand=True, show_lines=False)
        table.add_column("#", width=3, style="dim")
        table.add_column("Name", style="bright_white", no_wrap=False, max_width=40)
        table.add_column("Progress", width=12)
        table.add_column("DL", justify="right", style="green", width=10)
        table.add_column("UL", justify="right", style="cyan", width=10)
        table.add_column("Peers", justify="center", width=6)
        table.add_column("ETA", justify="right", width=8)
        table.add_column("Status", width=10)

        for i, info in enumerate(infos, 1):
            pct = info.progress * 100
            bar_filled = int(pct / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            
            name = info.name[:38] + "…" if len(info.name) > 38 else info.name
            eta_str = f"{info.eta//3600:02d}:{(info.eta%3600)//60:02d}:{info.eta%60:02d}" if info.eta > 0 else "--:--"
            
            table.add_row(
                str(i),
                name,
                f"[cyan]{bar}[/cyan] {pct:.1f}%",
                self._format_speed(info.dl_speed),
                self._format_speed(info.ul_speed),
                str(info.peers),
                eta_str,
                info.state
            )
        return table

    def run_live(self):
        self.console.print(Panel(Align.center(self.BANNER), border_style="bright_cyan"))
        
        # Get magnets
        self.console.print("[bold cyan]วาง Magnet Links (คั่นด้วยบรรทัดว่างเพื่อเริ่ม):[/bold cyan]")
        magnets = []
        while True:
            line = input()
            if not line.strip():
                break
            if line.strip().startswith('magnet:'):
                magnets.append(line.strip())
        
        if not magnets:
            self.console.print("[yellow]ไม่มี magnet — ออก[/yellow]")
            return
        
        for m in magnets:
            ih = self.engine.add_magnet(m)
            if ih:
                self.console.print(f"[green]✓ Added: {ih[:16]}...[/green]")
            else:
                self.console.print(f"[red]✗ Failed to add magnet[/red]")
        
        self.console.print("\n[bold]กด Ctrl+C เพื่อหยุด[/bold]\n")
        
        try:
            with Live(console=self.console, refresh_per_second=2, screen=False) as live:
                while self.running:
                    infos = self.engine.get_all_info()
                    
                    # Aggregate stats
                    total_dl = sum(i.dl_speed for i in infos)
                    total_ul = sum(i.ul_speed for i in infos)
                    total_peers = sum(i.peers for i in infos)
                    active = sum(1 for i in infos if i.dl_speed > 0)
                    
                    header = Table.grid(expand=True)
                    header.add_column()
                    header.add_column(justify="right")
                    header.add_row(
                        f"[bold bright_cyan]⬇ {self._format_speed(total_dl)}  ⬆ {self._format_speed(total_ul)}  👥 {total_peers}  🔥 {active}/{len(infos)} active[/bold bright_cyan]",
                        f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]"
                    )
                    
                    layout = Table.grid()
                    layout.add_row(header)
                    layout.add_row(self._make_table(infos))
                    
                    live.update(Panel(layout, border_style="bright_blue", title="Live Torrents"))
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            self.console.print("
[yellow]หยุดการทำงาน...[/yellow]")
            self.running = False

# ════════════════════════════════════════════════════════════
def main():
    console = Console()
    
    # Mount Drive
    try:
        from google.colab import drive
        if not Path("/content/drive").exists():
            drive.mount("/content/drive")
            console.print("[green]✓ Drive mounted[/green]")
    except:
        pass
    
    config = TorrentConfig()
    engine = TitanEngine(config)
    ui = TitanUI(engine)
    ui.run_live()

if __name__ == "__main__":
    main()
