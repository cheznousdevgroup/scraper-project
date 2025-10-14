import os
from dotenv import load_dotenv
from proxy_manager import ProxyManager
from locanto_scraper_final import LocantoScraperFinal
import json
import time
from datetime import datetime

def save_checkpoint(data: dict, filename: str):
    """Sauvegarde progressive"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    load_dotenv()
    
    print("="*70)
    print("🕷️  LOCANTO SCRAPER - PRODUCTION - SCRAPING COMPLET")
    print("="*70)
    
    # Init
    proxy_manager = ProxyManager()
    if not proxy_manager.test_proxy():
        return
    
    scraper = LocantoScraperFinal(proxy_manager)
    
    # Config
    site_url = os.getenv('SITE_URL', 'https://abidjan.locanto.ci/')
    max_categories = int(os.getenv('MAX_CATEGORIES', 999))  # Toutes les catégories
    max_listings = int(os.getenv('MAX_LISTINGS', 50))  # 50 annonces par catégorie
    max_pages = int(os.getenv('MAX_PAGES', 5))  # 5 pages par catégorie
    
    print(f"\n⚙️  CONFIGURATION")
    print(f"   Site: {site_url}")
    print(f"   Catégories max: {max_categories if max_categories < 999 else 'TOUTES'}")
    print(f"   Annonces/catégorie: {max_listings}")
    print(f"   Pages/catégorie: {max_pages}")
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    country = site_url.split('//')[1].split('.')[0].replace('www', 'main')
    
    output_dir = '/app/data/full_scrapes'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/{country}_{timestamp}.json"
    
    print(f"   Sortie: {filename}")
    print(f"\n{'='*70}")
    
    start_time = time.time()
    
    # Début du scraping
    result = {
        'site_url': site_url,
        'scrape_date': datetime.now().isoformat(),
        'config': {
            'max_categories': max_categories,
            'max_listings_per_category': max_listings,
            'max_pages_per_category': max_pages
        },
        'categories': [],
        'stats': {
            'total_listings': 0,
            'total_categories': 0,
            'errors': 0
        }
    }
    
    print(f"\n🌍 SCRAPING: {site_url}\n")
    print("="*70)
    
    # Extraire catégories
    categories = scraper.get_categories(site_url)
    
    if not categories:
        print("❌ Aucune catégorie trouvée")
        return
    
    total_cats = min(len(categories), max_categories)
    
    # Scraper chaque catégorie
    for i, category in enumerate(categories[:max_categories], 1):
        try:
            print(f"\n{'='*70}")
            print(f"📁 [{i}/{total_cats}] {category['name']}")
            print(f"   {category['url']}")
            print("="*70)
            
            # Extraire URLs annonces
            listing_urls = scraper.get_listings_from_category(category['url'], max_pages=max_pages)
            print(f"\n   📋 {len(listing_urls)} URLs collectées")
            
            if not listing_urls:
                print(f"   ⚠️ Aucune annonce dans cette catégorie")
                continue
            
            # Extraire détails
            listings = []
            errors = 0
            
            for j, url in enumerate(listing_urls[:max_listings], 1):
                print(f"   [{j}/{min(max_listings, len(listing_urls))}]", end=' ')
                
                try:
                    details = scraper.get_listing_details(url)
                    if details:
                        listings.append(details)
                except Exception as e:
                    errors += 1
                    print(f"      ❌ Erreur: {str(e)[:40]}")
            
            cat_data = {
                'name': category['name'],
                'url': category['url'],
                'listings_found': len(listing_urls),
                'listings_scraped': len(listings),
                'listings': listings,
                'errors': errors
            }
            
            result['categories'].append(cat_data)
            result['stats']['total_listings'] += len(listings)
            result['stats']['total_categories'] += 1
            result['stats']['errors'] += errors
            
            # Sauvegarde progressive tous les 5 catégories
            if i % 5 == 0:
                save_checkpoint(result, filename)
                print(f"\n   💾 Checkpoint sauvegardé ({i} catégories)")
            
            print(f"\n   ✅ {len(listings)} annonces extraites ({errors} erreurs)")
            
            # Pause entre catégories
            if i < total_cats:
                time.sleep(3)
        
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Interruption utilisateur")
            break
        except Exception as e:
            print(f"\n   ❌ Erreur catégorie: {e}")
            result['stats']['errors'] += 1
            continue
    
    # Sauvegarde finale
    save_checkpoint(result, filename)
    
    # Stats finales
    duration = time.time() - start_time
    
    print(f"\n{'='*70}")
    print(f"✅ SCRAPING TERMINÉ")
    print("="*70)
    print(f"\n📊 STATISTIQUES:")
    print(f"   • Durée totale: {duration/60:.1f} minutes")
    print(f"   • Catégories scrapées: {result['stats']['total_categories']}")
    print(f"   • Annonces extraites: {result['stats']['total_listings']}")
    print(f"   • Erreurs: {result['stats']['errors']}")
    print(f"   • Vitesse: {result['stats']['total_listings']/(duration/60):.1f} annonces/min")
    
    # Top catégories
    print(f"\n📈 TOP 5 CATÉGORIES:")
    top_cats = sorted(result['categories'], key=lambda x: len(x['listings']), reverse=True)[:5]
    for i, cat in enumerate(top_cats, 1):
        print(f"   {i}. {cat['name']}: {len(cat['listings'])} annonces")
    
    print(f"\n💾 Fichier: {filename}")
    print(f"\n{'='*70}")
    
    # Générer rapport CSV
    csv_filename = filename.replace('.json', '_summary.csv')
    with open(csv_filename, 'w', encoding='utf-8') as f:
        f.write("Catégorie,URL,Annonces Trouvées,Annonces Extraites,Erreurs\n")
        for cat in result['categories']:
            f.write(f'"{cat["name"]}","{cat["url"]}",{cat["listings_found"]},{cat["listings_scraped"]},{cat["errors"]}\n')
    
    print(f"📄 Rapport CSV: {csv_filename}\n")

if __name__ == "__main__":
    main()