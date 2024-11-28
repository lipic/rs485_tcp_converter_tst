from gc import collect
import uasyncio as asyncio
import ulogging
from umodbus.serial import Serial
from machine import Pin

collect()

sofar_addr: dict = {
    0x48D: ("U1", 1, 1),  # 0.1V
    0x498: ("U2", 1, 1),  # 0.1V
    0x4A3: ("U3", 1, 1),  # 0.1V
    0x48E: ("I1", 0.01, 1),  # 0.01A
    0x499: ("I2", 0.01, 1),  # 0.01A
    0x4A4: ("I3", 0.01, 1),  # 0.01A
    0x48F: ("P1", 0.01, 1),  # 0.01 kw
    0x49A: ("P2", 0.01, 1),  # 0.01 kw
    0x4A5: ("P3", 0.01, 1),  # 0.01 kw
    0x608: ("SOC", 1, 1),  # %
}

rct_addr: dict = {
    40039: ("U1", 0.1, 1),  # V
    40040: ("U2", 0.1, 1),  # V
    40041: ("U3", 0.1, 1),  # V
    40033: ("I1", 1, 1),  # 0.01A
    40034: ("I2", 1, 1),  # 0.01A
    40035: ("I3", 1, 1),  # 0.01A
    40075: ("SOC", 0.1, 1),  # %
}

sunway_addr: dict = {
    11009: ("U1", 0.1, 1),  # V
    11011: ("U2", 0.1, 1),  # V
    11013: ("U3", 0.1, 1),  # V
    10994: ("P1", 1, 2),  # kW
    10996: ("P2", 1, 2),  # kW
    10998: ("P3", 1, 2),  # kW
    43000: ("SOC", 1, 1),  # %
}

deye_addr: dict = {
    598: ("U1", 0.1, 1),  # V
    599: ("U2", 0.1, 1),  # V
    600: ("U3", 0.1, 1),  # V
    604: ("P1", 1, 1),  # kW
    605: ("P2", 1, 1),  # kW
    606: ("P3", 1, 1),  # kW
    610: ("I1", 1, 1),  # A
    611: ("I2", 1, 1),  # A
    612: ("I3", 1, 1),  # A
    214: ("SOC", 1, 1),  # %
}

wattsonic_addr: dict = {
    11009: ("U1", 0.1, 1),  # V
    11011: ("U2", 0.1, 1),  # V
    11013: ("U3", 0.1, 1),  # V
    10994: ("P1", 1, 2),  # W
    10996: ("P2", 1, 2),  # W
    10998: ("P3", 1, 2),  # W
    33000: ("SOC", 0.01, 1),  # %
}


class ModbusRTUServer:

    def __init__(self, config, modbus_tcp, debug=False) -> None:
        self.inverters: list = ['SOFAR', 'RCT', 'SUNWAY', 'DEYE', 'WATTSONIC']
        self.debug = debug
        self.config = config
        self.modbus_tcp = modbus_tcp
        self.server = None
        self.host = Serial(pins=(17, 16),  # (TX, RX)
                           baudrate=9600,
                           ctrl_pin=19,
                           uart_id=1)

        self.rs485_led = Pin(21, Pin.OUT)
        self.modbus_tcp.set_static_registers(int(self.config['inverter_type']))
        self.logger = ulogging.getLogger(__name__)
        if debug:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)
        self.logger.info(f" Supported inverters => {', '.join(self.inverters)}")
        self.logger.info(f" Selected inverter => {self.inverters[int(self.config['inverter_type']) - 1]}")
        self.modbus_id: int = 1

    async def run(self) -> None:
        konst: int = 1
        while True:
            try:
                data: dict = dict()
                if self.config['inverter_type'] == '1':
                    addr_dict = sofar_addr
                elif self.config['inverter_type'] == '2':
                    konst = 100
                    addr_dict = rct_addr
                elif self.config['inverter_type'] == '3':
                    konst = 100
                    addr_dict = sunway_addr
                elif self.config['inverter_type'] == '4':
                    addr_dict = deye_addr
                elif self.config['inverter_type'] == '5':
                    konst = 100
                    addr_dict = wattsonic_addr
                    self.modbus_id = 247
                else:
                    self.logger.debug("unknown inverter")
                    raise ValueError("unknown inverter")

                keys: list = [value[0] for value in addr_dict.values()]
                for address, (name, multiplier, length) in addr_dict.items():
                    val = self.host.read_holding_registers(slave_addr=self.modbus_id, starting_addr=address, register_qty=length)
                    if length > 1:
                        val = val[0] << 16 | val[1] & 0xFFFF
                    else:
                        val = val[0]
                    val = val * multiplier
                    data[name] = int(val)
                    await asyncio.sleep(0.1)

                for i in range(1, 4):
                    if f'I{i}' not in keys and data[f'U{i}'] != 0:
                        data[f'I{i}'] = int((data[f'P{i}'] * konst) / data[f'U{i}'])
                for i in range(1, 4):
                    if f'P{i}' not in keys:
                        data[f'P{i}'] = int((data[f'I{i}'] * konst) * data[f'U{i}'])

                self.logger.debug(data)
                self.rs485_led.on()
                self.modbus_tcp.set_dynamic_registers(data=data)

            except Exception as e:
                self.rs485_led.off()
                if 0 <= int(self.config['inverter_type'])-1 <= len(self.inverters):
                    self.logger.error(f" {self.inverters[int(self.config['inverter_type']) -1 ]} => {e}")
                else:
                    self.logger.error(e)

            collect()
            await asyncio.sleep(1)
