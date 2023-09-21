import requests
import json

# Desabilite a verificação do certificado SSL
requests.packages.urllib3.disable_warnings()

url = 'https://192.168.1.92/cdm/scan/v1/status'

# Faça a solicitação GET sem verificar o SSL
response = requests.get(url, verify=False)

# Verifique o código de status da resposta
if response.status_code == 200:
    try:
        scanner_status = response.json()  # Converte a resposta para JSON
    except ValueError:
        print("Erro: A resposta não é um JSON válido")
    else:
        # Verifique se "version" está presente e remova, se existir
        if "version" in scanner_status:
            del scanner_status["version"]
        
        # Extrair informações do JSON
        scanner_error = scanner_status.get("scannerError", "Desconhecido")
        scanner_state = scanner_status.get("scannerState", "Desconhecido")

        # Imprimir os valores no console do Flask
        print("Scanner Error:", scanner_error)
        print("Scanner State:", scanner_state)
else:
    print(f"A solicitação falhou com o código de status {response.status_code}")
