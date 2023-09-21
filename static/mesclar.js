// Função para Mesclar os PDFs
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
    const resultSalvamento = document.getElementById('result');

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
                resultSalvamento.innerHTML = 'Erro ao mesclar PDFs:<br> ' + data.error;
            });
        }
    })
    .catch(error => {
        // Trate erros de rede ou outras falhas
        resultSalvamento.innerHTML = 'Erro ao mesclar PDFs: ' + error;
    });
}