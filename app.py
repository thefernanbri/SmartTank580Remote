from flask import Flask, render_template, request, Response, jsonify, send_from_directory
from printer_routes import printer_blueprint
import requests
import tempfile
from PyPDF2 import PdfMerger
import os
from io import BytesIO
import socket
from services.printer_discovery_service import PrinterDiscoveryService
import re
import threading
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis do arquivo .env para o sistema
load_dotenv()

app = Flask(__name__)

# Variável global para armazenar o IP da impressora descoberto
discovered_printer_ip = None
# Variáveis globais de controle de estado (Cuidado: em produção com múltiplos usuários isso pode gerar conflito)
document_type = "pdf" 
scan_counter = 0
last_saved_pdf_name = ""


def get_target_ip():
    """
    Retorna o IP da impressora a ser usado.
    Prioridade: 
    1. IP descoberto na sessão atual (memória)
    2. IP salvo no arquivo .env
    3. IP padrão (fallback)
    """
    global discovered_printer_ip
    
    if discovered_printer_ip:
        return discovered_printer_ip
    
    # Tenta pegar do .env, se não existir usa o fixo como segurança
    return os.getenv('PRINTER_IP', '192.168.100.8')


# Rota para servir arquivos estáticos (JavaScript, CSS, imagens, etc.)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota para servir arquivos temporários
@app.route('/pdf/<path:filename>')
def download_file(filename):
    return send_from_directory('pdf', filename, as_attachment=True)

# Rota para servir arquivos da pasta temp (para preview)
@app.route('/temp/<path:filename>')
def serve_temp_file(filename):
    return send_from_directory('temp', filename)

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')
 
# Rota para verificar o estado do scanner

@app.route('/check_scanner_status')
def check_scanner_status():
    ip = get_target_ip()
    # URL de destino para verificar o estado do scanner
    url = f'https://{ip}/cdm/scan/v1/status'

    # Cabeçalhos da solicitação
    headers = {
        'Host': ip,
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
    global scan_counter, last_saved_pdf_name, document_type
    ip = get_target_ip()
    # URL de destino para verificar o estado da digitalização
    url = f'https://{ip}/eSCL/ScannerStatus'

    # Cabeçalhos da solicitação
    headers = {
        'Host': ip,
        'Connection': 'close'
    }

    # Emular a solicitação GET
    try:
        response = requests.get(url, headers=headers, verify=False)

        # Verificar a resposta
        if response.status_code == 200:
            scan_status = response.text
            job_info_start = scan_status.find('<scan:JobInfo>')
            
            if job_info_start != -1:
                job_info_end = scan_status.find('</scan:JobInfo>', job_info_start)
                job_info = scan_status[job_info_start:job_info_end]

                # Extrair informações (com tratamento básico de erro se a tag não existir)
                try:
                    job_uuid = job_info.split('<pwg:JobUuid>')[1].split('</pwg:JobUuid>')[0]
                    job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
                    job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]
                    
                    # Tentar baixar o arquivo se o estado for Processing, Completed ou mesmo Aborted
                    # (o arquivo pode estar disponível mesmo com estado Aborted)
                    if job_state in ["Processing", "Completed", "Aborted"]:
                        file_url = f'https://{ip}/eSCL/ScanJobs/{job_uuid}/NextDocument'
                        try:
                            file_response = requests.get(file_url, headers=headers, verify=False, timeout=5)
                            
                            if file_response.status_code == 200:
                                # Verifica se diretório temp existe
                                if not os.path.exists('temp'):
                                    os.makedirs('temp')

                                # Salvar o arquivo na pasta "temp"
                                file_name = f'temp/scan{scan_counter}.jpeg' if document_type == "photo" else f'temp/scan{scan_counter}.pdf'
                                
                                with open(file_name, 'wb') as file:
                                    file.write(file_response.content)
                                
                                # Atualizar o nome do último PDF salvo
                                last_saved_pdf_name = file_name
                                
                                print(f"Arquivo de digitalização '{file_name}' baixado com sucesso.")
                                
                                # Se o checkbox "Salvar no Computador" estiver marcado, salvar permanentemente
                                mensagem_salvamento = ""
                                if salvar_no_computador:
                                    try:
                                        # Verifica se diretório pdf existe
                                        if not os.path.exists('pdf'):
                                            os.makedirs('pdf')
                                        
                                        # Gerar nome do arquivo permanente
                                        if nome_arquivo_permanente:
                                            nome_permanente = nome_arquivo_permanente.strip()
                                            if not nome_permanente.endswith(('.pdf', '.jpeg', '.jpg')):
                                                nome_permanente += '.pdf' if document_type != "photo" else '.jpeg'
                                        else:
                                            # Gerar nome com data e hora
                                            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                            extensao = '.pdf' if document_type != "photo" else '.jpeg'
                                            nome_permanente = f'Digitalizacao_{timestamp}{extensao}'
                                        
                                        # Copiar arquivo para pasta pdf
                                        file_path_permanente = f'pdf/{nome_permanente}'
                                        with open(file_path_permanente, 'wb') as file_permanente:
                                            file_permanente.write(file_response.content)
                                        
                                        mensagem_salvamento = f" Arquivo salvo permanentemente como '{nome_permanente}'."
                                        print(f"Arquivo salvo permanentemente: '{file_path_permanente}'")
                                    except Exception as e:
                                        print(f"Erro ao salvar arquivo permanentemente: {e}")
                                        mensagem_salvamento = " Erro ao salvar permanentemente."
                                
                                scan_counter += 1  # Incrementar o contador de digitalizações
                                
                                # Se o arquivo foi baixado com sucesso, retornar estado como "Concluído"
                                nome_arquivo_simples = os.path.basename(file_name)
                                return jsonify({
                                    "estado": "Concluído", 
                                    "motivo": "Arquivo baixado com sucesso" + mensagem_salvamento,
                                    "arquivo_baixado": True,
                                    "nome_arquivo": nome_arquivo_simples,
                                    "url_preview": f"/temp/{nome_arquivo_simples}",
                                    "tipo": "image" if document_type == "photo" else "pdf"
                                })
                        except Exception as download_error:
                            # Se não conseguir baixar, apenas logar e continuar
                            print(f"Tentativa de download falhou: {download_error}")
                    
                    return jsonify({"estado": job_state, "motivo": job_JobStateReason})
                except IndexError:
                    return jsonify({"estado": "Desconhecido", "motivo": "Erro ao processar XML"})
            else:
                return jsonify({"estado": "Ocioso", "motivo": "Nenhuma tarefa ativa"})

        return jsonify({"erro": "Erro ao verificar o estado da impressora"})
    except Exception as e:
        return jsonify({"erro": str(e)})


# Rota para criar uma tarefa de digitalização
@app.route('/create_scan_job', methods=['POST'])

def create_scan_job():
    global document_type 

    # Obtenha o valor de scan_settings_xml da solicitação AJAX
    data = request.get_json()
    document_type = request.args.get('document_type')
    nome_arquivo = request.args.get('nomearquivo')
    salvar_pc = request.args.get('salvar_pc', 'false').lower() == 'true'
    
    # Armazenar o estado do checkbox e nome do arquivo em variáveis globais para uso posterior
    global salvar_no_computador, nome_arquivo_permanente
    salvar_no_computador = salvar_pc
    nome_arquivo_permanente = nome_arquivo
    
    # CORREÇÃO: Definição do IP antes do uso
    ip = get_target_ip()
    
    # URL de destino para criar a tarefa de digitalização
    scan_url = f'https://{ip}/eSCL/ScanJobs'

    # Cabeçalhos da solicitação
    headers = {
        'Host': ip,
        'Connection': 'close',
        'Content-Type': 'application/xml'
    }

    # Corpo da solicitação
    scan_settings_xml = data.get('scan_settings_xml')

    try:
        # Emular a solicitação POST para criar a tarefa de digitalização
        response = requests.post(scan_url, headers=headers, data=scan_settings_xml, verify=False)

        # Verificar a resposta
        if response.status_code == 201:
            print("Tarefa de digitalização criada com sucesso.")
            return jsonify({"sucesso": True, "mensagem": "Tarefa de Digitalização Criada"}), 200
        else:
            print(f"Falha ao criar a tarefa de digitalização. Código de status: {response.status_code}")
            # Retornar erro com o código de status do scanner
            mensagem_erro = f"Falha ao criar a tarefa de digitalização. Código de status: {response.status_code}"
            if response.status_code == 503:
                mensagem_erro += " - O scanner está temporariamente indisponível. Verifique se há outra tarefa em andamento ou se o scanner está ocupado."
            return jsonify({"erro": mensagem_erro, "status_code": response.status_code}), response.status_code
    except requests.exceptions.ConnectionError as e:
        print(f"Erro de conexão: {e}")
        return jsonify({"erro": "Erro de conexão com o scanner. Verifique se o scanner está ligado e conectado à rede."}), 503
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"erro": str(e)}), 500


# Rota para verificar o estado da digitalização e baixar arquivo
@app.route('/check_scan_status')
def check_scan_status():
    global scan_counter, last_saved_pdf_name, document_type 

    ip = get_target_ip()
    url = f'https://{ip}/eSCL/ScannerStatus'

    # CORREÇÃO: Usar a variável IP aqui também
    headers = {
        'Host': ip,
        'Connection': 'close'
    }

    try:
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            scan_status = response.text
            job_info_start = scan_status.find('<scan:JobInfo>')
            
            if job_info_start == -1:
                 return jsonify({"estado": "Ocioso", "motivo": "Nenhum trabalho encontrado"}), 200

            job_info_end = scan_status.find('</scan:JobInfo>', job_info_start)
            job_info = scan_status[job_info_start:job_info_end]

            job_uuid = job_info.split('<pwg:JobUuid>')[1].split('</pwg:JobUuid>')[0]
            job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
            job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]

            file_url = f'https://{ip}/eSCL/ScanJobs/{job_uuid}/NextDocument'
            
            # Tentar baixar o arquivo se o estado for Processing, Completed ou mesmo Aborted
            # (o arquivo pode estar disponível mesmo com estado Aborted)
            if job_state in ["Processing", "Completed", "Aborted"]:
                # Emular a solicitação GET para baixar o arquivo
                try:
                    file_response = requests.get(file_url, headers=headers, verify=False, timeout=5)

                    if file_response.status_code == 200:
                        # Verifica se diretório temp existe
                        if not os.path.exists('temp'):
                            os.makedirs('temp')

                        # Salvar o arquivo na pasta "temp"
                        file_name = f'temp/scan{scan_counter}.jpeg' if document_type == "photo" else f'temp/scan{scan_counter}.pdf'
                        
                        with open(file_name, 'wb') as file:
                            file.write(file_response.content)
                        
                        # Atualizar o nome do último PDF salvo
                        last_saved_pdf_name = file_name
                        
                        print(f"Arquivo de digitalização '{file_name}' baixado com sucesso.")
                        
                        # Se o checkbox "Salvar no Computador" estiver marcado, salvar permanentemente
                        mensagem_salvamento = ""
                        if salvar_no_computador:
                            try:
                                # Verifica se diretório pdf existe
                                if not os.path.exists('pdf'):
                                    os.makedirs('pdf')
                                
                                # Gerar nome do arquivo permanente
                                from datetime import datetime
                                if nome_arquivo_permanente:
                                    nome_permanente = nome_arquivo_permanente.strip()
                                    if not nome_permanente.endswith(('.pdf', '.jpeg', '.jpg')):
                                        nome_permanente += '.pdf' if document_type != "photo" else '.jpeg'
                                else:
                                    # Gerar nome com data e hora
                                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                    extensao = '.pdf' if document_type != "photo" else '.jpeg'
                                    nome_permanente = f'Digitalizacao_{timestamp}{extensao}'
                                
                                # Copiar arquivo para pasta pdf
                                file_path_permanente = f'pdf/{nome_permanente}'
                                with open(file_path_permanente, 'wb') as file_permanente:
                                    file_permanente.write(file_response.content)
                                
                                mensagem_salvamento = f" Arquivo salvo permanentemente como '{nome_permanente}'."
                                print(f"Arquivo salvo permanentemente: '{file_path_permanente}'")
                            except Exception as e:
                                print(f"Erro ao salvar arquivo permanentemente: {e}")
                                mensagem_salvamento = " Erro ao salvar permanentemente."
                        
                        scan_counter += 1  # Incrementar o contador de digitalizações
                        
                        # Se o arquivo foi baixado com sucesso, retornar estado como "Concluído"
                        nome_arquivo_simples = os.path.basename(file_name)
                        return jsonify({
                            "estado": "Concluído", 
                            "motivo": "Arquivo baixado com sucesso" + mensagem_salvamento,
                            "url_arquivo": file_url,
                            "arquivo_baixado": True,
                            "nome_arquivo": nome_arquivo_simples,
                            "url_preview": f"/temp/{nome_arquivo_simples}",
                            "tipo": "image" if document_type == "photo" else "pdf"
                        }), 200
                except Exception as download_error:
                    # Se não conseguir baixar, apenas logar e continuar
                    print(f"Tentativa de download falhou: {download_error}")

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
        if last_saved_pdf_name and os.path.exists(last_saved_pdf_name):
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
        
        if not os.path.exists(pdf_directory):
             return jsonify({"error": "Diretório temporário vazio."}), 400

        # Obtenha a lista de arquivos PDF no diretório
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
        pdf_files.sort() # Garante uma ordem (opcional, mas recomendada)

        # Verifique se há pelo menos 2 arquivos para mesclar
        if len(pdf_files) < 2:
            return jsonify({"error": "É necessário pelo menos dois arquivos para mesclar."}), 400

        # Crie um objeto PdfMerger para mesclar os PDFs
        pdf_merger = PdfMerger()

        # Adicione cada PDF à mesclagem
        for pdf_file in pdf_files:
            file_path = os.path.join(pdf_directory, pdf_file)
            with open(file_path, 'rb') as file:
                pdf_merger.append(file)

        # Nome do arquivo PDF de saída
        output_pdf_name = 'merged.pdf'

        # Crie um objeto BytesIO para armazenar o PDF mesclado na memória
        output_buffer = BytesIO()
        pdf_merger.write(output_buffer)
        output_buffer.seek(0)

        # Retorne o PDF como resposta HTTP com o nome de arquivo desejado
        return Response(output_buffer.read(), content_type='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename={output_pdf_name}'})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Função para verificar a existência de arquivos temporários
def verificar_arquivos_temp():
    pasta_temp = 'temp'  # Substitua pelo caminho real da sua pasta temp

    if os.path.exists(pasta_temp) and os.path.isdir(pasta_temp):
        arquivos_temp = [f for f in os.listdir(pasta_temp) if f != '.gitignore'] # Ignora arquivos de sistema
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
                print(f"Erro ao remover o arquivo {caminho_arquivo}: {str(e)}")
    
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

# Rota para listar arquivos da pasta temp (para preview)
@app.route('/listar_arquivos_temp', methods=['GET'])
def listar_arquivos_temp():
    try:
        pasta_temp = 'temp'
        if not os.path.exists(pasta_temp):
            return jsonify({"arquivos": []})
        
        arquivos = []
        for arquivo in os.listdir(pasta_temp):
            if arquivo != '.gitignore' and os.path.isfile(os.path.join(pasta_temp, arquivo)):
                arquivo_path = os.path.join(pasta_temp, arquivo)
                arquivos.append({
                    "nome": arquivo,
                    "url": f"/temp/{arquivo}",
                    "tipo": "image" if arquivo.lower().endswith(('.jpeg', '.jpg', '.png')) else "pdf"
                })
        
        # Ordenar por nome para manter ordem consistente
        arquivos.sort(key=lambda x: x["nome"])
        return jsonify({"arquivos": arquivos})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ==================== FUNCIONALIDADE DE DESCOBERTA DE IP ====================

def update_env_file(printer_ip: str):
    """
    Atualiza o arquivo .env com o IP da impressora encontrado
    """
    env_file = '.env'
    env_example_file = '.env.example'
    
    # Tenta ler o arquivo .env, se não existir, usa o .env.example como base
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif os.path.exists(env_example_file):
        with open(env_example_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = 'SCANNER_IP=\nPRINTER_IP=\n'
    
    # Atualiza ou adiciona SCANNER_IP e PRINTER_IP
    if re.search(r'^SCANNER_IP\s*=', content, re.MULTILINE):
        content = re.sub(r'^SCANNER_IP\s*=.*$', f'SCANNER_IP={printer_ip}', content, flags=re.MULTILINE)
    else:
        content += f'\nSCANNER_IP={printer_ip}'
    
    if re.search(r'^PRINTER_IP\s*=', content, re.MULTILINE):
        content = re.sub(r'^PRINTER_IP\s*=.*$', f'PRINTER_IP={printer_ip}', content, flags=re.MULTILINE)
    else:
        content += f'\nPRINTER_IP={printer_ip}'
    
    content = re.sub(r'\n\n+', '\n\n', content)
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')


@app.route('/discover_printer_ip', methods=['POST'])
def discover_printer_ip():
    """
    Rota para descobrir automaticamente o IP da impressora na rede
    """
    global discovered_printer_ip
    
    try:
        data = request.get_json() or {}
        custom_ranges = data.get('ranges', [])
        
        discovery_service = PrinterDiscoveryService(timeout=2.0)
        
        if custom_ranges:
            ip = discovery_service.discover_multiple_ranges(custom_ranges)
        else:
            ranges = [
                ('192.168.1.1', '192.168.1.255'),
                ('192.168.100.1', '192.168.100.255'),
                ('192.168.0.1', '192.168.0.255'),
                ('10.0.0.1', '10.0.0.255'),
            ]
            
            try:
                local_start, local_end = discovery_service.get_local_network_range()
                ranges.insert(0, (local_start.replace('.1', '.1'), local_end))
            except:
                pass
            
            ip = discovery_service.discover_multiple_ranges(ranges)
        
        if ip:
            discovered_printer_ip = ip
            try:
                update_env_file(ip)
                return jsonify({
                    "sucesso": True,
                    "ip": ip,
                    "mensagem": f"Impressora encontrada em {ip} e configuração atualizada!"
                })
            except Exception as e:
                return jsonify({
                    "sucesso": True,
                    "ip": ip,
                    "mensagem": f"Impressora encontrada em {ip}, mas houve erro ao atualizar .env: {str(e)}"
                })
        else:
            return jsonify({
                "sucesso": False,
                "mensagem": "Nenhuma impressora encontrada na rede. Verifique se a impressora está ligada e conectada à rede."
            }), 404
            
    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro ao descobrir impressora: {str(e)}"
        }), 500


@app.route('/discover_printer_ip_status', methods=['GET'])
def discover_printer_ip_status():
    global discovered_printer_ip
    return jsonify({
        "ip_descoberto": discovered_printer_ip,
        "status": "concluido" if discovered_printer_ip else "nao_encontrado"
    })


@app.route('/test_printer_ip', methods=['POST'])
def test_printer_ip():
    try:
        data = request.get_json()
        ip = data.get('ip')
        
        if not ip:
            return jsonify({
                "sucesso": False,
                "mensagem": "IP não fornecido"
            }), 400
        
        discovery_service = PrinterDiscoveryService(timeout=2.0)
        result = discovery_service.test_ip(ip)
        
        if result:
            return jsonify({
                "sucesso": True,
                "ip": ip,
                "mensagem": f"Impressora confirmada em {ip}!"
            })
        else:
            return jsonify({
                "sucesso": False,
                "mensagem": f"O IP {ip} não responde como impressora"
            }), 404
            
    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro ao testar IP: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)