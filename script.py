# -*- coding: utf-8 -*-
import os
import time
import random
import logging
import smtplib
import traceback
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from unidecode import unidecode
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys

my_email = "adikue@gmail.com"
box_url = 'https://elenakrygina.com/box/'
DRIVER_TYPE = webdriver.PhantomJS

FORMAT = '%(asctime)s %(name)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger('KPOOLER')


def login(driver):
    driver.get("https://elenakrygina.com/box/#top-up-auth")
    l_button = driver.find_element_by_css_selector(
        "a.top-up_open.header__profile-top__auth.g__icons")
    l_button.click()

    email_form = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/input[1]')
    email_form.clear()
    email_form.send_keys("litvinenko_v@inbox.ru")
    # email_form.send_keys("adikue@gmail.com")

    password_form = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/input[2]')
    password_form.clear()
    password_form.send_keys("yfnfif")
    # password_form.send_keys("qweASD123")

    login_button = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/button')
    login_button.click()


def init_webdriver(driver_cls=DRIVER_TYPE):
    headers = { 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.5',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Connection': 'keep-alive'
    }

    caps = DesiredCapabilities.PHANTOMJS.copy()
    for key, value in headers.iteritems():
        caps['phantomjs.page.customHeaders.{}'.format(key)] = value

    caps['phantomjs.page.settings.userAgent'] = "Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0"

    driver = driver_cls(desired_capabilities=caps)
    # driver = webdriver.Firefox()
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.implicitly_wait(5)
    try:
        login(driver)
    except:
        save_page_and_screenshot(driver)
        raise

    return driver


def safe_close_webdriver(driver):
    try:
        driver.close()
    except:
        pass
    else:
        logger.info('Driver has been properly closed')

def save_page_and_screenshot(driver):
    try:
        with open('page.html', 'wb+') as page:
            page.write(driver.page_source.encode('utf-8'))
        driver.save_screenshot('screenshot.png')
    except:
        pass
    else:
        logger.info('Page source and screenshot were saved')

class EmailSender(object):
    """docstring for EmailSender"""

    sent_storage = 'sent.boxes'

    basedir = os.path.dirname(sent_storage)
    if basedir and not os.path.exists(basedir):
        os.makedirs(basedir)
    if not os.path.exists(sent_storage):
        open(sent_storage, 'a+').close()

    def __init__(self):
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.login()

    def login(self):
        self.server.starttls()
        self.server.login(my_email, "clwqyihnzrdndphn")

    def safe_start(self):
        self.safe_quit()
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.login()
        self.init_storage(self.stor_fpath)

    def safe_quit(self):
        try:
            self.server.quit()
        except:
            pass

    @staticmethod
    def _boxmail_entry(box_mail):
        box = box_mail.box
        inbasket = 'in basket' if box_mail.inbasket else 'available'
        s = '[%s-%s]:%s to %s\n' % (box.month, box.name, inbasket, box_mail.msg['To'])
        return s

    @classmethod
    def boxmail_issent(cls, box_mail):
        with open(cls.sent_storage, 'r+') as stor:
            sent_boxes = stor.readlines()
        return cls._boxmail_entry(box_mail) in sent_boxes

    def remember_boxmail(self, box_mail):
        with open(self.sent_storage, 'a+') as stor:
            stor.write(self._boxmail_entry(box_mail))

    def send(self, msg):
        if isinstance(msg, BoxEmail):
            if self.boxmail_issent(msg):
                logger.info('The mail about this box has been sent already')
                return
            else:
                mail = msg.mail
                self.server.sendmail(mail['From'], mail['To'], mail.as_string())
                self.remember_boxmail(msg)
                logger.info('The mail has been sent and remembered')
        else:
            self.server.sendmail(msg['From'], msg['To'], msg.as_string())


class Box(object):
    """docstring for Box"""
    box_props_selects = {
        'name': 'div.fb-item__name',
        'month': 'div.fb-item__box__month',
        'description': 'div.fb-item__text.fb-item__text_mob',
        'price': 'div.fb-item__price.fb-item__price_box',
        
    }
    buy_btn_select = 'a.fb-item__link__buy.btn_buy.js-buy-box'
    item_select = 'div.fb-item__box-item'
    item_props_selects = {
        'name': 'div.fb-item__box-item__name',
        'description': 'div.fb-item__box-item__description',
        'price': 'div.fb-item__box-item__price',
    }

    class Item(object):
        """docstring for HtmlItem"""
        def __init__(self, name, description, price, **kwargs):
            super(Box.Item, self).__init__()
            self.name = name
            self.description = description
            self.price = price

        def __str__(self):
            s = "[%s](%s):\n%s" % (self.name, self.price, self.description)
            return s

        def html(self):
            s = '<p><strong>%s</p></strong>\n' % self.name
            s += '<p>%s</p>\n' % self.description
            s += '<p><em>%s</p></em>\n' % self.price
            return s

    def __init__(self, driver, url):
        super(Box, self).__init__()
        self._available = False
        self.box_items = []
        self.driver = driver
        self.url = url

        driver.get(url)
        for name, selector in self.box_props_selects.iteritems():
            elements = driver.find_elements_by_css_selector(selector)
            for e in elements:
                if e.text:
                    str_val = e.text.capitalize()
                    if name == 'price':
                        str_val = str_val[:-1] + u'руб'
                    setattr(self, name, str_val.encode('utf8', errors='ignore'))
                    break

        buy_btns = driver.find_elements_by_css_selector(self.buy_btn_select)
        for b in buy_btns:
            if b.text:
                self._available = True

        for box_elem in driver.find_elements_by_css_selector(self.item_select):
            propetries = {'name': '', 'description': '', 'price': ''}

            for name, selector in self.item_props_selects.iteritems():
                try:
                    e = box_elem.find_element_by_css_selector(selector)
                except NoSuchElementException:
                    continue

                str_val = e.get_attribute("textContent")
                if str_val:
                    str_val = str_val.strip()
                    if name == 'price':
                        str_val = str_val[:-1] + u'руб'
                    propetries[name] = str_val.encode('utf8', errors='ignore')

            if any(propetries.values()):
                self.box_items.append(Box.Item(**propetries))
        

    @property
    def available(self):
        return bool(self._available)

    def safe_buy(self):
        self.driver.get(self.url)
        buy_btns = self.driver.find_elements_by_css_selector(self.buy_btn_select)
        for b in buy_btns:
            if b.text:
                try:
                    self.driver.execute_script('arguments[0].click();', b)
                except:
                    return False
        return True

    def html(self):
        s = '<html><head></head><body>\n'
        s += '<h2>%s; %s</h2>\n' % (self.name, self.month)
        s += '<p><em>Цена - %s&nbsp;' % self.price
        s += '<a href="https://elenakrygina.com/store/user/cart/">Купить</a></em></p>\n'
        s += '<blockquote>\n'
        s += '<p>%s</p>\n' % self.description
        s += '</blockquote>\n'
        for i in self.box_items:
            s += i.html()
        s += '</body></html>'
        return s

    def __str__(self):
        s = "[%s: %s](%s): %s\n" % (self.month, self.name, self.price, self.description)
        s += "\n".join([str(i) for i in self.box_items])
        return s


class BoxEmail(object):
    """docstring for BoxEmail"""
    def __init__(self, box, subscribers, inbasket=False):
        super(BoxEmail, self).__init__()
        self.box = box
        self.inbasket = inbasket

        self.msg = MIMEMultipart('alternative')
        self.msg['Content-Type'] = "text/html; charset=utf-8"
        if inbasket:
            subj = "[kryginabox] %s в корзине. Есть 1 час чтобы купить" % box.month
        else:
            subj = "[kryginabox] %s доступна! Иди покупай быстрее" % box.month
        self.msg['Subject'] = subj
        self.msg['From'] = my_email
        self.msg['To'] = ', '.join(subscribers)

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(str(box), 'plain')
        part2 = MIMEText(box.html(), 'html', 'utf-8')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        self.msg.attach(part1)
        self.msg.attach(part2)

    @property
    def mail(self):
        return self.msg

    def __str__(self):
        return self.msg.as_string()
        

subscribers_list = [
    'litvinenko_v@inbox.ru',
    'adikue@gmail.com',
]

def box_notsent_to(box):
    not_sent = []
    for dest in subscribers_list:
        box_message = BoxEmail(box, [dest], True)
        if not EmailSender.boxmail_issent(box_message):
            logger.info('%r has NOT been notified' % dest)
            not_sent.append(dest)
        else:
            logger.info('%r has been notified' % dest)
    return not_sent

def main():
    logger.info("Started")
    driver = init_webdriver()
    while True:
        logger.info('Iteration started')
        try:
            box = Box(driver, box_url)
            if box.available:
                logger.info("Box is available to buy. "
                    "Checking if all subscribers were notified")
                not_sent_dst = box_notsent_to(box)

                if not_sent_dst:
                    logger.info("Putting into backet")
                    inbasket = box.safe_buy()
                    logger.info('In backet - %s' % inbasket)
                    if not inbasket:
                        logger.error('Problem putting into backet')

                    if not_sent_dst:
                        em_sender = EmailSender()
                        for dest in not_sent_dst:
                            box_message = BoxEmail(box, [dest], inbasket)
                            logger.info('Sending e-mail to %r' % dest)
                            em_sender = EmailSender()
                            em_sender.send(box_message)
                            time.sleep(1)
                        em_sender.safe_quit() 
            else:
                logger.info('Box is NOT available')
        except Exception as e:
            logger.error('Exception occured:')
            traceback.print_exc()
            save_page_and_screenshot(driver)
            if isinstance(e, WebDriverException):
                safe_close_webdriver(driver)
                for attempt in xrange(100):
                    logger.info('Attemprt to restart the WebDriver #%s' % attempt)
                    try:
                        driver = init_webdriver()
                    except:
                        logger.info('Failed to restart WebDriver')
                        pass
                    else:
                        logger.info('WebDriver has been restarted')
                        break
                    time.sleep(60)
                else:
                    raise
            else:
                logger.error('Unhandable exception. Exiting')
                safe_close_webdriver(driver)
                raise

        logger.info('Iteration ended')
        wait_seconds = random.randint(30, 120)
        logger.info('Will sleep for %ds' % wait_seconds)
        time.sleep(wait_seconds)

if __name__ == "__main__":
    main()
