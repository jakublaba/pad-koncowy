import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap
import plotly.graph_objects as go
from streamlit_folium import st_folium

# Load the datasets
delays = pd.read_csv('data/traffic/delays-merged.csv')
weather = pd.read_csv('data/weather/weather-merged.csv')
stops = pd.read_csv('data/gtfs/2025/01/03/stops.csv')

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
    st.title('Public Transport Delays Analysis in Warsaw')
with col2:
    transport_type = st.selectbox("Select Transport Type", ('Autobus', 'Tramwaj', 'Pociąg'))

# Filter data based on selected transport type
filtered_delays = delays[delays['vehicle_type'] == transport_type]
filtered_delays_with_stops = delays_with_stops[delays_with_stops['vehicle_type'] == transport_type]

# Create tabs
tab1, tab2, tab3 = st.tabs(["Weather conditions", "Time Trends", "Heatmap of Delays"])

with tab1:
    st.header(f'Average Delay vs. Weather Conditions for {transport_type}')

    # Merge datasets on date and hour
    merged_data = pd.merge(delays, weather, on=['date', 'hour'])

    # Define weather factors
    weather_factors = {
        'Temperature': 'temperatura',
        'Wind Speed': 'predkosc_wiatru',
        'Rain': 'suma_opadu'
    }

    # Select weather factor
    weather_factor = st.selectbox("Select Weather Factor", list(weather_factors.keys()))
    weather_column = weather_factors[weather_factor]

    # Regular Conditions Section
    st.subheader('Regular Conditions')
    avg_weather = merged_data[weather_column].mean()
    avg_delay = merged_data['Delay'].mean()

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"Average {weather_factor}", value=f"{avg_weather:.2f}")
    with col2:
        st.metric(label="Average Delay (minutes)", value=f"{avg_delay:.2f}")

    fig = px.scatter(merged_data, x=weather_column, y='Delay',
                     labels={weather_column: weather_factor, 'Delay': 'Delay (minutes)'},
                     title=f'Delay vs. {weather_factor}')
    st.plotly_chart(fig)

    # Challenging Conditions Section
    st.subheader('Challenging Conditions')

    # Define challenging weather conditions
    challenging_conditions = {
        'Rain': merged_data['suma_opadu'] > 7.6,
        'Wind Speed': merged_data['predkosc_wiatru'] > 8,
        'Temperature': merged_data['temperatura'] < 0
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
        st.metric(label="Average Temperature (°C)", value=f"{filtered_data['temperatura'].mean():.2f}")
        st.metric(label="Lowest Temperature (°C)", value=f"{filtered_data['temperatura'].min():.2f}")
    with col2:
        st.metric(label="Average Wind Speed (m/s)", value=f"{filtered_data['predkosc_wiatru'].mean():.2f}")
        lowest_temp_date = filtered_data.loc[filtered_data['temperatura'].idxmin(), 'date']
        st.metric(label="Day with Lowest Temperature", value=lowest_temp_date.strftime('%Y-%m-%d'))
    with col3:
        st.metric(label="Day with Biggest Delay", value=daily_mean_delay.idxmax().strftime('%Y-%m-%d'))

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
                title={'text': f"{row.vehicle_type} Influence Ratio"},
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

    # Create a bar chart for average delays under normal and challenging conditions
    fig = px.bar(influence_ratio, x='vehicle_type', y=['Delay_normal', 'Delay_challenging'],
                 title=f'Average Delays Under Normal and Challenging Conditions ({weather_factor})',
                 labels={'value': 'Average Delay (minutes)', 'variable': 'Condition'})
    st.plotly_chart(fig)
with tab2:
    st.header('Time Trends')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader('Average Delay Throughout the Day')
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
        st.metric(label="Average Delay Throughout the Day (minutes)", value=f"{avg_delay_day:.2f}")

        fig = px.line(mean_delay_by_hour, x='hour', y='Delay',
                      title='Average Delays Throughout the Day',
                      labels={'hour': 'Hour of the Day', 'Delay': 'Average Delay (minutes)'})
        st.plotly_chart(fig)

    with col2:
        st.subheader('Average Delay Throughout the Week')
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
        st.metric(label="Average Delay Throughout the Week (minutes)", value=f"{avg_delay_week:.2f}")

        fig = px.bar(mean_delay_by_day, x='day_of_week', y='Delay',
                     title='Average Delays Throughout the Week',
                     labels={'day_of_week': 'Day of the Week', 'Delay': 'Average Delay (minutes)'})
        st.plotly_chart(fig)

    with col3:
        st.subheader('Average Delay Throughout the Month')
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
        st.metric(label="Average Delay Throughout the Month (minutes)", value=f"{avg_delay_month:.2f}")

        fig = px.line(mean_delay_by_day, x='date', y='Delay',
                      title='Delay Trends Throughout the Month',
                      labels={'date': 'Date', 'Delay': 'Average Delay (minutes)'})
        st.plotly_chart(fig)

with tab3:
    st.header('Heatmap of Delays for Buses and Trams')


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


    st.subheader(f'{transport_type} Delays')
    transport_map, mean_delay_by_stop = create_heatmap(transport_type)

    # Display metric
    most_delayed_stop = mean_delay_by_stop.loc[mean_delay_by_stop['Delay'].idxmax()]
    st.metric(label="Most Delayed Stop", value=most_delayed_stop['stop_name'])

    st_folium(transport_map, use_container_width=True)