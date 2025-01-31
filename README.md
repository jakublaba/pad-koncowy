# Analiza danych warszawskiego transportu publicznego w grudniu 2024

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

Projekt zawiera 3 dashboardy:
(todo poprawić nazwy plików bo obecnie są trochę z dupy)

- `dashboard.py` - analiza z podziałem na typ pojazdu (autobus/tramwaj/pociąg)
- `holiday_analysis.py` - macierz korelacji, porównanie pogody i opóźnień z podziałem na różne kategorie
- `predictions.py` - prognozy opóźnień - ogólna, oraz szczegółowe dla każdego pojazdu, każdej brygady oraz linii

Uruchamiamy dashboard komendą:

```
streamlit run <dashboard>
```

W przypadku problemów z automatycznym wybraniem portu, może być konieczne ręczne sprecyzowanie go flagą `--server.port`:

```
streamlit run <dashboard> --server.port <port>
```
