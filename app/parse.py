import csv
import re
import time
from dataclasses import dataclass
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
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


def get_single_product(
    driver: webdriver.Chrome, memory: int = None
) -> Product:
    price = float(
        driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )

    return Product(
        title=driver.find_element(By.CLASS_NAME, "title").text,
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=price,
        memory=memory,
        rating=len(driver.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            re.search(
                r"\d+", driver.find_element(By.CLASS_NAME, "review-count").text
            ).group(0)
        ),
    )


def accept_cookies(driver: webdriver.Chrome) -> None:
    accept_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
    )
    accept_button.click()
    print("Cookies accepted.")


def get_products_with_different_memory(
    driver: webdriver.Chrome,
) -> list[Product]:
    products = []

    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        for button in buttons:
            button.click()
            product = get_single_product(
                driver, int(button.get_attribute("value"))
            )
            products.append(product)
            # time.sleep(1)

    except NoSuchElementException:
        product = get_single_product(driver)
        products.append(product)

    return products


def get_all_products(page_url) -> list[Product]:
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(page_url)

    accept_cookies(driver)

    page_links = driver.find_elements(By.CSS_SELECTOR, "h4 > a")
    page_links_li = [link.get_attribute("href") for link in page_links]

    products = []

    for link in page_links_li:
        driver.get(link)
        products += get_products_with_different_memory(driver)

    driver.quit()

    return products


def write_products_to_csv(page_url, csv_file_name):
    products = get_all_products(page_url)
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


if __name__ == "__main__":
    write_products_to_csv(HOME_URL, "home.csv")
    write_products_to_csv(urljoin(HOME_URL, "computers/"), "computers.csv")
