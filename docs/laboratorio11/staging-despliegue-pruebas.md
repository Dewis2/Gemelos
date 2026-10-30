# Laboratorio 11 — Staging cloud: despliegue y pruebas funcionales

**Proyecto:** Gemelo Digital Inteligente, Av. Ferrocarril, Huancayo.
**Repositorio:** https://github.com/Dewis2/Gemelos
**Tablero:** https://trello.com/b/IzYENbfc

> Estado comprobable: el código y `render.yaml` están listos para iniciar la
> provisión. **La existencia de esta configuración NO demuestra un despliegue.**
> No usar localhost, túneles ngrok ni capturas locales para acreditar la rúbrica.

## 1. Responsabilidades actualizadas

El equipo debe confirmar formalmente responsabilidades por ausencia temporal de
integrantes. **Fabricio Chicmana ha asumido frontend y backend para esta práctica**;
Brayan Ochoa puede revisar arquitectura y apoyar API; Marcelo Morris conserva la
especialidad de PostgreSQL/PostGIS; Christian Zevallos, la de IA/API; Carlos
Escobar, la de coordinación y Scrum. Los trabajos solo se registran como
ejecutados si hay evidencia de quién los realizó.

## 2. Arquitectura y servicios cloud propuestos

```text
Navegador HTTPS
   └─ Render Static Site: frontend React / Vite
          └─ HTTPS / FastAPI (Render Docker web)
                ├─ casos de uso + puertos de arquitectura hexagonal
                ├─ adaptador PostgreSQL + SQLAlchemy + Alembic
                │      └─ Render PostgreSQL + PostGIS (servicio gestionado)
                └─ adaptador Joblib / Random Forest (benchmark MITV-UCI)
```

SUMO y la validación con datos actuales de Huancayo siguen pendientes.
MQTT se mantiene desactivado en Staging hasta contar con broker accesible y
pruebas de integración; no se simula conectividad inexistente.

## 3. Pasos obligatorios en Render

1. Crear/vincular una cuenta en https://dashboard.render.com y enlazar el
   repositorio `Dewis2/Gemelos` con permiso de lectura.
2. Elegir **New > Blueprint** y seleccionar el archivo `render.yaml` de `main`.
   Revisar los planes disponibles y **los costos antes de confirmar**.
3. En la variable `VITE_API_URL` del frontend colocar la **URL HTTPS exacta**
   del servicio `gemelos-staging-api`, sin barra al final.
   Esta variable se inyecta al **compilar**, por lo que modificarla exige
   **redeploy del frontend**.
4. En la variable `CORS_ORIGINS` del backend colocar la **URL HTTPS exacta
   del frontend**, sin rutas ni barra final. Si hay más orígenes, separarlos
   con comas, pero no permitir `*`.
5. El backend recibe `DATABASE_URL` desde la BD gestionada. La aplicación
   convierte URLs `postgres://` y `postgresql://` a
   `postgresql+psycopg://` para usar psycopg 3.
6. Render construye el backend desde `deploy/Dockerfile.staging.backend`.
   Durante la compilación se descarga el benchmark **MITV-UCI** y se genera el
   artefacto Joblib. Requiere salida a Internet y tiempo/recursos suficientes;
   si falla, revisar logs de compilación. **No son aforos actuales de Huancayo.**
7. El proceso de inicio ejecuta `alembic upgrade head` sobre PostgreSQL,
   que crea PostGIS y aplica el esquema. Registrar evidencia del estado de
   la extensión, tablas y migración. No usar la base personal de desarrollo.
8. Esperar confirmación real de despliegue, sin inferirla del YAML. Registrar:
   - Frontend: `[URL_PUBLICA_HTTPS_PENDIENTE]`
   - Backend: `[URL_PUBLICA_HTTPS_PENDIENTE]`
   - Fecha y versión (SHA): `[PENDIENTE]`
   - Base: `[NOMBRE_INSTANCIA_PENDIENTE]` (nunca credenciales)

**Seguridad:** no exponer `DATABASE_URL`, tokens, secretos, ni credenciales en
capturas, commits o la memoria del informe. El prototipo no tiene autenticación
de usuarios ni controles de autorización productivos; exponer rutas de escritura
en una URL pública es un **riesgo**. Usar exclusivamente datos autorizados de
prueba, cuenta aislada de Staging y limitar el acceso por las capacidades
disponibles del proveedor. No ingresar datos personales ni producción real.

## 4. Pruebas funcionales: PMV1

Ejecutar en el entorno público y adjuntar capturas **completas con URL visible**:

| Historia | Acción verificable | Evidencia y estado |
| --- | --- | --- |
| HU-01 | Consultar históricos P03, P04 y P42 de 2013 | Pantalla y fuente. **Pendiente nube** |
| HU-02 | Identificar diferencia históricos vs actuales | Aviso periodo 2013. **Pendiente nube** |
| HU-03 | Mostrar los 3 tramos y puntos del mapa | Pantalla y aviso de geometría provisional. **Pendiente nube** |
| HU-04 | Solicitar predicción con datos válidos | Respuesta 201, valor y versión experimental. **Pendiente nube** |
| HU-05 | Validar variables y entradas | Respuesta 422, 404 y 503 según prueba. **Pendiente nube** |
| HU-06 | Mostrar métricas, procedencia MITV-UCI | Captura del aviso y fuente. **Pendiente nube** |
| HU-07 | Mostrar arquitectura hexagonal | Vista y carpetas GitHub. **Pendiente nube** |
| HU-08 | Demostrar dominio desacoplado | Prueba/código, no solo una captura. **Pendiente nube** |
| HU-09 | Mostrar estado real de servicios | Vista y limitaciones pendientes. **Pendiente nube** |
| HU-10 | Escenarios sin atribuir métricas reales a placeholders | Captura y notas. **Pendiente nube** |

## 5. Pruebas funcionales: PMV2

| Historia | Criterio de aceptación previsto | Estado verificado |
| --- | --- | --- |
| HU-11 | Exportación segura y huella de integridad SHA256 | **Pendiente; no acreditada en nube** |
| HU-12 | Versionamiento de experimentos ML y sus métricas | **Pendiente; no acreditada en nube** |
| HU-13 | Datos locales actuales y evaluación temporal del modelo | **Pendiente; aforos locales no acreditados** |
| HU-16 | Eventos MQTT de extremos a extremo | **Pendiente; MQTT desactivado en Staging** |
| HU-17 | Persistencia integral con PostgreSQL/PostGIS | **Pendiente de prueba remota** |
| HU-18 | Validación cartográfica de los tramos | **Pendiente de validación de geometría** |

**No completar casillas de aprobación sin ejecutar los escenarios con datos
reales de prueba, capturar las respuestas y adjuntar logs con timestamps.**

## 6. Comprobación automática y manual

La nueva acción GitHub `staging-readiness.yml` valida estructura de
`render.yaml`, configuración y pruebas Python, además de compilación Vite con
URL HTTPS ficticia **solo para verificar build** (no prueba cloud).

Después de desplegar, ejecutar desde un equipo externo:

```bash
python scripts/staging_smoke.py --frontend https://URL_FRONTEND --api https://URL_API
python scripts/staging_smoke.py --frontend https://URL_FRONTEND --api https://URL_API --predict
```

El segundo comando crea una predicción de prueba en la BD Staging. Debe
ejecutarse únicamente cuando ese entorno esté preparado para datos de prueba.
Registrar fecha, URLs, SHA, salida, capturas del frontend y consultas SQL en
DBeaver/pgAdmin; excluir secretos y datos personales.

## 7. Matriz de evidencias a completar por cada HU

- ID de HU / PMV y criterio **Given–When–Then**.
- URL pública HTTPS del frontend y endpoint HTTP.
- Datos **de prueba** y su procedencia.
- Captura de pantalla completa (URL, entrada, respuesta).
- Resultado HTTP/log o consulta SQL sobre la BD remota.
- Estado: **aprobado / rechazado / no ejecutado**.
- Fecha, ejecutor, responsable, Git SHA y acciones correctivas.

## 8. Estado del Laboratorio 11 frente a la rúbrica

| Criterio (5 puntos c/u) | Estado actual con evidencia |
| --- | --- |
| Cloud No Localhost y hexagonal | Código y configuración preparados; **URLs públicas por obtener** |
| BD e IA operativas en nube | Código y artefacto de entrenamiento preparado; **pruebas remotas pendientes** |
| End-to-end PMV1 y PMV2 | Casos documentados; **capturas de la nube pendientes** |
| Informe y equipo | Plan y roles identificados; **completar evidencias efectivas** |

**Conclusión:** listo para iniciar el despliegue; todavía no se acredita la
práctica por completo ni se puede asignar una nota de /20.

Fuentes: Guía de Laboratorio 11, documentos PMV1, repositorio del proyecto,
documentación oficial de Render:
https://render.com/docs/blueprint-spec y
https://render.com/docs/postgresql-extensions.
