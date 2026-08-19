import os
import json
import base64
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from google import genai
from google.genai import types
from main import inicializar_firebase, analizar_reporte_con_gemini, guardar_en_firestore, guardar_paquete_guion_firestore

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
# 2. Inyección de Estilos CSS Personalizados (Diseño Ultra-Premium / Command Center)
# =====================================================================
css_variables = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">

<style>
:root {{
    --bg: {"#09090b" if IS_DARK else "#f8fafc"};
    --bg-subtle: {"#0e0e12" if IS_DARK else "#f1f5f9"};
    --card: {"rgba(18, 18, 24, 0.75)" if IS_DARK else "#ffffff"};
    --card-solid: {"#121218" if IS_DARK else "#ffffff"};
    --card-hover: {"#171720" if IS_DARK else "#f1f5f9"};
    --border: {"rgba(255, 255, 255, 0.08)" if IS_DARK else "#e2e8f0"};
    --border-strong: {"rgba(255, 255, 255, 0.16)" if IS_DARK else "#cbd5e1"};
    --border-accent: {"rgba(37, 99, 235, 0.4)" if IS_DARK else "rgba(37, 99, 235, 0.5)"};
    --text: {"#f8fafc" if IS_DARK else "#0f172a"};
    --text-muted: {"#94a3b8" if IS_DARK else "#475569"};
    --text-dim: {"#64748b" if IS_DARK else "#64748b"};
    --accent: #2563eb;
    --accent-glow: rgba(37, 99, 235, 0.35);
    --shadow: {"0 12px 32px rgba(0, 0, 0, 0.5)" if IS_DARK else "0 4px 20px rgba(0, 0, 0, 0.06)"};
    --radius: 14px;
}}

/* Ocultar elementos nativos innecesarios de Streamlit */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Estilo global de la app */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}}

.block-container {{
    padding: 2.2rem 2.8rem 4rem !important;
    max-width: 1400px !important;
}}

/* Tipografía de código / mono */
code, pre, .stCodeBlock, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
    font-family: 'JetBrains Mono', monospace !important;
}}

/* Textos globales de Streamlit */
label, .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, div[data-testid="stMarkdownContainer"] p, div[data-testid="stWidgetLabel"] label, div[data-testid="stWidgetLabel"] p {{
    color: var(--text) !important;
}}

div[data-testid="stRadioButton"] label {{
    color: var(--text) !important;
    font-weight: 600 !important;
}}

/* Insignia Live Engine */
.live-badge {{
    background: {"rgba(16, 185, 129, 0.16)" if IS_DARK else "rgba(16, 185, 129, 0.12)"};
    color: {"#34d399" if IS_DARK else "#047857"};
    border: 1px solid {"rgba(16, 185, 129, 0.3)" if IS_DARK else "rgba(16, 185, 129, 0.4)"};
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}}

/* Contenedores de Tarjetas de Métricas KPI */
.metric-card {{
    background: var(--card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}
.metric-card:hover {{
    border-color: var(--border-accent);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; width: 4px; height: 100%;
    background: linear-gradient(180deg, #2563eb, #3b82f6);
    border-radius: 4px 0 0 4px;
}}
.metric-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.metric-value {{
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.03em;
    margin-top: 0.3rem;
}}
.metric-value-accent {{
    font-size: 1.35rem;
    font-weight: 800;
    margin-top: 0.6rem;
    color: {"#60a5fa" if IS_DARK else "#1d4ed8"};
}}

/* Tarjeta de Detalle del Reporte */
.report-detail-card {{
    background: var(--card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.2rem;
    box-shadow: var(--shadow);
    margin-top: 1.2rem;
    transition: border 0.3s ease;
}}
.report-detail-card:hover {{
    border-color: var(--border-strong);
}}

.report-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-family: 'JetBrains Mono', monospace;
}}
.badge-narrative {{
    background: {"rgba(37, 99, 235, 0.14)" if IS_DARK else "rgba(37, 99, 235, 0.1)"};
    color: {"#60a5fa" if IS_DARK else "#1d4ed8"};
    border: 1px solid {"rgba(59, 130, 246, 0.35)" if IS_DARK else "rgba(37, 99, 235, 0.35)"};
}}
.badge-impact {{
    background: {"rgba(239, 68, 68, 0.14)" if IS_DARK else "rgba(239, 68, 68, 0.1)"};
    color: {"#f87171" if IS_DARK else "#b91c1c"};
    border: 1px solid {"rgba(239, 68, 68, 0.35)" if IS_DARK else "rgba(239, 68, 68, 0.35)"};
}}

/* Formateo del guion de YouTube */
.script-hook-card {{
    background: {"rgba(239, 68, 68, 0.08)" if IS_DARK else "rgba(239, 68, 68, 0.04)"};
    border-left: 4px solid {"#ef4444" if IS_DARK else "#dc2626"};
    border-radius: 8px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(239, 68, 68, 0.1);
    color: var(--text);
}}
.script-section-header {{
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text);
    border-bottom: 2px solid var(--border);
    padding-bottom: 0.4rem;
    margin-top: 2.2rem;
    margin-bottom: 1.2rem;
    letter-spacing: -0.02em;
}}
.script-vo {{
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    font-size: 0.98rem;
    line-height: 1.75;
    color: var(--text);
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}}
.script-vo-label {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    color: {"#60a5fa" if IS_DARK else "#1d4ed8"};
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.script-production {{
    font-size: 0.85rem;
    background: {"rgba(24, 24, 27, 0.9)" if IS_DARK else "#f1f5f9"};
    color: var(--text-muted);
    border-left: 3px solid {"#64748b" if IS_DARK else "#94a3b8"};
    padding: 0.6rem 1rem;
    margin-bottom: 0.9rem;
    border-radius: 0 8px 8px 0;
}}
.script-sfx {{
    display: inline-block;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    background: {"rgba(245, 158, 11, 0.16)" if IS_DARK else "rgba(245, 158, 11, 0.12)"};
    color: {"#fbbf24" if IS_DARK else "#b45309"};
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 700;
    margin-bottom: 0.8rem;
    border: 1px solid {"rgba(245, 158, 11, 0.3)" if IS_DARK else "rgba(245, 158, 11, 0.4)"};
}}

/* Estilo para los botones principales y secundarios de Streamlit */
div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.4rem !important;
    box-shadow: 0 4px 18px rgba(37, 99, 235, 0.4) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
div.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 6px 24px rgba(37, 99, 235, 0.6) !important;
    transform: translateY(-1px) !important;
}}
div.stButton > button[kind="primary"]:active {{
    transform: scale(0.98) !important;
}}

div.stButton > button[kind="secondary"] {{
    background: var(--card-solid) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1.2rem !important;
    transition: all 0.2s ease !important;
}}
div.stButton > button[kind="secondary"]:hover {{
    background: var(--card-hover) !important;
    border-color: var(--border-accent) !important;
    color: var(--text) !important;
}}

/* Botones de Descarga de Streamlit */
div.stDownloadButton > button {{
    background: linear-gradient(135deg, #059669, #047857) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.7rem 1.4rem !important;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35) !important;
    transition: all 0.2s ease !important;
}}
div.stDownloadButton > button:hover {{
    background: linear-gradient(135deg, #10b981, #059669) !important;
    box-shadow: 0 6px 22px rgba(16, 185, 129, 0.5) !important;
    transform: translateY(-1px) !important;
}}

/* Estilo para los Pestañas (Tabs) de Streamlit */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.4rem !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}}
button[data-baseweb="tab"]:hover {{
    color: var(--text) !important;
    background: rgba(125, 125, 125, 0.08) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card-solid) !important;
    border: 1px solid var(--border-strong) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 6px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 4px;
}}

/* Inputs, Textareas y Selectboxes */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {{
    background-color: {"#121218" if IS_DARK else "#ffffff"} !important;
    border: 1px solid {"rgba(255, 255, 255, 0.16)" if IS_DARK else "#cbd5e1"} !important;
    border-radius: 12px !important;
    transition: border-color 0.2s ease !important;
}}

div[data-baseweb="select"] *,
div[data-baseweb="input"] *,
div[data-baseweb="textarea"] *,
.stSelectbox *,
.stTextInput input,
.stTextArea textarea {{
    color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
    -webkit-text-fill-color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
    fill: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
}}

input::placeholder, textarea::placeholder {{
    color: {"#94a3b8" if IS_DARK else "#64748b"} !important;
    -webkit-text-fill-color: {"#94a3b8" if IS_DARK else "#64748b"} !important;
}}

div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}}

/* Desplegables Selectbox Dropdown (Menu Flotante Popover) */
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"],
div[data-baseweb="menu"] *,
ul[data-baseweb="menu"],
ul[data-baseweb="menu"] *,
ul[role="listbox"],
ul[role="listbox"] * {{
    background-color: {"#121218" if IS_DARK else "#ffffff"} !important;
    color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
    -webkit-text-fill-color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
}}

li[role="option"],
div[role="option"] {{
    background-color: {"#121218" if IS_DARK else "#ffffff"} !important;
    color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
    -webkit-text-fill-color: {"#f8fafc" if IS_DARK else "#0f172a"} !important;
}}

li[role="option"]:hover,
li[role="option"][aria-selected="true"],
div[role="option"]:hover,
div[role="option"][aria-selected="true"] {{
    background-color: {"#222230" if IS_DARK else "#e2e8f0"} !important;
    color: {"#60a5fa" if IS_DARK else "#1d4ed8"} !important;
    -webkit-text-fill-color: {"#60a5fa" if IS_DARK else "#1d4ed8"} !important;
}}

/* Expanders */
.streamlit-expanderHeader {{
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}}
.streamlit-expanderContent {{
    background-color: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    color: var(--text) !important;
}}

blockquote {{
    border-left: 3px solid var(--border-accent) !important;
    padding: 0.6rem 1rem !important;
    margin: 0.6rem 0 !important;
    background: var(--bg-subtle) !important;
    border-radius: 0 8px 8px 0 !important;
    font-size: 0.9rem !important;
    color: var(--text-muted) !important;
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
    Actúa como un analista y guionista senior de YouTube de periodismo científico e investigación tecnológica (estilo periodista riguroso con opinión fundada, como Veritasium o VisualPolitik).
    Tu tarea es transformar el siguiente informe en un PAQUETE COMPLETO DE PUBLICACIÓN Y GUION PARA YOUTUBE (Video Largo 8-10 Minutos).
    
    LÍNEA EDITORIAL Y TESIS CENTRAL DEL CANAL (OBLIGATORIA):
    "Sociedad 5.0 — Sensibilización sobre el nuevo paradigma emergente y la transición indispensable desde el tecnocentrismo hacia el bienestar humano."
    
    DIRECTRICES PERIODÍSTICAS Y DE TONO (ESTRICTAS):
    1. PERIODISMO DE DOS CARAS ("AMBAS CARAS DE LA MONEDA"): No seas un mero propagandista ni tampoco un alarmista apocalíptico. Analiza rigurosamente tanto el potencial transformador y las oportunidades reales como los riesgos socioeconómicos, éticos, de empleo o soberanía tecnológica.
    2. ESTADO DE MADUREZ DE LA TECNOLOGÍA: Debes aclarar explícitamente en el guion si la noticia trata sobre un producto comercial ya en el mercado, un prototipo funcional, un estudio científico/paper de laboratorio o una propuesta conceptual, e indicar si es posible "conseguir/usar" la tecnología hoy en día o dónde consultar el avance.
    3. POSTURA HUMANA Y SUBJETIVA (SENTAR POSICIÓN): Como canal, sienta una postura firme: la tecnología solo tiene sentido si mejora genuinamente la calidad de vida y el bienestar humano. Cuestiona la fascinación puramente tecnocéntrica.
    4. TONO NATURAL SIN CLICHÉS DE IA: Prohibido usar expresiones como 'En un mundo donde...', 'Sumérgete en...', 'En la era digital...', 'Es fundamental destacar...', 'Un testimonio de...', 'Desentrañar...', 'En conclusión...'. Escribe con el ritmo, fluidez y cercanía de un profesional real.
    
    DATOS DEL INFORME:
    - Fuente Original: {analisis.get('fuente_original')}
    - Resumen Ejecutivo: {analisis.get('resumen_ejecutivo')}
    - Impacto: {analisis.get('nivel_impacto')}/10
    - Citas: {", ".join(analisis.get('citas_verificables', []))}
    - Fuentes: {", ".join(analisis.get('enlaces_fuentes', []))}
    - Narrativa: {analisis.get('narrativa_principal')}
    - Explicación: {analisis.get('explicacion_narrativa')}
    
    DEBES RESPONDER ÚNICA Y EXCLUSIVAMENTE CON UN OBJETO JSON VÁLIDO CON LA SIGUIENTE ESTRUCTURA EXACTA:
    
    {{
        "titulos": [
            "Título 1 CTR (Dilema o revelar la promesa vs la realidad)",
            "Título 2 CTR (Enfocado en impacto en el bienestar o futuro laboral)",
            "Título 3 CTR (Geopolítica o el gran cambio de paradigma)"
        ],
        "descripcion_seo": "Resumen periodístico para la descripción de YouTube.\\n\\n📌 CAPÍTULOS / MARCAS DE TIEMPO:\\n0:00 - El Gancho\\n0:30 - La Noticia y su Estado de Madurez (¿Producto o Estudio?)\\n2:00 - La Cara A: Avances y Soluciones\\n5:00 - La Cara B: Riesgos, Empleo y Ética\\n8:00 - Reflexión Sociedad 5.0 (Bienestar Humano)\\n9:30 - Cierre y Debate\\n\\n🔗 FUENTES OFICIALES:\\n" + ", ".join(analisis.get('enlaces_fuentes', [])) + "\\n\\n#IA #Tecnologia #Sociedad50 #BienestarHumano #Futuro",
        "etiquetas": "inteligencia artificial, sociedad 5.0, bienestar humano, periodismo tecnologico, futuro del trabajo, tecnologia, innovacion, geopolitica",
        "prompts_visuales": [
            "Prompt 1 en inglés para Midjourney/Flux: Cinematic 8k, hyperrealistic wide shot, warm natural lighting, human-centric technology focus, 35mm lens --ar 16:9",
            "Prompt 2 en inglés...",
            "Prompt 3 en inglés..."
        ],
        "guion_completo": "Markdown con el guion literario de 10 min estructurado con VOZ EN OFF:, APOYO VISUAL:, EFECTO DE SONIDO:, PROMPT IA:"
    }}
    
    REGLAS DEL GUION DENTRO DEL JSON:
    - Gancho inicial atrapante (30s) que plantea el dilema humano.
    - Presentación clara de la fuente y aclaración de si es un producto real o un estudio científico inicial.
    - Desarrollo en 2 bloques contrapuestos: Oportunidades (Cara A) vs Retos y Sombras (Cara B).
    - Reflexión central desde la perspectiva de la Sociedad 5.0 (bienestar humano sobre tecnocentrismo).
    - Cierre con llamado al debate en comentarios.
    - Prompts visuales en inglés (16:9) en cada escena clave.
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
    Actúa como un creador y analista periodístico de YouTube Shorts sobre tecnología e impacto social.
    Transforma el siguiente informe en un GUION Y PAQUETE PARA YOUTUBE SHORT DE 1 MINUTO (Formato Vertical 9:16, máximo 140 palabras).
    
    TESIS Y ENFOQUE DEL CANAL:
    "Sociedad 5.0: Pasar del tecnocentrismo al bienestar humano. Mostrar las dos caras de la noticia con visión periodística compacta."
    
    REGLAS DE TONO:
    1. DOS CARAS EN 60 SEGUNDOS: Enuncia la noticia rápida, menciona si es un producto real o un experimento/estudio, muestra la oportunidad y contrarréstala con el reto humano.
    2. POSTURA HUMANISTA: Cierra con una frase contundente que recuerde que la tecnología debe servir al bienestar humano.
    3. SIN CLICHÉS DE IA: Prohibido 'En un mundo donde...', 'Sumérgete en...', etc.
    
    INFORME BASE:
    - Fuente: {analisis.get('fuente_original')}
    - Resumen: {analisis.get('resumen_ejecutivo')}
    - Narrativa: {analisis.get('narrativa_principal')}
    
    DEBES RESPONDER ÚNICA Y EXCLUSIVAMENTE CON UN JSON VÁLIDO CON LA SIGUIENTE ESTRUCTURA:
    
    {{
        "titulo_short": "Título llamativo para Short (máx 60 caracteres con emojis)",
        "hashtags": "#Shorts #IA #Sociedad50 #BienestarHumano #TechNews",
        "prompts_visuales_916": [
            "Prompt 1 vertical en inglés: Vertical cinematic portrait, 8k, hyperrealistic, warm human aesthetic, --ar 9:16",
            "Prompt 2 vertical en inglés: ...",
            "Prompt 3 vertical en inglés: ..."
        ],
        "guion_short": "Markdown del Short de 60s divididos en: [0-5s HOOK DILEMA], [5-25s LA NOTICIA (¿Producto o Estudio?)], [25-45s LAS DOS CARAS (Promesa vs Riesgo)], [45-60s POSTURA SOCIEDAD 5.0 Y CTA]. Usar VOZ EN OFF: y CORTE VISUAL (9:16):"
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


import re
import html
import streamlit.components.v1 as components

def extraer_narracion_limpia(guion_texto: str) -> str:
    """
    Filtra y extrae únicamente el texto hablado (locución/voz en off)
    eliminando indicaciones técnicas, prompts visuales, SFX y marcadores de producción.
    """
    if not guion_texto:
        return ""
    
    lineas = guion_texto.split("\n")
    narracion = []
    
    for linea in lineas:
        l = linea.strip()
        if not l:
            continue
        
        # Omitir headers o secciones de apoyo técnico
        if any(kw in l.upper() for kw in [
            "APOYO VISUAL", "B-ROLL", "PROMPT IA", "EFECTO DE SONIDO", "SFX:", 
            "CORTE VISUAL", "CAPÍTULO", "TITULOS", "DESCRIPCIÓN", "ETIQUETAS",
            "HASHTAGS", "---", "###", "##", "# ", "VOZ EN OFF (LOCUCIÓN)"
        ]):
            continue
            
        # Extraer locución si contiene prefijo de voz
        if "VOZ EN OFF:" in l.upper() or "VO:" in l.upper():
            clean = re.sub(r'^(VOZ EN OFF|VO|🎙️ VOZ EN OFF):\s*', '', l, flags=re.IGNORECASE).strip()
            if clean:
                narracion.append(clean)
        else:
            # Si es texto plano de locución (sin etiquetas de producción ni corchetes)
            if not l.startswith("[") and not l.startswith("*") and len(l) > 8:
                narracion.append(l)
                
    return "\n\n".join(narracion) if narracion else guion_texto

def generar_html_teleprompter_standalone(narracion_limpia: str, titulo: str) -> str:
    """Genera una aplicación web HTML5 independiente para Teleprompter con soporte de grabación de video y conteo regresivo de 5s."""
    parrafos_html = "".join([f"<p style='margin-bottom: 2rem;'>{html.escape(p)}</p>" for p in narracion_limpia.split("\n\n") if p.strip()])
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Studio Teleprompter - {html.escape(titulo)}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body, html {{ width: 100%; height: 100%; overflow: hidden; background: #09090b; font-family: system-ui, -apple-system, sans-serif; color: #fff; touch-action: manipulation; }}
        
        #webcam {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover; z-index: 1; transform: scaleX(-1);
            -webkit-transform: scaleX(-1);
        }}
        #webcam.no-mirror {{ transform: none; -webkit-transform: none; }}
        
        #overlay {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.65); z-index: 2; pointer-events: none;
            transition: background 0.3s ease;
        }}
        
        #prompter-box {{
            position: absolute; top: 0; left: 50%; transform: translateX(-50%);
            width: 88%; max-width: 900px; height: 100%; z-index: 3;
            overflow-y: scroll; scroll-behavior: auto;
            padding: 40vh 1.5rem 50vh; scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
        }}
        #prompter-box::-webkit-scrollbar {{ display: none; }}
        
        #prompter-box.mode-916 {{
            width: 92vw; max-width: 420px;
            border-left: 2px dashed rgba(37, 99, 235, 0.4);
            border-right: 2px dashed rgba(37, 99, 235, 0.4);
        }}
        
        .script-content {{
            font-size: 34px; font-weight: 700; line-height: 1.6;
            text-align: center; color: #ffffff; text-shadow: 0 3px 12px rgba(0,0,0,0.95);
            transition: font-size 0.2s ease; word-break: break-word;
        }}
        .script-content.mirrored {{
            transform: scaleX(-1); -webkit-transform: scaleX(-1);
        }}
        
        #controls-bar {{
            position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
            z-index: 100; background: rgba(18, 18, 24, 0.95); backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.2); border-radius: 24px;
            padding: 10px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.9); transition: opacity 0.4s ease;
            width: 94vw; max-width: 900px; max-height: 50vh; overflow-y: auto;
        }}
        #controls-bar:hover, body.paused #controls-bar {{ opacity: 1; }}
        body.playing #controls-bar {{ opacity: 0.4; }}

        .btn {{
            background: #2563eb; color: white; border: none; padding: 10px 16px;
            border-radius: 20px; font-weight: 700; cursor: pointer; font-size: 13px;
            display: flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s;
            min-height: 44px; touch-action: manipulation; -webkit-tap-highlight-color: transparent;
        }}
        .btn:active {{ transform: scale(0.96); }}
        .btn-main {{ background: #2563eb; flex: 1 1 auto; }}
        .btn-main:hover {{ background: #1d4ed8; }}
        .btn-countdown {{ background: linear-gradient(135deg, #ef4444, #dc2626); color: white; flex: 1 1 auto; box-shadow: 0 4px 12px rgba(239,68,68,0.4); }}
        .btn-countdown:hover {{ background: linear-gradient(135deg, #dc2626, #b91c1c); }}
        .btn-rec {{ background: #dc2626; color: white; }}
        .btn-rec.recording {{ background: #991b1b; animation: pulse-rec 1s infinite alternate; }}
        .btn-download {{ background: #10b981; color: white; box-shadow: 0 4px 12px rgba(16,185,129,0.4); }}
        .btn-download:hover {{ background: #059669; }}
        .btn-sec {{ background: rgba(255,255,255,0.15); color: #fff; }}
        .btn-sec:hover {{ background: rgba(255,255,255,0.25); }}

        .ctrl-group {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #ccc; background: rgba(255,255,255,0.06); padding: 4px 10px; border-radius: 12px; }}
        input[type="range"] {{ accent-color: #2563eb; cursor: pointer; height: 30px; }}

        #rec-indicator {{
            position: fixed; top: 16px; right: 16px; z-index: 100;
            background: rgba(220, 38, 38, 0.9); color: white; padding: 6px 14px;
            border-radius: 20px; font-size: 14px; font-weight: 800;
            display: none; align-items: center; gap: 8px; box-shadow: 0 4px 14px rgba(220, 38, 38, 0.6);
            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        }}
        .dot-pulse {{
            width: 10px; height: 10px; background: white; border-radius: 50%;
            animation: pulse-dot 0.8s infinite alternate;
        }}

        #countdown-overlay {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.88); z-index: 1000; display: none;
            flex-direction: column; align-items: center; justify-content: center;
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        }}
        #countdown-number {{
            font-size: 140px; font-weight: 900; color: #ef4444;
            text-shadow: 0 0 50px rgba(239, 68, 68, 0.8);
            animation: zoom-pulse 0.9s infinite;
        }}

        #cam-status {{
            position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 100;
            background: rgba(220, 38, 38, 0.9); color: white; padding: 8px 16px;
            border-radius: 20px; font-size: 13px; font-weight: 700; display: none;
            align-items: center; gap: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.5);
        }}

        body.is-fullscreen {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 99999999 !important;
            background: #09090b !important;
        }}

        body.is-fullscreen #controls-bar {{
            bottom: 20px !important;
        }}

        @keyframes pulse-dot {{ from {{ opacity: 0.3; transform: scale(0.8); }} to {{ opacity: 1; transform: scale(1.2); }} }}
        @keyframes pulse-rec {{ from {{ background: #dc2626; }} to {{ background: #7f1d1d; }} }}
        @keyframes zoom-pulse {{ 0% {{ transform: scale(0.6); opacity: 0.3; }} 50% {{ transform: scale(1.1); opacity: 1; }} 100% {{ transform: scale(1); opacity: 0.9; }} }}

        @media (max-width: 768px) {{
            #controls-bar {{ bottom: 10px; padding: 8px; width: 96vw; gap: 5px; }}
            .btn {{ padding: 8px 10px; font-size: 12px; min-height: 42px; flex: 1 1 auto; }}
            .ctrl-group {{ flex: 1 1 45%; justify-content: space-between; font-size: 11px; }}
            .script-content {{ font-size: 26px; }}
            #prompter-box {{ padding: 30vh 1rem 40vh; width: 96%; }}
            #countdown-number {{ font-size: 100px; }}
        }}
    </style>
</head>
<body class="paused">
    <video id="webcam" autoplay playsinline webkit-playsinline muted></video>
    <div id="overlay"></div>
    
    <div id="cam-status">
        <span id="cam-status-msg">⚠️ Tu navegador no admite cámara en esta ventana. Usa el Visor Integrado.</span>
    </div>

    <div id="rec-indicator">
        <div class="dot-pulse"></div>
        <span id="rec-timer-text">🔴 REC 00:00</span>
    </div>

    <div id="countdown-overlay">
        <div id="countdown-number">5</div>
        <div style="font-size: 20px; color: #fff; font-weight: 700; margin-top: 15px;">Preparado... Iniciarás a hablar en breve</div>
    </div>
    
    <div id="prompter-box">
        <div id="text-node" class="script-content">{parrafos_html}</div>
    </div>
    
    <div id="controls-bar">
        <button id="btn-countdown-rec" class="btn btn-countdown">⏱️ Conteo (5s) + Grabar y Mover</button>
        <button id="btn-toggle" class="btn btn-main">▶️ INICIAR SCROLL</button>
        <button id="btn-rec-manual" class="btn btn-rec">🔴 Grabar Video</button>
        <button id="btn-download" class="btn btn-download" style="display: none;">💾 Descargar Video</button>
        
        <div class="ctrl-group">
            <label>⚡ Vel:</label>
            <input type="range" id="speed" min="1" max="15" value="4">
        </div>
        
        <div class="ctrl-group">
            <label>🔠 Texto:</label>
            <input type="range" id="fontsize" min="18" max="60" value="30">
        </div>

        <button id="btn-cam-toggle" class="btn btn-sec">📷 Activar Cámara</button>
        <button id="btn-mode" class="btn btn-sec">🖥️ 16:9 / 9:16</button>
        <button id="btn-mirror" class="btn btn-sec">🪞 Espejo</button>
        <button id="btn-reset" class="btn btn-sec">🔄 Inicio</button>
        <button id="btn-edit" class="btn btn-sec">✏️ Editar Texto</button>
        <button id="btn-fullscreen" class="btn btn-sec">⛶ Pantalla Completa</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const camStatus = document.getElementById('cam-status');
        const camStatusMsg = document.getElementById('cam-status-msg');
        const btnCamToggle = document.getElementById('btn-cam-toggle');
        
        let mediaStream = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let isRecording = false;
        let recTimer = null;
        let recSeconds = 0;
        let lastRecordedBlob = null;
        let lastRecordedUrl = null;

        async function startCamera() {{
            if (mediaStream) return true; // Ya está encendida

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                camStatus.style.display = 'flex';
                camStatusMsg.innerText = '⚠️ Tu navegador no admite cámara en esta ventana.';
                return false;
            }}

            const isVertical = box.classList.contains('mode-916') || (window.innerHeight > window.innerWidth);
            
            const audioConstraints = {{
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 48000,
                channelCount: 1
            }};

            const tryConstraints = [
                // 1. Full HD (1080p) con relación de aspecto explícita (9:16 vertical o 16:9 horizontal)
                {{
                    video: {{
                        facingMode: 'user',
                        width: {{ ideal: isVertical ? 1080 : 1920 }},
                        height: {{ ideal: isVertical ? 1920 : 1080 }},
                        aspectRatio: {{ ideal: isVertical ? (9/16) : (16/9) }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }},
                    audio: audioConstraints
                }},
                // 2. HD (720p) con relación de aspecto
                {{
                    video: {{
                        facingMode: 'user',
                        width: {{ ideal: isVertical ? 720 : 1280 }},
                        height: {{ ideal: isVertical ? 1280 : 720 }},
                        aspectRatio: {{ ideal: isVertical ? (9/16) : (16/9) }},
                        frameRate: {{ ideal: 30, max: 30 }}
                    }},
                    audio: audioConstraints
                }},
                // 3. Fallback inteligente con facingMode
                {{
                    video: {{ facingMode: 'user' }},
                    audio: audioConstraints
                }},
                // 4. Fallback básico universal
                {{
                    video: true,
                    audio: true
                }}
            ];

            mediaStream = null;
            for (const c of tryConstraints) {{
                try {{
                    mediaStream = await navigator.mediaDevices.getUserMedia(c);
                    if (mediaStream) break;
                }} catch(e) {{
                    console.warn("Constraint no soportado:", c, e);
                }}
            }}

            if (!mediaStream) {{
                camStatus.style.display = 'flex';
                camStatusMsg.innerText = '⚠️ Toca aquí para dar permiso a la cámara.';
                return false;
            }}

            video.srcObject = mediaStream;
            try {{
                await video.play();
            }} catch(e) {{
                console.log("Error en video.play():", e);
            }}
            camStatus.style.display = 'none';
            btnCamToggle.innerText = '🚫 Apagar Cámara';
            btnCamToggle.style.background = '#dc2626';
            return true;
        }}

        function stopCamera() {{
            if (mediaStream) {{
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }}
            if (video.srcObject) {{
                video.srcObject = null;
            }}
            camStatus.style.display = 'none';
            btnCamToggle.innerText = '📷 Activar Cámara';
            btnCamToggle.style.background = '';
        }}

        function toggleCamera() {{
            if (mediaStream) {{
                stopCamera();
            }} else {{
                startCamera();
            }}
        }}

        btnCamToggle.addEventListener('click', toggleCamera);

        // Limpiar cámara al cerrar la pestaña o cambiar de app
        document.addEventListener('visibilitychange', () => {{
            if (document.hidden && mediaStream && !isRecording) {{
                stopCamera();
            }}
        }});
        window.addEventListener('beforeunload', () => {{
            stopCamera();
        }});

        const box = document.getElementById('prompter-box');
        const textNode = document.getElementById('text-node');
        const btnToggle = document.getElementById('btn-toggle');
        const btnCountdownRec = document.getElementById('btn-countdown-rec');
        const btnRecManual = document.getElementById('btn-rec-manual');
        const btnDownload = document.getElementById('btn-download');
        const recIndicator = document.getElementById('rec-indicator');
        const recTimerText = document.getElementById('rec-timer-text');
        const countdownOverlay = document.getElementById('countdown-overlay');
        const countdownNumber = document.getElementById('countdown-number');
        
        const speedInput = document.getElementById('speed');
        const fontInput = document.getElementById('fontsize');
        const btnMode = document.getElementById('btn-mode');
        const btnMirror = document.getElementById('btn-mirror');
        const btnReset = document.getElementById('btn-reset');
        const btnEdit = document.getElementById('btn-edit');
        const btnFS = document.getElementById('btn-fullscreen');

        let isPlaying = false;
        let animId = null;
        let isEditingText = false;

        btnEdit.addEventListener('click', () => {{
            isEditingText = !isEditingText;
            if (isEditingText) {{
                pauseScroll();
                textNode.setAttribute('contenteditable', 'true');
                textNode.style.outline = '2px dashed #2563eb';
                textNode.style.padding = '12px';
                textNode.style.borderRadius = '12px';
                textNode.style.background = 'rgba(15, 23, 42, 0.75)';
                textNode.focus();
                btnEdit.innerText = '💾 Guardar Edición';
                btnEdit.style.background = '#059669';
            }} else {{
                textNode.setAttribute('contenteditable', 'false');
                textNode.style.outline = 'none';
                textNode.style.padding = '';
                textNode.style.background = '';
                btnEdit.innerText = '✏️ Editar Texto';
                btnEdit.style.background = '';
            }}
        }});

        function scrollStep() {{
            if (!isPlaying) return;
            box.scrollTop += parseFloat(speedInput.value) * 0.4;
            animId = requestAnimationFrame(scrollStep);
        }}

        function startScroll() {{
            if (isPlaying) return;
            isPlaying = true;
            document.body.classList.remove('paused');
            document.body.classList.add('playing');
            btnToggle.innerText = '⏸️ PAUSAR SCROLL';
            btnToggle.style.background = '#dc2626';
            scrollStep();
        }}

        function pauseScroll() {{
            if (!isPlaying) return;
            isPlaying = false;
            document.body.classList.remove('playing');
            document.body.classList.add('paused');
            btnToggle.innerText = '▶️ INICIAR SCROLL';
            btnToggle.style.background = '#2563eb';
            cancelAnimationFrame(animId);
        }}

        function togglePlay() {{
            if (isPlaying) {{
                pauseScroll();
                if (isRecording) {{
                    stopRecording();
                }}
            }} else {{
                startScroll();
            }}
        }}

        btnToggle.addEventListener('click', togglePlay);

        // --- FUNCIONES DE GRABACIÓN MEDIARECORDER (SINCRONIZACIÓN CAPCUT & 9:16 / 16:9) ---

        function getSupportedMimeType() {{
            const types = [
                'video/mp4;codecs=avc1.4d002a,mp4a.40.2',
                'video/mp4;codecs=avc1,mp4a.40.2',
                'video/mp4;codecs=avc1',
                'video/mp4',
                'video/webm;codecs=vp9,opus',
                'video/webm;codecs=vp8,opus',
                'video/webm'
            ];
            for (const t of types) {{
                if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)) {{
                    return t;
                }}
            }}
            return '';
        }}

        async function startRecording() {{
            if (isRecording) return;
            if (!mediaStream) {{
                await startCamera();
            }}
            if (!mediaStream) return;

            recordedChunks = [];
            const mimeType = getSupportedMimeType();
            const options = {{
                videoBitsPerSecond: 8000000,
                audioBitsPerSecond: 128000
            }};
            if (mimeType) {{
                options.mimeType = mimeType;
            }}

            try {{
                mediaRecorder = new MediaRecorder(mediaStream, options);
            }} catch(e) {{
                console.error("Error al instanciar MediaRecorder con opciones:", e);
                try {{
                    mediaRecorder = new MediaRecorder(mediaStream);
                }} catch(e2) {{
                    return console.warn("Grabación no soportada en este entorno.");
                }}
            }}

            mediaRecorder.ondataavailable = (e) => {{
                if (e.data && e.data.size > 0) {{
                    recordedChunks.push(e.data);
                }}
            }};

            mediaRecorder.onstop = () => {{
                const type = mediaRecorder.mimeType || (getSupportedMimeType().includes('mp4') ? 'video/mp4' : 'video/webm');
                lastRecordedBlob = new Blob(recordedChunks, {{ type }});
                if (lastRecordedUrl) URL.revokeObjectURL(lastRecordedUrl);
                lastRecordedUrl = URL.createObjectURL(lastRecordedBlob);
                
                btnDownload.style.display = 'flex';
                btnDownload.innerText = '💾 Descargar Video Grabado';
            }};

            // Grabación continua SIN timeslice para generar un contenedor unificado sin discontinuidades PTS/DTS
            mediaRecorder.start();
            isRecording = true;
            recSeconds = 0;
            updateRecTimerDisplay();
            
            recTimer = setInterval(() => {{
                recSeconds++;
                updateRecTimerDisplay();
            }}, 1000);

            recIndicator.style.display = 'flex';
            btnRecManual.innerText = '⏹️ Detener Grabación';
            btnRecManual.classList.add('recording');
        }}

        function stopRecording() {{
            if (!isRecording || !mediaRecorder) return;
            isRecording = false;
            clearInterval(recTimer);
            try {{
                if (mediaRecorder.state !== 'inactive') {{
                    mediaRecorder.stop();
                }}
            }} catch(e) {{
                console.log("Error al detener MediaRecorder:", e);
            }}
            recIndicator.style.display = 'none';
            btnRecManual.innerText = '🔴 Grabar Video';
            btnRecManual.classList.remove('recording');
        }}

        function updateRecTimerDisplay() {{
            const mins = String(Math.floor(recSeconds / 60)).padStart(2, '0');
            const secs = String(recSeconds % 60).padStart(2, '0');
            recTimerText.innerText = `🔴 REC ${{mins}}:${{secs}}`;
        }}

        btnRecManual.addEventListener('click', async () => {{
            if (isRecording) {{
                stopRecording();
            }} else {{
                await startRecording();
            }}
        }});

        // --- CONTEO REGRESIVO DE 5 SEGUNDOS ---

        btnCountdownRec.addEventListener('click', async () => {{
            // Intentar encender cámara por gesto de usuario en iOS
            await startCamera();

            countdownOverlay.style.display = 'flex';
            let count = 5;
            countdownNumber.innerText = count;

            const timer = setInterval(async () => {{
                count--;
                if (count > 0) {{
                    countdownNumber.innerText = count;
                }} else if (count === 0) {{
                    countdownNumber.innerText = '¡GRABANDO!';
                }} else {{
                    clearInterval(timer);
                    countdownOverlay.style.display = 'none';
                    box.scrollTop = 0;
                    if (mediaStream) {{
                        await startRecording();
                    }}
                    startScroll();
                }}
            }}, 1000);
        }});

        // --- DESCARGAR / GUARDAR VIDEO ---

        btnDownload.addEventListener('click', async () => {{
            if (!lastRecordedBlob) return alert('No hay grabación disponible.');
            
            const isMp4 = lastRecordedBlob.type.includes('mp4');
            const ext = isMp4 ? 'mp4' : 'webm';
            const filename = `teleprompter_rec_${{Date.now()}}.${{ext}}`;

            // En celulares, probar Web Share API primero para guardar directo en la galería / fotos
            const file = new File([lastRecordedBlob], filename, {{ type: lastRecordedBlob.type }});
            if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
                try {{
                    await navigator.share({{
                        files: [file],
                        title: 'Grabación Teleprompter',
                        text: 'Video de Teleprompter grabado en Studio Teleprompter'
                    }});
                    return;
                }} catch(shareErr) {{
                    console.log("Compartir cancelado o no soportado, descargando archivo directamente...", shareErr);
                }}
            }}

            // Descarga directa tradicional en navegador / PC
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = lastRecordedUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {{
                document.body.removeChild(a);
            }}, 200);
        }});
        
        fontInput.addEventListener('input', (e) => {{
            textNode.style.fontSize = e.target.value + 'px';
        }});

        btnReset.addEventListener('click', () => {{
            box.scrollTop = 0;
        }});

        btnMode.addEventListener('click', async () => {{
            box.classList.toggle('mode-916');
            if (mediaStream && !isRecording) {{
                stopCamera();
                await startCamera();
            }}
        }});

        btnMirror.addEventListener('click', () => {{
            textNode.classList.toggle('mirrored');
        }});

        // --- PANTALLA COMPLETA UNIVERSAL (INCLUIDO IPHONE Y MÓVILES) ---
        btnFS.addEventListener('click', () => {{
            const isFS = document.body.classList.toggle('is-fullscreen');

            try {{
                if (window.frameElement) {{
                    if (isFS) {{
                        window.frameElement.style.setProperty('position', 'fixed', 'important');
                        window.frameElement.style.setProperty('top', '0', 'important');
                        window.frameElement.style.setProperty('left', '0', 'important');
                        window.frameElement.style.setProperty('width', '100vw', 'important');
                        window.frameElement.style.setProperty('height', '100vh', 'important');
                        window.frameElement.style.setProperty('z-index', '9999999', 'important');
                        window.frameElement.style.setProperty('border', 'none', 'important');
                    }} else {{
                        window.frameElement.style.position = 'static';
                        window.frameElement.style.width = '100%';
                        window.frameElement.style.height = '680px';
                        window.frameElement.style.zIndex = 'auto';
                    }}
                }}
            }} catch(e) {{
                console.log("Error al ajustar frameElement:", e);
            }}

            if (isFS) {{
                btnFS.innerText = '⛶ Salir Pantalla Completa';
                btnFS.style.background = '#dc2626';
                try {{
                    if (document.documentElement.requestFullscreen) {{
                        document.documentElement.requestFullscreen().catch(e => {{}});
                    }} else if (document.documentElement.webkitRequestFullscreen) {{
                        document.documentElement.webkitRequestFullscreen().catch(e => {{}});
                    }}
                }} catch(e) {{}}
            }} else {{
                btnFS.innerText = '⛶ Pantalla Completa';
                btnFS.style.background = '';
                try {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen().catch(e => {{}});
                    }} else if (document.webkitExitFullscreen) {{
                        document.webkitExitFullscreen().catch(e => {{}});
                    }}
                }} catch(e) {{}}
            }}
        }});

        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                togglePlay();
            }} else if (e.code === 'KeyR') {{
                btnRecManual.click();
            }} else if (e.code === 'KeyC') {{
                btnCountdownRec.click();
            }} else if (e.code === 'ArrowUp') {{
                speedInput.value = Math.min(15, parseInt(speedInput.value) + 1);
            }} else if (e.code === 'ArrowDown') {{
                speedInput.value = Math.max(1, parseInt(speedInput.value) - 1);
            }} else if (e.code === 'KeyF') {{
                btnFS.click();
            }}
        }});
    </script>
</body>
</html>"""

def render_teleprompter_button(narracion_limpia: str, titulo: str):
    """Renderiza la experiencia de Teleprompter con soporte garantizado en móviles y PC."""
    html_content = generar_html_teleprompter_standalone(narracion_limpia, titulo)
    b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    
    # 1. Visor Integrado directo en la página (Recomendado para iPhone / Móviles ya que mantiene el origen HTTPS)
    st.markdown("#### 🎙️ Studio Teleprompter (Con Grabación de Video y Conteo 5s)")
    st.info("💡 **Para iPhone / iOS Chrome**: Usa el visor de abajo y presiona **'⛶ Pantalla Completa'** para expandir la cámara a toda la pantalla de tu celular con 100% de funciones de grabación.")
    components.html(html_content, height=680)
    
    # 2. Botón alternativo para abrir en ventana emergente (Ideal para monitores secundarios en PC y Android)
    component_code = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; margin: 10px 0;">
        <button id="open-prompter-btn" style="
            background: linear-gradient(135deg, #1e293b, #0f172a);
            color: #94a3b8; border: 1px solid rgba(255,255,255,0.15); padding: 12px 20px; border-radius: 10px;
            font-weight: 700; font-size: 14px; cursor: pointer; width: 100%;
            display: flex; align-items: center; justify-content: center; gap: 8px;
            transition: all 0.2s ease;
        ">
            🖥️ Abrir en Ventana Emergente (Ideal para Monitores PC y Android)
        </button>
        <script>
            const b64Data = "{b64_html}";
            document.getElementById('open-prompter-btn').addEventListener('click', () => {{
                try {{
                    const binaryStr = atob(b64Data);
                    const bytes = new Uint8Array(binaryStr.length);
                    for (let i = 0; i < binaryStr.length; i++) {{
                        bytes[i] = binaryStr.charCodeAt(i);
                    }}
                    const htmlText = new TextDecoder('utf-8').decode(bytes);
                    
                    const win = window.open('', '_blank');
                    if (win) {{
                        win.document.open();
                        win.document.write(htmlText);
                        win.document.close();
                    }} else {{
                        alert('Tu navegador bloqueó la ventana emergente. Por favor usa el Visor Integrado de la página.');
                    }}
                }} catch(e) {{
                    alert("Error al procesar Teleprompter: " + e.message);
                }}
            }});
        </script>
    </div>
    """
    components.html(component_code, height=60)

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
    <div style='display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 0.6rem;'>
        <div style='background: linear-gradient(135deg, #2563eb, #3b82f6); padding: 6px 14px; border-radius: 10px; box-shadow: 0 4px 14px rgba(37,99,235,0.4); display: flex; align-items: center; gap: 8px;'>
            <span style='color: white; font-weight: 900; font-size: 1.1rem;'>◆</span>
            <span style='color: white; font-weight: 800; font-size: 0.88rem; letter-spacing: 0.05em; font-family: "JetBrains Mono", monospace;'>SOCIEDAD 5.0</span>
        </div>
        <span style='font-size: 1.35rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text);'>INTELLIGENCE & MEDIA ENGINE</span>
        <span class='live-badge'>🟢 LIVE ENGINE v2.3</span>
    </div>
    <div style='color: var(--text-muted); font-size: 0.88rem; margin-top: -0.1rem; font-weight: 500;'>
        Plataforma autónoma de inteligencia geopolítica, producción de guiones de 10 min, Shorts verticales y crawling multifuente.
    </div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Modo Claro" if IS_DARK else "🌙 Modo Oscuro"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

st.markdown("<hr style='margin: 1.4rem 0 1.8rem; border-color: var(--border);'>", unsafe_allow_html=True)

# Cargar reportes al iniciar
lista_reportes = obtener_todos_reportes(db)

# =====================================================================
# 6. Pestañas de Navegación
# =====================================================================
tab_explorar, tab_shorts, tab_historial, tab_nuevo_analisis, tab_ingesta_automatica = st.tabs([
    "🔍 Guion YouTube (Largo)", 
    "📱 Shorts de IA (1 Minuto)",
    "📚 Historial de Guiones",
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
                <div class="metric-value-accent">{narrativa_dominante}</div>
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
            st.subheader("🎬 Paquete Completo para YouTube Studio (10 Minutos)")
            
            # Verificar si ya existe un paquete largo guardado en Firestore
            tiene_paquete_guardado = "paquete_largo" in reporte_selec and isinstance(reporte_selec["paquete_largo"], dict)
            
            if tiene_paquete_guardado:
                st.success("✅ Guion guardado previamente en Firestore. Cargado automáticamente sin gastar tokens.")
                btn_guion = st.button("🔄 Volver a Generar Paquete con IA (Regenerar)", type="secondary", use_container_width=True, key="btn_youtube_largo")
                pkg = reporte_selec["paquete_largo"]
            else:
                st.info("Produce automáticamente: Títulos CTR, Descripción SEO con Timestamps, Etiquetas y Prompts Visuales de IA en 16:9 (periodismo de 2 caras y bienestar humano).")
                btn_guion = st.button("Generar Paquete Completo para YouTube Largo 🚀", type="primary", use_container_width=True, key="btn_youtube_largo")
                pkg = None

            if btn_guion:
                with st.spinner("Gemini 3.5 Flash creando el paquete periodístico para YouTube (Sociedad 5.0)..."):
                    pkg_nuevo = generar_guion_youtube_paquete(reporte_selec)
                
                if "error" in pkg_nuevo:
                    st.error(pkg_nuevo["error"])
                else:
                    pkg = pkg_nuevo
                    reporte_selec["paquete_largo"] = pkg
                    # Guardar inmediatamente en Firestore
                    guardar_paquete_guion_firestore(db, reporte_selec["id"], "paquete_largo", pkg)
                    st.success("¡Paquete generado y guardado en Firestore exitosamente!")

            if pkg and "error" not in pkg:
                subtab_titulos, subtab_desc, subtab_tags, subtab_prompts, subtab_guion, subtab_prompter = st.tabs([
                    "📌 Títulos CTR", 
                    "📝 Descripción SEO", 
                    "🏷️ Etiquetas (Tags)", 
                    "🎨 Prompts IA (16:9)",
                    "📄 Guion Completo",
                    "🎙️ Teleprompter Studio"
                ])
                
                with subtab_titulos:
                    st.markdown("### 🎯 Opción de Títulos Persuasivos (Prueba A/B):")
                    for idx, tit in enumerate(pkg.get("titulos", [])):
                        st.text_input(f"Opción {idx+1}:", value=tit, key=f"tit_largo_{reporte_selec['id'][:6]}_{idx}")
                        
                with subtab_desc:
                    st.markdown("### 📝 Descripción Lista para Copiar:")
                    st.text_area("Copia esto directamente a YouTube Studio:", value=pkg.get("descripcion_seo", ""), height=250, key=f"desc_largo_{reporte_selec['id'][:6]}")
                    
                with subtab_tags:
                    st.markdown("### 🏷️ Etiquetas (Tags):")
                    st.text_area("Copia y pega en la sección de Etiquetas:", value=pkg.get("etiquetas", ""), height=100, key=f"tags_largo_{reporte_selec['id'][:6]}")
                    
                with subtab_prompts:
                    st.markdown("### 🎨 Prompts Visuales para Midjourney / Flux / Runway (16:9):")
                    for idx, pmt in enumerate(pkg.get("prompts_visuales", [])):
                        st.text_input(f"Prompt IA Scene {idx+1}:", value=pmt, key=f"pmt_largo_{reporte_selec['id'][:6]}_{idx}")
                        
                with subtab_guion:
                    st.markdown("### 📜 Guion Literario Completo (10 Min):")
                    st.info("💡 **Puedes editar el guion directamente aquí abajo. Al guardar los cambios, el Teleprompter se actualizará automáticamente.**")
                    
                    guion_largo_actual = pkg.get("guion_completo", "")
                    guion_largo_editado = st.text_area(
                        "✏️ Editar Guion de Locución:",
                        value=guion_largo_actual,
                        height=360,
                        key=f"edit_guion_largo_{reporte_selec['id'][:6]}"
                    )
                    
                    if guion_largo_editado != guion_largo_actual:
                        if st.button("💾 Guardar Guion Editado en Firestore", type="primary", key=f"btn_save_largo_{reporte_selec['id'][:6]}"):
                            pkg["guion_completo"] = guion_largo_editado
                            reporte_selec["paquete_largo"] = pkg
                            guardar_paquete_guion_firestore(db, reporte_selec["id"], "paquete_largo", pkg)
                            st.success("¡Guion editado y guardado en Firestore exitosamente!")
                            st.rerun()
                    
                    data_md = f"# PAQUETE YOUTUBE LARGO (SOCIEDAD 5.0)\n\n## TÍTULOS\n" + "\n".join(pkg.get("titulos", [])) + f"\n\n## DESCRIPCIÓN SEO\n{pkg.get('descripcion_seo')}\n\n## ETIQUETAS\n{pkg.get('etiquetas')}\n\n## GUION COMPLETO\n{guion_largo_editado}"
                    st.download_button(
                        label="📥 Descargar Paquete Completo (.md)",
                        data=data_md,
                        file_name=f"paquete_youtube_{reporte_selec.get('id')[:6]}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"btn_dl_md_largo_{reporte_selec['id'][:6]}"
                    )
                    
                with subtab_prompter:
                    st.markdown("### 🎙️ Studio Teleprompter (Grabación sin distracciones)")
                    st.info("Abre el Teleprompter adaptativo para móviles y PC con cámara en directo.")
                    narracion_largo_limpia = extraer_narracion_limpia(pkg.get("guion_completo", ""))
                    
                    render_teleprompter_button(narracion_largo_limpia, pkg.get("titulos", ["YouTube Studio"])[0])
                    
                    st.markdown("#### 📝 Texto de Locución Filtrado (Solo Narración):")
                    st.text_area("Copiar para Google Docs / Google Drive / Apps externas:", value=narracion_largo_limpia, height=220, key=f"txt_prompter_largo_{reporte_selec['id'][:6]}")
                    
                    st.download_button(
                        label="📥 Descargar Solo Narración (.txt)",
                        data=narracion_largo_limpia,
                        file_name=f"narracion_largo_{reporte_selec.get('id')[:6]}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"btn_dl_txt_largo_{reporte_selec['id'][:6]}"
                    )

# ---------------------------------------------------------------------
# PESTAÑA 2: NUEVO MÓDULO DE SHORTS DE IA (1 MINUTO / DIARIO)
# ---------------------------------------------------------------------
with tab_shorts:
    st.subheader("📱 Motor de Creación para YouTube Shorts (1 Minuto / Diario)")
    st.write("Selecciona cualquier reporte de Firestore y genera un Short de 60 segundos con formato vertical (9:16), dos caras de la noticia y postura enfocada en el bienestar humano.")
    
    if not lista_reportes:
        st.info("Ingresa o descarga primero un informe en Firestore para generar Shorts.")
    else:
        opciones_shorts = {f"[{r.get('nivel_impacto')} HP] - {r.get('fuente_original')} - ID: {r.get('id')[:6]}": r for r in lista_reportes}
        selected_short_key = st.selectbox("Selecciona informe para Short:", list(opciones_shorts.keys()), key="select_short")
        
        if selected_short_key:
            reporte_short = opciones_shorts[selected_short_key]
            
            st.markdown(f"**Fuente Seleccionada:** {reporte_short.get('fuente_original')} | **Narrativa:** {reporte_short.get('narrativa_principal')}")
            
            tiene_short_guardado = "paquete_short" in reporte_short and isinstance(reporte_short["paquete_short"], dict)
            
            if tiene_short_guardado:
                st.success("✅ Short guardado previamente en Firestore. Cargado automáticamente sin gastar tokens.")
                btn_gen_short = st.button("🔄 Volver a Generar Short con IA (Regenerar)", type="secondary", use_container_width=True, key="btn_short_action")
                pkg_short = reporte_short["paquete_short"]
            else:
                btn_gen_short = st.button("Generar YouTube Short de 1 Minuto ⚡", type="primary", use_container_width=True, key="btn_short_action")
                pkg_short = None

            if btn_gen_short:
                with st.spinner("Gemini 3.5 Flash condensando el informe en un Short vertical de 60 segundos con perspectiva periodística..."):
                    pkg_short_nuevo = generar_guion_short_paquete(reporte_short)
                    
                if "error" in pkg_short_nuevo:
                    st.error(pkg_short_nuevo["error"])
                else:
                    pkg_short = pkg_short_nuevo
                    reporte_short["paquete_short"] = pkg_short
                    # Guardar inmediatamente en Firestore
                    guardar_paquete_guion_firestore(db, reporte_short["id"], "paquete_short", pkg_short)
                    st.success("¡Short generado y guardado en Firestore exitosamente!")

            if pkg_short and "error" not in pkg_short:
                st.markdown(f"### 📌 Título del Short: `{pkg_short.get('titulo_short')}`")
                st.markdown(f"**Hashtags:** `{pkg_short.get('hashtags')}`")
                
                s_col1, s_col2 = st.columns([7, 5])
                with s_col1:
                    st.markdown("#### 📜 Guion Literario de 60 Segundos (Editable):")
                    guion_short_actual = pkg_short.get("guion_short", "")
                    guion_short_editado = st.text_area(
                        "✏️ Editar Texto del Short:",
                        value=guion_short_actual,
                        height=280,
                        key=f"edit_guion_short_{reporte_short['id'][:6]}"
                    )
                    if guion_short_editado != guion_short_actual:
                        if st.button("💾 Guardar Short Editado en Firestore", type="primary", key=f"btn_save_short_{reporte_short['id'][:6]}"):
                            pkg_short["guion_short"] = guion_short_editado
                            reporte_short["paquete_short"] = pkg_short
                            guardar_paquete_guion_firestore(db, reporte_short["id"], "paquete_short", pkg_short)
                            st.success("¡Guion del Short actualizado y guardado en Firestore!")
                            st.rerun()
                    
                with s_col2:
                    st.markdown("#### 📱 Prompts Visuales Verticals (9:16):")
                    for idx, p916 in enumerate(pkg_short.get("prompts_visuales_916", [])):
                        st.text_area(f"Prompt Vertical {idx+1} (--ar 9:16):", value=p916, height=90, key=f"short_pmt_{reporte_short['id'][:6]}_{idx}")
                        
                st.markdown("---")
                st.markdown("### 🎙️ Teleprompter Studio para Short (9:16)")
                narracion_short_limpia = extraer_narracion_limpia(guion_short_editado)
                render_teleprompter_button(narracion_short_limpia, pkg_short.get("titulo_short", "Short IA"))
                
                st.text_area("Copiar locución del Short a Google Docs / Drive:", value=narracion_short_limpia, height=140, key=f"txt_prompter_short_{reporte_short['id'][:6]}")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    data_short_md = f"# SHORT YOUTUBE: {pkg_short.get('titulo_short')}\n\nHashtags: {pkg_short.get('hashtags')}\n\n## GUION\n{pkg_short.get('guion_short')}\n\n## PROMPTS 9:16\n" + "\n".join(pkg_short.get("prompts_visuales_916", []))
                    st.download_button(
                        label="📥 Descargar Guion Completo de Short (.md)",
                        data=data_short_md,
                        file_name=f"short_youtube_{reporte_short.get('id')[:6]}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"btn_dl_md_short_{reporte_short['id'][:6]}"
                    )
                with col_d2:
                    st.download_button(
                        label="📥 Descargar Solo Narración del Short (.txt)",
                        data=narracion_short_limpia,
                        file_name=f"narracion_short_{reporte_short.get('id')[:6]}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"btn_dl_txt_short_{reporte_short['id'][:6]}"
                    )

# ---------------------------------------------------------------------
# PESTAÑA 3: PESTAÑA DEDICADA DE HISTORIAL DE GUIONES
# ---------------------------------------------------------------------
with tab_historial:
    st.subheader("📚 Historial de Guiones Guardados")
    st.write("Consulta y descarga en cualquier momento todos los guiones (Largos y Shorts) previamente generados sin necesidad de volver a gastar tokens de la IA.")
    
    # Filtrar reportes que tengan al menos un guion guardado
    reportes_con_guion = [r for r in lista_reportes if "paquete_largo" in r or "paquete_short" in r]
    
    if not reportes_con_guion:
        st.info("Aún no hay guiones generados en el historial. Ve a las pestañas 'Guion YouTube (Largo)' o 'Shorts de IA' para crear el primero.")
    else:
        filtro_tipo = st.radio("Filtrar por formato:", ["Todos los guiones", "Solo Videos Largos (10 Min)", "Solo Shorts (1 Min)"], horizontal=True)
        
        reportes_filtrados = reportes_con_guion
        if filtro_tipo == "Solo Videos Largos (10 Min)":
            reportes_filtrados = [r for r in reportes_con_guion if "paquete_largo" in r]
        elif filtro_tipo == "Solo Shorts (1 Min)":
            reportes_filtrados = [r for r in reportes_con_guion if "paquete_short" in r]
            
        if not reportes_filtrados:
            st.warning("No se encontraron guiones con el filtro seleccionado.")
        else:
            opciones_historial = {
                f"[{r.get('fuente_original')}] - {r.get('resumen_ejecutivo')[:60]}... (ID: {r.get('id')[:6]})": r 
                for r in reportes_filtrados
            }
            sel_hist_key = st.selectbox("Selecciona un guion guardado del historial:", list(opciones_historial.keys()), key="select_historial_main")
            
            if sel_hist_key:
                rep_h = opciones_historial[sel_hist_key]
                st.markdown("---")
                
                # Pestañas secundarias para alternar entre Largo y Short si existen ambos
                formatos_disponibles = []
                if "paquete_largo" in rep_h:
                    formatos_disponibles.append("🎬 Video Largo (10 Min)")
                if "paquete_short" in rep_h:
                    formatos_disponibles.append("📱 Short (1 Minuto)")
                    
                subtabs_h = st.tabs(formatos_disponibles)
                
                for idx_fmt, fmt_nombre in enumerate(formatos_disponibles):
                    with subtabs_h[idx_fmt]:
                        if "Video Largo" in fmt_nombre:
                            pkg_h_largo = rep_h["paquete_largo"]
                            st.markdown(f"### 🎬 Paquete Guardado de Video Largo — {rep_h.get('fuente_original')}")
                            
                            h_t1, h_t2, h_t3, h_t4, h_t5, h_t6 = st.tabs(["📌 Títulos", "📝 Descripción SEO", "🏷️ Tags", "🎨 Prompts 16:9", "📄 Guion", "🎙️ Teleprompter"])
                            with h_t1:
                                for i, t in enumerate(pkg_h_largo.get("titulos", [])):
                                    st.text_input(f"Título {i+1}:", value=t, key=f"hist_tit_l_{rep_h['id'][:6]}_{i}")
                            with h_t2:
                                st.text_area("Descripción SEO:", value=pkg_h_largo.get("descripcion_seo", ""), height=200, key=f"hist_desc_l_{rep_h['id'][:6]}")
                            with h_t3:
                                st.text_area("Etiquetas:", value=pkg_h_largo.get("etiquetas", ""), height=80, key=f"hist_tags_l_{rep_h['id'][:6]}")
                            with h_t4:
                                for i, p in enumerate(pkg_h_largo.get("prompts_visuales", [])):
                                    st.text_input(f"Prompt Scene {i+1}:", value=p, key=f"hist_pmt_l_{rep_h['id'][:6]}_{i}")
                            with h_t5:
                                guion_txt_h = pkg_h_largo.get("guion_completo", "")
                                st.markdown(guion_txt_h)
                                data_md_h = f"# PAQUETE YOUTUBE LARGO\n\n## TÍTULOS\n" + "\n".join(pkg_h_largo.get("titulos", [])) + f"\n\n## DESCRIPCIÓN SEO\n{pkg_h_largo.get('descripcion_seo')}\n\n## ETIQUETAS\n{pkg_h_largo.get('etiquetas')}\n\n## GUION COMPLETO\n{guion_txt_h}"
                                st.download_button("📥 Descargar Paquete (.md)", data=data_md_h, file_name=f"historial_largo_{rep_h['id'][:6]}.md", mime="text/markdown", use_container_width=True, key=f"btn_dl_hist_md_l_{rep_h['id'][:6]}")
                            with h_t6:
                                locucion_l = extraer_narracion_limpia(pkg_h_largo.get("guion_completo", ""))
                                render_teleprompter_button(locucion_l, pkg_h_largo.get("titulos", ["YouTube Studio"])[0])
                                st.text_area("Texto de Locución:", value=locucion_l, height=180, key=f"hist_txt_l_{rep_h['id'][:6]}")
                                st.download_button("📥 Descargar Locución (.txt)", data=locucion_l, file_name=f"narracion_largo_{rep_h['id'][:6]}.txt", mime="text/plain", use_container_width=True, key=f"btn_dl_hist_txt_l_{rep_h['id'][:6]}")
                                
                        elif "Short" in fmt_nombre:
                            pkg_h_short = rep_h["paquete_short"]
                            st.markdown(f"### 📱 Short Guardado de 1 Minuto — {rep_h.get('fuente_original')}")
                            st.markdown(f"**Título:** `{pkg_h_short.get('titulo_short')}`")
                            st.markdown(f"**Hashtags:** `{pkg_h_short.get('hashtags')}`")
                            
                            sc1, sc2 = st.columns([7, 5])
                            with sc1:
                                st.markdown("#### 📜 Guion de 60 Segundos:")
                                st.markdown(pkg_h_short.get("guion_short", ""))
                            with sc2:
                                st.markdown("#### 📱 Prompts 9:16:")
                                for i, p in enumerate(pkg_h_short.get("prompts_visuales_916", [])):
                                    st.text_area(f"Prompt {i+1}:", value=p, height=80, key=f"hist_pmt_s_{rep_h['id'][:6]}_{i}")
                                    
                            locucion_s = extraer_narracion_limpia(pkg_h_short.get("guion_short", ""))
                            render_teleprompter_button(locucion_s, pkg_h_short.get("titulo_short", "Short IA"))
                            
                            col_dh1, col_dh2 = st.columns(2)
                            with col_dh1:
                                data_short_md_h = f"# SHORT: {pkg_h_short.get('titulo_short')}\n\nHashtags: {pkg_h_short.get('hashtags')}\n\n## GUION\n{pkg_h_short.get('guion_short')}\n\n## PROMPTS 9:16\n" + "\n".join(pkg_h_short.get("prompts_visuales_916", []))
                                st.download_button("📥 Descargar Short (.md)", data=data_short_md_h, file_name=f"historial_short_{rep_h['id'][:6]}.md", mime="text/markdown", use_container_width=True, key=f"btn_dl_hist_md_s_{rep_h['id'][:6]}")
                            with col_dh2:
                                st.download_button("📥 Descargar Locución Short (.txt)", data=locucion_s, file_name=f"narracion_short_{rep_h['id'][:6]}.txt", mime="text/plain", use_container_width=True, key=f"btn_dl_hist_txt_s_{rep_h['id'][:6]}")



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
                "🌐 Búsqueda en Tiempo Real (Google News Global)",
                "Prensa Tech Global (TechCrunch, Wired, VentureBeat)",
                "Universidades & Ciencia (arXiv, IEEE Spectrum, Nature, MIT)",
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

