import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SCANNER_IP = os.getenv('SCANNER_IP', '192.168.100.2')
    SCANNER_BASE_URL = f'https://{SCANNER_IP}'
    PRINTER_IP = os.getenv('PRINTER_IP', '192.168.100.2')
    PRINTER_BASE_URL = f'https://{PRINTER_IP}'
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8080'))
    TEMP_DIR = 'temp'
    SSL_VERIFY = os.getenv('SSL_VERIFY', 'False').lower() == 'true'
