import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

BASE_URL = "http://books.toscrape.com/catalogue/"
current_url = BASE_URL + "page-1.html"
page_count = 0
max_pages = 5

print("Iniciando el proceso de scraping...")

all_books = []

while page_count < max_pages and current_url:
    page_count += 1
    print(f"Scrapeando página: {current_url}")

    try:
        response = requests.get(current_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        books = soup.find_all("article", class_="product_pod")

        for book in books:
            title = book.h3.a["title"]

            price_text = book.find("p", class_="price_color").text
            price = float(price_text[1:])

            rating_text = book.find("p", class_="star-rating")["class"][1]
            rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
            rating = rating_map.get(rating_text, 0)

            all_books.append({
                "title": title,
                "price": price,
                "rating": rating
            })

        next_li = soup.find("li", class_="next")
        if next_li:
            next_href = next_li.a["href"]
            current_url = BASE_URL + next_href
        else:
            current_url = None

        time.sleep(0.5)

    except requests.RequestException as e:
        print(f"Error al acceder a la página {current_url}: {e}")
        current_url = None

print(f"\nScraping completado. Total de libros extraídos: {len(all_books)}")

if all_books:
    df = pd.DataFrame(all_books)
    df.to_csv("books.csv", index=False, encoding="utf-8")
    print("Datos guardados exitosamente en 'books.csv'.")
else:
    print("No se extrajeron datos.")
