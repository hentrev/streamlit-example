import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
from time import sleep


station_information = 'https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/station_information.json'
station_status = 'https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/station_status.json'

json_information = requests.get(station_information).json()
json_status = requests.get(station_status).json()

df_info = pd.DataFrame(json_information['data']['stations'])
df_status = pd.DataFrame(json_status['data']['stations'])

df_info['station_id'] = df_info['station_id'].astype(int)
df_status['station_id'] = df_status['station_id'].astype(int)

df_merged = df_info.merge(df_status, left_on='station_id', right_on='station_id')
df_merged['num_bikes_available'] = df_merged['num_bikes_available']
df_merged['ratio'] = (df_merged['num_bikes_available'] / df_merged['num_docks_available'])
df_merged['ratio'].replace(np.inf, 0, inplace=True)

def get_color(pct):
    pct_diff = 1.0 - pct
    red_color = min(255, pct_diff*2 * 255)
    green_color = min(255, pct*2 * 255)
    col = (red_color, green_color, 0)
    return col

df_merged['color'] = df_merged.apply(lambda row: get_color(row['ratio']), axis=1)

empty_stations = df_merged[df_merged['num_bikes_available'] == 0]
full_stations = df_merged[df_merged['num_bikes_available'] == df_merged['num_docks_available']]

st.markdown('## Nextbike Mainz - Stationsstatus')

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

st.markdown('Daten aus öffentlicher [GBFS](https://github.com/MobilityData/gbfs) API: https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_mz/de/')

