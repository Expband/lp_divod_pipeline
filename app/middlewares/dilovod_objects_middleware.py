from app.middlewares.logger.loguru_logger import LoguruLogger


class DilovodObjectsMiddleware:
    def __init__(self):
        self.__logger = LoguruLogger().logger

    async def get_object_from_dict_by_id(
            self,
            target_id: str,
            dilovod_objects: list[dict]) -> dict:
        for object in dilovod_objects:
            object_header: dict = object.get('header')
            if not object_header:
                self.__logger.error(f'Unable to get header section in {object} dilovod object')
                continue
            id_object: dict = object_header.get('id')
            if not id_object:
                self.__logger.error(f'Unable to get id section from header section in {id_object} dilovod object')
                continue
            id: str = id_object.get('id')
            if not id:
                self.__logger.error(f'Unable to get id in {object} dilovod object')
                continue
            if id == target_id:
                return object
        return None
