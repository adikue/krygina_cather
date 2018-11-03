# -*- coding: utf-8 -*-
import os
import logging

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils import safe_retry


class KrWebDriver(webdriver.PhantomJS):  # webdriver.Firefox
    """docstring for KrWebDriver"""

    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,"
                  "application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:57.0)"
                      "Gecko/20100101 Firefox/57.0",
        "Connection": "keep-alive",
    }
    BOX_PROPS = {
        'name': ['div.fb-item__name',
                 'h1.fb-item__name'],
        'month': 'div.fb-item__box__month',
        'description': 'div.fb-item__text.fb-item__text_mob',
        'price': 'div.fb-item__price.fb-item__price_box',

    }
    BUY_BTN = 'a.fb-item__link__buy.btn_buy.js-buy-box'
    ITEM = 'div.fb-item__box-item'
    ITEM_PROPS = {
        'name': 'div.fb-item__box-item__name',
        'description': 'div.fb-item__box-item__description',
        'price': 'div.fb-item__box-item__price',
    }
    RESOURCE_DIR = "/etc/kpoller/"
    INIT_ARGS = ["email", "password"]

    def __init__(self, email, password):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.email = email
        self.password = password

        caps = DesiredCapabilities.PHANTOMJS.copy()
        for key, value in self.HEADERS.iteritems():
            caps["phantomjs.page.customHeaders.%s" % key] = value
        caps["phantomjs.page.settings.userAgent"] = self.HEADERS["User-Agent"]
        super(KrWebDriver, self).__init__(desired_capabilities=caps)
        self.set_window_size(1920, 1080)
        self.maximize_window()
        self.implicitly_wait(5)
        self.logger.info('Initialized')
        try:
            self.login()
        except WebDriverException as e:
            self.logger.info("Failed to login - %s" % e)
            self.save_page_and_screenshot()
            raise

    def login(self):
        self.logger.info('Login started...')
        self.get("https://elenakrygina.com/box/#top-up-auth")
        l_button = self.find_element_by_css_selector(
            "a.top-up_open.header__profile-top__auth.g__icons")
        l_button.click()

        email_form = self.find_element_by_xpath(
            '//*[@id="top-up-auth"]/form/div/div/input[1]')
        email_form.clear()
        email_form.send_keys(self.email)

        password_form = self.find_element_by_xpath(
            '//*[@id="top-up-auth"]/form/div/div/input[2]')
        password_form.clear()
        password_form.send_keys(self.password)

        login_button = self.find_element_by_xpath(
            '//*[@id="top-up-auth"]/form/div/div/button')
        login_button.click()
        self.logger.info('Sucessfully logined')

    def close(self):
        try:
            super(KrWebDriver, self).close()
        except Exception as e:
            self.logger.info("Failed to close - %s" % e)
        else:
            self.logger.info('Closed')

    def save_page_and_screenshot(self, folder=None):
        self.logger.info("Dumping page source and screenshot")
        folder = folder if folder else self.RESOURCE_DIR
        if not os.path.exists(folder):
            os.makedirs(folder)
        try:
            with open(os.path.join(folder, 'page.html'), 'wb+') as page:
                page.write(self.page_source.encode('utf-8'))
            self.save_screenshot(os.path.join(folder, 'screenshot.png'))
        except Exception as e:
            self.logger.info("Failed to save page source and "
                             "screenshot - %s" % e)
        else:
            self.logger.info("Page source and screenshot were saved")

    def get_box(self, url):
        self.get(url)

        # get properties real values from the page
        self.logger.info("Looking for [BOX] properties")
        box_props = self._get_properties(self.BOX_PROPS)

        box_items = []
        for idx, _ in enumerate(self.find_elements_by_css_selector(self.ITEM)):
            self.logger.info("Looking for [BOX ITEM #%s] "
                             "properties" % (idx + 1))
            item_props = self._get_properties(self.ITEM_PROPS)
            if item_props:
                box_items.append(KrBoxItem(**item_props))

        if not box_props and not box_items:
            raise RuntimeError("Failed to get any information about the box")

        return KrBox(items=box_items, url=url, **box_props)

    def _get_properties(self, sel_dict):
        props = {}
        for p_name, selectors in sel_dict.iteritems():
            # if property is already found
            if p_name in props:
                continue

            if not isinstance(selectors, list):
                selectors = [selectors]
            for sel in selectors:
                for e in self.find_elements_by_css_selector(sel):
                    text = getattr(e, 'text', '')
                    if not text:
                        text = e.get_attribute("textContent")
                    if text:
                        self.logger.debug("Found property %r" % p_name)
                        text = text.strip().capitalize()
                        if p_name == 'price':
                            text = text[:-1] + u'руб'
                        props[p_name] = unicode(text)
                        # props[p_name] = text.encode('utf-8', errors='ignore')
                        break
                else:
                    # if we not found any valid text on elements with this
                    # selector, move to the next one
                    continue
                break
        return props

    def buy_box(self, box):
        self.get(box.url)
        buy_btns = self.find_elements_by_css_selector(self.BUY_BTN)

        bought = False
        for bb in buy_btns:
            try:
                self.execute_script('arguments[0].click();', bb)
                bb.click()
            except WebDriverException:
                continue
            else:
                bought = True
                break
        return bought

    def box_isavailable(self, box):
        self.get(box.url)
        return bool(self.find_elements_by_css_selector(self.BUY_BTN))

KrWebDriver.safe_get_box = safe_retry(KrWebDriver.get_box,
                                      attempts=120, retry_time=60)
KrWebDriver.safe_buy_box = safe_retry(KrWebDriver.buy_box,
                                      attempts=10, retry_time=10)
KrWebDriver.safe_box_isavailable = safe_retry(KrWebDriver.box_isavailable,
                                              attempts=10, retry_time=10)

class KrBoxItem(object):
    """docstring for KrBoxItem"""

    def __init__(self, name='N/A', description='N/A', price='N/A'):
        super(KrBoxItem, self).__init__()
        self.name = name
        self.description = description
        self.price = price

    def __str__(self):
        s = u"[%s](%s):\n%s" % (self.name, self.price, self.description)
        return unicode(s)

    def html(self):
        s =  u"<p><strong>%s</p></strong>\n" % self.name
        s += u"<p>%s</p>\n" % self.description
        s += u"<p><em>%s</p></em>\n" % self.price
        return unicode(s)


class KrBox(object):
    """docstring for KrBox"""

    def __init__(self, name='N/A', month='N/A', description='N/A',
                 price='N/A', items=[], url='N/A'):
        super(KrBox, self).__init__()
        self.name = name
        self.month = month
        self.description = description
        self.price = price
        self.box_items = items
        self.url = url

    @property
    def available(self):
        return bool(self.buy_btns)

    def html(self, unsubscribe_url=None):
        s = u"<html><head></head><body>\n"
        s += u"<h2>%s; %s</h2>\n" % (self.name, self.month)
        s += u"<p><em>Цена - %s&nbsp;" % self.price
        s += u"<a href=\"%s\">Купить</a></em></p>\n" % self.url

        if unsubscribe_url:
            s += u"<a href=\"%s\">Не уведомлять об этой коробке</a></em></p>\n" % unsubscribe_url

        s += u"<blockquote>\n"
        s += u"<p>%s</p>\n" % self.description
        s += u"</blockquote>\n"
        for i in self.box_items:
            s += i.html()
        s += u"</body></html>"
        return unicode(s)

    def mail(self, inbasket=False, unsubscribe_url=None):
        msg = MIMEMultipart('alternative')
        msg['Content-Type'] = "text/html; charset=utf-8"
        if inbasket:
            subj = u"[kryginabox] %s в корзине. Есть 1 час чтобы купить" % self.month
        else:
            subj = u"[kryginabox] %s доступна! Иди покупай быстрее" % self.month
        msg['Subject'] = subj

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message,
        # in this case the HTML message, is best and preferred.
        msg.attach(MIMEText(self.text(), 'plain', 'utf-8'))
        msg.attach(MIMEText(self.html(unsubscribe_url), 'html', 'utf-8'))

        return msg

    def __str__(self):
        s = u"[%s: %s](%s)" % (self.month, self.name, self.price)
        return unicode(s)

    def text(self):
        s = u"%s: %s\n" % (self, self.description)
        s += u"\n".join([unicode(i) for i in self.box_items])
        return unicode(s)
