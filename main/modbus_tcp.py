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
        try:
            self.client = ModbusTCP()
            is_bound = self.client.get_bound_status()
            if not is_bound:
                self.client.bind(local_ip=ip, local_port=port)
        except OSError as e:
            import errno
            if e.args[0] == errno.EADDRINUSE:
                from machine import reset
                reset()

        collect()
        with open('main/registers.json', 'r') as file:
            register_definitions = json.load(file)
        collect()
        self.client.setup_registers(registers=register_definitions, use_default_vals=True)
        self.set_dynamic_registers(data={})

        self.logger = ulogging.getLogger(__name__)
        if debug:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def run(self) -> None:
        while True:
            if self.wifi.is_connected():
                try:
                    self.client.process()
                except Exception as e:
                    print(e)
            await asyncio.sleep(0.5)

    def set_dynamic_registers(self, data: dict) -> None:
        self.client.set_hreg(0, [data.get('U1', 0)])
        self.client.set_hreg(1, [data.get('U2', 0)])  
        self.client.set_hreg(2, [data.get('U3', 0)])  
        self.client.set_hreg(3, [data.get('I1', 0)])  
        self.client.set_hreg(4, [data.get('I2', 0)])  
        self.client.set_hreg(5, [data.get('I3', 0)])  
        self.client.set_hreg(6, [data.get('P1', 0)])  
        self.client.set_hreg(7, [data.get('P2', 0)])  
        self.client.set_hreg(8, [data.get('P3', 0)])  
        self.client.set_hreg(9, [data.get('SOC', 0)])

    def set_static_registers(self, inverter_type: int = 1) -> None:
        if inverter_type == 1:
            data = [ord(char) for char in "-SOFAR-RS485-"]
            self.client.set_hreg(50, data)
        elif inverter_type == 2:
            data = [ord(char) for char in "-RCT-RS485-"]
            self.client.set_hreg(50, data)
        elif inverter_type == 3:
            data = [ord(char) for char in "-SUNWAYS-RS485-"]
            self.client.set_hreg(50, data)
        elif inverter_type == 4:
            data = [ord(char) for char in "-DEYE-RS485-"]
            self.client.set_hreg(50, data)