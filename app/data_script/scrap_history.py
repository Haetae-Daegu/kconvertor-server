from bs4 import BeautifulSoup
import requests




def get_data(soup):
    data = []
    table = soup.find(class_="history-rates-data")
    rows = table.find_all("td")
    for line in rows:
        if line.find("a"):
            date = line.text.strip().split("\n")[1]
        if line.find("span"):
            currency_value = line.text.strip().split("\n")[0]
            to_remove = [("1 EUR = ", ""), ("KRW", ""), ("\xa0", "")]
            [currency_value := currency_value.replace(a, b) for a, b, in to_remove]
            obj = {"date": date, "currency_value": currency_value}
            data.append(obj)
    data.pop()
    print(data)

def get_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    } # Using this for avoiding error response from web server

    page = requests.get(url, headers=headers)

    if page.status_code == 200:
        return page.content
    return None

def scrap():
    page_content = get_page("https://www.exchange-rates.org/fr/historique/eur-krw-2025")
    soup = BeautifulSoup(page_content, "html.parser")
    get_data(soup)

    
if __name__ == "__main__":
    scrap()