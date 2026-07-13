import os
import json
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from google import genai
from google.genai import types
from main import inicializar_firebase, analizar_reporte_con_gemini, guardar_en_firestore

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "api_keys.env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# =====================================================================
# 1. Configuración de la Página de Streamlit
# =====================================================================
st.set_page_config(
    page_title="Sociedad 5.0 - Motor de Inteligencia",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inicializar estado del tema (oscuro por defecto para un look premium)
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# =====================================================================
# 2. Inyección de Estilos CSS Personalizados (Diseño Zinc/Premium)
# =====================================================================
css_variables = f"""
<style>
:root {{
    --bg: {"#09090b" if IS_DARK else "#ffffff"};
    --bg-subtle: {"#0c0c0f" if IS_DARK else "#f9fafb"};
    --card: {"#0c0c0f" if IS_DARK else "#ffffff"};
    --card-hover: {"#131316" if IS_DARK else "#f4f4f5"};
    --border: {"#1e1e24" if IS_DARK else "#e4e4e7"};
    --border-subtle: {"#16161a" if IS_DARK else "#f0f0f2"};
    --text: {"#fafafa" if IS_DARK else "#09090b"};
    --text-muted: #71717a;
    --text-dim: {"#52525b" if IS_DARK else "#a1a1aa"};
    --accent: #2563eb;
    --shadow: {"none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"};
    --radius: 10px;
}}

/* Ocultar Streamlit Chrome */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Estilo global de la app */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}

.block-container {{
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1360px !important;
}}

/* Contenedores personalizados */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.4rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}}
.metric-label {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.metric-value {{
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.03em;
    margin-top: 0.2rem;
}}

.report-detail-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.8rem;
    box-shadow: var(--shadow);
    margin-top: 1rem;
}}

.report-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}}
.badge-narrative {{
    background: rgba(37, 99, 235, 0.15);
    color: #3b82f6;
    border: 1px solid rgba(37, 99, 235, 0.3);
}}
.badge-impact {{
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}}

/* Formateo del guion de YouTube */
.script-hook-card {{
    background: {"rgba(239, 68, 68, 0.08)" if IS_DARK else "rgba(239, 68, 68, 0.03)"};
    border-left: 5px solid #ef4444;
    border-radius: 4px 8px 8px 4px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
}}
.script-section-header {{
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    border-bottom: 2px solid var(--border);
    padding-bottom: 0.3rem;
    margin-top: 2rem;
    margin-bottom: 1rem;
}}
.script-vo {{
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.8rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--text);
}}
.script-vo-label {{
    font-weight: 800;
    color: #3b82f6;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}}
.script-production {{
    font-size: 0.82rem;
    background: {"#18181b" if IS_DARK else "#f4f4f5"};
    color: var(--text-muted);
    border-left: 3px solid var(--text-dim);
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.8rem;
    border-radius: 0 4px 4px 0;
}}
.script-sfx {{
    display: inline-block;
    font-size: 0.72rem;
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 600;
    margin-bottom: 0.8rem;
}}

/* Estilo para los inputs de Streamlit */
div[data-baseweb="select"] {{
    background-color: var(--card) !important;
}}
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 7px !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 3px;
}}
</style>
"""
st.markdown(css_variables, unsafe_allow_html=True)

# =====================================================================
# 3. Inicialización del Estado y Conexión de Firebase
# =====================================================================
@st.cache_resource
def get_db_client():
    """Retorna el cliente de Firestore cacheado para optimizar rendimiento."""
    return inicializar_firebase()

try:
    db = get_db_client()
except Exception as e:
    st.error(f"Error al conectar con Firestore: {e}")
    db = None

# =====================================================================
# 4. Funciones Auxiliares para Carga de Datos y API de Gemini
# =====================================================================
def obtener_todos_reportes(db_client):
    """Descarga de Firestore todos los reportes analizados en orden cronológico inverso."""
    if not db_client:
        return []
    try:
        docs = db_client.collection("analisis_sociedad").order_by("fecha_creacion", direction="DESCENDING").stream()
        reportes = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            reportes.append(d)
        return reportes
    except Exception as err:
        st.warning(f"No se pudieron leer datos de Firestore: {err}")
        return []

def generar_guion_youtube(analisis: dict) -> str:
    """
    Envía el análisis de Firestore a Gemini 3.5 Flash para estructurar
    un guion literario de 10 minutos optimizado para la retención y el algoritmo.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY no configurada en las variables de entorno."
    
    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    
    prompt = f"""
    Actúa como un guionista y productor de YouTube profesional de nivel senior (al estilo de canales de alto impacto como VisualPolitik, Magnates de la Tecnología o Veritasium).
    Tu tarea es transformar el siguiente análisis de inteligencia tecnológica/geopolítica en un guion literario de video largo completo y fluido para YouTube, diseñado para durar aproximadamente 10 minutos (requiere alrededor de 1200 a 1400 palabras en la narración).
    
    INFORMACIÓN CLAVE DEL INFORME:
    - Emisor del Reporte: {analisis.get('fuente_original')}
    - Resumen Ejecutivo: {analisis.get('resumen_ejecutivo')}
    - Calificación de Impacto: {analisis.get('nivel_impacto')}/10
    - Citas Clave del Reporte: {", ".join(analisis.get('citas_verificables', []))}
    - Enlaces de las Fuentes: {", ".join(analisis.get('enlaces_fuentes', []))}
    - Narrativa Principal: {analisis.get('narrativa_principal')}
    - Explicación Temática: {analisis.get('explicacion_narrativa')}
    
    REQUISITOS DEL ALGORITMO Y ESTRUCTURA DE RETENCIÓN DE YOUTUBE:
    1. EL GANCHO DISRUPTIVO (0:00 - 0:30 segundos) [CRÍTICO]:
       Comienza de inmediato con una frase de altísima intriga o una revelación de impacto basada en la narrativa principal ('{analisis.get('narrativa_principal')}'). Plantea un dilema que afecte directamente al bolsillo o el entendimiento del espectador. Cero intros genéricas. Promete revelar la verdad al final.
    2. CONTEXTUALIZACIÓN (0:30 - 2:00 minutos):
       Introduce el informe oficial y las fuentes ({analisis.get('fuente_original')}) estableciendo autoridad y credibilidad. Explica la gravedad de la situación a nivel global.
    3. NÚCLEO NARRATIVO Y DESARROLLO (2:00 - 8:00 minutos):
       Divide el desarrollo en 3 capítulos o actos dinámicos con títulos llamativos. Desarrolla la tecnología y las dinámicas de poder económico. Explica explícitamente cómo repercute esto en regiones en desarrollo como América Latina.
    4. PREVISIÓN DEL FUTURO (8:00 - 9:30 minutos):
       Plantea qué sucederá en la sociedad o el mercado en los próximos 24 meses debido a esta tecnología.
    5. CIERRE CON CONEXIÓN Y CTA (9:30 - 10:00 minutos):
       Termina con una pregunta abierta filosófica o geopolítica para promover la sección de comentarios (esto dispara el alcance del algoritmo de YouTube). Haz un llamado a la acción (CTA) dinámico y rápido de suscripción y debate.
       
    REQUISITO DE FORMATO DE SALIDA (MUY IMPORTANTE):
    Debes estructurar el guion combinando los siguientes componentes usando markdown limpio:
    
    * Para la voz en off del narrador, usa:
      VOZ EN OFF: [Texto dinámico e intrigante a narrar]
      
    * Para instrucciones de apoyo de imágenes/videos a editar en pantalla, usa:
      APOYO VISUAL: [Descripción del clip de video, gráficos en 3D, mapas resaltados, recortes de prensa o b-roll ideal]
      
    * Para transiciones e indicaciones de efectos sonoros para mantener enganchada a la audiencia, usa:
      EFECTO DE SONIDO: [Descripción del SFX como un swoosh rápido, estática, golpe bajo, zumbido cibernético]
    
    Asegúrate de que la narración se sienta fluida, intrigante y cinematográfica.
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Incrementada para dar más creatividad y naturalidad al diálogo
            )
        )
        return response.text
    except Exception as e:
        return f"Error al generar el guion con Gemini: {e}"

# =====================================================================
# 5. Cabecera de la Aplicación
# =====================================================================
head_left, head_right = st.columns([10, 2])
with head_left:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;'>
        <div style='background: #2563eb; width: 14px; height: 14px; border-radius: 3px;'></div>
        <span style='font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em;'>SOCIEDAD 5.0 — INTEL ENGINE</span>
    </div>
    <div style='color: #71717a; font-size: 0.85rem; margin-top: -0.2rem;'>
        Motor de extracción geopolítica, análisis tecnológico y generación de contenidos audiovisuales.
    </div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Modo Claro" if IS_DARK else "🌙 Modo Oscuro"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

st.markdown("<hr style='margin: 1.2rem 0; border-color: var(--border);'>", unsafe_allow_html=True)

# Cargar reportes al iniciar
lista_reportes = obtener_todos_reportes(db)

# =====================================================================
# 6. Pestañas de Navegación
# =====================================================================
tab_explorar, tab_nuevo_analisis, tab_ingesta_automatica = st.tabs([
    "🔍 Explorador de Informes", 
    "⚙️ Procesar Nuevo Documento", 
    "📡 Ingesta Automática"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: EXPLORADOR DE INFORMES Y GENERADOR DE GUIONES
# ---------------------------------------------------------------------
with tab_explorar:
    if not lista_reportes:
        st.info("No se encontraron análisis en la base de datos Firestore. Ve a la pestaña 'Procesar Nuevo Documento' para ingresar el primero.")
    else:
        # Fila de KPIs
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        # Calcular métricas simples
        total_reportes = len(lista_reportes)
        promedio_impacto = sum([r.get("nivel_impacto", 0) for r in lista_reportes]) / total_reportes
        
        # Encontrar la narrativa dominante
        narrativas = [r.get("narrativa_principal") for r in lista_reportes if r.get("narrativa_principal")]
        narrativa_dominante = max(set(narrativas), key=narrativas.count) if narrativas else "Ninguna"
        
        with kpi_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Reportes Procesados</div>
                <div class="metric-value">{total_reportes}</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Impacto Global Promedio</div>
                <div class="metric-value">{promedio_impacto:.1f} / 10</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Narrativa Predominante</div>
                <div class="metric-value" style="font-size: 1.35rem; font-weight: 800; margin-top: 0.6rem; color: #3b82f6;">{narrativa_dominante}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Selección de Reporte
        opciones_reportes = {f"[{r.get('nivel_impacto')} HP] - {r.get('fuente_original')} - ID: {r.get('id')[:6]}": r for r in lista_reportes}
        selected_key = st.selectbox("Selecciona un informe de Firestore para explorar y guionizar:", list(opciones_reportes.keys()))
        
        if selected_key:
            reporte_selec = opciones_reportes[selected_key]
            
            # Layout del reporte
            st.markdown("<div class='report-detail-card'>", unsafe_allow_html=True)
            
            # Badges
            narrativa_val = reporte_selec.get('narrativa_principal', 'No especificada')
            impacto_val = reporte_selec.get('nivel_impacto', 1)
            
            st.markdown(f"""
            <div style='margin-bottom: 1rem;'>
                <span class='report-badge badge-narrative'>🎬 {narrativa_val}</span>
                <span class='report-badge badge-impact'>🔥 Impacto: {impacto_val}/10</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Detalles principales
            st.markdown(f"### {reporte_selec.get('fuente_original')}")
            
            # Fecha formateada
            fecha_cr = reporte_selec.get('fecha_creacion')
            if fecha_cr:
                if isinstance(fecha_cr, datetime):
                    fecha_str = fecha_cr.strftime("%B %d, %Y - %H:%M UTC")
                else:
                    fecha_str = str(fecha_cr)
                st.markdown(f"<p style='color: var(--text-dim); font-size:0.75rem; margin-top:-0.5rem;'>Analizado el {fecha_str}</p>", unsafe_allow_html=True)
            
            # Columnas del reporte
            col_izq, col_der = st.columns([7, 5])
            
            with col_izq:
                st.markdown("**Resumen Ejecutivo:**")
                st.markdown(f"<p style='line-height:1.6; color: var(--text);'>{reporte_selec.get('resumen_ejecutivo')}</p>", unsafe_allow_html=True)
                
                st.markdown("**Enfoque Narrativo (Justificación para Video):**")
                st.markdown(f"<p style='line-height:1.6; color: var(--text-muted); font-style: italic;'>{reporte_selec.get('explicacion_narrativa')}</p>", unsafe_allow_html=True)
                
            with col_der:
                # Citas
                st.markdown("**Citas Verificables Extraídas:**")
                for cita in reporte_selec.get('citas_verificables', []):
                    st.markdown(f"<blockquote style='border-left: 3px solid var(--border); padding-left: 0.8rem; margin-left: 0.5rem; font-size: 0.82rem; color: var(--text-muted);'>\"{cita}\"</blockquote>", unsafe_allow_html=True)
                
                # Enlaces
                st.markdown("**Enlaces y Fuentes Citadas:**")
                enlaces = reporte_selec.get('enlaces_fuentes', [])
                if enlaces:
                    for link in enlaces:
                        st.markdown(f"🌐 [{link}]({link})", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: var(--text-dim); font-size:0.8rem;'>No se detectaron enlaces web en el reporte.</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Sección de Guionización
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🎬 Creación del Guion literario para YouTube (8-10 Minutos)")
            st.info("Este módulo utiliza Gemini 3.5 Flash para estructurar un guion con técnicas de retención algorítmica de YouTube basadas en la narrativa de este reporte.")
            
            # Generar guion
            btn_guion = st.button("Generar Guion para YouTube con IA 🎬", type="primary", use_container_width=True)
            
            if btn_guion:
                with st.spinner("Gemini 3.5 Flash está analizando el reporte y redactando el guion literario de 10 minutos..."):
                    guion_texto = generar_guion_youtube(reporte_selec)
                
                st.success("¡Guion literario generado exitosamente!")
                
                # Renderizar el guion estilizado
                with st.expander("👁️ Ver Guion Completo Formateado", expanded=True):
                    # Dividir la respuesta de Gemini y aplicar estilos personalizados para cada bloque
                    lineas = guion_texto.split("\n")
                    for linea in lineas:
                        linea_strip = linea.strip()
                        if not linea_strip:
                            continue
                        
                        # Detectar gancho de inicio (primeros 30s)
                        if "GANCHO" in linea_strip.upper() or "HOOK" in linea_strip.upper():
                            st.markdown(f"<div class='script-hook-card'><strong>⚠️ SECCIÓN: GANCHO DE 30 SEGUNDOS (HOOK)</strong><br>{linea}</div>", unsafe_allow_html=True)
                        # Detectar Voz en Off (VO)
                        elif "VOZ EN OFF:" in linea_strip.upper() or "VO:" in linea_strip.upper():
                            txt_vo = linea_strip.replace("VOZ EN OFF:", "").replace("VO:", "").strip()
                            st.markdown(f"<div class='script-vo'><div class='script-vo-label'>🎙️ Voz en Off (Locución)</div>{txt_vo}</div>", unsafe_allow_html=True)
                        # Detectar apoyo visual
                        elif "APOYO VISUAL:" in linea_strip.upper() or "B-ROLL:" in linea_strip.upper():
                            txt_visual = linea_strip.replace("APOYO VISUAL:", "").replace("B-ROLL:", "").strip()
                            st.markdown(f"<div class='script-production'>📹 <strong>B-ROLL / APOYO VISUAL:</strong> {txt_visual}</div>", unsafe_allow_html=True)
                        # Detectar efectos de sonido
                        elif "EFECTO DE SONIDO:" in linea_strip.upper() or "SFX:" in linea_strip.upper():
                            txt_sfx = linea_strip.replace("EFECTO DE SONIDO:", "").replace("SFX:", "").strip()
                            st.markdown(f"<span class='script-sfx'>🎵 SFX: {txt_sfx}</span>", unsafe_allow_html=True)
                        # Títulos de secciones
                        elif linea_strip.startswith("###") or linea_strip.startswith("##") or "ESCENA" in linea_strip.upper() or "CAPÍTULO" in linea_strip.upper():
                            st.markdown(f"<div class='script-section-header'>{linea_strip.replace('#', '').strip()}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(linea_strip)
                
                # Descargar Guion
                st.download_button(
                    label="📥 Descargar Guion en formato Markdown (.md)",
                    data=guion_texto,
                    file_name=f"guion_youtube_{reporte_selec.get('id')[:6]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

# ---------------------------------------------------------------------
# PESTAÑA 2: PROCESAR NUEVO DOCUMENTO
# ---------------------------------------------------------------------
with tab_nuevo_analisis:
    st.subheader("Ingresa un nuevo reporte para análisis")
    st.write("Copia y pega un reporte económico, político o tecnológico. El motor utilizará Gemini 3.5 Flash para extraer la información y clasificarla en Firestore.")
    
    nuevo_texto = st.text_area("Cuerpo del reporte original:", height=300, placeholder="Escribe o pega aquí el reporte económico de McKinsey, WEF, arXiv, etc...")
    
    col_btn_izq, col_btn_der = st.columns([3, 1])
    with col_btn_izq:
        btn_analizar = st.button("Ejecutar Análisis del Reporte ⚙️", type="primary", use_container_width=True)
    with col_btn_der:
        if st.button("Limpiar campo 🗑️", use_container_width=True):
            st.rerun()
            
    if btn_analizar:
        if not nuevo_texto.strip():
            st.warning("Por favor, ingresa un texto de reporte válido.")
        else:
            with st.spinner("Analizando reporte con Gemini 3.5 Flash y estructurando datos..."):
                try:
                    # 1. Obtener el análisis estructurado
                    analisis_resultado = analizar_reporte_con_gemini(nuevo_texto)
                    st.success("¡Análisis estructurado por Gemini exitosamente!")
                    
                    # Mostrar vista previa
                    st.json(analisis_resultado)
                    
                    # 2. Guardar en Firestore
                    with st.spinner("Guardando en la base de datos Firestore ('socidad50')..."):
                        doc_id = guardar_en_firestore(db, analisis_resultado)
                        
                    st.success(f"Análisis guardado con éxito. ID de documento: {doc_id}")
                    
                    # Forzar recarga de reportes en la pestaña principal
                    st.toast("Actualizando panel con el nuevo reporte...")
                    st.rerun()
                    
                except Exception as err:
                    st.error(f"Ocurrió un fallo en el procesamiento: {err}")

# ---------------------------------------------------------------------
# PESTAÑA 3: INGESTA AUTOMÁTICA DE FUENTES
# ---------------------------------------------------------------------
with tab_ingesta_automatica:
    st.subheader("Búsqueda y Descarga Automática de Fuentes")
    st.write(
        "Este módulo rastrea de forma autónoma APIs y canales oficiales (arXiv, WEF, MIT) "
        "para buscar los informes y papers más recientes, pasarlos por el análisis de Gemini 3.5 Flash e insertarlos en Firestore."
    )
    
    # Formulario de búsqueda
    col_f1, col_f2, col_f3 = st.columns([4, 4, 2])
    with col_f1:
        fuente_opcion = st.selectbox(
            "Selecciona la fuente de datos:",
            ["Buscar en todas las fuentes (Consolidado)", "arXiv (Papers de Inteligencia Artificial - cs.AI)", "World Economic Forum (WEF - Feed de Agenda)", "MIT Technology Review (Feed General)"]
        )
    with col_f2:
        palabra_clave_busqueda = st.text_input("Filtrar por palabra clave (opcional):", placeholder="ej. post-quantum, agent, automation...")
    with col_f3:
        limite_busqueda = st.number_input("Límite de resultados:", min_value=1, max_value=10, value=3)
        
    btn_rastrear = st.button("Rastrear, Analizar y Guardar en Firestore ⚡", type="primary", use_container_width=True)
    
    if btn_rastrear:
        # Mapear opción seleccionada
        fuente_key = ""
        if "todas" in fuente_opcion.lower() or "consolidado" in fuente_opcion.lower():
            fuente_key = "todos"
        elif "arxiv" in fuente_opcion.lower():
            fuente_key = "arxiv"
        elif "wef" in fuente_opcion.lower() or "forum" in fuente_opcion.lower():
            fuente_key = "wef"
        elif "mit" in fuente_opcion.lower():
            fuente_key = "mit"
            
        with st.spinner(f"Consultando fuente externa '{fuente_opcion}'..."):
            from ingest import buscar_documentos_remotos
            documentos_encontrados = buscar_documentos_remotos(fuente_key, palabra_clave_busqueda, limite_busqueda)
            
        if not documentos_encontrados:
            st.warning("No se encontraron documentos o artículos recientes en la búsqueda con los filtros aplicados.")
        else:
            st.success(f"¡Se recuperaron {len(documentos_encontrados)} documentos con éxito!")
            
            # Procesar cada documento en lote
            for idx, doc in enumerate(documentos_encontrados):
                st.markdown(f"---")
                st.markdown(f"### Documento {idx+1}: {doc['titulo']}")
                st.markdown(f"**Fuente:** {doc['fuente']} | **Fecha:** {doc['fecha']} | [Enlace Oficial]({doc['enlace']})")
                
                # Crear el texto completo para Gemini
                texto_a_analizar = f"""
                TÍTULO: {doc['titulo']}
                AUTORES: {doc['autores']}
                FECHA: {doc['fecha']}
                ENLACE: {doc['enlace']}
                
                RESUMEN/TEXTO ORIGINAL:
                {doc['resumen']}
                """
                
                # Botón expandible para ver el crudo
                with st.expander("Ver contenido original recuperado", expanded=False):
                    st.text(doc['resumen'])
                
                # Analizar y guardar
                with st.spinner(f"Gemini 3.5 Flash analizando documento {idx+1}..."):
                    try:
                        analisis_resultado = analizar_reporte_con_gemini(texto_a_analizar)
                        
                        # Inyectar el enlace de la fuente descargada si el análisis no lo capturó de forma nativa
                        if doc['enlace'] not in analisis_resultado.get('enlaces_fuentes', []):
                            analisis_resultado.setdefault('enlaces_fuentes', []).append(doc['enlace'])
                            
                        # Mostrar resultado
                        st.json(analisis_resultado)
                        
                        # Guardar
                        doc_id = guardar_en_firestore(db, analisis_resultado)
                        st.success(f"¡Análisis estructurado y guardado en Firestore! ID: {doc_id}")
                        
                    except Exception as e:
                        st.error(f"Error al analizar el documento {idx+1}: {e}")
            
            st.toast("¡Procesamiento en lote completado!")
            st.rerun()
