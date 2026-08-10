import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict

# Cabeceras de simulación de navegador para evitar bloqueos HTTP 403 (Forbidden)
HEADERS_NAVEGADOR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive'
}


# =====================================================================
# 1. Recuperación de Papers de arXiv (Universidad de Cornell)
# =====================================================================
def consultar_arxiv(palabra_clave: str = "", max_resultados: int = 5) -> List[Dict]:
    """
    Consulta la API abierta de arXiv para recuperar los papers más recientes 
    en la categoría de Inteligencia Artificial (cs.AI) que coincidan con 
    una palabra clave opcional.
    
    Argumentos:
        palabra_clave (str): Término de búsqueda opcional para filtrar los papers.
        max_resultados (int): Cantidad máxima de papers a recuperar.
        
    Retorna:
        List[Dict]: Lista de artículos estructurados.
    """
    # Filtro base en Inteligencia Artificial
    query = "cat:cs.AI"
    if palabra_clave.strip():
        # Reemplazar espacios por formato de consulta de la API
        pk_safe = palabra_clave.strip().replace(" ", "+")
        query += f"+AND+all:{pk_safe}"
        
    # URL de la API de arXiv ordenando por fecha de publicación descendente
    url = (
        f"http://export.arxiv.org/api/query?search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_resultados}"
    )
    
    print(f"[INGEST] Consultando arXiv: {url}")
    
    try:
        req = urllib.request.Request(
            url, 
            headers=HEADERS_NAVEGADOR
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # Namespace de Atom XML utilizado por arXiv
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            id_url = entry.find('atom:id', ns).text.strip()
            title = entry.find('atom:title', ns).text.strip().replace("\n", " ")
            summary = entry.find('atom:summary', ns).text.strip().replace("\n", " ")
            published = entry.find('atom:published', ns).text.strip()
            
            # Extraer nombres de autores
            autores_list = []
            for author in entry.findall('atom:author', ns):
                name_node = author.find('atom:name', ns)
                if name_node is not None:
                    autores_list.append(name_node.text.strip())
            
            autores = ", ".join(autores_list)
            
            # Formatear la fecha
            try:
                dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                fecha_formato = dt.strftime("%B %d, %Y")
            except:
                fecha_formato = published
            
            papers.append({
                "fuente": "arXiv (cs.AI)",
                "enlace": id_url,
                "titulo": title,
                "resumen": summary,
                "autores": autores if autores else "Autores Desconocidos",
                "fecha": fecha_formato,
                "tipo": "Paper Científico"
            })
            
        print(f"[INGEST] arXiv retornó {len(papers)} resultados.")
        return papers
        
    except Exception as err:
        print(f"[ERROR INGEST] Falla al consultar arXiv: {err}")
        return []

# =====================================================================
# 2. Recuperación de Artículos desde Feeds RSS Públicos (MIT, WEF)
# =====================================================================
def consultar_rss(url_feed: str, nombre_fuente: str, palabra_clave: str = "", max_resultados: int = 5) -> List[Dict]:
    """
    Rastrea feeds RSS estándar en formato XML para extraer los artículos más recientes
    y filtrarlos por una palabra clave opcional.
    
    Argumentos:
        url_feed (str): URL del canal de RSS/XML de la fuente.
        nombre_fuente (str): Nombre amigable de la fuente (ej: MIT Technology Review, WEF).
        palabra_clave (str): Término de búsqueda opcional.
        max_resultados (int): Límite máximo de artículos a retornar.
        
    Retorna:
        List[Dict]: Lista de artículos parseados.
    """
    print(f"[INGEST] Consultando RSS de {nombre_fuente}: {url_feed}")
    
    try:
        req = urllib.request.Request(
            url_feed, 
            headers=HEADERS_NAVEGADOR
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # La estructura clásica de RSS es <rss><channel><item>...
        channel = root.find('channel')
        if channel is None:
            print(f"[INGEST] Formato RSS no estándar para {nombre_fuente}. Canal no encontrado.")
            return []
            
        articulos = []
        for item in channel.findall('item'):
            title_node = item.find('title')
            link_node = item.find('link')
            desc_node = item.find('description')
            pub_node = item.find('pubDate')
            
            title = title_node.text.strip() if title_node is not None else "Sin Título"
            link = link_node.text.strip() if link_node is not None else ""
            
            # Limpiar HTML básico de las descripciones si las hay
            desc = desc_node.text.strip() if desc_node is not None else ""
            if "<" in desc:
                # Quitar etiquetas HTML rudimentarias para el resumen
                import re
                desc = re.sub('<[^<]+?>', '', desc)
                
            published = pub_node.text.strip() if pub_node is not None else datetime.now().strftime("%B %d, %Y")
            
            # Filtrar por palabra clave si se especifica
            if palabra_clave.strip():
                pc = palabra_clave.lower().strip()
                if pc not in title.lower() and pc not in desc.lower():
                    continue
            
            articulos.append({
                "fuente": nombre_fuente,
                "enlace": link,
                "titulo": title,
                "resumen": desc,
                "autores": nombre_fuente,  # Atribución por defecto a la organización
                "fecha": published,
                "tipo": "Artículo Periodístico / Reporte"
            })
            
            if len(articulos) >= max_resultados:
                break
                
        print(f"[INGEST] RSS de {nombre_fuente} retornó {len(articulos)} resultados.")
        return articulos
        
    except Exception as err:
        print(f"[ERROR INGEST] Falla al parsear RSS de {nombre_fuente}: {err}")
        return []

# =====================================================================
# 2. Catálogo de Fuentes RSS Configuradas
# =====================================================================
FUENTES_RSS = {
    # 🔬 Universidades & Investigaciones Científicas
    "arxiv": {
        "nombre": "arXiv (cs.AI - Cornell Univ.)",
        "categoria": "Universidades & Ciencia",
        "tipo": "arxiv"
    },
    "ieee": {
        "nombre": "IEEE Spectrum (Robótica & IA)",
        "url": "https://spectrum.ieee.org/rss/artificial-intelligence/fulltext",
        "categoria": "Universidades & Ciencia",
        "tipo": "rss"
    },
    "nature": {
        "nombre": "Nature Machine Intelligence",
        "url": "https://www.nature.com/natmachintell.rss",
        "categoria": "Universidades & Ciencia",
        "tipo": "rss"
    },
    "mit": {
        "nombre": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "categoria": "Universidades & Ciencia",
        "tipo": "rss"
    },

    # 📰 Prensa Tecnológica Global
    "techcrunch": {
        "nombre": "TechCrunch (Artificial Intelligence)",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "categoria": "Prensa Tech Global",
        "tipo": "rss"
    },
    "wired": {
        "nombre": "Wired (AI & Tech)",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "categoria": "Prensa Tech Global",
        "tipo": "rss"
    },
    "venturebeat": {
        "nombre": "VentureBeat (Enterprise AI)",
        "url": "https://venturebeat.com/category/ai/feed/",
        "categoria": "Prensa Tech Global",
        "tipo": "rss"
    },

    # 🌐 Organismos & Coyuntura Global
    "bbc": {
        "nombre": "BBC News (Technology)",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "categoria": "Organismos & Coyuntura Global",
        "tipo": "rss"
    }
}

# =====================================================================
# 3. Función Unificada de Ingesta
# =====================================================================
def buscar_documentos_remotos(fuente_o_categoria: str, palabra_clave: str = "", limite: int = 3) -> List[Dict]:
    """
    Punto de entrada unificado para buscar documentos e informes en la web.
    Soporta buscar por clave específica de fuente, por categoría o en 'todas'.
    """
    target = fuente_o_categoria.lower().strip()
    resultados = []
    
    print(f"[INGEST] Iniciando búsqueda remota: filtro='{target}', palabra_clave='{palabra_clave}', limite={limite}")

    # Determinar qué fuentes consultar
    fuentes_a_consultar = []

    if target in ["todos", "all", "todas las fuentes (consolidado)"]:
        fuentes_a_consultar = list(FUENTES_RSS.keys())
    elif target in ["universidades & ciencia", "universidades", "ciencia"]:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Universidades & Ciencia"]
    elif target in ["prensa tech global", "prensa", "prensa tech"]:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Prensa Tech Global"]
    elif target in ["organismos & coyuntura global", "organismos", "coyuntura"]:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Organismos & Coyuntura Global"]
    else:
        # Buscar por clave específica o coincidencia parcial
        for k, v in FUENTES_RSS.items():
            if k in target or v["nombre"].lower() in target:
                fuentes_a_consultar.append(k)

    if not fuentes_a_consultar:
        # Fallback a todas si no se reconoce la categoría
        fuentes_a_consultar = list(FUENTES_RSS.keys())

    # Límite por fuente individual para no saturar
    limite_por_fuente = max(1, min(limite, 5))

    for key in fuentes_a_consultar:
        info = FUENTES_RSS.get(key)
        if not info:
            continue

        if info["tipo"] == "arxiv":
            res = consultar_arxiv(palabra_clave, max_resultados=limite_por_fuente)
            resultados.extend(res)
        elif info["tipo"] == "rss":
            res = consultar_rss(info["url"], info["nombre"], palabra_clave, max_resultados=limite_por_fuente)
            resultados.extend(res)

        if len(resultados) >= limite * len(fuentes_a_consultar):
            break

    print(f"[INGEST] Búsqueda finalizada. Total de documentos recuperados: {len(resultados)}")
    return resultados[:limite * 3]  # Retornar una lista acotada razonable

