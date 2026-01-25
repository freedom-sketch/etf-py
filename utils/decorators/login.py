from py3xui import AsyncApi
from LoggerFactory import logger_factory

logger = logger_factory.create_logger(name='utils.decorators.Login')

def login(method):
    async def wrapper(*args, **kwargs):
        panel_url = kwargs.get('panel_url')
        login = kwargs.get('login')
        password = kwargs.get('password')
        if not panel_url:
            raise ValueError("Недостаточно данных для подключения к панели")
        try:
            xui_api = AsyncApi(
                host=panel_url,
                username=login,
                password=password
            )
            await xui_api.login()

            return await method(*args, **kwargs, xui_api=xui_api)

        except Exception as e:
            logger.error(e)
            return await method(*args, **kwargs)

    return wrapper