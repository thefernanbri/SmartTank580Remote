from flask import Blueprint, jsonify
import requests

printer_blueprint = Blueprint('printer', __name__)

@printer_blueprint.route('/check_printer_status')
def check_printer_status():
    # URL de destino para verificar o estado da digitalização
    url = 'https://192.168.1.92/eSCL/ScannerStatus'

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
            scan_status = response.text
            job_info_start = scan_status.find('<scan:JobInfo>')
            job_info_end = scan_status.find('</scan:JobInfo>', job_info_start)
            job_info = scan_status[job_info_start:job_info_end]

            # Extrair informações
            job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
            job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]

            # Retorna as informações formatadas como um objeto JSON
            return jsonify({"estado": job_state, "motivo": job_JobStateReason})

        # Se o status da resposta não for 200, retorne uma mensagem de erro
        return jsonify({"erro": "Erro ao verificar o estado da impressora"}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
