# 🎙️ Convertidor de Artículos Web a Audio MP3 (Web-to-Audio)

Una aplicación en Python diseñada para transformar artículos publicados en páginas web en audiolibros o pistas de voz en formato MP3 de alta calidad a partir de cualquier URL.

El programa extrae el contenido editorial limpio, divide el texto respetando los límites naturales de las oraciones mediante procesamiento de lenguaje natural (PLN) y sintetiza el audio con Google Text-to-Speech (gTTS), optimizando el archivo final para su reproducción inmediata en cualquier dispositivo.

---

## 🌟 Características principales

- **Extracción de contenido inteligente**: Utiliza `newspaper4k` y `BeautifulSoup` para extraer el título, autor y cuerpo del artículo, descartando menús, barras de navegación y anuncios publicitarios.
- **Soporte para artículos de prensa y Wikipedia**: Detecta estructuras enciclopédicas y recupera introducciones completas sin omitir secciones.
- **Limpieza y normalización de texto**: Elimina espacios redundantes, marcas editoriales (`[editar]`) y notas al pie (`[1]`, `[nota 2]`) para una locución fluida y agradable.
- **Fragmentación sintáctica con NLTK**: Divide artículos extensos en bloques de audio respetando siempre el final de cada oración sin romper palabras ni abreviaturas (`Dr.`, `Srta.`, etc.).
- **Unión y optimización de audio MP3**: Ensambla los fragmentos generados mediante `imageio-ffmpeg`, produciendo archivos MP3 compatibles al 100% con Apple QuickTime, Música, VLC, reproductores móviles y navegadores.
- **Seguridad incorporada**: Protección contra ataques SSRF (*Server-Side Request Forgery*), bloqueando accesos a `localhost` y direcciones IP privadas. Sanitización estricta de nombres de archivos.
- **Suite de pruebas unitarias**: 17 pruebas automatizadas que funcionan sin conexión a Internet utilizando simulaciones (*mocks*).

---

## 📁 Estructura del proyecto

```text
WEB:MP3/
├── main.py                 # Punto de entrada interactivo y CLI
├── article_extractor.py    # Validación de URLs y descarga del contenido
├── text_processor.py       # Limpieza, sanitización y segmentación con NLTK
├── audio_generator.py      # Síntesis TTS y ensamblado MP3 con ffmpeg
├── requirements.txt        # Dependencias del proyecto
├── .env.example            # Plantilla de variables de configuración
├── .gitignore              # Archivos y carpetas excluidas de Git
├── tests/                  # Pruebas automatizadas (unit tests)
│   ├── __init__.py
│   ├── test_article_extractor.py
│   ├── test_text_processor.py
│   └── test_audio_generator.py
└── output/                 # Carpeta donde se guardan los audios MP3
    └── .gitkeep
```

---

## 🚀 Instalación y puesta en marcha

### 1. Requisitos previos
- **Python 3.9 o superior** instalado en tu sistema.
- Conexión a Internet (para descargar dependencias y generar audio con la API de Google).

### 2. Clonar o acceder al directorio del proyecto
```bash
cd "/ruta/a/tu/carpeta/WEB:MP3"
```

### 3. Crear y activar el entorno virtual
```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar el entorno virtual:
# En macOS / Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 5. Descargar los modelos lingüísticos de NLTK
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 6. Configuración opcional (`.env`)
Puedes copiar el archivo `.env.example` para personalizar valores por defecto:
```bash
cp .env.example .env
```
Valores configurables en `.env`:
- `DEFAULT_LANGUAGE`: Idioma por defecto de la voz (`es` para español, `en` para inglés, etc.).
- `OUTPUT_DIR`: Directorio donde se guardarán los MP3 (por defecto `output`).

---

## 💻 Uso del programa

### Modo interactivo (recomendado)
Ejecuta el programa y sigue las instrucciones en pantalla:
```bash
python3 main.py
```
1. Introduce la URL del artículo cuando se te solicite.
2. Selecciona el idioma (pulsa **Enter** directamente para usar español).

### Modo por línea de comandos (directo)
Puedes pasar la URL y opcionalmente el idioma como argumentos:
```bash
# Sintaxis: python3 main.py <URL> [código_idioma]
python3 main.py "https://es.wikipedia.org/wiki/Exploraci%C3%B3n_de_Marte" es
```

---

## 🎧 Cómo escuchar el audio generado

Los archivos generados se almacenan automáticamente en la carpeta `output/`.

- **Desde la terminal en macOS**:
  ```bash
  afplay "output/nombre_del_archivo.mp3"
  ```
  *(Pulsa `Ctrl + C` en cualquier momento para detener la reproducción).*

- **Visualmente**:
  Abre la carpeta `output/` en el Finder o Explorador de Archivos y haz doble clic sobre el archivo `.mp3`.

---

## 🧪 Ejecutar las pruebas automatizadas

El proyecto incluye pruebas unitarias completas que no requieren conexión a Internet:

```bash
python3 -m unittest discover tests -v
```

Todas las pruebas deben mostrar el mensaje de confirmación `OK`.

---

## 🛡️ Consideraciones de seguridad y buenas prácticas

- **Validación estricta de esquemas**: Solo se aceptan solicitudes `http://` y `https://`.
- **Prevención de SSRF**: El analizador bloquea accesos a redes locales (`127.0.0.1`, `localhost`, rangos privados `192.168.x.x`, `10.x.x.x`).
- **Nombres de archivo seguros**: Se eliminan caracteres reservados de sistemas operativos (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) y se limitan longitudes máximas.
- **Sin ejecución de código remoto**: El HTML se procesa exclusivamente como texto plano mediante analizadores sintácticos seguros.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT. Eres libre de usarlo, modificarlo y compartirlo en tus proyectos personales y profesionales.
