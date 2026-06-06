"""tax_corpus ingestion + citation/eval engine (stdlib-only).

Structure-aware HTML -> paragraph-anchored chunks (schemas/chunk.schema.json),
with provision extraction and currency inference. No third-party deps so it runs
anywhere; canada.ca-specific CSS selectors get finalized once we have real HTML.
"""
from __future__ import annotations
import re, hashlib
from html.parser import HTMLParser

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = HEADING_TAGS | {"p", "li", "td", "th", "dd", "dt"}
SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside"}

class _Blocks(HTMLParser):
    def __init__(self):
        super().__init__(); self.blocks = []; self._cur = None; self._buf = []; self._skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS: self._skip += 1
        elif tag in BLOCK_TAGS and self._skip == 0: self._flush(); self._cur = tag
    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip > 0: self._skip -= 1
        elif tag == self._cur: self._flush()
    def handle_data(self, data):
        if self._cur and self._skip == 0: self._buf.append(data)
    def _flush(self):
        if self._cur:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text: self.blocks.append((self._cur, text))
        self._cur = None; self._buf = []

def html_to_blocks(html: str):
    """[(tag, text)] preserving heading hierarchy + block order."""
    p = _Blocks(); p.feed(html); p._flush(); return p.blocks

# --- provision extraction (citation anchors) ---
_PROV = [
    re.compile(r"\b(?:sub)?section\s+(\d{1,3}(?:\.\d+)?)", re.I),
    re.compile(r"\b(?:paragraph|clause|subparagraph)\s+(\d{1,3}(?:\.\d+)?(?:\([0-9a-zA-Z.]+\))+)", re.I),
    re.compile(r"\b(\d{1,3}(?:\.\d+)?\((?:[0-9]+|[a-z])\)(?:\([0-9a-z.]+\))*)"),   # bare 20(1)(a)
    re.compile(r"\bETA\s+(\d{1,3}(?:\.\d+)?(?:\([0-9a-z.]+\))*|Sch(?:edule)?\.?\s+[IVXLC]+)", re.I),
    re.compile(r"\b(IT-\d{1,4}[A-Z]?\d?)\b"),                                      # Interpretation Bulletin
    re.compile(r"\b(S\d-F\d+-C\d+)\b"),                                            # Income Tax Folio
]
def extract_provisions(text: str):
    out = []
    for rx in _PROV:
        for m in rx.findall(text):
            v = m if isinstance(m, str) else m[0]
            if v and v not in out: out.append(v)
    # drop a bare section number subsumed by a fuller reference (e.g. "20" vs "20(1)(c)")
    return [v for v in out if not any(w != v and w.startswith(v + "(") for w in out)]

def infer_status(title: str, text: str):
    t = f"{title} {text}".lower()
    m = re.search(r"(?:superseded|replaced) by ([^.;\n]+)", t)
    if m: return "superseded", m.group(1).strip()[:80]
    if "archived" in t or "this bulletin is cancelled" in t: return "archived", None
    return "unknown", None

_PARA = re.compile(r"^\s*(\d{1,3})\.\s+")   # leading "12. " => paragraph_id

def chunk_blocks(blocks, *, doc_id, source_type, source_url, retrieved_at,
                 title=None, language="en", default_authority="unknown"):
    """Section/paragraph-aware chunks conforming to schemas/chunk.schema.json.
    Status is doc-level (an archived/superseded banner applies to the whole bulletin)."""
    if title is None:
        for tag, text in blocks:
            if tag in ("h1", "h2"): title = text; break
    status, superseded_by = infer_status(title or "", " ".join(t for _, t in blocks))
    section, chunks = [], []
    for tag, text in blocks:
        if tag in HEADING_TAGS:
            lvl = int(tag[1]); section = section[: lvl - 1] + [text]; continue
        m = _PARA.match(text); pid = m.group(1) if m else None
        cid = f"{doc_id}#{pid}" if pid else f"{doc_id}#b{len(chunks)}"
        chunks.append({
            "chunk_id": cid, "source_type": source_type, "doc_id": doc_id,
            "title": title, "section_path": list(section), "paragraph_id": pid,
            "text": text, "issue_date": None, "last_updated": None,
            "status": status, "superseded_by": superseded_by,
            "ita_sections": extract_provisions(text), "authority_tier": default_authority,
            "language": language, "source_url": source_url, "retrieved_at": retrieved_at,
            "content_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
        })
    return chunks
