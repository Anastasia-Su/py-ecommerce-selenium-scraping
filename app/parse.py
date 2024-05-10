import csv
import re
import time
from dataclasses import dataclass
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    memory: int
    rating: int
    num_of_reviews: int


class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(5)

    def accept_cookies(self) -> None:
        try:
            accept_button = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "acceptCookies")
                )
            )

            accept_button.click()
            print("Cookies accepted.")
        except TimeoutException:
            pass

    def get_single_product(self, memory: int = None) -> Product:
        price = float(
            self.driver.find_element(By.CLASS_NAME, "price").text.replace(
                "$", ""
            )
        )

        return Product(
            title=self.driver.find_element(By.CLASS_NAME, "title").text,
            description=self.driver.find_element(
                By.CLASS_NAME, "description"
            ).text,
            price=price,
            memory=memory,
            rating=len(
                self.driver.find_elements(By.CLASS_NAME, "ws-icon-star")
            ),
            num_of_reviews=int(
                re.search(
                    r"\d+",
                    self.driver.find_element(
                        By.CLASS_NAME, "review-count"
                    ).text,
                ).group(0)
            ),
        )

    def click_more_button(self):
        while True:
            try:
                more_button = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", more_button
                )
                self.driver.execute_script("window.scrollBy(0, -100);")
                more_button.click()
            except (ElementNotInteractableException, NoSuchElementException):
                break
        # try:
        #     more_button = self.driver.find_element(
        #         By.CLASS_NAME, "ecomerce-items-scroll-more"
        #     )
        #
        #     while more_button:
        #         more_button.click()
        #
        # except ElementNotInteractableException:
        #     pass
        # except NoSuchElementException:
        #     pass

    def get_products_with_different_memory(
        self,
    ) -> list[Product]:
        products = []

        try:
            swatches = self.driver.find_element(By.CLASS_NAME, "swatches")
            buttons = swatches.find_elements(By.TAG_NAME, "button")

            for button in buttons:
                button.click()
                product = self.get_single_product(
                    int(button.get_attribute("value"))
                )
                products.append(product)
                # time.sleep(1)

        except NoSuchElementException:
            product = self.get_single_product()
            products.append(product)

        return products

    def get_all_products(self, page_url) -> list[Product]:
        self.driver.implicitly_wait(1)
        self.driver.get(page_url)
        self.accept_cookies()
        self.click_more_button()

        page_links = self.driver.find_elements(By.CSS_SELECTOR, "h4 > a.title")
        page_links_li = [link.get_attribute("href") for link in page_links]

        products = []

        for link in page_links_li:
            self.driver.get(link)
            products += self.get_products_with_different_memory()
        print("products", products)

        return products

    def write_products_to_csv(self, page_url, csv_file_name):
        products = self.get_all_products(page_url)
        with open(csv_file_name, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(Product.__annotations__.keys())

            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.memory,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )

    def close_driver(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = Scraper()

    scraper.accept_cookies()

    scraper.write_products_to_csv(HOME_URL, "home.csv")

    scraper.write_products_to_csv(
        urljoin(HOME_URL, "computers/"), "computers.csv"
    )
    scraper.write_products_to_csv(
        urljoin(HOME_URL, "computers/tablets"), "tablets.csv"
    )
    scraper.write_products_to_csv(
        urljoin(HOME_URL, "computers/laptops"), "laptops.csv"
    )

    scraper.write_products_to_csv(urljoin(HOME_URL, "phones/"), "phones.csv")
    scraper.write_products_to_csv(
        urljoin(HOME_URL, "phones/touch"), "touch.csv"
    )

    scraper.close_driver()
