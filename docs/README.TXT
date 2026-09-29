=============================================================
 LEITOR DE NOTA FISCAL - SISTEMA DE EXTRACAO COM IA
 Atividade Pratica Academica
=============================================================

REPOSITORIO GITHUB
------------------
URL: https://github.com/Jubsvf/Leitor-de-PDF
Codigo de Versionamento (commit atual): 588c0a4372e10666c693a53a19f24c84cb2607c0
Commit curto: 588c0a4
Link do commit: https://github.com/Jubsvf/Leitor-de-PDF/commit/588c0a4372e10666c693a53a19f24c84cb2607c0

ESTRUTURA DE PASTAS E ARQUIVOS
------------------------------
Leitor-de-PDF/
├── frontend/                  # Interface do usuario (SPA)
│   ├── index.html             # Pagina unificada (Login integrado + Dashboard)
│   ├── style.css              # Estilos e responsividade
│   └── app.js                 # Logica de frontend, sessao e chamadas de API
├── backend/                   # Servidor, regras de negocio e extracao
│   ├── server.py              # API Flask, rotas REST, sessao e Swagger
│   ├── agente.py              # Agente de extracao com IA Gemini e pypdf
│   └── database/              # Camada de persistencia de dados
│       ├── connection.py      # Conexao com banco de dados
│       ├── models.py          # Modelos de dados
│       ├── seed.py            # Carga inicial de dados
│       └── fintrack.db        # Banco de dados local SQLite
├── deploy/                    # Arquivos de configuracao para nuvem
│   ├── Procfile               # Execucao via Gunicorn para Render / Heroku
│   └── render.yaml            # Infraestrutura como codigo para o Render
├── docs/                      # Documentacao tecnica e relatorios
│   └── README.TXT             # Este relatorio tecnico
├── requirements.txt           # Dependencias Python
├── .env.example               # Exemplo de variaveis de ambiente
└── README.md                  # Documentacao principal do repositorio

HISTORICO DE VERSOES E ATUALIZACOES RECENTES
---------------------------------------------
1. Foco e Simplificacao da Aplicacao:
   - Remocao de modulos excedentes de CRUD para concentrar a aplicacao
     estritamente no proposito principal: extracao automatizada e
     inteligente de dados de notas fiscais em PDF utilizando IA.

2. Otimizacao do Agente Extrator (backend/agente.py):
   - Integracao com a API Google Gemini (google-genai) para extracao
     estruturada e contextualizada dos campos da NF.
   - Parsing de layout tabular de alta precisao utilizando pypdf.
   - Classificacao automatica da despesa baseada na analise semantica
     dos produtos/servicos da nota, identificando categorias oficiais
     (Manutencao e Operacao, Insumos Agricolas, etc.) e termos detectados.

3. Interface Web Aprimorada (frontend/index.html, style.css, app.js):
   - Arquitetura Single Page Application (SPA): tela de login e dashboard
     integrados sem recarregamento de pagina.
   - Controle de sessao seguro no backend Flask.
   - Configuracao dinamica da chave da API Gemini em tempo real diretamente
     pela interface (com mascara e botao de alternancia de visibilidade).
   - Validacao de arquivo PDF com exibicao de tamanho e opcao de descarte.
   - Apresentacao dos resultados em abas:
     * Visualizacao Formatada: cards visuais de Emitente, Destinatario,
       Dados da Nota (numero, datas, valor total, parcelas),
       Descricao dos Produtos e banner de Classificacao da Despesa.
     * JSON Estruturado: payload bruto retornado pela IA com botao de copia.
   - Rodape com consumo da rota /api/version para exibicao do commit
     atual do Git em tempo real.

4. Reorganizacao Arquitetural Limpa:
   - Separacao modular em pastas dedicadas (frontend/, backend/, deploy/, docs/).
   - Configuracao WSGI otimizada com Gunicorn (--chdir backend server:app).

DADOS DE LOGIN / SENHA
-----------------------
URL de Acesso: http://127.0.0.1:5000/ (ou http://127.0.0.1:5000/login)
Usuario: admin
Senha:   admin123

GESTAO DA CHAVE DE API (Google Gemini)
---------------------------------------
A chave pode ser fornecida de duas formas:
  1. Em tempo real: na pagina principal, campo "Chave da API Gemini"
     (aplicada diretamente em memoria, sem reiniciar o servidor).
  2. Via arquivo .env: definir GEMINI_API_KEY=sua_chave_aqui na raiz
     (arquivo excluido do repositorio pelo .gitignore para seguranca).
Obtencao gratuita da chave: https://aistudio.google.com/

COMO EXECUTAR LOCALMENTE
------------------------
1. Clonar o repositorio:
   git clone https://github.com/Jubsvf/Leitor-de-PDF.git
   cd Leitor-de-PDF

2. Criar e ativar o ambiente virtual (recomendado):
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/macOS:
   source venv/bin/activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Configurar o .env (opcional, copiar de .env.example):
   GEMINI_API_KEY=sua_chave_aqui

5. Iniciar o servidor Flask:
   python backend/server.py
   (ou: cd backend && python server.py)

6. Acessar no navegador:
   http://127.0.0.1:5000/

7. Documentacao Swagger / OpenAPI:
   http://127.0.0.1:5000/apidocs

ENDPOINTS DA API
-----------------
- GET  /                     : Pagina principal unificada (SPA)
- GET  /login                : Rota alternativa para a SPA
- GET  /api/session          : Estado atual da sessao (autenticado/usuario)
- POST /api/login            : Autenticacao com usuario e senha
- POST /api/logout           : Encerramento de sessao
- GET  /api/version          : Hash do commit Git atual e repositorio
- POST /api/configurar-chave : Configuracao dinamica da chave Gemini
- GET  /api/status-chave     : Verifica se a chave esta definida
- POST /api/extrair-pdf      : Processamento do arquivo PDF com IA
- GET  /apidocs              : Documentacao Swagger UI interativa

TECNOLOGIAS UTILIZADAS
-----------------------
- Python 3.10+ / Flask (Backend e API REST)
- Google Gemini API (google-genai)
- pypdf (Extracao e leitura estruturada de PDF)
- HTML5, CSS3 Moderno e JavaScript Vanilla (Frontend SPA responsivo)
- Flasgger (Documentacao Swagger UI / OpenAPI)
- Gunicorn / Render (Suporte a deploy em nuvem via Procfile / render.yaml)

=============================================================
