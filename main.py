from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, WebDriverException
from db import WriteToDatabase


class OzonParser():
    MAIN_URL = "https://www.ozon.ru/"
    PATH = "config.conf"

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)

    def get_category_links(self):
        """
        Gets categories and their links for later parsing
        :return: list of category links
        """
        category_links = []
        try:
            self.driver.get(self.MAIN_URL)
            self.driver.find_element(By.XPATH, "//div[@class='ce1']//button[@type='button']").click()
            categories = self.driver.find_element(By.XPATH, "//div[@class='e1c']").find_elements(By.TAG_NAME, "a")
            category_links = [category.get_attribute('href') for category in categories[0:31]]
            return category_links
        except NoSuchElementException:
            print("Exception in 'get_category_links' method\nInternet connection is too slow! Please check it and "
                  "rerun!")

    def get_subcategory_links(self, category_link):
        """
        Gets subcategory links in given category
        :param category_link: given category link
        :return: list of subcategory links
        """
        self.driver.get(category_link + "?sorting=rating")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='ry5']")))
            categories = self.driver.find_elements(By.XPATH, "//a[@class='ry5']")
            category_links = [category.get_attribute('href') for category in categories]
            return category_links
        except NoSuchElementException:
            print("Exception in 'get_subcategory_links' method\nInternet connection is too slow! Please check it and "
                  "rerun!")

    def get_items_links(self, subcategory_link):
        """
        Gets all item's links in given page in the category (by link)
        :param subcategory_link: given subcategory link
        :return: list of item's links in given page
        """
        try:
            links = []
            # iterates through all pages while button "Дальше" available
            next_button = True
            self.driver.get(subcategory_link)
            while next_button:
                try:
                    next_button = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='ui-b4 ui-c0']")))
                except:
                    next_button = False
                    pass
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@class='tile-hover-target i7l']")))
                items = self.driver.find_elements(By.XPATH, "//a[@class='tile-hover-target i7l']")
                links.extend([_.get_attribute('href') for _ in items])
                if next_button:
                    next_button.click()
            return links
        except NoSuchElementException:
            print("Exception in 'get_page_items_links' method\nInternet connection is too slow! Please check it and "
                  "rerun!")

    def get_item_info(self, item_link):
        """
        Gets info from description of an item
        :param item_link: given item's link
        :return: dict with parsed info of an item
        """
        properties = {}
        self.driver.get(item_link)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='section-characteristics']//div//div[@class='s6j']")))
            prop_str = self.driver.find_element(By.XPATH, "//div[@id='section-characteristics']//div//div["
                                                          "@class='s6j']").text
            prop_str = prop_str.split("\n")
            for i in range(1, len(prop_str), 2):
                properties.update({prop_str[i - 1]: prop_str[i]})
            description = self.driver.find_element(By.XPATH,
                                                   "//div[@id='section-description']//div//div//div[@class='kn']").text
            ozon_id = item_link.split('/')
            ozon_id = ozon_id[len(ozon_id) - 2].split('-')
            ozon_id = ozon_id[len(ozon_id) - 1]

            price = 0
            try:
                price = self.driver.find_element(By.XPATH, "//div[@class='r8j']").text
                price = price.replace(" ", "").replace("₽", "")
            except:
                pass
            try:
                price = self.driver.find_element(By.XPATH, "//div[@class='k0w kw2 wk3']").text
                price = price.replace(" ", "").replace("₽", "")
            except:
                pass
            properties.update([("Описание", description), ("ozone_id", ozon_id), ("Цена", price)])
            return properties
        except NoSuchElementException:
            print("Exception in 'get_item_info' method\nInternet connection is too slow! Please check it and rerun!")

    def get_subcategory_items(self, subcategory_link):
        """
        Gets all items in given subcategory
        :param subcategory_link: given subcategory link
        :return: list of name od subcategory and list of dicts contains items info
        """
        try:
            name = subcategory_link.split("/")[4]
            name = name.split("-")[0]
            subcategory = []
            # iterates through all pages while button "Дальше" available
            links = self.get_items_links(subcategory_link)
            for item in links:
                subcategory.append(self.get_item_info(item))
            return [name, subcategory]
        except NoSuchElementException:
            print("Exception in 'get_category_items' method\nInternet connection is too slow! Please check it and "
                  "rerun!")

    # on "Автомобили и мототехника" category
    def test(self):
        # try:
        # initialize db module
        db = WriteToDatabase(self.PATH)
        # collect all category links
        cat_links = self.get_category_links()
        # collect all subcategory links of "Автомобили и мототехника" category
        sub_links = self.get_subcategory_links(cat_links[28])
        for s in sub_links:
            subcategory = self.get_subcategory_items(s)
            db.write_to_db(subcategory)
        # except WebDriverException or NoSuchWindowException:
        #     print("The WebDriver window was closed! Please rerun the program!")
        # except BaseException as e:
        #     print(e)
        # finally:
        #     self.driver.quit()
        self.driver.quit()


if __name__ == '__main__':
    auto = OzonParser()
    auto.test()


