import pandas as pd 
import json
from flatten_json import flatten
import requests
import reverse_geocoder as rg


data_url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json"
stations_url = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json'

#------------------------------ FONCTIONS ----------------------------------------------

def get_data(url):
    response = requests.get(url)
    if response.status_code != 204:
        data = response.json()['data']['stations']
        
    df = pd.DataFrame([flatten(d) for d in data])    
    df['last_reported'] = pd.to_datetime(df['last_reported'],unit='s', utc=True)
    df['last_reported'] = df['last_reported'].dt.tz_convert(tz='CET')
    df['last_reported'] = df['last_reported'].dt.tz_localize(None)
    max_date = df['last_reported'].dt.date.max()
    df = df[df['last_reported'].dt.date==max_date].sort_values('last_reported',ascending=False)
      
    return df

def get_stations(url):
    r = requests.get(url)
    d = r.json()
    data = d['data']['stations']
    df = pd.DataFrame([flatten(d) for d in data])    
    
    return df

def get_final_df(data,stations):
# Données temporaires qui vont s'actualiser ..
    final_df = pd.merge(data,stations, on='station_id')

    # Selecting & Renaming columns 
    cols = ['station_id','name','is_installed','capacity','numDocksAvailable','numBikesAvailable',
    'num_bikes_available_types_0_mechanical','num_bikes_available_types_1_ebike',
    'is_renting','is_returning','last_reported','lat','lon']

    final_df = final_df[cols]
    final_df.columns =  ['Identifiant station', 'Nom station', 'Station en fonctionnement',
       'Capacité de la station', 'Nombre bornettes libres',
       'Nombre total vélos disponibles', 'Vélos mécaniques disponibles',
       'Vélos électriques disponibles', 'Borne de paiement disponible',
       'Retour vélib possible', 'Actualisation de la donnée',
       'Lattitude', 'Longitude']

    villes = []
    region = []
    results = rg.search(list(zip(final_df['Lattitude'], final_df['Longitude'])))
    for element in results:
        villes.append(element['name'])
        region.append(element['admin1'])
    final_df['Ville'] = villes
    final_df['Region'] = region
    
    final_df['Tx_Disp_Velos'] = round(100*final_df['Nombre total vélos disponibles']/final_df['Capacité de la station'],2)
    final_df['Tx_Disp_Bornette'] = 100-final_df['Tx_Disp_Velos']

    return final_df


#------------------------------ PROCESS ----------------------------------------------
# Process
data = get_data(data_url)
stations = get_stations(stations_url)
final_df = get_final_df(data, stations)
final_df.to_csv('data.csv')
histo_df = pd.read_csv('histo.csv') 

#------------------------------ HISTORISATION ----------------------------------------------
# Historisation 
historisation = (pd.concat([final_df, histo_df], ignore_index=True, sort =False)
        .drop_duplicates(['Identifiant station','Actualisation de la donnée'], keep='last'))

historisation.to_csv('histo.csv', index=False)
