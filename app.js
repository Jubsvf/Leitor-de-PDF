// Elementos do DOM
const pdfInput = document.getElementById('pdfInput');
const fileStatusText = document.getElementById('fileStatusText');
const fileInfoBox = document.getElementById('fileInfoBox');
const fileNameEl = document.getElementById('fileName');
const fileSizeEl = document.getElementById('fileSize');
const btnRemoveFile = document.getElementById('btnRemoveFile');
const btnExtract = document.getElementById('btnExtract');

// Estado da Aplicação
let selectedFile = null;

// Formatação do tamanho do arquivo (KB/MB)
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  const kb = bytes / 1024;
  if (kb < 1024) return kb.toFixed(2) + ' KB';
  const mb = kb / 1024;
  return mb.toFixed(2) + ' MB';
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

// Remover arquivo selecionado
btnRemoveFile.addEventListener('click', () => {
  resetFileSelection();
});

const resultCard = document.getElementById('resultCard');
const jsonResult = document.getElementById('jsonResult');
const btnSalvarConta = document.getElementById('btnSalvarConta');
const btnText = document.getElementById('btnText');

// Aponta para o backend Flask (porta 5000) caso aberto via Live Server (porta 5500) ou file:///
const API_BASE = (window.location.port !== '5000') ? 'http://127.0.0.1:5000' : '';

let ultimoResultadoExtracao = null;

// Reset da seleção
function resetFileSelection() {
  selectedFile = null;
  ultimoResultadoExtracao = null;
  pdfInput.value = '';
  fileInfoBox.classList.add('hidden');
  fileStatusText.textContent = 'Nenhum arquivo escolhido';
  btnExtract.disabled = true;
  if (resultCard) resultCard.classList.add('hidden');
  if (btnText) btnText.textContent = 'EXTRAIR DADOS';
}

// Acionamento do Agente de IA para Extração dos Dados
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
      throw new Error(`Resposta do servidor não é um JSON válido (Status ${response.status}): ${responseText.substring(0, 100)}`);
    }

    if (!response.ok) {
      throw new Error(dados.erro || `Falha na requisição (Status ${response.status}).`);
    }

    ultimoResultadoExtracao = dados;

    if (jsonResult) {
      jsonResult.textContent = JSON.stringify(dados, null, 2);
    }
    if (resultCard) {
      resultCard.classList.remove('hidden');
      resultCard.scrollIntoView({ behavior: 'smooth' });
    }
  } catch (error) {
    console.error('Erro na extração:', error);
    if (error.message.includes('Failed to fetch') && window.location.protocol === 'file:') {
      alert('Não foi possível conectar ao backend na porta 5000.\nCertifique-se de que o servidor Flask está em execução (python server.py) ou acesse via http://127.0.0.1:5000/');
    } else {
      alert('Erro ao extrair dados da nota fiscal: ' + error.message);
    }
  } finally {
    if (btnText) btnText.textContent = originalText;
    btnExtract.disabled = false;
  }
});

// Ação para salvar o resultado diretamente no contas a pagar
if (btnSalvarConta) {
  btnSalvarConta.addEventListener('click', async () => {
    if (!ultimoResultadoExtracao) return;
    try {
      btnSalvarConta.disabled = true;
      btnSalvarConta.textContent = 'Salvando...';

      const res = await fetch(`${API_BASE}/api/salvar-conta-pagar-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ultimoResultadoExtracao),
      });

      const resData = await res.json();
      if (res.ok) {
        alert('Conta a pagar registrada com sucesso no banco de dados PostgreSQL! Você pode consultá-la na aba "Contas Pagar".');
      } else {
        alert('Erro ao salvar conta: ' + (resData.erro || 'Erro desconhecido'));
      }
    } catch (err) {
      alert('Erro de conexão ao salvar conta: ' + err.message);
    } finally {
      btnSalvarConta.disabled = false;
      btnSalvarConta.textContent = 'Salvar Dados';
    }
  });
}


