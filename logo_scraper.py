import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
from PIL import Image
import io
import sqlite3
from datetime import datetime
import base64

class EigenUrlAfbeeldingScraper:
    def __init__(self, database_pad="eigen_afbeeldingen.db"):
        self.database_pad = database_pad
        self.sessie = requests.Session()
        self.sessie.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.setup_database()
    
    def setup_database(self):
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS afbeeldingen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bron_url TEXT,
                afbeelding_url TEXT,
                lokaal_bestand TEXT,
                alt TEXT,
                titel TEXT,
                grootte INTEGER,
                afmeting TEXT,
                status TEXT,
                datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def vind_logo_afbeeldingen(self, url):
        r = self.sessie.get(url, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        img_tags = soup.find_all('img')
        kandidaten = []
        keywords = ['logo','brand','header','nav','banner']
        for img in img_tags:
            src = img.get('src') or ''
            src = urljoin(url, src)
            alt = img.get('alt','')
            titel = img.get('title','')
            info = f"{alt} {titel} {src}"
            score = sum(1 for kw in keywords if kw in info.lower())
            if score>0:
                kandidaten.append((score, src, alt, titel))
        kandidaten.sort(reverse=True)
        return kandidaten[:3]
    
    def download(self, url, bron):
        os.makedirs('logos', exist_ok=True)
        r = self.sessie.get(url, timeout=10)
        naam = os.path.basename(urlparse(url).path) or 'logo.png'
        pad = os.path.join('logos', re.sub(r'[^\w\.]', '_', naam))
        img = Image.open(io.BytesIO(r.content))
        img.thumbnail((200,200), Image.Resampling.LANCZOS)
        img.save(pad,optimize=True)
        return pad, img.size, len(r.content)
    
    def verwerk(self, naam, url):
        kandidaten = self.vind_logo_afbeeldingen(url)
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        for _, src, alt, titel in kandidaten:
            pad, (w,h), grootte = self.download(src, url)
            cursor.execute('''
                INSERT INTO afbeeldingen
                (bron_url, afbeelding_url, lokaal_bestand, alt, titel, grootte, afmeting, status)
                VALUES (?,?,?,?,?,?,?,?)
            ''', (url, src, pad, alt, titel, grootte, f"{w}x{h}", 'gedownload'))
        conn.commit()
        conn.close()
        
    def verwerk_url(self, url, alleen_logos=True):
        """Verwerkt een URL en retourneert resultaten in een gestructureerd formaat"""
        resultaten = []
        kandidaten = self.vind_logo_afbeeldingen(url)
        
        for score, src, alt, titel in kandidaten:
            try:
                pad, (w, h), grootte = self.download(src, url)
                
                # Sla op in database
                conn = sqlite3.connect(self.database_pad)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO afbeeldingen
                    (bron_url, afbeelding_url, lokaal_bestand, alt, titel, grootte, afmeting, status)
                    VALUES (?,?,?,?,?,?,?,?)
                ''', (url, src, pad, alt, titel, grootte, f"{w}x{h}", 'gedownload'))
                conn.commit()
                conn.close()
                
                resultaten.append({
                    'succes': True,
                    'url': src,
                    'bestand': pad,
                    'afmeting': f"{w}x{h}",
                    'grootte': grootte,
                    'alt': alt,
                    'titel': titel
                })
            except Exception as e:
                resultaten.append({
                    'succes': False,
                    'url': src,
                    'fout': str(e)
                })
        
        return resultaten

    def exporteer_naar_html_overzicht(self):
        """Exporteert alle verzamelde afbeeldingen naar een HTML overzicht"""
        conn = sqlite3.connect(self.database_pad)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM afbeeldingen ORDER BY datum DESC')
        afbeeldingen = cursor.fetchall()
        conn.close()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Afbeeldingen Overzicht</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
                .item { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .item img { max-width: 100%; height: auto; }
                .info { margin-top: 10px; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>Verzamelde Afbeeldingen</h1>
            <p>Gegenereerd op: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <div class="container">
        """
        
        for afbeelding in afbeeldingen:
            id, bron_url, afbeelding_url, lokaal_bestand, alt, titel, grootte, afmeting, status, datum = afbeelding
            html += f"""
            <div class="item">
                <img src="{lokaal_bestand}" alt="{alt}">
                <div class="info">
                    <p><strong>Bron:</strong> <a href="{bron_url}" target="_blank">{bron_url[:30]}...</a></p>
                    <p><strong>Alt:</strong> {alt}</p>
                    <p><strong>Titel:</strong> {titel}</p>
                    <p><strong>Afmeting:</strong> {afmeting}</p>
                    <p><strong>Grootte:</strong> {grootte} bytes</p>
                    <p><strong>Bestand:</strong> {lokaal_bestand}</p>
                </div>
            </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open("afbeeldingen_overzicht.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        return "afbeeldingen_overzicht.html"