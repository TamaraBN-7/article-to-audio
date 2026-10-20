"""Pruebas unitarias para el módulo article_extractor.

Verifica la validación de URLs (esquemas permitidos, prevención de SSRF)
y la extracción de artículos simulando respuestas web para no requerir conexión a Internet.
"""

import unittest
from unittest.mock import patch, MagicMock
from article_extractor import (
    validate_url,
    extract_article,
    InvalidURLError,
    ArticleExtractionError,
)


class TestURLExtractor(unittest.TestCase):
    """Pruebas de validación de URLs."""

    def test_valid_http_and_https_urls(self):
        """Verifica que las URLs con protocolos válidos son aceptadas."""
        self.assertEqual(validate_url("https://ejemplo.com/articulo"), "https://ejemplo.com/articulo")
        self.assertEqual(validate_url("http://noticias.es/post-1"), "http://noticias.es/post-1")
        # Debe limpiar espacios en blanco a los lados
        self.assertEqual(validate_url("  https://blog.com/ciencia  "), "https://blog.com/ciencia")

    def test_invalid_scheme(self):
        """Verifica que esquemas no HTTP/HTTPS son rechazados."""
        invalid_schemes = [
            "ftp://servidor.com/archivo.txt",
            "file:///Users/sandrabratosnuevo/documento.html",
            "javascript:alert(1)",
            "data:text/html,<h1>Hola</h1>",
        ]
        for url in invalid_schemes:
            with self.subTest(url=url):
                with self.assertRaises(InvalidURLError):
                    validate_url(url)

    def test_empty_or_malformed_urls(self):
        """Verifica el rechazo de URLs vacías o sin dominio."""
        with self.assertRaises(InvalidURLError):
            validate_url("")
        with self.assertRaises(InvalidURLError):
            validate_url("   ")
        with self.assertRaises(InvalidURLError):
            validate_url("not-a-valid-url")

    def test_ssrf_protection_blocks_localhost_and_private_ips(self):
        """Comprueba que se bloquean intentos de acceder a localhost o IPs privadas."""
        blocked_urls = [
            "http://localhost/admin",
            "https://127.0.0.1:8080/dashboard",
            "http://192.168.1.1/router",
            "http://10.0.0.1/secreto",
        ]
        for url in blocked_urls:
            with self.subTest(url=url):
                with self.assertRaises(InvalidURLError):
                    validate_url(url)


class TestArticleExtraction(unittest.TestCase):
    """Pruebas de extracción con simulación (mocks) de red."""

    @patch("article_extractor.Article")
    def test_extract_article_success(self, mock_article_class):
        """Verifica que se extrae correctamente un artículo con contenido suficiente."""
        mock_instance = MagicMock()
        mock_instance.title = "Título del artículo de prueba"
        mock_instance.text = "Este es un texto simulado de prueba con más de cien caracteres para comprobar que la función extract_article procesa la información sin errores y devuelve el diccionario estructurado."
        mock_instance.authors = ["Ana García", "Carlos Ruiz"]
        mock_instance.publish_date = None
        mock_instance.html = "<html><body><p>Contenido</p></body></html>"
        mock_article_class.return_value = mock_instance

        result = extract_article("https://ejemplo.com/articulo-test")

        self.assertEqual(result["title"], "Título del artículo de prueba")
        self.assertIn("Ana García", result["authors"])
        self.assertTrue(len(result["text"]) >= 100)

    @patch("article_extractor.Article")
    def test_extract_article_too_short_raises_error(self, mock_article_class):
        """Verifica que si el contenido extraído es muy corto, se lanza ArticleExtractionError."""
        mock_instance = MagicMock()
        mock_instance.title = "Aviso"
        mock_instance.text = "Página vacía."  # Menos de 100 caracteres
        mock_instance.html = "<html></html>"
        mock_article_class.return_value = mock_instance

        with self.assertRaises(ArticleExtractionError):
            extract_article("https://ejemplo.com/pagina-corta")


if __name__ == "__main__":
    unittest.main()
