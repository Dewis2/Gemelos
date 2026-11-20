"""Produce the private four-page congress change report with attendance evidence."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import gettempdir

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = (
    Path(gettempdir()) / "codex-clipboard-82a17f52-fa7c-4575-990d-d9e19e0baca7.png"
)
DEFAULT_OUTPUT = Path.home() / "Downloads" / "CHG-001-2026-Congreso-Gemelo-Digital.pdf"


def make_report(evidence: Path, output: Path) -> None:
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Arial-Bold",
            fontSize=18,
            leading=23,
            textColor=colors.HexColor("#173D34"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportHeading",
            fontName="Arial-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#173D34"),
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            fontName="Arial",
            fontSize=9.8,
            leading=14.2,
            textColor=colors.HexColor("#17231F"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSmall",
            fontName="Arial",
            fontSize=8.3,
            leading=11.5,
            textColor=colors.HexColor("#354A43"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportCenter",
            parent=styles["ReportBody"],
            alignment=TA_CENTER,
        )
    )
    body, small = styles["ReportBody"], styles["ReportSmall"]
    P = lambda text, style=body: Paragraph(text, style)

    def table(rows: list[list[str]], widths: list[float]) -> Table:
        data = [[P(str(c), small) for c in row] for row in rows]
        t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0EB")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#62897A")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return t

    def heading(text: str) -> Paragraph:
        return P(text, styles["ReportHeading"])

    story: list = []
    # Page 1.
    story += [
        P("Solicitud de cambio CHG-001-2026", styles["ReportTitle"]),
        P(
            "<b>Proyecto:</b> Gemelo Digital Inteligente para la movilidad urbana de Huancayo<br/>"
            "<b>Asignatura:</b> Taller de Proyectos 1 · NRC 30167<br/>"
            "<b>Fecha:</b> 20 de noviembre de 2026<br/>"
            "<b>Equipo:</b> Carlos Leonardo Escobar Cárdenas, Brayan José Ochoa Segovia, "
            "Christian John Zevallos Meza, Fabricio Renzo Chicmana Víncula y Marcelo Alen Morris Córdova"
        ),
        heading("Resumen ejecutivo"),
        P(
            "Se registra una mejora técnica del PMV3: la ejecución exploratoria de SUMO pasa por un puerto "
            "de salida y casos de uso, y el frontend comunica el resultado con separación visual y una "
            "región de estado accesible. La red procede de OpenStreetMap y las rutas son sintéticas. "
            "El cambio aumenta la verificabilidad y mantenibilidad del software sin convertirlo en "
            "un modelo calibrado del tránsito real."
        ),
        heading("Ponencia asociada y alcance de la evidencia"),
        P(
            "La consigna del curso incluye la ponencia <b>“Digital Twin Simulation”</b> de Walter Silva "
            "como referencia para C5 y C6. Se toma su tema como marco de transferencia tecnológica. "
            "La captura disponible acredita la presencia en una sesión virtual del VIII Congreso "
            "Internacional de Ingeniería y Arquitectura, día 2; la imagen no permite identificar "
            "qué ponencia concreta se escuchó. La síntesis técnica de este informe se apoya en el "
            "proyecto implementado y la consigna, sin atribuir afirmaciones al expositor."
        ),
        heading("Matriz de alineamiento con las seis competencias"),
        table(
            [
                ["Competencia", "Aplicación en el cambio"],
                [
                    "C1 Análisis del problema",
                    "Separar la necesidad de simulación reproducible de la necesidad futura de calibración con aforos locales.",
                ],
                [
                    "C2 Conocimientos de ingeniería",
                    "Justificar la semilla 30167, tres tasas de salida y métricas de duración, espera y velocidad.",
                ],
                [
                    "C3 Ingeniero y sociedad",
                    "Advertir que OSM y viajes sintéticos no fundamentan decisiones públicas ni impactos ambientales reales.",
                ],
                [
                    "C4 Gestión del proyecto",
                    "Registrar alcance, esfuerzo, riesgo, historias HU-19/HU-20 y control de cambios.",
                ],
                [
                    "C5 Herramientas modernas",
                    "Evaluar OSM, SUMO, FastAPI, React y sus límites técnicos.",
                ],
                [
                    "C6 Prueba de concepto",
                    "Comprobar la integración mediante puerto, adaptador y prueba con fake.",
                ],
            ],
            [135, 365],
        ),
        PageBreak(),
    ]
    # Page 2.
    story += [
        heading("Trazabilidad técnica de las competencias"),
        P(
            "<b>C1.</b> El problema observado no es la ausencia de una gráfica: es la mezcla potencial "
            "de datos de diferente lugar y fecha. El sistema dispone de nueve registros municipales de 2013, "
            "pero no de aforos fechados de 2026 ni geometría oficial. Por eso la aceptación del cambio "
            "se mide con reproducibilidad y claridad de etiquetas, no con precisión del tráfico."
        ),
        P(
            "<b>C2.</b> La red derivada de OSM contiene 1451 aristas aptas para automóviles; 59 llevan "
            "el nombre Av. Ferrocarril. SUMO 1.28 usa semilla 30167 y una ventana de salida de 900 s. "
            "Las demandas baja, normal y alta tienen intervalos sintéticos de 8, 4 y 2 s; completan "
            "113/113, 225/225 y 450/450 viajes. Duración y espera se agregan solo sobre viajes finalizados."
        ),
        P(
            "<b>C3.</b> La interfaz y la documentación distinguen los aforos históricos, el experimento "
            "nacional ML y la simulación local. Se conserva atribución OSM/ODbL. Los resultados no "
            "constituyen una evaluación de seguridad vial, emisiones, privacidad ni accesibilidad "
            "integral; esos asuntos requieren datos y pruebas específicos."
        ),
        P(
            "<b>C4.</b> La solicitud afecta PMV3 y añade dos historias con criterios verificables. "
            "El esfuerzo de 8–12 horas-persona es una estimación de planificación, no tiempo "
            "registrado. Se mantiene el contrato HTTP y no se migra la base de datos."
        ),
        P(
            "<b>C5.</b> OSM permite montar una red inicial pero es cartografía colaborativa; SUMO "
            "produce escenarios deterministas condicionados por rutas y parámetros. Render habilita "
            "una demostración publicada, aunque puede retrasar la primera respuesta tras inactividad. "
            "El control de versiones y los SHA-256 permiten revisar las entradas."
        ),
        P(
            "<b>C6.</b> El flujo es ruta REST → caso de uso → puerto OUT → adaptador SUMO. "
            "La prueba unitaria usa un adaptador falso y evita ejecutar el simulador. Las pruebas "
            "de rutas y autenticación conservan el contrato de ejecución."
        ),
        heading("Indicadores de aceptación"),
        table(
            [
                ["Indicador", "Resultado comprobado"],
                [
                    "Pruebas backend",
                    "83 aprobadas; 12 dependientes de PostgreSQL omitidas en este equipo.",
                ],
                [
                    "Frontend",
                    "TypeScript, regla de arquitectura y compilación de producción aprobadas.",
                ],
                [
                    "Staging SUMO normal",
                    "Interfaz publicada mostró 225/225 viajes y resultado recién calculado.",
                ],
                [
                    "Integridad del experimento",
                    "Hashes de mapa, red y rutas en el reporte JSON versionado.",
                ],
            ],
            [175, 325],
        ),
        PageBreak(),
    ]
    # Page 3.
    story += [
        heading("Ficha del cambio"),
        table(
            [
                ["Campo", "Registro"],
                ["Código", "CHG-001-2026"],
                [
                    "Ponencia de origen temático",
                    "Digital Twin Simulation · Walter Silva · programa del VIII Congreso.",
                ],
                [
                    "Línea base",
                    "Rama main del repositorio Gemelos, commit f9b1f98, antes de la revisión.",
                ],
                [
                    "Descripción",
                    "Interponer un puerto y casos de uso entre la ruta FastAPI y el ejecutor SUMO; mejorar el anuncio visual del resultado.",
                ],
                ["Hito", "PMV3. PMV1 y PMV2 conservan su alcance y esquema de datos."],
                [
                    "Impacto técnico",
                    "Puerto OUT ExploratorySimulationPort, casos GetExploratoryReport y RunExploratorySimulation, composición del contenedor y panel React.",
                ],
            ],
            [155, 345],
        ),
        heading("Impacto en el Product Backlog"),
        P(
            "<b>HU-19. Ejecución desacoplada.</b> Como mantenedor, quiero llamar a SUMO a través de un "
            "puerto de aplicación para sustituir el motor sin alterar la API. <b>Dado</b> un nivel "
            "admitido y un ejecutor disponible, <b>cuando</b> se llama al caso de uso, "
            "<b>entonces</b> se entrega el resultado del adaptador. La prueba con fake valida la "
            "orquestación. La validación de nivel y errores HTTP se conserva en el endpoint/adaptador."
        ),
        P(
            "<b>HU-20. Resultado legible.</b> Como editor, quiero ver claramente cuándo acabó SUMO. "
            "<b>Dado</b> un cálculo exitoso, <b>cuando</b> termina la petición, <b>entonces</b> la "
            "interfaz muestra “Resultado recién calculado por SUMO” separado del botón y con "
            "anuncio `role=status`. La compilación frontend verifica integridad de tipos."
        ),
        heading("Riesgos y plan de verificación"),
        table(
            [
                ["Riesgo", "Mitigación / evidencia"],
                [
                    "Regresión del endpoint protegido",
                    "Ejecutar pruebas de ruta y autenticación; probar POST sin token → 401.",
                ],
                [
                    "Confusión con tráfico real",
                    "Mantener etiqueta exploratoria y limitaciones junto a métricas.",
                ],
                [
                    "Fallo de dependencias externas",
                    "Repetir auditoría npm y pruebas SQL cuando el entorno lo permita.",
                ],
            ],
            [185, 315],
        ),
        PageBreak(),
    ]
    # Page 4.
    story += [
        heading("Factibilidad y dictamen del comité de cambios"),
        P(
            "La revisión técnica considera el cambio <b>factible</b>: afecta una ruta, la composición "
            "de dependencias, dos casos de uso, un puerto y un componente de interfaz. No exige "
            "migración SQL ni recolección de datos para demostrar la mejora de arquitectura. "
            "El alcance se limita a PMV3 y el esfuerzo estimado es 8–12 horas-persona."
        ),
        P(
            "<b>Estado CCB:</b> solicitud preparada e implementación técnica comprobada. "
            "La aprobación académica formal sigue pendiente de revisión y firma del equipo/docente. "
            "Este informe no suplanta esa decisión."
        ),
        heading("Conclusiones"),
        P(
            "1. El puerto de simulación permite probar la orquestación sin levantar SUMO y reduce "
            "el acoplamiento de la ruta REST."
        ),
        P(
            "2. Los tres escenarios se pueden reproducir, pero la red OSM y las rutas sintéticas "
            "no sustituyen aforos actuales ni cartografía oficial para calibrar Av. Ferrocarril."
        ),
        P(
            "3. El cambio se integra en PMV3 sin alterar la persistencia ni el contrato HTTP; "
            "su cierre académico requiere dictamen CCB y conservación de esta evidencia."
        ),
        heading("Evidencia de asistencia virtual"),
    ]
    if evidence.is_file():
        reader = ImageReader(str(evidence))
        iw, ih = reader.getSize()
        target_w = 485
        story.append(Image(str(evidence), width=target_w, height=target_w * ih / iw))
        story.append(Spacer(1, 8))
        story.append(
            P(
                "Figura 1. Captura aportada por el equipo: sesión virtual del VIII Congreso "
                "Internacional de Ingeniería y Arquitectura, día 2. La imagen acredita "
                "presencia en la sesión; no identifica una ponencia específica.",
                small,
            )
        )
    else:
        story.append(
            P(
                "La captura de asistencia no estaba disponible al generar este archivo.",
                small,
            )
        )
    story += [
        heading("Fuentes documentales"),
        P(
            "Consigna S14 del curso; repositorio Gemelos; `docs/semana14/CHG-001-2026.md`; "
            "`frontend/src/data/osm-exploratory-report.json`; evidencias de staging del 18/11/2026.",
            small,
        ),
    ]

    def footer(c, doc):
        c.setFont("Arial", 8)
        c.setFillColor(colors.HexColor("#51645B"))
        c.drawString(55, 40, "Taller de Proyectos 1 · NRC 30167 · CHG-001-2026")
        c.drawRightString(A4[0] - 55, 40, f"{doc.page}")

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=55,
        rightMargin=40,
        topMargin=45,
        bottomMargin=57,
        title="Solicitud de cambio CHG-001-2026",
        author="Equipo Gemelo Digital Huancayo",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    evidence_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_EVIDENCE
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    make_report(evidence_path, output_path)
    print(output_path)
