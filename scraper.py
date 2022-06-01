import pandas as pd 
import json
from flatten_json import flatten
import requests
import reverse_geocoder as rg
import requests 
from bs4 import BeautifulSoup 
from fake_useragent import FakeUserAgent
import random



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

def get_proxies():
    proxies = []
    response = requests.get('https://vpnhack.com/premium-proxy-list')
    soup = BeautifulSoup(response.text, 'lxml')
    for element in soup.find('tbody').find_all('tr'):
        ip = element.find('td').text
        port = element.findAll('td')[1].text
        port = port.replace(', 3128','')
        proxies.append(ip+':'+port)

    return random.choice(proxies)

#------------------------------ PROCESS ----------------------------------------------
# Process
data = get_data(data_url)
stations = get_stations(stations_url)
final_df = get_final_df(data, stations)

#-------------------------------- METEO ----------------------------------------------

ua = FakeUserAgent().random
prox = get_proxies()
villes = list(final_df['Ville'].unique())
meteo_data = []

for ville in villes:
    url = f'https://www.lameteoagricole.net/index_meteo-heure-par-heure.php?communehome={ville}'
    response = requests.get(url, headers = {'headers':ua}, proxies = {'http':prox}, timeout =5)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.findAll('div', {'class':'fond2'})[1]
    d = text.getText(strip=True,separator='\n').splitlines()
    d = d[1:]
    ville_data = [n.strip() for n in d[1::2]]
    ville_data.append(ville)
    meteo_data.append(ville_data)

cols = [n.strip() for n in d[0::2]]
cols.append('ville')
meteo_df = pd.DataFrame(meteo_data, columns=cols)

final_meteo_df = pd.merge(left=final_df, right=meteo_df, how='inner', left_on='Ville', right_on='ville')

final_meteo_df.to_csv('data.csv', index=False, compression="zip")

#------------------------------ HISTORISATION ----------------------------------------------
try:
    histo_df = pd.read_csv('histo.csv', compression="zip") 
    historisation = (pd.concat([final_meteo_df, histo_df], ignore_index=True, sort =False)
            .drop_duplicates(['Identifiant station','Actualisation de la donnée'], keep='last'))
    historisation.to_csv('histo.csv', index=False, compression="zip")
except:
    final_meteo_df.to_csv('histo.csv',index=False, compression="zip")
