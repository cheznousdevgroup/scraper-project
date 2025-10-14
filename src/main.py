import os
from dotenv import load_dotenv
from proxy_manager import ProxyManager
from scraper import WebScraper
import json

def main():
    # Chargement des variables d'environnement
    load_dotenv()
    
    print("=" * 50)
    print("🕷️  Outil de Scraping Web")
    print("=" * 50)
    
    # Initialisation du proxy
    proxy_manager = ProxyManager()
    print(f"\n📡 Service proxy: {proxy_manager.service.upper()}")
    
    # Test du proxy
    if not proxy_manager.test_proxy():
        print("❌ Impossible de continuer sans proxy fonctionnel")
        return
    
    # Initialisation du scraper
    scraper = WebScraper(proxy_manager)
    
    # Target URL
    target_url = os.getenv('TARGET_URL', 'https://www.locanto.info/')
    print(f"\n🎯 Cible: {target_url}")
    
    # Scraping
    print("\n" + "=" * 50)
    print("Début du scraping...")
    print("=" * 50 + "\n")
    
    results = scraper.scrape_locanto(target_url)
    
    # Sauvegarde des résultats
    output_file = '/app/data/results.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {len(results)} résultats sauvegardés dans {output_file}")
    
    # Affichage résumé
    print("\n" + "=" * 50)
    print("📊 Résumé")
    print("=" * 50)
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result.get('title', 'N/A')}")

if __name__ == "__main__":
    main()