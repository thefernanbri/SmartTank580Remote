import requests
import logging
from config import Config

class ScannerService:
    def __init__(self):
        self.base_url = Config.SCANNER_BASE_URL
        self.verify_ssl = Config.SSL_VERIFY
        self.timeout = Config.REQUEST_TIMEOUT
        self.logger = logging.getLogger(__name__)

    def check_scanner_status(self):
