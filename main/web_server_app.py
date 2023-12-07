import picoweb
from machine import reset, RTC
import ujson as json
from gc import collect, mem_free
import uasyncio as asyncio
import ulogging
import usocket as socket

SERVER_IP = '192.168.4.1'

class DNSQuery:
	def __init__(self, data):
		self.data = data
		self.domain = ''
		tipo = (data[2] >> 3) & 15  # Opcode bits
		if tipo == 0:  # Standard query
			ini = 12
			lon = data[ini]
			while lon != 0:
				self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
				ini += lon + 1
				lon = data[ini]
		print("searched domain:" + self.domain)

	def response(self, ip):

		print("Response {} == {}".format(self.domain, ip))
		if self.domain:
			packet = self.data[:2] + b'\x81\x80'
			packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
			packet += self.data[12:]  # Original Domain Name Question
			packet += b'\xC0\x0C'  # Pointer to domain name
			packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
			packet += bytes(map(int, ip.split('.'))) + b'\x00\x50'  # 4bytes of IP
		return packet


class WebServerApp:
    def __init__(self, wifi, setting, debug):
        self.setting = setting
        self.wifi_manager = wifi
        self.ip_address: str = ''
        self.port: int = 80
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
            ("/connecttest.txt", self.web_redirect_win11),
            ("/wpad.dat", self.web_not_found),
            ("/generate_204", self.web_204),
            ("/redirect", self.web_redirect),
            ("/hotspot-detect.html", self.web_redirect),
            ("/canonical.html", self.web_redirect),
            ("/success.txt", self.web_ok),
            ("/ncsi.txt", self.web_redirect),
            ("/favicon.ico", self.web_not_found)]

        self.app = picoweb.WebApp(None, self.router)

    def web_not_found(self, req, resp):
        yield from picoweb.start_response(resp, status="404")
    def web_204(self, req, resp):
        yield from picoweb.start_response(resp, status="204")
    def web_ok(self, req, resp):
        yield from picoweb.start_response(resp, status="200")
    def web_redirect_win11(self, req, resp):
        self.setting.loading_wifi = True
        headers = {"Location": "http://logout.net"}
        yield from picoweb.start_response(resp, status="302", headers=headers)

    def web_redirect(self, req, resp):
        self.setting.loading_wifi = True
        target_ip = '192.168.4.1'
        target_port = '8000'
        target_url = 'http://' + target_ip + ':' + target_port
        headers = {"Location": target_url}
        yield from picoweb.start_response(resp, status="302", headers=headers)
    def main(self, req, resp):
        collect()
        self.setting.loading_wifi = True
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "main.html")

    def load_wifi_ssid(self, req, resp):
        self.setting.loading_wifi = True
        client = self.wifi_manager.getSSID()
        datalayer = {}
        for i in client:
            if client[i] > -86:
                datalayer[i] = client[i]
        datalayer["connectSSID"] = self.wifi_manager.getCurrentConnectSSID()
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))

    def update_wifi(self, req, resp):
        collect()
        size = int(req.headers[b"Content-Length"])
        qs = yield from req.reader.read(size)
        req.qs = qs.decode()
        try:
            i = json.loads(req.qs)
        except:
            pass
        datalayer = await self.wifi_manager.handle_configure(i["ssid"], i["password"])
        self.ip_address = self.wifi_manager.getIp()
        datalayer = {"process": datalayer, "ip": self.ip_address}

        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))
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
        datalayer = {"ID": " BCBOX: {}".format(self.setting.config['ID']), "IP": self.wifi_manager.getIp()}
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))

    async def web_server_run(self):
        try:
            self.logger.info("Webserver app started")
            self.app.run(debug=False, host=SERVER_IP, port=self.port)
            while True:
                await asyncio.sleep(100)
        except Exception as e:
            self.logger.error("Webserver error: {}. I will reset MCU".format(e))
            reset()

    async def run_dns_server(self):

        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)
        udps.bind(('0.0.0.0', 53))

        while True:
            try:
                collect()
                data, addr = udps.recvfrom(4096)
                DNS = DNSQuery(data)
                udps.sendto(DNS.response(SERVER_IP), addr)
                self.wifi_manager.wlan_sta.disconnect()
                self.setting.loading_wifi = True
                await asyncio.sleep_ms(100)
            except Exception as e:
                await asyncio.sleep_ms(3000)

        udps.close()
