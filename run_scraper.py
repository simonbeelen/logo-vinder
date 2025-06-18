from logo_scraper import LogoScraper
import sys

def main():
    if len(sys.argv) < 2:
        print("Gebruik: python run_scraper.py <bedrijf_naam> [domein]")
        sys.exit(1)
    
    bedrijf_naam = sys.argv[1]
    domein = sys.argv[2] if len(sys.argv) > 2 else None
    
    scraper = LogoScraper()
    succes = scraper.voeg_bedrijf_toe(bedrijf_naam, domein)
    
    if succes:
        print(f"Logo gevonden voor {bedrijf_naam}")
        scraper.exporteer_naar_sql()
    else:
        print(f"Geen logo gevonden voor {bedrijf_naam}")

if __name__ == "__main__":
    main()