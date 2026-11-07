#!/usr/bin/env python3
"""
HTML section extractor for paper-read skill (PRIMARY path for arXiv inputs).

Many arXiv papers ship a LaTeXML/ar5iv HTML rendering at
    https://arxiv.org/html/<id>
which is far cleaner to parse than the PDF: it has explicit <section> blocks,
<h1..h6 class="ltx_title_*"> headings with section numbers, a
class="ltx_abstract" block, and <figcaption class="ltx_caption"> captions.

This script consumes such an HTML document (local file OR URL) and emits the
SAME sections.json schema that pdf_to_sections.py produces, so all downstream
prompts (triage / deep-read / synth) work unchanged.

Usage:
    python3 html_to_sections.py <input.html | URL> --output sections.json
    python3 html_to_sections.py https://arxiv.org/html/1706.03762 -o sections.json

Exit codes:
    0  success, healthy sections.json written
    1  fetched/parsed but degraded (n_sections == 0)  -> caller should fall back
    2  input not found / fetch failed                  -> caller should fall back
    3  unexpected parse error                          -> caller should fall back

Dependencies: Python stdlib only (urllib, html.parser, html, re). No pip needed.
"""

import argparse
import html as _html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 (paper-read skill; +https://arxiv.org)"

# ar5iv / LaTeXML class markers
CLS_TITLE_DOC = "ltx_title_document"
CLS_ABSTRACT = "ltx_abstract"
CLS_CAPTION = "ltx_caption"
RE_TITLE_SECTION = re.compile(r"ltx_title_(section|subsection|subsubsection|paragraph)\b")
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
DROP_TAGS = {"script", "style", "nav", "header", "footer"}
# void elements never get a matching close tag -> don't push them on the stack
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}

RE_NUM_PREFIX = re.compile(r"^\s*((?:\d+|[A-Z])(?:\.\d+)*)[\.\s]+(.*)$")
RE_CAP_PREFIX = re.compile(r"^(Figure|Fig\.?|Table|Tab\.?)\s*(\d+)\b[.:]?\s*(.*)$", re.IGNORECASE)
RE_WS = re.compile(r"\s+")


def fetch(src: str) -> str:
    """Read HTML from a URL or local path. Raises on failure."""
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")
    return Path(src).read_text(encoding="utf-8", errors="replace")


class Ar5ivParser(HTMLParser):
    """
    Element-stack parser. Each open (non-void) element pushes a frame recording
    whether it opened a scope we care about (title-doc / abstract / caption /
    heading). Text is routed to whichever scopes are currently active. Closing a
    tag pops the matching frame and finalizes any scope it owned.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.abstract_parts = []
        self.captions = []           # {type, number, caption}
        self.headings = []           # {level, number, title, body: []}
        self._stack = []             # list of frames (dicts)
        self._drop_depth = 0

    @staticmethod
    def _class_of(attrs):
        for k, v in attrs:
            if k == "class":
                return v or ""
        return ""

    def _active(self, key):
        """True if any frame on the stack owns scope `key`."""
        return any(f.get(key) for f in self._stack)

    def handle_starttag(self, tag, attrs):
        if tag in DROP_TAGS:
            self._drop_depth += 1
            # still push so the matching close decrements correctly
            if tag not in VOID_TAGS:
                self._stack.append({"tag": tag, "drop": True})
            return
        if tag in VOID_TAGS:
            return

        cls = self._class_of(attrs)
        frame = {"tag": tag}
        if CLS_TITLE_DOC in cls and not self.title_parts:
            frame["title_doc"] = True
        if CLS_ABSTRACT in cls:
            frame["abstract"] = True
        if CLS_CAPTION in cls:
            frame["caption"] = True
            frame["caption_buf"] = []
        m = RE_TITLE_SECTION.search(cls)
        if m and tag in HEADING_TAGS:
            level = {"section": 1, "subsection": 2,
                     "subsubsection": 3, "paragraph": 4}[m.group(1)]
            frame["heading"] = True
            frame["heading_level"] = level
            frame["heading_buf"] = []
        self._stack.append(frame)

    def handle_endtag(self, tag):
        # pop until we find the matching tag (tolerate minor mismatches)
        idx = None
        for j in range(len(self._stack) - 1, -1, -1):
            if self._stack[j]["tag"] == tag:
                idx = j
                break
        if idx is None:
            return
        # finalize frames from top down to idx
        for f in reversed(self._stack[idx:]):
            if f.get("drop"):
                self._drop_depth = max(0, self._drop_depth - 1)
            if f.get("heading"):
                raw = RE_WS.sub(" ", "".join(f["heading_buf"])).strip()
                num, title = "", raw
                mm = RE_NUM_PREFIX.match(raw)
                if mm:
                    num, title = mm.group(1), mm.group(2).strip()
                self.headings.append({
                    "level": f["heading_level"],
                    "number": num,
                    "title": title or raw,
                    "body": [],
                })
            if f.get("caption"):
                text = RE_WS.sub(" ", "".join(f["caption_buf"])).strip()
                cm = RE_CAP_PREFIX.match(text)
                if cm:
                    self.captions.append({
                        "type": cm.group(1),
                        "number": int(cm.group(2)),
                        "caption": cm.group(3).strip(),
                    })
        del self._stack[idx:]

    def handle_data(self, data):
        if self._drop_depth:
            return
        # route text to the innermost active heading/caption buffer, plus
        # title/abstract scopes, plus the current section body.
        if self._active("title_doc"):
            self.title_parts.append(data)
        if self._active("abstract"):
            self.abstract_parts.append(data)
        # caption buffer: nearest caption frame
        cap_frame = next((f for f in reversed(self._stack) if f.get("caption")), None)
        head_frame = next((f for f in reversed(self._stack) if f.get("heading")), None)
        if cap_frame is not None:
            cap_frame["caption_buf"].append(data)
        if head_frame is not None:
            head_frame["heading_buf"].append(data)
        elif self.headings and not self._active("abstract") and not self._active("title_doc"):
            # accumulate body text under the most recent finalized heading
            self.headings[-1]["body"].append(data)


def _norm_cap_type(t):
    t = t.lower()
    if t.startswith("fig"):
        return "figure"
    if t.startswith("tab"):
        return "table"
    return t


def build_payload(parser: Ar5ivParser, source: str):
    title = RE_WS.sub(" ", "".join(parser.title_parts)).strip()
    abstract = RE_WS.sub(" ", "".join(parser.abstract_parts)).strip()
    # abstract sometimes starts with the word "Abstract"
    abstract = re.sub(r"^Abstract[:.\s]*", "", abstract).strip()

    sections = []
    for i, h in enumerate(parser.headings):
        body = RE_WS.sub(" ", "".join(h["body"])).strip()
        sections.append({
            "idx": i,
            "page": None,
            "level": h["level"],
            "number": h["number"],
            "title": _html.unescape(h["title"]),
            "text": _html.unescape(body),
            "char_len": len(body),
        })

    captions = [{
        "page": None,
        "type": _norm_cap_type(c["type"]),
        "number": c["number"],
        "caption": _html.unescape(c["caption"]),
    } for c in parser.captions]

    return {
        "source_html": source,
        "backend": "arxiv-html",
        "title": _html.unescape(title),
        "abstract": _html.unescape(abstract),
        "n_pages": None,
        "n_sections": len(sections),
        "sections": sections,
        "captions": captions,
    }


def main():
    ap = argparse.ArgumentParser(description="Extract sections from arXiv/LaTeXML HTML for paper-read.")
    ap.add_argument("src", help="HTML URL (e.g. https://arxiv.org/html/<id>) or local .html path")
    ap.add_argument("--output", "-o", type=Path, default=Path("sections.json"))
    args = ap.parse_args()

    try:
        html_text = fetch(args.src)
    except Exception as e:
        print(f"[paper-read] HTML 获取失败: {e}", file=sys.stderr)
        sys.exit(2)

    if len(html_text) < 2000:
        print("[paper-read] ⚠ HTML 内容过短, 疑似无 HTML 版本。", file=sys.stderr)
        sys.exit(1)

    try:
        parser = Ar5ivParser()
        parser.feed(html_text)
        payload = build_payload(parser, args.src)
    except Exception as e:
        print(f"[paper-read] HTML 解析失败: {e}", file=sys.stderr)
        sys.exit(3)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if payload["n_sections"] == 0:
        print("[paper-read] ⚠ HTML 未识别出任何章节 (可能不是 ar5iv/LaTeXML 渲染)。", file=sys.stderr)
        sys.exit(1)

    print(f"[paper-read] ✓ sections.json 已写入 (HTML): {args.output}")
    print(f"  - backend: arxiv-html")
    print(f"  - title: {payload['title'][:80]}")
    print(f"  - sections detected: {payload['n_sections']}")
    print(f"  - captions detected: {len(payload['captions'])}")


if __name__ == "__main__":
    main()
