import csv
import pandas as pd
from logo_scraper import LogoScraper

def importeer_uit_csv(csv_bestand):
    scraper = LogoScraper()
    
    df = pd.read_csv(csv_bestand)
    
    bedrijven_lijst = []
    for index, row in df.iterrows():
        bedrijf_data = {
            'naam': row.get('bedrijf_naam', row.get('naam')),
            'domein': row.get('domein', row.get('website'))
        }
        bedrijven_lijst.append(bedrijf_data)
    
    resultaten = scraper.verwerk_bedrijven_lijst(bedrijven_lijst)
    
    scraper.exporteer_naar_sql(f"upload_{csv_bestand.replace('.csv', '')}.sql")
    
    return resultaten