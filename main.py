import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoSuchWindowException, \
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
            self.driver.find_element(By.XPATH, "//div[@class='ec2']").click()
            categories = self.driver.find_element(By.XPATH, "//div[@class='c3e']").find_elements(By.TAG_NAME, "a")
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
            categories = self.driver.find_elements(By.XPATH, "//a[@class='s2s']")
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
        # iterates through all pages while button "Дальше" available
        self.driver.get(subcategory_link)
        # take a restriction of 500 for the number of products due to long time process
        while next_button and items and len(links) < 40:
            try:
                next_button = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='ui-b3']")))
                if len(next_button) > 1:
                    next_button = next_button[1]
                else:
                    next_button = next_button[0]
                # only for products category - //a[@class='tile-hover-target li9']
                items = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='n0i tile-hover-target']")))
            except:
                break
            links.extend([_.get_attribute('href') for _ in items])
            if next_button:
                next_button.click()
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
                text += i.text + "\n"
            prop_str = text.replace(":", "\n").split("\n")
            for i in range(0, len(prop_str) - 1, 2):
                properties.update({prop_str[i]: prop_str[i + 1]})
            try:
                r_description = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@id='section-description']//div//div[@class='kn6']")))
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
                headers = r_description[1].find_elements(By.TAG_NAME, "h3")
                desc = r_description[1].find_elements(By.TAG_NAME, "p")
                if len(headers) == len(desc):
                    for i in range(len(headers)):
                        properties.update({headers[i].text : desc[i].text})
            # extract ozon_id
            ozon_id = item_link.split('/')
            ozon_id = ozon_id[len(ozon_id) - 2].split('-')
            ozon_id = ozon_id[len(ozon_id) - 1]
            # extract price
            price = ""
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='wk7 w7k']").text
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//span[@class='wk7']").text
            except:
                pass
            price = price.split("₽")[0]
            price = price.replace(" ", "")
            properties.update(
                [("Описание", description), ("ozone_id", ozon_id),
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
                print(item)
                print(t)
            except NoSuchWindowException as n:
                print(n)
                return
        return [name, subcategory]

    # auxiliary methods for parsing process optimization
    @staticmethod
    def add_parsed_category(link):
        with open(f"parsed_categories.txt", "a") as f:
            f.write(link + "\n")

    @staticmethod
    def check_if_parsed(link):
        with open(f"parsed_categories.txt", "r") as f:
            s_text = f.read()
        if link in s_text:
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
    #auto.get_item_info("https://www.ozon.ru/product/tsukaty-bez-sahara-tykva-v-shokolade-na-sirope-topinambura-naturalnyy-produkt-barri-briyut-495980670/?advert=3Wx1uwCseQ84EAEn5X8jxfhDG7r3So4_BLkEUe8ZqENxhc7f3EwP1dMD_SQxpz5RAJVjPgV6z4Q0MITVEHKphFuiibJ3j_VlLy8A-Fvmwk-VpvPZnUJPEnKaOl3L1jiMeWbNiQ3Lf5gPW-inEAO7LWDl84PN60U-I0uzyW_yljU8amI1QMkZbLNq5LMlTN5CJ4zDy1fV0ih2CopDQ4wlXNsDM0qiqnXwoxcaZKq_FHJ-eWwcj6jdezamqzzLIj2ntSjwPCHVyWjOnvEBcApziEjkSJ9S42YJoJYxxU0hebC_Fedf4Jk3gjOr7lcur4AY3y-3JKxWKFK8-r-oKi6bgk_dc-1eGVAnmhZvR6W6TmW_WZw6rJ2rs6OLBDjJgr840OqPQmk_wimIU3pOPhguKklHr9FHOUK4OLpLQ2166BHznD_fSLfhUIKJLqrCf81dQwJQLZrwf7Nez8q3uIsQ6NZUQfoPUFNGblnLH7uRpeK8CV8YsjoaDnoFLnEmjJGTVxgNlekBsOBd-zKhbAzYJp6Kf5KdrEYRq_Z9npb9p5jY0a6TgVuQSXeJHRkEQglm")
    # with open("json_backup/konditerskie_izdeliya.json") as json_file:
    #     data = json.load(json_file)
    # WriteToDatabase.write_from_json(self.PATH, data)
    auto.test_products_category()
