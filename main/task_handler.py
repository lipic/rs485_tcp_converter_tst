import uasyncio as asyncio
from led_handler import LedHandler
from gc import mem_free, collect, mem_alloc
from collections import OrderedDict
from machine import Pin, WDT
from main import web_server_app
from main.__config__ import Config
import ulogging

LED_WIFI_HANDLER_ERR: int = 1
LED_MQTT_GSM_ERR: int = 2
TIME_SYNC_ERR: int = 4


class TaskHandler:
    def __init__(self, wifi):
        self.wdt: WDT = WDT(timeout=60000)
        self.setting: OrderedDict = Config()
        self.web_server_app = web_server_app.WebServerApp(wifi=wifi, setting=self.setting, debug=int(self.setting.config['testing_software']))
        self.wifi_manager = wifi
        self.led_error_handler: LedHandler = LedHandler(21, 1, 2, 40)
        self.led_wifi_handler: LedHandler = LedHandler(22, 1, 2, 20)
        self.wifi_manager.turnONAp()
        self.number_of_connection_attempts: int = 0

        self.logger = ulogging.getLogger(__name__)
        if int(self.setting.config['testing_software']) == 1:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def led_wifi(self):
        while True:
            await self.led_wifi_handler.led_handler()
            await asyncio.sleep(0.1)
            collect()

    async def led_error(self):
        while True:
            await self.led_error_handler.led_handler()
            await asyncio.sleep(0.1)
            collect()

    async def wifi_handler(self):
        wifi_handler_error: int = -1
        ap: int = 1
        wifi: int = 2
        wifi_status: int = 0

        while True:
            try:
                self.led_wifi_handler.add_state(ap)
                wifi_status |= ap
                if self.wifi_manager.is_connected():
                    self.led_wifi_handler.add_state(wifi)
                    wifi_status |= wifi
                else:
                    self.led_wifi_handler.remove_state(wifi)
                    wifi_status &= ~wifi
                    if len(self.wifi_manager.read_profiles()) != 0:
                        if self.number_of_connection_attempts > 30:
                            self.number_of_connection_attempts = 0
                            await self.wifi_manager.get_connection()
                        self.number_of_connection_attempts = self.number_of_connection_attempts + 1
                self.led_error_handler.remove_state(LED_WIFI_HANDLER_ERR)
            except Exception as e:
                self.led_error_handler.add_state(LED_WIFI_HANDLER_ERR)
                wifi_status = wifi_handler_error
                self.logger.error("Wi-fi handler error: {}".format(e))

            self.setting.config['wifi_status'] = '{}'.format(wifi_status)
            collect()
            await asyncio.sleep(2)

    async def system_handler(self):
        while True:
            self.wdt.feed()
            collect()
            await asyncio.sleep(1)

    def main_task_handler_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.wifi_handler())
        loop.create_task(self.system_handler())
        loop.create_task(self.led_error())
        loop.create_task(self.led_wifi())
        loop.create_task(self.web_server_app.web_server_run())
        # loop.create_task(self.web_server_app.run_dns_server())
        loop.run_forever()
