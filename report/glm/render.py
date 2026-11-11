"""Render the bilingual report sources with embedded fonts and predictable pagination."""

import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#172B4D")
TEAL = colors.HexColor("#197F75")
GRAY = colors.HexColor("#526174")


def inline(text):
    text = escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font color="#245B79">\1</font>', text)
    return re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#197F75">\1</link>',
        text,
    )


def render(source, destination, language):
    chinese = language == "zh"
    regular = "C:/Windows/Fonts/msyh.ttc" if chinese else "C:/Windows/Fonts/arial.ttf"
    bold = "C:/Windows/Fonts/msyhbd.ttc" if chinese else "C:/Windows/Fonts/arialbd.ttf"
    font, font_bold = "ReportRegular", "ReportBold"
    pdfmetrics.registerFont(TTFont(font, regular))
    pdfmetrics.registerFont(TTFont(font_bold, bold))
    pdfmetrics.registerFontFamily(
        font, normal=font, bold=font_bold, italic=font, boldItalic=font_bold
    )
    styles = {
        "body": ParagraphStyle(
            "body",
            fontName=font,
            fontSize=10,
            leading=15,
            textColor=NAVY,
            spaceAfter=7,
            wordWrap="CJK" if chinese else None,
        ),
        "title": ParagraphStyle(
            "title",
            fontName=font_bold,
            fontSize=22,
            leading=29,
            textColor=NAVY,
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=font_bold,
            fontSize=15,
            leading=21,
            textColor=NAVY,
            spaceBefore=5,
            spaceAfter=9,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName=font_bold,
            fontSize=11,
            leading=16,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=font,
            fontSize=8.5,
            leading=12,
            textColor=GRAY,
            spaceAfter=8,
        ),
        "cell": ParagraphStyle(
            "cell",
            fontName=font,
            fontSize=8.2,
            leading=11.5,
            textColor=NAVY,
            wordWrap="CJK" if chinese else None,
        ),
        "headcell": ParagraphStyle(
            "headcell",
            fontName=font_bold,
            fontSize=8.2,
            leading=11.5,
            textColor=NAVY,
            wordWrap="CJK" if chinese else None,
        ),
    }
    width = A4[0] - 92
    story = []
    lines = source.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- page -->":
            story.append(PageBreak())
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", x) for x in cells):
                    rows.append(cells)
                i += 1
            count = len(rows[0])
            widths = [width / count] * count
            if count >= 5:
                widths = [width * 0.23] + [width * 0.77 / (count - 1)] * (count - 1)
            data = [
                [
                    Paragraph(inline(c), styles["headcell" if n == 0 else "cell"])
                    for c in row
                ]
                for n, row in enumerate(rows)
            ]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("LINEABOVE", (0, 0), (-1, 0), 0.8, NAVY),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, NAVY),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        (
                            "LINEBELOW",
                            (0, -1),
                            (-1, -1),
                            0.4,
                            colors.HexColor("#CED8E1"),
                        ),
                    ]
                )
            )
            story.extend([table, Spacer(1, 9)])
            continue
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
            if not match:
                raise ValueError("Invalid image syntax: " + line)
            path = (source.parent / match[2]).resolve()
            img = Image(str(path))
            scale = width / img.imageWidth
            img.drawWidth, img.drawHeight = width, img.imageHeight * scale
            story.extend([img, Paragraph(inline(match[1]), styles["caption"])])
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["h3"]))
        else:
            paragraph = [line]
            while (
                i + 1 < len(lines)
                and lines[i + 1].strip()
                and not lines[i + 1].startswith(("#", "|", "![", "<!--"))
            ):
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph(inline(" ".join(paragraph)), styles["body"]))
        i += 1

    def frame(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#D5DFE8"))
        canvas.line(46, A4[1] - 34, A4[0] - 46, A4[1] - 34)
        canvas.setFillColor(GRAY)
        canvas.setFont(font, 7.5)
        canvas.drawString(46, A4[1] - 26, "FTEC5660  /  SWE-Pruner  /  GLM-4.6")
        canvas.drawString(46, 25, "Xia Feifan  ·  1155204948")
        canvas.drawRightString(A4[0] - 46, 25, str(doc.page))

    document = SimpleDocTemplate(
        str(destination),
        pagesize=A4,
        rightMargin=46,
        leftMargin=46,
        topMargin=48,
        bottomMargin=43,
        title="SWE-Pruner Reproduction and Exact Observation Recovery",
        author="Xia Feifan",
        pageCompression=1,
    )
    document.build(story, onFirstPage=frame, onLaterPages=frame)
    pages = len(PdfReader(destination).pages)
    if pages > 10:
        raise RuntimeError(f"Report exceeds the assignment limit: {pages} pages")
    print(f"{destination}: {pages} pages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--language", choices=["zh", "en"], required=True)
    options = parser.parse_args()
    render(options.source, options.destination, options.language)
