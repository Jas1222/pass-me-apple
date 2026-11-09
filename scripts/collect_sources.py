#!/usr/bin/env python3
"""Fetch registered public Apple sources locally; never sends app artifacts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class Page(HTMLParser):
    """Retain article text, anchors and links; ignore navigation and scripts."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
    SKIP = {"nav", "aside", "footer", "script", "style", "svg", "template", "noscript"}
    BLOCK = {"p", "li", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "tr", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.all_text, self.main_text = [], [], []
        self.title, self.anchors, self.links = [], [], []
        self.has_main = False

    def emit(self, text):
        if not any(t in self.SKIP for t in self.stack):
            if "body" in self.stack:
                self.all_text.append(text)
            if "main" in self.stack:
                self.main_text.append(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in self.VOID:
            self.stack.append(tag)
        if tag == "main":
            self.has_main = True
        if tag in self.BLOCK:
            self.emit("\n")
        if tag in {"td", "th"}:
            self.emit(" | ")
        if "main" in self.stack and not any(t in self.SKIP for t in self.stack):
            anchor = attrs.get("id", "")
            if re.fullmatch(r"[1-5](?:\.\d+)+(?:\([a-z]+\)|[a-z])?", anchor):
                if anchor not in self.anchors:
                    self.anchors.append(anchor)
                    self.emit("\n[clause " + anchor + "]\n")
            if tag == "a" and attrs.get("href"):
                self.links.append(attrs["href"])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.emit("\n")
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            del self.stack[index:]

    def handle_data(self, text):
        if "title" in self.stack:
            self.title.append(text)
        self.emit(text)

    def text(self):
        parts = self.main_text if self.has_main else self.all_text
        return "\n".join(line for line in (" ".join(s.split()) for s in "".join(parts).splitlines()) if line)


def fetch(source, out):
    record = dict(source, retrieved_at_utc=utc_now(), status="error")
    stem = source["id"]
    raw_path = out / (stem + ".html")
    try:
        if urlparse(source["url"]).hostname != "developer.apple.com":
            raise ValueError("Registry URL must use developer.apple.com")
        result = subprocess.run([
            "curl", "--fail", "--silent", "--show-error", "--location",
            "--proto", "=https", "--proto-redir", "=https", "--max-redirs", "5",
            "--connect-timeout", "15", "--max-time", "45", "--max-filesize", "10000000",
            "--output", str(raw_path), "--write-out", "%{url_effective}", source["url"],
        ], capture_output=True, text=True, timeout=50)
        if result.returncode:
            raise ValueError(result.stderr.strip() or "curl failed")
        final_url = result.stdout.strip()
        if urlparse(final_url).hostname != "developer.apple.com":
            raise ValueError("Unexpected redirect host; verify this source manually")
        raw = raw_path.read_bytes()
        page = Page()
        page.feed(raw.decode("utf-8", errors="replace"))
        body = page.text()
        text_path = out / (stem + ".txt")
        text_path.write_text(body + "\n", encoding="utf-8")
        links = sorted({urljoin(final_url, link) for link in page.links})
        write_json(out / (stem + ".links.json"), links)
        record.update(final_url=final_url, page_title="".join(page.title).strip(),
                      sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                      text_characters=len(body), html_path=str(raw_path), text_path=str(text_path))
        if not page.has_main or len(body) < 400:
            raise ValueError("Missing or short main content; inspect with browser")
        if any(x in record["page_title"].lower() for x in ("page not found", "access denied", "sign in")):
            raise ValueError("Unexpected page title; inspect with browser")
        if stem == "guidelines":
            missing = [name for number, name in enumerate(("Safety", "Performance", "Business", "Design", "Legal"), 1)
                       if not re.search(rf"\b{number}\.\s*{name}\b", body)]
            if missing or len(page.anchors) < 50:
                raise ValueError("Incomplete guideline structure; manually verify chapters and clause extraction")
            write_json(out / "guideline-coverage-seed.json", [
                dict(clause=anchor, source_url=final_url.split("#")[0] + "#" + anchor,
                     applicability="unreviewed", status="Not verified", evidence=[], findings=[], notes="")
                for anchor in page.anchors
            ])
            record["clause_anchor_count"] = len(page.anchors)
        record["status"] = "retrieved"
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        record["error"] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New or empty local output directory")
    parser.add_argument("--include", action="append", default=[], help="Additional source ID; repeatable")
    parser.add_argument("--all", action="store_true", help="Fetch all registered sources")
    args = parser.parse_args()
    registry = json.loads((Path(__file__).resolve().parents[1] / "references/apple-sources.json").read_text())
    available = {s["id"] for s in registry["sources"]}
    unknown = set(args.include) - available
    if unknown:
        parser.error("Unknown source IDs: " + ", ".join(sorted(unknown)))
    out = args.out.expanduser().resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Output must be a new or empty directory; existing snapshots are never overwritten")
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    selected = [s for s in registry["sources"] if s["core"] or args.all or s["id"] in args.include]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda s: fetch(s, out), selected))
    errors = [r["id"] for r in records if r["status"] != "retrieved"]
    write_json(out / "manifest.json", dict(created_at_utc=utc_now(),
        scope="Registered public Apple pages; follow relevant links for additional requirements",
        all_selected_retrieved=not errors, sources=records))
    print(json.dumps(dict(output=str(out), retrieved=len(records)-len(errors), failed=errors,
                          coverage_seed_is_unreviewed=True), indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
