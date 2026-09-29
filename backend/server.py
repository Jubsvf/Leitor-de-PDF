import os
import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv

# Importa o agente da mesma pasta (backend/)
from agente import Agente

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)
app.secret_key = os.getenv("SECRET_KEY", "fintrack-secret-2025")
CORS(app, supports_credentials=True)

# Credenciais de acesso acadêmico
APP_USERS = {
    "admin": "admin123"
}


def login_required(f):
    """Decorator que exige login ativo para chamadas da API."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"erro": "Acesso não autorizado. Faça login primeiro."}), 401
        return f(*args, **kwargs)
    return decorated


# Configuração do Swagger
app.config["SWAGGER"] = {
    "title": "API de Extração de Dados de Notas Fiscais em PDF",
    "uiversion": 3,
    "description": "API REST para extração inteligente de dados de notas fiscais (PDF) com IA.",
    "version": "1.0.0",
}
swagger = Swagger(app)


# ============================================================================
# PÁGINA PRINCIPAL & ESTÁTICOS
# ============================================================================

@app.route("/")
@app.route("/login")
def index():
    """Entrega a aplicação unificada (index.html com tela de login e dashboard)."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/static/<path:filename>")
def serve_static_compat(filename):
    """Compatibilidade para requisições com prefixo /static."""
    base_name = os.path.basename(filename)
    return send_from_directory(FRONTEND_DIR, base_name)


# ============================================================================
# ROTAS DE AUTENTICAÇÃO E SESSÃO
# ============================================================================

@app.route("/api/session", methods=["GET"])
def api_session():
    """Retorna o status atual da sessão do usuário."""
    return jsonify({
        "logged_in": bool(session.get("logged_in")),
        "username": session.get("username", "")
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    """Realiza o login do usuário."""
    dados = request.get_json() or {}
    username = (dados.get("username") or "").strip()
    password = dados.get("password") or ""
    if APP_USERS.get(username) == password:
        session["logged_in"] = True
        session["username"] = username
        return jsonify({"ok": True, "mensagem": "Login realizado com sucesso."})
    return jsonify({"ok": False, "erro": "Usuário ou senha inválidos."}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Encerra a sessão do usuário."""
    session.clear()
    return jsonify({"ok": True, "mensagem": "Logout realizado com sucesso."})


# ============================================================================
# INFORMAÇÕES DE VERSÃO E CHAVE DE API EM RUNTIME
# ============================================================================

def _get_git_hash():
    # 1. Tenta extrair do README.TXT para manter paridade exata entre documentação e interface
    try:
        for p in [os.path.join(PROJECT_ROOT, "README.TXT"), os.path.join(PROJECT_ROOT, "docs", "README.TXT")]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if "Codigo de Versionamento" in line and ":" in line:
                            val = line.split(":", 1)[1].strip()
                            if val:
                                return val
    except Exception:
        pass

    # 2. Variável de ambiente do Render
    commit_env = os.getenv("RENDER_GIT_COMMIT")
    if commit_env:
        return commit_env.strip()

    # 3. Consulta direta ao Git local
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    return "5c08b731332e5dce590caa979ed98966b12c2bdd"

GIT_COMMIT_HASH = _get_git_hash()
GIT_REPO_URL = "https://github.com/Jubsvf/Leitor-de-PDF"

_runtime_api_key = None


@app.route("/api/version", methods=["GET"])
def api_version():
    """Retorna informações de versão do sistema."""
    return jsonify({
        "commit": GIT_COMMIT_HASH,
        "commit_short": GIT_COMMIT_HASH[:7] if GIT_COMMIT_HASH != "N/A" else "N/A",
        "repositorio": GIT_REPO_URL,
        "link_commit": f"{GIT_REPO_URL}/commit/{GIT_COMMIT_HASH}" if GIT_COMMIT_HASH != "N/A" else GIT_REPO_URL,
    })


@app.route("/api/configurar-chave", methods=["POST"])
@login_required
def configurar_chave():
    """Configura a chave da API Gemini em tempo real."""
    global _runtime_api_key
    dados = request.get_json() or {}
    chave = (dados.get("api_key") or "").strip()
    if not chave:
        return jsonify({"erro": "Campo 'api_key' não informado ou vazio."}), 400
    _runtime_api_key = chave
    os.environ["GEMINI_API_KEY"] = chave
    return jsonify({"mensagem": "Chave da API Gemini configurada com sucesso.", "status": "ok"})


@app.route("/api/status-chave", methods=["GET"])
@login_required
def status_chave():
    """Verifica se a chave da API Gemini está configurada."""
    chave = _runtime_api_key or os.getenv("GEMINI_API_KEY", "")
    configurada = bool(chave and chave.strip())
    return jsonify({
        "configurada": configurada,
        "origem": "runtime" if _runtime_api_key else ("env" if configurada else "nenhuma"),
        "preview": (chave[:8] + "...") if configurada else None,
    })


# ============================================================================
# PROCESSADOR DE PDF COM IA (GEMINI)
# ============================================================================

@app.route("/api/extrair-pdf", methods=["POST"])
@login_required
def extrair_pdf():
    """
    Processa uma nota fiscal em PDF e retorna os dados extraídos em formato JSON.
    ---
    tags:
      - Processador de PDF
    consumes:
      - multipart/form-data
    parameters:
      - name: pdf
        in: formData
        type: file
        required: true
        description: Arquivo PDF da nota fiscal
      - name: api_key
        in: formData
        type: string
        required: false
        description: Chave da API Gemini (opcional)
    responses:
      200:
        description: JSON estruturado com os dados extraídos e a classificação
      400:
        description: Nenhum arquivo enviado ou formato inválido
    """
    if "pdf" not in request.files and "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo PDF foi enviado no campo 'pdf'."}), 400

    pdf_file = request.files.get("pdf") or request.files.get("file")
    if not pdf_file.filename.lower().endswith(".pdf"):
        return jsonify({"erro": "O arquivo deve ser um documento PDF válido."}), 400

    chave_form = (request.form.get("api_key") or "").strip()
    chave_efetiva = chave_form or _runtime_api_key or os.getenv("GEMINI_API_KEY", "")

    if not chave_efetiva:
        return jsonify({
            "erro": "Chave da API Gemini não configurada! Por favor, cole a chave no campo da interface ou defina GEMINI_API_KEY no arquivo .env."
        }), 400

    try:
        agente = Agente(api_key=chave_efetiva)
        resultado = agente.extrair_dados(pdf_file)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": f"Erro na API Gemini: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
