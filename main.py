import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Literal

# Cargar variables de entorno desde api_keys.env
env_path = os.path.join(os.path.dirname(__file__), "api_keys.env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Cae a .env por defecto si no existe el archivo específico

# =====================================================================
# 1. Definición del Esquema Structured Output (Pydantic)
# =====================================================================
class AnalisisReporte(BaseModel):
    """
    Define la estructura estricta del JSON que Gemini debe devolver.
    Cada campo contiene descripciones semánticas para guiar al modelo.
    """
    fuente_original: str = Field(
        description="La fuente, autor, medio u organización original que emite el reporte o informe (ej. McKinsey, BCG, WEF, OCDE, arXiv, MIT, IEEE)."
    )
    resumen_ejecutivo: str = Field(
        description="Un resumen ejecutivo exhaustivo pero conciso que sintetice los puntos principales, el contexto geopolítico o tecnológico y las conclusiones."
    )
    nivel_impacto: int = Field(
        description="Evaluación numérica del impacto geopolítico, tecnológico o socioeconómico del reporte. Escala del 1 (impacto irrelevante) al 10 (impacto crítico y disruptivo).",
        ge=1,
        le=10
    )
    citas_verificables: List[str] = Field(
        description="Lista de citas de texto directas, literales y verificables del reporte original que respaldan el análisis o la evaluación de impacto."
    )
    enlaces_fuentes: List[str] = Field(
        description="Lista de enlaces web, URLs o referencias hipervínculo oficiales citadas en el reporte original que corresponden a las fuentes."
    )
    narrativa_principal: Literal["Transferencia de Riqueza", "Cambio de Poder Geopolítico", "Obsolescencia Cotidiana"] = Field(
        description="La narrativa audiovisual clave que mejor describe el documento analizado."
    )
    explicacion_narrativa: str = Field(
        description="Justificación y explicación detallada y llamativa de la narrativa seleccionada (quién gana/pierde dinero, qué país domina y cómo afecta a LatAm, o qué hábito/profesión desaparece en 24 meses)."
    )

# =====================================================================
# 2. Inicialización de Google Cloud Firestore
# =====================================================================
def inicializar_firebase() -> firestore.firestore.Client:
    """
    Inicializa el SDK de Firebase Admin utilizando el archivo de credenciales
    de cuenta de servicio definido en las variables de entorno.
    
    Retorna:
        firestore.firestore.Client: Cliente activo para interactuar con Firestore.
    """
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise ValueError(
            "La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está definida.\n"
            "Asegúrate de configurarla en api_keys.env apuntando al archivo JSON de credenciales."
        )
    
    # Manejar rutas relativas respecto a la ubicación de main.py
    if not os.path.isabs(cred_path):
        cred_path = os.path.abspath(os.path.join(os.path.dirname(__file__), cred_path))
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"No se encontró el archivo JSON de credenciales de Firebase en la ruta: {cred_path}"
        )
    
    # Prevenir doble inicialización de la app
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] Conexión establecida con éxito.")
    
    # Obtener el ID de la base de datos de las variables de entorno
    db_id = os.getenv("FIREBASE_DATABASE_ID")
    from google.cloud import firestore as gcloud_firestore
    
    if db_id and db_id.strip() and db_id != "(default)":
        print(f"[FIREBASE] Utilizando base de datos específica: '{db_id}'")
        # Instanciar el cliente directamente para soportar bases de datos con ID personalizados
        return gcloud_firestore.Client(database=db_id.strip())
    
    print("[FIREBASE] Utilizando base de datos predeterminada '(default)'")
    return gcloud_firestore.Client()

# =====================================================================
# 3. Consulta a la API de Gemini 1.5 Pro
# =====================================================================
def analizar_reporte_con_gemini(texto_reporte: str) -> dict:
    """
    Envía el texto largo a la API de Gemini 1.5 Pro solicitando estrictamente
    un JSON que se ajuste al esquema AnalisisReporte.
    
    Argumentos:
        texto_reporte (str): Texto original largo que representa el informe a analizar.
        
    Retorna:
        dict: Diccionario que cumple con la estructura de AnalisisReporte.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "La variable de entorno GEMINI_API_KEY no está definida.\n"
            "Asegúrate de configurarla en api_keys.env."
        )
    
    # Inicializar el cliente oficial moderno de Google GenAI
    client = genai.Client(api_key=api_key)
    
    # Instrucciones de comportamiento para el modelo
    prompt_sistema = (
        "Actúa como un arquitecto analista senior en inteligencia económica, geopolítica y tecnológica para 'Sociedad 5.0'. "
        "Tu objetivo es extraer del reporte provisto información estructurada de alta fidelidad. "
        "Presta especial atención a fuentes clave mundiales de alto nivel, tales como:\n"
        "1. Inteligencia Económica/Geopolítica: McKinsey Global Institute, Boston Consulting Group (BCG), World Economic Forum (WEF), OCDE.\n"
        "2. Científicas/Técnicas: ArXiv (especialmente cs.AI), MIT Technology Review, IEEE.\n\n"
        "El análisis debe centrarse obligatoriamente en identificar y desarrollar una de estas tres narrativas audiovisuales de alto impacto:\n"
        "- 'Transferencia de Riqueza': Quién pierde dinero y quién lo gana con esta tecnología (desplazamiento de poder económico de unas industrias/entidades a otras).\n"
        "- 'Cambio de Poder Geopolítico': Qué país o bloque domina la tecnología y cómo afecta esto a regiones en desarrollo, con foco particular en América Latina.\n"
        "- 'Obsolescencia Cotidiana': Qué profesión, industria o hábito cultural desaparecerá por completo en los próximos 24 meses debido a esta tecnología.\n\n"
        "Debes estructurar el JSON de salida respetando estrictamente el esquema provisto, incluyendo fuente, resumen, nivel de impacto, citas exactas del texto, "
        "enlaces o URLs citadas en el reporte, la narrativa identificada y la justificación llamativa para contenido audiovisual.\n"
        "Debes responder única y exclusivamente con un JSON que cumpla el esquema proporcionado. No agregues markdown adicional."
    )
    
    # Obtener el modelo de las variables de entorno (fallback a gemini-2.5-pro por compatibilidad de API)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    
    print(f"[GEMINI] Enviando reporte a {model_name} para análisis...")
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt_sistema, texto_reporte],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalisisReporte,
                temperature=0.1,  # Temperatura baja para asegurar coherencia y fidelidad al texto
            )
        )
        
        # Deserializar la respuesta estructurada
        analisis_json = json.loads(response.text)
        return analisis_json
        
    except json.JSONDecodeError as jde:
        print(f"[ERROR] Gemini no retornó un JSON estructurado válido: {jde}")
        print(f"Respuesta cruda del modelo: {response.text}")
        raise
    except Exception as e:
        print(f"[ERROR] Error al invocar la API de Gemini: {e}")
        raise

# =====================================================================
# 4. Guardar Análisis en Firestore
# =====================================================================
def guardar_en_firestore(db: firestore.firestore.Client, analisis: dict) -> str:
    """
    Toma el JSON (diccionario) del análisis y lo almacena como un nuevo
    documento dentro de la colección 'analisis_sociedad' en Firestore.
    
    Argumentos:
        db (firestore.firestore.Client): Cliente de Firestore.
        analisis (dict): Datos estructurados del análisis.
        
    Retorna:
        str: ID del documento creado en Firestore.
    """
    try:
        # Agregar timestamp de auditoría al documento
        documento = {
            **analisis,
            "fecha_creacion": datetime.now(timezone.utc)
        }
        
        # Crear referencia a un documento aleatorio en la colección
        doc_ref = db.collection("analisis_sociedad").document()
        doc_ref.set(documento)
        
        print(f"[FIRESTORE] Documento guardado exitosamente en 'analisis_sociedad' con ID: {doc_ref.id}")
        return doc_ref.id
        
    except Exception as e:
        print(f"[ERROR] Error al escribir en la base de datos Firestore: {e}")
        raise

# =====================================================================
# 5. Función Integradora (Orquestación del Flujo)
# =====================================================================
def procesar_reporte_completo(texto_reporte: str) -> str:
    """
    Función que recibe el texto largo del reporte, orquesta
    la inicialización de Firebase, el análisis con Gemini y el guardado en Firestore.
    
    Argumentos:
        texto_reporte (str): El texto del reporte a procesar.
        
    Retorna:
        str: El ID del documento insertado en Firestore.
    """
    print("\n" + "="*50)
    print("INICIANDO MOTOR DE ANÁLISIS - SOCIEDAD 5.0")
    print("="*50)
    
    # 1. Inicializar Base de Datos NoSQL Firestore
    db = inicializar_firebase()
    
    # 2. Obtener análisis estructurado mediante Gemini 1.5 Pro
    analisis = analizar_reporte_con_gemini(texto_reporte)
    print("\n[ANALISIS OBTENIDO]:")
    print(json.dumps(analisis, indent=4, ensure_ascii=False))
    
    # 3. Guardar el análisis en la base de datos
    doc_id = guardar_en_firestore(db, analisis)
    
    print("\n" + "="*50)
    print(f"PROCESAMIENTO EXITOSO. Documento ID: {doc_id}")
    print("="*50)
    
    return doc_id

# =====================================================================
# Bloque de Prueba Local
# =====================================================================
if __name__ == "__main__":
    # Reporte simulado enfocado en tecnología y geopolítica
    reporte_economico_geopolitico = """
    INFORME DE RIESGOS TECNOLÓGICOS Y GEOPOLÍTICOS 2026
    Publicado por: World Economic Forum (WEF) en colaboración con el MIT Technology Review.
    Enlace al reporte del WEF: https://www.weforum.org/reports/global-risks-2026
    Enlace al paper técnico de soporte en arXiv: https://arxiv.org/abs/2605.12345
    
    El rápido avance en el desarrollo de microcontroladores neuromórficos por parte de corporaciones estatales en Asia Oriental ha provocado un giro drástico en el control de las cadenas de suministro de hardware de inteligencia artificial. Según datos de la OCDE (disponibles en https://www.oecd.org/artificial-intelligence), se proyecta un desplazamiento de la manufactura tradicional hacia centros de computación de borde soberanos. 
    
    "El control sobre el silicio neuromórfico determinará el control sobre los flujos comerciales en la próxima década. Quienes dominen el diseño y producción de estos microchips controlarán las rutas de datos globales, dejando a regiones importadoras como América Latina en una situación de dependencia tecnológica y regulatoria extrema si no desarrollan alternativas locales de inmediato", advierte el reporte del WEF.
    
    Esta automatización avanzada a nivel de hardware amenaza directamente la viabilidad de las industrias de subcontratación de software y centros de soporte técnico (call centers) tradicionales en todo el continente americano. Se estima que más del 70% de los roles de soporte técnico básico de nivel 1 serán obsoletos en los próximos 24 meses debido a la autogestión de fallos por silicio neuromórfico local. Esto representa una transferencia de riqueza sin precedentes desde las economías emergentes prestadoras de servicios de soporte (estimado en 18 mil millones de dólares anuales en ingresos salariales perdidos) hacia los dueños de patentes tecnológicas en el hemisferio oriental y multinacionales de computación cuántica.
    """
    
    try:
        procesar_reporte_completo(reporte_economico_geopolitico)
    except Exception as error:
        print(f"\n[FALLO CRÍTICO] La ejecución del script falló: {error}")
