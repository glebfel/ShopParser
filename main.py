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
        :return: list of category links
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
        """
        Get subcategory links in given category
        :return: list of subcategory links
        """
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='ry5']")))
        categories = self.driver.find_elements(By.XPATH, "//a[@class='ry5']")
        category_links = [category.get_attribute('href') for category in categories]
        return category_links

    def get_page_items_links(self):
        """
        Get all item's links in given page in the category (by link)
        :return: list of item's links in given page
        """
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='tile-hover-target i7l']")))
            items = self.driver.find_elements(By.XPATH, "//a[@class='tile-hover-target i7l']")
        except Exception as e:
            print(e)
        return [_.get_attribute('href') for _ in items]

    def get_item_info(self, item_link):
        """
        :param item_link: given item's link
        :return: dict with parsed info of an item
        """
        properties = {}
        self.driver.get(item_link)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='section-characteristics']//div//div[@class='s6j']")))
            prop_str = self.driver.find_element(By.XPATH, "//div[@id='section-characteristics']//div//div["
                                                            "@class='s6j']").text
            prop_str = prop_str.split("\n")
            for i in range(1, len(prop_str), 2):
                properties.update({prop_str[i-1]:prop_str[i]})
            description = self.driver.find_element(By.XPATH, "//div[@id='section-description']//div//div//div[@class='kn']").text
            ozon_id = item_link.split('/')
            ozon_id = ozon_id[len(ozon_id) - 2].split('-')
            ozon_id = ozon_id[len(ozon_id) - 1]
            properties.update([("Описание",description), ("ozone_id",ozon_id)])
        except Exception as e:
            print(e)
        return properties

    def get_category_items(self, category_link):
        """
        :param category_link: given category link
        :return: list of dicts contains subcategories and items in it
        """
        category = []
        self.driver.get(category_link)
        # check if button "Смотреть все товары" is present
        try:
            button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='o1d d2o']//div[@class='ui-b1']")))
            button.click()
        except:
            return
        # collect all links of categories
        subcategories = self.get_subcategory_links()
        for s in subcategories:
            name = s.split("/")[4]
            name = name.split("-")[0]
            subcategory = []
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
                    subcategory.append(self.get_item_info(item))
                next_button.click()
            category.append({name:subcategory})
        return category

    # on "Автомобили и мототехника" category
    def test(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        try:
            category_links = self.get_category_links()
            items = self.get_category_items(category_links[28])
        except Exception as e:
            print(e)
        self.driver.quit()


s = OzonParser()
s.test()
