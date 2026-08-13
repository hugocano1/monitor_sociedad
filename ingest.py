import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
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
# 1. Búsqueda en Tiempo Real en Google News Global
# =====================================================================
def consultar_google_news(palabra_clave: str, max_resultados: int = 5) -> List[Dict]:
    """
    Rastrea Google News en tiempo real para cualquier término de búsqueda 
    (ej: 'Gemini 3.7', 'Claude 3.7', 'Robótica Humanode').
    """
    if not palabra_clave.strip():
        palabra_clave = "Artificial Intelligence"
        
    query_encoded = urllib.parse.quote(palabra_clave.strip())
    url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-US&gl=US&ceid=US:en"
    
    print(f"[INGEST] Consultando Google News Realtime: {url}")
    try:
        req = urllib.request.Request(url, headers=HEADERS_NAVEGADOR)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        channel = root.find('channel')
        if channel is None:
            return []
            
        articulos = []
        for item in channel.findall('item'):
            title_node = item.find('title')
            link_node = item.find('link')
            desc_node = item.find('description')
            pub_node = item.find('pubDate')
            source_node = item.find('source')
            
            title = title_node.text.strip() if title_node is not None else "Sin Título"
            link = link_node.text.strip() if link_node is not None else ""
            desc = desc_node.text.strip() if desc_node is not None else ""
            if "<" in desc:
                desc = re.sub('<[^<]+?>', '', desc)
                
            published = pub_node.text.strip() if pub_node is not None else datetime.now().strftime("%B %d, %Y")
            nombre_fuente = source_node.text.strip() if source_node is not None and source_node.text else "Google News Global"
            
            articulos.append({
                "fuente": f"Prensa Tech ({nombre_fuente})",
                "enlace": link,
                "titulo": title,
                "resumen": desc if desc else title,
                "autores": nombre_fuente,
                "fecha": published,
                "tipo": "Noticia de Prensa Tecnológica"
            })
            
            if len(articulos) >= max_resultados:
                break
                
        print(f"[INGEST] Google News retornó {len(articulos)} noticias para '{palabra_clave}'.")
        return articulos
    except Exception as err:
        print(f"[ERROR INGEST] Falla al consultar Google News: {err}")
        return []


# =====================================================================
# 2. Recuperación de Papers de arXiv (Universidad de Cornell)
# =====================================================================
def consultar_arxiv(palabra_clave: str = "", max_resultados: int = 5) -> List[Dict]:
    """
    Consulta la API abierta de arXiv para recuperar los papers más recientes 
    en la categoría de Inteligencia Artificial (cs.AI).
    """
    query = "cat:cs.AI"
    if palabra_clave.strip():
        pk_safe = palabra_clave.strip().replace(" ", "+")
        query += f"+AND+all:{pk_safe}"
        
    url = (
        f"http://export.arxiv.org/api/query?search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_resultados}"
    )
    
    print(f"[INGEST] Consultando arXiv: {url}")
    try:
        req = urllib.request.Request(url, headers=HEADERS_NAVEGADOR)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            id_url = entry.find('atom:id', ns).text.strip()
            title = entry.find('atom:title', ns).text.strip().replace("\n", " ")
            summary = entry.find('atom:summary', ns).text.strip().replace("\n", " ")
            published = entry.find('atom:published', ns).text.strip()
            
            autores_list = []
            for author in entry.findall('atom:author', ns):
                name_node = author.find('atom:name', ns)
                if name_node is not None:
                    autores_list.append(name_node.text.strip())
            
            autores = ", ".join(autores_list)
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
# 3. Recuperación de Artículos desde Feeds RSS Públicos (MIT, WEF, Wired)
# =====================================================================
def consultar_rss(url_feed: str, nombre_fuente: str, palabra_clave: str = "", max_resultados: int = 5) -> List[Dict]:
    """
    Rastrea feeds RSS estándar en formato XML para extraer los artículos más recientes.
    """
    print(f"[INGEST] Consultando RSS de {nombre_fuente}: {url_feed}")
    try:
        req = urllib.request.Request(url_feed, headers=HEADERS_NAVEGADOR)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        channel = root.find('channel')
        if channel is None:
            return []
            
        articulos = []
        kw_words = [w.lower().strip() for w in palabra_clave.split() if w.strip()]
        
        for item in channel.findall('item'):
            title_node = item.find('title')
            link_node = item.find('link')
            desc_node = item.find('description')
            pub_node = item.find('pubDate')
            
            title = title_node.text.strip() if title_node is not None else "Sin Título"
            link = link_node.text.strip() if link_node is not None else ""
            desc = desc_node.text.strip() if desc_node is not None else ""
            if "<" in desc:
                desc = re.sub('<[^<]+?>', '', desc)
                
            published = pub_node.text.strip() if pub_node is not None else datetime.now().strftime("%B %d, %Y")
            
            # Coincidencia flexible de palabras clave (todas las palabras deben estar presentes)
            if kw_words:
                text_to_check = (title + " " + desc).lower()
                if not all(w in text_to_check for w in kw_words):
                    continue
            
            articulos.append({
                "fuente": nombre_fuente,
                "enlace": link,
                "titulo": title,
                "resumen": desc,
                "autores": nombre_fuente,
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
# 4. Catálogo de Fuentes RSS Configuradas
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
# 5. Función Unificada de Ingesta
# =====================================================================
def buscar_documentos_remotos(fuente_o_categoria: str, palabra_clave: str = "", limite: int = 3) -> List[Dict]:
    """
    Punto de entrada unificado para buscar documentos e informes en la web.
    """
    raw_target = fuente_o_categoria.lower().strip()
    target = re.sub(r'\(.*?\)', '', raw_target).strip()
    resultados = []
    
    print(f"[INGEST] Iniciando búsqueda remota: raw='{raw_target}', target='{target}', palabra_clave='{palabra_clave}', limite={limite}")

    # Si se especifica la categoría Google News explícita
    if "google news" in raw_target:
        return consultar_google_news(palabra_clave, max_resultados=limite)

    # Determinar fuentes estáticas a consultar
    fuentes_a_consultar = []
    if target in ["todos", "all", "todas las fuentes", "todas las fuentes (consolidado global)"]:
        fuentes_a_consultar = list(FUENTES_RSS.keys())
    elif "universidades" in target or "ciencia" in target:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Universidades & Ciencia"]
    elif "prensa" in target or "prensa tech" in target:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Prensa Tech Global"]
    elif "organismos" in target or "coyuntura" in target:
        fuentes_a_consultar = [k for k, v in FUENTES_RSS.items() if v["categoria"] == "Organismos & Coyuntura Global"]
    else:
        for k, v in FUENTES_RSS.items():
            if k in target or v["nombre"].lower() in target:
                fuentes_a_consultar.append(k)

    if not fuentes_a_consultar:
        fuentes_a_consultar = list(FUENTES_RSS.keys())

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

        if len(resultados) >= limite:
            break

    # Si hay palabra clave específica (ej: Gemini 3.7) y las fuentes estáticas devolvieron menos resultados de los solicitados,
    # consultar Google News Realtime como respaldo dinámico para no dejar al usuario sin resultados.
    if palabra_clave.strip() and len(resultados) < limite:
        print(f"[INGEST] Fuentes estáticas retornaron solo {len(resultados)} resultados para '{palabra_clave}'. Consultando Google News Realtime...")
        res_gn = consultar_google_news(palabra_clave, max_resultados=limite - len(resultados))
        # Evitar duplicados por URL
        urls_existentes = {r.get('enlace') for r in resultados}
        for g in res_gn:
            if g.get('enlace') not in urls_existentes:
                resultados.append(g)

    return resultados[:limite * 2]
