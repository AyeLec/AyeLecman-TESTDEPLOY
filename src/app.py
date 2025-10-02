"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger  # si no lo usás, podés removerlo
from api.utils import APIException, generate_sitemap
from api.models import db
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands

# ------------------------------------------------------------
# Entorno y rutas de estáticos (build de Vite)
# ------------------------------------------------------------
ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
BASE_DIR = os.path.dirname(os.path.realpath(__file__))   # .../src
DIST_DIR = os.path.join(BASE_DIR, "dist")          # .../dist

# Servimos dist/ como carpeta estática en la raíz del sitio
# (esto hace que /assets/* y archivos estáticos salgan con MIME correcto)
app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
app.url_map.strict_slashes = False

# ---- DEBUG PRINTS ----
print("DIST_DIR:", DIST_DIR)
print("INDEX exists?:", os.path.exists(os.path.join(DIST_DIR, "index.html")))
assets_dir = os.path.join(DIST_DIR, "assets")
print("ASSETS DIR exists?:", os.path.isdir(assets_dir))
try:
    print("ASSETS sample:", sorted(os.listdir(assets_dir))[:5])
except Exception as e:
    print("ASSETS list error:", e)
# -----------------------

# ⬇️⬇️ INSERTAR AQUÍ ⬇️⬇️
import mimetypes
mimetypes.add_type("application/javascript", ".js")  # por las dudas del MIME

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(DIST_DIR, "assets"), filename)
# ⬆️⬆️ HASTA AQUÍ ⬆️⬆️

# ------------------------------------------------------------
# Configuración de base de datos
# ------------------------------------------------------------
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Compatibilidad para antiguos URLs de Heroku
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# ------------------------------------------------------------
# Admin y comandos
# ------------------------------------------------------------
setup_admin(app)
setup_commands(app)

# ------------------------------------------------------------
# API
# ------------------------------------------------------------
# Todos tus endpoints quedan bajo /api/*
app.register_blueprint(api, url_prefix="/api")

# ------------------------------------------------------------
# Manejo de errores API como JSON
# ------------------------------------------------------------
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# ------------------------------------------------------------
# Rutas de frontend (SPA) y sitemap en dev
# ------------------------------------------------------------
@app.route("/")
def root():
    # En desarrollo: devolvemos el sitemap de endpoints
    if ENV == "development":
        return generate_sitemap(app)
    # En producción: servimos el index.html compilado por Vite
    return app.send_static_file("index.html")

# Favicon (opcional, evita warnings en consola)
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(DIST_DIR, "favicon.ico")

# Fallback SPA: si no es /api y el recurso no existe, devolvemos index.html
@app.errorhandler(404)
def spa_fallback(_e):
    # No interceptar rutas de API
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    # Cualquier otra ruta (React Router) vuelve al index para que el front resuelva
    return app.send_static_file("index.html")

# ------------------------------------------------------------
# (Opcional) Healthcheck simple para Render
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}, 200

# ------------------------------------------------------------
# App runner local
# ------------------------------------------------------------
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3001))
    app.run(host="0.0.0.0", port=PORT, debug=True)
