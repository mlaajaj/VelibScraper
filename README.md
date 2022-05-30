
# Velib Scraper 

![Python 3.6](https://img.shields.io/badge/Python-3.6-brightgreen.svg) 

## A propos de cette application

![Velib](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Vélib-Métropole-Logo.png/280px-Vélib-Métropole-Logo.png). 

Velib Scraper est comme son nom l'indique un scraper de données de l'API "Velib". 


## Le constat 

Voulant travailler sur une application permettant de fournir un historique de l'utilisation des vélib par emplacement, j'ai décidé d'utiliser l'API officielle afin d'obtenir ces données. 
Cependant, les données fournies sont en flux continu et ne permettent pas d'obtenir un historique des stations et des flux.   
J'ai décidé, par le biais de Python et de Github Workflow, de récupérer les données et de les répartir en deux fichiers:

| Elements | MàJ | Contenu |
| :---:         |     :---:      |          :---: |
| data.csv   | 30 min     | Flux continu    |
| histo.csv     | 30 min       | Flux continu + historique      |

## TO-DO

- Histo.csv --> en fichier zip.

- Créer une API


## License

[MIT](https://choosealicense.com/licenses/mit/)
