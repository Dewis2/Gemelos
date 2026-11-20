"""Build the editable English paper and the A1 scientific poster from repo evidence."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "semana14"
SOURCE = ROOT / "docs" / "articulo" / "urban-mobility-digital-twin.md"


def add_inline(paragraph, value: str) -> None:
    pieces = re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", value)
    for piece in pieces:
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            paragraph.add_run(piece[2:-2]).bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            paragraph.add_run(piece[1:-1])
        elif piece.startswith("*") and piece.endswith("*"):
            paragraph.add_run(piece[1:-1]).italic = True
        else:
            paragraph.add_run(piece.replace("  ", " "))


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def build_docx() -> Path:
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.2)
    section.left_margin = section.right_margin = Cm(2.4)
    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(6)
    for name, size in (("Title", 17), ("Heading 1", 12), ("Heading 2", 10.5)):
        st = doc.styles[name]
        st.font.name = "Aptos"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_before = Pt(10)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.keep_with_next = True
        if name == "Title":
            ppr = st._element.pPr
            if ppr is not None:
                border = ppr.find(qn("w:pBdr"))
                if border is not None:
                    ppr.remove(border)

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, value in enumerate(row):
                    cell = table.cell(ri, ci)
                    cell.text = value.replace("`", "")
                    if ri == 0:
                        shade(cell, "E8EFED")
                        for run in cell.paragraphs[0].runs:
                            run.bold = True
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.space_after = Pt(1)
                        for run in paragraph.runs:
                            run.font.size = Pt(7.5)
            doc.add_paragraph()
            continue
        if line.startswith("# "):
            p = doc.add_paragraph(style="Title")
            add_inline(p, line[2:])
        elif line.startswith("## "):
            p = doc.add_paragraph(style="Heading 1")
            add_inline(p, line[3:])
        elif line.startswith("### "):
            p = doc.add_paragraph(style="Heading 2")
            add_inline(p, line[4:])
        else:
            p = doc.add_paragraph()
            if line.startswith("**Keywords:**"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_inline(p, line)
        i += 1

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Gemelo Digital Huancayo  |  2026").font.size = Pt(8)
    path = OUT / "Articulo_Gemelo_Digital_Huancayo_2026.docx"
    doc.save(path)
    return path


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")


def paragraph(
    c: canvas.Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    size: float = 24,
    color: str = "#203431",
    leading: float | None = None,
    bold: bool = False,
    align: int = TA_LEFT,
) -> float:
    style = ParagraphStyle(
        "p",
        fontName="Arial-Bold" if bold else "Arial",
        fontSize=size,
        leading=leading or size * 1.33,
        textColor=colors.HexColor(color),
        alignment=align,
        spaceAfter=0,
    )
    p = Paragraph(text, style)
    _, h = p.wrap(width, 9999)
    p.drawOn(c, x, top - h)
    return top - h


def panel(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    fill: str = "#F7FAF8",
) -> float:
    c.setFillColor(colors.HexColor(fill))
    c.roundRect(x, y, w, h, 18, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#168A69"))
    c.roundRect(x + 26, y + h - 70, 8, 42, 4, stroke=0, fill=1)
    paragraph(c, title, x + 52, y + h - 26, w - 80, 34, "#123E34", bold=True)
    return y + h - 95


def build_poster() -> Path:
    register_fonts()
    w, h = 2384, 1684  # A1 landscape in points, approximately 841 x 594 mm
    path = OUT / "Poster_Cientifico_Gemelo_Digital_Huancayo_A1.pdf"
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle("Gemelo digital de movilidad urbana de Huancayo")
    c.setFillColor(colors.HexColor("#EFF5F1"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#07392D"))
    c.rect(0, h - 260, w, 260, fill=1, stroke=0)
    paragraph(
        c,
        "Gemelo digital exploratorio de movilidad urbana en Huancayo",
        76,
        h - 52,
        w - 150,
        71,
        "#FFFFFF",
        leading=82,
        bold=True,
    )
    paragraph(
        c,
        "Carlos L. Escobar · Brayan J. Ochoa · Christian J. Zevallos · Fabricio R. Chicmana · Marcelo A. Morris",
        78,
        h - 158,
        w - 160,
        28,
        "#D5EDE2",
    )
    paragraph(
        c,
        "Universidad Continental  |  Taller de Proyectos 1  |  NRC 30167  |  2026",
        78,
        h - 210,
        w - 160,
        25,
        "#B6D6C8",
    )

    gap, left, col = 24, 66, 735
    xs = [left + i * (col + gap) for i in range(3)]
    top = h - 290
    bottom = 84

    # Column 1: purpose, method, software boundary.
    y = top - 405
    t = panel(c, xs[0], y, col, 405, "Problema y objetivo")
    t = paragraph(
        c,
        "La información disponible mezcla aforos municipales antiguos, un experimento nacional de aprendizaje automático y escenarios locales sintéticos. Cada fuente tiene una cobertura distinta.",
        xs[0] + 32,
        t,
        col - 64,
        25,
    )
    t -= 22
    paragraph(
        c,
        "<b>Objetivo:</b> presentar y reproducir escenarios de movilidad sin convertir datos históricos o sintéticos en afirmaciones sobre el tráfico actual de la Av. Ferrocarril.",
        xs[0] + 32,
        t,
        col - 64,
        25,
    )

    y2 = y - gap - 545
    t = panel(c, xs[0], y2, col, 545, "Método reproducible")
    for n, body in [
        (
            "1",
            "Nueve registros municipales de 2013; total documentado: 11 892 vehículos.",
        ),
        (
            "2",
            "Recorte OpenStreetMap del entorno de Av. Ferrocarril; 1451 aristas para automóviles.",
        ),
        (
            "3",
            "SUMO 1.28.0; semilla 30167; salidas sintéticas cada 8, 4 y 2 segundos durante 900 s.",
        ),
        (
            "4",
            "Reporte con SHA-256 de mapa, red y rutas; métricas calculadas sobre viajes finalizados.",
        ),
    ]:
        t = paragraph(c, f"<b>{n}.</b> {body}", xs[0] + 32, t, col - 64, 24) - 17
    paragraph(
        c,
        "Los intervalos son parámetros del experimento, no mediciones locales.",
        xs[0] + 32,
        t - 2,
        col - 64,
        23,
        "#9A4E18",
        bold=True,
    )

    y3 = bottom
    t = panel(c, xs[0], y3, col, y2 - gap - y3, "Arquitectura")
    paragraph(
        c,
        "React y Leaflet  →  FastAPI  →  casos de uso y puertos  →  PostgreSQL/PostGIS y SUMO",
        xs[0] + 32,
        t,
        col - 64,
        25,
        bold=True,
    )
    paragraph(
        c,
        "El comando SUMO requiere sesión de editor. El adaptador de simulación se sustituye detrás de un puerto sin cambiar la ruta HTTP.",
        xs[0] + 32,
        t - 94,
        col - 64,
        22,
    )

    # Column 2: chart and measured software results.
    y = top - 710
    t = panel(c, xs[1], y, col, 710, "Resultados de simulación")
    paragraph(
        c,
        "Duración media en verde y espera media en ocre (segundos)",
        xs[1] + 32,
        t,
        col - 64,
        23,
    )
    chart_left = xs[1] + 180
    for idx, (label, duration, waiting, trips) in enumerate(
        [
            ("Baja", 168.61, 34.27, "113/113"),
            ("Normal", 182.52, 42.89, "225/225"),
            ("Alta", 192.16, 46.67, "450/450"),
        ]
    ):
        yy = t - 105 - idx * 145
        paragraph(c, label, xs[1] + 32, yy + 10, 132, 25, bold=True)
        c.setFillColor(colors.HexColor("#19A77B"))
        c.roundRect(chart_left, yy - 22, duration * 2.35, 36, 8, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#F0AD45"))
        c.roundRect(chart_left, yy - 68, waiting * 2.35, 28, 8, fill=1, stroke=0)
        paragraph(
            c,
            f"{duration:.2f} s / {waiting:.2f} s  ·  {trips} viajes",
            chart_left,
            yy - 79,
            col - 215,
            19,
        )
    paragraph(
        c,
        "En esta configuración, una demanda sintética mayor coincide con más duración y espera. La comparación es interna al experimento.",
        xs[1] + 32,
        y + 121,
        col - 64,
        23,
    )

    y2 = bottom
    t = panel(c, xs[1], y2, col, y - gap - y2, "Verificación del software")
    t = paragraph(
        c,
        "<b>83</b> pruebas backend aprobadas; <b>12</b> pruebas PostgreSQL omitidas en este equipo. El frontend pasó TypeScript y compilación.",
        xs[1] + 32,
        t,
        col - 64,
        24,
    )
    t -= 20
    t = paragraph(
        c,
        "En staging, la interfaz mostró una ejecución autenticada de demanda normal: <b>225 de 225 viajes</b> completados.",
        xs[1] + 32,
        t,
        col - 64,
        24,
    )
    t -= 20
    paragraph(
        c,
        "Modelo nacional aparte: random forest, prueba temporal, MAE 7083,46. Esta métrica no mide el corredor local.",
        xs[1] + 32,
        t,
        col - 64,
        22,
    )

    # Column 3: image, limitations, conclusion and references.
    y = top - 650
    t = panel(c, xs[2], y, col, 650, "Evidencia de ejecución")
    img_path = (
        ROOT
        / "docs"
        / "evidencias"
        / "2026-11-18"
        / "render-sumo-normal-live-results.png"
    )
    img = ImageReader(str(img_path))
    iw, ih = img.getSize()
    target_w = col - 64
    target_h = target_w * ih / iw
    c.drawImage(img, xs[2] + 32, t - target_h - 4, width=target_w, height=target_h)
    paragraph(
        c,
        "Interfaz de staging: mapa OSM, métricas SUMO y comparación de demandas. Captura del 18/11/2026.",
        xs[2] + 32,
        t - target_h - 32,
        col - 64,
        19,
    )

    y2 = y - gap - 390
    t = panel(c, xs[2], y2, col, 390, "Límites y conclusión")
    t = paragraph(
        c,
        "<b>No se dispone de aforos locales fechados de 2026 ni de geometría oficial utilizable.</b> OpenStreetMap es una fuente colaborativa; las rutas se generaron de forma sintética.",
        xs[2] + 32,
        t,
        col - 64,
        24,
    )
    t -= 23
    paragraph(
        c,
        "El sistema demuestra consulta, trazabilidad y ejecución reproducible de escenarios. Sus tiempos y velocidades no son predicciones ni calibración del tránsito real.",
        xs[2] + 32,
        t,
        col - 64,
        24,
    )

    t = panel(c, xs[2], bottom, col, y2 - gap - bottom, "Fuentes")
    paragraph(
        c,
        "[1] Rundel y De Amicis, Front. Virtual Real. 2023, doi:10.3389/frvir.2023.1048753<br/>[2] Wibisana et al., ISPRS Annals 2024, doi:10.5194/isprs-annals-X-4-2024-411-2024<br/>[3] Repositorio Gemelos, reporte OSM/SUMO y evidencias de 2026. github.com/Dewis2/Gemelos",
        xs[2] + 32,
        t,
        col - 64,
        18,
    )

    c.setFont("Arial", 17)
    c.setFillColor(colors.HexColor("#45635A"))
    c.drawString(
        70,
        37,
        "Datos OSM © OpenStreetMap contributors (ODbL)  ·  Estudio exploratorio sin calibración vial",
    )
    c.save()
    return path


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(build_docx())
    print(build_poster())
