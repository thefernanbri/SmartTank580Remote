// Função para descobrir o IP da impressora
function discoverPrinterIp() {
    const button = document.getElementById('discoverPrinterButton');
    const statusDiv = document.getElementById('discoveryStatus');
    const ipDiv = document.getElementById('discoveredIp');
    
    // Desabilita o botão e mostra status
    button.disabled = true;
    button.textContent = '🔍 Procurando impressora...';
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div style="color: #2196F3;">⏳ Varrendo a rede em busca da impressora. Isso pode levar alguns minutos...</div>';
    ipDiv.style.display = 'none';
    
    // Faz a requisição para descobrir o IP
    fetch('/discover_printer_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.mensagem || 'Erro ao descobrir impressora');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.sucesso) {
            statusDiv.innerHTML = `<div style="color: #4CAF50; font-weight: bold;">✅ ${data.mensagem}</div>`;
            ipDiv.style.display = 'block';
            ipDiv.innerHTML = `<div style="color: #333; background-color: #e8f5e9; padding: 10px; border-radius: 4px;">
                <strong>IP Encontrado:</strong> ${data.ip}<br>
                <small style="color: #666;">O arquivo .env foi atualizado automaticamente. Reinicie a aplicação para usar o novo IP.</small>
            </div>`;
            
            // Recarrega a página após 3 segundos para aplicar as mudanças
            setTimeout(() => {
                if (confirm('IP descoberto com sucesso! Deseja recarregar a página para aplicar as mudanças?')) {
                    window.location.reload();
                }
            }, 2000);
        } else {
            statusDiv.innerHTML = `<div style="color: #f44336;">❌ ${data.mensagem}</div>`;
        }
    })
    .catch(error => {
        statusDiv.innerHTML = `<div style="color: #f44336;">❌ Erro: ${error.message}</div>`;
    })
    .finally(() => {
        button.disabled = false;
        button.textContent = '🔍 Descobrir IP da Impressora';
    });
}

// Adiciona o event listener quando a página carregar
document.addEventListener("DOMContentLoaded", function() {
    const discoverButton = document.getElementById('discoverPrinterButton');
    if (discoverButton) {
        discoverButton.addEventListener('click', discoverPrinterIp);
    }
});

// Função para testar um IP específico (pode ser útil no futuro)
function testPrinterIp(ip) {
    return fetch('/test_printer_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip: ip })
    })
    .then(response => response.json());
}

