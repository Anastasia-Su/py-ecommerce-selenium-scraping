import csv
import re
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

    def get_single_product(self, card) -> Product:
        description = card.find_element(By.CLASS_NAME, "description").text
        price = float(
            card.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        )
        rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(
            re.search(
                r"\d+", card.find_element(By.CLASS_NAME, "review-count").text
            ).group(0)
        )

        title_link = card.find_element(
            By.CSS_SELECTOR, "h4 > a.title"
        ).get_attribute("href")

        self.driver.get(title_link)

        title = self.driver.find_element(By.CLASS_NAME, "card-title").text
        self.driver.back()

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )

    def click_more_button(self):
        while True:
            try:
                more_button = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )

                self.driver.execute_script(
                    "arguments[0].click();", more_button
                )

                more_button.click()

            except (
                ElementNotInteractableException,
                NoSuchElementException,
                TimeoutException,
            ):
                break

    def get_products_list(self, page_url) -> list[Product]:
        self.driver.implicitly_wait(1)
        self.driver.get(page_url)
        self.accept_cookies()
        self.click_more_button()

        products = []

        products_cards = self.driver.find_elements(By.CLASS_NAME, "card-body")
        for card in products_cards:
            products.append(self.get_single_product(card))

        return products

    def write_products_to_csv(self, page_url, csv_file_name):
        products = self.get_products_list(page_url)
        with open(csv_file_name, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(Product.__annotations__.keys())

            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )

    def close_driver(self):
        self.driver.quit()


def get_all_products():
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


if __name__ == "__main__":
    get_all_products()
