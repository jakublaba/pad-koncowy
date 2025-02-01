import pandas as pd
import plotly.express as px
import streamlit as st

from util import TrafficColumn, WeatherColumn, Metric, calculate_traffic_metrics, load_traffic_data, load_weather_data

traffic_df = load_traffic_data()
weather_df = load_weather_data()

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

# ============================== TRAFFIC CATEGORIES ==============================
traffic_groups = [
    TrafficColumn.VEHICLE_NO.value,
    TrafficColumn.BRIGADE.value,
    TrafficColumn.OUTSIDE.value,
    TrafficColumn.DAY_TYPE.value
]

selected_traffic_group = st.selectbox("Kategoria", traffic_groups)
selected_traffic_metric = st.selectbox("Metryka", [e.value for e in Metric])

traffic_metrics_df = (traffic_df
                      .groupby(selected_traffic_group)[[TrafficColumn.DELAY.value]]
                      .apply(calculate_traffic_metrics)
                      .reset_index())

fig = px.bar(
    traffic_metrics_df,
    x=selected_traffic_group,
    y=selected_traffic_metric,
    title=f"{selected_traffic_metric.replace('_', ' ').title()} w kategorii: {selected_traffic_group}",
)
fig.update_layout(
    xaxis_type="category",
    yaxis_title="Opóźnienie (min)"
)
st.plotly_chart(fig)
st.write(
    """
    Po średniej i medianie na pierwszy rzut oka widać kilka ektremalnych przypadków:
    - pojazd 1398 spóźnia się średnio około godziny
    - pojazdy 2058 oraz 2060 spieszą się średnio około 2.5 godziny
    - pojazdy 3604 oraz 3639 spieszą się średnio około godziny
    
    Jest więcej odstających próbek, ale wybrałem najbardziej ekstremalne przypadki. \
    Następnie sprawdziłem odchylenia standardowe i ilości opóźnień.
    - pojazd 1398: niskie odchylenie 0.7 i 2 niezgodności z rozkładem
    - pojazd 2058: wysokie odchylenie 111.3 i 4 niezgodności z rozkładem
    - pojazd 2060: brak odchylenia ponieważ była tylko jedna niezgodność z rozkładem
    - pojazd 3604: wysokie odchylenie 134.7 i 64 niezgodności z rozkładem
    - pojazd 3639: wysokie odchylenie 97.7 i 7 niezgodności z rozkładem
    
    Sprawdziłem te numery w [bazie pojazdów ZTM](https://www.ztm.waw.pl/baza-danych-pojazdow/), z ciekawości czy da się zauważyć jakąś prawidłowość w producencie, typie lub roku produkcji:
    - pojazd 1398: konstal, 105N, 1993
    - pojazd 2058: konstal, 105N, 1999
    - pojazd 2060: konstal, 105N, 1999
    - pojazd 3604: pesa, 128N, 2014
    - pojazd 3639: pesa, 128N, 2015
    
    Przed przystąpieniem do analizy ze względu na brygadę, warto przytoczyć definicję.
    
    > Brygada autobusowa czy tramwajowa oznacza przypisanie kierowcy i pojazdu do kursów, które wykonuje.
    > Każdy pojazd komunikacji miejskiej wykonujący kurs, porusza się po trasie konkretnej linii oraz ma przypisaną brygadę.
    > Na każdej linii może być wiele brygad - tyle ile pojazdów poruszających się w ramach danej linii w danym momencie.
    > Po numerze linii i brygadzie, można sprawdzić rozkład konkretnego autobusu czy tramwaju dla danego dnia.
    > Brygada zazwyczaj jest w formie numeru widocznego na przedniej szybie pojazdu lub w okolicy kierowcy. Każde miasto ma inny system numeracji brygad.
    > Inaczej mówiąc, brygada to zadanie przewozowe przypisane do konkretnego pojazdu i kierowcy, posiadające swój własny rozkład jazdy.
    
    Widać na pierwszy rzut oka kilka ekstremalnych przypadków:
    - brygada 181: średnio 4 godziny przed czasem
    - brygada 186: średnio 3.5 godziny przed czasem
    - brygada 257: średnio 2.5 godziny przed czasem
    Największe spóźnienia nie są aż tak ekstremalne, ale można kilka zaobserwować:
    - brygada 128: średnio 20 minut opóźnienia
    - brygada 174: średnio 24 minuty opóźnienia
    - brygada 184: średnio 23 minuty opóźnienia
    
    Najciekawszą analizą jest jednak ilość opóźnień, ponieważ widać bardzo szczególny schemat, mianowicie
    każda brygada z jednocyfrowym oznaczeniem nieporówywalnie odstaje od całej reszty próbek.
    Z pomocą [brygadowych rozkładów jazdy](https://czynaczas.pl/warsaw/rozklad-jazdy-brygady), sprawdziłem ile przejazdów obsługuje każda
    z jednocyfrowych brygad:
    - brygada 1: 223 w dni powszednie, 184 w weekendy
    - brygada 2: 200 w dni powszednie, 160 w weekendy
    - brygada 3: 164 w dni powszednie, 130 w weekendy
    - brygada 4: 136 w dni powszednie, 105 w weekendy
    - brygada 5: 114 w dni powszednie, 88 w weekendy
    - brygada 6: 92 w dni powszednie, 64 w weekendy
    - brygada 7: 74 w dni powszednie, 48 w weekendy
    - brygada 8: 64 w dni powszednie, 38 w weekendy
    - brygada 9: 53 w dni powszednie, 24 w weekendy
    Widać tutaj 2 rzeczy:
    - jednocyfrowe brygady obsługują dużo więcej przejazdów w porównaniu do innych (zazwyczaj brygady mają ich po kilka lub kilkanaście)
    - od brygady 1 do 9, widać trend spadkowy zarówno w ilości obsługiwanych przejazdów, co intuicyjnie wyjaśnia spadek również ilości spóźnień
    
    Te dane wyjaśnia bardzo dobrze [opis numeracji brygad](http://www.wgkm.waw.pl/portal/index.php/17-inne/126-numeracja-brygad).
    Jednocyfrowe brygady to tzw. "brygady całodziennie", czyli po prostu standardowe codziennie przejazdy.
    Przykłady innych brygad:
    - maratony: występujące z reguły w dni wolne dla wzmocnienia linii, oznaczane literą M, np. M1, M3, itd.
    - wtyczki: kursują na linii, ale nie są wskazane w rozkładzie dla pasażerów - służą do chwilowego wzmocnienia linii
    bez zmiany rozkładu
    """
)
# ===============================================================================
