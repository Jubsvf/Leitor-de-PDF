import os
import datetime
from decimal import Decimal
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import (
    Fornecedor,
    Cliente,
    Faturado,
    TipoReceita,
    TipoDespesa,
    ContaPagar,
    ParcelaPagar,
    ClassificacaoContaPagar,
    ContaReceber,
    ParcelaReceber,
    ClassificacaoContaReceber,
)
from agente import Agente
from seed import init_database

load_dotenv()

# Inicializar tabelas e seeds no PostgreSQL
init_database()

app = Flask(__name__, static_folder=".", template_folder="templates")
CORS(app)

# Configuração do Swagger
app.config["SWAGGER"] = {
    "title": "API de Gestão Financeira e Extração de PDF",
    "uiversion": 3,
    "description": "Documentação OpenAPI/Swagger para o sistema de gestão financeira e extração de notas fiscais com IA (Gemini).",
    "version": "1.0.0",
}
swagger = Swagger(app)


# Utilitário para parse de datas e decimais
def parse_date(date_str):
    if not date_str:
        return datetime.date.today()
    if isinstance(date_str, datetime.date):
        return date_str
    # Tenta DD/MM/AAAA ou AAAA-MM-DD
    if "/" in date_str:
        d, m, y = date_str.split("/")
        return datetime.date(int(y), int(m), int(d))
    return datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()


def parse_decimal(val):
    if val is None or val == "":
        return Decimal("0.00")
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    # Tratar formato brasileiro 1.234,56
    clean_val = str(val).replace("R$", "").strip()
    if "," in clean_val and "." in clean_val:
        clean_val = clean_val.replace(".", "").replace(",", ".")
    elif "," in clean_val:
        clean_val = clean_val.replace(",", ".")
    return Decimal(clean_val)


# ============================================================================
# ROTAS DE PÁGINAS WEB (VIEWS)
# ============================================================================

@app.route("/")
def index():
    """Página principal de Upload e Extração de PDF (frontend original mantido)."""
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve arquivos estáticos da pasta raiz (style.css, app.js, etc)."""
    return send_from_directory(".", filename)


@app.route("/fornecedores")
@app.route("/fornecedores.html")
def view_fornecedores():
    return send_from_directory(".", "fornecedores.html")


@app.route("/clientes")
@app.route("/clientes.html")
def view_clientes():
    return send_from_directory(".", "clientes.html")


@app.route("/faturados")
@app.route("/faturados.html")
def view_faturados():
    return send_from_directory(".", "faturados.html")


@app.route("/tipos-receita")
@app.route("/tipos-receita.html")
def view_tipos_receita():
    return send_from_directory(".", "tipos-receita.html")


@app.route("/tipos-despesa")
@app.route("/tipos-despesa.html")
def view_tipos_despesa():
    return send_from_directory(".", "tipos-despesa.html")


@app.route("/contas-pagar")
@app.route("/contas-pagar.html")
def view_contas_pagar():
    return send_from_directory(".", "contas-pagar.html")


@app.route("/contas-receber")
@app.route("/contas-receber.html")
def view_contas_receber():
    return send_from_directory(".", "contas-receber.html")


# ============================================================================
# PROCESSADOR DE PDF COM IA (GEMINI)
# ============================================================================

@app.route("/api/extrair-pdf", methods=["POST"])
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

    agente = Agente()
    resultado = agente.extrair_dados(pdf_file)
    return jsonify(resultado)


@app.route("/api/salvar-conta-pagar-pdf", methods=["POST"])
def salvar_conta_pagar_pdf():
    """
    Salva uma Conta a Pagar diretamente a partir do JSON extraído da nota fiscal.
    ---
    tags:
      - Processador de PDF
    consumes:
      - application/json
    responses:
      201:
        description: Conta a pagar registrada com sucesso
    """
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        # Extrair campos
        nome_emitente = dados.get("Nome do Emitente") or dados.get("razao_social") or "Fornecedor da NF"
        cnpj_emitente = dados.get("CNPJ do Emitente") or dados.get("cnpj") or "00.000.000/0000-00"
        nome_destinatario = dados.get("Nome do Destinatário") or dados.get("nome_destinatario") or "Destinatário NF"
        cnpj_destinatario = dados.get("CNPJ do Destinatário") or dados.get("cpf") or "000.000.000-00"
        numero_nf = dados.get("Número da Nota Fiscal") or dados.get("numero_nf") or "S/N"
        data_emissao = parse_date(dados.get("Data de Emissão"))
        data_vencimento = parse_date(dados.get("Data de Vencimento") or dados.get("Data de Emissão"))
        descricao_produtos = dados.get("Descrição dos Produtos") or ""
        valor_total = parse_decimal(dados.get("Valor Total") or 0)

        # 1. Encontrar ou criar Fornecedor
        fornecedor = db.query(Fornecedor).filter(Fornecedor.cnpj == cnpj_emitente).first()
        if not fornecedor:
            fornecedor = Fornecedor(
                razao_social=nome_emitente,
                nome_fantasia=nome_emitente,
                cnpj=cnpj_emitente,
                ativo=True
            )
            db.add(fornecedor)
            db.flush()

        # 2. Encontrar ou criar Faturado
        faturado = db.query(Faturado).filter(Faturado.cpf == cnpj_destinatario).first()
        if not faturado:
            faturado = Faturado(
                nome_completo=nome_destinatario,
                cpf=cnpj_destinatario,
                ativo=True
            )
            db.add(faturado)
            db.flush()

        # 3. Classificação de Despesa
        classif = dados.get("CLASSIFICAÇÃO") or {}
        categoria_nome = classif.get("categoria") or "MANUTENÇÃO E OPERAÇÃO"
        tipo_despesa = db.query(TipoDespesa).filter(TipoDespesa.categoria == categoria_nome).first()
        if not tipo_despesa:
            tipo_despesa = db.query(TipoDespesa).first()

        # 4. Criar Conta a Pagar
        conta = ContaPagar(
            fornecedor_id=fornecedor.id,
            faturado_id=faturado.id,
            numero_nf=numero_nf,
            data_emissao=data_emissao,
            descricao_produtos=descricao_produtos,
            valor_total=valor_total,
            quantidade_parcelas=1,
            ativo=True
        )
        db.add(conta)
        db.flush()

        # 5. Criar Parcela
        parcela = ParcelaPagar(
            conta_pagar_id=conta.id,
            numero_parcela=1,
            data_vencimento=data_vencimento,
            valor=valor_total,
            status="PENDENTE",
            ativo=True
        )
        db.add(parcela)

        # 6. Criar Classificação
        if tipo_despesa:
            item_classif = ClassificacaoContaPagar(
                conta_pagar_id=conta.id,
                tipo_despesa_id=tipo_despesa.id,
                percentual=100.0,
                valor=valor_total
            )
            db.add(item_classif)

        db.commit()
        db.refresh(conta)
        return jsonify({"mensagem": "Conta a pagar registrada com sucesso!", "conta": conta.to_dict()}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


# ============================================================================
# CRUD: MANTER FORNECEDOR
# ============================================================================

@app.route("/api/fornecedores", methods=["GET"])
def listar_fornecedores():
    """
    Lista todos os fornecedores cadastrados.
    ---
    tags:
      - Fornecedores
    parameters:
      - name: ativo
        in: query
        type: string
        description: Filtrar por ativo (true, false ou all)
    responses:
      200:
        description: Lista de fornecedores
    """
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(Fornecedor)
        if ativo_param == "true":
            query = query.filter(Fornecedor.ativo == True)
        elif ativo_param == "false":
            query = query.filter(Fornecedor.ativo == False)
        fornecedores = query.order_by(Fornecedor.razao_social).all()
        return jsonify([f.to_dict() for f in fornecedores])
    finally:
        db.close()


@app.route("/api/fornecedores", methods=["POST"])
def criar_fornecedor():
    """
    Cadastra um novo fornecedor.
    ---
    tags:
      - Fornecedores
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - razao_social
            - cnpj
          properties:
            razao_social:
              type: string
            nome_fantasia:
              type: string
            cnpj:
              type: string
    responses:
      201:
        description: Fornecedor criado
    """
    dados = request.get_json() or {}
    razao = dados.get("razao_social", "").strip()
    cnpj = dados.get("cnpj", "").strip()
    fantasia = dados.get("nome_fantasia", "").strip()

    if not razao or not cnpj:
        return jsonify({"erro": "Razão Social e CNPJ são obrigatórios."}), 400

    db = SessionLocal()
    try:
        existente = db.query(Fornecedor).filter(Fornecedor.cnpj == cnpj).first()
        if existente:
            return jsonify({"erro": f"Já existe um fornecedor cadastrado com o CNPJ {cnpj}."}), 409

        forn = Fornecedor(razao_social=razao, nome_fantasia=fantasia, cnpj=cnpj, ativo=True)
        db.add(forn)
        db.commit()
        db.refresh(forn)
        return jsonify(forn.to_dict()), 201
    finally:
        db.close()


@app.route("/api/fornecedores/<int:id>", methods=["GET"])
def obter_fornecedor(id):
    """Obtém detalhes de um fornecedor pelo ID."""
    db = SessionLocal()
    try:
        forn = db.query(Fornecedor).filter(Fornecedor.id == id).first()
        if not forn:
            return jsonify({"erro": "Fornecedor não encontrado."}), 404
        return jsonify(forn.to_dict())
    finally:
        db.close()


@app.route("/api/fornecedores/<int:id>", methods=["PUT"])
def atualizar_fornecedor(id):
    """Atualiza dados de um fornecedor."""
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        forn = db.query(Fornecedor).filter(Fornecedor.id == id).first()
        if not forn:
            return jsonify({"erro": "Fornecedor não encontrado."}), 404

        if "razao_social" in dados and dados["razao_social"].strip():
            forn.razao_social = dados["razao_social"].strip()
        if "nome_fantasia" in dados:
            forn.nome_fantasia = dados["nome_fantasia"].strip()
        if "cnpj" in dados and dados["cnpj"].strip():
            # Verificar duplicidade
            outro = db.query(Fornecedor).filter(Fornecedor.cnpj == dados["cnpj"].strip(), Fornecedor.id != id).first()
            if outro:
                return jsonify({"erro": "CNPJ já utilizado por outro fornecedor."}), 409
            forn.cnpj = dados["cnpj"].strip()

        db.commit()
        db.refresh(forn)
        return jsonify(forn.to_dict())
    finally:
        db.close()


@app.route("/api/fornecedores/<int:id>/inativar", methods=["POST"])
@app.route("/api/fornecedores/<int:id>", methods=["DELETE"])
def inativar_fornecedor(id):
    """
    Regra de negócio: Cadastros NÃO podem ser excluídos, apenas INATIVADOS.
    """
    db = SessionLocal()
    try:
        forn = db.query(Fornecedor).filter(Fornecedor.id == id).first()
        if not forn:
            return jsonify({"erro": "Fornecedor não encontrado."}), 404

        forn.ativo = False
        db.commit()
        return jsonify({"mensagem": "Fornecedor inativado com sucesso (exclusão física não permitida por regra de negócio).", "fornecedor": forn.to_dict()})
    finally:
        db.close()


@app.route("/api/fornecedores/<int:id>/reativar", methods=["POST"])
def reativar_fornecedor(id):
    """Regra de negócio: Registros inativos devem poder ser REATIVADOS."""
    db = SessionLocal()
    try:
        forn = db.query(Fornecedor).filter(Fornecedor.id == id).first()
        if not forn:
            return jsonify({"erro": "Fornecedor não encontrado."}), 404

        forn.ativo = True
        db.commit()
        return jsonify({"mensagem": "Fornecedor reativado com sucesso!", "fornecedor": forn.to_dict()})
    finally:
        db.close()


# ============================================================================
# CRUD: MANTER CLIENTE
# ============================================================================

@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    """Lista todos os clientes."""
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(Cliente)
        if ativo_param == "true":
            query = query.filter(Cliente.ativo == True)
        elif ativo_param == "false":
            query = query.filter(Cliente.ativo == False)
        clientes = query.order_by(Cliente.razao_social).all()
        return jsonify([c.to_dict() for c in clientes])
    finally:
        db.close()


@app.route("/api/clientes", methods=["POST"])
def criar_cliente():
    """Cadastra um novo cliente."""
    dados = request.get_json() or {}
    razao = dados.get("razao_social", "").strip()
    cpf_cnpj = dados.get("cpf_cnpj", "").strip()
    fantasia = dados.get("nome_fantasia", "").strip()

    if not razao or not cpf_cnpj:
        return jsonify({"erro": "Razão Social / Nome e CPF/CNPJ são obrigatórios."}), 400

    db = SessionLocal()
    try:
        existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cnpj).first()
        if existente:
            return jsonify({"erro": f"Já existe um cliente cadastrado com o CPF/CNPJ {cpf_cnpj}."}), 409

        cli = Cliente(razao_social=razao, nome_fantasia=fantasia, cpf_cnpj=cpf_cnpj, ativo=True)
        db.add(cli)
        db.commit()
        db.refresh(cli)
        return jsonify(cli.to_dict()), 201
    finally:
        db.close()


@app.route("/api/clientes/<int:id>", methods=["GET"])
def obter_cliente(id):
    db = SessionLocal()
    try:
        cli = db.query(Cliente).filter(Cliente.id == id).first()
        if not cli:
            return jsonify({"erro": "Cliente não encontrado."}), 404
        return jsonify(cli.to_dict())
    finally:
        db.close()


@app.route("/api/clientes/<int:id>", methods=["PUT"])
def atualizar_cliente(id):
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        cli = db.query(Cliente).filter(Cliente.id == id).first()
        if not cli:
            return jsonify({"erro": "Cliente não encontrado."}), 404

        if "razao_social" in dados and dados["razao_social"].strip():
            cli.razao_social = dados["razao_social"].strip()
        if "nome_fantasia" in dados:
            cli.nome_fantasia = dados["nome_fantasia"].strip()
        if "cpf_cnpj" in dados and dados["cpf_cnpj"].strip():
            outro = db.query(Cliente).filter(Cliente.cpf_cnpj == dados["cpf_cnpj"].strip(), Cliente.id != id).first()
            if outro:
                return jsonify({"erro": "CPF/CNPJ já utilizado por outro cliente."}), 409
            cli.cpf_cnpj = dados["cpf_cnpj"].strip()

        db.commit()
        db.refresh(cli)
        return jsonify(cli.to_dict())
    finally:
        db.close()


@app.route("/api/clientes/<int:id>/inativar", methods=["POST"])
@app.route("/api/clientes/<int:id>", methods=["DELETE"])
def inativar_cliente(id):
    db = SessionLocal()
    try:
        cli = db.query(Cliente).filter(Cliente.id == id).first()
        if not cli:
            return jsonify({"erro": "Cliente não encontrado."}), 404

        cli.ativo = False
        db.commit()
        return jsonify({"mensagem": "Cliente inativado com sucesso.", "cliente": cli.to_dict()})
    finally:
        db.close()


@app.route("/api/clientes/<int:id>/reativar", methods=["POST"])
def reativar_cliente(id):
    db = SessionLocal()
    try:
        cli = db.query(Cliente).filter(Cliente.id == id).first()
        if not cli:
            return jsonify({"erro": "Cliente não encontrado."}), 404

        cli.ativo = True
        db.commit()
        return jsonify({"mensagem": "Cliente reativado com sucesso.", "cliente": cli.to_dict()})
    finally:
        db.close()


# ============================================================================
# CRUD: MANTER FATURADO
# ============================================================================

@app.route("/api/faturados", methods=["GET"])
def listar_faturados():
    """Lista todos os faturados."""
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(Faturado)
        if ativo_param == "true":
            query = query.filter(Faturado.ativo == True)
        elif ativo_param == "false":
            query = query.filter(Faturado.ativo == False)
        faturados = query.order_by(Faturado.nome_completo).all()
        return jsonify([f.to_dict() for f in faturados])
    finally:
        db.close()


@app.route("/api/faturados", methods=["POST"])
def criar_faturado():
    """Cadastra um novo faturado."""
    dados = request.get_json() or {}
    nome = dados.get("nome_completo", "").strip()
    cpf = dados.get("cpf", "").strip()

    if not nome or not cpf:
        return jsonify({"erro": "Nome Completo e CPF são obrigatórios."}), 400

    db = SessionLocal()
    try:
        existente = db.query(Faturado).filter(Faturado.cpf == cpf).first()
        if existente:
            return jsonify({"erro": f"Já existe um faturado cadastrado com o CPF {cpf}."}), 409

        fat = Faturado(nome_completo=nome, cpf=cpf, ativo=True)
        db.add(fat)
        db.commit()
        db.refresh(fat)
        return jsonify(fat.to_dict()), 201
    finally:
        db.close()


@app.route("/api/faturados/<int:id>", methods=["GET"])
def obter_faturado(id):
    db = SessionLocal()
    try:
        fat = db.query(Faturado).filter(Faturado.id == id).first()
        if not fat:
            return jsonify({"erro": "Faturado não encontrado."}), 404
        return jsonify(fat.to_dict())
    finally:
        db.close()


@app.route("/api/faturados/<int:id>", methods=["PUT"])
def atualizar_faturado(id):
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        fat = db.query(Faturado).filter(Faturado.id == id).first()
        if not fat:
            return jsonify({"erro": "Faturado não encontrado."}), 404

        if "nome_completo" in dados and dados["nome_completo"].strip():
            fat.nome_completo = dados["nome_completo"].strip()
        if "cpf" in dados and dados["cpf"].strip():
            outro = db.query(Faturado).filter(Faturado.cpf == dados["cpf"].strip(), Faturado.id != id).first()
            if outro:
                return jsonify({"erro": "CPF já utilizado por outro faturado."}), 409
            fat.cpf = dados["cpf"].strip()

        db.commit()
        db.refresh(fat)
        return jsonify(fat.to_dict())
    finally:
        db.close()


@app.route("/api/faturados/<int:id>/inativar", methods=["POST"])
@app.route("/api/faturados/<int:id>", methods=["DELETE"])
def inativar_faturado(id):
    db = SessionLocal()
    try:
        fat = db.query(Faturado).filter(Faturado.id == id).first()
        if not fat:
            return jsonify({"erro": "Faturado não encontrado."}), 404

        fat.ativo = False
        db.commit()
        return jsonify({"mensagem": "Faturado inativado com sucesso.", "faturado": fat.to_dict()})
    finally:
        db.close()


@app.route("/api/faturados/<int:id>/reativar", methods=["POST"])
def reativar_faturado(id):
    db = SessionLocal()
    try:
        fat = db.query(Faturado).filter(Faturado.id == id).first()
        if not fat:
            return jsonify({"erro": "Faturado não encontrado."}), 404

        fat.ativo = True
        db.commit()
        return jsonify({"mensagem": "Faturado reativado com sucesso.", "faturado": fat.to_dict()})
    finally:
        db.close()


# ============================================================================
# CRUD: MANTER TIPO DE RECEITA
# ============================================================================

@app.route("/api/tipos-receita", methods=["GET"])
def listar_tipos_receita():
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(TipoReceita)
        if ativo_param == "true":
            query = query.filter(TipoReceita.ativo == True)
        elif ativo_param == "false":
            query = query.filter(TipoReceita.ativo == False)
        tipos = query.order_by(TipoReceita.descricao).all()
        return jsonify([t.to_dict() for t in tipos])
    finally:
        db.close()


@app.route("/api/tipos-receita", methods=["POST"])
def criar_tipo_receita():
    dados = request.get_json() or {}
    desc = dados.get("descricao", "").strip()
    if not desc:
        return jsonify({"erro": "Descrição do tipo de receita é obrigatória."}), 400

    db = SessionLocal()
    try:
        existente = db.query(TipoReceita).filter(TipoReceita.descricao.ilike(desc)).first()
        if existente:
            return jsonify({"erro": "Tipo de receita já cadastrado com esta descrição."}), 409

        tr = TipoReceita(descricao=desc, ativo=True)
        db.add(tr)
        db.commit()
        db.refresh(tr)
        return jsonify(tr.to_dict()), 201
    finally:
        db.close()


@app.route("/api/tipos-receita/<int:id>", methods=["PUT"])
def atualizar_tipo_receita(id):
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        tr = db.query(TipoReceita).filter(TipoReceita.id == id).first()
        if not tr:
            return jsonify({"erro": "Tipo de receita não encontrado."}), 404

        if "descricao" in dados and dados["descricao"].strip():
            tr.descricao = dados["descricao"].strip()

        db.commit()
        db.refresh(tr)
        return jsonify(tr.to_dict())
    finally:
        db.close()


@app.route("/api/tipos-receita/<int:id>/inativar", methods=["POST"])
@app.route("/api/tipos-receita/<int:id>", methods=["DELETE"])
def inativar_tipo_receita(id):
    db = SessionLocal()
    try:
        tr = db.query(TipoReceita).filter(TipoReceita.id == id).first()
        if not tr:
            return jsonify({"erro": "Tipo de receita não encontrado."}), 404

        tr.ativo = False
        db.commit()
        return jsonify({"mensagem": "Tipo de receita inativado com sucesso.", "tipo_receita": tr.to_dict()})
    finally:
        db.close()


@app.route("/api/tipos-receita/<int:id>/reativar", methods=["POST"])
def reativar_tipo_receita(id):
    db = SessionLocal()
    try:
        tr = db.query(TipoReceita).filter(TipoReceita.id == id).first()
        if not tr:
            return jsonify({"erro": "Tipo de receita não encontrado."}), 404

        tr.ativo = True
        db.commit()
        return jsonify({"mensagem": "Tipo de receita reativado com sucesso.", "tipo_receita": tr.to_dict()})
    finally:
        db.close()


# ============================================================================
# CRUD: MANTER TIPO DE DESPESA
# ============================================================================

@app.route("/api/tipos-despesa", methods=["GET"])
def listar_tipos_despesa():
    ativo_param = request.args.get("ativo", "all").lower()
    categoria_param = request.args.get("categoria", "").strip()
    db = SessionLocal()
    try:
        query = db.query(TipoDespesa)
        if ativo_param == "true":
            query = query.filter(TipoDespesa.ativo == True)
        elif ativo_param == "false":
            query = query.filter(TipoDespesa.ativo == False)
        if categoria_param:
            query = query.filter(TipoDespesa.categoria == categoria_param)
        tipos = query.order_by(TipoDespesa.categoria, TipoDespesa.descricao).all()
        return jsonify([t.to_dict() for t in tipos])
    finally:
        db.close()


@app.route("/api/tipos-despesa", methods=["POST"])
def criar_tipo_despesa():
    dados = request.get_json() or {}
    categoria = dados.get("categoria", "").strip()
    descricao = dados.get("descricao", "").strip()

    if not categoria or not descricao:
        return jsonify({"erro": "Categoria e Descrição são obrigatórias."}), 400

    db = SessionLocal()
    try:
        td = TipoDespesa(categoria=categoria, descricao=descricao, ativo=True)
        db.add(td)
        db.commit()
        db.refresh(td)
        return jsonify(td.to_dict()), 201
    finally:
        db.close()


@app.route("/api/tipos-despesa/<int:id>", methods=["PUT"])
def atualizar_tipo_despesa(id):
    dados = request.get_json() or {}
    db = SessionLocal()
    try:
        td = db.query(TipoDespesa).filter(TipoDespesa.id == id).first()
        if not td:
            return jsonify({"erro": "Tipo de despesa não encontrado."}), 404

        if "categoria" in dados and dados["categoria"].strip():
            td.categoria = dados["categoria"].strip()
        if "descricao" in dados and dados["descricao"].strip():
            td.descricao = dados["descricao"].strip()

        db.commit()
        db.refresh(td)
        return jsonify(td.to_dict())
    finally:
        db.close()


@app.route("/api/tipos-despesa/<int:id>/inativar", methods=["POST"])
@app.route("/api/tipos-despesa/<int:id>", methods=["DELETE"])
def inativar_tipo_despesa(id):
    db = SessionLocal()
    try:
        td = db.query(TipoDespesa).filter(TipoDespesa.id == id).first()
        if not td:
            return jsonify({"erro": "Tipo de despesa não encontrado."}), 404

        td.ativo = False
        db.commit()
        return jsonify({"mensagem": "Tipo de despesa inativado com sucesso.", "tipo_despesa": td.to_dict()})
    finally:
        db.close()


@app.route("/api/tipos-despesa/<int:id>/reativar", methods=["POST"])
def reativar_tipo_despesa(id):
    db = SessionLocal()
    try:
        td = db.query(TipoDespesa).filter(TipoDespesa.id == id).first()
        if not td:
            return jsonify({"erro": "Tipo de despesa não encontrado."}), 404

        td.ativo = True
        db.commit()
        return jsonify({"mensagem": "Tipo de despesa reativado com sucesso.", "tipo_despesa": td.to_dict()})
    finally:
        db.close()


# ============================================================================
# REGISTRAR CONTAS A PAGAR
# ============================================================================

@app.route("/api/contas-pagar", methods=["GET"])
def listar_contas_pagar():
    """Lista todas as contas a pagar."""
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(ContaPagar)
        if ativo_param == "true":
            query = query.filter(ContaPagar.ativo == True)
        elif ativo_param == "false":
            query = query.filter(ContaPagar.ativo == False)
        contas = query.order_by(ContaPagar.data_emissao.desc()).all()
        return jsonify([c.to_dict() for c in contas])
    finally:
        db.close()


@app.route("/api/contas-pagar", methods=["POST"])
def criar_conta_pagar():
    """
    Registra uma nova Conta a Pagar com parcelas e classificações de despesa.
    Suporta 1 ou múltiplas parcelas e 1 ou múltiplas classificações.
    """
    dados = request.get_json() or {}
    fornecedor_id = dados.get("fornecedor_id")
    faturado_id = dados.get("faturado_id")
    numero_nf = dados.get("numero_nf", "").strip()
    data_emissao = parse_date(dados.get("data_emissao"))
    descricao = dados.get("descricao_produtos", "").strip()
    valor_total = parse_decimal(dados.get("valor_total", 0))

    if not fornecedor_id or not faturado_id or not numero_nf:
        return jsonify({"erro": "Fornecedor, Faturado e Número da NF são obrigatórios."}), 400

    db = SessionLocal()
    try:
        forn = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
        fat = db.query(Faturado).filter(Faturado.id == faturado_id).first()
        if not forn or not fat:
            return jsonify({"erro": "Fornecedor ou Faturado inválido."}), 400

        parcelas_input = dados.get("parcelas") or []
        if not parcelas_input:
            venc = parse_date(dados.get("data_vencimento") or data_emissao)
            parcelas_input = [{"numero_parcela": 1, "data_vencimento": venc, "valor": valor_total}]

        classificacoes_input = dados.get("classificacoes") or []
        if not classificacoes_input:
            td_id = dados.get("tipo_despesa_id")
            if td_id:
                classificacoes_input = [{"tipo_despesa_id": td_id, "percentual": 100.0, "valor": valor_total}]
            else:
                primeiro_td = db.query(TipoDespesa).filter(TipoDespesa.ativo == True).first()
                if primeiro_td:
                    classificacoes_input = [{"tipo_despesa_id": primeiro_td.id, "percentual": 100.0, "valor": valor_total}]

        conta = ContaPagar(
            fornecedor_id=fornecedor_id,
            faturado_id=faturado_id,
            numero_nf=numero_nf,
            data_emissao=data_emissao,
            descricao_produtos=descricao,
            valor_total=valor_total,
            quantidade_parcelas=len(parcelas_input),
            ativo=True
        )
        db.add(conta)
        db.flush()

        for idx, p_item in enumerate(parcelas_input, 1):
            p_venc = parse_date(p_item.get("data_vencimento"))
            p_val = parse_decimal(p_item.get("valor", valor_total / len(parcelas_input)))
            parcela = ParcelaPagar(
                conta_pagar_id=conta.id,
                numero_parcela=p_item.get("numero_parcela", idx),
                data_vencimento=p_venc,
                valor=p_val,
                status=p_item.get("status", "PENDENTE"),
                ativo=True
            )
            db.add(parcela)

        for c_item in classificacoes_input:
            c_td_id = c_item.get("tipo_despesa_id")
            c_perc = parse_decimal(c_item.get("percentual", 100.0))
            c_val = parse_decimal(c_item.get("valor", valor_total))
            classif = ClassificacaoContaPagar(
                conta_pagar_id=conta.id,
                tipo_despesa_id=c_td_id,
                percentual=c_perc,
                valor=c_val
            )
            db.add(classif)

        db.commit()
        db.refresh(conta)
        return jsonify(conta.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@app.route("/api/contas-pagar/<int:id>", methods=["GET"])
def obter_conta_pagar(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaPagar).filter(ContaPagar.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a pagar não encontrada."}), 404
        return jsonify(conta.to_dict())
    finally:
        db.close()


@app.route("/api/contas-pagar/<int:id>/inativar", methods=["POST"])
@app.route("/api/contas-pagar/<int:id>", methods=["DELETE"])
def inativar_conta_pagar(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaPagar).filter(ContaPagar.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a pagar não encontrada."}), 404

        conta.ativo = False
        for p in conta.parcelas:
            p.ativo = False
        db.commit()
        return jsonify({"mensagem": "Conta a pagar inativada com sucesso.", "conta": conta.to_dict()})
    finally:
        db.close()


@app.route("/api/contas-pagar/<int:id>/reativar", methods=["POST"])
def reativar_conta_pagar(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaPagar).filter(ContaPagar.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a pagar não encontrada."}), 404

        conta.ativo = True
        for p in conta.parcelas:
            p.ativo = True
        db.commit()
        return jsonify({"mensagem": "Conta a pagar reativada com sucesso.", "conta": conta.to_dict()})
    finally:
        db.close()


# ============================================================================
# REGISTRAR CONTAS A RECEBER
# ============================================================================

@app.route("/api/contas-receber", methods=["GET"])
def listar_contas_receber():
    ativo_param = request.args.get("ativo", "all").lower()
    db = SessionLocal()
    try:
        query = db.query(ContaReceber)
        if ativo_param == "true":
            query = query.filter(ContaReceber.ativo == True)
        elif ativo_param == "false":
            query = query.filter(ContaReceber.ativo == False)
        contas = query.order_by(ContaReceber.data_emissao.desc()).all()
        return jsonify([c.to_dict() for c in contas])
    finally:
        db.close()


@app.route("/api/contas-receber", methods=["POST"])
def criar_conta_receber():
    dados = request.get_json() or {}
    cliente_id = dados.get("cliente_id")
    faturado_id = dados.get("faturado_id")
    numero_doc = dados.get("numero_documento", "").strip()
    data_emissao = parse_date(dados.get("data_emissao"))
    descricao = dados.get("descricao", "").strip()
    valor_total = parse_decimal(dados.get("valor_total", 0))

    if not cliente_id or not faturado_id or not numero_doc:
        return jsonify({"erro": "Cliente, Faturado e Número do Documento são obrigatórios."}), 400

    db = SessionLocal()
    try:
        cli = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        fat = db.query(Faturado).filter(Faturado.id == faturado_id).first()
        if not cli or not fat:
            return jsonify({"erro": "Cliente ou Faturado inválido."}), 400

        parcelas_input = dados.get("parcelas") or []
        if not parcelas_input:
            venc = parse_date(dados.get("data_vencimento") or data_emissao)
            parcelas_input = [{"numero_parcela": 1, "data_vencimento": venc, "valor": valor_total}]

        classificacoes_input = dados.get("classificacoes") or []
        if not classificacoes_input:
            tr_id = dados.get("tipo_receita_id")
            if tr_id:
                classificacoes_input = [{"tipo_receita_id": tr_id, "percentual": 100.0, "valor": valor_total}]
            else:
                primeiro_tr = db.query(TipoReceita).filter(TipoReceita.ativo == True).first()
                if primeiro_tr:
                    classificacoes_input = [{"tipo_receita_id": primeiro_tr.id, "percentual": 100.0, "valor": valor_total}]

        conta = ContaReceber(
            cliente_id=cliente_id,
            faturado_id=faturado_id,
            numero_documento=numero_doc,
            data_emissao=data_emissao,
            descricao=descricao,
            valor_total=valor_total,
            quantidade_parcelas=len(parcelas_input),
            ativo=True
        )
        db.add(conta)
        db.flush()

        for idx, p_item in enumerate(parcelas_input, 1):
            p_venc = parse_date(p_item.get("data_vencimento"))
            p_val = parse_decimal(p_item.get("valor", valor_total / len(parcelas_input)))
            parcela = ParcelaReceber(
                conta_receber_id=conta.id,
                numero_parcela=p_item.get("numero_parcela", idx),
                data_vencimento=p_venc,
                valor=p_val,
                status=p_item.get("status", "PENDENTE"),
                ativo=True
            )
            db.add(parcela)

        for c_item in classificacoes_input:
            c_tr_id = c_item.get("tipo_receita_id")
            c_perc = parse_decimal(c_item.get("percentual", 100.0))
            c_val = parse_decimal(c_item.get("valor", valor_total))
            classif = ClassificacaoContaReceber(
                conta_receber_id=conta.id,
                tipo_receita_id=c_tr_id,
                percentual=c_perc,
                valor=c_val
            )
            db.add(classif)

        db.commit()
        db.refresh(conta)
        return jsonify(conta.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 400
    finally:
        db.close()


@app.route("/api/contas-receber/<int:id>", methods=["GET"])
def obter_conta_receber(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaReceber).filter(ContaReceber.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a receber não encontrada."}), 404
        return jsonify(conta.to_dict())
    finally:
        db.close()


@app.route("/api/contas-receber/<int:id>/inativar", methods=["POST"])
@app.route("/api/contas-receber/<int:id>", methods=["DELETE"])
def inativar_conta_receber(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaReceber).filter(ContaReceber.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a receber não encontrada."}), 404

        conta.ativo = False
        for p in conta.parcelas:
            p.ativo = False
        db.commit()
        return jsonify({"mensagem": "Conta a receber inativada com sucesso.", "conta": conta.to_dict()})
    finally:
        db.close()


@app.route("/api/contas-receber/<int:id>/reativar", methods=["POST"])
def reativar_conta_receber(id):
    db = SessionLocal()
    try:
        conta = db.query(ContaReceber).filter(ContaReceber.id == id).first()
        if not conta:
            return jsonify({"erro": "Conta a receber não encontrada."}), 404

        conta.ativo = True
        for p in conta.parcelas:
            p.ativo = True
        db.commit()
        return jsonify({"mensagem": "Conta a receber reativada com sucesso.", "conta": conta.to_dict()})
    finally:
        db.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Iniciando servidor Flask na porta {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
