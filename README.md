# Locanto Scraper

Scraper automatique pour extraire les annonces de tous les pays Locanto.

## Installation
```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec tes credentials Oxylabs
nano .env

# Lancer le scraper
docker-compose up --build
```

## Utilisation

### Scraping automatique de tous les pays
```bash
docker-compose run --rm scraper python src/scrape_all_countries.py
```

### Scraping d'un pays spécifique
```bash
SITE_URL=https://abidjan.locanto.ci/ docker-compose run --rm scraper python src/scrape_full_country.py
```

## Structure des données

Les résultats sont sauvegardés dans `/data/countries/`



##  Structure 
```
scraper-project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .gitignore
├── README.md                      #  créer
├── src/
│   ├── __init__.py               # Vide
│   ├── proxy_manager.py          # Gestion proxy
│   ├── locanto_scraper_final.py  # Scraper principal
│   ├── scrape_all_countries.py   # Script maître
│   └── scrape_full_country.py    # Scraping pays unique
├── data/
│   ├── countries/                # Résultats multi-pays
│   ├── full_scrapes/             # Résultats scraping complet
│   └── inspection/               # Debug (peut supprimer)
└── logs/                          # Logs (optionnel)


## Scraping automatique de tous les pays
docker-compose run --rm scraper python src/scrape_all_countries.py

## Avec filtres
TARGET_COUNTRIES="ci,ng,gh" docker-compose run --rm scraper python src/scrape_all_countries.py

# Un seul pays
SITE_URL=https://abidjan.locanto.ci/ docker-compose run --rm scraper python src/scrape_full_country.py