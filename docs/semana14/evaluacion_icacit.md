# Evaluación de evidencias por atributo ICACIT

**Proyecto:** Gemelo Digital Inteligente para la movilidad urbana de Huancayo. **NRC:** 30167. **Corte:** 20/11/2026. Base revisada: informe `docs/informes/Informe_PMV1_PMV2_PMV3_2026-11-13.docx`, código y evidencias del repositorio. Esta matriz evalúa evidencias del proyecto; no declara acreditación ICACIT del programa.

| Atributo solicitado | Evidencia comprobable | Hallazgo y mejora | Sección recomendada del informe |
| --- | --- | --- | --- |
| Conocimientos de Ingeniería | Secciones 2 y 5.2: arquitectura hexagonal, OSM, SUMO 1.28, semilla 30167; metadatos ML con partición temporal y métricas | Explicar ecuaciones de duración, espera, MAE y RMSE y justificar la selección de escenarios. Separar aprendizaje nacional de simulación local | 2 Metodología; nueva subsección 5.2.1 Fundamento técnico |
| Medioambiente y Sostenibilidad | Sección 6 reconoce que no hay validación del corredor | No hay inventario de energía/emisiones ni comparación ambiental. Definir indicadores medibles para una futura campaña y declarar que hoy no se estiman impactos reales | Nueva 6.1 Impacto ambiental y límites |
| El Ingeniero y la Sociedad | Secciones 1 y 6 advierten sobre la antigüedad de aforos, procedencia OSM y ausencia de calibración | Agregar análisis de privacidad, licencias ODbL, accesibilidad y consecuencias de usar predicciones no validadas para decisiones públicas | Nueva 6.2 Ética, normativa y accesibilidad |
| Gestión de Proyectos | Secciones 3–5 organizan PMV e historias HU-01 a HU-18; PR y respaldos tienen fechas | Falta matriz de responsables, esfuerzo y control de cambios formal. Incorporar CHG-001 y riesgos con dueño, fecha y criterio de cierre | 2 Metodología; nueva 5.5 Gestión del cambio |
| Diseño y Desarrollo de Soluciones | Secciones 3–5 muestran interfaz, API, persistencia y simulación; las pruebas de fakes sostienen separación de capas | El informe del 13/11 no refleja el nuevo endpoint autenticado de SUMO ni los casos de uso agregados. Actualizar diagrama y prueba de aceptación | 5.4 Integración y calidad |
| Análisis de Problemas | Secciones 1 y 6 delimitan ausencia de aforos 2026 y geometría oficial | Cuantificar cobertura de fuentes y presentar un plan de medición/calibración con criterios de aceptación antes de afirmar utilidad vial | 1 Introducción; 6 Discusión |
| Uso de Herramientas Modernas | Secciones 2 y 5: PostgreSQL/PostGIS, React, FastAPI, OSM, SUMO, GitHub Actions y hashes | Completar matriz herramienta–propósito–limitación; registrar versiones, licencias y la falta de auditoría npm por `ECONNRESET` | 2 Metodología; anexo de reproducción |

## Juicio de cumplimiento

Las siete dimensiones tienen alguna evidencia técnica, pero **ninguna prueba de software sustituye una evaluación de impacto social o ambiental**. El proyecto cumple de forma parcial como prototipo académico. La principal brecha científica es la ausencia de aforos locales recientes y geometría oficial; los escenarios OSM/SUMO se etiquetan exploratorios. El documento de origen ICACIT solicita hallazgos, mejoras y ubicación de cada atributo: esta matriz cubre esos tres campos y enlaza con la [auditoría final](../07_auditoria_final.md).
