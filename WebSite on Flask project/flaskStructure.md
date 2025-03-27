/mi_proyecto/
│── /app/               # Carpeta principal de la aplicación
│   │── /static/        # Archivos estáticos (CSS, JS, imágenes)
│   │── /templates/     # Plantillas HTML (Jinja2)
│   │── /routes/        # Módulos de rutas (división modular de las rutas)
│   │── /models/        # Definición de modelos (SQLAlchemy u otro ORM)
│   │── /forms/         # Definición de formularios (WTForms, Flask-WTF)
│   │── /services/      # Lógica de negocio y funciones auxiliares
│   │── __init__.py     # Inicialización de la aplicación Flask
│   │── config.py       # Configuración de la app (variables de entorno, BD, etc.)
│   │── extensions.py   # Extensiones (SQLAlchemy, Flask-Login, etc.)
│── /migrations/        # Migraciones de base de datos (Flask-Migrate)
│── /tests/             # Pruebas unitarias y de integración
│── venv/               # Entorno virtual (si usas uno)
│── .env                # Variables de entorno (opcional)
│── .flaskenv           # Configuración de Flask (modo debug, puerto, etc.)
│── requirements.txt    # Dependencias del proyecto
│── run.py              # Script de arranque principal de la aplicación
│── README.md           # Descripción del proyecto
