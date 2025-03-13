import pytz
from datetime import datetime
from typing import Literal


class DilovodStatisticsMiddleware:
    def __init__(self):
        self.__execution_statistics: dict = {
            'all_operations_count': 0,
            'success': {
                'registred_docs': 0,
                'unregistred_docs': 0,
                'all': 0
            },
            'unsuccess': {
                'error_not_found': 0,
                'error_multyThread_access': 0,
                'error_other': 0,
                'all': 0
            },
            'execution_start': None,
            'execution_end': None,
            'execution_duration': None
        }
        self.__ukr_tz = pytz.timezone('Europe/Kiev')

    def update_statistics(
        self,
        status: Literal[
            'success',
            'unsuccess'],
        description: Literal[
            'registred_docs',
            'unregistred_docs',
            'error_not_found',
            'error_multyThread_access',
            'error_other'
        ]
        ):
        self.__execution_statistics['all_operations_count'] += 1
        self.__execution_statistics[status]['all'] += 1
        self.__execution_statistics[status][description] += 1

    def capture_time(self, point: Literal['start', 'end']) -> None:
        current_time: datetime = datetime.now(self.__ukr_tz)
        if point == 'start':
            self.__execution_statistics['execution_start'] = current_time
        if point == 'end':
            self.__execution_statistics['execution_end'] = current_time

    def get_statistics(self) -> dict:
        start_time: datetime = self.__execution_statistics['execution_start']
        end_time: datetime = self.__execution_statistics['execution_end']
        duration: datetime = end_time - start_time
        start_time_str: str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time_str: str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        self.__execution_statistics['execution_start'] = start_time_str
        self.__execution_statistics['execution_end'] = end_time_str
        self.__execution_statistics['duration'] = str(duration)
        return self.__execution_statistics
