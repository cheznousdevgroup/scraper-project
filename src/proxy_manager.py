import os
from urllib.parse import quote
from typing import Dict, Optional

class ProxyManager:
    def __init__(self):
        self.service = os.getenv('PROXY_SERVICE', 'oxylabs')
    
    def get_oxylabs_proxy(self) -> Dict[str, str]:
        """Configure Oxylabs proxy"""
        username = os.getenv('OXYLABS_USERNAME')
        password = os.getenv('OXYLABS_PASSWORD')
        country = os.getenv('OXYLABS_COUNTRY', 'US')
        
        # Pour Web Unblocker (recommandé pour scraping)
        proxy_url = f'http://customer-{username}-cc-{country}:{password}@pr.oxylabs.io:7777'
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_brightdata_proxy(self) -> Dict[str, str]:
        """Configure BrightData proxy"""
        host = os.getenv('BRIGHTDATA_HOST')
        port = os.getenv('BRIGHTDATA_PORT')
        username = os.getenv('BRIGHTDATA_USERNAME')
        password = os.getenv('BRIGHTDATA_PASSWORD')
        
        proxy_url = f'http://{username}:{password}@{host}:{port}'
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_proxy(self) -> Dict[str, str]:
        """Retourne le proxy selon le service configuré"""
        if self.service == 'oxylabs':
            return self.get_oxylabs_proxy()
        elif self.service == 'brightdata':
            return self.get_brightdata_proxy()
        else:
            raise ValueError(f"Service proxy inconnu: {self.service}")
    
    def test_proxy(self) -> bool:
        """Test le proxy configuré"""
        import requests
        
        proxies = self.get_proxy()
        test_url = 'https://ip.oxylabs.io/location' if self.service == 'oxylabs' else 'https://geo.brdtest.com/welcome.txt'
        
        try:
            response = requests.get(test_url, proxies=proxies, timeout=30)
            print(f"✅ Proxy {self.service} OK: {response.status_code}")
            print(f"📍 Info: {response.text[:200]}")
            return True
        except Exception as e:
            print(f"❌ Erreur proxy {self.service}: {e}")
            return False