# Leitor de Nota Fiscal com Inteligência Artificial (Google Gemini)

Aplicação web desenvolvida para a atividade prática acadêmica, com foco especializado na **extração inteligente e estruturação automatizada de dados de notas fiscais em formato PDF**, utilizando Inteligência Artificial Generativa (**Google Gemini API**) e algoritmo de leitura e parsing de layout via **pypdf**.

---

## 📌 Sobre o Projeto

O **Leitor de Nota Fiscal** oferece uma experiência completa e moderna para processamento de documentos fiscais em PDF. Através de uma interface limpa em formato Single Page Application (SPA), o usuário realiza o upload do documento, configura a chave da API em tempo real e obtém imediatamente os dados estruturados do emitente, destinatário, valores, parcelas, produtos e a **classificação automática da despesa**.

A solução foi projetada de forma modular e desacoplada, eliminando complexidades desnecessárias e concentrando-se com alta fidelidade no objetivo principal da atividade acadêmica.

---

## 🚀 Principais Funcionalidades

1. **Autenticação e Sessão Segura**:
   - Tela de login integrada na interface unificada (SPA), sem recarregamentos bruscos de página.
   - Controle de sessão no backend Flask com rotas protegidas por autenticação.
   - **Credenciais de acesso acadêmico**:
     - **Usuário**: `admin`
     - **Senha**: `admin123`

2. **Gestão Flexível da Chave da API Gemini**:
   - **Em tempo real via Interface**: campo dedicado para inserção da chave com máscara de visualização e botão de alternância (mostrar/ocultar), permitindo o uso sem necessidade de reiniciar o servidor.
   - **Via Variável de Ambiente**: suporte a arquivo `.env` (`GEMINI_API_KEY`), protegido pelo `.gitignore`.
   - Indicador visual em tempo real do status de configuração da chave.

3. **Upload e Validação de Arquivo PDF**:
   - Validação de formato (apenas arquivos `.pdf`).
   - Exibição em tempo real do nome e tamanho do arquivo selecionado.
   - Botão para descarte ou troca imediata do documento antes do processamento.
   - Feedback visual com estado de carregamento durante a extração.

4. **Extração Inteligente com Agente de IA**:
   - Leitura otimizada do PDF preservando layout tabular de notas fiscais (`pypdf layout mode`).
   - Extração estruturada via modelo **Google Gemini** com prompt especializado.
   - **Campos extraídos com precisão**:
     - **Emitente (Fornecedor)**: Razão Social, Nome Fantasia, CNPJ, Inscrição Estadual e Endereço Completo.
     - **Destinatário (Faturado)**: Nome Completo / Razão Social, CPF / CNPJ e Endereço Completo.
     - **Dados da Nota**: Número da NF, Data de Emissão, Data de Vencimento/Saída, Valor Total e Condição de Pagamento / Parcelas detalhadas.
     - **Produtos / Serviços**: Descrição consolidada dos itens constantes na nota fiscal.
   - **Classificação Automática da Despesa**: categorização inteligente baseada no contexto dos produtos/serviços faturados (ex.: *Manutenção e Operação*, *Insumos Agrícolas*, *Serviços Operacionais*, *Infraestrutura*, etc.), acompanhada dos termos-chave identificados que fundamentaram a decisão.

5. **Apresentação dos Resultados em Visualização Dupla**:
   - **Aba "Visualização Formatada"**: Cards visuais organizados por blocos lógicos (Emitente, Destinatário, Dados da Nota, Produtos e Banner em destaque com a Classificação da Despesa).
   - **Aba "JSON Estruturado"**: Visualização do payload JSON bruto retornado pela IA, com formatação e botão de **Copiar JSON** com um único clique.

6. **Rodapé com Versionamento Dinâmico**:
   - Integração com a rota `/api/version`, que lê o hash do commit Git atual (`588c0a4`) em tempo real e provê link direto para o repositório oficial no GitHub.

7. **Documentação Interativa Swagger / OpenAPI**:
   - Endpoints REST documentados e testáveis interativamente via Swagger UI no endpoint `/apidocs`.

---

## 📁 Estrutura Organizada do Projeto

O repositório adota uma arquitetura limpa, modular e com separação estrita de responsabilidades:

```text
Leitor-de-PDF/
├── frontend/                  # Camada de Apresentação (Interface SPA)
│   ├── index.html             # Estrutura unificada (Login integrado + Dashboard de Extração)
│   ├── style.css              # Identidade visual moderna, tema escuro e responsividade
│   └── app.js                 # Controlador frontend (sessão, upload, tabs e consumo da API)
├── backend/                   # Camada de Servidor e Regras de Negócio
│   ├── server.py              # Servidor Flask, rotas REST, sessão e documentação Swagger
│   ├── agente.py              # Agente de IA Gemini e rotinas de leitura de PDF com pypdf
│   └── database/              # Camada de persistência relacional (SQLAlchemy / SQLite / PostgreSQL)
│       ├── __init__.py
│       ├── connection.py      # Gerenciamento de conexão com banco de dados
│       ├── models.py          # Modelos de entidades de dados
│       ├── seed.py            # Carga inicial de dados
│       └── fintrack.db        # Banco de dados local SQLite
├── deploy/                    # Configurações de Deploy em Nuvem
│   ├── Procfile               # Configuração WSGI Gunicorn para Render / Heroku
│   └── render.yaml            # Infraestrutura como código para publicação no Render
├── docs/                      # Documentação Acadêmica
│   └── README.TXT             # Relatório técnico acadêmico e histórico de versões
├── requirements.txt           # Dependências do projeto Python
├── .env.example               # Exemplo de configuração de variáveis de ambiente
└── README.md                  # Documentação principal do repositório
```

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.10+
- **Backend / API REST**: [Flask](https://flask.palletsprojects.com/), [Flask-CORS](https://flask-cors.readthedocs.io/), [Flasgger (Swagger/OpenAPI)](https://github.com/flasgger/flasgger)
- **Servidor de Aplicação (WSGI)**: [Gunicorn](https://gunicorn.org/)
- **Inteligência Artificial**: [Google Gemini API (google-genai)](https://ai.google.dev/)
- **Processamento de PDF**: [pypdf](https://pypdf.readthedocs.io/)
- **Persistência / ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) com drivers SQLite e PostgreSQL
- **Frontend**: HTML5 semântico, CSS3 moderno (Custom Properties, Flexbox, Grid, Animações e Glassmorphism) e JavaScript Vanilla (SPA sem dependências pesadas)

---

## 💻 Como Executar Localmente

### 1. Pré-requisitos
- Python 3.10 ou superior instalado na máquina.
- Git instalado (opcional, para clonagem).

### 2. Clonar o Repositório
```bash
git clone https://github.com/Jubsvf/Leitor-de-PDF.git
cd Leitor-de-PDF
```

### 3. Criar e Ativar o Ambiente Virtual (Recomendado)
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 5. Configurar as Variáveis de Ambiente (Opcional)
Você pode criar um arquivo `.env` na raiz do projeto copiando o modelo de `.env.example`:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
SECRET_KEY=fintrack-secret-chave-segura
```
> *Nota: Se preferir, você não precisa criar o arquivo `.env`; a chave da API do Gemini pode ser informada diretamente na interface após o login.*

### 6. Iniciar o Servidor Flask
A partir da raiz do projeto:
```bash
python backend/server.py
```
*(Ou acesse a pasta `backend` com `cd backend` e execute `python server.py`)*

### 7. Acessar a Aplicação
Abra seu navegador e acesse:
- **Aplicação Principal**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/) (ou [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login))
- **Documentação da API (Swagger)**: [http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)

---

## 🔑 Credenciais de Acesso e Uso

| Campo | Valor Padrão |
| :--- | :--- |
| **Usuário** | `admin` |
| **Senha** | `admin123` |

### Fluxo de Uso:
1. Faça login utilizando as credenciais acima.
2. No card **Chave da API Gemini**, insira sua chave caso não a tenha definido no `.env` (obtenha gratuitamente no [Google AI Studio](https://aistudio.google.com/)).
3. Clique em **Escolher arquivo** e selecione uma Nota Fiscal em formato PDF.
4. Clique no botão **EXTRAIR DADOS**.
5. Visualize os dados formatados nos cards ou navegue até a aba **JSON Estruturado** para inspecionar ou copiar o payload completo.

---

## 📡 Endpoints da API REST

| Método | Rota | Autenticação | Descrição |
| :--- | :--- | :---: | :--- |
| `GET` | `/` ou `/login` | Pública | Entrega a aplicação web unificada (SPA). |
| `GET` | `/api/session` | Pública | Retorna o estado atual da sessão (`logged_in` e `username`). |
| `POST` | `/api/login` | Pública | Valida credenciais e inicia a sessão autenticada. |
| `POST` | `/api/logout` | Pública | Encerra a sessão do usuário. |
| `GET` | `/api/version` | Pública | Retorna o hash do commit Git atual e link do repositório. |
| `POST` | `/api/configurar-chave` | Sessão ativa | Armazena dinamicamente a chave da API Gemini em memória. |
| `GET` | `/api/status-chave` | Sessão ativa | Informa se uma chave válida do Gemini está configurada. |
| `POST` | `/api/extrair-pdf` | Sessão ativa | Recebe o arquivo PDF via `multipart/form-data` e retorna os dados extraídos em JSON. |
| `GET` | `/apidocs` | Pública | Interface interativa Swagger UI / OpenAPI com especificações dos endpoints. |

---

## ☁️ Deploy em Nuvem

O projeto possui suporte nativo para publicação em plataformas em nuvem como o [Render](https://render.com/):

- **Arquivo `deploy/Procfile`**:
  ```text
  web: gunicorn --chdir backend server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
  ```
- **Arquivo `deploy/render.yaml`**:
  Define a especificação completa de serviço com comando de build (`pip install -r requirements.txt`) e variáveis de ambiente gerenciadas.

---

## 📄 Informações Acadêmicas e Repositório

- **Repositório GitHub**: [https://github.com/Jubsvf/Leitor-de-PDF](https://github.com/Jubsvf/Leitor-de-PDF)
- **Commit de Referência**: `588c0a4` ([Ver commit no GitHub](https://github.com/Jubsvf/Leitor-de-PDF/commit/588c0a4372e10666c693a53a19f24c84cb2607c0))
- **Documentação Complementar**: consulte [docs/README.TXT](docs/README.TXT) para o relatório técnico em texto puro.