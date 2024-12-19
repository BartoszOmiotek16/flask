import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
from datetime import datetime
from urllib.parse import urlparse
import time


def accept_google_popup(driver):
    """
    Akceptuje popup dotyczący polityki cookies na stronie Google.
    """
    try:
        wait = WebDriverWait(driver, 20)  # Zwiększono czas oczekiwania na element
        possible_selectors = [
            "button#L2AGLb",  # Dodano unikalny id z popupu na Twoim screenie
            "button[aria-label='Zaakceptuj wszystko']",
            "button[jsname='Njthtb']",
            "//button[text()='Zaakceptuj wszystko']",
            "//button[contains(text(), 'Akceptuj')]"
        ]

        for selector in possible_selectors:
            try:
                print(f"Próba kliknięcia selektora: {selector}")
                if selector.startswith("//"):
                    accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                # Kliknięcie przycisku za pomocą JavaScript
                driver.execute_script("arguments[0].click();", accept_button)
                print(f"Kliknięto przycisk za pomocą: {selector}")
                time.sleep(1)
                return
            except Exception as e:
                print(f"Nie udało się kliknąć przycisku {selector}: {e}")
                continue
        print("Nie udało się znaleźć przycisku akceptacji popupu.")
    except Exception as e:
        print(f"Wystąpił błąd przy akceptacji popupu: {e}")


def google_search(query, max_pages=None):
    """
    Wykonuje wyszukiwanie w Google i zwraca listę linków z wyników organicznych.
    Zaznacza, czy wyniki są sponsorowane.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(f"https://www.google.com/search?q={query}&hl=pl")
    time.sleep(2)

    # Akceptowanie popupu Google
    accept_google_popup(driver)

    results = []
    excluded_domains = ["facebook.com", "olx.pl", "oferteo.pl"]
    current_page = 1

    while True:
        print(f"Przetwarzanie strony {current_page}...")

        # Pobieranie wyników z bieżącej strony
        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.g")
        found_on_page = 0
        for div in result_divs:
            try:
                link_element = div.find_element(By.CSS_SELECTOR, "a")
                if link_element:
                    url = link_element.get_attribute("href")
                    if url and "http" in url and not any(domain in url for domain in excluded_domains):
                        is_sponsored = "Nie"
                        try:
                            # Sprawdzanie oznaczenia reklamowego
                            ad_label = div.find_element(By.CSS_SELECTOR, "span[data-text-ad]")
                            if ad_label:
                                is_sponsored = "Tak"
                        except Exception:
                            pass

                        results.append({
                            "url": url,
                            "is_sponsored": is_sponsored
                        })
                        found_on_page += 1
            except Exception as e:
                print(f"Błąd przy przetwarzaniu linku: {e}")
                continue

        print(f"Znaleziono {found_on_page} wyników na stronie {current_page}.")

        # Przejście na następną stronę
        try:
            if max_pages and current_page >= max_pages:
                print("Osiągnięto maksymalną liczbę stron.")
                break

            wait = WebDriverWait(driver, 10)
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#pnnext")))
            next_button.click()
            current_page += 1
            time.sleep(2)
        except Exception as e:
            print(f"Brak więcej stron wyników lub problem z przyciskiem 'Następna strona': {e}")
            break

    driver.quit()
    print(f"Ostatecznie znaleziono {len(results)} wyników spełniających kryteria.")
    return results


def fetch_metadata(url, is_sponsored):
    """
    Pobiera metadane ze strony, takie jak tytuł, opis oraz obecność sitemap.xml.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "Brak tytułu"
        description = soup.find("meta", attrs={"name": "description"})
        description_content = description["content"] if description else "Brak opisu"

        try:
            base_url = parsed_url.scheme + "://" + parsed_url.netloc
            sitemap_url = f"{base_url}/sitemap_index.xml"
            sitemap_response = requests.head(sitemap_url, timeout=5)
            sitemap_exists = sitemap_response.status_code == 200
        except Exception:
            sitemap_exists = False

        return {
            "url": url,
            "domain": domain,
            "title": title.strip(),
            "description": description_content.strip(),
            "sitemap": "Tak" if sitemap_exists else "Nie",
            "is_sponsored": is_sponsored
        }
    except Exception:
        return {"url": url, "domain": "Błąd", "title": "Błąd", "description": "Błąd", "sitemap": "Nie", "is_sponsored": "Nie"}


def save_to_csv(data, query, filename=None):
    """
    Zapisuje dane do pliku CSV. Nazwa pliku zawiera frazę wyszukiwaną i datę.
    Dodaje BOM (Byte Order Mark), aby Excel poprawnie rozpoznał UTF-8.
    """
    if not data:
        print("Brak danych do zapisania. Plik nie został utworzony.")
        return

    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        if not filename:
            filename = f"{query.replace(' ', '_')}-{date_str}.csv"

        fieldnames = ["domain", "title", "description", "sitemap", "is_sponsored", "url"]

        with open(filename, "w", newline="", encoding="utf-8-sig") as file:  # Używamy utf-8-sig
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(data)
        print(f"Dane zostały zapisane w pliku: {filename}")
    except Exception as e:
        print(f"Błąd podczas zapisu pliku: {e}")


if __name__ == "__main__":
    print("Bieżący katalog pracy:", os.getcwd())
    query = input("Podaj frazę do wyszukiwania: ")
    max_pages = input("Podaj maksymalną liczbę stron do przeszukania (lub wciśnij Enter, aby przeszukać wszystkie): ")
    max_pages = int(max_pages) if max_pages.isdigit() else None

    print("Wykonywanie wyszukiwania...")
    search_results = google_search(query, max_pages=max_pages)
    print(f"Znaleziono {len(search_results)} wyników.")

    print("Pobieranie danych meta...")
    results = [fetch_metadata(result["url"], result["is_sponsored"]) for result in search_results]

    print("Zebrane dane:")
    for result in results:
        print(result)

    save_to_csv(results, query)
    print("Gotowe!")


