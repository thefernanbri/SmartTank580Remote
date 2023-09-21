from flask import Flask, render_template, request, Response
from printer_routes import printer_blueprint
from flask import jsonify
import requests
from flask import Flask, send_from_directory
import tempfile
from PyPDF2 import PdfMerger
import os
from io import BytesIO
import socket

app = Flask(__name__)

# Rota para servir arquivos estáticos (JavaScript, CSS, imagens, etc.)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota para servir arquivos temporários
@app.route('/pdf/<path:filename>')
def download_file(filename):
    return send_from_directory('pdf', filename, as_attachment=True)


# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')
 
# Rota para verificar o estado do scanner

@app.route('/check_scanner_status')
def check_scanner_status():
    # URL de destino para verificar o estado do scanner
    url = 'https://192.168.1.92/cdm/scan/v1/status'

    # Cabeçalhos da solicitação
    headers = {
        'Host': '192.168.1.92',
        'Connection': 'close'
    }

    try:
        # Emular a solicitação GET
        response = requests.get(url, headers=headers, verify=False)

        # Verificar a resposta
        if response.status_code == 200:
            try:
                scanner_status = response.json()  # Converte a resposta para JSON
            except ValueError:
                return jsonify({"erro": "A resposta não é um JSON válido"})
            else:
                # Verifique se "version" está presente e remova, se existir
                if "version" in scanner_status:
                    del scanner_status["version"]
                
                # Extrair informações do JSON
                scanner_error = scanner_status.get("scannerError", "Desconhecido")
                scanner_state = scanner_status.get("scannerState", "Desconhecido")

                # Retorna as informações formatadas como um objeto JSON
                return jsonify({"scannerError": scanner_error, "scannerState": scanner_state})
        else:
            return jsonify({"erro": f"A solicitação falhou com o código de status {response.status_code}"})
    except requests.exceptions.ConnectionError:
        # Lidar com o erro de conexão (scanner offline)
        return jsonify({"erro": "A impressora está offline"})



# Rota para verificar o estado da digitalização
@app.route('/check_Digitalizacao_status')
def check_Digitalizacao_status():
    # URL de destino para verificar o estado da digitalização
    url = 'https://192.168.1.92/eSCL/ScannerStatus'

    # Cabeçalhos da solicitação
    headers = {
        'Host': '192.168.1.92',
        'Connection': 'close'
    }

    # Emular a solicitação GET
    response = requests.get(url, headers=headers, verify=False)

    # Verificar a resposta
    if response.status_code == 200:
        scan_status = response.text
        job_info_start = scan_status.find('<scan:JobInfo>')
        job_info_end = scan_status.find('</scan:JobInfo>', job_info_start)
        job_info = scan_status[job_info_start:job_info_end]

        # Extrair informações
        job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
        job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]

        # Retorna as informações formatadas como um objeto JSON
        return jsonify({"estado": job_state, "motivo": job_JobStateReason})

    # Se houver um erro na resposta, retorne uma mensagem de erro
    return jsonify({"erro": "Erro ao verificar o estado da impressora"})


# Rota para criar uma tarefa de digitalização
@app.route('/create_scan_job', methods=['POST'])

def create_scan_job():
    # Obtenha o valor de scan_settings_xml da solicitação AJAX
    data = request.get_json()
    
    # URL de destino para criar a tarefa de digitalização
    scan_url = 'https://192.168.1.92/eSCL/ScanJobs'

    # Cabeçalhos da solicitação
    headers = {
        'Host': '192.168.1.92',
        'Connection': 'close',
        'Content-Type': 'application/xml'
    }

    # Corpo da solicitação
    scan_settings_xml = data.get('scan_settings_xml')

    # Emular a solicitação POST para criar a tarefa de digitalização
    response = requests.post(scan_url, headers=headers, data=scan_settings_xml, verify=False)

    # Verificar a resposta
    if response.status_code == 201:
        print("Tarefa de digitalização criada com sucesso.")
        check_scan_status()
    else:
        print(f"Falha ao criar a tarefa de digitalização. Código de status: {response.status_code}")

    return "Tarefa de Digitalização Criada"  # Movido para dentro da função


# Rota para verificar o estado da digitalização
# Contador para nomear os arquivos de digitalização
scan_counter = 0
last_saved_pdf_name = ""
@app.route('/check_scan_status')
def check_scan_status():
    global scan_counter, last_saved_pdf_name  # Usar a variável global para contar os arquivos de digitalização

    # Substitua com as configurações da sua impressora
    url = 'https://192.168.1.92/eSCL/ScannerStatus'

    headers = {
        'Host': '192.168.1.92',
        'Connection': 'close'
    }

    try:
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            scan_status = response.text
            job_info_start = scan_status.find('<scan:JobInfo>')
            job_info_end = scan_status.find('</scan:JobInfo>', job_info_start)
            job_info = scan_status[job_info_start:job_info_end]

            job_uuid = job_info.split('<pwg:JobUuid>')[1].split('</pwg:JobUuid>')[0]
            job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
            job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]

            file_url = f'https://192.168.1.92/eSCL/ScanJobs/{job_uuid}/NextDocument'
            if job_state == "Processing":
                # Emular a solicitação GET para baixar o arquivo
                file_response = requests.get(file_url, headers=headers, verify=False)

                if file_response.status_code == 200:
                    # Salvar o arquivo na pasta "temp" com o nome no formato 'scan0.pdf', 'scan1.pdf', ...
                    file_name = f'temp/scan{scan_counter}.pdf'
                    with open(file_name, 'wb') as file:
                        file.write(file_response.content)
                        
                    # Atualizar o nome do último PDF salvo
                    last_saved_pdf_name = file_name
                    
                    print(f"Arquivo de digitalização '{file_name}' baixado com sucesso.")
                    scan_counter += 1  # Incrementar o contador de digitalizações

                return jsonify({"estado": job_state, "motivo": job_JobStateReason, "url_arquivo": file_url}), 200
            else:
                return jsonify({"estado": job_state, "motivo": job_JobStateReason}), 200
        else:
            return jsonify({"erro": "Erro ao verificar o estado da digitalização"}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Rota para obter o último PDF salvo
@app.route('/get_last_saved_pdf')
def get_last_saved_pdf():

    global last_saved_pdf_name
    try:
        if last_saved_pdf_name:
            # Capturar o nome de arquivo personalizado, se fornecido como um parâmetro na URL
            nome_arquivo_personalizado = request.args.get('nomeArquivo')

            # Definir o nome do arquivo com base no nome personalizado ou padrão
            nome_arquivo_final = nome_arquivo_personalizado or 'Arquivo.pdf'

            with open(last_saved_pdf_name, 'rb') as file:
                pdf_data = file.read()

            return Response(pdf_data, content_type='application/pdf', headers={'Content-Disposition': f'attachment; filename={nome_arquivo_final}'})
            
        else:
            return jsonify({"error": "Nenhum PDF foi salvo ainda."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    try:
        # Diretório onde os PDFs foram salvos
        pdf_directory = 'temp/'

        # Obtenha a lista de arquivos PDF no diretório
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]

        # Verifique se há pelo menos 2 arquivos para mesclar
        if len(pdf_files) < 2:
            return jsonify({"error": "É necessário pelo menos dois arquivos para mesclar."}), 400

        # Crie um objeto PdfMerger para mesclar os PDFs
        pdf_merger = PdfMerger()

        # Adicione cada PDF à mesclagem
        for pdf_file in pdf_files:
            with open(pdf_directory + pdf_file, 'rb') as file:
                pdf_merger.append(file)

        # Nome do arquivo PDF de saída
        output_pdf_name = 'merged.pdf'

        # Crie um objeto BytesIO para armazenar o PDF mesclado na memória
        output_buffer = BytesIO()
        pdf_merger.write(output_buffer)
        output_buffer.seek(0)

        # Limpeza dos arquivos temporários
        for pdf_file in pdf_files:
            os.remove(pdf_directory + pdf_file)

        # Retorne o PDF como resposta HTTP com o nome de arquivo desejado
        return Response(output_buffer.read(), content_type='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename={output_pdf_name}'})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Função para verificar a existência de arquivos temporários
def verificar_arquivos_temp():
    pasta_temp = 'temp'  # Substitua pelo caminho real da sua pasta temp

    if os.path.exists(pasta_temp) and os.path.isdir(pasta_temp):
        arquivos_temp = os.listdir(pasta_temp)
        return len(arquivos_temp) > 0
    else:
        return False

# Função para limpar os arquivos temporários
def limpar_arquivos_temp():
    pasta_temp = 'temp'  # Substitua pelo caminho real da sua pasta temp

    if os.path.exists(pasta_temp) and os.path.isdir(pasta_temp):
        arquivos_temp = os.listdir(pasta_temp)
        for arquivo in arquivos_temp:
            caminho_arquivo = os.path.join(pasta_temp, arquivo)
            try:
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
            except Exception as e:
                # Trate erros de remoção de arquivo aqui, se necessário
                print(f"Erro ao remover o arquivo {caminho_arquivo}: {str(e)}")
    
    # Opcional: Retorne uma mensagem de sucesso ou um status para a sua aplicação
    return 'Digitalizações Temporárias Limpas!'


# Rota para verificar a existência de arquivos temporários
@app.route('/verificar_arquivos_temp', methods=['GET'])
def verificar_arquivos_temp_route():
    arquivos_existem = verificar_arquivos_temp()
    return jsonify({'arquivos_existem': arquivos_existem})

# Rota para limpar os arquivos temporários
@app.route('/limpar_arquivos_temp', methods=['GET'])
def limpar_arquivos_temp_route():
    mensagem = limpar_arquivos_temp()
    return mensagem


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
   