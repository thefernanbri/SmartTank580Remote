// Função para verificar a existência de arquivos temporários
function verificarArquivosTemp() {
	$.ajax({
		url: '/verificar_arquivos_temp', // Rota Flask para verificar os arquivos temporários
		type: 'GET',
		success: function(response) {
			if (response.arquivos_existem) {
				// Exibir uma mensagem e as opções Limpar e Ignorar
				var confirmacao = confirm('Existem digitalizações temporárias. Deseja limpar ?');

				if (confirmacao) {
					// O usuário escolheu Limpar, então execute a limpeza e atualize a div de resultado
					$.ajax({
						url: '/limpar_arquivos_temp', // Rota Flask para limpar os arquivos temporários
						type: 'GET',
						success: function(resultado) {
							$('#result').text(resultado);
						}
					});
				} else {
					// O usuário escolheu Ignorar, não faz nada
					$('#result').text('Limpeza ignorada!');
				}
			}
		}
	});
}

// Chame a função de verificação assim que a página carregar
verificarArquivosTemp();

// FUNÇÕES DOS BOTÕES
document.addEventListener("DOMContentLoaded", function() {
	// Adicione tratamento de eventos aos botões
	document.getElementById('createScanJobButton').addEventListener("click", createScanJob);
	document.getElementById('SaveButton').addEventListener("click", salvardigitalizacao);
	document.getElementById('JoinButton').addEventListener("click", mesclar);
	// Adicione um ouvinte de evento ao elemento select
	const documentTypeSelect = document.getElementById('documentType');
	documentTypeSelect.addEventListener("change", updateScanSettings);
});



// Mapeamento de tradução para os estados do scanner
const scannerStateTranslations = {
  "unknown": "Desconhecido",
  "Processing": "Digitalizando",
  "Idle": "Em espera",
};

// Mapeamento de tradução para erros do scanner
const scannerErrorTranslations = {
  "unknown": "Desconhecido",
  "noError": "Sem erro",
};

// Variável para controlar se há uma requisição em andamento
let scannerStatusRequestInProgress = false;
let scannerStatusIntervalId = null;

// Função para verificar o estado do scanner
function checkScannerStatus() {
  // Evita requisições simultâneas
  if (scannerStatusRequestInProgress) {
    return;
  }
  
  scannerStatusRequestInProgress = true;
  
  fetch('/check_scanner_status')
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro na solicitação para verificar o estado do scanner');
      }
      return response.json();
    })
    .then(data => {
      if (data.erro) {
        showError('resultContainer', 'Erro: ' + data.erro);
      } else {
        // Traduzir os valores do JSON antes de exibi-los
        const translatedState = scannerStateTranslations[data.scannerState] || data.scannerState;
        const translatedError = scannerErrorTranslations[data.scannerError] || data.scannerError;

        showInfo('StateScannerContainer', `Estado do Scanner: ${translatedState}`);
        
        if (data.scannerError !== 'noError') {
          showInfo('ErrorScannerContainer', `Erro do Scanner: ${translatedError}`);
        } else {
          // Se não houver erro, limpe o container de erro
          clearError('ErrorScannerContainer');
        }
      }
    })
    .catch(error => {
      if (error.message.includes('winerror 10060')) {
        showError('resultContainer', 'A impressora está offline');
      } else {
        showError('resultContainer', 'Erro' + error.message);
      }
    })
    .finally(() => {
      scannerStatusRequestInProgress = false;
    });
}

// Função para limpar o conteúdo do elemento com o ID especificado
function clearError(elementId) {
	const element = document.getElementById(elementId);
	if (element) {
		element.innerHTML = '';
	}
}

// Iniciar o polling apenas uma vez quando a página carregar
// Intervalo aumentado para 5 segundos para reduzir carga na impressora
if (!scannerStatusIntervalId) {
  scannerStatusIntervalId = setInterval(checkScannerStatus, 5000); // 5000 milissegundos = 5 segundos
}


let loopIntervalId = null; // Variável para armazenar o ID do intervalo

// Função para iniciar o loop
function iniciarDigitalizacaoStatus() {
    if (!loopIntervalId) {
        loopIntervalId = setInterval(checkDigitalizacaoStatus, 2000);
    }
}

// Função para parar o loop e limpar os elementos
function pararDigitalizacaoStatus() {
    if (loopIntervalId) {
        clearInterval(loopIntervalId);
        loopIntervalId = null;
        // Limpe os elementos de conteúdo
        clearError('resultContainer');
        clearError('stateContainer');
        clearError('reasonContainer');
    }
}

// Função para parar o loop de verificação da digitalização
function pararDigitalizacaoStatus2() {
    if (loopIntervalId) {
        clearInterval(loopIntervalId);
        loopIntervalId = null;
    }
}

// Função para verificar o estado da digitalização
function checkDigitalizacaoStatus() {
    let loopAtivo = false;
    fetch('/check_Digitalizacao_status')
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                showError('resultContainer', 'Erro ao verificar o estado da impressora: ' + data.erro);
            } else {
                showInfo('stateContainer', `Estado da digitalização: ${data.estado}`);
                showInfo('reasonContainer', `Motivo: ${data.motivo}`);
                
                // Se o arquivo foi baixado com sucesso, parar o loop de monitoramento e atualizar preview
                if (data.arquivo_baixado || data.estado === "Concluído") {
                    pararDigitalizacaoStatus();
                    showInfo('resultContainer', 'Digitalização concluída e arquivo baixado com sucesso!');
                    
                    // Adicionar ao preview se houver informações do arquivo
                    if (data.nome_arquivo && data.url_preview) {
                        adicionarAoPreview(data.nome_arquivo, data.url_preview, data.tipo || 'pdf');
                    } else {
                        // Se não tiver informações, recarregar todos os arquivos
                        carregarPreview();
                    }
                }
            }
        })
        .catch(error => {
            showError('resultContainer', 'Erro ao verificar o estado da digitalização: ' + error);
        });
}

// Função para limpar o conteúdo do elemento
function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}


// Função para verificar o estado da digitalização
function checkScanStatus() {
	fetch('/check_scan_status')
		.then(response => response.json())
		.then(data => {
			if (data.erro) {
				showError('scanResultContainer', 'Erro ao verificar o estado da digitalização: ' + data.erro);
			} else if (data.estado === "Processing") {
				showInfo('stateContainer', `Estado da digitalização: ${data.estado}`);
				showInfo('reasonContainer', `Motivo: ${data.motivo}`);
			} else if (data.estado === "Concluído") {
				showMessage('stateContainer', 'A digitalização foi concluída com sucesso.');
			} else {
				showMessage('stateContainer', 'A digitalização não está em processamento neste momento.');
			}
		})
		.catch(error => {
			showError('scanResultContainer', 'Erro ao verificar o estado da digitalização: ' + error);
		});
}


// Função para exibir informações
function showInfo(containerId, message) {
	const container = document.getElementById(containerId);
	container.innerHTML = message;
	container.classList.remove('error');
}

// Função para exibir mensagens
function showMessage(containerId, message) {
	const container = document.getElementById(containerId);
	container.innerHTML = message;
	container.classList.remove('error');
}

// Função para exibir erros
function showError(containerId, message) {
  const container = document.getElementById(containerId);
  container.innerHTML = message;
  container.classList.add('error');
}

// ========== FUNÇÕES DE PREVIEW ==========

// Função para adicionar um arquivo ao preview
function adicionarAoPreview(nomeArquivo, urlPreview, tipo) {
    const previewContainer = document.getElementById('previewContainer');
    
    // Remover mensagem de vazio se existir
    const emptyMsg = previewContainer.querySelector('.preview-empty');
    if (emptyMsg) {
        emptyMsg.remove();
    }
    
    // Verificar se o arquivo já existe no preview
    const existingItem = previewContainer.querySelector(`[data-nome="${nomeArquivo}"]`);
    if (existingItem) {
        return; // Já existe, não adicionar novamente
    }
    
    // Criar elemento do preview
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';
    previewItem.setAttribute('data-nome', nomeArquivo);
    
    const header = document.createElement('div');
    header.className = 'preview-item-header';
    
    const nome = document.createElement('div');
    nome.className = 'preview-item-name';
    nome.textContent = nomeArquivo;
    
    const removeBtn = document.createElement('button');
    removeBtn.className = 'preview-item-remove';
    removeBtn.textContent = 'Remover';
    removeBtn.onclick = () => removerDoPreview(nomeArquivo, previewItem);
    
    header.appendChild(nome);
    header.appendChild(removeBtn);
    
    const content = document.createElement('div');
    content.className = 'preview-item-content';
    
    if (tipo === 'image') {
        const img = document.createElement('img');
        img.src = urlPreview;
        img.alt = nomeArquivo;
        img.onerror = function() {
            this.style.display = 'none';
            content.innerHTML = `<div class="pdf-placeholder">Erro ao carregar imagem: ${nomeArquivo}</div>`;
        };
        content.appendChild(img);
    } else {
        // Para PDF, usar iframe ou placeholder com link
        const iframe = document.createElement('iframe');
        iframe.src = urlPreview;
        iframe.title = nomeArquivo;
        iframe.onerror = function() {
            this.style.display = 'none';
            content.innerHTML = `<div class="pdf-placeholder"><a href="${urlPreview}" target="_blank">Abrir PDF: ${nomeArquivo}</a></div>`;
        };
        content.appendChild(iframe);
    }
    
    previewItem.appendChild(header);
    previewItem.appendChild(content);
    
    // Adicionar no início do container (mais recente primeiro)
    previewContainer.insertBefore(previewItem, previewContainer.firstChild);
}

// Função para remover um arquivo do preview
function removerDoPreview(nomeArquivo, elemento) {
    if (confirm(`Deseja realmente remover ${nomeArquivo} do preview?`)) {
        elemento.remove();
        
        // Verificar se não há mais itens, mostrar mensagem de vazio
        const previewContainer = document.getElementById('previewContainer');
        if (previewContainer.children.length === 0) {
            const emptyMsg = document.createElement('p');
            emptyMsg.className = 'preview-empty';
            emptyMsg.textContent = 'Nenhum arquivo escaneado ainda';
            previewContainer.appendChild(emptyMsg);
        }
    }
}

// Função para carregar todos os arquivos no preview
function carregarPreview() {
    fetch('/listar_arquivos_temp')
        .then(response => response.json())
        .then(data => {
            const previewContainer = document.getElementById('previewContainer');
            previewContainer.innerHTML = ''; // Limpar container
            
            if (data.erro) {
                previewContainer.innerHTML = `<p class="preview-empty">Erro ao carregar arquivos: ${data.erro}</p>`;
                return;
            }
            
            if (data.arquivos && data.arquivos.length > 0) {
                // Adicionar arquivos (mais recente primeiro - ordem reversa)
                data.arquivos.reverse().forEach(arquivo => {
                    adicionarAoPreview(arquivo.nome, arquivo.url, arquivo.tipo);
                });
            } else {
                previewContainer.innerHTML = '<p class="preview-empty">Nenhum arquivo escaneado ainda</p>';
            }
        })
        .catch(error => {
            const previewContainer = document.getElementById('previewContainer');
            previewContainer.innerHTML = `<p class="preview-empty">Erro ao carregar preview: ${error}</p>`;
        });
}

// Carregar preview quando a página carregar (após DOMContentLoaded)
setTimeout(function() {
    carregarPreview();
}, 500);
