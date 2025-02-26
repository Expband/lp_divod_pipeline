import requests
from typing import Optional, Union

from middlewares.logger.loguru_logger import LoguruLogger


class HTTPClient:
    def __init__(self, headers: Optional[dict] = None):
        self.__session = requests.Session()
        self.__logger = LoguruLogger().logger
        if headers:
            self.__session.headers.update(headers)

    async def _handle_request(self, request_func, url: str, **kwargs):
        """Загальний метод для виконання запиту та обробки помилок."""
        try:
            response = request_func(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            self.__logger.error(f'Timeout exception occurred for {url}')
        except requests.exceptions.ConnectionError:
            self.__logger.error(f'Connection error occurred for {url}')
        except requests.exceptions.HTTPError as e:
            self.__logger.error(
                f'HTTP error occurred for {url}: {e.response.status_code} - {e.response.text}')
        except requests.exceptions.RequestException as e:
            self.__logger.error(
                f'Unexpected request error occurred for {url}: {str(e)}')

    async def get(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None):
        return await self._handle_request(
            self.__session.get,
            url,
            headers=headers,
            params=params)

    async def post(self, url: str, payload: Union[str, dict], headers: Optional[dict] = None, parse_mode: str = 'json'):
        if parse_mode == 'json':
            return await self._handle_request(
                self.__session.post,
                url,
                json=payload,
                headers=headers)
        elif parse_mode == 'xml':
            return await self._handle_request(
                self.__session.post,
                url,
                data=payload,
                headers=headers)
        else:
            self.__logger.error(f'Invalid parse mode: {parse_mode}')
            return None
