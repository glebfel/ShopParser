import json
import os
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, \
    StaleElementReferenceException, WebDriverException
from db import WriteToDatabase


class OzonParser:
    MAIN_URL = "https://www.ozon.ru/"
    PATH = "config.conf"

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
            self.driver.get(self.MAIN_URL)
            categories = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='g3s e4c c5e']")))
            category_links = [category.get_attribute('href') for category in categories]
            return category_links
        except Exception as e:
            print(e)

    def get_subcategory_links(self, category_link):
        """
        Gets subcategory links in given category
        :param category_link: given category link
        :return: list of subcategory links
        """
        self.driver.get(category_link + "?sorting=rating")
        try:
            categories = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='s7s']")))
            categories = categories.find_elements(By.TAG_NAME, "a")
            category_links = [category.get_attribute('href') for category in categories]
            return category_links
        except:
            pass

    def get_items_links(self, subcategory_link):
        """
        Gets all item's links in given page in the category (by link)
        :param subcategory_link: given subcategory link
        :return: list of item's links in given page
        """
        links = []
        items = True
        next_button = True
        first_time = False
        # iterates through all pages while button "Дальше" available
        self.driver.get(subcategory_link)
        # take a restriction of 600 for the number of products due to long time process
        while next_button and items and len(links) < 600:
            try:
                next_button = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='ui-b3']")))
                if len(next_button) > 1:
                    next_button = next_button[1]
                else:
                    if self.driver.current_url == subcategory_link and first_time:
                        break
                    next_button = next_button[0]
                first_time = True
                # only for products category - //a[@class='tile-hover-target li9']
                next_button.send_keys(Keys.PAGE_DOWN)
                items = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='tile-hover-target i5m']")))
                links.extend([_.get_attribute('href') for _ in items])
                self.driver.get(next_button.get_attribute('href'))
            except:
                self.driver.execute_script(f"window.scrollTo(0, {1080})")
                items = self.driver.find_elements(By.XPATH, "//a[@class='tile-hover-target i5m']")
                links.extend([_.get_attribute('href') for _ in items])
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
        try:
            prop_str = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='section-characteristics']")))
            prop_str = prop_str.find_elements(By.TAG_NAME, "dl")
            text = ""
            for i in prop_str:
                text += i.text.replace("\'", "") + "\n"
            prop_str = text.replace(":", "\n").split("\n")
            for i in range(0, len(prop_str) - 1, 2):
                properties.update({prop_str[i]: prop_str[i + 1]})
            try:
                r_description = WebDriverWait(self.driver, 3).until(
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
                description = description.replace("\"", "").replace("\'", "").replace("Описание\n", "").replace("Показать полностью", "")
                headers = r_description[1].find_elements(By.TAG_NAME, "h3")
                desc = r_description[1].find_elements(By.TAG_NAME, "p")
                if len(headers) == len(desc):
                    for i in range(len(headers)):
                        properties.update({headers[i].text.replace("\'", "") : desc[i].text.replace("\'", "")})
            # extract ozon_id
            ozon_id = item_link.split('/')
            ozon_id = ozon_id[len(ozon_id) - 2].split('-')
            ozon_id = ozon_id[len(ozon_id) - 1]
            # extract price
            price = ""
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='wk9 w9k']").text
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='wk9']").text
            except:
                pass
            price = price.split("₽")[0]
            price = price.replace(" ", "")
            # extract product score
            r_sum = 0
            score = "Нет оценок"
            try:
                self.driver.execute_script(f"window.scrollTo(0, {3*1080})")
                score = self.driver.find_element(By.XPATH,"(//div[@data-widget='webReviewProductScore'])[3]").text
                score = score.split("\n")
                for i in range(1, len(score) - 1, 2):
                    properties.update({score[i]: score[i + 1]})
                    r_sum += int(score[i + 1])
                score = score[0].split("/")[0]
            except:
                pass
            properties.update(
                [("Количество отзывов", r_sum), ("Оценка", score), ("Описание", description), ("ozone_id", ozon_id),
                 ("Цена (руб.)", price), ("Ссылка", item_link)])
            return properties
        except Exception as e:
            print(e)

    def get_subcategory_items(self, subcategory_link):
        """
        Gets all items in given subcategory
        :param subcategory_link: given subcategory link
        :return: list of name od subcategory and list of dicts contains items info
        """
        name = subcategory_link.split("/")[4]
        name = name.split("-")
        if len(name) > 1:
            n_name = ""
            for i in range(len(name) - 1):
                n_name += name[i] + "_"
            name = n_name[0:len(n_name) - 1]
        else:
            name = name[0]
        subcategory = []
        # iterates through all pages while button "Дальше" available
        links = self.get_items_links(subcategory_link)
        for item in links:
            try:
                subcategory.append(self.get_item_info(item))
            except (TimeoutException,StaleElementReferenceException, WebDriverException) as t:
                print(f"Exception while parsing item was caught:\n{item}")
            except NoSuchWindowException as n:
                print(n)
                return
        return [name, subcategory, subcategory_link]

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
    def json_item_backup(item):
        """
        Prepares backup for parsed data
        """
        if not os.path.isdir("json_backup"):
            os.mkdir("json_backup")
        with open(f"json_backup/{item['Ссылка'].split('/')[5]}.json", "w") as write_file:
            json.dump(item, write_file)
        print(f"json backup of {item['Ссылка'].split('/')[5]} item was successfully created in 'json_backup' folder!")

    @staticmethod
    def json_backup(category):
        """
        Prepares backup for parsed data
        """
        if not os.path.isdir("json_backup"):
            os.mkdir("json_backup")
        with open(f"json_backup/{category[0]}.json", "w") as write_file:
            json.dump(category, write_file)
        print(f"json backup of {category[0]} category was successfully created in 'json_backup' folder!")

    def parse_category(self, link):
        sub_links = self.get_subcategory_links(link)
        for s in sub_links:
            if not self.check_if_parsed(s):
                subcategory = self.get_subcategory_items(s)
                self.json_backup(subcategory)
                WriteToDatabase.write_to_db(self.PATH, subcategory)
                self.add_parsed_category(s)
        print(f"category was successfully parsed!")
        self.driver.quit()

    def parse_site(self):
        categories = self.get_category_links()
        for c in categories:
            sub_links = self.get_subcategory_links(c)
            for s in sub_links:
                if not self.check_if_parsed(s):
                    subcategory = self.get_subcategory_items(s)
                    self.json_backup(subcategory)
                    WriteToDatabase.write_to_db(self.PATH, subcategory)
                    self.add_parsed_category(s)
        print(f"site was successfully parsed!")
        self.driver.quit()
