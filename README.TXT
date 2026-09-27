=============================================================
 LEITOR DE NOTA FISCAL - SISTEMA DE EXTRACAO COM IA
 Atividade Pratica Academica
=============================================================

REPOSITORIO GITHUB
------------------
URL: https://github.com/Jubsvf/Leitor-de-PDF
Codigo de Versionamento (commit atual): 5e08c2fda1e60038dd3a5c3a148ae654f7b0a5fe
Commit curto: 5e08c2f
Link do commit: https://github.com/Jubsvf/Leitor-de-PDF/commit/5e08c2fda1e60038dd3a5c3a148ae654f7b0a5fe

HISTORICO DE VERSOES (commits)
-------------------------------
A aplicacao demonstra o versionamento diretamente na interface,
no rodape da pagina principal (http://127.0.0.1:5000/).
O hash do commit e exibido em tempo real via rota /api/version.

DADOS DE LOGIN / SENHA
-----------------------
URL de Acesso: http://127.0.0.1:5000/login
Usuario: admin
Senha:   fintrack2025

GESTAO DA CHAVE DE API (Gemini)
---------------------------------
A chave pode ser fornecida de duas formas:
  1. Em tempo real: na pagina principal, campo "Chave da API Gemini"
     (enviada apenas na requisicao, nao armazenada em codigo)
  2. Via arquivo .env: definir GEMINI_API_KEY=sua_chave_aqui
     (arquivo excluido do repositorio pelo .gitignore)
Obtencao da chave: https://aistudio.google.com/

COMO EXECUTAR
--------------
1. Clonar o repositorio:
   git clone https://github.com/Jubsvf/Leitor-de-PDF.git

2. Instalar dependencias:
   pip install -r requirements.txt

3. Configurar o .env (copiar de .env.example):
   GEMINI_API_KEY=sua_chave_aqui

4. Iniciar o servidor:
   python server.py

5. Acessar no navegador:
   http://127.0.0.1:5000/login

TECNOLOGIAS UTILIZADAS
-----------------------
- Python 3 / Flask
- SQLAlchemy + SQLite (fallback) / PostgreSQL
- Google Gemini API (google-genai)
- HTML, CSS, JavaScript Vanilla
- Flasgger (Swagger UI)

=============================================================
