from bs4 import BeautifulSoup
import requests


def get_data(soup):
    data = []
    table = soup.find(class_="history-rates-data")
    rows = table.find_all("td")
    with open("../../data/historical_currency.txt", "a", encoding="utf-8") as file:
        for line in rows:
            if line.find("a"):
                date = line.text.strip().split("\n")[1]
            if line.find("span"):
                currency_value = line.text.strip().split("\n")[0]
                to_remove = [("1 EUR = ", ""), ("KRW", ""), ("\xa0", "")]
                [currency_value := currency_value.replace(a, b) for a, b, in to_remove]
                
                if "Taux de change" in currency_value:
                    continue

                formatted_line = f"KRW\t{date}\t{currency_value}\n"
                file.write(formatted_line)

def get_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    } # Using this for avoiding error response from web server

    page = requests.get(url, headers=headers)

    if page.status_code == 200:
        return page.content
    return None

def scrap(years):
    base_url = "https://www.exchange-rates.org/fr/historique/eur-krw-"
    for year in years:
        print(f"Scraping data of {year}...")
        page_content = get_page(base_url + str(year))
        if page_content:
            soup = BeautifulSoup(page_content, "html.parser")
            get_data(soup)
        else:
            print(f"Impossible de récupérer la page pour l'année {year}. Vérifiez l'URL ou la connexion.")

    
if __name__ == "__main__":
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    scrap(years)