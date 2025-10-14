import os
from urllib.parse import quote
from typing import Dict, Optional
import urllib3

# Désactiver les warnings SSL (car Oxylabs utilise son propre certificat)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxyManager:
    def __init__(self):
        self.service = os.getenv('PROXY_SERVICE', 'oxylabs')
    
    def get_oxylabs_proxy(self) -> Dict[str, str]:
        """Configure Oxylabs Web Unblocker (celui qui fonctionne avec curl)"""
        username = os.getenv('OXYLABS_USERNAME')
        password = os.getenv('OXYLABS_PASSWORD')
        
        # Encoder le mot de passe pour gérer les caractères spéciaux
        encoded_password = quote(password, safe='')
        
        # Web Unblocker - celui qui fonctionne avec ton curl
        proxy_url = f'http://{username}:{encoded_password}@unblock.oxylabs.io:60000'
        
        print(f"🔐 Utilisation Web Unblocker: http://{username}:***@unblock.oxylabs.io:60000")
        
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
        
        encoded_password = quote(password, safe='')
        proxy_url = f'http://{username}:{encoded_password}@{host}:{port}'
        
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
        """Test le proxy configuré avec la bonne config SSL"""
        import requests
        
        proxies = self.get_proxy()
        
        if self.service == 'oxylabs':
            test_url = 'https://ip.oxylabs.io/location'
        else:
            test_url = 'https://geo.brdtest.com/welcome.txt'
        
        try:
            print(f"🧪 Test du proxy vers {test_url}...")
            
            # IMPORTANT : verify=False pour Oxylabs Web Unblocker
            response = requests.get(
                test_url, 
                proxies=proxies, 
                timeout=30,
                verify=False  # Désactive la vérification SSL
            )
            
            print(f"✅ Proxy {self.service} OK: {response.status_code}")
            print(f"📍 Réponse:\n{response.text[:400]}")
            
            # Afficher les headers Oxylabs
            if 'X-Oxylabs-Client-Id' in response.headers:
                print(f"🆔 Client ID: {response.headers.get('X-Oxylabs-Client-Id')}")
                print(f"📊 Job ID: {response.headers.get('X-Oxylabs-Job-Id')}")
            
            return True
            
        except requests.exceptions.SSLError as e:
            print(f"❌ Erreur SSL: {e}")
            print("💡 Vérifie que verify=False est bien utilisé")
            return False
            
        except requests.exceptions.ProxyError as e:
            print(f"❌ Erreur d'authentification proxy: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Erreur proxy {self.service}: {e}")
            return False