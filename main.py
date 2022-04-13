import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from db import WriteToDatabase


class OzonParser:
    MAIN_URL = "https://www.ozon.ru/"
    PATH = "config.conf"

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--dns-prefetch-disable")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)

    def get_category_links(self):
        """
        Gets categories and their links for later parsing
        :return: list of category links
        """
        try:
            self.driver.get(self.MAIN_URL)
            self.driver.find_element(By.XPATH, "//div[@class='c1e']").click()
            categories = self.driver.find_element(By.XPATH, "//div[@class='e1c']").find_elements(By.TAG_NAME, "a")
            category_links = [category.get_attribute('href') for category in categories[0:31]]
            return category_links
        except NoSuchElementException as e:
            print("Exception in 'get_category_links' method: \n" + e)

    def get_subcategory_links(self, category_link):
        """
        Gets subcategory links in given category
        :param category_link: given category link
        :return: list of subcategory links
        """
        self.driver.get(category_link + "?sorting=rating")
        try:
            categories = self.driver.find_elements(By.XPATH, "//a[@class='rz7']")
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
        try:
            links = []
            items = []
            # iterates through all pages while button "Дальше" available
            next_button = True
            self.driver.get(subcategory_link)
            # take a restriction of 1200 for the number of products due to long time process
            while next_button and len(links) < 500:
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, "//a[@class='ui-c3']")))
                    next_button = self.driver.find_elements(By.XPATH, "//a[@class='ui-c3']")
                    if len(next_button) > 1:
                        next_button = self.driver.find_elements(By.XPATH, "(//a[@class='ui-c3'])[2]")
                except:
                    next_button = False
                try:
                    items = self.driver.find_elements(By.XPATH, "//a[@class='tile-hover-target li9']")
                except:
                    pass
                links.extend([_.get_attribute('href') for _ in items])
                if next_button:
                    next_button[0].click()
            return links
        except NoSuchElementException as e:
            print(e)

    def get_item_info(self, item_link):
        """
        Gets info from description of an item
        :param item_link: given item's link
        :return: dict with parsed info of an item
        """
        properties = {}
        r_description = []
        complectation = ""
        self.driver.get(item_link)
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//dl[@class='tj2']")))
            prop_str = self.driver.find_elements(By.XPATH, "//dl[@class='tj2']")
            text = ""
            for i in prop_str:
                text += i.text + "\n"
            prop_str = text.split("\n")
            prop_str = list(dict.fromkeys(prop_str))
            for i in range(1, len(prop_str) - 1, 2):
                properties.update({prop_str[i - 1]: prop_str[i]})
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@id='section-description']//div//div[@class='n1k']")))
                r_description = self.driver.find_elements(By.XPATH,
                                                          "//div[@id='section-description']//div//div[@class='n1k']")
            except:
                pass
            if len(r_description) == 0:
                description = ""
            elif len(r_description) == 1:
                description = r_description[0].text
                description = description.replace("\"", "").replace("\'", "")
            elif len(r_description) == 2:
                description = r_description[0].text
                description = description.replace("\"", "").replace("\'", "")
                complectation = r_description[1].text
                complectation = complectation.replace("\"", "").replace("\'", "").replace("Комплектация", "")
            # extract ozon_id
            ozon_id = item_link.split('/')
            ozon_id = ozon_id[len(ozon_id) - 2].split('-')
            ozon_id = ozon_id[len(ozon_id) - 1]
            # extract price
            try:
                price = self.driver.find_element(By.XPATH, "//div[@class='sj0']").text
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='k3w wk3']").text
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='k3w']").text
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='k3w w3k']").text
            except:
                pass
            price = price.split("₽")[0]
            price = price.replace(" ", "")
            properties.update(
                [("Описание", description), ("Комплектация", complectation), ("ozone_id", ozon_id),
                 ("Цена (руб.)", price), ("Ссылка", item_link)])
            return properties
        except NoSuchElementException as e:
            print(e)

    def get_subcategory_items(self, subcategory_link):
        """
        Gets all items in given subcategory
        :param subcategory_link: given subcategory link
        :return: list of name od subcategory and list of dicts contains items info
        """
        try:
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
                except Exception as e:
                    self.driver.delete_all_cookies()
                    print(subcategory_link + "\n" + e)
            return [name, subcategory]
        except NoSuchElementException as e:
            print(e)

    # auxiliary methods for parsing process optimization
    @staticmethod
    def add_parsed_category(link):
        with open(f"parsed_categories.txt", "a") as f:
            f.write(link + "\n")

    @staticmethod
    def check_if_parsed(link):
        with open(f"parsed_categories.txt", "r") as f:
            text = f.read()
        if link in text:
            return True
        return False

    @staticmethod
    def json_backup(category):
        """
        Prepares backup for parsed data
        """
        if not os.path.isdir("json_backup"):
            os.mkdir("json_backup")
        with open(f"json_backup/{category[0]}.json", "w") as write_file:
            json.dump(category, write_file)

    def test_products_category(self):
        sub_links = self.get_subcategory_links("https://www.ozon.ru/category/produkty-pitaniya-9200/?sorting=rating")
        for s in sub_links:
            if not self.check_if_parsed(s):
                subcategory = self.get_subcategory_items(s)
                self.json_backup(subcategory)
                WriteToDatabase.write_to_db(self.PATH, subcategory)
                self.add_parsed_category(s)
        self.driver.quit()


if __name__ == '__main__':
    auto = OzonParser()
    # with open("json_backup/konditerskie_izdeliya.json") as json_file:
    #     data = json.load(json_file)
    # WriteToDatabase.write_from_json(self.PATH, data)
    auto.test_products_category()
