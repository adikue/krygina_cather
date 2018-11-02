import logging
import functools
from smtplib import SMTP, SMTPException

from utils import safe_retry


class EmailSender(SMTP):
    """docstring for EmailSender"""
    INIT_ARGS = ["host", "user", "password", "port"]

    def __init__(self, host, user, password, port=587):
        self.logger = logging.getLogger(self.__class__.__name__)
        SMTP.__init__(self, host, port)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.logger.info("Initialized")
        self.login()

    def login(self, user=None, password=None):
        user = user if user else self.user
        password = password if password else self.password
        self.logger.debug(SMTP.starttls(self))
        self.logger.debug(SMTP.login(self, user, password))
        self.logger.info("Logined")

    def quit(self):
        try:
            SMTP.quit(self)
        except SMTPException:
            pass
        finally:
            self.logger.info("Quited")

    def sendmail(self, from_addr, to_addrs, msg):
        if not isinstance(to_addrs, list):
            to_addrs = [to_addrs]
        self.logger.info("Sending mail to %s" % to_addrs)

        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)
        return SMTP.sendmail(self, from_addr, to_addrs, msg.as_string())

EmailSender.safe_sendmail = safe_retry(EmailSender.sendmail,
                                      attempts=10, retry_time=10)