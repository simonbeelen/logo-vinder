import requests
import os
import json
import time
from urllib.parse import urljoin, urlparse
from PIL import Image
import io
import sqlite3
from datetime import datetime

class LogoScraper:
    def __init__(self, database_pad="bedrijven_logos.db"):
        self.database_pad = database_pad
        self.sessie = requests.Session()
        self.sessie.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.setup_database()
    
    def setup_database(self):
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bedrijven_logos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bedrijf_naam TEXT NOT NULL,
                logo_url TEXT,
                logo_bestand_pad TEXT,
                logo_grootte TEXT,
                datum_toegevoegd TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'nieuw'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def zoek_logo_clearbit(self, bedrijf_naam, domein=None):
        if domein:
            url = f"https://logo.clearbit.com/{domein}"
        else:
            domein_gok = f"{bedrijf_naam.lower().replace(' ', '')}.com"
            url = f"https://logo.clearbit.com/{domein_gok}"
        
        try:
            response = self.sessie.get(url, timeout=10)
            if response.status_code == 200:
                return url
        except:
            pass
        return None
    
    def zoek_logo_favicon(self, domein):
        if not domein.startswith('http'):
            domein = f"https://{domein}"
        
        favicon_urls = [
            f"{domein}/favicon.ico",
            f"{domein}/favicon.png",
            f"{domein}/apple-touch-icon.png",
            f"{domein}/android-chrome-192x192.png"
        ]
        
        for url in favicon_urls:
            try:
                response = self.sessie.get(url, timeout=5)
                if response.status_code == 200:
                    return url
            except:
                continue
        return None
    
    def download_logo(self, logo_url, bedrijf_naam):
        try:
            response = self.sessie.get(logo_url, timeout=10)
            if response.status_code == 200:
                os.makedirs("logos", exist_ok=True)
                
                extensie = logo_url.split('.')[-1].lower()
                if extensie not in ['png', 'jpg', 'jpeg', 'gif', 'svg']:
                    extensie = 'png'
                
                bestand_naam = f"{bedrijf_naam.lower().replace(' ', '_')}.{extensie}"
                bestand_pad = os.path.join("logos", bestand_naam)
                
                if extensie in ['png', 'jpg', 'jpeg']:
                    img = Image.open(io.BytesIO(response.content))
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    img.save(bestand_pad, optimize=True)
                    grootte = f"{img.size[0]}x{img.size[1]}"
                else:
                    with open(bestand_pad, 'wb') as f:
                        f.write(response.content)
                    grootte = "onbekend"
                
                return bestand_pad, grootte
        except Exception as e:
            print(f"Fout bij downloaden van {logo_url}: {e}")
        
        return None, None
    
    def voeg_bedrijf_toe(self, bedrijf_naam, domein=None):
        print(f"Zoeken naar logo voor: {bedrijf_naam}")
        
        logo_url = None
        
        logo_url = self.zoek_logo_clearbit(bedrijf_naam, domein)
        
        if not logo_url and domein:
            logo_url = self.zoek_logo_favicon(domein)
        
        bestand_pad = None
        grootte = None
        if logo_url:
            bestand_pad, grootte = self.download_logo(logo_url, bedrijf_naam)
        
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bedrijven_logos 
            (bedrijf_naam, logo_url, logo_bestand_pad, logo_grootte, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            bedrijf_naam,
            logo_url,
            bestand_pad,
            grootte,
            'gevonden' if logo_url else 'niet_gevonden'
        ))
        
        conn.commit()
        conn.close()
        
        return logo_url is not None
    
    def verwerk_bedrijven_lijst(self, bedrijven_lijst):
        resultaten = []
        
        for bedrijf_data in bedrijven_lijst:
            if isinstance(bedrijf_data, str):
                bedrijf_naam = bedrijf_data
                domein = None
            else:
                bedrijf_naam = bedrijf_data.get('naam')
                domein = bedrijf_data.get('domein')
            
            succes = self.voeg_bedrijf_toe(bedrijf_naam, domein)
            resultaten.append({
                'bedrijf': bedrijf_naam,
                'succes': succes
            })
            
            time.sleep(1)
        
        return resultaten
    
    def exporteer_naar_sql(self, output_bestand="logo_upload.sql"):
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bedrijven_logos WHERE status = 'gevonden'")
        records = cursor.fetchall()
        
        with open(output_bestand, 'w', encoding='utf-8') as f:
            f.write("-- Logo upload bestand gegenereerd op " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
            
            for record in records:
                id_val, naam, logo_url, bestand_pad, grootte, datum, status = record
                
                logo_base64 = None
                if bestand_pad and os.path.exists(bestand_pad):
                    with open(bestand_pad, 'rb') as img_file:
                        import base64
                        logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
                f.write(f"INSERT INTO bedrijven (naam, logo_url, logo_data, logo_grootte) VALUES (\n")
                f.write(f"    '{naam}',\n")
                f.write(f"    '{logo_url}',\n")
                f.write(f"    '{logo_base64}',\n" if logo_base64 else "    NULL,\n")
                f.write(f"    '{grootte}'\n")
                f.write(f");\n\n")
        
        conn.close()
        print(f"SQL upload bestand opgeslagen als: {output_bestand}")


def main():
    scraper = LogoScraper()
    
    bedrijven = [
        {'naam': 'Google', 'domein': 'google.com'},
        {'naam': 'Microsoft', 'domein': 'microsoft.com'},
        {'naam': 'Apple', 'domein': 'apple.com'},
        'Amazon',
        'Tesla'
    ]
    
    resultaten = scraper.verwerk_bedrijven_lijst(bedrijven)
    
    for resultaat in resultaten:
        status = "✓" if resultaat['succes'] else "✗"
        print(f"{status} {resultaat['bedrijf']}")
    
    scraper.exporteer_naar_sql()

if __name__ == "__main__":
    main()