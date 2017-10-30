# -*- coding: utf-8 -*-
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
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys

my_email = "adikue@gmail.com"
box_url = 'https://elenakrygina.com/box/'


def login(driver):
    driver.get("https://elenakrygina.com/box/#top-up-auth")

    email_form = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/input[1]')
    email_form.send_keys("litvinenko_v@inbox.ru")

    password_form = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/input[2]')
    password_form.send_keys("yfnfif")

    login_button = driver.find_element_by_xpath('//*[@id="top-up-auth"]/form/div/div/button')
    login_button.click()


def init_webdriver():
    driver = webdriver.Firefox()
    driver.implicitly_wait(10)
    login(driver)
    return driver


def save_close_webdriver():
    try:
        driver.close()
    except:
        pass


class EmailSender(object):
    """docstring for EmailSender"""

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

    def safe_quit(self):
        try:
            self.server.quit()
        except:
            pass

    def send(self, msg):
        self.server.sendmail(msg['From'], msg['To'], msg.as_string())


class Box(object):
    """docstring for Box"""
    box_props_selects = {
        'name': 'div.fb-item__name',
        'month': 'div.fb-item__box__month',
        'description': 'div.fb-item__text.fb-item__text_mob',
        'price': 'div.fb-item__price.fb-item__price_box',
        'buy_button': 'a.fb-item__link__buy.btn_buy.js-buy-box',
        'items': 'a.fb-item__link__buy.btn_buy.js-buy-box',
    }
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
        self.buy_button = None
        self.items = []

        driver.get(url)
        for name, selector in self.box_props_selects.iteritems():
            elements = driver.find_elements_by_css_selector(selector)
            for e in elements:
                if e.text:
                    if name == 'buy_button':
                        setattr(self, name, e)
                    else:
                        str_val = e.text.capitalize()
                        if name == 'price':
                            str_val = str_val[:-1] + u'руб'
                        setattr(self, name, str_val.encode('utf8', errors='ignore'))
                    break

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
                self.items.append(Box.Item(**propetries))

    @property
    def available(self):
        return bool(self.buy_button)

    def buy(self):
        if self.available:
            self.buy_button.click()

    def html(self):
        s = '<html><head></head><body>\n'
        s += '<h2>%s; %s</h2>\n' % (self.name, self.month)
        s += '<p><em>Цена - %s&nbsp;' % self.price
        s += '<a href="https://elenakrygina.com/store/user/cart/">Купить</a></em></p>\n'
        s += '<blockquote>\n'
        s += '<p>%s</p>\n' % self.description
        s += '</blockquote>\n'
        for i in self.items:
            s += i.html()
        s += '</body></html>'
        return s

    def __str__(self):
        s = "[%s: %s](%s): %s\n" % (self.month, self.name, self.price, self.description)
        s += "\n".join([str(i) for i in self.items])
        return s


class BoxEmail(object):
    """docstring for BoxEmail"""
    def __init__(self, box, subscribers, inbasket=False):
        super(BoxEmail, self).__init__()

        self.msg = MIMEMultipart('alternative')
        self.msg['Content-Type'] = "text/html; charset=utf-8"
        if inbasket:
            subj = "[kryginabox] %s в корзине. Есть 1 час чтобы купить" % box.month
        else:
            subj = "[kryginabox] %s доступна! Иди покупай быстрее"
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
    'adikue@gmail.com',
    'litvinenko_v@inbox.ru'
]

def main():
    FORMAT = '%(asctime)s %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger('KPOOLER')
    logger.info("Started")
    driver = init_webdriver()
    while True:
        logger.info('Iteration started')
        try:
            box = Box(driver, box_url)
            if box.available:
                logger.info('Box is available to buy. Putting into basket')
                try:
                    box.buy()
                    inbasket = True
                    logger.info('In backet now')
                except:
                    inbasket = False
                    logger.error('Problem putting into backet')

                logger.info('Generating e-mail')
                box_message = BoxEmail(box, subscribers_list, inbasket)
                logger.info('Sending e-mail')
                em_sender = EmailSender()
                em_sender.send(box_message.mail)
                em_sender.safe_quit()
                logger.info('E-mail has been sent')
            else:
                logger.info('Box is NOT available')
        except Exception as e:
            logger.error('Exception occured:')
            traceback.print_exc()
            if isinstance(e, WebDriverException):
                save_close_webdriver()
                driver = init_webdriver()
                logger.info('WebDriver has been restarted')
            else:
                logger.error('Unhandable exception. Exiting')
                save_close_webdriver()
                raise

        logger.info('Iteration ended')
        wait_seconds = random.randint(30, 120)
        logger.info('Will sleep for %ds' % wait_seconds)
        time.sleep(wait_seconds)

if __name__ == "__main__":
    main()
