"""
C1 — Collecte par scraping web (quotes.toscrape.com - site prévu pour le scraping)
En production, remplacer par un site d'avis réel.
"""
import sys
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "scraped_reviews_raw.csv"
BASE_URL = "https://quotes.toscrape.com"


def scrape_quotes(pages: int = 3) -> list[dict]:
    """Scrape des citations depuis quotes.toscrape.com."""
    all_quotes = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/page/{page}/"
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            quote_divs = soup.find_all("div", class_="quote")
            if not quote_divs:
                print(f"[INFO] Page {page} : fin du contenu")
                break
            for div in quote_divs:
                text = div.find("span", class_="text")
                author = div.find("small", class_="author")
                tags = div.find_all("a", class_="tag")
                all_quotes.append({
                    "text": text.get_text(strip=True) if text else "",
                    "author": author.get_text(strip=True) if author else "",
                    "tags": ", ".join(t.get_text(strip=True) for t in tags),
                    "source_url": url,
                    "scraped_at": datetime.now().isoformat(),
                })
            print(f"[OK] Page {page}/{pages} — {len(quote_divs)} éléments")
        except requests.Timeout:
            print(f"[WARN] Timeout page {page}")
        except requests.RequestException as e:
            print(f"[ERREUR] Page {page} : {e}")
    return all_quotes


def main():
    print("=" * 60)
    print(f"COLLECTE SCRAPING — {datetime.now().isoformat()}")
    print("=" * 60)
    quotes = scrape_quotes(pages=3)
    if not quotes:
        print("[ERREUR] Aucune donnée extraite.")
        sys.exit(1)
    df = pd.DataFrame(quotes)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Sauvegardé : {OUTPUT_FILE} ({len(df)} éléments)")
    print("=" * 60)


if __name__ == "__main__":
    main()
