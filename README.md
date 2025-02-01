# Analiza danych warszawskiego transportu publicznego w grudniu 2024

## Dane

Dane były zbierane z:

- [API IMGW](https://danepubliczne.imgw.pl/pl/apiinfo)
- Wstępnie webscraping z [czynaczas.pl](czynaczas.pl), później po kontakcie z właścicielem serwisu udało się uzyskać
  chwilowy
  dostęp do API
- [FEED GTFS ZA POŚREDNICTWEM mkuran.pl](https://mkuran.pl/)

Za pomocą napisanych przez nas procesów etl dostępnych w
repozytorium [jakublaba/mobility-etl](https://github.com/jakublaba/mobility-etl). \
Proces był hostowany w następujących warunkach:
![](data/server.jpg)

## Jak uruchomić projekt?

### Przygotowanie środowiska wirtualnego

Standardowa procedura w każdym pythonowym projekcie

1. `python -m venv .venv`
2. `. .venv/bin/activate` (Linux/MacOS) lub `. \.venv\Scripts\Activate.ps1` (Windows)
3. `pip install -r requirements.txt`

### Przygotowanie danych

1. Przygotuj token dostępowy w pliku `.env`: `AZURE_CONN_STRING=...`
2. Uruchom skrypt `setup.py` - może to chwilę potrwać, danych jest około 6GB.

### Dashboardy

Projekt zawiera 4 dashboardy:

- `traffic_overview.py` - analiza opóźnień z podziałem na typ pojazdu - autobus, tramwaj, pociąg + mapy cieplne
- `weather.py` - analiza pogody - macierz korelacji oraz porównanie pogody w różne typy dni
- `traffic_categories.py` - analiza opóźnień z podziałem na kategorie - pojazdy, brygady, linie
- `predictions.py` - predykcje średnich opóźnień oraz ilości opóźnień - ogólne oraz z podziałem na kategorie - pojazdy,
  brygady, linie

Uruchamiamy wybrany dashboard komendą:

```
python -m streamlit run dashboards/<dashboard>
```

W przypadku problemów z automatycznym wybraniem portu, może być konieczne ręczne sprecyzowanie go flagą `--server.port`:

```
python -m streamlit run dashboards/<dashboard> --server.port <port>
```

### Juper Notebook

W projekcie mamy też notebook `analiza.ipynb`, zawierający notatki i komentarze do danych i wykresów.
