document.addEventListener("DOMContentLoaded", function() {
	// Adicione tratamento de eventos aos botões
	document.getElementById('createScanJobButton').addEventListener("click", createScanJob);
	document.getElementById('SaveButton').addEventListener("click", salvardigitalizacao);
	document.getElementById('JoinButton').addEventListener("click", mesclar);
	// Adicione um ouvinte de evento ao elemento select
	const documentTypeSelect = document.getElementById('documentType');
	documentTypeSelect.addEventListener("change", updateScanSettings);
});

function updateScanSettings() {
	// SELECIONAR TIPO DO DOCUMENTO
	const documentTypeSelect = document.getElementById('documentType');
	const selectedDocumentOption = documentTypeSelect.value;
	const scanIntent = selectedDocumentOption === 'document' ? 'Document' : 'Photo';
	const documentFormatExt = selectedDocumentOption === 'document' ? 'application/pdf' : 'image/jpeg';

	// SELECIONAR COR DO DOCUMENTO
	const documentColorSelect = document.getElementById('documentColor');
	const selectedColorOption = documentColorSelect.value;
	const colormode = selectedColorOption === 'Color' ? 'RGB24' : 'Grayscale8';

	// SELECIONAR DPI
	const documentDpiSelect = document.getElementById('documentDpi');
	const selectedDpiOption = documentDpiSelect.value;

	// SELECIONAR QUALIDADE
	const documentQualitySelect = document.getElementById('documentQuality');
	const selectedQualityOption = documentQualitySelect.value;

	// SELECIONAR TAMANHO DO DOCUMENTO
	const documentSizeSelect = document.getElementById('documentSize');
	const selectedSizeOption = documentSizeSelect.value;
	let height, width;

	// Mapeie os valores selecionados aos tamanhos correspondentes
	switch (selectedSizeOption) {
		case 'letter':
			height = 3300;
			width = 2550;
			break;
		case 'a4':
			height = 3507;
			width = 2481;
			break;
		case '4x6':
			height = 1800;
			width = 1200;
			break;
		case '5x7':
			height = 2100;
			width = 1500;
			break;
		case '10x15':
			height = 1771;
			width = 1181;
			break;
		default:
			// Trate um caso padrão se necessário
			break;
	}

	// Atualize os valores em scan_settings_xml
	const scanSettingsXml = `
		<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05" xmlns:scc="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
			<pwg:Version>2.1</pwg:Version>
			<scan:Intent>${scanIntent}</scan:Intent>
			<pwg:ScanRegions>
				<pwg:ScanRegion>
					<pwg:Height>${height}</pwg:Height>
					<pwg:Width>${width}</pwg:Width>
					<pwg:XOffset>0</pwg:XOffset>
					<pwg:YOffset>0</pwg:YOffset>
				</pwg:ScanRegion>
			</pwg:ScanRegions>
			<pwg:InputSource>Platen</pwg:InputSource>
			<scan:DocumentFormatExt>${documentFormatExt}</scan:DocumentFormatExt>
			<scan:XResolution>${selectedDpiOption}</scan:XResolution>
			<scan:YResolution>${selectedDpiOption}</scan:YResolution>
			<scan:ColorMode>${colormode}</scan:ColorMode>
			<scan:CompressionFactor>${selectedQualityOption}</scan:CompressionFactor>
			<scan:Brightness>1000</scan:Brightness>
			<scan:Contrast>1000</scan:Contrast>
		</scan:ScanSettings>
	`;

	// Retorne o valor do scanSettingsXml
	return scanSettingsXml;
}

	// Função para verificar o estado do scanner
	function checkScannerStatus() {
		fetch('/check_scanner_status')
			.then(response => response.json())
			.then(data => {
				if (data.erro) {
					showError('resultContainer', 'Erro ao verificar o estado da impressora: ' + data.erro);
				} else {
					showInfo('StateScannerContainer', `Estado do Scanner: ${data.scannerState}`);
					if (data.scannerError !== 'noError') {
						showInfo('ErrorScannerContainer', `Erro do Scanner: ${data.scannerError}`);
					} else {
						// Se não houver erro, limpe o container de erro
						clearError('ErrorScannerContainer');
					}
				}
			})
			.catch(error => {
				showError('resultContainer', 'Erro ao verificar o estado da impressora: ' + error);
			});
	}

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

// Função para limpar o conteúdo do elemento com o ID especificado
function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}


function createScanJob() {
	const documentType = document.getElementById('documentType').value;

	// Obtém o valor do campo "Nome do Arquivo"
	const nomeArquivo = document.getElementById('nomearquivo').value;

	// Obtém o valor de scan_settings_xml do JavaScript
	const scanSettingsXml = updateScanSettings();

	// Faz uma solicitação POST para o Flask com o valor de scan_settings_xml e nomearquivo
	fetch(`/create_scan_job?document_type=${documentType}&nomearquivo=${nomeArquivo}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ scan_settings_xml: scanSettingsXml }),
	})
		iniciarDigitalizacaoStatus()
		.then(response => response.text())
		.then(data => {
			showInfo('resultContainer', data)
		})
		.catch(error => {
			showError('resultContainer', 'Erro ao criar a tarefa: ' + error);
		});
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
	
	
// Função para Mesclar
function mesclar() {
    // Captura o valor do campo de entrada de nome
    const nomeArquivo = document.getElementById('nomearquivo').value.trim();

    // Gera um nome de arquivo com base na data e hora atual, se o campo estiver vazio
    let nomeArquivoFinal = nomeArquivo || `Digitalizacao_${new Date().toLocaleString().replace(/[/:, ]/g, '-')}`;

    // Adicione a extensão .pdf ao nome, se ainda não estiver presente
    if (!nomeArquivoFinal.endsWith('.pdf')) {
        nomeArquivoFinal += '.pdf';
    }

    // Seleciona a div onde você deseja exibir o status
    const resultSalvamento = document.getElementById('resultSalvamento');

    // Atualiza o conteúdo da div com uma mensagem de status
    resultSalvamento.innerHTML = 'Iniciando a operação de mesclagem...';

    // Faça uma solicitação POST para a rota de mesclagem de PDFs no servidor
    fetch('/merge_pdfs', {
        method: 'POST',
        body: JSON.stringify({ nomeArquivo: nomeArquivoFinal }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            // Se a resposta for bem-sucedida, inicie o download do PDF
            response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = nomeArquivoFinal;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            });
            resultSalvamento.innerHTML = 'Operação concluída com sucesso!';
        } else {
            // Se a resposta não for bem-sucedida, mostre uma mensagem de erro
            response.json().then(data => {
                resultSalvamento.innerHTML = 'Erro ao mesclar PDFs: ' + data.error;
            });
        }
    })
    .catch(error => {
        // Trate erros de rede ou outras falhas
        resultSalvamento.innerHTML = 'Erro ao mesclar PDFs: ' + error;
    });
}


// Função para baixar o último PDF salvo com diretrizes de nome de arquivo
function salvardigitalizacao() {
    // Captura o valor do campo de entrada de nome (caso queira nomear o arquivo de forma personalizada)
    const nomeArquivo = document.getElementById('nomearquivo').value.trim();

    // Gera um nome de arquivo com base na data e hora atual, se o campo estiver vazio
    let nomeArquivoFinal = nomeArquivo || `Digitalizacao_${new Date().toLocaleString().replace(/[/:, ]/g, '-')}`;

    // Adicione a extensão .pdf ao nome, se ainda não estiver presente
    if (!nomeArquivoFinal.endsWith('.pdf')) {
        nomeArquivoFinal += '.pdf';
    }

    // Seleciona a div onde você deseja exibir o status
    const resultSalvamento = document.getElementById('resultSalvamento');

    // Atualiza o conteúdo da div com uma mensagem de status
    resultSalvamento.innerHTML = 'Verificando a existência do PDF...';

    // Construa a URL da rota que obtém o último PDF salvo com as diretrizes de nome de arquivo
    const url = `/get_last_saved_pdf`;

    // Envie uma solicitação AJAX para verificar a existência do PDF
    fetch(url)
        .then(response => {
            if (response.ok) {
                // O PDF existe, crie o link de download e inicie o download
                resultSalvamento.innerHTML = 'Iniciando o download do último PDF salvo...';

                // Construa a URL da rota de download real
                const downloadUrl = `/get_last_saved_pdf?nomeArquivo=${encodeURIComponent(nomeArquivoFinal)}`;

                // Crie um link para iniciar o download
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = nomeArquivoFinal;
                a.style.display = 'none';
                document.body.appendChild(a);

                // Inicie o download
                a.click();

                // Remova o link após o download
                document.body.removeChild(a);

                resultSalvamento.innerHTML = 'Download concluído!';
            } else {
                // O PDF não existe, exiba uma mensagem de erro
                resultSalvamento.innerHTML = 'Nenhuma Digitalização Realizada!';
            }
        })
        .catch(error => {
            console.error(error);
            resultSalvamento.innerHTML = 'Erro ao verificar a existência do PDF.';
        });
}
