import uasyncio as asyncio
import ulogging
from umodbus.modbus import ModbusTCP
import ujson as json
from gc import collect


class ModbusTCPServer:

    def __init__(self, wifi, port: int = 502, ip: str = '0.0.0.0', debug: bool = False) -> None:
        self.port = port
        self.wifi = wifi
        self.ip = ip
        self.debug = debug
        self.server = None

        self.client = ModbusTCP()
        is_bound = self.client.get_bound_status()
        try:
            if not is_bound:
                self.client.bind(local_ip=ip, local_port=port)
        except:
            from machine import reset
            reset()

        collect()
        with open('main/registers.json', 'r') as file:
            register_definitions = json.load(file)
        collect()
        self.client.setup_registers(registers=register_definitions, use_default_vals=True)
        self.logger = ulogging.getLogger(__name__)
        if debug:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def run(self) -> None:
        while True:
            if self.wifi.is_connected():
                self.client.process()
            await asyncio.sleep(0.5)

    def set_dynamic_registers(self, data: dict) -> None:
        self.client.set_hreg(0, [data['U1']])
        self.client.set_hreg(1, [data['U2']])
        self.client.set_hreg(2, [data['U3']])
        i1: int = 22# self.data['I1'] if self.data['I1'] < 32769 else self.data['I1'] - 65535
        self.client.set_hreg(3, [i1])
        self.client.set_hreg(4, [data['I2']])
        self.client.set_hreg(5, [data['I3']])
        self.client.set_hreg(6, [data['P1']])
        self.client.set_hreg(7, [data['P2']])
        self.client.set_hreg(8, [data['P3']])
