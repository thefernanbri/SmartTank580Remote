// FUNÇÃO QUE CRIA A TAREFA
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

// FUNÇÃO PARA ENVIAR OS DADOS

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