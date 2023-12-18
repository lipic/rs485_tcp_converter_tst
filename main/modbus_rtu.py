import uasyncio as asyncio
import ulogging
from umodbus.serial import Serial


class ModbusRTUServer:

    def __init__(self, baudrate: int = 9600, debug: bool = False) -> None:
        self.debug = debug
        self.server = None
        self.host = Serial(pins=(17, 16),  # (TX, RX)
                           baudrate=baudrate,
                           ctrl_pin=23,
                           uart_id=2)

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
                print(resp)
            except Exception as e:
                self.logger.debug(e)
            await asyncio.sleep(2)
