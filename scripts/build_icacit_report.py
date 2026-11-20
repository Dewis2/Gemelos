"""Create an editable academic report from the week-14 ICACIT evidence matrix."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "semana14" / "evaluacion_icacit.md"
OUTPUT = ROOT / "docs" / "semana14" / "Evaluacion_ICACIT_Gemelo_Digital_2026.docx"


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines:
        if (
            line.startswith("|")
            and "Atributo solicitado" not in line
            and "---" not in line
        ):
            fields = [
                part.strip().replace("`", "") for part in line.strip("|").split("|")
            ]
            if len(fields) == 4:
                records.append(fields)

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.3)
    sec.top_margin = Cm(2.1)
    sec.bottom_margin = Cm(2.1)
    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(7)
    for name, size in (("Title", 17), ("Heading 1", 12), ("Heading 2", 10.5)):
        style = doc.styles[name]
        style.font.name = "Aptos"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(11)
        style.paragraph_format.space_after = Pt(5)
        if name == "Title":
            ppr = style._element.pPr
            if ppr is not None:
                border = ppr.find(qn("w:pBdr"))
                if border is not None:
                    ppr.remove(border)

    doc.add_paragraph("Evaluación de evidencias de los atributos ICACIT", "Title")
    doc.add_paragraph(
        "Gemelo Digital Inteligente para la movilidad urbana de Huancayo · "
        "Taller de Proyectos 1 · NRC 30167 · 20 de noviembre de 2026"
    )
    doc.add_paragraph(
        "El informe PMV del 13 de noviembre, el código y las pruebas del 20 de noviembre "
        "aportan evidencia parcial para los siete atributos solicitados. Esta evaluación "
        "indica qué hallazgos deben corregirse y en qué sección del informe conviene "
        "presentarlos. No es un dictamen de acreditación institucional."
    )
    doc.add_paragraph("Evaluación por atributo", "Heading 1")
    for name, evidence, finding, placement in records:
        doc.add_paragraph(name, "Heading 2")
        p = doc.add_paragraph()
        p.add_run("Evidencia. ").bold = True
        p.add_run(evidence)
        p = doc.add_paragraph()
        p.add_run("Hallazgo y mejora. ").bold = True
        p.add_run(finding)
        p = doc.add_paragraph()
        p.add_run("Ubicación recomendada. ").bold = True
        p.add_run(placement)

    doc.add_paragraph("Dictamen", "Heading 1")
    doc.add_paragraph(
        "El proyecto cumple parcialmente como prototipo académico. Sus pruebas "
        "demuestran funcionamiento de software, pero no impacto social o ambiental "
        "medido. La ausencia de aforos locales fechados de 2026 y geometría oficial "
        "impide calibrar el corredor. Los escenarios OSM/SUMO deben conservar la "
        "etiqueta exploratoria hasta contar con una campaña de medición verificable."
    )
    doc.add_paragraph("Fuentes revisadas", "Heading 1")
    doc.add_paragraph(
        "S14. Evaluacion de evidencias de ICACIT.docx; "
        "docs/informes/Informe_PMV1_PMV2_PMV3_2026-11-13.docx; "
        "docs/evidencias/2026-11-18/README.md; "
        "docs/ingenieria_inversa.md; docs/07_auditoria_final.md."
    )
    footer = sec.footer.paragraphs[0]
    footer.add_run(
        "Taller de Proyectos 1 · NRC 30167 · Evaluación ICACIT"
    ).font.size = Pt(8)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
