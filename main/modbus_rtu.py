import uasyncio as asyncio
import ulogging
from umodbus.serial import Serial
from machine import Pin

class ModbusRTUServer:

    def __init__(self, baudrate: int = 9600, debug: bool = False) -> None:
        self.debug = debug
        self.server = None
        self.host = Serial(pins=(17, 16),  # (TX, RX)
                           baudrate=baudrate,
                           ctrl_pin=19, #31
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
                resp = self.host.read_holding_registers(slave_addr=1,
                                                        starting_addr=100,
                                                        register_qty=1)
                self.rs485_led.on()
                print(resp)
            except Exception as e:
                self.rs485_led.off()
                self.logger.debug(e)
            await asyncio.sleep(2)
