import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json
import csv
import base64
from urllib.parse import urlparse, urljoin
from functools import lru_cache
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Tuple
import hashlib
import time
import random
from concurrent.futures import ThreadPoolExecutor
import os
import signal
import sys
import shutil
import mimetypes
import binascii

# Fix UnicodeEncodeError by setting stdout encoding to utf-8
# This is the simplest way to solve Thai printing issues in Windows Console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
# Explicitly set FileHandler and StreamHandler to use encoding='utf-8'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Constants for Request Headers
FETCH_HEADERS = {
    "accept": "*/*",
    "accept-language": "en,th;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "referer": "https://www.91cg1.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Color codes for Terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_BLACK = '\033[40m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# ASCII Art for "91cg1"
def get_91cg1_ascii_art():
    return [
        "  ██████╗  ██╗   ██╗ ███████╗  ██████╗  ██╗  ██╗ ",
        "  ██╔══██╗ ██║   ██║ ██╔════╝ ██╔════╝  ██║  ██║ ",
        "  ██████╔╝ ██║   ██║ █████╗   ██║       ███████║ ",
        "  ██╔══██╗ ██║   ██║ ██╔══╝   ██║       ██╔══██║ ",
        "  ██║  ██║ ███████║ ███████╗  ██████╗  ██║  ██║ ",
        "  ╚═╝  ╚═╝ ╚══════╝ ╚══════╝  ╚══════╝  ╚═╝  ╚═╝ "
    ]

# Configuration (can be adjusted as needed)
@dataclass
class Config:
    MAX_PAGES: int = 3
    MAX_POSTS: int = 0
    SAVE_JSON: bool = True
    SAVE_CSV: bool = True
    SAVE_HTML: bool = True
    SAVE_MD: bool = True
    MAX_CONCURRENT_REQUESTS: int = 15
    REQUEST_TIMEOUT: int = 15
    RETRY_ATTEMPTS: int = 3
    DELAY_BETWEEN_REQUESTS: float = 0.5
    USER_AGENTS: List[str] = None
    PROXY_URLS: List[str] = None

    def __post_init__(self):
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]

@dataclass
class Base64ReverseEngineered:
    data_url: str
    is_valid: bool
    image_type: Optional[str] = None
    hidden_data: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)

class AdvancedBase64Analyzer:
    # รูปแบบที่พบบ่อยของ Base64 ที่ถูกแปลง
    COMMON_OBFUSCATION_PATTERNS = [
        r'data:\s*image/\w+;\s*base64\s*,\s*([^\'"]+)',  # มีช่องว่าง
        r'data:image/[^;]+;charset=[^;]+;base64,([^\'"]+)',  # มี charset
        r'data:image/[^;]+;version=[^;]+;base64,([^\'"]+)',  # มี version
        r'data:[\s\S]+?base64,([^\'"]+)'  # รูปแบบทั่วไป
    ]

    # รูปแบบที่อาจซ่อนข้อมูล
    SUSPICIOUS_PATTERNS = [
        r'eval\(',
        r'function\(',
        r'unescape\(',
        r'fromCharCode\(',
        r'String\.fromCharCode\(',
        r'\\x[0-9a-fA-F]{2}',
        r'%[0-9a-fA-F]{2}'
    ]

    @classmethod
    def decode_obfuscated_base64(cls, data_url: str) -> Optional[str]:
        """ถอดรหัส Base64 ที่ถูกแปลงรูปแบบ"""
        for pattern in cls.COMMON_OBFUSCATION_PATTERNS:
            match = re.search(pattern, data_url, re.IGNORECASE)
            if match:
                base64_data = match.group(1)
                try:
                    # ลบช่องว่างและอักขระแปลกปลอม
                    cleaned = re.sub(r'[^a-zA-Z0-9+/=]', '', base64_data)
                    # เติม padding ถ้าจำเป็น
                    pad_len = len(cleaned) % 4
                    if pad_len:
                        cleaned += '=' * (4 - pad_len)
                    return cleaned
                except Exception:
                    continue
        return None

    @classmethod
    def analyze_image_structure(cls, decoded_data: bytes) -> Dict:
        """วิเคราะห์โครงสร้างของข้อมูลภาพ"""
        analysis = {
            'signature': decoded_data[:8].hex(),
            'size_bytes': len(decoded_data),
            'likely_type': None,
            'is_valid_image': False
        }

        # ตรวจสอบ signature ที่รู้จัก
        signatures = {
            'ffd8ffe0': 'JPEG',
            '89504e47': 'PNG',
            '47494638': 'GIF',
            '52494646': 'WEBP',
            '49492a00': 'TIFF',
            '4d4d002a': 'TIFF'
        }

        file_sig = analysis['signature']
        for sig, img_type in signatures.items():
            if file_sig.startswith(sig):
                analysis['likely_type'] = img_type
                analysis['is_valid_image'] = True
                break

        return analysis

    @classmethod
    def detect_hidden_data(cls, decoded_data: bytes) -> Optional[str]:
        """ตรวจสอบข้อมูลที่อาจซ่อนอยู่ในภาพ"""
        try:
            text_data = decoded_data.decode('utf-8', errors='ignore')

            # ตรวจหารูปแบบที่สงสัยว่าจะมีโค้ดหรือข้อมูลซ่อนอยู่
            suspicious = []
            for pattern in cls.SUSPICIOUS_PATTERNS:
                if re.search(pattern, text_data):
                    suspicious.append(pattern)

            return suspicious if suspicious else None
        except Exception:
            return None

    @classmethod
    def reverse_engineer(cls, data_url: str) -> Base64ReverseEngineered:
        """ทำ reverse engineering Base64 image"""
        result = Base64ReverseEngineered(data_url=data_url, is_valid=False)

        try:
            # ลองถอดรหัสแบบมาตรฐานก่อน
            try:
                header, data = data_url.split(';base64,')
                decoded_data = base64.b64decode(data)
                result.is_valid = True
            except (ValueError, binascii.Error):
                # ถ้าไม่ได้ ลองถอดรหัสแบบที่ถูกแปลงรูปแบบ
                cleaned_data = cls.decode_obfuscated_base64(data_url)
                if cleaned_data:
                    decoded_data = base64.b64decode(cleaned_data)
                    result.is_valid = True
                    result.anomalies.append('obfuscated_base64')
                else:
                    raise ValueError("Invalid Base64 data")

            # วิเคราะห์โครงสร้างภาพ
            image_analysis = cls.analyze_image_structure(decoded_data)
            result.metadata.update(image_analysis)

            if not image_analysis['is_valid_image']:
                result.anomalies.append('invalid_image_structure')

            # ตรวจหาข้อมูลที่ซ่อนอยู่
            hidden = cls.detect_hidden_data(decoded_data)
            if hidden:
                result.hidden_data = hidden
                result.anomalies.append('possible_hidden_data')

            # ระบุประเภทภาพ
            result.image_type = image_analysis['likely_type']

        except Exception as e:
            result.anomalies.append(f'processing_error: {str(e)}')

        return result

@dataclass
class Base64Image:
    data_url: str
    file_name: str = ""
    file_extension: str = ""
    file_path: str = ""
    mime_type: str = ""
    size_kb: float = 0.0

    def __post_init__(self):
        """Extract metadata from Base64 data URL"""
        if not self.data_url.startswith('data:image/'):
            raise ValueError("Invalid Base64 image data URL")

        # Extract MIME type
        mime_type = self.data_url.split(';')[0][5:]
        self.mime_type = mime_type

        # Determine file extension
        self.file_extension = mimetypes.guess_extension(mime_type) or '.bin'
        if self.file_extension == '.jpe':
            self.file_extension = '.jpg'

        # Calculate size in KB
        base64_data = self.data_url.split(',')[1]
        self.size_kb = (len(base64_data) * 3 / 4) / 1024  # Approximate size

        # Generate filename if not provided
        if not self.file_name:
            self.file_name = f"image_{hash(self.data_url[:50])}{self.file_extension}"

class M3U8Analyzer:
    """Advanced M3U8 stream analyzer"""

    @staticmethod
    def parse_m3u8(content: str) -> dict:
        """Parses M3U8 content into structured data"""
        result = {
            'type': None,
            'version': None,
            'target_duration': None,
            'media_sequences': [],
            'stream_infos': [],
            'key_infos': [],
            'segments': []
        }

        lines = [line.strip() for line in content.split('\n') if line.strip()]

        if not lines or lines[0] != '#EXTM3U':
            return result

        result['type'] = 'master' if '#EXT-X-STREAM-INF' in content else 'media'

        for line in lines:
            if line.startswith('#EXT-X-VERSION:'):
                result['version'] = line.split(':')[1]
            elif line.startswith('#EXT-X-TARGETDURATION:'):
                result['target_duration'] = line.split(':')[1]
            elif line.startswith('#EXT-X-STREAM-INF:'):
                stream_info = {}
                parts = line.split(':')[1].split(',')
                for part in parts:
                    if '=' in part:
                        key, val = part.split('=', 1)
                        stream_info[key] = val
                result['stream_infos'].append(stream_info)
            elif line.startswith('#EXT-X-KEY:'):
                key_info = {}
                parts = line.split(':')[1].split(',')
                for part in parts:
                    if '=' in part:
                        key, val = part.split('=', 1)
                        key_info[key] = val.strip('"')
                result['key_infos'].append(key_info)
            elif not line.startswith('#'):
                result['segments'].append(line)

        return result

    @staticmethod
    async def analyze_stream(session: aiohttp.ClientSession, url: str) -> dict:
        """Comprehensive stream analysis"""
        analysis = {
            'url': url,
            'valid': False,
            'type': None,
            'encrypted': False,
            'drm_info': None,
            'bitrates': [],
            'resolutions': [],
            'codecs': [],
            'duration': None,
            'segment_count': 0,
            'redirect_chain': [],
            'errors': []
        }

        try:
            async with session.get(
                url,
                headers=FETCH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True
            ) as response:
                # Track redirects
                analysis['redirect_chain'] = [str(response.history[0].url)] if response.history else []
                analysis['redirect_chain'].append(str(response.url))

                content = await response.text()

                if '#EXTM3U' not in content:
                    analysis['errors'].append('Not a valid M3U8 file')
                    return analysis

                parsed = M3U8Analyzer.parse_m3u8(content)
                analysis.update(parsed)
                analysis['valid'] = True

                # Check for encryption
                analysis['encrypted'] = len(parsed['key_infos']) > 0
                if analysis['encrypted']:
                    analysis['drm_info'] = parsed['key_infos'][0].get('METHOD', 'UNKNOWN')

                # Calculate approximate duration
                if parsed['segments']:
                    analysis['segment_count'] = len(parsed['segments'])
                    if parsed['target_duration']:
                        analysis['duration'] = float(parsed['target_duration']) * analysis['segment_count']

                # Extract bitrates and resolutions for master playlists
                if analysis['type'] == 'master':
                    for stream in parsed['stream_infos']:
                        analysis['bitrates'].append(int(stream.get('BANDWIDTH', 0)))
                        analysis['resolutions'].append(stream.get('RESOLUTION', 'N/A'))
                        analysis['codecs'].append(stream.get('CODECS', 'N/A'))

        except Exception as e:
            analysis['errors'].append(str(e))

        return analysis


@dataclass
class PostData:
    post_id: str
    title: str
    link: str
    description: Optional[str]
    datePublished: Optional[str]
    video_links: List[dict]  # Changed from List[str] to store more info
    categories: List[str]
    reverse_engineered_images: List[Base64ReverseEngineered] = field(default_factory=list)
    hash: Optional[str] = None
    m3u8_analysis: List[dict] = field(default_factory=list)  # Added for detailed analysis

    def __post_init__(self):
        self.hash = hashlib.md5((self.link + str(time.time())).encode()).hexdigest()
        # Convert simple video links to dict format if needed
        if self.video_links and isinstance(self.video_links[0], str):
            self.video_links = [{'url': url, 'valid': None} for url in self.video_links]

# Class for URL utilities
class URLUtils:
    @staticmethod
    @lru_cache(maxsize=1024)
    def clean_url(url: str) -> str:
        """Cleans the URL by removing query parameters and fragments"""
        url = url.split('?')[0].split('#')[0]
        return url.rstrip('/')

    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """Checks if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False

    @staticmethod
    def get_random_user_agent(config: Config) -> str:
        """Returns a random User-Agent from Config"""
        return random.choice(config.USER_AGENTS)

# Class for managing Requests and Retries
class RequestManager:
    def __init__(self, config: Config):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT),
            connector=aiohttp.TCPConnector(limit=self.config.MAX_CONCURRENT_REQUESTS)
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def fetch(self, url: str, method: str = 'GET', headers: dict = None, **kwargs) -> Optional[str]:
        """Fetches URL with retries and random delay"""
        headers = headers or FETCH_HEADERS.copy()
        headers['user-agent'] = URLUtils.get_random_user_agent(self.config)

        for attempt in range(self.config.RETRY_ATTEMPTS):
            try:
                async with self.semaphore:
                    await asyncio.sleep(random.uniform(0, self.config.DELAY_BETWEEN_REQUESTS))
                    async with self.session.request(
                        method,
                        url,
                        headers=headers,
                        **kwargs
                    ) as response:
                        response.raise_for_status()
                        return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.config.RETRY_ATTEMPTS - 1:
                    logging.error(f"Failed to fetch {url} after {self.config.RETRY_ATTEMPTS} attempts")
                    return None
                await asyncio.sleep((attempt + 1) * 2)
        return None

# Class for parsing content
class ContentParser:
    @staticmethod
    def extract_post_links(html: str, base_url: str) -> Set[str]:
        """Extracts all post links from an Archives page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/archives/' in href and href.rstrip('/').split('/')[-1].isdigit():
                post_url = urljoin(base_url, href)
                links.add(URLUtils.clean_url(post_url))
        return links

    @staticmethod
    def find_next_page(html: str, current_url: str) -> Optional[str]:
        """Finds the URL of the next page in pagination"""
        soup = BeautifulSoup(html, 'html.parser')
        next_links = [
            soup.find('a', string=lambda t: t and (t.strip() == '下一页' or t.strip().lower() in ['next', 'next page'])),
            soup.find('a', rel='next'),
            soup.find('a', class_=re.compile(r'next|page-next', re.I)),
            soup.find('li', class_=re.compile(r'next|page-next', re.I))
        ]
        for link in filter(None, next_links):
            href = link.get('href')
            if href:
                return urljoin(current_url, href)
        return None

    @staticmethod
    def extract_video_links(html: str, base_url: str) -> List[str]:
        """Extracts video (m3u8) links from HTML with enhanced detection"""
        soup = BeautifulSoup(html, 'html.parser')
        video_links = set()

        # Improved extraction patterns
        extraction_methods = [
            # 1. Standard video tags
            {
                'tags': ['video', 'source', 'iframe'],
                'attrs': ['src', 'data-src', 'data-url', 'data-video-url']
            },
            # 2. Anchor tags
            {
                'tags': ['a'],
                'attrs': ['href']
            },
            # 3. Script variables
            {
                'pattern': r'(?:var|let|const)\s+\w*\s*=\s*["\'](https?://[^"\'\s]+\.m3u8[^"\'\s]*)["\']'
            },
            # 4. JSON configurations
            {
                'pattern': r'{\s*["\']url["\']\s*:\s*["\'](https?://[^"\'\s]+\.m3u8[^"\'\s]*)["\']'
            },
            # 5. DPlayer specific
            {
                'selector': '.dplayer',
                'config_attr': 'data-config'
            }
        ]

        # Execute all extraction methods
        for method in extraction_methods:
            if 'tags' in method:
                for tag in method['tags']:
                    for element in soup.find_all(tag):
                        for attr in method['attrs']:
                            if element.get(attr) and '.m3u8' in element.get(attr).lower():
                                video_links.add(urljoin(base_url, element.get(attr)))

            if 'pattern' in method:
                matches = re.findall(method['pattern'], html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = next((m for m in match if m and '.m3u8' in m.lower()), None)
                    if match:
                        video_links.add(urljoin(base_url, match))

            if 'selector' in method:
                for element in soup.select(method['selector']):
                    config = element.get(method.get('config_attr', 'data-config'))
                    if config:
                        try:
                            config_data = json.loads(config)
                            if isinstance(config_data, dict) and 'url' in config_data and '.m3u8' in config_data['url'].lower():
                                video_links.add(urljoin(base_url, config_data['url']))
                        except json.JSONDecodeError:
                            # Fallback to regex if JSON parsing fails
                            matches = re.findall(r'["\']url["\']\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', config)
                            for m in matches:
                                if m and '.m3u8' in m.lower():
                                    video_links.add(urljoin(base_url, m))

        # Additional advanced extraction
        # 1. Check for base64 encoded URLs
        base64_pattern = r'atob\(["\']([a-zA-Z0-9+/=]+)["\']'
        for match in re.findall(base64_pattern, html):
            try:
                decoded = base64.b64decode(match).decode('utf-8')
                if '.m3u8' in decoded:
                    video_links.add(decoded)
            except (binascii.Error, UnicodeDecodeError) as e:
                logging.warning(f"Failed to decode Base64 URL: {match[:50]}... Error: {e}")
                continue

        # 2. Check for encoded URLs
        encoded_pattern = r'(?:decodeURIComponent|unescape)\(["\']([^"\']+)["\']\)'
        for match in re.findall(encoded_pattern, html):
            try:
                decoded = unquote(match)
                if '.m3u8' in decoded:
                    video_links.add(decoded)
            except Exception as e:
                logging.warning(f"Failed to decode URL: {match[:50]}... Error: {e}")
                continue

        return list(video_links)

    @staticmethod
    def extract_base64_images(html: str) -> List[Base64ReverseEngineered]:
        """สกัดและวิเคราะห์ Base64 images แบบ reverse engineering"""
        # สกัดข้อมูล Base64 ทั้งหมดจาก HTML
        base64_patterns = [
            r'data:\s*image/[^;]+;\s*base64\s*,\s*[^\'">]+',
            r'src=["\'](data:image/[^"\']+)["\']',
            r'url\(["\']?(data:image/[^"\')]+)',
            r'background-image:\s*url\(["\']?(data:image/[^"\')]+)'
        ]

        found_images = set()
        for pattern in base64_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            found_images.update(matches)

        # วิเคราะห์แต่ละภาพ
        analyzed_images = []
        for img_data in found_images:
            try:
                analyzed = AdvancedBase64Analyzer.reverse_engineer(img_data)
                if analyzed.is_valid:
                    analyzed_images.append(analyzed)
            except Exception as e:
                logging.warning(f"Failed to analyze Base64 image: {str(e)}")

        return analyzed_images

    @staticmethod
    def extract_post_metadata(html: str, url: str) -> Dict:
        """Extracts post metadata (title, date, categories, description)"""
        soup = BeautifulSoup(html, 'html.parser')

        title = 'N/A'
        description = 'N/A'
        datePublished = 'N/A'

        # Extract data from JSON-LD schema first
        json_ld_script = soup.find('script', type='application/ld+json')
        if json_ld_script and json_ld_script.string:
            try:
                json_data = json.loads(json_ld_script.string)
                if isinstance(json_data, list):
                    json_data = json_data[0] # Assume the first item is the main post data

                if 'headline' in json_data:
                    title = json_data['headline']
                elif 'name' in json_data:
                    title = json_data['name']
                if 'description' in json_data:
                    description = json_data['description']
                if 'datePublished' in json_data:
                    datePublished = json_data['datePublished'].split('T')[0]
            except json.JSONDecodeError:
                logging.warning(f"Could not parse JSON-LD in post {url}")

        # Use data from other tags as fallback if JSON-LD is missing
        if title == 'N/A':
            title_tag = soup.find('h1', class_='post-title')
            title = title_tag.text.strip() if title_tag else 'N/A'

        if datePublished == 'N/A':
            date_tag = soup.find('meta', {'itemprop': 'datePublished'})
            datePublished = date_tag.get('content', 'N/A').split('T')[0] if date_tag else 'N/A'

        # Extract categories from various tags
        category_tags = soup.find_all(['a', 'span'], class_=['category', 'tag', 'post-category', 'nav-link'])
        categories = list({tag.text.strip().lower() for tag in category_tags if tag.text.strip()})

        return {
            'title': title,
            'description': description,
            'datePublished': datePublished,
            'categories': categories,
        }

class ImageStorage:
    @staticmethod
    def save_base64_image(base64_img: Base64Image, output_dir: str = "images") -> str:
        """Saves a Base64 image to disk and returns the file path"""
        os.makedirs(output_dir, exist_ok=True)

        # Extract the Base64 data
        header, data = base64_img.data_url.split(';base64,')

        # Decode and save the image
        file_path = os.path.join(output_dir, base64_img.file_name)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(data))

        base64_img.file_path = file_path
        return file_path

    @staticmethod
    def save_all_base64_images(images: List[Base64Image], output_dir: str = "images") -> List[Dict]:
        """Saves multiple Base64 images and returns their metadata"""
        saved_images = []
        for img in images:
            try:
                path = ImageStorage.save_base64_image(img, output_dir)
                saved_images.append({
                    'original_url': img.data_url[:100] + '...' if len(img.data_url) > 100 else img.data_url,
                    'file_name': img.file_name,
                    'file_path': path,
                    'mime_type': img.mime_type,
                    'size_kb': img.size_kb
                })
            except Exception as e:
                logging.error(f"Failed to save image {img.file_name}: {str(e)}")
        return saved_images


# Class for storing data in various formats
class DataStorage:
    @staticmethod
    def save_hls_report(data: List[PostData], filename: str = "hls_streams_report.html"):
        """Enhanced HLS report with analysis data"""
        html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>HLS/m3u8 Streams Report</title>
            <style>
                body { font-family: 'Courier New', monospace; margin: 20px; background: #000; color: #00ff00; }
                .digital-grid {
                    border: 2px solid #00ff00;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    background: #001100;
                    box-shadow: 0 0 20px #00ff00;
                }
                .grid-header {
                    text-align: center;
                    font-size: 1.5em;
                    margin-bottom: 20px;
                    text-shadow: 0 0 10px #00ff00;
                }
                .grid-content {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 15px;
                }
                .stream-card {
                    border: 1px solid #00ff00;
                    padding: 15px;
                    border-radius: 5px;
                    background: #002200;
                }
                .stream-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #ffff00;
                }
                .stream-url {
                    word-break: break-all;
                    margin-bottom: 10px;
                    font-size: 0.9em;
                }
                .action-buttons {
                    display: flex;
                    gap: 5px;
                    flex-wrap: wrap;
                }
                .btn {
                    background: #003300;
                    color: #00ff00;
                    border: 1px solid #00ff00;
                    padding: 5px 10px;
                    border-radius: 3px;
                    cursor: pointer;
                    font-family: 'Courier New', monospace;
                    font-size: 0.8em;
                }
                .btn:hover {
                    background: #00ff00;
                    color: #000;
                }
                .playlist-btn {
                    background: #ff6600;
                    color: #fff;
                    border: 1px solid #ff6600;
                }
                .playlist-btn:hover {
                    background: #ff8800;
                }
                .search-container {
                    margin-bottom: 20px;
                    text-align: center;
                }
                #searchInput {
                    background: #001100;
                    color: #00ff00;
                    border: 1px solid #00ff00;
                    padding: 8px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
                #searchInput::placeholder {
                    color: #00aa00;
                }
                .stats {
                    text-align: center;
                    margin: 20px 0;
                    font-size: 1.2em;
                }
                .analysis-details {
                    margin-top: 10px;
                    background: #000;
                    border: 1px solid #00ff00;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
                .analysis-details pre {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <div class="digital-grid">
                <div class="grid-header">HLS/m3u8 STREAMS REPORT</div>
                <div class="stats">
                    <span id="totalStreams">0</span> Total Streams |
                    <span id="totalPosts">0</span> Posts with Streams
                </div>
                <div class="search-container">
                    <input type="text" id="searchInput" placeholder="Search streams...">
                    <button class="btn" onclick="searchStreams()">Search</button>
                    <button class="btn playlist-btn" onclick="generatePlaylist()">Generate Playlist</button>
                </div>
                <div class="grid-content" id="streamGrid">"""

        for item in data:
            for i, stream in enumerate(item.video_links):
                if not stream['valid']:
                    continue

                analysis = next((a for a in item.m3u8_analysis if a['url'] == stream['url']), {})

                html += f"""
                <div class="stream-card" data-post-id="{item.post_id}" data-title="{item.title}">
                    <div class="stream-title">[{item.post_id}] {item.title}</div>
                    <div class="stream-url">{stream['url']}</div>
                    <div class="stream-info">
                        <strong>Type:</strong> {stream.get('type', 'N/A')} |
                        <strong>Streams:</strong> {stream.get('streams', 0)} |
                        <strong>Encrypted:</strong> {analysis.get('encrypted', False)} |
                        <strong>Duration:</strong> {analysis.get('duration', 'N/A')}s
                    </div>
                    <div class="action-buttons">
                        <button class="btn" onclick="openInPotPlayer(['{stream['url']}'])">PotPlayer</button>
                        <button class="btn" onclick="copyStream('{stream['url']}')">Copy URL</button>
                        <button class="btn" onclick="showAnalysis('analysis_{item.post_id}_{i}')">Analysis</button>
                    </div>
                    <div id="analysis_{item.post_id}_{i}" class="analysis-details" style="display:none;">
                        <pre>{json.dumps(analysis, indent=2)}</pre>
                    </div>
                </div>"""

        html += """
                </div>
            </div>
            <script>
                // Update stats
                const streamCards = document.querySelectorAll('.stream-card');
                document.getElementById('totalStreams').textContent = streamCards.length;
                document.getElementById('totalPosts').textContent = new Set([...streamCards].map(card => card.dataset.postId)).size;

                function searchStreams() {
                    const input = document.getElementById("searchInput");
                    const filter = input.value.toUpperCase();
                    const cards = document.querySelectorAll('.stream-card');

                    cards.forEach(card => {
                        const title = card.querySelector('.stream-title').textContent.toUpperCase();
                        const url = card.querySelector('.stream-url').textContent.toUpperCase();
                        const visible = title.includes(filter) || url.includes(filter);
                        card.style.display = visible ? 'block' : 'none';
                    });
                }

                function generatePlaylist() {
                    const streams = [];
                    document.querySelectorAll('.stream-card').forEach(card => {
                        const url = card.querySelector('.stream-url').textContent;
                        const title = card.querySelector('.stream-title').textContent;
                        streams.push({url, title});
                    });

                    if (streams.length === 0) {
                        alert('No streams available for playlist!');
                        return;
                    }

                    // Generate M3U playlist
                    let playlist = '#EXTM3U\\n';
                    streams.forEach(stream => {
                        playlist += `#EXTINF:-1,${stream.title}\\n`;
                        playlist += `${stream.url}\\n`;
                    });

                    // Download playlist
                    const blob = new Blob([playlist], {type: 'application/vnd.apple.mpegurl'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'hls_playlist.m3u';
                    a.click();
                    URL.revokeObjectURL(url);

                    alert(`Playlist generated with ${streams.length} streams!`);
                }

                function openInPotPlayer(links) {
                    if (links && links.length > 0) {
                        const potUri = 'potplayer://' + links.join('|');
                        navigator.clipboard.writeText(potUri);
                        alert('PotPlayer links copied to clipboard!');
                    } else {
                        alert('No HLS streams available!');
                    }
                }

                function copyStream(url) {
                    navigator.clipboard.writeText(url);
                    alert('Stream URL copied to clipboard!');
                }

                function openStream(url) {
                    window.open(url, '_blank');
                }

                function showAnalysis(id) {
                    const element = document.getElementById(id);
                    if (element.style.display === 'none') {
                        element.style.display = 'block';
                    } else {
                        element.style.display = 'none';
                    }
                }

                document.getElementById("searchInput").addEventListener("keyup", function(event) {
                    if (event.key === "Enter") {
                        searchStreams();
                    }
                });
            </script>
        </body>
        </html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    @staticmethod
    def save_base64_report(data: List[PostData], filename: str = "base64_images_report.html"):
        """Generates a separate Base64 images report with reverse engineering analysis"""
        html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Base64 Images Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; position: sticky; top: 0; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .base64-preview { max-width: 120px; max-height: 120px; border: 1px solid #ccc; border-radius: 4px; }
                .search-container { margin-bottom: 20px; }
                .download-btn { background: #4caf50; color: #fff; border: none; padding: 6px 16px; border-radius: 6px; cursor: pointer; margin: 4px; }
                .download-btn:hover { background: #45a049; }
                .copy-btn { background: #ff9800; color: #fff; border: none; padding: 6px 16px; border-radius: 6px; cursor: pointer; margin: 4px; }
                .copy-btn:hover { background: #f57c00; }
                .analysis-info { font-size: 0.8em; color: #555; margin-top: 5px; }
            </style>
        </head>
        <body>
            <h1>Base64 Images Report</h1>
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search...">
                <button onclick="searchTable()">Search</button>
            </div>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>Post ID</th><th>Title</th><th>Link</th><th>Image Preview</th><th>Analysis</th><th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""

        for item in data:
            if item.reverse_engineered_images:  # Display only posts with reverse-engineered images
                for i, img in enumerate(item.reverse_engineered_images):
                    title_text = f"Type: {img.image_type or 'N/A'}, Valid: {img.is_valid}"
                    if img.anomalies:
                        title_text += f", Anomalies: {', '.join(img.anomalies)}"
                    if img.hidden_data:
                        title_text += f", Hidden Data: {img.hidden_data}"

                    html += f"""
                        <tr>
                            <td>{item.post_id}</td>
                            <td>{item.title}</td>
                            <td><a href="{item.link}" target="_blank">{item.link}</a></td>
                            <td><img src="{img.data_url}" class="base64-preview" onclick="window.open('{img.data_url}')" title="Base64 Image {i+1}"></td>
                            <td>
                                <strong>Type:</strong> {img.image_type or 'N/A'}<br>
                                <strong>Valid:</strong> {img.is_valid}<br>
                                <strong>Size:</strong> {img.metadata.get('size_bytes', 'N/A')} bytes<br>
                                <strong>Signature:</strong> {img.metadata.get('signature', 'N/A')}<br>
                                <strong>Anomalies:</strong> {', '.join(img.anomalies) if img.anomalies else 'None'}<br>
                                <strong>Hidden Data:</strong> {img.hidden_data if img.hidden_data else 'None'}
                            </td>
                            <td>
                                <button class="download-btn" onclick="downloadBase64('{img.data_url}', 'image_{item.post_id}_{i}.png')">Download</button>
                                <button class="copy-btn" onclick="copyStream('{img.data_url}')">Copy URL</button>
                            </td>
                        </tr>"""

        html += """
                </tbody>
            </table>
            <script>
                function searchTable() {
                    const input = document.getElementById("searchInput");
                    const filter = input.value.toUpperCase();
                    const table = document.getElementById("dataTable");
                    const tr = table.getElementsByTagName("tr");
                    for (let i = 1; i < tr.length; i++) {
                        let found = false;
                        const td = tr[i].getElementsByTagName("td");
                        for (let j = 0; j < td.length; j++) {
                            if (td[j]) {
                                const txtValue = td[j].textContent || td[j].innerText;
                                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                                    found = true;
                                    break;
                                }
                            }
                        }
                        tr[i].style.display = found ? "" : "none";
                    }
                }

                function downloadBase64(dataUrl, filename) {
                    const link = document.createElement('a');
                    link.href = dataUrl;
                    link.download = filename;
                    link.click();
                }

                function copyStream(url) {
                    navigator.clipboard.writeText(url);
                    alert('Base64 Data URL copied to clipboard!');
                }

                document.getElementById("searchInput").addEventListener("keyup", function(event) {
                    if (event.key === "Enter") {
                        searchTable();
                    }
                });
            </script>
        </body>
        </html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    @staticmethod
    def save_hls_playlist(data: List[PostData], filename: str = "hls_playlist.m3u"):
        """Creates an HLS playlist file"""
        playlist_content = "#EXTM3U\n"

        for item in data:
            if item.video_links:
                for stream in item.video_links:
                    # Only add valid streams to the playlist
                    if stream['valid']:
                        playlist_content += f"#EXTINF:-1,{item.title}\n"
                        playlist_content += f"{stream['url']}\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(playlist_content)

    @staticmethod
    def save_json(data: List[PostData], filename: str = "scraped_data.json"):
        """Saves data to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([{
                'post_id': item.post_id,
                'title': item.title,
                'link': item.link,
                'description': item.description,
                'datePublished': item.datePublished,
                'video_links': item.video_links,
                'categories': item.categories,
                'reverse_engineered_images': [asdict(img) for img in item.reverse_engineered_images],
                'hash': item.hash,
                'm3u8_analysis': item.m3u8_analysis
            } for item in data], f, ensure_ascii=False, indent=4)

    @staticmethod
    def save_csv(data: List[PostData], filename: str = "scraped_data.csv"):
        """Saves data to a CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date Published", "Title", "Description", "Link", "Videos", "Categories", "Reverse Engineered Images (Type, Valid, Anomalies, Hidden Data)"])
            for item in data:
                reverse_engineered_summary = []
                for img in item.reverse_engineered_images:
                    summary = f"Type: {img.image_type}, Valid: {img.is_valid}"
                    if img.anomalies:
                        summary += f", Anomalies: {', '.join(img.anomalies)}"
                    if img.hidden_data:
                        summary += f", Hidden Data: {img.hidden_data}"
                    reverse_engineered_summary.append(summary)

                writer.writerow([
                    item.post_id,
                    item.datePublished,
                    item.title,
                    item.description,
                    item.link,
                    "|".join([v['url'] for v in item.video_links]), # Extract 'url' from each dictionary
                    "|".join(item.categories),
                    "|".join(reverse_engineered_summary)
                ])

    @staticmethod
    def save_html(data: List[PostData], filename: str = "scraped_data.html"):
        """Generates an interactive HTML report"""
        html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Scraped Data Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; position: sticky; top: 0; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .video-link { word-break: break-all; }
                .search-container { margin-bottom: 20px; }
                .base64-preview { max-width: 100px; max-height: 100px; border: 1px solid #ccc; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Scraped Data Report</h1>
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search...">
                <button onclick="searchTable()">Search</button>
            </div>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>ID</th><th>Date Published</th><th>Title</th><th>Description</th><th>Link</th><th>Videos</th><th>Categories</th><th>Reverse Engineered Images</th>
                    </tr>
                </thead>
                <tbody>"""
        for item in data:
            reverse_engineered_images_html = ""
            if item.reverse_engineered_images:
                for i, img in enumerate(item.reverse_engineered_images):
                    title_text = f"Type: {img.image_type or 'N/A'}, Valid: {img.is_valid}"
                    if img.anomalies:
                        title_text += f", Anomalies: {', '.join(img.anomalies)}"
                    if img.hidden_data:
                        title_text += f", Hidden Data: {img.hidden_data}"
                    reverse_engineered_images_html += f'<img src="{img.data_url}" class="base64-preview" onclick="window.open(\'{img.data_url}\')" title="{title_text}" style="max-width:100px;max-height:100px;border:1px solid #ccc;border-radius:4px;margin:2px;">'

            html += f"""
                <tr>
                    <td>{item.post_id}</td>
                    <td>{item.datePublished}</td>
                    <td>{item.title}</td>
                    <td>{item.description}</td>
                    <td><a href="{item.link}" target="_blank">{item.link}</a></td>
                    <td class="video-link">{"<br>".join([f'<a href="{vid}" target="_blank">Video {i+1}</a>' for i, vid in enumerate(item.video_links)])}</td>
                    <td>{", ".join(item.categories)}</td>
                    <td>{reverse_engineered_images_html}</td>
                </tr>"""
        html += """
                </tbody>
            </table>
            <script>
                function searchTable() {
                    const input = document.getElementById("searchInput");
                    const filter = input.value.toUpperCase();
                    const table = document.getElementById("dataTable");
                    const tr = table.getElementsByTagName("tr");
                    for (let i = 1; i < tr.length; i++) {
                        let found = false;
                        const td = tr[i].getElementsByTagName("td");
                        // Search all columns except the last one (Reverse Engineered Images column)
                        for (let j = 0; j < td.length - 1; j++) {
                            if (td[j]) {
                                const txtValue = td[j].textContent || td[j].innerText;
                                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                                    found = true;
                                    break;
                                }
                            }
                        }
                        tr[i].style.display = found ? "" : "none";
                    }
                }
                document.getElementById("searchInput").addEventListener("keyup", function(event) {
                    if (event.key === "Enter") {
                        searchTable();
                    }
                });
            </script>
        </body>
        </html>"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    @staticmethod
    def save_markdown(data: List[PostData], filename: str = "scraped_data.md"):
        """Saves data to a Markdown file"""
        md = "# Scraped Data Report\n\n"
        md += "| ID | Date Published | Title | Description | Link | Videos | Categories | Reverse Engineered Images |\n"
        md += "|----|----------------|-------|-------------|------|--------|------------|---------------------------|\n"
        for item in data:
            videos_md = " ".join([f"[▶️]({vid})" for vid in item.video_links])

            reverse_engineered_md = []
            for img in item.reverse_engineered_images:
                summary = f"Type: {img.image_type or 'N/A'}, Valid: {img.is_valid}"
                if img.anomalies:
                    summary += f", Anomalies: {', '.join(img.anomalies)}"
                if img.hidden_data:
                    summary += f", Hidden Data: {img.hidden_data}"
                reverse_engineered_md.append(f"[{summary}]({img.data_url[:50]}...)") # Link to data_url, truncate for markdown table

            md += f"| {item.post_id} | {item.datePublished} | {item.title} | {item.description} | [Link]({item.link}) | {videos_md} | {', '.join(item.categories)} | {', '.join(reverse_engineered_md)} |\n"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)

# Main Scraper Class
class WebScraper:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.request_manager = None
        self.parser = ContentParser()
        self.storage = DataStorage()
        self.scraped_data = []
        self._stop_flag = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handles signals for graceful shutdown"""
        logging.warning(f"{Colors.RED}Received signal {signum}. Shutting down...{Colors.RESET}")
        self._stop_flag = True

    async def validate_m3u8(self, url: str) -> Tuple[bool, dict]:
        """Validates m3u8 URL and returns validation info"""
        validation_result = {
            'valid': False,
            'type': None,
            'redirects': [],
            'content_type': None,
            'is_master': False,
            'streams': 0,
            'error': None
        }

        try:
            # Follow redirects and check final URL
            async with self.request_manager.session.get(
                url,
                headers=FETCH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True,
                raise_for_status=False
            ) as response:
                # Check if this is a master playlist
                content = await response.text()
                validation_result['content_type'] = response.headers.get('Content-Type', '')

                if '#EXTM3U' in content:
                    validation_result['valid'] = True
                    validation_result['type'] = 'master' if '#EXT-X-STREAM-INF' in content else 'media'

                    if validation_result['type'] == 'master':
                        # Count variant streams
                        validation_result['streams'] = content.count('#EXT-X-STREAM-INF')
                        validation_result['is_master'] = True

                    return (True, validation_result)

        except Exception as e:
            validation_result['error'] = str(e)

        return (False, validation_result)

    async def scrape_post(self, url: str) -> Optional[PostData]:
        """Scrapes post with enhanced video analysis"""
        if self._stop_flag:
            return None

        logging.info(f"{Colors.GREEN}Scraping post: {url}{Colors.RESET}")

        try:
            html = await self.request_manager.fetch(url)
            if not html:
                return None

            metadata = self.parser.extract_post_metadata(html, url)
            video_links = self.parser.extract_video_links(html, url)
            reverse_engineered_images = self.parser.extract_base64_images(html)

            # Validate and analyze each video link
            validated_videos = []
            m3u8_analysis = []

            for video_url in video_links:
                clean_url = URLUtils.clean_url(video_url)
                is_valid, validation_info = await self.validate_m3u8(clean_url)

                video_info = {
                    'url': clean_url,
                    'valid': is_valid,
                    'type': validation_info.get('type'),
                    'is_master': validation_info.get('is_master', False),
                    'streams': validation_info.get('streams', 0)
                }

                validated_videos.append(video_info)

                # Perform deep analysis for valid streams
                if is_valid:
                    analysis = await M3U8Analyzer.analyze_stream(
                        self.request_manager.session,
                        clean_url
                    )
                    m3u8_analysis.append(analysis)

            post = PostData(
                post_id=url.rstrip('/').split('/')[-1],
                title=metadata['title'],
                description=metadata['description'],
                datePublished=metadata['datePublished'],
                link=url,
                video_links=validated_videos,
                categories=metadata['categories'],
                reverse_engineered_images=reverse_engineered_images,
                m3u8_analysis=m3u8_analysis
            )

            logging.info(f"{Colors.GREEN}Successfully scraped post: {url}{Colors.RESET}")
            return post

        except Exception as e:
            logging.error(f"{Colors.RED}Error scraping post {url}: {e}{Colors.RESET}")
            return None

    async def scrape_archive_page(self, url: str) -> Set[str]:
        """Scrapes an Archives page for post links"""
        if self._stop_flag:
            return set()
        logging.info(f"{Colors.BLUE}Scraping Archives page: {url}{Colors.RESET}")
        try:
            html = await self.request_manager.fetch(url)
            if not html:
                return set()
            return self.parser.extract_post_links(html, url)
        except Exception as e:
            logging.error(f"{Colors.RED}Error scraping Archives page {url}: {e}{Colors.RESET}")
            return set()

    async def get_all_post_links(self, start_url: str) -> List[str]:
        """Retrieves all post links from Archives pages"""
        url = start_url
        post_links = set()
        page_count = 0
        while url and not self._stop_flag and (self.config.MAX_PAGES == 0 or page_count < self.config.MAX_PAGES):
            current_links = await self.scrape_archive_page(url)
            post_links.update(current_links)
            html = await self.request_manager.fetch(url)
            if html:
                url = self.parser.find_next_page(html, url)
            else:
                url = None
            page_count += 1
            if self.config.MAX_POSTS > 0 and len(post_links) >= self.config.MAX_POSTS:
                break
        return sorted(post_links)[:self.config.MAX_POSTS] if self.config.MAX_POSTS > 0 else sorted(post_links)

    async def run(self, start_url: str = "https://www.91cg1.com/archives.html"):
        """Main execution flow of the Scraper"""
        start_time = time.time()
        async with RequestManager(self.config) as manager:
            self.request_manager = manager
            try:
                logging.info(f"{Colors.YELLOW}Starting to collect post links...{Colors.RESET}")
                post_links = await self.get_all_post_links(start_url)
                if not post_links:
                    logging.warning(f"{Colors.RED}No post links found!{Colors.RESET}")
                    return
                logging.info(f"{Colors.GREEN}Found {len(post_links)} post links to scrape{Colors.RESET}")
                logging.info(f"{Colors.YELLOW}Starting to scrape posts...{Colors.RESET}")
                tasks = [self.scrape_post(link) for link in post_links]
                results = await asyncio.gather(*tasks)
                self.scraped_data = [post for post in results if post]
                if not self.scraped_data:
                    logging.warning(f"{Colors.RED}No scraped post data found!{Colors.RESET}")
                    return
                logging.info(f"{Colors.YELLOW}Saving data...{Colors.RESET}")
                if self.config.SAVE_JSON:
                    self.storage.save_json(self.scraped_data)
                    logging.info(f"{Colors.GREEN}JSON data saved{Colors.RESET}")
                if self.config.SAVE_CSV:
                    self.storage.save_csv(self.scraped_data)
                    logging.info(f"{Colors.GREEN}CSV data saved{Colors.RESET}")
                if self.config.SAVE_HTML:
                    self.storage.save_html(self.scraped_data)
                    logging.info(f"{Colors.GREEN}HTML report saved{Colors.RESET}")
                if self.config.SAVE_MD:
                    self.storage.save_markdown(self.scraped_data)
                    logging.info(f"{Colors.GREEN}Markdown report saved{Colors.RESET}")

                # Generate separate reports for HLS/m3u8 and Base64 images
                self.storage.save_hls_report(self.scraped_data)
                logging.info(f"{Colors.GREEN}HLS/m3u8 streams report saved{Colors.RESET}")
                self.storage.save_base64_report(self.scraped_data)
                logging.info(f"{Colors.GREEN}Base64 images report saved{Colors.RESET}")

                # Generate HLS playlist
                self.storage.save_hls_playlist(self.scraped_data)
                logging.info(f"{Colors.GREEN}HLS playlist created{Colors.RESET}")
                elapsed = time.time() - start_time

                # Display detection statistics
                total_hls_streams = sum(len(post.video_links) for post in self.scraped_data)
                total_reverse_engineered_images = sum(len(post.reverse_engineered_images) for post in self.scraped_data)
                posts_with_hls = sum(1 for post in self.scraped_data if post.video_links)
                posts_with_reverse_engineered_images = sum(1 for post in self.scraped_data if post.reverse_engineered_images)

                logging.info(f"{Colors.GREEN}Scraping completed! Processed {len(self.scraped_data)} posts in {elapsed:.2f} seconds{Colors.RESET}")
                logging.info(f"{Colors.CYAN}Detection Statistics:{Colors.RESET}")
                logging.info(f"{Colors.CYAN}- Posts with HLS/m3u8 streams: {posts_with_hls}/{len(self.scraped_data)} (Total {total_hls_streams} streams){Colors.RESET}")
                logging.info(f"{Colors.CYAN}- Posts with Reverse Engineered Images: {posts_with_reverse_engineered_images}/{len(self.scraped_data)} (Total {total_reverse_engineered_images} images){Colors.RESET}")
            except Exception as e:
                logging.error(f"{Colors.RED}A critical error occurred in the Scraper: {e}{Colors.RESET}")
                raise


if __name__ == "__main__":

    # Run scraper normally
    config = Config(
        MAX_PAGES=5,
        MAX_POSTS=0,
        MAX_CONCURRENT_REQUESTS=10,
        REQUEST_TIMEOUT=20,
        RETRY_ATTEMPTS=3,
        DELAY_BETWEEN_REQUESTS=1.0
    )
    scraper = WebScraper(config)
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logging.warning(f"{Colors.YELLOW}Scraping stopped by user{Colors.RESET}")
    except Exception as e:
        logging.error(f"{Colors.RED}A critical error occurred: {e}{Colors.RESET}")
        sys.exit(1)
