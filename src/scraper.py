import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
from typing import Dict, List, Optional

class WebScraper:
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.proxies = proxy_manager.get_proxy()
    
    def get_headers(self) -> Dict[str, str]:
        """Headers réalistes pour éviter la détection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def scrape_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Scrape une page avec retry automatique"""
        for attempt in range(retries):
            try:
                print(f"🔍 Scraping: {url} (tentative {attempt + 1}/{retries})")
                
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30,
                    verify=True
                )
                
                response.raise_for_status()
                
                # Délai aléatoire pour paraître humain
                time.sleep(random.uniform(2, 5))
                
                soup = BeautifulSoup(response.content, 'lxml')
                print(f"✅ Page récupérée: {len(response.content)} bytes")
                
                return soup
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Erreur tentative {attempt + 1}: {e}")
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⏳ Attente {wait_time}s avant retry...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Échec après {retries} tentatives")
                    return None
    
    def scrape_locanto(self, base_url: str = "https://www.locanto.info/") -> List[Dict]:
        """Scrape Locanto et ses filiales"""
        results = []
        
        soup = self.scrape_page(base_url)
        if not soup:
            return results
        
        # Exemple d'extraction (à adapter selon la structure de Locanto)
        # Ici on récupère les liens de catégories
        categories = soup.find_all('a', class_='category-link')  # Adapter le sélecteur
        
        for cat in categories[:5]:  # Limiter pour le test
            title = cat.get_text(strip=True)
            link = cat.get('href')
            
            if link and not link.startswith('http'):
                link = base_url.rstrip('/') + '/' + link.lstrip('/')
            
            results.append({
                'title': title,
                'url': link,
                'source': 'locanto'
            })
            
            print(f"📌 Trouvé: {title}")
        
        return results
    
    def extract_listing_data(self, soup: BeautifulSoup) -> Dict:
        """Extrait les données d'une annonce"""
        # À personnaliser selon tes besoins
        data = {
            'title': soup.find('h1', class_='title').get_text(strip=True) if soup.find('h1', class_='title') else None,
            'price': soup.find('span', class_='price').get_text(strip=True) if soup.find('span', class_='price') else None,
            'description': soup.find('div', class_='description').get_text(strip=True) if soup.find('div', class_='description') else None,
            'contact': soup.find('div', class_='contact').get_text(strip=True) if soup.find('div', class_='contact') else None,
        }
        return data