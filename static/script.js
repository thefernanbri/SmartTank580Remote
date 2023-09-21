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

// Função para verificar o estado do scanner
function checkScannerStatus() {
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
    });
}

// Agendar a chamada da função a cada 2 segundos
setInterval(checkScannerStatus, 2000); // 2000 milissegundos = 2 segundos



// Função para limpar o conteúdo do elemento com o ID especificado
function clearError(elementId) {
	const element = document.getElementById(elementId);
	if (element) {
		element.innerHTML = '';
	}
}

// Agendar a chamada da função a cada 2 segundos
setInterval(checkScannerStatus, 2000); // 2000 milissegundos = 2 segundos


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

// Função para exibir erros
function showError(containerId, message) {
  const container = document.getElementById(containerId);
  container.innerHTML = message;
  container.classList.add('error');
}
