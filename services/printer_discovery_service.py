import socket
import ipaddress
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple
import logging
import urllib3

# Desabilita avisos SSL para requisições HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrinterDiscoveryService:
    """Serviço para descobrir automaticamente o IP da impressora na rede"""
    
    # Endpoints conhecidos da impressora para testar
    TEST_ENDPOINTS = [
        '/eSCL/ScannerStatus',
        '/cdm/scan/v1/status'
    ]
    
    def __init__(self, timeout: float = 2.0):
        """
        Inicializa o serviço de descoberta
        
        Args:
            timeout: Tempo limite para cada tentativa de conexão (segundos)
        """
        self.timeout = timeout
        self.found_ips = []
        
    def get_local_network_range(self) -> Tuple[str, str]:
        """
        Descobre automaticamente a faixa de IPs da rede local
        
        Returns:
            Tupla (network_base, netmask) - Ex: ('192.168.1.0', '192.168.1.255')
        """
        try:
            # Conecta a um servidor externo para descobrir o IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Não precisa realmente conectar
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            finally:
                s.close()
            
            # Determina a rede baseada no IP local
            # Assumindo máscara de sub-rede comum /24 (255.255.255.0)
            ip_parts = local_ip.split('.')
            network_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
            network_end = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.255"
            
            logger.info(f"Rede local detectada: {network_base} - {network_end}")
            return network_base, network_end
        except Exception as e:
            logger.error(f"Erro ao descobrir rede local: {e}")
            # Fallback para ranges comuns
            return "192.168.1.1", "192.168.1.255"
    
    def test_printer_endpoint(self, ip: str, endpoint: str) -> bool:
        """
        Testa se um IP responde a um endpoint específico da impressora
        
        Args:
            ip: IP para testar
            endpoint: Endpoint para testar (ex: '/eSCL/ScannerStatus')
            
        Returns:
            True se o endpoint respondeu com sucesso, False caso contrário
        """
        url = f'https://{ip}{endpoint}'
        headers = {
            'Host': ip,
            'Connection': 'close'
        }
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                verify=False, 
                timeout=self.timeout
            )
            
            # Verifica se a resposta é válida
            if response.status_code == 200:
                # Verifica se a resposta tem conteúdo característico da impressora
                if endpoint == '/eSCL/ScannerStatus':
                    # Verifica se contém tags XML do eSCL
                    if '<scan:JobInfo>' in response.text or '<pwg:JobState>' in response.text:
                        return True
                elif endpoint == '/cdm/scan/v1/status':
                    # Verifica se é JSON válido com campos do scanner
                    try:
                        data = response.json()
                        if 'scannerState' in data or 'scannerError' in data:
                            return True
                    except:
                        pass
                return False
            return False
            
        except (requests.exceptions.RequestException, socket.error, Exception) as e:
            return False
    
    def test_ip(self, ip: str) -> Optional[str]:
        """
        Testa um IP para ver se é a impressora
        
        Args:
            ip: IP para testar
            
        Returns:
            IP se encontrado, None caso contrário
        """
        for endpoint in self.TEST_ENDPOINTS:
            if self.test_printer_endpoint(ip, endpoint):
                logger.info(f"Impressora encontrada em {ip} (endpoint: {endpoint})")
                return ip
        return None
    
    def scan_network_range(self, start_ip: str, end_ip: str, max_workers: int = 50) -> List[str]:
        """
        Varre uma faixa de IPs procurando pela impressora
        
        Args:
            start_ip: IP inicial da faixa (ex: '192.168.1.1')
            end_ip: IP final da faixa (ex: '192.168.1.255')
            max_workers: Número máximo de threads paralelas
            
        Returns:
            Lista de IPs encontrados que respondem como impressora
        """
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
        except ValueError as e:
            logger.error(f"IPs inválidos: {e}")
            return []
        
        found_ips = []
        
        # Gera lista de IPs do range
        all_ips = []
        current = int(start)
        end_int = int(end)
        
        while current <= end_int:
            all_ips.append(str(ipaddress.IPv4Address(current)))
            current += 1
        
        logger.info(f"Varrendo {len(all_ips)} IPs na faixa {start_ip} - {end_ip}...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete todas as tarefas
            future_to_ip = {executor.submit(self.test_ip, ip): ip for ip in all_ips}
            
            # Processa resultados conforme completam
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    if result:
                        found_ips.append(result)
                        # Para na primeira impressora encontrada para economizar tempo
                        logger.info(f"Impressora encontrada! Interrompendo busca...")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao testar {ip}: {e}")
        
        return found_ips
    
    def discover_printer_ip(self, custom_range: Optional[Tuple[str, str]] = None) -> Optional[str]:
        """
        Descobre o IP da impressora na rede
        
        Args:
            custom_range: Tupla opcional (start_ip, end_ip) para definir range personalizado
            
        Returns:
            IP da impressora encontrado, ou None se não encontrado
        """
        if custom_range:
            start_ip, end_ip = custom_range
        else:
            start_ip, end_ip = self.get_local_network_range()
        
        found_ips = self.scan_network_range(start_ip, end_ip)
        
        if found_ips:
            # Retorna o primeiro IP encontrado
            return found_ips[0]
        else:
            logger.warning("Nenhuma impressora encontrada na rede")
            return None
    
    def discover_multiple_ranges(self, ranges: List[Tuple[str, str]]) -> Optional[str]:
        """
        Varre múltiplas faixas de IPs procurando pela impressora
        Útil quando a rede pode estar em sub-redes diferentes
        
        Args:
            ranges: Lista de tuplas (start_ip, end_ip)
            
        Returns:
            IP da impressora encontrado, ou None se não encontrado
        """
        for start_ip, end_ip in ranges:
            logger.info(f"Varrendo faixa {start_ip} - {end_ip}...")
            found_ips = self.scan_network_range(start_ip, end_ip)
            if found_ips:
                return found_ips[0]
        
        return None

