"""Punto de entrada principal para la aplicación: Convertidor de Artículos Web a Audio MP3.

Coordina la validación y extracción del artículo (article_extractor),
la limpieza y fragmentación del texto (text_processor),
y la síntesis de voz en archivo MP3 (audio_generator).
"""

import warnings
warnings.filterwarnings("ignore", message=".*urllib3.*NotOpenSSLWarning.*")

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()


from article_extractor import (
    validate_url,
    extract_article,
    InvalidURLError,
    ArticleExtractionError,
)
from text_processor import (
    clean_text,
    sanitize_filename,
    split_text_into_chunks,
)
from audio_generator import (
    generate_audio_from_text,
    AudioGenerationError,
)

DEFAULT_LANG = os.getenv("DEFAULT_LANGUAGE", "es")
DEFAULT_OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))


def print_banner() -> None:
    """Muestra la cabecera informativa de la aplicación."""
    print("=" * 65)
    print(" 🎙️  CONVERTIDOR DE ARTÍCULOS WEB A AUDIO MP3  🎙️ ")
    print("=" * 65)


def get_user_inputs() -> tuple:
    """Solicita al usuario la URL y el idioma a través de la terminal interactiva.

    Returns:
        tuple: (url_limpia, codigo_idioma)
    """
    # 1. Solicitar URL
    if len(sys.argv) > 1:
        # Permite ejecutar: python main.py https://sitio.com/articulo
        raw_url = sys.argv[1].strip()
        print(f"\n🔗 URL recibida por parámetro: {raw_url}")
    else:
        print("\nIntroduce la dirección web del artículo que deseas escuchar:")
        raw_url = input("👉 URL (http/https): ").strip()

    valid_url = validate_url(raw_url)

    # 2. Selección de idioma
    if len(sys.argv) > 2:
        selected_lang = sys.argv[2].strip().lower()
        print(f"🗣️  Idioma recibido por parámetro: {selected_lang}")
    else:
        print(f"\nSelecciona el idioma de la voz [Enter para español '{DEFAULT_LANG}']:")
        print("  • 'es' - Español")
        print("  • 'en' - Inglés")
        print("  • 'fr' - Francés")
        print("  • 'de' - Alemán")
        selected_lang = input(f"👉 Idioma [{DEFAULT_LANG}]: ").strip().lower()

    if not selected_lang:
        selected_lang = DEFAULT_LANG

    return valid_url, selected_lang


def process_article_to_audio(url: str, language: str = "es", output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Ejecuta el flujo completo de extracción, limpieza y conversión a audio.

    Args:
        url: URL validada del artículo web.
        language: Código de idioma para la voz ('es', 'en', etc.).
        output_dir: Carpeta donde se guardará el archivo MP3 resultante.

    Returns:
        Path: Ruta del archivo MP3 final generado.
    """
    # Paso 1: Extracción
    print("\n⏳ [1/4] Descargando y analizando el contenido del artículo...")
    article_data = extract_article(url)
    title = article_data["title"]
    raw_text = article_data["text"]

    print(f"   ✓ Título detectado: \"{title}\"")
    if article_data.get("authors"):
        print(f"   ✓ Autor(es): {', '.join(article_data['authors'])}")

    # Paso 2: Limpieza y normalización
    print("\n⏳ [2/4] Limpiando el texto y eliminando contenido residual...")
    cleaned_text = clean_text(raw_text)
    char_count = len(cleaned_text)
    word_count = len(cleaned_text.split())

    print(f"   ✓ Caracteres limpios: {char_count:,}")
    print(f"   ✓ Palabras estimadas: {word_count:,}")

    # Paso 3: División en oraciones inteligentes con NLTK
    print("\n⏳ [3/4] Analizando oraciones con NLTK...")
    chunks = split_text_into_chunks(cleaned_text, max_chunk_chars=2000, language=language)
    print(f"   ✓ Fragmentos generados: {len(chunks)} parte(s)")

    # Paso 4: Generación de audio
    safe_name = sanitize_filename(title)
    output_file = output_dir / f"{safe_name}.mp3"

    print(f"\n⏳ [4/4] Sintetizando voz con gTTS y generando archivo MP3...")
    print(f"   (Idioma: {language} | Destino: {output_file.name})")

    final_path = generate_audio_from_text(
        text_or_chunks=chunks,
        output_path=output_file,
        language=language,
    )

    return final_path, title, char_count, word_count, len(chunks)


def main() -> None:
    """Función principal con interfaz de usuario por consola y control de excepciones."""
    print_banner()

    try:
        url, language = get_user_inputs()
        final_mp3, title, chars, words, chunks_count = process_article_to_audio(url, language)

        file_size_mb = final_mp3.stat().st_size / (1024 * 1024)

        print("\n" + "=" * 65)
        print("🎉  ¡PROCESO COMPLETADO CON ÉXITO!  🎉")
        print("=" * 65)
        print(f"📰 Título del artículo: {title}")
        print(f"📊 Estadísticas:        {chars:,} caracteres | {words:,} palabras | {chunks_count} fragmentos")
        print(f"📦 Tamaño del audio:    {file_size_mb:.2f} MB")
        print(f"🎧 Archivo generado en: {final_mp3.resolve()}")
        print("=" * 65)
        print(f"💡 Para escucharlo ahora en tu Mac, ejecuta en tu terminal:")
        print(f"   afplay \"{final_mp3}\"")
        print("   O haz doble clic sobre él en el Finder.\n")

    except KeyboardInterrupt:
        print("\n\n⚠️ Operación cancelada por el usuario. ¡Hasta pronto!")
        sys.exit(0)
    except InvalidURLError as err:
        print(f"\n❌ Error de validación en la URL: {err}\n")
        sys.exit(1)
    except ArticleExtractionError as err:
        print(f"\n❌ Error al extraer el artículo: {err}\n")
        sys.exit(1)
    except AudioGenerationError as err:
        print(f"\n❌ Error al generar el archivo de audio: {err}\n")
        sys.exit(1)
    except Exception as err:
        print(f"\n❌ Ocurrió un error inesperado: {err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
