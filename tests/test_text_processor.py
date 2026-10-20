"""Pruebas unitarias para el módulo text_processor.

Verifica la limpieza de texto (espacios redundantes, marcas editoriales y notas),
la sanitización de nombres de archivo y la división inteligente en fragmentos mediante NLTK.
"""

import unittest
from text_processor import (
    clean_text,
    sanitize_filename,
    split_text_into_chunks,
)


class TestTextCleaner(unittest.TestCase):
    """Pruebas para la función clean_text."""

    def test_clean_text_basic_spacing(self):
        """Verifica la eliminación de espacios y saltos de línea excesivos."""
        raw = "   Párrafo 1 con    muchos    espacios.  \n\n\n\n\n  Párrafo 2.   "
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "Párrafo 1 con muchos espacios.\n\nPárrafo 2.")

    def test_clean_text_removes_editorial_notes_and_citations(self):
        """Comprueba que se limpian enlaces como [editar] y notas numéricas [1]."""
        raw = "Historia del proyecto [editar]. Descubrimiento en 1990 [1] y confirmado después [nota 3]."
        cleaned = clean_text(raw)
        self.assertNotIn("[editar]", cleaned)
        self.assertNotIn("[1]", cleaned)
        self.assertNotIn("[nota 3]", cleaned)
        self.assertIn("Historia del proyecto . Descubrimiento en 1990 y confirmado después .", cleaned)

    def test_clean_text_empty_input(self):
        """Verifica que entradas vacías o no válidas devuelven una cadena vacía."""
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("   \n\n   "), "")
        self.assertEqual(clean_text(None), "")


class TestFilenameSanitizer(unittest.TestCase):
    """Pruebas para sanitize_filename."""

    def test_removes_accents_and_special_characters(self):
        """Comprueba que elimina tildes, signos de puntuación y símbolos conflictivos."""
        title = "¿Cómo programar en Python 3?: ¡Guía Rápida & Práctica!"
        safe = sanitize_filename(title)
        self.assertEqual(safe, "como_programar_en_python_3_guia_rapida_practica")

    def test_respects_max_length(self):
        """Verifica que respeta el límite máximo de caracteres sin cortar de forma fea."""
        long_title = "Un título extremadamente largo para un artículo que describe descubrimientos astronómicos fascinantes en galaxias lejanas"
        safe = sanitize_filename(long_title, max_length=30)
        self.assertTrue(len(safe) <= 30)
        self.assertFalse(safe.endswith("_"))

    def test_empty_or_special_only_title_uses_default(self):
        """Verifica el uso del nombre de reserva si no queda texto tras limpiar."""
        self.assertEqual(sanitize_filename("", default_name="audio_fallback"), "audio_fallback")
        self.assertEqual(sanitize_filename("??? / \\ ***", default_name="audio_fallback"), "audio_fallback")


class TestChunkSplitter(unittest.TestCase):
    """Pruebas para la división inteligente de textos con NLTK."""

    def test_split_preserves_sentences_without_breaking_abbreviations(self):
        """Comprueba que no rompe oraciones a la mitad ni confunde abreviaturas como 'Dr.'."""
        text = (
            "El Dr. Rodríguez llegó a las 10:00 h al laboratorio. "
            "Revisó todas las muestras con el microscopio óptico. "
            "El resultado fue plenamente satisfactorio."
        )
        # Forzamos fragmentos pequeños (~70 caracteres) para obligar a dividir
        chunks = split_text_into_chunks(text, max_chunk_chars=75, language="es")
        self.assertTrue(len(chunks) >= 2)
        # La primera frase debe contener "Dr. Rodríguez" íntegro sin romperse en "Dr."
        self.assertIn("Dr. Rodríguez", chunks[0])

    def test_split_empty_text(self):
        """Verifica que textos vacíos devuelven lista vacía."""
        self.assertEqual(split_text_into_chunks(""), [])
        self.assertEqual(split_text_into_chunks("   "), [])


if __name__ == "__main__":
    unittest.main()
