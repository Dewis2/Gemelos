# Verificación de remediaciones OWASP

Fecha de corte: 20/11/2026. Referencia: [plan](05_plan_owasp.md).

| ID | Estado | Evidencia / razón |
| --- | --- | --- |
| S-01 | Pendiente | No hay política de limitación de intentos que haya sido comprobada detrás del proxy de Render. Añadir un contador local sin entender ese origen podría bloquear usuarios legítimos. |
| S-02 | Pendiente | Dos ejecuciones de `npm audit --omit=dev --json` terminaron con `ECONNRESET`; no existe resultado de paquetes Python desplegados. |
| S-03 | Parcial preexistente | Los tokens tienen `exp`, firma y prueba de alteración. No hay revocación individual ni prueba de rotación en staging. |
| S-04 | Pendiente | Se dispone de logs, pero no de una alerta probada. |
| S-05 | Parcial preexistente | Cabeceras de protección y CI presentes; CSP y fijación por digest no se implementaron. |

La prueba `backend/tests/integration/test_editor_auth.py` demuestra rechazo de una escritura sin token, login correcto, rechazo de firma alterada y preflight CORS. La captura de [ejecución SUMO autenticada](evidencias/2026-11-18/README.md) demuestra el flujo del frontend en staging, no una auditoría de ataques. No se afirma que las vulnerabilidades potenciales hayan sido corregidas.
