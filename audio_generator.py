"""Módulo para la síntesis de voz (Text-to-Speech) y generación de archivos MP3.

Utiliza gTTS (Google Text-to-Speech) para transformar texto en voz.
Si el texto viene dividido en fragmentos, genera cada parte y las une
de forma limpia usando ffmpeg (a través de imageio-ffmpeg) para garantizar
que el archivo MP3 sea 100% compatible con reproductores de macOS (QuickTime, Música),
Windows y navegadores web.
"""

import warnings
warnings.filterwarnings("ignore", message=".*urllib3.*NotOpenSSLWarning.*")

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Union
from gtts import gTTS
from gtts.tts import gTTSError

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = None


class AudioGenerationError(RuntimeError):
    """Se lanza cuando ocurre un fallo al sintetizar la voz o guardar el archivo MP3."""
    pass


def concatenate_mp3_files(source_files: List[Path], target_file: Path) -> None:
    """Une múltiples archivos MP3 en un único archivo final garantizando compatibilidad total.

    Utiliza ffmpeg si está disponible (mediante imageio-ffmpeg o el sistema) para
    generar un stream de audio continuo con encabezados correctos de duración.
    Si ffmpeg no estuviera disponible, utiliza concatenación binaria como respaldo.

    Args:
        source_files: Lista de rutas a los archivos MP3 temporales.
        target_file: Ruta de destino para el MP3 unificado.
    """
    if not source_files:
        raise AudioGenerationError("No hay fragmentos de audio para unir.")

    target_file.parent.mkdir(parents=True, exist_ok=True)

    # Si solo hay un archivo y ffmpeg está disponible, normalizamos el header
    if len(source_files) == 1 and not FFMPEG_EXE:
        shutil.copyfile(source_files[0], target_file)
        return

    # Método 1: ffmpeg concat demuxer (produce MP3s perfectamente compatibles con QuickTime/Music)
    if FFMPEG_EXE:
        concat_list_file = target_file.parent / f"concat_{target_file.stem}.txt"
        try:
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for file_path in source_files:
                    # Escapar comillas simples para la sintaxis de ffmpeg concat
                    escaped_path = str(file_path.resolve()).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            cmd = [
                FFMPEG_EXE,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_file),
                "-acodec", "copy",
                str(target_file),
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and target_file.exists() and target_file.stat().st_size > 0:
                return
        except Exception:
            pass
        finally:
            if concat_list_file.exists():
                concat_list_file.unlink()

    # Método 2: Respaldo binario si ffmpeg fallara
    with open(target_file, "wb") as outfile:
        for file_path in source_files:
            with open(file_path, "rb") as infile:
                shutil.copyfileobj(infile, outfile)


def generate_audio_from_text(
    text_or_chunks: Union[str, List[str]],
    output_path: Union[str, Path],
    language: str = "es",
    slow: bool = False,
) -> Path:
    """Genera un archivo MP3 a partir de una cadena de texto o una lista de fragmentos.

    Args:
        text_or_chunks: Texto completo o lista de fragmentos generados por split_text_into_chunks.
        output_path: Ruta completa donde guardar el MP3 resultante.
        language: Código de idioma ('es' para español, 'en' para inglés, etc.).
        slow: True para locución más pausada, False para velocidad normal.

    Returns:
        Path: Ruta confirmada del archivo MP3 generado.

    Raises:
        AudioGenerationError: Si la síntesis falla por errores de red, permisos o parámetros inválidos.
    """
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Normalizar la entrada a una lista de fragmentos no vacíos
    if isinstance(text_or_chunks, str):
        chunks = [text_or_chunks.strip()] if text_or_chunks.strip() else []
    else:
        chunks = [c.strip() for c in text_or_chunks if c and c.strip()]

    if not chunks:
        raise AudioGenerationError("No se proporcionó texto válido para generar el audio.")

    temp_dir = Path(tempfile.mkdtemp(prefix="tts_chunks_"))

    try:
        temp_audio_files: List[Path] = []

        total_chunks = len(chunks)
        for index, chunk in enumerate(chunks, start=1):
            temp_file = temp_dir / f"chunk_{index:04d}.mp3"
            print(f"   🎙️  Sintetizando audio: parte {index} de {total_chunks}...", flush=True)
            try:
                tts = gTTS(text=chunk, lang=language, slow=slow)
                tts.save(str(temp_file))
            except gTTSError as exc:
                raise AudioGenerationError(
                    f"Error de la API de gTTS al sintetizar el fragmento {index}: {exc}"
                ) from exc
            except Exception as exc:
                raise AudioGenerationError(
                    f"Fallo de conexión al comunicarse con el servicio de voz: {exc}"
                ) from exc

            if not temp_file.exists() or temp_file.stat().st_size == 0:
                raise AudioGenerationError(
                    f"El archivo temporal para el fragmento {index} no se generó correctamente."
                )

            temp_audio_files.append(temp_file)

        print("   🔗 Ensamblando y optimizando el archivo MP3 final...", flush=True)
        # Unir todos los fragmentos
        concatenate_mp3_files(temp_audio_files, destination)

        if not destination.exists() or destination.stat().st_size == 0:
            raise AudioGenerationError("El archivo MP3 final no se pudo crear o está vacío.")

        return destination

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Probando generación de audio con compatibilidad total...")
    test_output = Path("output/prueba_audio.mp3")

    test_fragments = [
        "Bienvenido a tu convertidor de artículos web a formato de audio MP3.",
        "El sistema divide el texto en oraciones completas y las sintetiza de manera natural.",
        "Este archivo es totalmente compatible con QuickTime, Apple Music y cualquier reproductor.",
    ]

    try:
        result_path = generate_audio_from_text(
            text_or_chunks=test_fragments,
            output_path=test_output,
            language="es",
        )
        file_size_kb = result_path.stat().st_size / 1024
        print(f"✅ ¡Audio generado con éxito!")
        print(f"📁 Ruta: {result_path}")
        print(f"📦 Tamaño: {file_size_kb:.1f} KB")
    except AudioGenerationError as error:
        print(f"❌ Error al generar audio: {error}")
