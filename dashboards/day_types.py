import pandas as pd
import plotly.express as px
import streamlit as st
from holidays.countries import Poland

from util import load_traffic_data, load_weather_data, TrafficColumn, WeatherColumn, calculate_delay_stats, DayType, \
    Metric

traffic_df = load_traffic_data()
weather_df = load_weather_data()

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

# ============================== CORRELATION MATRIX ==============================
merged_df = pd.merge(
    weather_df, traffic_df,
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="left",
    validate="1:m"
)
delay_stats_df = calculate_delay_stats(traffic_df)
correlation_df = pd.merge(
    weather_df, delay_stats_df,
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="left",
    validate="1:m"
)
correlation_matrix = correlation_df.corr()
correlation_fig = px.imshow(
    correlation_matrix,
    text_auto=True,
    aspect="auto",
    title="Macierz korelacji"
)
st.plotly_chart(correlation_fig)
st.write(
    """
    Interesuje nas tutaj tak naprawdę tylko lewa dolna ćwiartka - korelacja różnych czynników pogodowych z metrykami
    opóźnień. Możemy zaobserwować bardzo niskie korelacje, w większości nie przekraczające 0.15, w dużej ilości przypadków
    również ujemne. Najmocniejszą korelacją jest tutaj prędkość wiatru i ilość opóźnień, ale nadal nie jest ona szczególnie
    silna, bo zaledwie 0.25.
    Wbrew oczekiwaniom, okazuje się że pogoda nie miała szczególnego wpływu na opóźnienia transportu publicznego.
    """
)
# ================================================================================

# ============================== WEATHER STATS =====================================
start_date = min(
    traffic_df[TrafficColumn.TIMESTAMP.value].min(),
    weather_df[WeatherColumn.TIMESTAMP.value].min()
)
end_date = max(
    traffic_df[TrafficColumn.TIMESTAMP.value].max(),
    weather_df[WeatherColumn.TIMESTAMP.value].max()
)

pl_holidays = [
    pd.Timestamp(date) for date in
    Poland(years=range(start_date.year, end_date.year + 1))
]


def get_day_type(date):
    date = pd.Timestamp(date)
    if date in pl_holidays:
        return DayType.HOLIDAY.value
    elif date.weekday() >= 5:
        return DayType.WEEKEND.value
    else:
        return DayType.WEEKDAY.value


traffic_df[TrafficColumn.DAY_TYPE.value] = traffic_df[TrafficColumn.TIMESTAMP.value].dt.date.apply(get_day_type)
weather_df[WeatherColumn.DAY_TYPE.value] = weather_df[WeatherColumn.TIMESTAMP.value].dt.date.apply(get_day_type)

weather_holiday_analysis = {
    Metric.MEAN.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).mean().reset_index(),
    Metric.MEDIAN.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).median().reset_index(),
    Metric.STD_DEV.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).std().reset_index(),
    Metric.Q1.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).quantile(0.25).reset_index(),
    Metric.Q3.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).quantile(0.75).reset_index(),
}

selected_weather_metric = st.selectbox(
    "Metryka",
    [e.value for e in Metric if e != Metric.COUNT]
)
selected_weather_param = st.selectbox(
    "Parametr pogody",
    [
        WeatherColumn.TEMPERATURE.value,
        WeatherColumn.WIND_SPEED.value,
        WeatherColumn.HUMIDITY.value,
        WeatherColumn.RAINFALL.value,
        WeatherColumn.PRESSURE.value,
    ]
)

avg_weather_params_fig = px.bar(
    weather_holiday_analysis[selected_weather_metric][[
        WeatherColumn.DAY_TYPE.value,
        selected_weather_param
    ]],
    x=WeatherColumn.DAY_TYPE.value,
    y=selected_weather_param,
    title=f"{selected_weather_metric} dla parametru: {selected_weather_param}",
)

st.plotly_chart(avg_weather_params_fig)
st.write(
    """
    - **Temperatura** - nieznaczne różnice - średnia i mediana pomiędzy dniami roboczymi, weekendami i świętami różnią się
    zaledwie o 1 lub 0.5 stopnia
    - **Prędkość wiatru** - różnice znów są niezbyt znaczące, około 1km/h
    - **Wilgotność względna** - niewielkie różnice, w święta około 15pp mniej wilgotno
    - **Suma opadów** - pierwszy czynnik pogodowy, w którym widać wyraźną różnicę - w porównaniu do dni roboczych,
    w weekendy i święta praktycznie nie padało. Weekendy i święta mają bardzo niskie odchylenie standardowe w tej kategorii,
    więc widać że średnia suma opadów nie jest zaniżona przez mocno odstające próbki.
    - **Ciśnienie** - nie widać istotnej różnicy, wszystkie metryki na podobnym poziomie.
    """
)
# ================================================================================

# ============================== GLOBAL DELAY STATS ==============================
delay_stats = {
    Metric.MEAN.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].mean().reset_index(),
    Metric.MEDIAN.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[
        TrafficColumn.DELAY.value].median().reset_index(),
    Metric.STD_DEV.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[
        TrafficColumn.DELAY.value].std().reset_index(),
    Metric.Q1.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].quantile(
        0.25).reset_index(),
    Metric.Q3.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].quantile(
        0.75).reset_index(),
    Metric.COUNT.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[
        TrafficColumn.DELAY.value].count().reset_index(),
}

selected_delay_stat = st.selectbox(
    "Metryka",
    [e.value for e in Metric]
)

delay_stats_fig = px.bar(
    delay_stats[selected_delay_stat],
    x=TrafficColumn.DAY_TYPE.value,
    y=TrafficColumn.DELAY.value,
    title=f"{selected_delay_stat} opóźnień dla różnych typów dni",
    labels={TrafficColumn.DAY_TYPE.value: "Typ dnia", TrafficColumn.DELAY.value: "Opóźnienie (minuty)"}
)

st.plotly_chart(delay_stats_fig)
st.write(
    """
    Dni robocze odstają zarówno wysoką średnią jak i medianą, podczas kiedy odchylenia standardowe są na podobnym poziomie.
    Można więc stwierdzić że w dni robocze opóźnienia zazwyczaj są dłuższe.
    Warto wziąć tutaj pod uwagę, że spieszenie się pojazdów jest oznaczone przez ujemne opóźnienie - to może oznaczać również że
    w weekendy oraz święta pojazdy bardziej się spieszą - jest to zgodne z intuicją, w te dni zazwyczaj na drogach jest mniejszy ruch.
    Przy ilości opóźnień nie do końca dobrze skonstruowaliśmy wykres - widać na nim sumaryczną ilość ze wszystkich dni w danej kategorii,
    więc logiczne że w dni robocze będzie ich najwięcej.
    Powinniśmy rozważyć średnią ilość opóźnień dziennie, w rozpatrywanym okresie wystąpiło:
    - 15 dni roboczych
    - 8 dni weekendowych
    - 3 dni świąteczne
    
    Średnia ilość opóźnień w:
    - dni robocze: $205.323.000 \div 15 = 13.688.200$
    - weekendy: $84.768.000 \div 8 = 10.596.000$
    - święta: $28.918.000 \div 3 = 9.639.333,(3)$
    
    Nadal z danych wynika, że transport najczęściej spóźnia się w dni powszednie a najrzadziej w święta, jednak nie jest to już
    tak kolosalna różnica.
    Warto tutaj wspomnieć, że na wykresie z dashboardu traffic_overview widać wzrost opóźnień tuż przed okresem świątecznym, a następnie
    spadek w same święta - jest to zgodne z intuicją, dużo osób wyjeżdża na święta do rodziny w tym okresie, co powoduje wzmożony ruch.
    """
)
# ================================================================================
