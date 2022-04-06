import re
import os
import json
import pymysql
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


class OzonParser():
    MAIN_URL = "https://www.ozon.ru/"

    def get_category_links(self):
        """
        Get categories and their links for later parsing
        :return: list of links on categories
        """
        category_links = []
        try:
            self.driver.get(self.MAIN_URL)
            self.driver.find_element(By.XPATH, "//div[@class='ce1']//button[@type='button']").click()
            categories = self.driver.find_element(By.XPATH, "//div[@class='e1c']").find_elements(By.TAG_NAME, "a")
            category_links = [category.get_attribute('href') for category in categories[0:31]]
        except Exception as e:
            print(e)
        return category_links

    # for "Автомобили и мототехника" only
    def get_subcategory_links(self):
        categories = self.driver.find_elements(By.XPATH, "//a[@class='r5y']")
        category_links = [category.get_attribute('href') for category in categories]
        return category_links

    def get_page_items_links(self):
        """
        :return: list of links of items in given page
        Parse all items in given page in the category (by link)
        """
        items1 = self.driver.find_elements(By.XPATH, "(//div[@class='n2i i3n'])")
        items2 = self.driver.find_elements(By.XPATH, "(//div[@class='ni4 n4i'])")
        if items1:
            return items1
        elif items2:
            return items2
        else:
            raise Exception("Something went wrong while parsing this category! Check parsing elements!")

    def get_item_info(self, item_link):
        """

        """

    def get_category_items(self, category_link):
        """
        :param category_link: given category link
        :return: dict of parsed items
        """
        self.driver.get(category_link)
        # check if button "Смотреть все товары" is present
        try:
            button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='o1d d2o']//div[@class='ui-b1']")))
            button.click()
        except:
            return
        subcategories = self.get_subcategory_links()
        for s in subcategories:
            self.driver.get(s)
            next_button = None
            # iterates through all pages while button "Дальше" available
            try:
                next_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='ui-b4 ui-c0']")))
            except:
                pass
            while next_button:
                links = self.get_page_items_links()
                for item in links:
                    self.get_item_info()
                next_button.click()

    # on "Автомобили и мототехника" category
    def test(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        category_links = []
        try:
            category_links = self.get_category_links()
            items = self.get_category_items(category_links[28])
        except Exception as e:
            print(e)
        self.driver.quit()


s = OzonParser()
s.test()
