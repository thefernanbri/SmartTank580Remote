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
    const resultSalvamento = document.getElementById('result');

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