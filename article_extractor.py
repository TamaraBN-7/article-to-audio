"""Módulo para validar URLs y extraer el contenido principal de artículos web.

Utiliza la biblioteca newspaper4k para procesar el HTML y extraer el título,
autores y texto principal del artículo, ignorando menús y publicidad.
"""

import warnings
warnings.filterwarnings("ignore", message=".*urllib3.*NotOpenSSLWarning.*")

from urllib.parse import urlparse

import ipaddress
import socket
from typing import Dict, Any
from bs4 import BeautifulSoup
from newspaper import Article



class InvalidURLError(ValueError):
    """Se lanza cuando la URL proporcionada no es válida o no es segura."""
    pass


class ArticleExtractionError(RuntimeError):
    """Se lanza cuando ocurre un problema al descargar o parsear el artículo."""
    pass


def validate_url(url: str) -> str:
    """Valida el formato de la URL y comprueba que sea una dirección HTTP/HTTPS pública.

    Args:
        url: Cadena con la URL a validar.

    Returns:
        str: La URL limpia y validada.

    Raises:
        InvalidURLError: Si la URL está vacía, no es HTTP/HTTPS o apunta a redes locales/privadas.
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError("La URL no puede estar vacía.")

    url = url.strip()
    parsed = urlparse(url)

    # 1. Validar esquema (solo HTTP y HTTPS)
    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidURLError(
            f"Protocolo no soportado '{parsed.scheme}'. Solo se aceptan direcciones 'http://' o 'https://'."
        )

    # 2. Validar que tenga un dominio (hostname)
    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("La URL no contiene un nombre de dominio válido.")

    # 3. Seguridad básica contra SSRF: evitar consultas a localhost y redes privadas
    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        raise InvalidURLError("No está permitido procesar direcciones locales (localhost).")

    ip_obj = None
    try:
        ip_obj = ipaddress.ip_address(hostname)
    except ValueError:
        # No es una IP numérica directa, es un nombre de dominio normal (ej: elpais.com)
        pass

    if ip_obj and (ip_obj.is_private or ip_obj.is_loopback):
        raise InvalidURLError("No se permite acceder a direcciones IP privadas o locales.")

    return url


def _extract_from_wikipedia(html: str) -> str:
    """Extrae todos los párrafos de un artículo de Wikipedia incluyendo la introducción.

    Args:
        html: Contenido HTML descargado de la página.

    Returns:
        str: Texto de los párrafos enciclopédicos unidos por saltos de línea.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", class_="mw-parser-output")
    if not content:
        return ""

    paragraphs = []
    for p in content.find_all("p"):
        # Ignorar párrafos que pertenezcan a tablas, infoboxes o barras de navegación
        if p.find_parent("table") or p.find_parent("div", class_="infobox") or p.find_parent("div", class_="navbox"):
            continue
        text = p.get_text().strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_article(url: str, min_chars: int = 100) -> Dict[str, Any]:
    """Descarga y extrae los datos principales de un artículo web a partir de su URL.

    Args:
        url: Dirección web del artículo.
        min_chars: Longitud mínima requerida del texto para considerarlo un artículo válido.

    Returns:
        Dict[str, Any]: Diccionario con la información extraída:
            - 'title': Título del artículo.
            - 'text': Texto completo del artículo.
            - 'url': URL original del artículo.
            - 'authors': Lista de autores identificados.
            - 'publish_date': Fecha de publicación (si está disponible).

    Raises:
        InvalidURLError: Si la URL no supera las comprobaciones de validación.
        ArticleExtractionError: Si falla la descarga, el análisis o el contenido es insuficiente.
    """
    valid_url = validate_url(url)

    try:
        # Creamos la instancia del artículo indicando el idioma si es necesario
        article = Article(valid_url)
        # Descarga el HTML de la página web
        article.download()
        # Procesa el HTML y extrae título, texto, imágenes, etc.
        article.parse()
    except Exception as exc:
        raise ArticleExtractionError(
            f"No fue posible descargar o analizar el artículo desde '{valid_url}'. Detalle: {exc}"
        ) from exc

    title = (article.title or "").strip()
    text = (article.text or "").strip()

    # Si el artículo proviene de Wikipedia/MediaWiki, extraemos también los párrafos
    # de la introducción que el algoritmo top-node de newspaper suele omitir
    if "wikipedia.org" in valid_url.lower() or "mw-parser-output" in (article.html or ""):
        wiki_text = _extract_from_wikipedia(article.html)
        if wiki_text and len(wiki_text) > len(text):
            text = wiki_text

    # Comprobación de que se obtuvo texto suficiente
    if len(text) < min_chars:
        raise ArticleExtractionError(
            f"El contenido extraído es demasiado corto ({len(text)} caracteres). "
            "Es posible que la página requiera suscripción (paywall), use JavaScript dinámico "
            "o no contenga un artículo legible."
        )

    # Si no se detectó un título claro, se asigna uno por defecto
    if not title:
        title = "Artículo sin título"

    return {
        "title": title,
        "text": text,
        "url": valid_url,
        "authors": article.authors,
        "publish_date": article.publish_date,
    }


if __name__ == "__main__":
    # Prueba manual rápida si se ejecuta este módulo directamente
    import sys

    test_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://es.wikipedia.org/wiki/Python_(lenguaje_de_programaci%C3%B3n)"
    )

    print(f"Probando extracción con: {test_url}\n")
    try:
        result = extract_article(test_url)
        print(f"✅ Título: {result['title']}")
        print(f"✅ Caracteres extraídos: {len(result['text'])}")
        print(f"✅ Primeras 300 letras:\n{result['text'][:300]}...")
    except (InvalidURLError, ArticleExtractionError) as error:
        print(f"❌ Error en la extracción: {error}")
