import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Load the datasets
delays = pd.read_csv('../data/traffic/delays-merged.csv')
weather = pd.read_csv('../data/weather/weather-merged.csv')
stops = pd.read_csv('../data/gtfs/2025/01/03/stops.csv')

# Convert timestamp columns to datetime
delays['timestamp'] = pd.to_datetime(delays['Timestamp'])
weather['timestamp'] = pd.to_datetime(weather['timestamp'])

# Extract date and hour from timestamp
delays['date'] = delays['timestamp'].dt.date
delays['hour'] = delays['timestamp'].dt.hour
weather['date'] = weather['timestamp'].dt.date
weather['hour'] = weather['timestamp'].dt.hour

# Merge delays with stop locations by stop_name
delays['stop_name'] = delays['Stop Name']
delays['vehicle_type'] = delays['Type']
delays_with_stops = pd.merge(delays, stops, left_on='stop_name', right_on='stop_name')

col1, col2 = st.columns([3, 1])
with col1:
    st.title('Analiza Opóźnień Transportu Publicznego w Warszawie')
with col2:
    transport_type = st.selectbox("Wybierz Typ Transportu", ('Autobus', 'Tramwaj', 'Pociąg'))

# Filter data based on selected transport type
filtered_delays = delays[delays['vehicle_type'] == transport_type]
filtered_delays_with_stops = delays_with_stops[delays_with_stops['vehicle_type'] == transport_type]

# Create tabs
tab1, tab2, tab3 = st.tabs(["Warunki pogodowe", "Trendy czasowe", "Mapa opóźnień"])

st.markdown("""
    <style>
    .metric-container {
        background-color: rgb(240, 242, 246);
        border-radius: 5px;
        padding: 5px;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

with tab1:
    st.header(f'Średnie Opóźnienie vs. Warunki Pogodowe (wszystkie typy pojazdów)')

    # Merge datasets on date and hour
    merged_data = pd.merge(delays, weather, on=['date', 'hour'])

    # Define weather factors
    weather_factors = {
        'Temperatura': 'temperatura',
        'Prędkość wiatru': 'predkosc_wiatru',
        'Opady': 'suma_opadu'
    }

    # Select weather factor
    weather_factor = st.selectbox("Wybierz Czynnik Pogodowy", list(weather_factors.keys()))
    weather_column = weather_factors[weather_factor]

    # Regular Conditions Section
    st.subheader('Regularne Warunki')
    avg_weather = merged_data[weather_column].mean()
    avg_delay = merged_data['Delay'].mean()

    col1, col2 = st.columns(2)
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    with col1:

        st.metric(label=f"Średnia {weather_factor}", value=f"{avg_weather:.2f}")

    with col2:
        st.metric(label="Średnie Opóźnienie (minuty)", value=f"{avg_delay:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)
    fig = px.scatter(merged_data, x=weather_column, y='Delay',
                     labels={weather_column: weather_factor, 'Delay': 'Opóźnienie (minuty)'},
                     title=f'Opóźnienie vs. {weather_factor}')
    st.plotly_chart(fig)

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Challenging Conditions Section
    st.subheader('Trudne Warunki')

    # Define challenging weather conditions
    challenging_conditions = {
        'Opady': merged_data['suma_opadu'] > 7.6,
        'Prędkość wiatru': merged_data['predkosc_wiatru'] > 8,
        'Temperatura': merged_data['temperatura'] < 0
    }

    condition = challenging_conditions[weather_factor]
    filtered_data = merged_data[condition]

    # Calculate daily mean delay and weather factor
    daily_mean_delay = filtered_data.groupby('date')['Delay'].mean()
    daily_mean_weather_factor = filtered_data.groupby('date')[weather_column].mean()
    challenging_data = pd.DataFrame(
        {'mean_delay': daily_mean_delay, 'mean_weather_factor': daily_mean_weather_factor}).dropna()

    # Display metrics in rows and columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Średnia Temperatura (°C)", value=f"{filtered_data['temperatura'].mean():.2f}")
        st.metric(label="Najniższa Temperatura (°C)", value=f"{filtered_data['temperatura'].min():.2f}")
    with col2:
        st.metric(label="Średnia Prędkość Wiatru (m/s)", value=f"{filtered_data['predkosc_wiatru'].mean():.2f}")
        lowest_temp_date = filtered_data.loc[filtered_data['temperatura'].idxmin(), 'date']
        st.metric(label="Dzień z Najniższą Temperaturą", value=lowest_temp_date.strftime('%Y-%m-%d'))
    with col3:
        st.metric(label="Dzień z Największym Opóźnieniem", value=daily_mean_delay.idxmax().strftime('%Y-%m-%d'))

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Calculate mean delay for each vehicle type under normal and challenging conditions
    mean_delay_normal = merged_data[~condition].groupby('vehicle_type')['Delay'].mean().reset_index()
    mean_delay_challenging = filtered_data.groupby('vehicle_type')['Delay'].mean().reset_index()

    # Calculate influence ratio
    influence_ratio = pd.merge(mean_delay_normal, mean_delay_challenging, on='vehicle_type',
                               suffixes=('_normal', '_challenging'))
    influence_ratio['influence_ratio'] = influence_ratio['Delay_challenging'] / influence_ratio['Delay_normal']

    # Display influence ratio using half-circle plots with color coding
    col1, col2, col3 = st.columns(3)


    def get_color(value):
        if value < 0:
            return "lightgreen"
        elif value < 1:
            return "orange"
        else:
            return "red"


    for col, row in zip([col1, col2, col3], influence_ratio.itertuples()):
        with col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row.influence_ratio,
                title={'text': f"{row.vehicle_type} Wskaźnik Wpływu"},
                gauge={
                    'axis': {'range': [-1, 2], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': get_color(row.influence_ratio)},
                    'bgcolor': "white",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [-1, 0], 'color': "lightgray"},
                        {'range': [0, 1], 'color': "lightgray"},
                        {'range': [1, 2], 'color': "lightgray"}
                    ],
                    'bordercolor': "gray",
                }
            ))
            st.plotly_chart(fig)

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Create a bar chart for average delays under normal and challenging conditions
    fig = px.bar(influence_ratio, x='vehicle_type', y=['Delay_normal', 'Delay_challenging'],
                 title=f'Średnie Opóźnienia w Normalnych i Trudnych Warunkach ({weather_factor})',
                 labels={'value': 'Średnie Opóźnienie (minuty)', 'variable': 'Warunek'})
    st.plotly_chart(fig)

with tab2:
    st.header(f'Trendy Czasowe dla {transport_type}')

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with col1:
        st.subheader('Średnie Opóźnienie w Ciągu Dnia (godziny)')
        mean_delay_by_hour = filtered_delays.groupby('hour')['Delay'].mean().reset_index()
        Q1 = mean_delay_by_hour['Delay'].quantile(0.25)
        Q3 = mean_delay_by_hour['Delay'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        mean_delay_by_hour = mean_delay_by_hour[
            (mean_delay_by_hour['Delay'] >= lower_bound) & (mean_delay_by_hour['Delay'] <= upper_bound)]

        # Display metric
        avg_delay_day = mean_delay_by_hour['Delay'].mean()
        st.metric(label="Średnie Opóźnienie w Ciągu Dnia (minuty)", value=f"{avg_delay_day:.2f}")

        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        fig = px.line(mean_delay_by_hour, x='hour', y='Delay',
                      title='Średnie Opóźnienia w Ciągu Dnia',
                      labels={'hour': 'Godzina Dnia', 'Delay': 'Średnie Opóźnienie (minuty)'})
        st.plotly_chart(fig)

    with col2:
        st.subheader('Średnie Opóźnienie w Ciągu Tygodnia')
        filtered_delays['day_of_week'] = filtered_delays['timestamp'].dt.day_name()
        mean_delay_by_day = filtered_delays.groupby('day_of_week')['Delay'].mean().reset_index()
        Q1 = mean_delay_by_day['Delay'].quantile(0.25)
        Q3 = mean_delay_by_day['Delay'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        mean_delay_by_day = mean_delay_by_day[
            (mean_delay_by_day['Delay'] >= lower_bound) & (mean_delay_by_day['Delay'] <= upper_bound)]
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        mean_delay_by_day['day_of_week'] = pd.Categorical(mean_delay_by_day['day_of_week'], categories=days_order,
                                                          ordered=True)
        mean_delay_by_day = mean_delay_by_day.sort_values('day_of_week')

        # Display metric
        avg_delay_week = mean_delay_by_day['Delay'].mean()
        st.metric(label="Średnie Opóźnienie w Ciągu Tygodnia (minuty)", value=f"{avg_delay_week:.2f}")

        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        fig = px.bar(mean_delay_by_day, x='day_of_week', y='Delay',
                     title='Średnie Opóźnienia w Ciągu Tygodnia',
                     labels={'day_of_week': 'Dzień Tygodnia', 'Delay': 'Średnie Opóźnienie (minuty)'})
        st.plotly_chart(fig)

    with col3:
        st.subheader('Średnie Opóźnienie w Ciągu Miesiąca')
        mean_delay_by_day = filtered_delays.groupby('date')['Delay'].mean().reset_index()
        Q1 = mean_delay_by_day['Delay'].quantile(0.25)
        Q3 = mean_delay_by_day['Delay'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        mean_delay_by_day = mean_delay_by_day[
            (mean_delay_by_day['Delay'] >= lower_bound) & (mean_delay_by_day['Delay'] <= upper_bound)]

        # Display metric
        avg_delay_month = mean_delay_by_day['Delay'].mean()
        st.metric(label="Średnie Opóźnienie w Ciągu Miesiąca (minuty)", value=f"{avg_delay_month:.2f}")

        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        fig = px.line(mean_delay_by_day, x='date', y='Delay',
                      title='Trendy Opóźnień w Ciągu Miesiąca',
                      labels={'date': 'Data', 'Delay': 'Średnie Opóźnienie (minuty)'})
        st.plotly_chart(fig)

with tab3:
    st.header('Mapa Opóźnień dla Autobusów i Tramwajów')


    def create_heatmap(vehicle_type):
        vehicle_delays = filtered_delays_with_stops[filtered_delays_with_stops['vehicle_type'] == vehicle_type]
        mean_delay_by_stop = vehicle_delays.groupby(['stop_name', 'stop_lat', 'stop_lon'])['Delay'].mean().reset_index()
        Q1 = mean_delay_by_stop['Delay'].quantile(0.25)
        Q3 = mean_delay_by_stop['Delay'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        mean_delay_by_stop = mean_delay_by_stop[
            (mean_delay_by_stop['Delay'] >= lower_bound) & (mean_delay_by_stop['Delay'] <= upper_bound)]
        warsaw_map = folium.Map(location=[52.2297, 21.0122], zoom_start=12)
        heat_data = [[row['stop_lat'], row['stop_lon'], row['Delay']] for index, row in mean_delay_by_stop.iterrows()]
        HeatMap(heat_data).add_to(warsaw_map)
        return warsaw_map, mean_delay_by_stop


    st.subheader(f'Opóźnienia {transport_type}')
    transport_map, mean_delay_by_stop = create_heatmap(transport_type)

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Display metric
    most_delayed_stop = mean_delay_by_stop.loc[mean_delay_by_stop['Delay'].idxmax()]
    st.metric(label="Najbardziej Opóźniony Przystanek", value=most_delayed_stop['stop_name'])

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st_folium(transport_map, use_container_width=True)
