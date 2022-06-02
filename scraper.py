import pandas as pd 
import requests
from bs4 import BeautifulSoup 
from anti_useragent import UserAgent
import random


data_url = "https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/download/?format=csv&timezone=Europe/Berlin&lang=fr&use_labels_for_header=true&csv_separator=%3B"
stations_url = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json'

#------------------------------ FONCTIONS ----------------------------------------------

def get_data(url):
    
    df = pd.read_csv(url, sep=';')
    df = df.drop(columns=df.columns[-1]) 
    df['Actualisation de la donnée'] = pd.to_datetime(df['Actualisation de la donnée'],utc=True)
    df['Actualisation de la donnée'] = df['Actualisation de la donnée'].dt.tz_convert(tz='CET')
    df['Actualisation de la donnée'] = df['Actualisation de la donnée'].dt.tz_localize(None)
    max_date = df['Actualisation de la donnée'].dt.date.max()
    df = df[df['Actualisation de la donnée'].dt.date==max_date].sort_values('Actualisation de la donnée',ascending=False)
      
    return df

def get_proxies():
    proxies = []
    response = requests.get('https://vpnhack.com/premium-proxy-list')
    soup = BeautifulSoup(response.text, 'html.parser')
    for element in soup.find('tbody').find_all('tr'):
        ip = element.find('td').text
        port = element.findAll('td')[1].text
        port = port.replace(', 3128','')
        proxies.append(ip+':'+port)

    return proxies


def get_meteo(villes):
    
    ua = UserAgent().random
    proxies = get_proxies()
    prox = random.choice(proxies)
    meteo_data = []
    
    for ville in villes:
        url = f'https://www.lameteoagricole.net/index_meteo-heure-par-heure.php?communehome={ville}'
        response = requests.get(url, headers = {'headers':ua}, proxies = {'http':prox}, timeout =5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.findAll('div', {'class':'fond2'})[1]
        d = text.getText(strip=True,separator='\n').splitlines()[1:]
        ville_data = [n.strip() for n in d[1::2]]
        ville_data.append(ville)
        meteo_data.append(ville_data)
        
    cols = [n.strip() for n in d[0::2]]
    cols = [n.strip() for n in d[0::2]]
    cols.append('ville')
    
    return pd.DataFrame(meteo_data, columns=cols)

#------------------------------ PROCESS ----------------------------------------------
# Process
data = get_data(data_url)

#-------------------------------- METEO ----------------------------------------------

villes = list(data['Nom communes équipées'].unique())
meteo_df = get_meteo(villes)
final_meteo_df = pd.merge(left=data, right=meteo_df, how='inner', left_on='Nom communes équipées', right_on='ville')
final_meteo_df.to_csv('data.csv', index=False)

#------------------------------ HISTORISATION ----------------------------------------------
try:
    histo_df = pd.read_csv('histo.csv') 
    historisation = (pd.concat([final_meteo_df, histo_df], ignore_index=True, sort =False)
            .drop_duplicates(['Identifiant station','Actualisation de la donnée'], keep='last'))
    historisation.to_csv('histo.csv', index=False)
except:
    final_meteo_df.to_csv('histo.csv',index=False)
