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
  9. **Búsqueda Consolidada Multifuente (v1.4)**: Añadido soporte en `ingest.py` y `app.py` para consultar simultáneamente en arXiv, MIT y WEF con un solo clic, automatizando por completo la recopilación de informes de inteligencia.

### Sesión: 10 de Agosto de 2026 (v2.0)
* **Objetivo**: Transformación y escalabilidad del proyecto para soporte de YouTube Studio completo (títulos, descripciones SEO, tags, prompts IA 16:9), nuevo módulo exclusivo de YouTube Shorts (1 min), expansión de ingesta a más revistas y portales científicos/técnicos mundiales, y preparación para despliegue 100% cloud.
* **Logros**:
  1. **Paquete YouTube Largo (10 Min)**: Implementación en [app.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/app.py) de la función `generar_guion_youtube_paquete()` que genera en un solo paso: 3 títulos persuasivos CTR, descripción SEO optimizada con timestamps y hashtags, lista de etiquetas (tags) para copiar a YouTube Studio, prompts visuales de IA cinematográficos en inglés (16:9) y el guion literario de 10 min.
  2. **Motor de YouTube Shorts (1 Min / Diario)**: Creación de la pestaña `📱 Shorts de IA (1 Minuto)` en [app.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/app.py) y la función `generar_guion_short_paquete()` para condensar cualquier informe de Firestore en un Short vertical de 60 segundos (~140 palabras) con ganchos de 5s, ritmo dinámico, título con emojis, hashtags (#Shorts #IA) y prompts visuales en formato vertical (`--ar 9:16`).
  3. **Expansión Multifuente Global (v2.0)**: Actualización de [ingest.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/ingest.py) incorporando nuevas fuentes de alta reputación: *IEEE Spectrum*, *Nature Machine Intelligence*, *MIT Tech Review*, *arXiv (cs.AI)*, *TechCrunch AI*, *Wired AI*, *VentureBeat AI* y *BBC News Tech*.
  4. **Categorización de Ingesta**: Clasificación de fuentes por categorías (`Universidades & Ciencia`, `Prensa Tech Global`, `Organismos & Coyuntura Global`).
  5. **Compatibilidad 100% Cloud**: Adaptación de `inicializar_firebase()` y `analizar_reporte_con_gemini()` en [main.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/main.py) y [app.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/app.py) para resolver credenciales e API keys desde `st.secrets` y variables de entorno crudas (`FIREBASE_CREDENTIALS_JSON`), permitiendo desplegar la app 24/7 en **Streamlit Community Cloud** sin depender de ejecutar `streamlit run` en la PC local.
  6. **Humanización y Enfoque Constructivo Positivo**: Inyección de directrices estrictas anti-IA (prohibiendo muletillas como 'En un mundo donde...', 'Sumérgete en...') y garantizando una perspectiva equilibrada de optimismo tecnológico que celebre los proyectos e investigaciones que hacen crecer positivamente a la sociedad y mejoran la vida humana.
  7. **Studio Teleprompter Interactivo**: Implementación de un visor de Teleprompter en ventana limpia e independiente que solicita permisos de webcam (laptop/celular), superpone el texto narrativo filtrado (`extraer_narracion_limpia`), ofrece atajos de teclado (`Barra Espaciadora`, `Flechas`), ajuste de velocidad, tamaño de fuente, modo espejo y alternador de formato 16:9 / 9:16. Incluye exportación en `.txt` y copiado fácil para Google Drive/Docs.
  8. **Corrección de Inicialización en Nube de Firestore**: Fijado de paso de `project_id` y `credentials` explícitos en `gcloud_firestore.Client()` en [main.py](file:///C:/Users/Hugoalx/Desktop/monitor_sociedad/main.py) para solucionar el fallo `Project was not passed and could not be determined from the environment` en Streamlit Cloud.
  9. **Refactorización Binaria Base64 para Teleprompter**: Solución completa del error `Uncaught SyntaxError` mediante codificación Base64 Uint8Array para el lanzamiento del Teleprompter en popup/nueva ventana y adición de visor desplegable alternativo en pantalla completa compatible con navegadores móviles estrictos.

---

## Tareas Pendientes (Backlog)

- [ ] **Manejo de Errores Geográficos y Red**: Implementar una política de reintentos (retry policy) con retroceso exponencial (exponential backoff) para manejar caídas temporales de red o cuotas de API (Error 429/503).
- [x] **Procesamiento por Lotes (Batch Processing)**: Diseñado y programado mediante el escaneo e ingesta múltiple en lote directo en la pestaña 4.
- [ ] **Control de Contexto (Tokens)**: Añadir una función de conteo de tokens o validación de longitud previa para evitar sobrepasar los límites de contexto de modelos más pequeños en textos extremadamente largos.
- [x] **Visualizador de Base de Datos**: Reemplazado y superado con creces mediante la creación del Dashboard interactivo local/cloud en Streamlit.
- [x] **Paquete Metadatos YouTube (v2.0)**: Completado (Títulos A/B, Descripción SEO, Tags, Prompts IA 16:9).
- [x] **Módulo de Shorts Diarios (v2.0)**: Completado (Guiones 60s, Prompts 9:16).
- [x] **Despliegue Cloud (v2.0)**: Preparado para Streamlit Community Cloud.

