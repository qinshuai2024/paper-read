#!/usr/bin/env python3
"""
PDF section splitter for paper-read skill.

Extracts title, abstract, sections (with hierarchy), and figure/table
captions from a PDF. Author metadata is not extracted. Outputs a single JSON file
that downstream prompts (triage / global-view / deep-read) consume.

Usage:
    python3 pdf_to_sections.py <input.pdf> --output sections.json

Dependencies:
    - PyMuPDF (fitz): primary backend
    - Fallback: pdftotext (poppler) if PyMuPDF unavailable

If neither is installed, prints friendly install instructions and exits 1.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


# -------- Dependency self-check ----------------------------------------------

def check_pymupdf():
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def check_pdftotext():
    return shutil.which("pdftotext") is not None


def print_install_help():
    print("[paper-read] PDF 解析依赖未安装。请任选其一：", file=sys.stderr)
    print("", file=sys.stderr)
    print("  ① 推荐 — PyMuPDF (功能最完整):", file=sys.stderr)
    print("      pip install pymupdf", file=sys.stderr)
    print("      # 或: pip3 install pymupdf", file=sys.stderr)
    print("      # conda: conda install -c conda-forge pymupdf", file=sys.stderr)
    print("", file=sys.stderr)
    print("  ② 兜底 — pdftotext (Poppler):", file=sys.stderr)
    print("      macOS:  brew install poppler", file=sys.stderr)
    print("      Linux:  apt install poppler-utils", file=sys.stderr)
    print("", file=sys.stderr)
    print("装好后重新运行本命令即可。", file=sys.stderr)


# -------- PyMuPDF backend -----------------------------------------------------

def extract_with_pymupdf(pdf_path: Path):
    import fitz

    doc = fitz.open(str(pdf_path))
    full_text_blocks = []  # list of dict {page, font_size, text, bbox}
    captions = []

    for page_idx, page in enumerate(doc):
        # blocks: each block is (x0, y0, x1, y1, text, block_no, block_type)
        # use "dict" mode to access font size
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                line_text = line_text.strip()
                if not line_text:
                    continue
                # representative font size for the line (max span)
                sizes = [span.get("size", 0) for span in line.get("spans", [])]
                font_size = max(sizes) if sizes else 0
                # is this line bold?
                bold = any(("bold" in (span.get("font", "").lower())) for span in line.get("spans", []))
                full_text_blocks.append({
                    "page": page_idx + 1,
                    "size": round(font_size, 2),
                    "bold": bold,
                    "text": line_text,
                })

    doc.close()
    return full_text_blocks


# -------- pdftotext fallback --------------------------------------------------

def extract_with_pdftotext(pdf_path: Path):
    """Returns list of {page, size: None, bold: None, text} blocks."""
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    blocks = []
    page = 1
    for raw_line in out.stdout.splitlines():
        if "\x0c" in raw_line:
            page += 1
            raw_line = raw_line.replace("\x0c", "")
        line = raw_line.strip()
        if line:
            blocks.append({"page": page, "size": None, "bold": None, "text": line})
    return blocks


# -------- Structure parsing ---------------------------------------------------

SECTION_PATTERNS = [
    # "1 Introduction", "1. Introduction", "1.1 Background"
    re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][A-Za-z][^\n]{0,80})$"),
    # "I Introduction" (Roman)
    re.compile(r"^(I{1,3}V?|IV|V|VI{0,3}|IX|X)\.\s+([A-Z][^\n]{0,80})$"),
]

KNOWN_HEADERS = {
    "abstract", "introduction", "related work", "background", "preliminaries",
    "method", "methods", "methodology", "approach", "model", "framework",
    "experiments", "experimental setup", "evaluation", "results",
    "discussion", "analysis", "ablation", "ablation study",
    "conclusion", "conclusions", "limitations", "future work",
    "references", "acknowledgments", "acknowledgements", "appendix",
}

CAPTION_PATTERN = re.compile(r"^(Figure|Fig\.?|Table|Tab\.?)\s*(\d+)[.:]\s*(.+)$", re.IGNORECASE)


def detect_sections(blocks):
    """
    Heuristics:
      1. Numeric pattern "1 Introduction" / "1.1 Foo" — strongest signal
      2. Known header keywords as standalone line — fallback
      3. If PyMuPDF data has font_size, prefer larger-than-body lines

    Returns: list of {idx, page, level, number, title, line_index}
    """
    sections = []

    # estimate body font size if available
    sizes = [b["size"] for b in blocks if b.get("size")]
    body_size = None
    if sizes:
        # mode-ish: pick the most frequent rounded size
        from collections import Counter
        body_size = Counter(round(s) for s in sizes).most_common(1)[0][0]

    for i, b in enumerate(blocks):
        text = b["text"].strip()
        if not text or len(text) > 120:
            continue

        matched = None
        for pat in SECTION_PATTERNS:
            m = pat.match(text)
            if m:
                number = m.group(1)
                title = m.group(2).strip()
                level = number.count(".") + 1 if number[0].isdigit() else 1
                matched = (number, title, level)
                break

        if not matched:
            # known-header fallback (only if line is short and visually a heading)
            tl = text.lower().strip(":")
            if tl in KNOWN_HEADERS:
                # require either bold OR larger font OR pdftotext fallback
                visual = True
                if b.get("size") and body_size:
                    visual = b["size"] >= body_size + 0.5 or b.get("bold")
                if visual:
                    matched = ("", text, 1)

        if matched:
            number, title, level = matched
            sections.append({
                "idx": len(sections),
                "page": b["page"],
                "level": level,
                "number": number,
                "title": title,
                "line_index": i,
            })

    return sections


def slice_section_text(blocks, sections):
    """For each section, gather text lines until the next section starts."""
    result = []
    for i, sec in enumerate(sections):
        start = sec["line_index"] + 1
        end = sections[i + 1]["line_index"] if i + 1 < len(sections) else len(blocks)
        body = " ".join(b["text"] for b in blocks[start:end]).strip()
        # Compress whitespace
        body = re.sub(r"\s+", " ", body)
        result.append({
            "idx": sec["idx"],
            "page": sec["page"],
            "level": sec["level"],
            "number": sec["number"],
            "title": sec["title"],
            "text": body,
            "char_len": len(body),
        })
    return result


def extract_captions(blocks):
    caps = []
    for b in blocks:
        m = CAPTION_PATTERN.match(b["text"].strip())
        if m:
            caps.append({
                "page": b["page"],
                "type": m.group(1).rstrip(".").lower(),  # "figure" or "table"
                "number": int(m.group(2)),
                "caption": m.group(3).strip(),
            })
    return caps


def extract_title_authors_abstract(blocks):
    """Very heuristic: title is the largest text on page 1; abstract follows."""
    # arXiv's large rotated margin stamp can exceed the title font size.
    # Exclude it from both font-based and plain-text title candidates.
    page1 = [b for b in blocks if b["page"] == 1
             and not re.match(r"^arxiv\s*:", b["text"].strip(), re.IGNORECASE)]
    title = ""
    if page1:
        # If we have font sizes, pick the largest line cluster at the top
        sized = [b for b in page1 if b.get("size")]
        if sized:
            max_size = max(b["size"] for b in sized)
            title_lines = [b["text"] for b in sized
                           if abs(b["size"] - max_size) < 0.5 and len(b["text"]) > 5][:3]
            title = " ".join(title_lines).strip()
        else:
            # Fallback: first non-trivial line
            for b in page1:
                if len(b["text"]) > 10:
                    title = b["text"]
                    break

    # Abstract: find "Abstract" keyword, take following ~30 lines or until next section
    abstract = ""
    for i, b in enumerate(blocks):
        if b["text"].strip().lower().rstrip(":") in {"abstract", "abstract."}:
            # take next ~40 lines until next likely section
            buf = []
            for nb in blocks[i + 1:i + 50]:
                if re.match(r"^(\d+\.?\s+[A-Z])", nb["text"]):
                    break
                if nb["text"].strip().lower() in KNOWN_HEADERS - {"abstract"}:
                    break
                buf.append(nb["text"])
            abstract = " ".join(buf).strip()
            abstract = re.sub(r"\s+", " ", abstract)
            break

    return title, abstract


# -------- Main ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract sections from PDF for paper-read skill.")
    parser.add_argument("pdf", type=Path, help="Input PDF path")
    parser.add_argument("--output", "-o", type=Path, default=Path("sections.json"),
                        help="Output JSON file (default: sections.json)")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"[paper-read] PDF 不存在: {args.pdf}", file=sys.stderr)
        sys.exit(2)

    has_pymupdf = check_pymupdf()
    has_pdftotext = check_pdftotext()

    if not has_pymupdf and not has_pdftotext:
        print_install_help()
        sys.exit(1)

    try:
        if has_pymupdf:
            backend = "pymupdf"
            blocks = extract_with_pymupdf(args.pdf)
        else:
            backend = "pdftotext"
            print("[paper-read] PyMuPDF 未安装, 退回 pdftotext。", file=sys.stderr)
            blocks = extract_with_pdftotext(args.pdf)
    except Exception as e:
        print(f"[paper-read] PDF 解析失败: {e}", file=sys.stderr)
        sys.exit(3)

    sections = detect_sections(blocks)
    if not sections:
        print("[paper-read] ⚠ 未识别出任何章节标题。可能 PDF 是扫描版/排版异常。", file=sys.stderr)
        print("  建议: 手动粘贴章节文本，或先 OCR 后再试。", file=sys.stderr)

    section_data = slice_section_text(blocks, sections)
    captions = extract_captions(blocks)
    title, abstract = extract_title_authors_abstract(blocks)

    payload = {
        "source_pdf": str(args.pdf.resolve()),
        "backend": backend,
        "title": title,
        "abstract": abstract,
        "n_pages": max((b["page"] for b in blocks), default=0),
        "n_sections": len(section_data),
        "sections": section_data,
        "captions": captions,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[paper-read] ✓ sections.json 已写入: {args.output}")
    print(f"  - backend: {backend}")
    print(f"  - title: {title[:80]}")
    print(f"  - sections detected: {len(section_data)}")
    print(f"  - captions detected: {len(captions)}")


if __name__ == "__main__":
    main()
