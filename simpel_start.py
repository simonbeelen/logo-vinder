from logo_scraper import EigenUrlAfbeeldingScraper

def simpel_gebruik():
    scraper = EigenUrlAfbeeldingScraper()
    mijn_urls = [
        "https://www.google.com",
        "https://www.microsoft.com",
    ]
    print("Starten met afbeeldingen scrapen...")
    for url in mijn_urls:
        print(f"\nVerwerken: {url}")
        # Using the existing 'verwerk' method instead of 'verwerk_url'
        scraper.verwerk("", url)
        print(f"  ✓ Afbeeldingen opgeslagen in 'logos' map")
    
    print("\nKlaar! Check de 'logos' map en 'eigen_afbeeldingen.db' voor resultaten.")

if __name__ == "__main__":
    simpel_gebruik()