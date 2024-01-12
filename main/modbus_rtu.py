import uasyncio as asyncio
import ulogging
from umodbus.serial import Serial
from machine import Pin


class ModbusRTUServer:

    def __init__(self, config, modbus_tcp, debug=False) -> None:
        self.debug = debug
        self.config = config  # priklad pouziti... self.config['inverter_type']
        self.modbus_tcp = modbus_tcp   # priklad pouziti... self.modbus_tcp.set_dynamic_registers(data)
        self.server = None
        self.host = Serial(pins=(17, 16),  # (TX, RX)
                           baudrate=9600,
                           ctrl_pin=19,  # 31
                           uart_id=2)

        self.rs485_led = Pin(21, Pin.OUT)
        self.logger = ulogging.getLogger(__name__)
        if debug:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def run(self) -> None:
        while True:
            try:
                data: dict = dict()
                data["U1"] = 230
                data["U2"] = 230
                data["U3"] = 230
                data["I1"] = 3200
                data["I2"] = 3200
                data["I3"] = 3200
                data["P1"] = 9000
                data["P2"] = 9000
                data["P3"] = 9000
                data["SOC"] = 77
                self.modbus_tcp.set_dynamic_registers(data=data)
                #resp = self.host.read_holding_registers(slave_addr=1,
                #                                        starting_addr=100,
                #                                        register_qty=1)
                self.rs485_led.on()
                print(resp)
            except Exception as e:
                self.rs485_led.off()
                self.logger.debug(e)
            await asyncio.sleep(2)
