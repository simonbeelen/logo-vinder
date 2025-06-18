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