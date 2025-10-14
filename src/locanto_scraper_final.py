import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
from typing import Dict, List, Optional
import urllib3
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LocantoScraperFinal:
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.proxies = proxy_manager.get_proxy()
        self.session.verify = False
        self.visited_urls = set()
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
    
    def scrape_page(self, url: str) -> Optional[BeautifulSoup]:
        if url in self.visited_urls:
            return None
        
        try:
            print(f"      🔍 {url[:80]}")
            response = self.session.get(url, headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            self.visited_urls.add(url)
            time.sleep(random.uniform(2, 4))
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"         ❌ {str(e)[:60]}")
            return None
    
    def parse_price(self, text: str) -> Dict:
        """Parse prix avec gestion correcte des séparateurs de milliers"""
        if not text:
            return {'price': None, 'currency': None}
        
        # Patterns avec séparateurs
        patterns = [
            # Format français : 16,450 CFA ou 16.450 CFA
            (r'(\d{1,3}(?:[,.\s]\d{3})+)\s*(FCFA|CFA|F\s*CFA|XOF)', lambda m: (m.group(1).replace(',', '').replace('.', '').replace(' ', ''), 'XOF')),
            # Format simple : 16450 CFA
            (r'(\d+)\s*(FCFA|CFA|F\s*CFA|XOF)', lambda m: (m.group(1), 'XOF')),
            # Taka
            (r'(\d{1,3}(?:[,.\s]\d{3})+)\s*(Taka|BDT|৳)', lambda m: (m.group(1).replace(',', '').replace('.', '').replace(' ', ''), 'BDT')),
            (r'(\d+)\s*(Taka|BDT|৳)', lambda m: (m.group(1), 'BDT')),
            # Cedi
            (r'(\d{1,3}(?:[,.\s]\d{3})+)\s*(Cedi|GHS|GH₵)', lambda m: (m.group(1).replace(',', '').replace('.', '').replace(' ', ''), 'GHS')),
            (r'(\d+)\s*(Cedi|GHS|GH₵)', lambda m: (m.group(1), 'GHS')),
            # USD
            (r'\$\s*(\d{1,3}(?:[,]\d{3})+)', lambda m: (m.group(1).replace(',', ''), 'USD')),
            (r'\$\s*(\d+)', lambda m: (m.group(1), 'USD')),
            # EUR
            (r'€\s*(\d{1,3}(?:[,]\d{3})+)', lambda m: (m.group(1).replace(',', ''), 'EUR')),
            (r'€\s*(\d+)', lambda m: (m.group(1), 'EUR')),
        ]
        
        for pattern, processor in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str, currency = processor(match)
                try:
                    price = float(price_str)
                    return {'price': price, 'currency': currency}
                except:
                    continue
        
        return {'price': None, 'currency': None}
    
    def parse_relative_date(self, date_text: str) -> str:
        """Convertit dates relatives en dates réelles"""
        if not date_text:
            return None
        
        date_text_lower = date_text.lower()
        today = datetime.now()
        
        # Français
        if 'aujourd\'hui' in date_text_lower or 'today' in date_text_lower:
            return today.strftime('%Y-%m-%d')
        
        if 'hier' in date_text_lower or 'yesterday' in date_text_lower:
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # "il y a X jours" / "X days ago"
        days_match = re.search(r'(\d+)\s*(jour|day)', date_text_lower)
        if days_match:
            days = int(days_match.group(1))
            return (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # "il y a X semaines" / "X weeks ago"
        weeks_match = re.search(r'(\d+)\s*(semaine|week)', date_text_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return (today - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        
        # "moins d'une semaine" / "less than a week"
        if 'moins d\'une semaine' in date_text_lower or 'less than a week' in date_text_lower:
            return (today - timedelta(days=3)).strftime('%Y-%m-%d')
        
        # "il y a un mois" / "a month ago"
        if 'mois' in date_text_lower or 'month' in date_text_lower:
            return (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Sinon retourner le texte original
        return date_text
    
    def clean_city(self, text: str) -> str:
        """Nettoie le texte de localisation"""
        if not text:
            return None
        
        # Supprimer coordonnées GPS du début
        text = re.sub(r'^[\d\.\-\s]+', '', text)
        text = text.strip(',').strip()
        
        return text if text else None
    
    def get_categories(self, site_url: str) -> List[Dict]:
        """Extrait les catégories"""
        print(f"\n{'='*60}")
        print(f"📂 Extraction catégories")
        print("="*60)
        
        soup = self.scrape_page(site_url)
        if not soup:
            return []
        
        categories = []
        
        # Chercher dans le menu
        cat_links = soup.select('.catlist a, .header_menu a[href*="/"]:not([href*="post"]):not([href*="my"])')
        
        for link in cat_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if text and 5 < len(text) < 50:
                skip = ['help', 'faq', 'contact', 'about', 'terms', 'privacy', 'post', 'sign']
                if any(x in text.lower() or x in href.lower() for x in skip):
                    continue
                
                full_url = urljoin(site_url, href)
                
                if full_url not in [c['url'] for c in categories]:
                    categories.append({
                        'name': text,
                        'url': full_url
                    })
                    print(f"      ✓ {text}")
        
        print(f"\n      Total: {len(categories)} catégories")
        return categories
    
    def get_listings_from_category(self, category_url: str, max_pages: int = 2) -> List[str]:
        """Extrait URLs des annonces"""
        listing_urls = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{category_url}?page={page}" if page > 1 else category_url
            
            soup = self.scrape_page(page_url)
            if not soup:
                break
            
            ad_links = soup.find_all('a', href=re.compile(r'/ID_\d+/.*\.html'))
            
            print(f"         Page {page}: {len(ad_links)} annonces trouvées")
            
            seen_ids = set()
            for link in ad_links:
                href = link.get('href', '')
                id_match = re.search(r'ID_(\d+)', href)
                if not id_match:
                    continue
                
                ad_id = id_match.group(1)
                if ad_id in seen_ids:
                    continue
                seen_ids.add(ad_id)
                
                full_url = urljoin(category_url, href)
                listing_urls.append(full_url)
            
            if not ad_links:
                break
        
        return listing_urls
    
    def get_listing_details(self, listing_url: str) -> Optional[Dict]:
        """Extrait détails complets - VERSION CORRIGÉE"""
        soup = self.scrape_page(listing_url)
        if not soup:
            return None
        
        try:
            # ID
            id_match = re.search(r'ID_(\d+)', listing_url)
            listing_id = id_match.group(1) if id_match else None
            
            # Titre
            title_elem = soup.select_one('h1.h1__title, h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Description - CORRECTION MAJEURE
            desc_elem = soup.select_one('.simple__description')
            description = None
            if desc_elem:
                # Prendre tout le texte sauf les éléments de prix
                desc_text = desc_elem.get_text(strip=True)
                # Supprimer le prix s'il est dans la description
                desc_text = re.sub(r'\d+[\s,.]?\d*\s*(FCFA|CFA|Taka|BDT|Cedi|GHS|USD|EUR|\$|€)', '', desc_text)
                description = desc_text.strip()
            
            # Prix - CORRECTION MAJEURE avec séparateurs
            price_data = {'price': None, 'currency': None}
            
            # Chercher dans plusieurs endroits
            price_sources = [
                soup.select_one('.simple__description'),
                soup.select_one('.simple__price'),
                soup.select_one('[class*="price"]')
            ]
            
            all_text = ' '.join([elem.get_text() for elem in price_sources if elem])
            price_data = self.parse_price(all_text)
            
            # Images
            images = []
            for img in soup.select('.user_images__img, img[alt*="Image"]'):
                src = img.get('src') or img.get('srcset', '').split()[0]
                if src and 'images.locanto' in src:
                    clean_src = src.split()[0] if ' ' in src else src
                    if clean_src not in images:
                        images.append(clean_src)
            
            # Contact - téléphone
            phone = None
            phone_elem = soup.select_one('.button__element_label.js-button_element_label')
            if phone_elem:
                phone_text = phone_elem.get_text(strip=True)
                if re.search(r'\d{3,}', phone_text) and len(phone_text) < 50:
                    phone = phone_text
            
            # Username
            username_elem = soup.select_one('.userprofile__nickname_label')
            username = username_elem.get_text(strip=True) if username_elem else None
            
            # Localisation - nettoyée
            location_elem = soup.select_one('[itemprop="addressLocality"]')
            city_raw = location_elem.get_text(strip=True) if location_elem else None
            city = self.clean_city(city_raw)
            
            # GPS
            lat_elem = soup.select_one('[itemprop="latitude"]')
            lon_elem = soup.select_one('[itemprop="longitude"]')
            latitude = lat_elem.get_text(strip=True) if lat_elem else None
            longitude = lon_elem.get_text(strip=True) if lon_elem else None
            
            # Date - CORRECTION MAJEURE
            posted_elem = soup.select_one('.list__element_label')
            date_posted = None
            if posted_elem:
                text = posted_elem.get_text(strip=True)
                if 'Publié' in text or 'Posted' in text:
                    date_text = text.replace('Publiée: ', '').replace('Posted: ', '')
                    date_posted = self.parse_relative_date(date_text)
            
            # Catégorie
            category_elem = soup.select('.breadcrumb__link')
            category = category_elem[-1].get_text(strip=True) if category_elem else None
            
            listing = {
                'id': listing_id,
                'url': listing_url,
                'title': title,
                'price': price_data['price'],
                'currency': price_data['currency'],
                'description': description,
                'images': images,
                'mainImage': images[0] if images else None,
                'contact': {
                    'username': username,
                    'phone': phone
                },
                'location': {
                    'city': city,
                    'latitude': latitude,
                    'longitude': longitude
                },
                'category': category,
                'datePosted': date_posted,
                'scrapedAt': datetime.now().isoformat()
            }
            
            print(f"            ✅ {title[:40] if title else 'Sans titre'} | {price_data['price']} {price_data['currency']}")
            return listing
            
        except Exception as e:
            print(f"            ⚠️ Erreur: {e}")
            return None
    
    def scrape_site(self, site_url: str, max_categories: int = 3, max_listings: int = 5, max_pages: int = 2) -> Dict:
        """Scrape complet"""
        print(f"\n{'='*60}")
        print(f"🌍 SCRAPING: {site_url}")
        print("="*60)
        
        result = {
            'site_url': site_url,
            'scrape_date': datetime.now().isoformat(),
            'config': {
                'max_categories': max_categories,
                'max_listings': max_listings,
                'max_pages': max_pages
            },
            'categories': []
        }
        
        categories = self.get_categories(site_url)
        
        for i, category in enumerate(categories[:max_categories], 1):
            print(f"\n{'='*60}")
            print(f"📁 [{i}/{min(max_categories, len(categories))}] {category['name']}")
            print(f"   {category['url']}")
            print("="*60)
            
            listing_urls = self.get_listings_from_category(category['url'], max_pages=max_pages)
            print(f"\n   📋 {len(listing_urls)} URLs collectées")
            
            if not listing_urls:
                continue
            
            listings = []
            for j, url in enumerate(listing_urls[:max_listings], 1):
                print(f"   [{j}/{min(max_listings, len(listing_urls))}]", end=' ')
                details = self.get_listing_details(url)
                if details:
                    listings.append(details)
            
            result['categories'].append({
                'name': category['name'],
                'url': category['url'],
                'listings_found': len(listing_urls),
                'listings_scraped': len(listings),
                'listings': listings
            })
            
            print(f"\n   ✅ {len(listings)} annonces extraites")
        
        return result