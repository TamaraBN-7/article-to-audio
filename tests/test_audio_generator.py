"""Pruebas unitarias para el módulo audio_generator.

Utiliza simulaciones (mocks) de la API de gTTS para verificar la lógica de
generación, concatenación y manejo de errores sin necesidad de conexión a Internet.
"""

import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock
from audio_generator import (
    generate_audio_from_text,
    concatenate_mp3_files,
    AudioGenerationError,
)


class TestAudioGenerator(unittest.TestCase):
    """Pruebas para la generación y ensamblado de audio."""

    def setUp(self):
        """Crea un directorio temporal para las pruebas."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.test_dir.name) / "test_result.mp3"

    def tearDown(self):
        """Limpia el directorio temporal tras cada prueba."""
        self.test_dir.cleanup()

    def test_empty_input_raises_audio_error(self):
        """Verifica que si no hay texto para sintetizar, se lanza AudioGenerationError."""
        with self.assertRaises(AudioGenerationError):
            generate_audio_from_text("", self.output_path)
        with self.assertRaises(AudioGenerationError):
            generate_audio_from_text([], self.output_path)

    @patch("audio_generator.gTTS")
    def test_generate_audio_with_mocked_tts(self, mock_gtts_class):
        """Verifica que se coordinan correctamente gTTS y la concatenación."""
        # Simulamos que gTTS guarda un archivo no vacío
        def fake_save(target_path):
            with open(target_path, "wb") as f:
                f.write(b"FAKE_MP3_DATA_STREAM")

        mock_instance = MagicMock()
        mock_instance.save.side_effect = fake_save
        mock_gtts_class.return_value = mock_instance

        chunks = ["Primer fragmento de prueba.", "Segundo fragmento para unir."]
        result_path = generate_audio_from_text(chunks, self.output_path, language="es")

        self.assertTrue(result_path.exists())
        self.assertGreater(result_path.stat().st_size, 0)
        # Debe haberse llamado a gTTS dos veces (una por fragmento)
        self.assertEqual(mock_gtts_class.call_count, 2)

    def test_concatenate_single_file(self):
        """Verifica que unir una lista con un único archivo lo copia correctamente."""
        source = Path(self.test_dir.name) / "single_chunk.mp3"
        target = Path(self.test_dir.name) / "final.mp3"
        source.write_bytes(b"SINGLE_CHUNK_BYTES")

        concatenate_mp3_files([source], target)

        self.assertTrue(target.exists())
        self.assertEqual(target.read_bytes(), b"SINGLE_CHUNK_BYTES")


if __name__ == "__main__":
    unittest.main()
