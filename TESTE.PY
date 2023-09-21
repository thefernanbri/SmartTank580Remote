import requests
import time

# Função para criar uma nova digitalização
def create_scan_job():
    # URL de destino para criar a tarefa de digitalização
    scan_url = 'https://192.168.1.92/eSCL/ScanJobs'

    # Cabeçalhos da solicitação
    headers = {
        'Host': '192.168.1.92',
        'Connection': 'close',
        'Content-Type': 'application/xml'
    }

    # Corpo da solicitação
    scan_settings_xml = """
    <scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05" xmlns:scc="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
        <pwg:Version>2.1</pwg:Version>
        <scan:Intent>Document</scan:Intent>
        <pwg:ScanRegions>
            <pwg:ScanRegion>
                <pwg:Height>3507</pwg:Height>
                <pwg:Width>2481</pwg:Width>
                <pwg:XOffset>0</pwg:XOffset>
                <pwg:YOffset>0</pwg:YOffset>
            </pwg:ScanRegion>
        </pwg:ScanRegions>
        <pwg:InputSource>Platen</pwg:InputSource>
        <scan:DocumentFormatExt>application/pdf</scan:DocumentFormatExt>
        <scan:XResolution>300</scan:XResolution>
        <scan:YResolution>300</scan:YResolution>
        <scan:ColorMode>RGB24</scan:ColorMode>
        <scan:CompressionFactor>0</scan:CompressionFactor>
        <scan:Brightness>1000</scan:Brightness>
        <scan:Contrast>1000</scan:Contrast>
    </scan:ScanSettings>
    """

    # Emular a solicitação POST para criar a tarefa de digitalização
    response = requests.post(scan_url, headers=headers, data=scan_settings_xml, verify=False)

    # Verificar a resposta
    if response.status_code == 201:
        print("Tarefa de digitalização criada com sucesso.")
    else:
        print(f"Falha ao criar a tarefa de digitalização. Código de status: {response.status_code}")

# Criar uma nova tarefa de digitalização
create_scan_job()

# Função para verificar o estado da digitalização
def check_scan_status():
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

        # Extrair informações da primeira tarefa
        job_uuid = job_info.split('<pwg:JobUuid>')[1].split('</pwg:JobUuid>')[0]
        job_state = job_info.split('<pwg:JobState>')[1].split('</pwg:JobState>')[0]
        job_JobStateReason = job_info.split('<pwg:JobStateReason>')[1].split('</pwg:JobStateReason>')[0]

        print(f"Estado da digitalização: {job_state}")
        print(f"Motivo: {job_JobStateReason}")
        print(f"UUID: {job_uuid}")
        # Construir a URL do arquivo a ser baixado
        file_url = f'https://192.168.1.92/eSCL/ScanJobs/{job_uuid}/NextDocument'

        # Emular a solicitação GET para baixar o arquivo
        response = requests.get(file_url, headers=headers, verify=False)

        # Verificar a resposta
        if response.status_code == 200:
            # O conteúdo do arquivo estará em response.content
            # Você pode salvá-lo em um arquivo local, se desejar
            with open('scan_result.pdf', 'wb') as file:
                file.write(response.content)
            print("Arquivo de digitalização baixado com sucesso.")
        else:
            print(f"Falha ao baixar o arquivo de digitalização. Código de status: {response.status_code}")
    else:
        print(f"Falha ao verificar o estado da digitalização. Código de status: {response.status_code}")

# Chamar a função para verificar o estado da digitalização uma vez
check_scan_status()