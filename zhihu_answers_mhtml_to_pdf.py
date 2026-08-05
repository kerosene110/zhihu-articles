#!/usr/bin/env python3
import argparse
import base64
import copy
import html
import mimetypes
import os
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Dict, Iterable, Optional

import requests
from lxml import html as lxml_html
from lxml import etree

from zhihu_column_to_pdf import html_to_pdf

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def image_token(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = re.search(r"(v2-[0-9a-f]+)", value)
    if match:
        return match.group(1)
    return None


def log(message: str) -> None:
    print(message, flush=True)


def safe_filename(title: str) -> str:
    base = re.sub(r"[^\w\-\s]", "", title, flags=re.UNICODE).strip()
    base = re.sub(r"\s+", " ", base)
    if not base:
        base = "zhihu-answer"
    return f"{base}.pdf"


def iter_mhtml_files(path: str) -> Iterable[Path]:
    base = Path(path)
    if base.is_file():
        yield base
        return
    if not base.is_dir():
        raise RuntimeError(f"Input path is neither a file nor a directory: {path}")

    for file_path in sorted(base.iterdir()):
        if file_path.suffix.lower() in {".mhtml", ".mht"}:
            yield file_path


def parse_mhtml(mhtml_path: Path) -> tuple[str, str, Dict[str, str], Optional[str]]:
    msg = BytesParser(policy=policy.default).parsebytes(mhtml_path.read_bytes())
    html_text: Optional[str] = None
    asset_map: Dict[str, str] = {}

    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "multipart/related":
            continue

        if content_type == "text/html" and html_text is None:
            raw = part.get_payload(decode=True)
            if raw is None:
                continue
            html_text = raw.decode("utf-8", errors="replace")
            continue

        raw = part.get_payload(decode=True)
        if raw is None:
            continue
        cid = part.get("Content-ID")
        location = part.get("Content-Location")
        mime = content_type or mimetypes.guess_type(location or "")[0] or "application/octet-stream"
        data_uri = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
        if cid:
            asset_map[f"cid:{cid.strip('<>')}"] = data_uri
        if location:
            asset_map[location] = data_uri
            token = image_token(location)
            if token:
                asset_map[token] = data_uri

    if html_text is None:
        raise RuntimeError(f"No HTML part found in {mhtml_path}")

    source_url = msg.get("Snapshot-Content-Location")
    return html_text, source_url or str(mhtml_path), asset_map, msg.get("Subject")


def first_node(tree: lxml_html.HtmlElement, xpaths: list[str]):
    for xpath in xpaths:
        nodes = tree.xpath(xpath)
        if nodes:
            return nodes[0]
    return None


def rewrite_embedded_assets(node: lxml_html.HtmlElement, asset_map: Dict[str, str]) -> None:
    for element in node.xpath(".//*[@src or @href]"):
        for attr in ("src", "href"):
            value = element.get(attr)
            if not value:
                continue
            replacement = asset_map.get(value)
            if replacement:
                element.set(attr, replacement)


def normalize_image_nodes(node: lxml_html.HtmlElement, asset_map: Dict[str, str]) -> None:
    for img in node.xpath(".//img"):
        src = img.get("src") or ""
        candidates = [
            img.get("data-original-token"),
            img.get("data-original"),
            img.get("data-actualsrc"),
            img.get("data-src"),
        ]
        token_candidates = [token for token in (image_token(src), *(image_token(x) for x in candidates)) if token]
        if src.startswith("data:image/svg+xml"):
            replaced = False
            for token in token_candidates:
                replacement = asset_map.get(token)
                if replacement:
                    img.set("src", replacement)
                    replaced = True
                    break
            if replaced:
                continue
            for candidate in candidates:
                if not candidate:
                    continue
                img.set("src", asset_map.get(candidate, candidate))
                break
        elif not src:
            replaced = False
            for token in token_candidates:
                replacement = asset_map.get(token)
                if replacement:
                    img.set("src", replacement)
                    replaced = True
                    break
            if replaced:
                continue
            for candidate in candidates:
                if not candidate:
                    continue
                img.set("src", asset_map.get(candidate, candidate))
                break


def fetch_as_data_uri(session: requests.Session, url: str, referer: str) -> Optional[str]:
    try:
        resp = session.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Referer": referer,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            timeout=30,
        )
        resp.raise_for_status()
    except Exception:
        return None

    mime = resp.headers.get("Content-Type", "").split(";")[0].strip() or mimetypes.guess_type(url)[0]
    if not mime:
        mime = "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(resp.content).decode('ascii')}"


def inline_remote_images(node: lxml_html.HtmlElement, source_url: str) -> None:
    session = requests.Session()
    cache: Dict[str, Optional[str]] = {}
    for img in node.xpath(".//img"):
        src = img.get("src") or ""
        if not src.startswith(("http://", "https://")):
            continue
        if src not in cache:
            cache[src] = fetch_as_data_uri(session, src, source_url)
        data_uri = cache[src]
        if data_uri:
            img.set("src", data_uri)


def render_tex_to_html(tex: str) -> str:
    tex = tex.strip()

    def parse_expr(index: int, stop_char: Optional[str] = None) -> tuple[list[str], int]:
        parts: list[str] = []
        while index < len(tex):
            ch = tex[index]
            if stop_char and ch == stop_char:
                break
            if ch.isspace():
                parts.append(" ")
                index += 1
                continue
            if tex.startswith("\\frac", index):
                numerator, index = parse_required_group(index + 5)
                denominator, index = parse_required_group(index)
                parts.append(
                    '<span class="tex-frac">'
                    f'<span class="tex-num">{"".join(numerator)}</span>'
                    f'<span class="tex-den">{"".join(denominator)}</span>'
                    "</span>"
                )
                continue
            if ch in "^_":
                if not parts:
                    index += 1
                    continue
                script_parts, index = parse_script(index + 1)
                script_html = "".join(script_parts)
                base = parts.pop()
                if ch == "^":
                    parts.append(f'<span class="tex-scripted">{base}<sup>{script_html}</sup></span>')
                else:
                    parts.append(f'<span class="tex-scripted">{base}<sub>{script_html}</sub></span>')
                continue
            atom, index = parse_atom(index)
            parts.append(atom)
        return parts, index

    def parse_required_group(index: int) -> tuple[list[str], int]:
        while index < len(tex) and tex[index].isspace():
            index += 1
        if index >= len(tex):
            return [], index
        if tex[index] == "{":
            items, new_index = parse_expr(index + 1, "}")
            return items, new_index + 1
        atom, new_index = parse_atom(index)
        return [atom], new_index

    def parse_script(index: int) -> tuple[list[str], int]:
        return parse_required_group(index)

    def parse_atom(index: int) -> tuple[str, int]:
        if tex[index] == "{":
            items, new_index = parse_expr(index + 1, "}")
            return "".join(items), new_index + 1
        if tex[index] == "\\":
            match = re.match(r"\\[A-Za-z]+", tex[index:])
            if match:
                command = match.group(0)
                index += len(command)
                replacements = {
                    r"\cdot": "&middot;",
                    r"\times": "&times;",
                    r"\leq": "&le;",
                    r"\geq": "&ge;",
                    r"\neq": "&ne;",
                    r"\approx": "&asymp;",
                    r"\pm": "&plusmn;",
                    r"\infty": "&infin;",
                    r"\sum": "&sum;",
                }
                return replacements.get(command, html.escape(command[1:])), index
            return html.escape(tex[index]), index + 1
        return html.escape(tex[index]), index + 1

    parts, _ = parse_expr(0)
    return "".join(parts)


def normalize_math_nodes(node: lxml_html.HtmlElement, math_defs: list[etree._Element]) -> None:
    for math_node in node.xpath(".//span[contains(@class, 'ztext-math')]"):
        svg_nodes = math_node.xpath(".//span[contains(@class, 'MathJax_SVG')]/svg")
        for child in list(math_node):
            math_node.remove(child)
        math_node.text = None

        if svg_nodes:
            original_svg = svg_nodes[0]
            svg_xml = etree.fromstring(
                lxml_html.tostring(original_svg, encoding="utf-8", method="xml")
            )
            if "viewBox" not in svg_xml.attrib and "viewbox" in svg_xml.attrib:
                svg_xml.attrib["viewBox"] = svg_xml.attrib.pop("viewbox")
            if not svg_xml.xpath("./svg:defs", namespaces={"svg": "http://www.w3.org/2000/svg"}):
                defs_wrapper = etree.Element("{http://www.w3.org/2000/svg}defs")
                for defs in math_defs:
                    for child in defs:
                        defs_wrapper.append(copy.deepcopy(child))
                if len(defs_wrapper):
                    svg_xml.insert(0, defs_wrapper)

            svg_data = etree.tostring(svg_xml, encoding="utf-8", xml_declaration=False)
            img = etree.Element("img")
            img.attrib["src"] = f"data:image/svg+xml;base64,{base64.b64encode(svg_data).decode('ascii')}"
            img.attrib["alt"] = math_node.get("data-tex", "")
            img.attrib["style"] = "display:inline-block; vertical-align:middle;"
            math_node.append(img)
            continue

        tex_html = render_tex_to_html(math_node.get("data-tex", ""))
        fallback = etree.Element("span")
        fallback.attrib["class"] = "tex-math-fallback"
        fragment_nodes = lxml_html.fragments_fromstring(tex_html)
        for fragment in fragment_nodes:
            if isinstance(fragment, str):
                if fallback.text:
                    fallback.text += fragment
                else:
                    fallback.text = fragment
            else:
                fallback.append(fragment)
        math_node.append(fallback)


def extract_answer_html(
    html_text: str, asset_map: Dict[str, str], subject: Optional[str], source_url: str
) -> tuple[str, str, str]:
    tree = lxml_html.fromstring(html_text)

    title_node = first_node(
        tree,
        [
            "//h1[contains(@class, 'QuestionHeader-title')]",
            "//meta[@property='og:title']/@content",
            "//title",
        ],
    )
    if isinstance(title_node, str):
        title = title_node
    elif title_node is not None:
        title = title_node.text_content().strip()
    elif subject:
        title = subject
    else:
        title = "Zhihu Answer"
    title = re.sub(r"\s*-\s*知乎\s*$", "", title).strip()

    answer_node = first_node(
        tree,
        [
            "//div[contains(@class, 'AnswerItem')]//div[contains(@class, 'RichContent-inner')]",
            "//div[contains(@class, 'RichContent-inner')]",
            "//div[contains(@class, 'RichText') and contains(@class, 'ztext')]",
        ],
    )
    if answer_node is None:
        raise RuntimeError("Could not locate Zhihu answer content in saved page.")

    rewrite_embedded_assets(answer_node, asset_map)
    normalize_image_nodes(answer_node, asset_map)
    inline_remote_images(answer_node, source_url)
    math_defs = tree.xpath("//defs[@id='MathJax_SVG_glyphs']")
    normalize_math_nodes(answer_node, math_defs)
    content_html = lxml_html.tostring(answer_node, encoding="unicode", method="html")
    return title, content_html, ""


def build_html(title: str, content_html: str, source_url: str, math_defs_html: str) -> str:
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: "Noto Serif CJK SC", "Songti SC", "SimSun", serif; margin: 2.5cm; line-height: 1.7; }}
      h1 {{ font-size: 24px; margin-bottom: 0.2em; }}
      .source {{ color: #666; font-size: 12px; margin-bottom: 1.2em; }}
      img {{ max-width: 100%; height: auto; }}
      pre, code {{ white-space: pre-wrap; }}
      blockquote {{ color: #444; border-left: 3px solid #ddd; margin-left: 0; padding-left: 0.8em; }}
      .tex-math-fallback {{ display: inline-block; font-family: "Times New Roman", "Noto Serif", serif; }}
      .tex-scripted sup {{ font-size: 0.75em; vertical-align: super; }}
      .tex-scripted sub {{ font-size: 0.75em; vertical-align: sub; }}
      .tex-frac {{ display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; margin: 0 0.12em; }}
      .tex-num {{ border-bottom: 1px solid currentColor; padding: 0 0.2em 0.05em; }}
      .tex-den {{ padding: 0.05em 0.2em 0; }}
    </style>
  </head>
  <body>
    {math_defs_html}
    <h1>{html.escape(title)}</h1>
    <div class="source">{html.escape(source_url)}</div>
    {content_html}
  </body>
</html>
"""


def convert_file(mhtml_path: Path, output_dir: Path, overwrite: bool) -> bool:
    html_text, source_url, asset_map, subject = parse_mhtml(mhtml_path)
    title, content_html, math_defs_html = extract_answer_html(
        html_text, asset_map, subject, source_url
    )
    output_path = output_dir / safe_filename(title)

    if output_path.exists() and not overwrite:
        log(f"Skipping existing PDF: {output_path}")
        return False

    full_html = build_html(title, content_html, source_url, math_defs_html)
    ok = html_to_pdf(full_html, str(output_path), source_url)
    if ok:
        log(f"Saved PDF: {output_path}")
        return True

    fallback_path = output_path.with_suffix(".html")
    fallback_path.write_text(full_html, encoding="utf-8")
    log(f"PDF backend unavailable or failed; saved HTML instead: {fallback_path}")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert saved Zhihu answer MHTML files to PDFs."
    )
    parser.add_argument("input", help="Input .mhtml file or directory containing .mhtml files")
    parser.add_argument("--out", help="Output directory (default: same directory as the input)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PDFs")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.out) if args.out else (input_path if input_path.is_dir() else input_path.parent)
    output_dir.mkdir(parents=True, exist_ok=True)

    converted = 0
    for mhtml_path in iter_mhtml_files(args.input):
        try:
            if convert_file(mhtml_path, output_dir, args.overwrite):
                converted += 1
        except Exception as exc:
            log(f"Failed to convert {mhtml_path}: {exc}")

    log(f"Converted {converted} files to PDFs in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
