"""Módulo para la limpieza, normalización y fragmentación de texto.

Combina funciones de Python estándar (expresiones regulares y manipulación de cadenas)
con NLTK para dividir textos largos en frases naturales sin romper el sentido ni abreviaturas.
"""

import re
import unicodedata
from typing import List
import nltk
from nltk.tokenize import sent_tokenize


def clean_text(raw_text: str) -> str:
    """Limpia el texto eliminando espacios redundantes, saltos de línea repetidos y líneas vacías.

    Tareas realizadas con Python estándar:
    - Normaliza caracteres Unicode (evita caracteres invisibles o formatos extraños).
    - Convierte múltiples espacios horizontales en un solo espacio.
    - Reduce 3 o más saltos de línea consecutivos a máximo dos saltos de línea (párrafos limpios).
    - Elimina espacios en blanco al inicio y al final de cada línea.

    Args:
        raw_text: Texto original extraído del artículo.

    Returns:
        str: Texto limpio y listo para procesar.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    # 1. Normalización Unicode (NFKC unifica símbolos equivalentes y espacios de ancho cero)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Reemplazar tabulaciones y retornos de carro
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")

    # 3. Limpiar referencias y marcas editoriales típicas de la web (ej: [editar], [edit], [1], [nota 2])
    text = re.sub(r"\[(?:editar|edit|cita requerida|citation needed)\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\d+\]", "", text)  # notas al pie numéricas estilo [1], [2]
    text = re.sub(r"\[(?:nota|ref)\s*\d+\]", "", text, flags=re.IGNORECASE)

    # 4. Limpiar espacios múltiples dentro de cada línea
    lines = [re.sub(r"[ ]+", " ", line).strip() for line in text.split("\n")]

    # 5. Eliminar líneas vacías repetidas consecutivas
    cleaned_lines: List[str] = []
    previous_was_empty = False

    for line in lines:
        if line:
            cleaned_lines.append(line)
            previous_was_empty = False
        else:
            if not previous_was_empty:
                cleaned_lines.append("")
                previous_was_empty = True

    result = "\n".join(cleaned_lines).strip()
    return result


def sanitize_filename(title: str, max_length: int = 60, default_name: str = "articulo") -> str:
    """Genera un nombre de archivo seguro y legible para el sistema operativo a partir de un título.

    - Convierte a minúsculas y sustituye espacios por guiones bajos.
    - Elimina tildes, signos de puntuación problemáticos (\, /, :, *, ?, ", <, >, |).
    - Limita la longitud máxima para evitar nombres de archivo excesivamente largos.

    Args:
        title: Título del artículo o texto a sanitizar.
        max_length: Longitud máxima de caracteres para el nombre resultante.
        default_name: Nombre por defecto en caso de que el título quede vacío tras limpiar.

    Returns:
        str: Nombre seguro apto para usar como archivo (sin extensión .mp3).
    """
    if not title or not isinstance(title, str):
        return default_name

    # Normalizar para separar tildes de las letras (ej: 'ó' -> 'o' + acento)
    normalized = unicodedata.normalize("NFD", title)
    # Filtrar marcas de acento para dejar solo caracteres ASCII básicos
    ascii_title = "".join(char for char in normalized if unicodedata.category(char) != "Mn")

    # Reemplazar cualquier carácter que no sea letra, número o espacio por un guion bajo
    safe_chars = re.sub(r"[^\w\s-]", "", ascii_title).strip().lower()
    # Sustituir espacios o guiones consecutivos por un único guion bajo
    filename = re.sub(r"[-\s]+", "_", safe_chars)

    # Recortar si supera la longitud máxima permitida
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip("_")

    return filename if filename else default_name


def split_text_into_chunks(text: str, max_chunk_chars: int = 2500, language: str = "spanish") -> List[str]:
    """Divide un texto largo en fragmentos que no superen un número máximo de caracteres,
    respetando SIEMPRE los límites de oraciones mediante NLTK.

    ¿Por qué usar NLTK aquí y no un simple text.split('.')?
    Un `.split('.')` rompería abreviaturas como "pág. 5", "Sr. García" o "3.14 km".
    NLTK entiende la gramática y sabe distinguir cuándo un punto es el final de una oración
    y cuándo forma parte de una abreviatura o número decimal.

    Args:
        text: Texto completo a dividir.
        max_chunk_chars: Límite aproximado de caracteres por fragmento.
        language: Idioma para el modelo de tokenización de NLTK ('spanish', 'english', etc.).

    Returns:
        List[str]: Lista de fragmentos de texto coherentes listos para enviar al sintetizador de voz.
    """
    if not text or not text.strip():
        return []

    # Mapeo de códigos de idioma simples al nombre que espera NLTK
    lang_mapping = {
        "es": "spanish",
        "en": "english",
        "fr": "french",
        "de": "german",
        "it": "italian",
        "pt": "portuguese",
    }
    nltk_lang = lang_mapping.get(language.lower(), language.lower())

    try:
        sentences = sent_tokenize(text, language=nltk_lang)
    except Exception:
        # Si el idioma no estuviera descargado o soportado, recurrimos a español/inglés por defecto
        try:
            sentences = sent_tokenize(text, language="spanish")
        except Exception:
            # Plan B: división por saltos de línea y puntos simples si NLTK fallara
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence)

        # Si una sola frase supera el límite máximo por sí misma, se añade individualmente
        if sentence_length > max_chunk_chars:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            chunks.append(sentence)
            continue

        # Si añadir la frase supera el límite, cerramos el fragmento actual
        if current_length + sentence_length + 1 > max_chunk_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length + (1 if current_length > 0 else 0)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


if __name__ == "__main__":
    # Prueba rápida del módulo
    sample_text = (
        "El Dr. García presentó el nuevo informe a las 14:30 h.   \n\n\n\n"
        "El coste estimado fue de 1.500 € aprox. y los resultados fueron excelentes.\n\n"
        "¿Quién lo hubiera imaginado? ¡Es impresionante! Visite www.ejemplo.com para más datos."
    )

    print("--- Texto limpio ---")
    cleaned = clean_text(sample_text)
    print(repr(cleaned))

    print("\n--- Nombre de archivo sanitizado ---")
    title_example = "¿Cómo aprender Python en 2026? Guía Definitiva: ¡Paso a Paso!"
    safe_name = sanitize_filename(title_example)
    print(f"Original: {title_example}")
    print(f"Seguro:   {safe_name}.mp3")

    print("\n--- Fragmentación inteligente con NLTK ---")
    test_chunks = split_text_into_chunks(cleaned, max_chunk_chars=80, language="es")
    for idx, chunk in enumerate(test_chunks, start=1):
        print(f"Fragmento {idx} ({len(chunk)} chars): {chunk}")
