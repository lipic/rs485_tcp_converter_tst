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
        self.set_static_registers()

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
        self.client.set_hreg(0, [data['U1']])  # [V]
        self.client.set_hreg(1, [data['U2']])  # [V]
        self.client.set_hreg(2, [data['U3']])  # [V]
        self.client.set_hreg(3, [data['I1']])  # [A*0.01]
        self.client.set_hreg(4, [data['I2']])  # [A*0.01]
        self.client.set_hreg(5, [data['I3']])  # [A*0.01]
        self.client.set_hreg(6, [data['P1']])  # [W]
        self.client.set_hreg(7, [data['P2']])  # [W]
        self.client.set_hreg(8, [data['P3']])  # [W]
        self.client.set_hreg(9, [data['SOC']])  # [%]
        self.client.set_hreg(10, [data['TYPE']])

    def set_static_registers(self, inverter_type: int = 1) -> None:
        #  -SOFAR-ID
        if inverter_type == 1:
            data = [ord(char) for char in "-SOFAR-123654-"]
            # data.extend([5, 48, 54, 53, 52, 45])
            self.client.set_hreg(50, data)
