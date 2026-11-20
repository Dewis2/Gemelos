"""Place the English manuscript into ACM's official single-column Word submission template."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from tempfile import gettempdir

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "articulo" / "urban-mobility-digital-twin.md"
OUTPUT = ROOT / "docs" / "semana14" / "Articulo_Gemelo_Digital_Huancayo_ACM.docx"
TEMPLATE = Path(gettempdir()) / "acm_submission_template.docx"
TEMPLATE_URL = (
    "https://authors.acm.org/binaries/content/assets/publications/taps/"
    "acm_submission_template.docx"
)


def fill_inline(paragraph, text: str) -> None:
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            paragraph.add_run(part[1:-1])
        elif part.startswith("*") and part.endswith("*"):
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def main() -> None:
    if not TEMPLATE.exists():
        urllib.request.urlretrieve(TEMPLATE_URL, TEMPLATE)
    doc = Document(TEMPLATE)
    body = doc._element.body
    for element in list(body):
        if element.tag != qn("w:sectPr"):
            body.remove(element)
    doc.core_properties.title = (
        "An Exploratory Urban Mobility Digital Twin for Huancayo"
    )
    doc.core_properties.author = "Gemelo Digital Huancayo team"
    doc.core_properties.subject = "Exploratory OSM SUMO urban mobility prototype"

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    after_heading = False
    in_references = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                fields = [f.strip() for f in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", f) for f in fields):
                    rows.append(fields)
                i += 1
            doc.add_paragraph(
                "Table 1. Results of the synthetic SUMO scenarios", "TableCaption"
            )
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, value in enumerate(row):
                    cell = table.cell(ri, ci)
                    cell.text = value
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(8)
                            if ri == 0:
                                run.bold = True
            continue
        if line.startswith("# "):
            fill_inline(doc.add_paragraph(style="Title_document"), line[2:])
            i += 1
            authors = lines[i].strip()
            fill_inline(doc.add_paragraph(style="Authors"), authors)
            i += 1
            if i < len(lines) and not lines[i].strip():
                i += 1
            fill_inline(doc.add_paragraph(style="Affiliation"), lines[i].strip())
        elif line == "## Abstract":
            pass
        elif line.startswith("**Keywords:**"):
            doc.add_paragraph(
                "CCS Concepts: • Information systems → Geographic information systems; "
                "• Computing methodologies → Simulation and modeling.",
                "CCSDescription",
            )
            fill_inline(doc.add_paragraph(style="KeyWords"), line.replace("**", ""))
        elif line == "## References":
            doc.add_paragraph("References", "ReferenceHead")
            in_references = True
        elif line.startswith("## "):
            heading_text = re.sub(r"^\d+\s+", "", line[3:])
            fill_inline(doc.add_paragraph(style="Head1"), heading_text)
            after_heading = True
        elif line.startswith("### "):
            heading_text = re.sub(r"^\d+(?:\.\d+)*\s+", "", line[4:])
            fill_inline(doc.add_paragraph(style="Head2"), heading_text)
            after_heading = True
        else:
            style = (
                "Abstract"
                if "## Abstract" in lines[:i]
                and not any(x.startswith("## 1 Introduction") for x in lines[:i])
                else (
                    "Bib_entry"
                    if in_references
                    else "PostHeadPara" if after_heading else "Para"
                )
            )
            if in_references:
                line = re.sub(r"^\[\d+\]\s+", "", line)
            fill_inline(doc.add_paragraph(style=style), line)
            after_heading = False
        i += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
