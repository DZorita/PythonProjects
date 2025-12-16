from flask import Flask
from src.api.routes import init_api_routes
from src.config import db

app = Flask(__name__)

# Esto crea las tablas en la BBDD basadas en los modelos importados [cite: 82]
# Importante: Asegúrate de importar el modelo aquí o en db para que SQLAlchemy lo detecte
from src.models.book import Book
db.Base.metadata.create_all(db.engine)

# Inicializamos las rutas [cite: 83]
init_api_routes(app)

if __name__ == '__main__':
    app.run(debug=True) # [cite: 85]