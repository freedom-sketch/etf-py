from py3xui import AsyncApi, Client
from utils.decorators.login import login
from typing import Optional, Union
from time import time
from pydantic_models.models import ServerStatus
from LoggerFactory import logger_factory

logger = logger_factory.create_logger(name='xui.methods')


class XuiAPI:
    @staticmethod
    @login
    async def add_new_client(email: Union[str, int],
                             user_id: str,
                             panel_url: str,
                             login: str,
                             password: str,
                             subscription_duration: int,
                             inbound_id: int=1,
                             flow: str='xtls-rprx-vision',
                             limit_ip: int=3,
                             xui_api: Optional[AsyncApi]=None
                             ) -> None:
        """
        :param email: email пользователя
        :param user_id: id пользователя
        :param panel_url: url x-ui панели. Используется декоратором для авторизации
        :param login: логин от панели 3x-ui
        :param password: пароль от панели 3x-ui
        :param subscription_duration: длительность подписки (в днях). 0 - без ограничения
        :param inbound_id: id блока соединений
        :param flow: способ управления трафиком
        :param limit_ip: лимит ip
        :param xui_api: экземпляр класса AsyncApi. Передается декоратором
        :return: None
        """
        try:
            if subscription_duration != 0:
                expiry_time = int(time() * 1000) + subscription_duration * 86400 * 1000
            else:
                expiry_time = 0

            new_client = Client(
                id=user_id,
                email=str(email),
                flow=flow,
                limit_ip=limit_ip,
                enable=True,
                expiry_time=expiry_time)

            await xui_api.client.add(inbound_id, [new_client])
        except Exception as e:
            logger.error(e)


    @staticmethod
    @login
    async def get_connection_string(telegram_id: Union[str, int],
                                    panel_url: str,
                                    login: str,
                                    password: str,
                                    server_address: str,
                                    server_port: int,
                                    inbound_id: int=1,
                                    tag: Optional[str]=None,
                                    description: Optional[str]=None,
                                    xui_api: Optional[AsyncApi]=None) -> Optional[str]:
        """
        :param telegram_id: Telegram id пользователя
        :param panel_url: url x-ui панели. Используется декоратором для авторизации
        :param login: логин от панели 3x-ui
        :param password: пароль от панели 3x-ui
        :param server_address: ip сервера
        :param server_port: порт на сервере для подключения
        :param inbound_id: id блока соединений
        :param tag: тэг для идентификации ключа
        :param xui_api: экземпляр класса AsyncApi. Передается декоратором
        :return: строка подключения или None
        """
        try:
            if xui_api is not None:
                inbound = await xui_api.inbound.get_by_id(inbound_id)

                import random
                reality_settings = inbound.stream_settings.reality_settings
                public_key = reality_settings["settings"]["publicKey"]
                random_website_name_index = random.randint(0, len(reality_settings["serverNames"])-1)
                website_name = reality_settings["serverNames"][random_website_name_index]
                short_id = reality_settings["shortIds"][0]
                fingerprint = reality_settings['settings']['fingerprint']
                #flow = reality_settings.get("flow", "xtls-rprx-vision")

                if description == 'XHTTP':
                    connection_string = (
                        f"vless://{telegram_id}@{server_address}:{server_port}"
                        f"?type=xhttp&encryption=none&path=%2F&host=&mode=auto&security=reality&pbk={public_key}&fp={fingerprint}&sni={website_name}"
                        f"&sid={short_id}&spx=%2F#{tag if tag else ''}"
                    )
                elif description == 'TCP':
                    connection_string = (
                        f"vless://{telegram_id}@{server_address}:{server_port}"
                        f"?type=tcp&encryption=none&security=reality&pbk={public_key}&fp={fingerprint}&sni={website_name}"
                        f"&sid={short_id}&spx=%2F&flow=xtls-rprx-vision#{tag if tag else ''}"
                    )
                else:
                    connection_string = ''
                return connection_string
            else:
                return None

        except Exception as e:
            logger.error(f"{panel_url}: {str(e)}")
            return None


    @staticmethod
    @login
    async def get_server_status(panel_url: str,
                                login: str,
                                password: str,
                                xui_api: Optional[AsyncApi]=None) -> ServerStatus:

        server_status = await xui_api.server.get_status()

        return ServerStatus(
            cpu_load=round(server_status.cpu, 2),
            cpu_cores=server_status.cpu_cores,
            cpu_speed=round(server_status.cpu_speed_mhz / 1000, 2),
            memory_usage=round(server_status.mem.current / 1024 ** 3, 2),
            memory_total=round(server_status.mem.total / 1024 ** 3, 2),
            disk_memory_total=round(server_status.disk.total / (1024**3), 2),
            disk_memory_current=round(server_status.disk.current / (1024**3), 2),
            public_ip_v4=server_status.public_ip.ipv4,
            public_ip_v6=server_status.public_ip.ipv6,
            uptime=server_status.uptime,
            xray_state=server_status.xray.state,
            xray_version=server_status.xray.version,
        )


    @staticmethod
    @login
    async def get_online_clients(panel_url: str,
                                 login: str,
                                 password: str,
                                xui_api: Optional[AsyncApi]=None) -> list[str]:
        return await xui_api.client.online()


    @staticmethod
    @login
    async def get_subscription_userinfo(user_id: Union[str, int],
                                        panel_url: str,
                                        login: str,
                                        password: str,
                                 xui_api: Optional[AsyncApi] = None):
        try:
            if xui_api is not None:
                return await xui_api.client.get_traffic_by_id(client_uuid=user_id)
        except Exception as e:
            logger.error(e)
            return None
