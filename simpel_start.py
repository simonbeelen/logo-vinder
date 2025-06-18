from eigen_url_scraper import EigenUrlAfbeeldingScraper

def simpel_gebruik():
    scraper = EigenUrlAfbeeldingScraper()
    mijn_urls = [
        "https://www.google.com",
        "https://www.microsoft.com",
    ]
    print("Starten met afbeeldingen scrapen...")
    for url in mijn_urls:
        print(f"\nVerwerken: {url}")
        resultaten = scraper.verwerk_url(url, alleen_logos=True)
        for resultaat in resultaten:
            if resultaat['succes']:
                print(f"  ✓ Gedownload: {resultaat['bestand']}")
            else:
                print(f"  ✗ Fout: {resultaat['url']}")
    scraper.exporteer_naar_html_overzicht()
    print("\nKlaar! Check 'afbeeldingen_overzicht.html' voor resultaten.")

if __name__ == "__main__":
    simpel_gebruik()