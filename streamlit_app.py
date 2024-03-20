import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
from time import sleep
from itertools import chain


def get_color(pct):
    pct_diff = (100 - pct) / 100
    red_color = min(255, pct_diff * 255)
    green_color = min(255, pct_diff * 255)
    col = (red_color, green_color, 0, 1)
    return col

station_information = 'https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/station_information.json'
station_status = 'https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/station_status.json'
free_bike_status = 'https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/free_bike_status.json'

json_information = requests.get(station_information).json()
json_status = requests.get(station_status).json()
json_free_bike_status = requests.get(free_bike_status).json()

df_bikes = pd.DataFrame(json_free_bike_status['data']['bikes'])
num_bikes_available = len(df_bikes[df_bikes['is_disabled'] == False].index)
num_bikes_unavailable = len(df_bikes[df_bikes['is_disabled'] == True].index)
bikes_without_station = df_bikes[df_bikes['station_id'].isna()]
num_bikes_without_station = len(bikes_without_station.index)

df_cargo_charging = df_bikes[df_bikes['vehicle_type_id'] == '225']
df_cargo_charging['fuel_color'] = df_cargo_charging.apply(lambda row: get_color(row['current_fuel_percent']), axis=1)
df_cargo_charging = df_cargo_charging.sort_values(by=['current_fuel_percent'])
df_cargo_charging = df_cargo_charging[['bike_id', 'current_fuel_percent', 'fuel_color', 'lat', 'lon', 'station_id', 'vehicle_type_id']]

df_info = pd.DataFrame(json_information['data']['stations'])
df_status = pd.DataFrame(json_status['data']['stations'])

df_info['station_id'] = df_info['station_id'].astype(int)
df_status['station_id'] = df_status['station_id'].astype(int)

df_merged = df_info.merge(df_status, left_on='station_id', right_on='station_id')
df_merged['num_bikes_available'] = df_merged['num_bikes_available']
df_merged['ratio'] = (df_merged['num_bikes_available'] / df_merged['num_docks_available'])
df_merged['ratio'] = df_merged['ratio'].replace(np.inf, 0)



df_merged['color'] = df_merged.apply(lambda row: get_color(row['ratio']), axis=1)

empty_stations = df_merged[df_merged['num_bikes_available'] == 0]
full_stations = df_merged[df_merged['num_docks_available'] == 0]

st.markdown('## Nextbike Mainz - Status')

st.markdown('### Räder')

col1, col2, col3 = st.columns(3)
col1.metric('Anzahl aktive Räder', num_bikes_available)
col2.metric('Anzahl deaktivierte Räder', num_bikes_unavailable)
col3.metric('Anzahl Räder abseits einer Station', num_bikes_without_station)

st.markdown('#### Räder abseits einer Station')
st.map(bikes_without_station, latitude='lat', longitude='lon')

st.markdown('### Stationen')

col1, col2, col3 = st.columns(3)
percentage_empty_stations = str(int(((len(empty_stations) / len(df_merged))*100))) + "%"
col1.metric('Leere Stationen', len(empty_stations))
col2.metric('Anteil leere Stationen', percentage_empty_stations)
col3.metric('Volle Stationen', len(full_stations))

ids_empty = empty_stations['name'].tolist()
ids_full = full_stations['name'].tolist()

st.markdown('### Leere Stationen')
st.map(empty_stations, latitude='lat', longitude='lon')
st.dataframe(empty_stations[['name', 'num_bikes_available', 'num_docks_available']])

st.markdown('### Volle Stationen')
st.map(full_stations, latitude='lat', longitude='lon')
st.dataframe(full_stations[['name', 'num_bikes_available', 'num_docks_available']])


st.markdown('### Ladezustand Lastenräder')
st.map(df_cargo_charging, latitude='lat', longitude='lon', color='fuel_color')
st.dataframe(df_cargo_charging)

st.markdown('Daten aus öffentlicher [GBFS](https://github.com/MobilityData/gbfs) API: https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/')

