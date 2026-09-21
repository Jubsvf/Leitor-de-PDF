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

// Reset da seleção
function resetFileSelection() {
  selectedFile = null;
  pdfInput.value = '';
  fileInfoBox.classList.add('hidden');
  fileStatusText.textContent = 'Nenhum arquivo escolhido';
  btnExtract.disabled = true;
}

// Ponto de acionamento para o futuro Agente de IA
btnExtract.addEventListener('click', () => {
  if (!selectedFile) return;

  console.log('Arquivo selecionado pronto para envio ao Agente de IA:', selectedFile);
  // O processamento e extração serão implementados pelo Agente de IA posteriormente
});
