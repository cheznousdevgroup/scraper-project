import os
from dotenv import load_dotenv
from proxy_manager import ProxyManager
from locanto_scraper_final import LocantoScraperFinal
import json
import time
from datetime import datetime
import re
from urllib.parse import urljoin

def save_checkpoint(data: dict, filename: str):
    """Sauvegarde progressive"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_country_domains(proxy_manager) -> list:
    """
    Step 1: Récupère TOUS les domaines de pays depuis locanto.info
    """
    print("="*70)
    print("🌍 ÉTAPE 1 : RÉCUPÉRATION DES DOMAINES DE TOUS LES PAYS")
    print("="*70)
    
    scraper = LocantoScraperFinal(proxy_manager)
    
    # Page index globale
    index_url = "https://www.locanto.info"
    print(f"\n📍 Récupération depuis : {index_url}")
    
    soup = scraper.scrape_page(index_url)
    if not soup:
        print("❌ Impossible de charger l'index global")
        return []
    
    countries = []
    
    # Chercher tous les liens vers les sites de pays
    # Pattern : locanto.TLD ou subdomain.locanto.TLD
    all_links = soup.find_all('a', href=True)
    
    seen_domains = set()
    
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Filtrer les liens vers des sites Locanto
        # Exemples : www.locanto.ci, www.locanto.com.ng, fr.locanto.be, etc.
        if 'locanto' in href and not 'locanto.info' in href:
            # Extraire le domaine complet
            domain_match = re.search(r'https?://([^/]+)', href)
            if domain_match:
                domain = domain_match.group(1)
                
                # Éviter les doublons
                if domain in seen_domains:
                    continue
                
                # Éviter les liens internes/système
                if any(x in domain for x in ['static', 'api', 'admin', 'cdn']):
                    continue
                
                seen_domains.add(domain)
                
                # Construire l'URL complète
                full_url = f"https://{domain}/"
                
                countries.append({
                    'name': text or domain,
                    'domain': domain,
                    'url': full_url
                })
                
                print(f"   ✓ {text or domain} → {domain}")
    
    print(f"\n📊 Total : {len(countries)} pays trouvés")
    
    return countries

def scrape_country(scraper, country: dict, config: dict, output_dir: str):
    """
    Scrape un pays complet
    """
    print(f"\n{'='*70}")
    print(f"🌍 SCRAPING : {country['name']}")
    print(f"   URL : {country['url']}")
    print("="*70)
    
    start_time = time.time()
    
    try:
        # Scraper le pays
        result = scraper.scrape_site(
            country['url'],
            max_categories=config['max_categories'],
            max_listings=config['max_listings'],
            max_pages=config['max_pages']
        )
        
        # Ajouter métadonnées
        result['country_name'] = country['name']
        result['country_domain'] = country['domain']
        
        # Stats
        total_listings = sum(len(cat['listings']) for cat in result['categories'])
        duration = time.time() - start_time
        
        result['stats'] = {
            'total_listings': total_listings,
            'total_categories': len(result['categories']),
            'duration_seconds': round(duration, 2),
            'listings_per_minute': round(total_listings / (duration/60), 2) if duration > 0 else 0
        }
        
        # Nom de fichier basé sur le domaine
        # Ex: locanto.ci → ci.json, www.locanto.com.ng → ng.json
        domain_parts = country['domain'].replace('www.', '').split('.')
        if len(domain_parts) >= 2:
            if 'locanto' in domain_parts:
                # Prendre ce qui est après 'locanto'
                country_code = '.'.join(domain_parts[domain_parts.index('locanto')+1:])
            else:
                country_code = domain_parts[-1]
        else:
            country_code = country['domain'].replace('.', '_')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/{country_code}_{timestamp}.json"
        
        # Sauvegarder
        save_checkpoint(result, filename)
        
        print(f"\n{'='*70}")
        print(f"✅ {country['name']} TERMINÉ")
        print(f"   📊 {total_listings} annonces en {duration/60:.1f} minutes")
        print(f"   💾 {filename}")
        print("="*70)
        
        return {
            'country': country['name'],
            'domain': country['domain'],
            'success': True,
            'listings': total_listings,
            'categories': len(result['categories']),
            'duration': duration,
            'filename': filename
        }
        
    except Exception as e:
        print(f"\n❌ ERREUR pour {country['name']}: {e}")
        return {
            'country': country['name'],
            'domain': country['domain'],
            'success': False,
            'error': str(e)
        }

def main():
    load_dotenv()
    
    print("="*70)
    print("🕷️  LOCANTO SCRAPER - SCRAPING MULTI-PAYS AUTOMATIQUE")
    print("="*70)
    
    # Init proxy
    proxy_manager = ProxyManager()
    if not proxy_manager.test_proxy():
        return
    
    scraper = LocantoScraperFinal(proxy_manager)
    
    # Config
    config = {
        'max_categories': int(os.getenv('MAX_CATEGORIES', 999)),
        'max_listings': int(os.getenv('MAX_LISTINGS', 50)),
        'max_pages': int(os.getenv('MAX_PAGES', 5))
    }
    
    # Filtres optionnels
    target_countries = os.getenv('TARGET_COUNTRIES', '')  # Ex: "ci,ng,gh" pour filtrer
    skip_countries = os.getenv('SKIP_COUNTRIES', '')  # Ex: "de,fr" pour ignorer
    
    print(f"\n⚙️  CONFIGURATION")
    print(f"   Catégories max: {config['max_categories'] if config['max_categories'] < 999 else 'TOUTES'}")
    print(f"   Annonces/catégorie: {config['max_listings']}")
    print(f"   Pages/catégorie: {config['max_pages']}")
    
    if target_countries:
        print(f"   Filtre pays: {target_countries}")
    if skip_countries:
        print(f"   Ignorer pays: {skip_countries}")
    
    # Output directory
    output_dir = '/app/data/countries'
    os.makedirs(output_dir, exist_ok=True)
    
    # ÉTAPE 1 : Récupérer tous les pays
    countries = get_all_country_domains(proxy_manager)
    
    if not countries:
        print("\n❌ Aucun pays trouvé")
        return
    
    # Appliquer filtres
    if target_countries:
        target_list = [c.strip().lower() for c in target_countries.split(',')]
        countries = [c for c in countries if any(t in c['domain'].lower() for t in target_list)]
        print(f"\n🎯 {len(countries)} pays après filtre TARGET_COUNTRIES")
    
    if skip_countries:
        skip_list = [c.strip().lower() for c in skip_countries.split(',')]
        countries = [c for c in countries if not any(s in c['domain'].lower() for s in skip_list)]
        print(f"\n⏭️  {len(countries)} pays après filtre SKIP_COUNTRIES")
    
    print(f"\n{'='*70}")
    print(f"🚀 LANCEMENT DU SCRAPING DE {len(countries)} PAYS")
    print("="*70)
    
    # ÉTAPE 2 : Scraper chaque pays
    results = []
    global_start = time.time()
    
    for i, country in enumerate(countries, 1):
        print(f"\n\n{'#'*70}")
        print(f"# PAYS {i}/{len(countries)}")
        print(f"{'#'*70}")
        
        result = scrape_country(scraper, country, config, output_dir)
        results.append(result)
        
        # Pause entre pays
        if i < len(countries):
            print(f"\n⏸️  Pause 5 secondes avant le prochain pays...")
            time.sleep(5)
    
    # RAPPORT FINAL
    global_duration = time.time() - global_start
    
    print(f"\n\n{'='*70}")
    print(f"🎉 SCRAPING MULTI-PAYS TERMINÉ")
    print("="*70)
    
    success_count = sum(1 for r in results if r.get('success'))
    total_listings = sum(r.get('listings', 0) for r in results if r.get('success'))
    
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"   • Durée totale: {global_duration/60:.1f} minutes ({global_duration/3600:.1f}h)")
    print(f"   • Pays réussis: {success_count}/{len(countries)}")
    print(f"   • Annonces totales: {total_listings}")
    print(f"   • Vitesse moyenne: {total_listings/(global_duration/60):.1f} annonces/min")
    
    print(f"\n📈 TOP 10 PAYS PAR NOMBRE D'ANNONCES:")
    top_countries = sorted([r for r in results if r.get('success')], 
                          key=lambda x: x.get('listings', 0), reverse=True)[:10]
    for i, r in enumerate(top_countries, 1):
        print(f"   {i}. {r['country']}: {r['listings']} annonces")
    
    # Pays en erreur
    failed = [r for r in results if not r.get('success')]
    if failed:
        print(f"\n⚠️  PAYS EN ERREUR ({len(failed)}):")
        for r in failed:
            print(f"   • {r['country']}: {r.get('error', 'Unknown error')}")
    
    # Sauvegarder rapport global
    report_file = f"{output_dir}/scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        'start_time': datetime.now().isoformat(),
        'duration_seconds': global_duration,
        'config': config,
        'total_countries': len(countries),
        'successful_countries': success_count,
        'total_listings': total_listings,
        'countries': results
    }
    save_checkpoint(report, report_file)
    
    print(f"\n💾 Rapport global: {report_file}")
    print(f"📁 Données pays: {output_dir}/")
    print("="*70)

if __name__ == "__main__":
    main()