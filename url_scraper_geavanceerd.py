import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse
import time
from PIL import Image
import io

class GeavanceerdeAfbeeldingScraper:
    def __init__(self):
        self.sessie = requests.Session()
        self.sessie.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def zoek_afbeeldingen_met_css_selectors(self, url, css_selectors):
        try:
            response = self.sessie.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            gevonden_afbeeldingen = []
            for selector in css_selectors:
                elementen = soup.select(selector)
                for element in elementen:
                    if element.name == 'img':
                        img_url = element.get('src') or element.get('data-src')
                        if img_url:
                            gevonden_afbeeldingen.append({
                                'url': urljoin(url, img_url),
                                'selector': selector,
                                'alt': element.get('alt', ''),
                                'class': ' '.join(element.get('class', []))
                            })
                    style = element.get('style', '')
                    if 'background-image' in style:
                        import re
                        bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                        if bg_match:
                            gevonden_afbeeldingen.append({
                                'url': urljoin(url, bg_match.group(1)),
                                'selector': selector,
                                'type': 'background-image',
                                'alt': '',
                                'class': ' '.join(element.get('class', []))
                            })
            return gevonden_afbeeldingen
        except Exception as e:
            print(f"Fout bij CSS selector zoeken: {e}")
            return []
    
    def zoek_afbeeldingen_in_json_ld(self, url):
        try:
            response = self.sessie.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            afbeeldingen = []
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    def zoek_afbeeldingen_in_data(obj, pad=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if key in ['image', 'logo', 'photo', 'thumbnail']:
                                    if isinstance(value, str):
                                        afbeeldingen.append({
                                            'url': urljoin(url, value),
                                            'type': 'json-ld',
                                            'property': f"{pad}.{key}",
                                            'alt': f"JSON-LD {key}"
                                        })
                                    elif isinstance(value, dict) and 'url' in value:
                                        afbeeldingen.append({
                                            'url': urljoin(url, value['url']),
                                            'type': 'json-ld',
                                            'property': f"{pad}.{key}.url",
                                            'alt': value.get('alt', f"JSON-LD {key}")
                                        })
                                else:
                                    zoek_afbeeldingen_in_data(value, f"{pad}.{key}")
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                zoek_afbeeldingen_in_data(item, f"{pad}[{i}]")
                    zoek_afbeeldingen_in_data(data)
                except json.JSONDecodeError:
                    continue
            return afbeeldingen
        except Exception as e:
            print(f"Fout bij JSON-LD zoeken: {e}")
            return []
    
    def zoek_meta_afbeeldingen(self, url):
        try:
            response = self.sessie.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            meta_afbeeldingen = []
            og_images = soup.find_all('meta', property=lambda x: x and 'og:image' in x)
            for meta in og_images:
                content = meta.get('content')
                if content:
                    meta_afbeeldingen.append({
                        'url': urljoin(url, content),
                        'type': 'opengraph',
                        'property': meta.get('property'),
                        'alt': 'OpenGraph afbeelding'
                    })
            twitter_images = soup.find_all('meta', name=lambda x: x and 'twitter:image' in x)
            for meta in twitter_images:
                content = meta.get('content')
                if content:
                    meta_afbeeldingen.append({
                        'url': urljoin(url, content),
                        'type': 'twitter',
                        'property': meta.get('name'),
                        'alt': 'Twitter Card afbeelding'
                    })
            andere_meta = soup.find_all('meta', name=['image', 'thumbnail'])
            for meta in andere_meta:
                content = meta.get('content')
                if content:
                    meta_afbeeldingen.append({
                        'url': urljoin(url, content),
                        'type': 'meta',
                        'property': meta.get('name'),
                        'alt': f"Meta {meta.get('name')} afbeelding"
                    })
            return meta_afbeeldingen
        except Exception as e:
            print(f"Fout bij meta tag zoeken: {e}")
            return []

def volledig_voorbeeld():
    from eigen_url_scraper import EigenUrlAfbeeldingScraper
    basis_scraper = EigenUrlAfbeeldingScraper()
    geavanceerd_scraper = GeavanceerdeAfbeeldingScraper()
    test_url = "https://www.apple.com"
    print(f"=== VOLLEDIG VOORBEELD: {test_url} ===\n")
    print("1. Basis logo zoeken...")
    logos = basis_scraper.vind_logo_afbeeldingen(test_url)
    print(f"   Gevonden {len(logos)} logo kandidaten")
    print("\n2. CSS selector zoeken...")
    css_selectors = [
        'header img', '.logo img', '#logo img', '[class*="logo"] img', 'nav img', '.navbar img'
    ]
    css_afbeeldingen = geavanceerd_scraper.zoek_afbeeldingen_met_css_selectors(test_url, css_selectors)
    print(f"   Gevonden {len(css_afbeeldingen)} afbeeldingen via CSS selectors")
    print("\n3. JSON-LD structured data zoeken...")
    json_afbeeldingen = geavanceerd_scraper.zoek_afbeeldingen_in_json_ld(test_url)
    print(f"   Gevonden {len(json_afbeeldingen)} afbeeldingen in JSON-LD")
    print("\n4. Meta tags zoeken...")
    meta_afbeeldingen = geavanceerd_scraper.zoek_meta_afbeeldingen(test_url)
    print(f"   Gevonden {len(meta_afbeeldingen)} afbeeldingen in meta tags")
    alle_urls = set()
    for logo in logos:
        alle_urls.add(logo['url'])
    for afbeelding in css_afbeeldingen:
        alle_urls.add(afbeelding['url'])
    for afbeelding in json_afbeeldingen:
        alle_urls.add(afbeelding['url'])
    for afbeelding in meta_afbeeldingen:
        alle_urls.add(afbeelding['url'])
    print(f"\n5. Totaal {len(alle_urls)} unieke afbeelding URLs gevonden")
    print("\n6. Downloaden van afbeeldingen...")
    beste_kandidaten = list(alle_urls)[:5]
    for i, url in enumerate(beste_kandidaten):
        print(f"   Downloaden {i+1}/{len(beste_kandidaten)}: {url}")
        bestand_pad, afmeting, grootte = basis_scraper.download_afbeelding(url, test_url)
        if bestand_pad:
            print(f"      ✓ Opgeslagen: {bestand_pad} ({afmeting})")
        else:
            print(f"      ✗ Fout bij downloaden")
    print("\n=== KLAAR ===")

if __name__ == "__main__":
    volledig_voorbeeld()