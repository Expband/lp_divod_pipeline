import os

from dotenv import load_dotenv
load_dotenv()


class ConfigParser:

    @property
    def output_api_key(self):
        OUTPUT_API_KEY = os.getenv('LP_CRM_OUTPUT_API_KEY')
        return OUTPUT_API_KEY

    @property
    def api_url(self):
        API_URL = os.getenv('API_URL')
        return API_URL
