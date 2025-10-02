"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import mimetypes
from flask import Flask, request, jsonify, send_from_directory, abort
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
DIST_DIR = os.path.join(BASE_DIR, "..", "dist")          # .../dist en raíz del repo

# Servimos dist/ como carpeta estática en la raíz del sitio
app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
app.url_map.strict_slashes = False

# Aseguramos MIME correcto para JS
mimetypes.add_type("application/javascript", ".js")

# ---- DEBUG PRINTS ----
print("=== STATIC CONFIG ===")
print("DIST_DIR:", DIST_DIR)
print("INDEX exists?:", os.path.exists(os.path.join(DIST_DIR, "index.html")))
assets_dir = os.path.join(DIST_DIR, "assets")
print("ASSETS DIR exists?:", os.path.isdir(assets_dir))
try:
    print("ASSETS sample:", sorted(os.listdir(assets_dir))[:5])
except Exception as e:
    print("ASSETS list error:", e)
print("=====================")
# -----------------------

# Ruta explícita para assets (evita que el fallback devuelva index.html)
@app.route("/assets/<path:filename>")
def assets(filename):
    assets_dir = os.path.join(DIST_DIR, "assets")
    file_path = os.path.join(assets_dir, filename)
    if not os.path.isfile(file_path):
        print(f"[ERROR] Asset no encontrado: {file_path}")
        abort(404)
    print(f"[OK] Sirviendo asset: {file_path}")
    return send_from_directory(assets_dir, filename)

# ------------------------------------------------------------
# Configuración de base de datos
# ------------------------------------------------------------
db_url = os.getenv("DATABASE_URL")
if db_url:
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
    if ENV == "development":
        return generate_sitemap(app)
    index_path = os.path.join(DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        print(f"[ERROR] No se encontró index.html en {index_path}")
        abort(404)
    print(f"[OK] Sirviendo index.html desde {index_path}")
    return app.send_static_file("index.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(DIST_DIR, "favicon.ico")

# Fallback SPA: si no es /api ni /assets, devolvemos index.html
@app.errorhandler(404)
def spa_fallback(_e):
    if request.path.startswith("/api/") or request.path.startswith("/assets/"):
        print(f"[404] Ruta API/Assets no encontrada: {request.path}")
        return jsonify({"error": "Not found"}), 404
    print(f"[SPA] Ruta {request.path} redirigida a index.html")
    return app.send_static_file("index.html")

# ------------------------------------------------------------
# Healthcheck simple para Render
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
