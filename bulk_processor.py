import asyncio
import aiohttp
import aiofiles
import sqlite3
import base64
import os

class AsyncLogoScraper:
    def __init__(self, max_gelijktijdig=10):
        self.max_gelijktijdig = max_gelijktijdig
        self.database_pad = "bedrijven_logos.db"
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
    
    async def download_logo_async(self, sessie, logo_url, bedrijf_naam):
        try:
            async with sessie.get(logo_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    extensie = logo_url.split('.')[-1].lower()
                    if extensie not in ['png', 'jpg', 'jpeg', 'gif', 'svg']:
                        extensie = 'png'
                    
                    bestand_naam = f"{bedrijf_naam.lower().replace(' ', '_')}.{extensie}"
                    bestand_pad = f"logos/{bestand_naam}"
                    
                    os.makedirs("logos", exist_ok=True)
                    async with aiofiles.open(bestand_pad, 'wb') as f:
                        await f.write(content)
                    
                    return bestand_pad
        except Exception as e:
            print(f"Async download fout voor {bedrijf_naam}: {e}")
        
        return None
    
    async def zoek_logo_async(self, sessie, bedrijf_naam, domein=None):
        if domein:
            clearbit_url = f"https://logo.clearbit.com/{domein}"
        else:
            domein_gok = f"{bedrijf_naam.lower().replace(' ', '')}.com"
            clearbit_url = f"https://logo.clearbit.com/{domein_gok}"
        
        try:
            async with sessie.get(clearbit_url) as response:
                if response.status == 200:
                    return clearbit_url
        except:
            pass
        
        return None
    
    async def verwerk_bedrijf_async(self, sessie, bedrijf_data):
        if isinstance(bedrijf_data, str):
            bedrijf_naam = bedrijf_data
            domein = None
        else:
            bedrijf_naam = bedrijf_data.get('naam')
            domein = bedrijf_data.get('domein')
        
        logo_url = await self.zoek_logo_async(sessie, bedrijf_naam, domein)
        
        bestand_pad = None
        if logo_url:
            bestand_pad = await self.download_logo_async(sessie, logo_url, bedrijf_naam)
        
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bedrijven_logos 
            (bedrijf_naam, logo_url, logo_bestand_pad, status)
            VALUES (?, ?, ?, ?)
        ''', (
            bedrijf_naam,
            logo_url,
            bestand_pad,
            'gevonden' if logo_url else 'niet_gevonden'
        ))
        conn.commit()
        conn.close()
        
        return {
            'bedrijf': bedrijf_naam,
            'succes': logo_url is not None
        }
    
    async def verwerk_alle_bedrijven(self, bedrijven_lijst):
        connector = aiohttp.TCPConnector(limit=self.max_gelijktijdig)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        ) as sessie:
            
            taken = []
            for bedrijf_data in bedrijven_lijst:
                taak = self.verwerk_bedrijf_async(sessie, bedrijf_data)
                taken.append(taak)
            
            resultaten = await asyncio.gather(*taken, return_exceptions=True)
            
        return [r for r in resultaten if not isinstance(r, Exception)]

async def bulk_verwerking():
    scraper = AsyncLogoScraper(max_gelijktijdig=20)
    
    bedrijven = [
        {'naam': 'Google', 'domein': 'google.com'},
        {'naam': 'Microsoft', 'domein': 'microsoft.com'},
    ]
    
    resultaten = await scraper.verwerk_alle_bedrijven(bedrijven)
    
    for resultaat in resultaten:
        status = "✓" if resultaat['succes'] else "✗"
        print(f"{status} {resultaat['bedrijf']}")