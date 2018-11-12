import copy
import datetime
import json
import logging.config
import os
import random
import re
import sys
import time
import uuid
from datetime import datetime as dt

import jctconv
import requests
from xlrd import open_workbook
from xlrd import XL_CELL_TEXT

import licencemanager

LOG_CONF = "./logging.conf"
logging.config.fileConfig(LOG_CONF)

from bs4 import BeautifulSoup
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

if hasattr(sys, "_MEIPASS"):
    resource_add_path(sys._MEIPASS)

EMPTY = ""
JP = "jp"
JP_CAP = "JP"
NEW = "CATEGORY: NEW"
TOPS_SWEATERS = "TOPS/SWEATERS"
LEAVE_BLANK = "*leave blank*"
SIZE_S = "s"
SIZE_M = "m"
SIZE_L = "l"
SIZE_XL = "xl"
KEY_INDEX = "index"
KEY_ITEM_CODE = "itemCode"
KEY_NAME = "name"
KEY_LOCALE = "locale"
KEY_TITLE = "title"
KEY_MONITOR = "monitor"
KEY_SCHEDULE = "schedule"
KEY_COLOR = "color"
KEY_PAGE = "page"
KEY_CHECKOUT_DELAY_ENABLED = "checkout_delay_enabled"
KEY_CHECKOUT_DELAY_SECONDS = "checkout_delay_seconds"
KEY_PROXY_RATIO = "proxyratio"
KEY_TASK_RATIO = "taskratio"
KEY_TASKS = "tasks"
KEY_EMAIL = "email"
KEY_BILLING = "billing"
KEY_FIRST = "first"
KEY_LAST = "last"
KEY_ADDRESS1 = "address1"
KEY_POST_CODE = "postcode"
KEY_CITY = "city"
KEY_REGION = "region"
KEY_COUNTRY = "country"
KEY_PHONE = "phone"
KEY_CARD = "card"
KEY_TYPE = "type"
KEY_NUMBER = "number"
KEY_MONTH = "month"
KEY_YEAR = "year"
KEY_CODE = "code"
KEY_SIZES = "sizes"
KEY_CHECKOUT_PROFILE = "checkoutprofile"
INDEX_TWITTER = 0
INDEX_EMAIL = 10
INDEX_FIRST_NAME = 3
INDEX_LAST_NAME = 4
INDEX_ADDRESS = 8
INDEX_POST_CODE = 5
INDEX_CITY = 7
INDEX_REGION = 6
INDEX_PHONE = 9
INDEX_PAY_TYPE = 11
INDEX_CARD_NUMBER = 12
INDEX_CARD_LIMIT_MONTH = 13
INDEX_CARD_LIMIT_YEAR = 14
INDEX_CARD_CVV = 15
INDEX_ITEM_NO = 1
INDEX_ITEM_SIZE = 2
VAL_CHECKOUT_DELAY_ENABLED = False
VAL_CHECKOUT_DELAY_SECONDS = 5.0
VAL_PROXY_RATIO = 1
VAL_TASK_RATIO = 1
HEADER_KEY_LIST = [KEY_INDEX, KEY_ITEM_CODE, KEY_NAME, KEY_MONITOR]
HEADER_MONITOR_KEY_LIST = [KEY_PAGE, KEY_TITLE, KEY_COLOR]
SIZE_X_DICT = {
    KEY_INDEX: 0.7, KEY_NAME: 1, KEY_PAGE: 0.3, KEY_TITLE: 0.5, KEY_COLOR: 0.3
}

URL = "http://www.nikeslayer.com/news/category/supremeslayer-keywords/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
}

ID_ITEM_VIEW = "item_view_data"
ID_GET_SITE_INFO_BUTTON = "get_site_info_button"
ID_DUMP_CHECKOUTPROFILES_BUTTON = "dump_checkoutprofiles_button"
ID_DUMP_RELEASEPROFILES_BUTTON = "dump_releaseprofiles_button"
ID_MESSAGE = "message"
ID_MAX_DATA_NUM_PER_FILE = "max_data_num_per_file"

RELEASE_PROFILES_JSON = "releaseprofiles{}.json"
CHECKOUT_PROFILES_JSON = "checkoutprofiles.json"
UTF8 = "utf8"
SATURDAY_INDEX = 5


class JsonMakerScreen(Screen):
    def __init__(self, **kwargs):
        super(JsonMakerScreen, self).__init__(**kwargs)
        self.item_list = []
        self.task_list_dict = {}
        self._file = Window.bind(on_dropfile=self._on_file_drop)
        self.tmp_txt_path = None

    def _on_file_drop(self, window, file_path):
        self.disp_messg("{}を読み込みました".format(os.path.basename(file_path.decode("utf-8"))))
        self.tmp_txt_path = file_path.decode("utf-8")
        self.ids[ID_DUMP_CHECKOUTPROFILES_BUTTON].disabled = False

    def disp_drag_and_drop_msg(self):
        self.disp_messg("Excelファイルをツール画面上にドラッグ&ドロップしてください")

    @staticmethod
    def get_latest_url():
        r = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a"):
            if a.text == "Read more":
                return a.get("href")

    def get_site_info(self):
        self.disp_messg("サイトから最新情報を取得中...")
        self.ids[ID_GET_SITE_INFO_BUTTON].disabled = True
        Clock.schedule_once(self.update_item_view)

    def update_item_view(self, dt):
        try:
            url = self.get_latest_url()
            self.parse_site_info(url)
            scrollview = self.ids["container"]
            scrollview.clear_widgets()
            row_len = len(self.item_list)

            scrollview.height = row_len * 40
            for i in range(row_len):
                self.add_item_info_row(i, scrollview)

            self.disp_messg("サイトから最新情報を取得しました")
        except Exception as e:
            self.disp_messg_err("サイトから最新情報を取得するのに失敗しました。")
            log.exception("Unknown Exception : %s.", e)
        finally:
            self.ids[ID_GET_SITE_INFO_BUTTON].disabled = False

    def add_item_info_row(self, i, scrollview):
        box = BoxLayout()
        item_dict = self.item_list[i]
        self.add_text_widget_on_grid(box, str(i + 1), size_hint_x=0.15)
        for key in HEADER_KEY_LIST:
            if key == KEY_MONITOR:
                mon_dict = item_dict[key]
                for mon_key in HEADER_MONITOR_KEY_LIST:
                    self.add_text_widget_on_grid(box, mon_dict.get(mon_key, ""), size_hint_x=SIZE_X_DICT[mon_key])
            elif key == KEY_ITEM_CODE:
                #self.add_text_widget_on_grid(box, "", "itemCode-" + str(i), size_hint_x=0.3, disabled=False)
                pass
            else:
                self.add_text_widget_on_grid(box, item_dict[key], size_hint_x=SIZE_X_DICT[key])

        scrollview.add_widget(box)

    @staticmethod
    def add_text_widget_on_grid(box, text, id=None, size_hint_x=1, disabled=True):
        text = TextInput(text=text, size_hint_x=size_hint_x, multiline=False, write_tab=False)
        text.id = id
        text.is_focusable = False
        #text.disabled = disabled
        text.disabled_foreground_color = (0, 0, 0, 1)
        text.background_disabled_normal = text.background_normal
        box.add_widget(text)

    @staticmethod
    def get_page(th_list):
        page = th_list[0].text
        if NEW in page:
            page = "new"
        elif page == TOPS_SWEATERS:
            page = "tops_sweaters"
        return page.lower()

    def save_item_info(self, page, td_list):
        has_multi_color = False
        base_name = td_list[0].text
        title = td_list[1].text
        color_list = td_list[2].text.split(",")

        if len(color_list) > 1:
            has_multi_color = True

        for color in color_list:
            item_dict = {}
            item_dict[KEY_INDEX] = "rk_" + str(uuid.uuid4()).replace("-", "")
            monitor_dict = {}
            monitor_dict[KEY_PAGE] = page
            monitor_dict[KEY_TITLE] = title
            color = re.sub("^ ", EMPTY, color)

            if has_multi_color:
                item_dict[KEY_NAME] = "{} {}".format(base_name, color)
            else:
                item_dict[KEY_NAME] = base_name

            item_dict[KEY_LOCALE] = JP

            if color != LEAVE_BLANK:
                monitor_dict[KEY_COLOR] = color

            item_dict[KEY_MONITOR] = monitor_dict
            item_dict[KEY_SCHEDULE] = self.get_next_saturday_epoch()
            item_dict[KEY_CHECKOUT_DELAY_ENABLED] = VAL_CHECKOUT_DELAY_ENABLED
            item_dict[KEY_CHECKOUT_DELAY_SECONDS] = VAL_CHECKOUT_DELAY_SECONDS
            item_dict[KEY_PROXY_RATIO] = VAL_PROXY_RATIO
            item_dict[KEY_TASK_RATIO] = VAL_TASK_RATIO
            self.item_list.append(item_dict)

    def parse_site_info(self, url):
        self.item_list = []
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "lxml")
        for tab in soup.find_all("table"):
            page = None
            for tr in tab.find_all("tr"):
                th_list = tr.find_all("th")
                if len(th_list) > 0:
                    page = self.get_page(th_list)

                td_list = tr.find_all("td")
                if len(td_list) > 0:
                    self.save_item_info(page, td_list)

    def dump_checkoutprofiles(self):
        try:
            self.dump_checkoutprofile_core()
        except Exception as e:
            self.disp_messg_err("checkoutprofiles.jsonを出力に失敗しました。")
            log.exception("checkoutprofiles.jsonの出力に失敗しました。%s", e)

    def dump_checkoutprofile_core(self):
        self.task_list_dict = {}
        address_list = []
        dump_cnt = 0
        workbook = open_workbook(self.tmp_txt_path)
        sheet = workbook.sheet_by_index(0)
        for i in range(1, sheet.nrows):
            row = sheet.row(i)
            log.info(row)
            address_dict = {}
            index = "ckk_" + str(uuid.uuid4()).replace("-", "")
            address_dict[KEY_INDEX] = index

            if self.is_not_address_record(row):
                log.info("{}行目に必須項目未入力のセルがありました。この行の取り込みをスキップします".format(i + 1))
                continue

            address_dict[KEY_NAME] = row[INDEX_TWITTER].value
            address_dict[KEY_LOCALE] = JP
            address_dict[KEY_EMAIL] = row[INDEX_EMAIL].value
            address_dict[KEY_BILLING] = self.mk_bill_dict(row)
            address_dict[KEY_CARD] = self.mk_card_dict(row)

            size = self.format_size(str(row[INDEX_ITEM_SIZE].value))
            if size is None:
                log.info("{}行目のサイズ値が不正です。この行の取り込みをスキップします".format(i + 1))
                continue

            address_list.append(address_dict)
            dump_cnt += 1

            self.append_task_list(index, row, size)

        with open(CHECKOUT_PROFILES_JSON, "w", encoding=UTF8) as f:
            f.write(json.dumps(address_list, indent=2, ensure_ascii=False))

        self.ids[ID_DUMP_RELEASEPROFILES_BUTTON].disabled = False
        self.disp_messg("{}行のレコードをcheckoutprofiles.jsonに出力しました".format(dump_cnt))

    def append_task_list(self, index, row, size):
        item_no = int(row[INDEX_ITEM_NO].value)
        task_list = self.task_list_dict.get(item_no)
        if task_list is None:
            task_list = []
            self.task_list_dict[item_no] = task_list
        task_dict = {}
        task_dict[KEY_SIZES] = [size]
        task_dict[KEY_CHECKOUT_PROFILE] = index
        task_list.append(task_dict)

    def mk_card_dict(self, row):
        card_dict = {}
        if row[INDEX_PAY_TYPE].value == "代金引換":
            card_dict[KEY_TYPE] = "cashondelivery"
        else:
            card_dict[KEY_TYPE] = row[INDEX_PAY_TYPE].value.replace(" ", "").lower()
            card_dict[KEY_NUMBER] = row[INDEX_CARD_NUMBER].value
            card_dict[KEY_MONTH] = int(row[INDEX_CARD_LIMIT_MONTH].value)
            card_dict[KEY_YEAR] = int("20{}".format(int(row[INDEX_CARD_LIMIT_YEAR].value)))

            if row[INDEX_CARD_CVV].ctype == XL_CELL_TEXT:
                card_dict[KEY_CODE] = row[INDEX_CARD_CVV].value
            else:
                card_dict[KEY_CODE] = str(int(row[INDEX_CARD_CVV].value))

        return card_dict

    @staticmethod
    def mk_bill_dict(row):
        bill_dict = {}
        bill_dict[KEY_FIRST] = row[INDEX_FIRST_NAME].value
        bill_dict[KEY_LAST] = row[INDEX_LAST_NAME].value
        bill_dict[KEY_ADDRESS1] = row[INDEX_ADDRESS].value

        if row[INDEX_POST_CODE].ctype == XL_CELL_TEXT:
            bill_dict[KEY_POST_CODE] = row[INDEX_POST_CODE].value
        else:
            bill_dict[KEY_POST_CODE] = str(int(row[INDEX_POST_CODE].value))

        bill_dict[KEY_CITY] = row[INDEX_CITY].value
        bill_dict[KEY_REGION] = row[INDEX_REGION].value
        bill_dict[KEY_COUNTRY] = JP_CAP
        bill_dict[KEY_PHONE] = row[INDEX_PHONE].value
        return bill_dict

    @staticmethod
    def is_not_address_record(row):
        if row[INDEX_TWITTER].value == EMPTY or row[INDEX_EMAIL].value == EMPTY \
                or row[INDEX_FIRST_NAME].value == EMPTY or row[INDEX_LAST_NAME].value == EMPTY \
                or row[INDEX_ADDRESS].value == EMPTY or row[INDEX_POST_CODE].value == EMPTY \
                or row[INDEX_CITY].value == EMPTY or row[INDEX_REGION].value == EMPTY \
                or row[INDEX_PHONE].value == EMPTY or row[INDEX_PAY_TYPE].value == EMPTY:
            return True

        if row[INDEX_PAY_TYPE].value != "代金引換":
            if row[INDEX_PAY_TYPE].value == EMPTY or row[INDEX_CARD_NUMBER].value == EMPTY \
                    or row[INDEX_CARD_LIMIT_MONTH].value == EMPTY or row[INDEX_CARD_LIMIT_YEAR].value == EMPTY \
                    or row[INDEX_CARD_CVV].value == EMPTY:
                return True

        return False

    def disp_messg(self, msg):
        self.ids[ID_MESSAGE].text = msg
        self.ids[ID_MESSAGE].color = (0, 0, 0, 1)

    def disp_messg_err(self, msg):
        self.ids[ID_MESSAGE].text = "{}詳細はログファイルを確認してください。".format(msg)
        self.ids[ID_MESSAGE].color = (1, 0, 0, 1)

    @staticmethod
    def format_size(size):
        size = jctconv.normalize(size.lower())
        if size == EMPTY:
            return "random_random"
        elif size == SIZE_S or size == SIZE_M or size == SIZE_L or size == SIZE_XL:
            return "shirtsother_{}".format(size)
        elif "/" in size:
            return None
        else:
            size = float(size)
            if size % 1.0 == 0.0:
                size = int(size)

            if size < 28:
                return "shoes_{}".format(size)
            else:
                return "pants_{}".format(size)

    @staticmethod
    def conv_0_to_empty(num):
        if num == 0:
            return ""
        else:
            return num

    def dump_releaseprofiles(self):
        try:
            self.dump_releaseprofiles_core()
        except Exception as e:
            self.disp_messg_err("releaseprofiles.jsonを出力に失敗しました。")
            log.exception("releaseprofiles.jsonの出力に失敗しました。%s", e)

    def dump_releaseprofiles_core(self):

        dump_item_list = []
        max_data_num_per_file = int(self.ids[ID_MAX_DATA_NUM_PER_FILE].text)
        order_num = 0
        dumped_num = 0

        for i in range(len(self.item_list)):
            item_dict = self.item_list[i]
            #item_no = self.get_item_no(i)
            #if item_no is None:
            #    continue

            task_list = self.task_list_dict.get(i + 1)
            if task_list is None:
                continue

            if order_num + len(task_list) <= max_data_num_per_file:
                item_dict[KEY_TASKS] = task_list
                dump_item_list.append(item_dict)
                order_num += len(task_list)
                if max_data_num_per_file <= order_num:
                    self.write_release_profiles_json(dump_item_list, dumped_num)
                    dumped_num += 1
                    dump_item_list = []
                    order_num = 0
            else:
                item_dict_without_task = copy.deepcopy(item_dict)
                split_task_list = []
                for task in task_list:
                    split_task_list.append(task)
                    order_num += 1
                    if order_num >= max_data_num_per_file:
                        item_dict[KEY_TASKS] = split_task_list
                        dump_item_list.append(item_dict)
                        self.write_release_profiles_json(dump_item_list, dumped_num)
                        dumped_num += 1
                        order_num = 0
                        dump_item_list = []
                        split_task_list = []
                        item_dict = item_dict_without_task
                        item_dict_without_task = copy.deepcopy(item_dict)

                if 0 < len(split_task_list):
                    item_dict[KEY_TASKS] = split_task_list
                    dump_item_list.append(item_dict)

        if 0 < order_num:
            self.write_release_profiles_json(dump_item_list, dumped_num)
            dumped_num += 1

        self.disp_messg("releaseprofiles.jsonを{}ファイル出力しました".format(dumped_num))

    @staticmethod
    def get_next_saturday_epoch():
        today = dt.today()
        add_day = SATURDAY_INDEX - today.weekday()
        if add_day < 0:
            add_day = 6
        next_day = today + datetime.timedelta(days=add_day)

        sec = random.randint(20, 50)
        next_date_str = "{}-{}-{} 10:59:{}".format(next_day.year, next_day.month, next_day.day, sec)
        next_date = dt.strptime(next_date_str, '%Y-%m-%d %H:%M:%S')
        epoch = int(time.mktime(next_date.timetuple())) + (9 * 3600)
        return str(epoch)

    def write_release_profiles_json(self, dump_item_list, dumped_num):
        with open(RELEASE_PROFILES_JSON.format(self.conv_0_to_empty(dumped_num)), "w", encoding=UTF8) as f:
            f.write(json.dumps(dump_item_list, indent=2, ensure_ascii=False))

    def get_item_no(self, no):
        for widget in self.walk():
            if widget.id == "itemCode-{}".format(no):
                return widget.text


class JsonMakerApp(App):
    title = "大和型slayer補助ツール"

    def build(self):
        return JsonMakerScreen()


def setup_config():
    Config.set('modules', 'inspector', '')  # Inspectorを有効にする
    Config.set('graphics', 'width', 1280)  # Windowの幅を1280にする
    Config.set('graphics', 'maxfps', 20)  # フレームレートを最大で20にする
    Config.set('graphics', 'resizable', 0)  # Windowの大きさを変えられなくする
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    Config.write()


def match_license():
    return licencemanager.match_license()


if __name__ == '__main__':

    log = logging.getLogger('my-log')

    if not match_license():
        log.error("ライセンスエラー。プログラムを終了します。")
        sys.exit(-1)

    setup_config()
    LabelBase.register(DEFAULT_FONT, "ipaexg.ttf")
    JsonMakerApp().run()

