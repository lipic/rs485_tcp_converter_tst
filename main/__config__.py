import bootloader
from collections import OrderedDict
import os


class Config:

    def __init__(self):
        self.boot = bootloader.Bootloader('https://github.com/lipic/bcbox_tst', "")
        self.setting_profiles: str = 'setting.dat'
        self.config = OrderedDict()
        self.config['reset'] = '0'
        self.config['automatic_update'] = '1'
        self.config['actual_sw_version'] = '0'
        self.config['testing_software'] = '0'
        self.config['errors'] = '0'
        self.config['id'] = '0'
        self.config['wi-fi_ap'] = '0'
        self.config['factory_reset'] = '0'
        self.config['wifi_status'] = '0'
        self.handle_configure('actual_sw_version', self.boot.get_version(""))
        self.get_config()

    def factory_reset(self) -> None:
        self.config = OrderedDict()
        self.config['reset'] = '0'
        self.config['automatic_update'] = '1'
        self.config['actual_sw_version'] = '0'
        self.config['testing_software'] = '0'
        self.config['errors'] = '0'
        self.config['id'] = '0'
        self.config['wi-fi_ap'] = '0'
        self.config['factory_reset'] = '0'
        self.config['wifi_status'] = '0'
        self.handle_configure('actual_sw_version', self.boot.get_version(""))
        self.write_setting(self.config)

    def get_config(self) -> OrderedDict[str, str]:
        try:
            setting = self.read_setting()
        except OSError:
            setting = {}

        if len(setting) != len(self.config):
            with open(self.setting_profiles, 'w') as file_to_write:
                file_to_write.write('')
                file_to_write.close()

            for i in self.config:
                if i in setting:
                    if self.config[i] != setting[i]:
                        self.config[i] = setting[i]
            setting = {}

        for i in self.config:
            if i in setting:
                if self.config[i] != setting[i]:
                    self.config[i] = setting[i]
            else:
                setting[i] = self.config[i]
                self.write_setting(setting)

        if self.config['id'] == '0':
            _id = bytearray(os.urandom(8))
            rand_id = ''
            for i in range(0, len(_id)):
                rand_id += str((int(_id[i])))
            self.config['id'] = rand_id[-6:]
            self.handle_configure('id', self.config['id'])

        return self.config

    def handle_configure(self, variable, value) -> bool:
        try:
            if variable == 'reset':
                from machine import reset
                reset()

            if len(variable) > 0:
                try:
                    setting = self.read_setting()
                except OSError:
                    setting = {}

                if setting[variable] != value:
                    setting[variable] = value
                    self.write_setting(setting)
                    self.get_config()
                    return True
            else:
                return False
        except Exception as e:
            print(e)

    def read_setting(self) -> OrderedDict[str, str]:
        with open(self.setting_profiles) as f:
            lines = f.readlines()

        setting: OrderedDict = {}
        try:
            for line in lines:
                variable, value = line.strip("\n").split(";")
                setting[variable] = value
            return setting

        except Exception:
            self.write_setting(self.config)
            return self.config

    # method for write data to file.dat
    def write_setting(self, setting) -> None:
        lines: list = []
        for variable, value in setting.items():
            lines.append("%s;%s\n" % (variable, value))
        with open(self.setting_profiles, "w") as f:
            f.write(''.join(lines))

    def __getitem__(self, key):
        return self.config[key]
