import picoweb
from machine import reset, RTC
import ujson as json
from gc import collect, mem_free
import uasyncio as asyncio
import ulogging
import usocket as socket
from re import compile

SERVER_IP = '8.8.8.8'
# Helper to detect uasyncio v3
IS_UASYNCIO_V3 = hasattr(asyncio, "__version__") and asyncio.__version__ >= (3,)

class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15
        if tipo == 0:
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]
        print("searched domain:" + self.domain)

    def response(self, ip):

        print("Response {} == {}".format(self.domain, ip))
        packet = None
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.'))) #+ b'\x00\x50'  # 4bytes of IP
        return packet


class WebServerApp:
    def __init__(self, wifi, setting, debug):
        self.setting = setting
        self.wifi_manager = wifi
        self.ip_address: str = ''
        self.port: int = 80
        self.ssid_client: dict = dict()
        self.datalayer = dict()

        self.logger = ulogging.getLogger("WebServerApp")
        if debug == 1:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)
        self.router = [
            ("/", self.main),
            ("/updateWifi", self.update_wifi),
            ("/loadWifiSSID", self.load_wifi_ssid),
            ("/loadSettings", self.load_settings),
            ("/updateSetting", self.update_setting),
            ("/getEspID", self.get_esp_id),

            ("/hotspot-detect.html", self.web_redirect),
            ("/success.html", self.web_redirect),
            (compile("^/generate_204"), self.web_204),
            ("/ncsi.txt", self.web_redirect),
            ("/check_network_status.txt", self.web_redirect),
            ("/connecttest.txt", self.web_redirect_win11),
            ("/wpad.dat", self.web_not_found),
            ("/redirect", self.web_redirect),
            ("/canonical.html", self.web_redirect),
            ("/success.txt", self.web_ok),
            ("/favicon.ico", self.web_not_found)]

        self.app = picoweb.WebApp(None, self.router)

    def web_not_found(self, req, resp):
        yield from picoweb.start_response(resp, status="404")

    def web_204(self, req, resp):
        target_port = '80'
        target_url = 'http://' + SERVER_IP + ':' + target_port
        header = {"Location": target_url}
        yield from picoweb.start_response(resp, status="302 Found", headers=header)

    def web_ok(self, req, resp):
        yield from picoweb.start_response(resp, status="200")

    def web_redirect_win11(self, req, resp):
        self.setting.loading_wifi = True
        headers = {"Location": "http://logout.net"}
        yield from picoweb.start_response(resp, status="302", headers=headers)

    def web_redirect(self, req, resp):
        self.setting.loading_wifi = True
        target_port = '80'
        target_url = 'http://' + SERVER_IP + ':' + target_port
        headers = {"Location": target_url}
        yield from picoweb.start_response(resp, status="302", headers=headers)
        yield from resp.awrite("Success")

    def main(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "main.html")

    def load_wifi_ssid(self, req, resp):
        if self.wifi_manager.is_connected() and req.method == "GET":
            self.ssid_client["connectSSID"] = self.wifi_manager.getCurrentConnectSSID()
            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(self.ssid_client))
        else:
            self.setting.loading_wifi = True
            self.ssid_client.clear()
            client = self.wifi_manager.getSSID()
            for i in client:
                if client[i] > -86:
                    self.ssid_client[i] = client[i]
            self.ssid_client["connectSSID"] = self.wifi_manager.getCurrentConnectSSID()
            print(self.ssid_client)
            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(self.ssid_client))

    def update_wifi(self, req, resp):
        collect()
        size = int(req.headers[b"Content-Length"])
        qs = yield from req.reader.read(size)
        req.qs = qs.decode()
        data_layer: dict = {}
        try:
            i = json.loads(req.qs)
            data_layer = await self.wifi_manager.handle_configure(i["ssid"], i["password"])
        except:
            pass
        self.ip_address = self.wifi_manager.get_ip()
        data_layer = {"process": data_layer, "ip": self.ip_address}

        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(data_layer))
        asyncio.create_task(self.reset_task())

    async def reset_task(self):
        await asyncio.sleep(20)
        reset()

    def update_setting(self, req, resp):
        collect()
        datalayer = {}
        req = await self.process_msg(req)

        for i in req.form:
            i = json.loads(i)
            datalayer = self.setting.handle_configure(i["variable"], i["value"])
            datalayer = {"process": datalayer}

        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))

    def load_settings(self, req, resp):
        collect()
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(self.setting.config))

    def process_msg(self, req):
        size = int(req.headers[b"Content-Length"])
        qs = yield from req.reader.read(size)
        req.qs = qs.decode()
        req.parse_qs()
        return req

    def get_esp_id(self, req, resp):
        datalayer = {"ID": " VC: {}".format(self.setting.config['id']), "IP": self.wifi_manager.get_ip()}
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))

    async def web_server_run(self):
        try:
            self.logger.info(f"Webserver app started on IP: {SERVER_IP}, PORT: {self.port}")
            self.app.run(debug=False, host=SERVER_IP, port=self.port)
            while True:
                await asyncio.sleep(100)
        except Exception as e:
            self.logger.error("Webserver error: {}. I will reset MCU".format(e))
            reset()

    async def run_dns_server(self):
        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)
        udps.bind((SERVER_IP, 53))

        while True:
            try:
                collect()
                if IS_UASYNCIO_V3:
                    yield asyncio.core._io_queue.queue_read(udps)
                else:
                    yield asyncio.IORead(udps)
                data, addr = udps.recvfrom(4096)
                DNS = DNSQuery(data)
                udps.sendto(DNS.response(SERVER_IP), addr)
                print("Replying: {:s} -> {:s}".format(DNS.domain, SERVER_IP))

            except Exception as e:
                await asyncio.sleep_ms(3000)

        udps.close()
