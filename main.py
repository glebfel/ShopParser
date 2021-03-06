import json
import requests
import os
import time
import validators
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException
from db import WriteToDatabase


class ParseTools:

    # auxiliary methods for parsing process optimization
    @staticmethod
    def add_parsed_category(link):
        """
        serialize parsed categories
        :param link: link of the category
        """
        with open(f"parsed_categories.txt", "a") as f:
            f.write(link + "\n")

    @staticmethod
    def check_if_parsed(link):
        """
        Check if category was serialized
        :param link: link of the category
        :return: boolean value
        """
        with open(f"parsed_categories.txt", "r") as f:
            s_text = f.read()
        if link in s_text:
            return True
        return False

    @staticmethod
    def get_name_from_link(link):
        """
        Get name of category from link
        :param link: string type link
        :return: string type name
        """
        if 'ozon' in link:
            name = link.split("/")[4]
            name = name.split("-")
            if len(name) > 1:
                n_name = ""
                for i in range(len(name) - 1):
                    n_name += name[i] + "_"
                name = n_name[0:len(n_name) - 1]
            else:
                name = name[0]
        elif 'wildberries' in link:
            name = link.split("/")[4]
        return name

    @staticmethod
    def json_item_backup(item):
        """
        Prepares backup for parsed data
        """
        if not os.path.isdir("json_backup"):
            os.mkdir("json_backup")
        if 'ozon' in item['Ссылка']:
            if not os.path.isdir("json_backup/ozon"):
                os.mkdir("json_backup/ozon")
            with open(f"json_backup/ozon/{item['Ссылка'].split('/')[4]}.json", "w") as write_file:
                json.dump(item, write_file)
            print(f"JSON-backup of {item['Ссылка'].split('/')[4]} item was successfully created in 'json_backup' folder!")
        elif 'wildberries' in item['Ссылка']:
            if not os.path.isdir("json_backup/wildberries"):
                os.mkdir("json_backup/wildberries")
            with open(f"json_backup/wildberries/{item['Ссылка'].split('/')[4]}.json", "w") as write_file:
                json.dump(item, write_file)
            print(f"JSON-backup of {item['Ссылка'].split('/')[4]} item was successfully created in 'json_backup' directory!")

    @classmethod
    def json_backup(cls, category, subcategory):
        """
        Prepares backup for parsed data
        :param subcategory: list of dicts of items in given subcategory
        :param category: string with link of global category
        """
        if not os.path.isdir("json_backup"):
            os.mkdir("json_backup")
        name_cat = ParseTools.get_name_from_link(category)
        name_subcat = subcategory[0]
        if 'ozon' in subcategory[2]:
            if not os.path.isdir("json_backup/ozon"):
                os.mkdir("json_backup/ozon")
            if name_cat == name_subcat:
                with open(f"json_backup/ozon/{name_subcat}.json", "w") as write_file:
                    json.dump(subcategory[1], write_file)
            else:
                if not os.path.isdir(f"json_backup/ozon/{name_cat}"):
                    os.mkdir(f"json_backup/ozon/{name_cat}")
                with open(f"json_backup/ozon/{name_cat}/{name_subcat}.json", "w") as write_file:
                    json.dump(subcategory[1], write_file)
        elif 'wildberries' in subcategory[2]:
            if not os.path.isdir("json_backup/wildberries"):
                os.mkdir("json_backup/wildberries")
            if name_cat == name_subcat:
                with open(f"json_backup/wildberries/{name_subcat}.json", "w") as write_file:
                    json.dump(subcategory[1], write_file)
            else:
                if not os.path.isdir(f"json_backup/wildberries/{name_cat}"):
                    os.mkdir(f"json_backup/wildberries/{name_cat}")
                with open(f"json_backup/wildberries/{name_cat}/{name_subcat}.json", "w") as write_file:
                    json.dump(subcategory[1], write_file)
        print(f"JSON-backup of {name_subcat} category was successfully created in 'json_backup' directory!")


class OzonParser:
    MAIN_URL = 'https://www.ozon.ru'

    headers = {
        'accept': '* / *',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'}

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--incognito")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(15)

    def get_category_links(self):
        """
        Gets categories and their links for later parsing
        :return: list of category links
        """
        try:
            page = requests.get(self.MAIN_URL, headers=self.headers).text
            bs = BeautifulSoup(page, 'lxml')
            categories = bs.find("div", id="stickyHeader").findAll("a")
            category_links = [self.MAIN_URL + category.get('href') + "?sorting=score" for category in categories]
            category_links = [c for c in category_links if 'category' in c and validators.url(c)]
            return category_links
        except Exception as e:
            print(e)

    def get_subcategory_links(self, category_link):
        """
        Gets subcategory links in given category
        :param category_link: given category link
        :return: list of subcategory links
        """
        self.driver.get(category_link + "?sorting=score")
        try:
            categories = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='s2t']")))
            categories = categories.find_elements(By.TAG_NAME, "a")
            category_links = [category.get_attribute('href') for category in categories]
            return category_links
        except:
            pass
        return [category_link]

    def get_items_links(self, page_link):
        """
        Gets all item's links in given page in the category (by link)
        :param page_link: given subcategory link
        :return: list of item's links in given page
        """
        links = []
        items = True
        self.driver.get(page_link)
        # take a restriction of 1000 for the number of products due to long time process
        counter = 1
        while items and len(links) < 800:
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                items = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-widget='searchResultsV2']")))
                items = items.find_elements(By.TAG_NAME, 'a')
                items = [_.get_attribute('href') for _ in items]
                items = [_ for _ in items if 'comments--offset-80' not in _]
                items = list(dict.fromkeys(items))
                links.extend(items)
                counter+=1
                link = page_link.replace('?sorting=score', '') + f'?page={counter}&sorting=score'
                self.driver.get(link)
            except:
                break
        return links

    def get_item_info(self, item_link):
        """
        Gets info from description of an item
        :param item_link: given item's link
        :return: dict with parsed info of an item
        """
        properties = {}
        r_description = []
        self.driver.get(item_link)
        prop_str = WebDriverWait(self.driver, 1).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='section-characteristics']")))
        prop_str = prop_str.find_elements(By.TAG_NAME, "dl")
        text = ""
        for i in prop_str:
            text += i.text.replace("\'", "").replace("₽", "") + "\n"
        prop_str = text.replace(":", "\n").split("\n")
        for i in range(0, len(prop_str) - 1, 2):
            properties.update({prop_str[i]: prop_str[i + 1]})
        try:
            r_description = WebDriverWait(self.driver, 1).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@id='section-description']")))
        except:
            pass
        if len(r_description) == 0:
            description = ""
        elif len(r_description) == 1:
            description = r_description[0].text
            description = description.replace("\"", "").replace("\'", "").replace("Описание\n", "")
        elif len(r_description) == 2:
            description = r_description[0].text
            description = description.replace("\"", "").replace("\'", "").replace("Описание\n", "").replace(
                "Показать полностью", "")
            headers = r_description[1].find_elements(By.TAG_NAME, "h3")
            desc = r_description[1].find_elements(By.TAG_NAME, "p")
            if len(headers) == len(desc):
                for i in range(len(headers)):
                    properties.update({headers[i].text.replace("\'", ""): desc[i].text.replace("\'", "")})

        # extract ozon_id
        ozon_id = item_link.split('/')
        ozon_id = ozon_id[len(ozon_id) - 2].split('-')
        ozon_id = ozon_id[len(ozon_id) - 1]

        # extract subcategory
        subcategory = ""
        try:
            subcategory = self.driver.find_element(By.XPATH, "//div[@data-widget='breadCrumbsPdp']").text
            subcategory = subcategory.split('\n')[1]
        except:
            pass
        try:
            subcategory = self.driver.find_element(By.XPATH, "//div[@data-widget='breadCrumbs']").text
            subcategory = subcategory.split('\n')[1]
        except:
            pass

        # extract name of the item
        name = self.driver.find_element(By.XPATH, "//div[@data-widget='webProductHeading']").text
        name = name.replace("\"", "").replace("\'", "")
        # extract price
        price = ""
        price = self.driver.find_element(By.XPATH, "//div[@data-widget='webPrice']").text
        price = price.split("₽")[0]
        price = price.replace(" ", "")
        # extract product score
        r_sum = 0
        score = ""
        try:
            self.driver.execute_script(f"window.scrollTo(0, {4 * 1080})")
            score = WebDriverWait(self.driver, 1).until(
            EC.presence_of_element_located((By.XPATH, "(//div[@data-widget='webReviewProductScore'])[3]"))).text
            score = score.split("\n")
            for i in range(1, len(score) - 1, 2):
                properties.update({score[i]: score[i + 1]})
                r_sum += int(score[i + 1])
            score = score[0].split("/")[0]
            if 'Нет оценок' in score:
                score = ""
        except:
            pass
        properties.update(
            [("Название", name), ("Количество отзывов", r_sum), ("Оценка", score), ("Описание", description),
             ("ozone_id", ozon_id),
             ("Цена (руб.)", price), ("Ссылка", item_link), ("Подкатегория", subcategory)])
        return properties

    def get_subcategory_items(self, subcategory_link):
        """
        Gets all items in given subcategory
        :param subcategory_link: given subcategory link
        :return: list containing name of subcategory, list of dicts contains items info and link of the subcategory
        """
        name = ParseTools.get_name_from_link(subcategory_link)
        subcategory = []
        # iterates through all pages while button "Дальше" available
        links = self.get_items_links(subcategory_link)
        for item in links:
            try:
                subcategory.append(self.get_item_info(item))
            except NoSuchWindowException as n:
                print(n)
                return
            except Exception as e:
                pass
                # print(e)
                # print(f"Exception while parsing item was caught:\n{item}")
        return [name, subcategory, subcategory_link]

    def parse_category(self, link):
        sub_links = self.get_subcategory_links(link)
        for s in sub_links:
            if not ParseTools.check_if_parsed(s):
                subcategory = self.get_subcategory_items(s)
                ParseTools.json_backup(link, subcategory)
                WriteToDatabase.write_to_db(subcategory)
                ParseTools.add_parsed_category(s)
            else:
                print(
                    f"The category: {s} is already parsed at {time.ctime(os.path.getmtime('parsed_categories.txt'))}!\nDo "
                    f"you want to update the data or to pass it?")
                print("Enter 'Y' to update or any key to continue")
                key = input()
                if key == 'y' or key == 'Y':
                    subcategory = self.get_subcategory_items(s)
                    ParseTools.json_backup(link, subcategory)
                    WriteToDatabase.update_to_db(subcategory)
        print(f"Category was successfully parsed!")
        self.driver.quit()

    def parse_site(self):
        categories = self.get_category_links()
        for c in categories:
            if not ParseTools.check_if_parsed(c):
                subcategory = self.get_subcategory_items(c)
                ParseTools.json_backup(c, subcategory)
                ParseTools.add_parsed_category(c)
            else:
                print(
                    f"The category: {c} is already parsed at {time.ctime(os.path.getmtime('parsed_categories.txt'))}!\nDo "
                    f"you want to update the data or to pass it?")
                print("Enter 'Y' to update or any key to continue")
                key = input()
                if key == 'y' or key == 'Y':
                    subcategory = self.get_subcategory_items(c)
                    ParseTools.json_backup(c, subcategory)
                    WriteToDatabase.update_to_db(subcategory)
        print(f"Site was successfully parsed!")
        self.driver.quit()


class WildberriesParser:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--incognito")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(15)

    def get_category_links(self):
        """
        Gets categories and their links for later parsing
        :return: list of category links
        """
        try:
            r = requests.get("https://www.wildberries.ru/gettopmenuinner?lang=ru").json()
            r = r['value']['menu']
            categories = []
            for _ in r:
                if 'catalog' in _['pageUrl']:
                    categories.append("https://www.wildberries.ru" + _['pageUrl'])
            return categories
        except Exception as e:
            print(e)

    def get_subcategory_links(self, category_link):
        """
        Gets subcategory links in given category
        :param category_link: given category link
        :return: list of subcategory links
        """
        try:
            self.driver.get(category_link)
            subcategories = []
            try:
                subcategories = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//ul[@class='menu-catalog__list-2 maincatalog-list-2']")))
            except:
                pass
            try:
                subcategories = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//li[@class='selected hasnochild']//ul")))
            except:
                pass
            if not subcategories:
                return [category_link]
            subcategories = subcategories.find_elements(By.TAG_NAME, "a")
            subcategory_links = [c.get_attribute('href') for c in subcategories]
            return subcategory_links
        except Exception as e:
            print(e)

    def get_items_links(self, page_link):
        """
        Gets all item's links in given page in the category (by link)
        :param page_link: given subcategory link
        :return: list of item's links in given page
        """
        links = []
        items = True
        next_button = True
        # iterates through all pages while button "Дальше" available
        self.driver.get(page_link)
        # take a restriction of 1000 for the number of products due to long time process
        while next_button and items and len(links) < 700:
            try:
                next_button = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Следующая страница')]")))
                next_button.send_keys(Keys.PAGE_DOWN)
                items = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='product-card__main j-card-link']")))
                links.extend([_.get_attribute('href') for _ in items])
                self.driver.get(next_button.get_attribute('href'))
            except:
                break
        return links

    def get_item_info(self, item_link):
        """
        Gets info from description of an item
        :param item_link: given item's link
        :return: dict with parsed info of an item
        """
        self.driver.get(item_link)
        properties = {}
        id = item_link.split("/")[4]
        r = requests.get(f"https://wbx-content-v2.wbstatic.net/ru/{id}.json").json()
        n_list = ['imt_id', 'subj_root_name', 'grouped_options', 'colors', 'full_colors', 'tnved', 'media', 'data', 'sizes_table']
        for _ in r:
            if _ == 'kinds':
                properties.update({_: r[_][0]})
            elif _ not in n_list:
                if isinstance(r[_], list):
                    for i in r[_]:
                        if 'name' in i and 'value' in i:
                            if 'measure' in i:
                                properties.update({f"{i['name']} ({i['measure']})": i['value']})
                            else:
                                properties.update({i['name']: i['value']})
                else:
                    properties.update({_: r[_]})

        # parse product price
        price = requests.get(f"https://wbxcatalog-ru.wildberries.ru/nm-2-card/catalog?spp=0&regions=64,83,4,38,33,70,82,"
                         f"75,30,69,86,40,22,1,31,66,48,71,80,68&stores=117673,122258,122259,125238,125239,125240,"
                         f"6159,507,3158,117501,120602,120762,6158,121709,124731,159402,2737,130744,117986,1733,686,"
                         f"132043&pricemarginCoeff=1.0&reg=0&appType=1&offlineBonus=0&onlineBonus=0&emp=0&locale=ru"
                         f"&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&dest=-1029256,-102269,-1278703,"
                         f"-1255563&nm={id}").json()
        price = price['data']['products'][0]['salePriceU']
        # parse product score
        self.driver.execute_script(f"window.scrollTo(0, {3 * 1080})")
        average_score = 0
        score_number = 0
        five_score_num = 0
        four_score_num = 0
        three_score_num = 0
        two_score_num = 0
        one_score_num = 0
        try:
            score = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='user-scores__rating']"))).text
            print("+")
            score = score.split("\n")
            average_score = score[0]
            score_number = score[1].split(" ")[2]
            five_score_num = round(int(score_number)*int(score[3].replace("%", ""))/100)
            four_score_num = round(int(score_number)*int(score[5].replace("%", ""))/100)
            three_score_num = round(int(score_number)*int(score[7].replace("%", ""))/100)
            two_score_num = round(int(score_number)*int(score[9].replace("%", ""))/100)
            one_score_num = round(int(score_number)*int(score[11].replace("%", ""))/100)
        except Exception as e:
            pass
        properties.update(
            [("price", price), ("link", item_link), ("average_score", average_score), ("score_number", score_number), ("five_score_num", five_score_num),
             ("four_score_num", four_score_num),
             ("three_score_num", three_score_num), ("two_score_num", two_score_num), ("one_score_nu", one_score_num)])
        return properties

    def get_subcategory_items(self, subcategory_link):
        """
        Gets all items in given subcategory
        :param subcategory_link: given subcategory link
        :return: list containing name of subcategory, list of dicts contains items info and link of the subcategory
        """
        name = ParseTools.get_name_from_link(subcategory_link)
        subcategory = []
        # iterates through all pages while button "Дальше" available
        links = self.get_items_links(subcategory_link)
        for item in links:
            try:
                subcategory.append(self.get_item_info(item))
            except NoSuchWindowException as n:
                print(n)
                return
            except Exception:
                print(f"Exception while parsing item was caught:\n{item}")
        return [name, subcategory, subcategory_link]

    def parse_category(self, link):
        sub_links = self.get_subcategory_links(link)
        for s in sub_links:
            if not ParseTools.check_if_parsed(s):
                subcategory = self.get_subcategory_items(s)
                ParseTools.json_backup(link, subcategory)
                WriteToDatabase.write_to_db(subcategory)
                ParseTools.add_parsed_category(s)
            else:
                print(
                    f"The subcategory: {s} in category {link} is already parsed at {time.ctime(os.path.getmtime('parsed_categories.txt'))}!\nDo "
                    f"you want to update the data or to pass it?")
                print("Enter 'Y' to update or any key to continue")
                key = input()
                if key == 'y' or key == 'Y':
                    subcategory = self.get_subcategory_items(s)
                    ParseTools.json_backup(link, subcategory)
                    WriteToDatabase.update_to_db(subcategory)
        print(f"Category was successfully parsed!")
        self.driver.quit()

    def parse_site(self):
        categories = self.get_category_links()
        for c in categories:
            sub_links = self.get_subcategory_links(c)
            for s in sub_links:
                if not ParseTools.check_if_parsed(s):
                    subcategory = self.get_subcategory_items(s)
                    ParseTools.json_backup(c, subcategory)
                    WriteToDatabase.write_to_db(subcategory)
                    ParseTools.add_parsed_category(s)
                else:
                    print(
                        f"The subcategory: {s} is already parsed at {time.ctime(os.path.getmtime('parsed_categories.txt'))}!\nDo "
                        f"you want to update the data or to pass it?")
                    print("Enter 'Y' to update or any key to continue")
                    key = input()
                    if key == 'y' or key == 'Y':
                        subcategory = self.get_subcategory_items(s)
                        ParseTools.json_backup(c, subcategory)
                        WriteToDatabase.update_to_db(subcategory)
        print(f"Site was successfully parsed!")
        self.driver.quit()
