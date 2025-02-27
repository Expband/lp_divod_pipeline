import os

from dotenv import load_dotenv
load_dotenv()


class ConfigParser:

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
