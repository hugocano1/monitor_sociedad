# Memoria de Proyecto: Sociedad 5.0

Este archivo actúa como la bitácora de desarrollo y estado del motor de análisis geopolítico y tecnológico **Sociedad 5.0**.

## Contexto del Proyecto
El sistema procesa reportes y documentos extensos sobre coyunturas económicas, geopolíticas y tecnológicas utilizando modelos de la familia **Google Gemini** mediante salidas estructuradas de JSON (*Structured Outputs*). Los análisis resultantes se guardan de forma persistente en colecciones NoSQL dentro de una base de datos específica en **Google Cloud Firestore**.

---

## Historial de Sesiones

### Sesión: 12 de Julio de 2026
* **Objetivo**: Configuración inicial, expansión del pipeline para estructurar fuentes prioritarias (v1.1) y creación de la interfaz web en Streamlit con generador de guiones para YouTube (v1.2).
* **Logros**:
  1. **Inicialización del Entorno**: Configuración del entorno virtual `.venv` y definición de dependencias en [requirements.txt](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/requirements.txt) (UTF-8) añadiendo `streamlit`.
  2. **Estructura Pydantic Avanzada (v1.1)**: Expansión de `AnalisisReporte` para incluir `enlaces_fuentes` (lista de URLs), `narrativa_principal` (restringido a "Transferencia de Riqueza", "Cambio de Poder Geopolítico" u "Obsolescencia Cotidiana"), y `explicacion_narrativa` (justificación dinámica orientada a producción audiovisual).
  3. **Enfoque en Fuentes Globales**: Modificación del prompt del sistema para orientar y priorizar fuentes oficiales y de prestigio como McKinsey, BCG, WEF, OCDE, arXiv, MIT Technology Review e IEEE.
  4. **Adaptabilidad del Modelo**: Configuración dinámica de `GEMINI_MODEL` (usando `gemini-3.5-flash` por cuota).
  5. **Conexión Firestore Específica**: Configuración del cliente para conectarse directamente a la base de datos `"socidad50"`.
  6. **Prueba Completa Exitosa**: Ejecución satisfactoria de extremo a extremo que generó un análisis detallado bajo la narrativa de "Transferencia de Riqueza" con extracción de 3 URLs oficiales e inserción exitosa en Firestore con ID de documento: `VuToZM2Y0iODqN92hqyR`.
  7. **Interfaz Web Streamlit (v1.2)**: Creación de [app.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/app.py) que permite visualizar reportes directamente desde Firestore, ingresar nuevos análisis, e invocar a Gemini 3.5 Flash para generar guiones literarios completos de 10 minutos con marcadores de producción (Voz en Off, B-Roll, SFX) optimizados para la retención del algoritmo de YouTube.
  8. **Ingesta Automática de Fuentes (v1.3)**: Implementación de [ingest.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/ingest.py), un motor que rastrea automáticamente APIs públicas y RSS feeds (arXiv, WEF, MIT) para extraer nuevos reportes e informes sin intervención manual, procesarlos en lote con la IA de Gemini e insertarlos en Firestore.

---

## Tareas Pendientes (Backlog)

- [ ] **Manejo de Errores Geográficos y Red**: Implementar una política de reintentos (retry policy) con retroceso exponencial (exponential backoff) para manejar caídas temporales de red o cuotas de API (Error 429/503).
- [x] **Procesamiento por Lotes (Batch Processing)**: Diseñado y programado mediante el escaneo e ingesta múltiple en lote directo en la pestaña 3.
- [ ] **Control de Contexto (Tokens)**: Añadir una función de conteo de tokens o validación de longitud previa para evitar sobrepasar los límites de contexto de modelos más pequeños en textos extremadamente largos.
- [x] **Visualizador de Base de Datos**: Reemplazado y superado con creces mediante la creación del Dashboard interactivo local en Streamlit.
