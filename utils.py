import re, secrets, string
from urllib.parse import urlparse

BASE62 = string.digits + string.ascii_letters

def random_code(n: int = 7) -> str:
    return "".join(secrets.choice(BASE62) for _ in range(n))

# basic URL sanity check
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

def normalize_url(url: str) -> str:
    url = url.strip()
    if not _URL_RE.match(url):
        url = "http://" + url  # allow users to omit scheme
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("Invalid URL")
    return url
