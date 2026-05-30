"""Collect background/context information from text, URL, or file uploads."""
import base64
import html.parser
import io
import ipaddress
import os
import re
import socket
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAX_BACKGROUND_CHARS = 8000
MAX_URL_BYTES = 2 * 1024 * 1024  # 2MB
URL_TIMEOUT = 10.0

_PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_private_host(hostname: str) -> bool:
    """Check whether hostname resolves to a private/internal IP address."""
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            addr = ipaddress.ip_address(socket.getaddrinfo(hostname, None)[0][4][0])
        except (socket.gaierror, IndexError):
            return True  # block unresolvable hosts
    return any(addr in net for net in _PRIVATE_NETS)


class _TextExtractor(html.parser.HTMLParser):
    """Extract visible text from HTML, stripping scripts and styles."""

    def __init__(self):
        super().__init__()
        self._text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        if tag in ("p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._text.append("\n")

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self._text.append(t)

    def get_text(self) -> str:
        return "\n".join(self._text)


def collect_background(
    background_text: str = "",
    background_url: str = "",
    background_file: tuple | None = None,
) -> str | None:
    """Collect background context from one or more input sources.

    Args:
        background_text: Raw background text.
        background_url: URL to fetch and extract text from.
        background_file: (filename, bytes) tuple of uploaded file.

    Returns:
        Combined background text, or None if all inputs are empty.

    Raises:
        ValueError: For unsupported formats or fetch failures.
    """
    parts: list[str] = []

    if background_text.strip():
        parts.append(f"[背景文字]\n{background_text.strip()}")

    if background_url.strip():
        parts.append(f"[链接内容]\n{_fetch_url(background_url.strip())}")

    if background_file:
        filename, content = background_file
        parts.append(f"[文件内容]\n{_extract_file_content(filename, content)}")

    if not parts:
        return None

    combined = "\n\n---\n\n".join(parts)
    if len(combined) > MAX_BACKGROUND_CHARS:
        combined = combined[:MAX_BACKGROUND_CHARS] + "\n\n[背景内容过长，已截断]"
    return combined


def _fetch_url(url: str) -> str:
    """Fetch a URL and extract readable text content."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("链接仅支持 http/https 协议。")
    if _is_private_host(parsed.hostname or ""):
        raise ValueError("不支持访问内网地址。")

    import httpx

    try:
        with httpx.Client(
            timeout=URL_TIMEOUT,
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": "EssayGrader/1.0"},
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.TimeoutException:
        raise ValueError(f"链接访问超时（{URL_TIMEOUT} 秒）：{url}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"链接返回错误 {e.response.status_code}：{url}")
    except Exception as e:
        raise ValueError(f"链接访问失败：{e}")

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError("链接返回的不是网页内容，无法提取文字。")

    body = resp.text[:MAX_URL_BYTES]
    if "text/html" in content_type:
        parser = _TextExtractor()
        parser.feed(body)
        text = parser.get_text()
    else:
        text = body

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text.strip():
        raise ValueError("链接中未能提取到文字内容。")
    return text


def _extract_file_content(filename: str, content: bytes) -> str:
    """Extract text from uploaded file. Supports txt/docx/pdf (doc_parser)
    and png/jpg (DeepSeek Vision)."""
    lower = filename.lower()

    if lower.endswith((".txt", ".docx", ".pdf")):
        from doc_parser import extract_text
        return extract_text(filename, content)

    if lower.endswith((".png", ".jpg", ".jpeg")):
        return _ocr_image(filename, content)

    raise ValueError(f"不支持的文件格式：{filename}。请上传 .txt、.docx、.pdf、.png 或 .jpg 文件。")


def _ocr_image(filename: str, content: bytes) -> str:
    """Extract text from an image using DeepSeek Vision API."""
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(content))
    except Exception:
        raise ValueError("无法读取图片文件，请确认文件未损坏。")

    # Resize large images to keep base64 payload manageable
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    img_format = img.format or "PNG"
    if img_format.upper() in ("JPG", "JPEG"):
        img.save(buf, format="JPEG", quality=85)
    else:
        img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise RuntimeError("未设置 DEEPSEEK_API_KEY，无法进行图片识别。")

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请提取并整理以下图片中的全部文字内容。保留原文格式和段落结构，只输出提取的文字，不要添加额外说明。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/{img_format.lower()};base64,{img_b64}"},
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )
        text = response.choices[0].message.content.strip()
    except Exception as e:
        raise ValueError(f"图片文字识别失败：{e}")

    if not text:
        raise ValueError("未能从图片中识别到文字内容。")
    return text
