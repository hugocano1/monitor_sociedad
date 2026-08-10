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

def get_gemini_client():
    """Obtiene el cliente de GenAI resolviendo API key de env o secrets."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def get_gemini_model_name():
    model_name = os.getenv("GEMINI_MODEL")
    if not model_name:
        try:
            if hasattr(st, "secrets") and "GEMINI_MODEL" in st.secrets:
                model_name = st.secrets["GEMINI_MODEL"]
        except Exception:
            pass
    return model_name or "gemini-3.5-flash"

def generar_guion_youtube_paquete(analisis: dict) -> dict:
    """
    Genera un paquete completo de publicación para YouTube (Video Largo ~10 Min):
    1. 3 Títulos persuasivos de alto CTR.
    2. Descripción SEO optimizada con marcas de tiempo, síntesis y hashtags.
    3. Lista de etiquetas (Tags) para YouTube Studio.
    4. Prompts visuales de IA robustos en inglés (Midjourney/Flux/Runway format).
    5. Guion literario completo estructurado.
    """
    client = get_gemini_client()
    if not client:
        return {"error": "GEMINI_API_KEY no configurada."}
    
    model_name = get_gemini_model_name()
    
    prompt = f"""
    Actúa como un creador y guionista de YouTube humano de nivel senior (estilo periodista de divulgación científica y analista apasionado, como VisualPolitik o Veritasium).
    Tu tarea es transformar el siguiente informe en un PAQUETE COMPLETO DE PUBLICACIÓN Y GUION PARA YOUTUBE (Video Largo 8-10 Minutos).
    
    DIRECTRICES DE ESTILO Y TONO (OBLIGATORIAS):
    1. TONO HUMANO Y NATURAL: Escribe como un ser humano real conversando con otro apasionado de la tecnología. PROHIBIDO usar muletillas y clichés de IA como 'En un mundo donde...', 'Sumérgete en...', 'En la era digital...', 'Es fundamental destacar...', 'Un testimonio de...', 'Desentrañar...', 'En conclusión...'.
    2. VISIÓN CONSTRUCTIVA Y ENFOQUE POSITIVO: NO seas apocalíptico ni alarmista sin sentido. Reconoce y resalta cuando la tecnología beneficia a la humanidad, resuelve problemas complejos o impulsa el bienestar social, combinando esto con análisis maduro de los desafíos.
    3. RITMO DINÁMICO: Frases de longitud variada, analogías de la vida cotidiana y tono ágil.
    
    DATOS DEL INFORME:
    - Fuente Original: {analisis.get('fuente_original')}
    - Resumen Ejecutivo: {analisis.get('resumen_ejecutivo')}
    - Impacto: {analisis.get('nivel_impacto')}/10
    - Citas: {", ".join(analisis.get('citas_verificables', []))}
    - Fuentes: {", ".join(analisis.get('enlaces_fuentes', []))}
    - Narrativa: {analisis.get('narrativa_principal')}
    - Explicación: {analisis.get('explicacion_narrativa')}
    
    DEBES RESPONDER ÚNICA Y EXCLUSIVAMENTE CON UN OBJETO JSON VÁLIDO QUE TENGA LA SIGUIENTE ESTRUCTURA EXACTA (SIN TEXTO EXTRA ADICIONAL FUERA DEL JSON):
    
    {{
        "titulos": [
            "Título 1 Persuasivo de alto CTR (Dilema o Revelación positiva/impactante)",
            "Título 2 Alternativo enfocado en Oportunidad/Transformación",
            "Título 3 Alternativo enfocado en Futuro/Sociedad"
        ],
        "descripcion_seo": "Resumen atractivo de la descripción para YouTube Studio.\\n\\n📌 CAPÍTULOS / MARCAS DE TIEMPO:\\n0:00 - El Gancho\\n0:30 - Contexto Global\\n2:00 - Desarrollo\\n8:00 - Previsión 24 Meses\\n9:30 - Conclusión\\n\\n🔗 FUENTES OFICIALES:\\n" + ", ".join(analisis.get('enlaces_fuentes', [])) + "\\n\\n#IA #Tecnologia #Geopolitica #Sociedad50",
        "etiquetas": "inteligencia artificial, geopolitica, economia global, sociedad 5.0, futuro del trabajo, tecnologia, avances tecnologicos, noticias tech",
        "prompts_visuales": [
            "Prompt 1 en inglés detallado para Midjourney/Flux: Cinematic 8k, hyperrealistic, warm atmospheric lighting, cinematic wide shot, [elemento clave], 35mm lens --ar 16:9",
            "Prompt 2 en inglés...",
            "Prompt 3 en inglés..."
        ],
        "guion_completo": "Markdown con el guion literario de 10 min estructurado con VOZ EN OFF:, APOYO VISUAL:, EFECTO DE SONIDO:, PROMPT IA:"
    }}
    
    REGLAS DEL GUION DENTRO DEL JSON:
    - Gancho inicial de 30 segundos intrigante y humano.
    - Contextualización de fuentes.
    - 3 capítulos de desarrollo dinámico destacando el valor positivo y los retos reales.
    - Previsión a 24 meses realista.
    - Cierre con pregunta abierta para comentarios y CTA rápido.
    - Incluye indicaciones de PROMPT IA: en inglés en cada escena clave.
    """
    
    max_reintentos = 3
    for intento in range(max_reintentos):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            if intento == max_reintentos - 1:
                return {"error": f"Fallo al generar paquete de YouTube: {e}"}
            import time
            time.sleep(2)

def generar_guion_short_paquete(analisis: dict) -> dict:
    """
    Genera un paquete exclusivo para YouTube Shorts (1 Minuto / Formato Vertical 9:16):
    - Título del Short.
    - Hashtags optimizados.
    - Prompts visuales verticales (--ar 9:16).
    - Guion ultrarrápido de 60 segundos (~140 palabras).
    """
    client = get_gemini_client()
    if not client:
        return {"error": "GEMINI_API_KEY no configurada."}
    
    model_name = get_gemini_model_name()
    
    prompt = f"""
    Actúa como un creador humano de YouTube Shorts experto en divulgación de IA y tecnología.
    Transforma el siguiente informe en un GUION Y PAQUETE PARA YOUTUBE SHORT DE 1 MINUTO (Formato Vertical 9:16, máximo 140 palabras en narración).
    
    REGLAS DE TONO:
    - Tono fresco, conversacional, sin clichés de IA ('En un mundo donde...', 'Sumérgete en...').
    - Destaca con energía cuando el avance tecnológico solucione un problema o beneficie a la gente.
    
    INFORME BASE:
    - Fuente: {analisis.get('fuente_original')}
    - Resumen: {analisis.get('resumen_ejecutivo')}
    - Narrativa: {analisis.get('narrativa_principal')}
    
    DEBES RESPONDER ÚNICA Y EXCLUSIVAMENTE CON UN JSON VÁLIDO CON LA SIGUIENTE ESTRUCTURA (SIN TEXTO ADICIONAL):
    
    {{
        "titulo_short": "Título ultrallamativo para Short (máximo 60 caracteres con emojis)",
        "hashtags": "#Shorts #IA #TechNews #Geopolitica #Innovacion",
        "prompts_visuales_916": [
            "Prompt 1 en inglés vertical: Vertical cinematic portrait, 8k, hyperrealistic, vibrant aesthetic, [concepto], --ar 9:16",
            "Prompt 2 en inglés vertical: ...",
            "Prompt 3 en inglés vertical: ..."
        ],
        "guion_short": "Markdown del Short de 60 segundos divididos en: [0-5s HOOK], [5-35s NOTICIA CLAVE], [35-50s IMPACTO POSITIVO/FUTURO], [50-60s CTA]. Usar VOZ EN OFF: y CORTE VISUAL (9:16):"
    }}
    """
    
    max_reintentos = 3
    for intento in range(max_reintentos):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            if intento == max_reintentos - 1:
                return {"error": f"Fallo al generar Short: {e}"}
            import time
            time.sleep(2)

# Mantener compatibilidad con la función anterior
def generar_guion_youtube(analisis: dict) -> str:
    res = generar_guion_youtube_paquete(analisis)
    if "error" in res:
        return res["error"]
    return res.get("guion_completo", "No se pudo recuperar el guion.")

# =====================================================================
# 5. Cabecera de la Aplicación
# =====================================================================
head_left, head_right = st.columns([10, 2])
with head_left:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;'>
        <div style='background: #2563eb; width: 14px; height: 14px; border-radius: 3px;'></div>
        <span style='font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em;'>SOCIEDAD 5.0 — INTEL & MEDIA ENGINE</span>
    </div>
    <div style='color: #71717a; font-size: 0.85rem; margin-top: -0.2rem;'>
        Plataforma de inteligencia geopolítica, producción de guiones de 10 min, Shorts diarios y crawling global.
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
tab_explorar, tab_shorts, tab_nuevo_analisis, tab_ingesta_automatica = st.tabs([
    "🔍 Guion YouTube (Largo)", 
    "📱 Shorts de IA (1 Minuto)",
    "⚙️ Procesar Nuevo Documento", 
    "📡 Ingesta Automática"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: EXPLORADOR DE INFORMES Y GUIONES DE VIDEO LARGO
# ---------------------------------------------------------------------
with tab_explorar:
    if not lista_reportes:
        st.info("No se encontraron análisis en la base de datos Firestore. Ve a la pestaña 'Procesar Nuevo Documento' para ingresar el primero.")
    else:
        # Fila de KPIs
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        total_reportes = len(lista_reportes)
        promedio_impacto = sum([r.get("nivel_impacto", 0) for r in lista_reportes]) / total_reportes
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
        selected_key = st.selectbox("Selecciona un informe para explorar y generar paquete de YouTube Largo:", list(opciones_reportes.keys()), key="select_largo")
        
        if selected_key:
            reporte_selec = opciones_reportes[selected_key]
            
            # Layout del reporte
            st.markdown("<div class='report-detail-card'>", unsafe_allow_html=True)
            narrativa_val = reporte_selec.get('narrativa_principal', 'No especificada')
            impacto_val = reporte_selec.get('nivel_impacto', 1)
            
            st.markdown(f"""
            <div style='margin-bottom: 1rem;'>
                <span class='report-badge badge-narrative'>🎬 {narrativa_val}</span>
                <span class='report-badge badge-impact'>🔥 Impacto: {impacto_val}/10</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"### {reporte_selec.get('fuente_original')}")
            
            fecha_cr = reporte_selec.get('fecha_creacion')
            if fecha_cr:
                fecha_str = fecha_cr.strftime("%B %d, %Y - %H:%M UTC") if isinstance(fecha_cr, datetime) else str(fecha_cr)
                st.markdown(f"<p style='color: var(--text-dim); font-size:0.75rem; margin-top:-0.5rem;'>Analizado el {fecha_str}</p>", unsafe_allow_html=True)
            
            col_izq, col_der = st.columns([7, 5])
            with col_izq:
                st.markdown("**Resumen Ejecutivo:**")
                st.markdown(f"<p style='line-height:1.6; color: var(--text);'>{reporte_selec.get('resumen_ejecutivo')}</p>", unsafe_allow_html=True)
                st.markdown("**Enfoque Narrativo (Justificación para Video):**")
                st.markdown(f"<p style='line-height:1.6; color: var(--text-muted); font-style: italic;'>{reporte_selec.get('explicacion_narrativa')}</p>", unsafe_allow_html=True)
                
            with col_der:
                st.markdown("**Citas Verificables Extraídas:**")
                for cita in reporte_selec.get('citas_verificables', []):
                    st.markdown(f"<blockquote style='border-left: 3px solid var(--border); padding-left: 0.8rem; margin-left: 0.5rem; font-size: 0.82rem; color: var(--text-muted);'>\"{cita}\"</blockquote>", unsafe_allow_html=True)
                
                st.markdown("**Enlaces y Fuentes Citadas:**")
                enlaces = reporte_selec.get('enlaces_fuentes', [])
                if enlaces:
                    for link in enlaces:
                        st.markdown(f"🌐 [{link}]({link})", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: var(--text-dim); font-size:0.8rem;'>No se detectaron enlaces web en el reporte.</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🎬 Generar Paquete Completo para YouTube Studio (10 Minutos)")
            st.info("Produce automáticamente: Títulos CTR, Descripción SEO con Timestamps, Etiquetas y Prompts Visuales de IA en 16:9.")
            
            btn_guion = st.button("Generar Paquete Completo para YouTube Largo 🚀", type="primary", use_container_width=True, key="btn_youtube_largo")
            
            if btn_guion:
                with st.spinner("Gemini 3.5 Flash creando el paquete de contenido para YouTube..."):
                    pkg = generar_guion_youtube_paquete(reporte_selec)
                
                if "error" in pkg:
                    st.error(pkg["error"])
                else:
                    st.success("¡Paquete completo generado exitosamente!")
                    
                    subtab_titulos, subtab_desc, subtab_tags, subtab_prompts, subtab_guion = st.tabs([
                        "📌 Títulos CTR", 
                        "📝 Descripción SEO", 
                        "🏷️ Etiquetas (Tags)", 
                        "🎨 Prompts IA (16:9)",
                        "📄 Guion Completo"
                    ])
                    
                    with subtab_titulos:
                        st.markdown("### 🎯 Opción de Títulos Persuasivos (Prueba A/B):")
                        for idx, tit in enumerate(pkg.get("titulos", [])):
                            st.text_input(f"Opción {idx+1}:", value=tit, key=f"tit_largo_{idx}")
                            
                    with subtab_desc:
                        st.markdown("### 📝 Descripción Lista para Copiar:")
                        st.text_area("Copia esto directamente a YouTube Studio:", value=pkg.get("descripcion_seo", ""), height=250, key="desc_largo")
                        
                    with subtab_tags:
                        st.markdown("### 🏷️ Etiquetas (Tags):")
                        st.text_area("Copia y pega en la sección de Etiquetas:", value=pkg.get("etiquetas", ""), height=100, key="tags_largo")
                        
                    with subtab_prompts:
                        st.markdown("### 🎨 Prompts Visuales para Midjourney / Flux / Runway (16:9):")
                        for idx, pmt in enumerate(pkg.get("prompts_visuales", [])):
                            st.text_input(f"Prompt IA Scene {idx+1}:", value=pmt, key=f"pmt_largo_{idx}")
                            
                    with subtab_guion:
                        st.markdown("### 📜 Guion Literario Completo (10 Min):")
                        guion_txt = pkg.get("guion_completo", "")
                        st.markdown(guion_txt)
                        st.download_button(
                            label="📥 Descargar Paquete Completo (.md)",
                            data=f"# PAQUETE YOUTUBE\n\n## TÍTULOS\n" + "\n".join(pkg.get("titulos", [])) + f"\n\n## DESCRIPCIÓN SEO\n{pkg.get('descripcion_seo')}\n\n## ETIQUETAS\n{pkg.get('etiquetas')}\n\n## GUION COMPLETO\n{guion_txt}",
                            file_name=f"paquete_youtube_{reporte_selec.get('id')[:6]}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

# ---------------------------------------------------------------------
# PESTAÑA 2: NUEVO MÓDULO DE SHORTS DE IA (1 MINUTO / DIARIO)
# ---------------------------------------------------------------------
with tab_shorts:
    st.subheader("📱 Motor de Creación para YouTube Shorts (1 Minuto / Diario)")
    st.write("Selecciona cualquier reporte de Firestore y genera al instante un Short de 60 segundos con formato vertical (9:16), ritmo acelerado y prompts visuales listos para publicación diaria.")
    
    if not lista_reportes:
        st.info("Ingresa o descarga primero un informe en Firestore para generar Shorts.")
    else:
        opciones_shorts = {f"[{r.get('nivel_impacto')} HP] - {r.get('fuente_original')} - ID: {r.get('id')[:6]}": r for r in lista_reportes}
        selected_short_key = st.selectbox("Selecciona informe para Short:", list(opciones_shorts.keys()), key="select_short")
        
        if selected_short_key:
            reporte_short = opciones_shorts[selected_short_key]
            
            st.markdown(f"**Fuente Seleccionada:** {reporte_short.get('fuente_original')} | **Narrativa:** {reporte_short.get('narrativa_principal')}")
            
            btn_gen_short = st.button("Generar YouTube Short de 1 Minuto ⚡", type="primary", use_container_width=True, key="btn_short_action")
            
            if btn_gen_short:
                with st.spinner("Gemini 3.5 Flash condensando el informe en un Short vertical de 60 segundos..."):
                    pkg_short = generar_guion_short_paquete(reporte_short)
                    
                if "error" in pkg_short:
                    st.error(pkg_short["error"])
                else:
                    st.success("¡Short generado exitosamente!")
                    
                    st.markdown(f"### 📌 Título del Short: `{pkg_short.get('titulo_short')}`")
                    st.markdown(f"**Hashtags:** `{pkg_short.get('hashtags')}`")
                    
                    s_col1, s_col2 = st.columns([7, 5])
                    with s_col1:
                        st.markdown("#### 📜 Guion Literario de 60 Segundos:")
                        st.markdown(pkg_short.get("guion_short", ""))
                        
                    with s_col2:
                        st.markdown("#### 📱 Prompts Visuales Verticals (9:16):")
                        for idx, p916 in enumerate(pkg_short.get("prompts_visuales_916", [])):
                            st.text_area(f"Prompt Vertical {idx+1} (--ar 9:16):", value=p916, height=90, key=f"short_pmt_{idx}")
                            
                    st.download_button(
                        label="📥 Descargar Guion de Short (.md)",
                        data=f"# SHORT: {pkg_short.get('titulo_short')}\n\nHashtags: {pkg_short.get('hashtags')}\n\n## GUION\n{pkg_short.get('guion_short')}\n\n## PROMPTS 9:16\n" + "\n".join(pkg_short.get("prompts_visuales_916", [])),
                        file_name=f"short_youtube_{reporte_short.get('id')[:6]}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

# ---------------------------------------------------------------------
# PESTAÑA 3: PROCESAR NUEVO DOCUMENTO
# ---------------------------------------------------------------------
with tab_nuevo_analisis:
    st.subheader("Ingresa un nuevo reporte para análisis")
    st.write("Copia y pega un reporte económico, político o tecnológico. El motor utilizará Gemini para extraer la información y clasificarla en Firestore.")
    
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
                    analisis_resultado = analizar_reporte_con_gemini(nuevo_texto)
                    st.success("¡Análisis estructurado por Gemini exitosamente!")
                    st.json(analisis_resultado)
                    
                    with st.spinner("Guardando en la base de datos Firestore ('socidad50')..."):
                        doc_id = guardar_en_firestore(db, analisis_resultado)
                        
                    st.success(f"Análisis guardado con éxito. ID de documento: {doc_id}")
                    st.toast("Actualizando panel con el nuevo reporte...")
                    st.rerun()
                    
                except Exception as err:
                    st.error(f"Ocurrió un fallo en el procesamiento: {err}")

# ---------------------------------------------------------------------
# PESTAÑA 4: INGESTA AUTOMÁTICA DE FUENTES GLOBALES
# ---------------------------------------------------------------------
with tab_ingesta_automatica:
    st.subheader("📡 Búsqueda y Descarga Automática de Fuentes Globales")
    st.write(
        "Rastrea de forma autónoma revistas académicas, portales tecnológicos y medios de prensa mundial "
        "(arXiv, IEEE Spectrum, Nature, MIT, TechCrunch, Wired) para guardar análisis en Firestore."
    )
    
    col_f1, col_f2, col_f3 = st.columns([4, 4, 2])
    with col_f1:
        fuente_opcion = st.selectbox(
            "Selecciona la fuente o categoría de búsqueda:",
            [
                "Todas las fuentes (Consolidado Global)",
                "Universidades & Ciencia (arXiv, IEEE Spectrum, Nature, MIT)",
                "Prensa Tech Global (TechCrunch, Wired, VentureBeat)",
                "Organismos & Coyuntura Global (BBC Tech, WEF)"
            ]
        )
    with col_f2:
        palabra_clave_busqueda = st.text_input("Filtrar por palabra clave (opcional):", placeholder="ej. quantum, humanoid, agent, LLM...")
    with col_f3:
        limite_busqueda = st.number_input("Límite de resultados:", min_value=1, max_value=10, value=3)
        
    btn_rastrear = st.button("Rastrear, Analizar y Guardar en Firestore ⚡", type="primary", use_container_width=True, key="btn_ingest_exec")
    
    if btn_rastrear:
        fuente_key = fuente_opcion.lower()
            
        with st.spinner(f"Consultando fuentes en '{fuente_opcion}'..."):
            from ingest import buscar_documentos_remotos
            documentos_encontrados = buscar_documentos_remotos(fuente_key, palabra_clave_busqueda, limite_busqueda)
            
        if not documentos_encontrados:
            st.warning("No se encontraron documentos o artículos recientes con los filtros aplicados.")
        else:
            st.success(f"¡Se recuperaron {len(documentos_encontrados)} documentos con éxito!")
            
            for idx, doc in enumerate(documentos_encontrados):
                st.markdown(f"---")
                st.markdown(f"### Documento {idx+1}: {doc['titulo']}")
                st.markdown(f"**Fuente:** {doc['fuente']} | **Fecha:** {doc['fecha']} | [Enlace Oficial]({doc['enlace']})")
                
                texto_a_analizar = f"""
                TÍTULO: {doc['titulo']}
                AUTORES: {doc['autores']}
                FECHA: {doc['fecha']}
                ENLACE: {doc['enlace']}
                
                RESUMEN/TEXTO ORIGINAL:
                {doc['resumen']}
                """
                
                with st.expander("Ver contenido original recuperado", expanded=False):
                    st.text(doc['resumen'])
                
                with st.spinner(f"Gemini 3.5 Flash analizando documento {idx+1}..."):
                    try:
                        analisis_resultado = analizar_reporte_con_gemini(texto_a_analizar)
                        
                        if doc['enlace'] not in analisis_resultado.get('enlaces_fuentes', []):
                            analisis_resultado.setdefault('enlaces_fuentes', []).append(doc['enlace'])
                            
                        st.json(analisis_resultado)
                        doc_id = guardar_en_firestore(db, analisis_resultado)
                        st.success(f"¡Análisis estructurado y guardado en Firestore! ID: {doc_id}")
                        
                    except Exception as e:
                        st.error(f"Error al analizar el documento {idx+1}: {e}")
            
            st.toast("¡Procesamiento en lote completado!")
            st.rerun()

