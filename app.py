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
    """Genera una aplicación web HTML5 independiente para Teleprompter libre de distracciones y adaptada a móviles."""
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
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            z-index: 100; background: rgba(18, 18, 24, 0.95); backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.2); border-radius: 30px;
            padding: 8px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.9); transition: opacity 0.4s ease;
            width: 92vw; max-width: 850px; max-height: 45vh; overflow-y: auto;
        }}
        #controls-bar:hover, body.paused #controls-bar {{ opacity: 1; }}
        body.playing #controls-bar {{ opacity: 0.35; }}

        .btn {{
            background: #2563eb; color: white; border: none; padding: 10px 16px;
            border-radius: 25px; font-weight: 700; cursor: pointer; font-size: 14px;
            display: flex; align-items: center; justify-content: center; gap: 6px; transition: background 0.2s;
            min-height: 44px; touch-action: manipulation; -webkit-tap-highlight-color: transparent;
        }}
        .btn:active {{ transform: scale(0.97); }}
        .btn:hover {{ background: #1d4ed8; }}
        .btn-sec {{ background: rgba(255,255,255,0.18); }}
        .btn-sec:hover {{ background: rgba(255,255,255,0.28); }}

        .ctrl-group {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #ccc; background: rgba(255,255,255,0.06); padding: 4px 10px; border-radius: 12px; }}
        input[type="range"] {{ accent-color: #2563eb; cursor: pointer; height: 30px; }}

        @media (max-width: 768px) {{
            #controls-bar {{
                bottom: 12px; padding: 10px 8px; border-radius: 20px; width: 95vw; gap: 6px;
            }}
            .btn {{
                padding: 10px 12px; font-size: 13px; min-height: 44px; flex: 1 1 auto;
            }}
            .ctrl-group {{
                flex: 1 1 45%; justify-content: space-between; font-size: 11px;
            }}
            .script-content {{ font-size: 26px; }}
            #prompter-box {{ padding: 30vh 1rem 40vh; width: 96%; }}
        }}
    </style>
</head>
<body class="paused">
    <video id="webcam" autoplay playsinline webkit-playsinline muted></video>
    <div id="overlay"></div>
    
    <div id="prompter-box">
        <div id="text-node" class="script-content">{parrafos_html}</div>
    </div>
    
    <div id="controls-bar">
        <button id="btn-toggle" class="btn" style="flex: 1 1 100%; background: #2563eb; font-size: 15px;">▶️ INICIAR / PAUSAR TELEPROMPTER</button>
        
        <div class="ctrl-group">
            <label>⚡ Vel:</label>
            <input type="range" id="speed" min="1" max="15" value="4">
        </div>
        
        <div class="ctrl-group">
            <label>🔠 Texto:</label>
            <input type="range" id="fontsize" min="18" max="60" value="30">
        </div>

        <button id="btn-mode" class="btn btn-sec">🖥️ 16:9 / 9:16</button>
        <button id="btn-mirror" class="btn btn-sec">🪞 Espejo</button>
        <button id="btn-reset" class="btn btn-sec">🔄 Inicio</button>
        <button id="btn-fullscreen" class="btn btn-sec">⛶ Pantalla Completa</button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'user', width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }} }})
                .then(stream => {{ 
                    video.srcObject = stream;
                    video.play().catch(e => console.log("video play error:", e));
                }})
                .catch(err => console.log("Camara no disponible o denegada: ", err));
        }}

        const box = document.getElementById('prompter-box');
        const textNode = document.getElementById('text-node');
        const btnToggle = document.getElementById('btn-toggle');
        const speedInput = document.getElementById('speed');
        const fontInput = document.getElementById('fontsize');
        const btnMode = document.getElementById('btn-mode');
        const btnMirror = document.getElementById('btn-mirror');
        const btnReset = document.getElementById('btn-reset');
        const btnFS = document.getElementById('btn-fullscreen');

        let isPlaying = false;
        let animId = null;

        function scrollStep() {{
            if (!isPlaying) return;
            box.scrollTop += parseFloat(speedInput.value) * 0.4;
            animId = requestAnimationFrame(scrollStep);
        }}

        function togglePlay() {{
            isPlaying = !isPlaying;
            if (isPlaying) {{
                document.body.classList.remove('paused');
                document.body.classList.add('playing');
                btnToggle.innerText = '⏸️ PAUSAR SCROLL';
                btnToggle.style.background = '#dc2626';
                scrollStep();
            }} else {{
                document.body.classList.remove('playing');
                document.body.classList.add('paused');
                btnToggle.innerText = '▶️ INICIAR SCROLL';
                btnToggle.style.background = '#2563eb';
                cancelAnimationFrame(animId);
            }}
        }}

        btnToggle.addEventListener('click', togglePlay);
        
        fontInput.addEventListener('input', (e) => {{
            textNode.style.fontSize = e.target.value + 'px';
        }});

        btnReset.addEventListener('click', () => {{
            box.scrollTop = 0;
        }});

        btnMode.addEventListener('click', () => {{
            box.classList.toggle('mode-916');
        }});

        btnMirror.addEventListener('click', () => {{
            textNode.classList.toggle('mirrored');
        }});

        btnFS.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                if (document.documentElement.requestFullscreen) {{
                    document.documentElement.requestFullscreen();
                }} else if (document.documentElement.webkitRequestFullscreen) {{
                    document.documentElement.webkitRequestFullscreen();
                }}
            }} else {{
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }} else if (document.webkitExitFullscreen) {{
                    document.webkitExitFullscreen();
                }}
            }}
        }});

        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                togglePlay();
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
    """Renderiza la experiencia de Teleprompter libre de errores de sintaxis en PC y celulares."""
    html_content = generar_html_teleprompter_standalone(narracion_limpia, titulo)
    b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    
    component_code = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; margin: 5px 0;">
        <button id="open-prompter-btn" style="
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white; border: none; padding: 14px 24px; border-radius: 10px;
            font-weight: 700; font-size: 15px; cursor: pointer; width: 100%;
            display: flex; align-items: center; justify-content: center; gap: 8px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35); transition: all 0.2s ease;
        ">
            🚀 Abrir Studio Teleprompter (Nueva Ventana / Celular y PC)
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
                    const blob = new Blob([bytes], {{ type: 'text/html;charset=utf-8' }});
                    const url = URL.createObjectURL(blob);
                    const win = window.open(url, '_blank');
                    if (!win) {{
                        alert('Tu navegador bloqueó la ventana emergente. Por favor, permite ventanas emergentes para este sitio o usa la opción desplegable de abajo.');
                    }}
                }} catch(e) {{
                    alert("Error al procesar Teleprompter: " + e.message);
                }}
            }});
        </script>
    </div>
    """
    components.html(component_code, height=70)
    
    # Visor integrado alternativo por si el navegador móvil bloquea ventanas emergentes
    with st.expander("👁️ O abrir Visor Integrado de Teleprompter en Pantalla Completa", expanded=False):
        st.info("Presiona el botón '⛶ Pantalla Completa' dentro del visor para activar la cámara a pantalla completa sin distracciones.")
        components.html(html_content, height=650)

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
                    guion_txt = pkg.get("guion_completo", "")
                    st.markdown(guion_txt)
                    
                    data_md = f"# PAQUETE YOUTUBE LARGO (SOCIEDAD 5.0)\n\n## TÍTULOS\n" + "\n".join(pkg.get("titulos", [])) + f"\n\n## DESCRIPCIÓN SEO\n{pkg.get('descripcion_seo')}\n\n## ETIQUETAS\n{pkg.get('etiquetas')}\n\n## GUION COMPLETO\n{guion_txt}"
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
                    st.markdown("#### 📜 Guion Literario de 60 Segundos:")
                    st.markdown(pkg_short.get("guion_short", ""))
                    
                with s_col2:
                    st.markdown("#### 📱 Prompts Visuales Verticals (9:16):")
                    for idx, p916 in enumerate(pkg_short.get("prompts_visuales_916", [])):
                        st.text_area(f"Prompt Vertical {idx+1} (--ar 9:16):", value=p916, height=90, key=f"short_pmt_{reporte_short['id'][:6]}_{idx}")
                        
                st.markdown("---")
                st.markdown("### 🎙️ Teleprompter Studio para Short (9:16)")
                narracion_short_limpia = extraer_narracion_limpia(pkg_short.get("guion_short", ""))
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

