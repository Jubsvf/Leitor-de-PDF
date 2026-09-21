# Leitor de Nota Fiscal (Extração de Dados em PDF)

Aplicação web desenvolvida para atividade prática acadêmica, projetada para fornecer uma interface limpa, intuitiva e direta para o upload de notas fiscais em formato PDF, preparando o arquivo para futura extração automatizada de dados utilizando Inteligência Artificial.

---

## 📌 Sobre o Projeto

O objetivo deste projeto é servir como camada de entrada (frontend) para um fluxo de processamento inteligente de documentos fiscais. A interface permite que o usuário selecione um arquivo PDF de nota fiscal, visualize detalhes imediatos (nome e tamanho), remova ou troque o arquivo e dispare a ação de extração de dados.

---

## 📁 Estrutura do Projeto e Resumo dos Códigos

O projeto foi construído utilizando tecnologias web fundamentais (HTML, CSS e JavaScript Vanilla), prezando pela simplicidade, clareza e facilidade de manutenção:

### 1. `index.html`
- **Função**: Define a estrutura semântica e acessível da interface.
- **Destaques**:
  - Cabeçalho com título e descrição do propósito do sistema.
  - Card centralizado com ícones SVG modernos para upload.
  - Input de arquivo customizado com texto de feedback de seleção.
  - Card dinâmico para exibição de metadados do PDF selecionado (nome, tamanho e botão de remoção rápida).
  - Botão de ação *"EXTRAIR DADOS"*, inicialmente desabilitado até a escolha de um arquivo válido.
  - Legenda e atribuição de figura acadêmica (*"Fonte: Autor (2025)"*).

### 2. `style.css`
- **Função**: Responsável por toda a identidade visual, layout e responsividade.
- **Destaques**:
  - Estilização limpa, sem dependências externas pesadas (apenas importação da fonte *Inter*).
  - Paleta de cores neutras e corporativas (tons de cinza, ardósia e azul de destaque).
  - Feedback visual claro para os estados dos botões (hover, clique e desabilitado).
  - Layout flexível e responsivo, adaptável tanto a desktops quanto a dispositivos móveis.

### 3. `app.js`
- **Função**: Controla a lógica e a interatividade da aplicação no navegador.
- **Destaques**:
  - **Validação de formato**: Garante que apenas arquivos `.pdf` válidos sejam aceitos, alertando o usuário caso contrário.
  - **Cálculo de tamanho**: Converte e formata dinamicamente o peso do arquivo em bytes para uma visualização amigável (`KB` ou `MB`).
  - **Gerenciamento de estado**: Controla a visibilidade dos metadados do arquivo e o desbloqueio do botão de extração.
  - **Limpeza e reset**: Permite remover o arquivo atual e restaurar a interface ao estado inicial.
  - **Ponto de integração**: Prepara o arquivo selecionado no evento de clique para envio ao futuro Agente/API de IA.

---

## 🚀 Como Executar

Por utilizar tecnologias nativas, a aplicação não requer instalação de dependências ou servidores complexos:

1. Clone o repositório:
   ```bash
   git clone https://github.com/Jubsvf/Leitor-de-PDF.git
   ```
2. Abra a pasta do projeto e dê dois cliques no arquivo `index.html` (ou abra-o diretamente no navegador de sua preferência).

---

## 🔮 Próximos Passos

- Integração com backend / Agente de IA para parsing e OCR do PDF.
- Extração de campos estruturados da NF (Chave de Acesso, CNPJ Emitente/Destinatário, Data, Itens e Valor Total).
- Exibição tabular e exportação dos dados extraídos (ex: JSON ou CSV).