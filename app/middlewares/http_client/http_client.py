import requests
from requests import Response
from typing import Optional, Union, Literal

from app.middlewares.http_client.request_error import RequestError
from app.middlewares.logger.loguru_logger import LoguruLogger


class HTTPClient:
    def __init__(self, headers: Optional[dict] = None):
        self.__session = requests.Session()
        self.__logger = LoguruLogger().logger
        if headers:
            self.__session.headers.update(headers)

    async def _handle_request(
            self,
            request_func,
            url: str, **kwargs) -> Response:
        """Загальний метод для виконання запиту та обробки помилок."""
        try:
            response: Response = request_func(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            self.__logger.error(f'Timeout exception occurred for {url}')
            return None
        except requests.exceptions.HTTPError as e:
            error_message = (
                f'HTTP error occurred for {url}:'
                f'{e.response.status_code} - {e.response.text}')
            self.__logger.error(error_message)
            raise RequestError(error_message, e.response.status_code)
        except requests.exceptions.RequestException as e:
            self.__logger.error(
                f'Unexpected request error occurred for {url}: {str(e)}')
            return None

    async def get(
            self,
            url: str,
            headers: Optional[dict] = None,
            params: Optional[dict] = None) -> Response:
        return await self._handle_request(
            self.__session.get,
            url,
            headers=headers,
            params=params)

    async def post(
            self,
            url: str,
            payload: Union[str, dict],
            parse_mode: Literal[
                'json',
                'xml'],
            headers: Optional[dict] = None,) -> Response:
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
