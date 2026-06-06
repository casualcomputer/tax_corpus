"""Fetch layer with a LOCAL-DROP fallback.

Because remote-execution environments often restrict outbound network (this one blocks
canada.ca), the realistic path is: download the source files once (or change the env's
network policy) and drop them in a directory; this reads from disk and records provenance.
When the network IS allowed, fetch_url() works the same and caches raw bytes.
"""
from __future__ import annotations
import re, json, hashlib, pathlib, datetime, urllib.request, urllib.error

def slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:120]

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def fetch_url(url: str, cache_dir="data/corpus/raw", drop_dir="data/corpus/source",
              ua="tax_corpus-bot/0.1 (+contact)", timeout=30):
    """Return (raw_bytes, meta). Resolution order: cache -> local drop -> network.
    meta = {source_url, retrieved_at, content_hash, origin}."""
    cache_dir, drop_dir = pathlib.Path(cache_dir), pathlib.Path(drop_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cf = cache_dir / (slug(url) + ".bin")
    if cf.exists():
        raw = cf.read_bytes()
        return raw, {"source_url": url, "retrieved_at": _now(), "origin": "cache",
                     "content_hash": hashlib.sha256(raw).hexdigest()[:16]}
    # local drop: match any file whose name contains the slug, else caller iterates drop dir
    if drop_dir.exists():
        for p in drop_dir.glob("*"):
            if slug(url)[:40] in slug(p.name):
                raw = p.read_bytes()
                return raw, {"source_url": url, "retrieved_at": _now(), "origin": f"drop:{p.name}",
                             "content_hash": hashlib.sha256(raw).hexdigest()[:16]}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        cf.write_bytes(raw)
        return raw, {"source_url": url, "retrieved_at": _now(), "origin": "network",
                     "content_hash": hashlib.sha256(raw).hexdigest()[:16]}
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise RuntimeError(
            f"Cannot fetch {url} ({e}). This environment blocks canada.ca. Either (a) change the "
            f"environment network policy to allow canada.ca, or (b) drop the file into {drop_dir}/, "
            f"or (c) run ingestion where the network is open and commit the parsed corpus.") from e

def iter_drop(drop_dir="data/corpus/source"):
    """Yield (path, raw_bytes) for every pre-downloaded source file."""
    for p in sorted(pathlib.Path(drop_dir).glob("**/*")):
        if p.is_file():
            yield p, p.read_bytes()
