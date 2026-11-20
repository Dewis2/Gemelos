# Auditoría OWASP Top 10 del prototipo

Fecha de corte: 20/11/2026. La guía docente enumera las categorías OWASP Top 10 **2021**, que se usan en esta tabla. [OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/) reorganiza la cadena de suministro y las condiciones excepcionales; se indica la correspondencia al final. Esta revisión es de código, configuración y pruebas disponibles; no es un pentest.

| Categoría de la guía | Estado y evidencia | Impacto / probabilidad | Severidad residual |
| --- | --- | --- | --- |
| A01 Control de acceso roto | Staging exige token para POST/PUT/PATCH/DELETE; test de 401 y 200 autenticado. GET público es una decisión de producto. No existen roles granulares. | Medio / medio | Medio |
| A02 Fallos criptográficos | `scrypt` para contraseña, HMAC-SHA256 para token, HTTPS y secreto fuera del repositorio. Token de 8 h sin revocación individual. | Medio / bajo | Medio |
| A03 Inyección | Entradas Pydantic y ORM; SUMO acepta tres niveles, sin rutas arbitrarias ni shell. No hay prueba de fuzzing o SAST completo. | Alto / bajo | Medio |
| A04 Diseño inseguro | Se distinguen datos reales, históricos y simulados; el editor único limita la granularidad de permisos. Falta modelo formal de amenazas. | Medio / medio | Medio |
| A05 Configuración incorrecta | Staging falla al arrancar sin auth, PostgreSQL remota y origen CORS HTTPS. Cabeceras `nosniff`, `DENY`, `no-referrer`; falta CSP documentada. | Medio / medio | Medio |
| A06 Componentes vulnerables | `package-lock.json` existe. La auditoría npm no concluyó por `ECONNRESET`; Python emplea rangos de versiones, sin lock verificable. | Alto / indeterminada | Pendiente de medición |
| A07 Fallos de autenticación | Login y rechazo de tokens modificados probados. No se observa limitación de intentos ni invalidación anticipada de tokens. | Medio / medio | Medio |
| A08 Integridad de software y datos | Hashes SHA-256 de red/rutas SUMO y CI; las acciones GitHub usan etiquetas de versión y las dependencias Python no están fijadas por hash. | Medio / medio | Medio |
| A09 Registro y monitoreo | Logging de aplicación y logs de Render; no hay umbrales, alertas ni revisión documentada de eventos de login. | Medio / medio | Medio |
| A10 SSRF | Las rutas HTTP públicas no aceptan una URL de destino para fetch; el comando de ingesta es una operación administrativa separada. No hubo prueba dirigida de SSRF. | Alto / bajo | Bajo |

**Cobertura verificable:** controles parciales o suficientes en 8 de las 10 categorías; A06 carece de dictamen de componentes y A09 de alertamiento. Este conteo no es un «score de seguridad» probabilístico ni prueba ausencia de vulnerabilidades. El dictamen es **seguridad parcial de staging; no acreditada para producción**.

En OWASP 2025, A03 agrupa fallos de cadena de suministro y A10 se ocupa del manejo de condiciones excepcionales; el SSRF de 2021 deja de figurar como categoría independiente. La matriz docente se conserva para facilitar evaluación.
