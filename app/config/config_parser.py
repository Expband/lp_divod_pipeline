import os
from pathlib import Path
from dotenv import load_dotenv


class ConfigParser:

    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR/'config'/'.env')

    @property
    def lp_output_api_key(self):
        OUTPUT_API_KEY = os.getenv('LP_CRM_OUTPUT_API_KEY')
        return OUTPUT_API_KEY

    @property
    def lp_api_url(self):
        LP_API_URL = os.getenv('LP_API_URL')
        return LP_API_URL

    @property
    def dilovod_api_url(self):
        DILOVOD_API_URL = os.getenv('DILOVOD_API_URL')
        return DILOVOD_API_URL

    @property
    def dilovod_api_key(self):
        DILOVOD_API_KEY = os.getenv('DILOVOD_API_KEY')
        return DILOVOD_API_KEY

    @property
    def novapost_api_key(self):
        NOVAPOST_API_KEY = os.getenv('NOVAPOST_API_KEY')
        return NOVAPOST_API_KEY

    @property
    def novapost_url(self):
        NOVAPOST_URL = os.getenv('NOVAPOST_URL')
        return NOVAPOST_URL

    @property
    def ukrpost_url(self):
        UKRPOST_URL = os.getenv('UKRPOST_URL')
        return UKRPOST_URL

    @property
    def ukrpost_api_key(self):
        UKRPOST_API_KEY = os.getenv('UKRPOST_API_KEY')
        return UKRPOST_API_KEY
