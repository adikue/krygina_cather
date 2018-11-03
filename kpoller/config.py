from ConfigParser import SafeConfigParser

class Config(object):
    """docstring for Config"""

    OPTIONS = {
        "db_url": ("kpoller", "database_url"),
        "box_url": ("kpoller", "box_url"),
        "kr_login": ("kpoller", "kr_login"),
        "kr_pass": ("kpoller", "kr_pass"),

        "smtp_login": ("smtp", "smtp_login"),
        "smtp_pass": ("smtp", "smtp_pass"),

        "port": ("app", "port"),
    }

    def __init__(self, conf_path):
        super(Config, self).__init__()
        self.conf_path = conf_path

        self.config = SafeConfigParser()
        self.config.readfp(open(conf_path))

        for opt in self.OPTIONS.values():
            self.config.get(*opt)

    @property
    def db_url(self):
        return self.config.get(*self.OPTIONS["db_url"])

    @property
    def box_url(self):
        return self.config.get(*self.OPTIONS["box_url"])

    @property
    def kr_login(self):
        return self.config.get(*self.OPTIONS["kr_login"])

    @property
    def kr_pass(self):
        return self.config.get(*self.OPTIONS["kr_pass"])

    @property
    def smtp_login(self):
        return self.config.get(*self.OPTIONS["smtp_login"])

    @property
    def smtp_pass(self):
        return self.config.get(*self.OPTIONS["smtp_pass"])

    @property
    def port(self):
        return self.config.get(*self.OPTIONS["port"])
