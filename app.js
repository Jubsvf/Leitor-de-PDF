// ==========================================================================
// Leitor de Nota Fiscal — Frontend Controller (app.js)
// ==========================================================================

const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '5000' ? 'http://127.0.0.1:5000' : '';

// Elementos do DOM - Upload
const pdfInput = document.getElementById('pdfInput');
const fileStatusText = document.getElementById('fileStatusText');
const fileInfoBox = document.getElementById('fileInfoBox');
const fileNameEl = document.getElementById('fileName');
const fileSizeEl = document.getElementById('fileSize');
const btnRemoveFile = document.getElementById('btnRemoveFile');
const btnExtract = document.getElementById('btnExtract');
const btnText = document.getElementById('btnText');

// Elementos do DOM - Resultado & Abas
const resultCard = document.getElementById('resultCard');
const tabFormatada = document.getElementById('tabFormatada');
const tabJson = document.getElementById('tabJson');
const viewFormatada = document.getElementById('viewFormatada');
const viewJson = document.getElementById('viewJson');
const jsonResult = document.getElementById('jsonResult');
const btnCopyJson = document.getElementById('btnCopyJson');

// Elementos do DOM - Visualização Formatada
const fmtCategoria = document.getElementById('fmtCategoria');
const fmtTermos = document.getElementById('fmtTermos');
const fmtRazaoSocial = document.getElementById('fmtRazaoSocial');
const fmtNomeFantasia = document.getElementById('fmtNomeFantasia');
const fmtCnpjEmitente = document.getElementById('fmtCnpjEmitente');
const fmtNomeDestinatario = document.getElementById('fmtNomeDestinatario');
const fmtCpfDestinatario = document.getElementById('fmtCpfDestinatario');
const fmtNumeroNf = document.getElementById('fmtNumeroNf');
const fmtDataEmissao = document.getElementById('fmtDataEmissao');
const fmtDataVencimento = document.getElementById('fmtDataVencimento');
const fmtValorTotal = document.getElementById('fmtValorTotal');
const fmtParcelas = document.getElementById('fmtParcelas');
const fmtProdutos = document.getElementById('fmtProdutos');

// Elementos do DOM - Chave Gemini & Versão
const apiKeyInput = document.getElementById('apiKeyInput');
const btnAplicarChave = document.getElementById('btnAplicarChave');
const btnToggleKey = document.getElementById('btnToggleKey');
const keyStatusBadge = document.getElementById('keyStatusBadge');
const versionLink = document.getElementById('versionLink');

// Estado
let selectedFile = null;
let ultimoResultadoExtracao = null;

// Formatação do tamanho do arquivo (B / KB / MB)
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  const kb = bytes / 1024;
  if (kb < 1024) return kb.toFixed(2) + ' KB';
  const mb = kb / 1024;
  return mb.toFixed(2) + ' MB';
}

// Formatação de valor em moeda brasileira
function formatCurrency(val) {
  if (!val) return 'R$ 0,00';
  let str = String(val).trim().replace('R$', '').trim();
  if (!str.includes(',')) {
    const num = parseFloat(str);
    if (!isNaN(num)) {
      return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }
  }
  return 'R$ ' + str;
}

// Reset da seleção de arquivo
function resetFileSelection() {
  selectedFile = null;
  ultimoResultadoExtracao = null;
  pdfInput.value = '';
  fileInfoBox.classList.add('hidden');
  fileStatusText.textContent = 'Nenhum arquivo escolhido';
  btnExtract.disabled = true;
  if (btnText) btnText.textContent = 'EXTRAIR DADOS';
  if (resultCard) resultCard.classList.add('hidden');
}

// Manipulação da seleção de arquivo PDF
pdfInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      alert('Por favor, selecione um arquivo no formato PDF.');
      resetFileSelection();
      return;
    }

    selectedFile = file;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatFileSize(file.size);

    fileInfoBox.classList.remove('hidden');
    fileStatusText.textContent = '';
    btnExtract.disabled = false;
  } else {
    resetFileSelection();
  }
});

btnRemoveFile.addEventListener('click', () => {
  resetFileSelection();
});

// Ação de Extrair Dados via IA / Backend
btnExtract.addEventListener('click', async () => {
  if (!selectedFile) return;

  const originalText = btnText ? btnText.textContent : 'EXTRAIR DADOS';
  if (btnText) btnText.textContent = 'PROCESSANDO COM IA...';
  btnExtract.disabled = true;

  try {
    const formData = new FormData();
    formData.append('pdf', selectedFile);

    const response = await fetch(`${API_BASE}/api/extrair-pdf`, {
      method: 'POST',
      body: formData,
    });

    const responseText = await response.text();
    let dados;
    try {
      dados = JSON.parse(responseText);
    } catch (parseErr) {
      throw new Error(`Resposta do servidor não é um JSON válido: ${responseText.substring(0, 100)}`);
    }

    if (!response.ok) {
      throw new Error(dados.erro || `Falha na requisição (Status ${response.status}).`);
    }

    ultimoResultadoExtracao = dados;
    renderDadosExtraidos(dados);
  } catch (error) {
    console.error('Erro na extração:', error);
    alert('Erro ao extrair dados da nota fiscal: ' + error.message);
  } finally {
    if (btnText) btnText.textContent = originalText;
    btnExtract.disabled = false;
  }
});

// Renderização dos Dados Extraídos
function renderDadosExtraidos(dados) {
  // 1. Preencher JSON
  if (jsonResult) {
    jsonResult.textContent = JSON.stringify(dados, null, 2);
  }

  // 2. Preencher Visualização Formatada
  const classif = dados['CLASSIFICAÇÃO'] || {};
  const categoria = (classif.categoria || dados['Categoria'] || 'MANUTENÇÃO E OPERAÇÃO').toUpperCase();
  if (fmtCategoria) fmtCategoria.textContent = categoria;

  if (fmtTermos) {
    fmtTermos.innerHTML = '';
    const termos = classif.termos_detectados || classif.termos || [];
    if (Array.isArray(termos) && termos.length > 0) {
      termos.forEach((termo) => {
        const span = document.createElement('span');
        span.className = 'pill-item';
        span.textContent = termo.toUpperCase();
        fmtTermos.appendChild(span);
      });
    } else {
      const span = document.createElement('span');
      span.className = 'pill-item';
      span.textContent = 'CLASSIFICAÇÃO GERAL';
      fmtTermos.appendChild(span);
    }
  }

  // Fornecedor / Emitente
  const nomeEmitente = dados['Nome do Emitente'] || dados['razao_social'] || '-';
  if (fmtRazaoSocial) fmtRazaoSocial.textContent = nomeEmitente;
  if (fmtNomeFantasia) {
    fmtNomeFantasia.textContent = dados['Nome Fantasia'] || dados['nome_fantasia'] || (nomeEmitente !== '-' ? nomeEmitente.split(',')[0].replace(/RECEBI\(EMOS\)\s+DE\s+/i, '') : '-');
  }
  if (fmtCnpjEmitente) fmtCnpjEmitente.textContent = dados['CNPJ do Emitente'] || dados['cnpj'] || '-';

  // Faturado / Destinatário
  if (fmtNomeDestinatario) fmtNomeDestinatario.textContent = dados['Nome do Destinatário'] || dados['nome_destinatario'] || '-';
  if (fmtCpfDestinatario) fmtCpfDestinatario.textContent = dados['CNPJ do Destinatário'] || dados['cpf'] || dados['cnpj_destinatario'] || '-';

  // Dados da Nota
  if (fmtNumeroNf) fmtNumeroNf.textContent = dados['Número da Nota Fiscal'] || dados['numero_nf'] || '-';
  if (fmtDataEmissao) fmtDataEmissao.textContent = dados['Data de Emissão'] || dados['data_emissao'] || '-';
  if (fmtDataVencimento) fmtDataVencimento.textContent = dados['Data de Vencimento'] || dados['data_vencimento'] || dados['Data de Emissão'] || '-';
  if (fmtValorTotal) fmtValorTotal.textContent = formatCurrency(dados['Valor Total'] || dados['valor_total']);
  if (fmtParcelas) fmtParcelas.textContent = dados['Parcelas'] || '1 parcela(s)';

  // Produtos / Serviços
  if (fmtProdutos) {
    fmtProdutos.textContent = dados['Descrição dos Produtos'] || dados['descricao_produtos'] || 'Itens da Nota Fiscal';
  }

  // Exibir o card de resultados
  if (resultCard) {
    resultCard.classList.remove('hidden');
    resultCard.scrollIntoView({ behavior: 'smooth' });
  }
}

// Alternância entre as abas (Formatada vs JSON)
if (tabFormatada && tabJson) {
  tabFormatada.addEventListener('click', () => {
    tabFormatada.classList.add('active');
    tabJson.classList.remove('active');
    viewFormatada.classList.remove('hidden');
    viewJson.classList.add('hidden');
  });

  tabJson.addEventListener('click', () => {
    tabJson.classList.add('active');
    tabFormatada.classList.remove('active');
    viewJson.classList.remove('hidden');
    viewFormatada.classList.add('hidden');
  });
}

// Copiar JSON para área de transferência
if (btnCopyJson) {
  btnCopyJson.addEventListener('click', async () => {
    if (!ultimoResultadoExtracao) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(ultimoResultadoExtracao, null, 2));
      const originalText = btnCopyJson.textContent;
      btnCopyJson.textContent = 'Copiado!';
      setTimeout(() => {
        btnCopyJson.textContent = originalText;
      }, 2000);
    } catch (err) {
      alert('Não foi possível copiar o JSON.');
    }
  });
}

// Configuração da Chave da API Gemini
async function verificarStatusChave() {
  try {
    const res = await fetch(`${API_BASE}/api/status-chave`);
    if (res.ok) {
      const data = await res.json();
      if (keyStatusBadge) {
        if (data.configurada) {
          keyStatusBadge.textContent = 'Configurada (' + (data.origem === 'runtime' ? 'Sessão' : 'Ativa') + ')';
          keyStatusBadge.className = 'status-badge ready';
          if (data.preview && apiKeyInput) {
            apiKeyInput.placeholder = `Chave atual: ${data.preview}`;
          }
        } else {
          keyStatusBadge.textContent = 'Não configurada (Modo Fallback)';
          keyStatusBadge.className = 'status-badge';
        }
      }
    }
  } catch (err) {
    if (keyStatusBadge) keyStatusBadge.textContent = 'Servidor Offline';
  }
}

if (btnAplicarChave && apiKeyInput) {
  btnAplicarChave.addEventListener('click', async () => {
    const chave = apiKeyInput.value.trim();
    if (!chave) {
      alert('Informe a chave da API Gemini.');
      return;
    }

    btnAplicarChave.disabled = true;
    btnAplicarChave.textContent = 'Aplicando...';

    try {
      const res = await fetch(`${API_BASE}/api/configurar-chave`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: chave }),
      });

      const data = await res.json();
      if (res.ok) {
        alert('Chave da API Gemini configurada com sucesso!');
        apiKeyInput.value = '';
        verificarStatusChave();
      } else {
        alert('Erro ao configurar chave: ' + (data.erro || 'Erro desconhecido'));
      }
    } catch (err) {
      alert('Erro de comunicação com o servidor: ' + err.message);
    } finally {
      btnAplicarChave.disabled = false;
      btnAplicarChave.textContent = 'Aplicar Chave';
    }
  });
}

if (btnToggleKey && apiKeyInput) {
  btnToggleKey.addEventListener('click', () => {
    apiKeyInput.type = apiKeyInput.type === 'password' ? 'text' : 'password';
  });
}

// Carregar versão do Git no rodapé
async function carregarVersao() {
  if (!versionLink) return;
  try {
    const res = await fetch(`${API_BASE}/api/version`);
    if (res.ok) {
      const data = await res.json();
      versionLink.textContent = data.commit_short || 'main';
      if (data.link_commit) {
        versionLink.href = data.link_commit;
      }
    }
  } catch (err) {
    versionLink.textContent = 'local';
  }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  verificarStatusChave();
  carregarVersao();
});
