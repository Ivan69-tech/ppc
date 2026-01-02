# Configuration Grafana pour visualisation des bases SQLite

Ce dossier contient la configuration Docker Compose pour lancer Grafana avec accès aux bases de données SQLite présentes
dans le dossier `../db`.

## Prérequis

- Docker
- Docker Compose

## Lancement

```bash
cd grafana
docker-compose up -d
```

Grafana sera accessible à l'adresse : http://localhost:3000

## Configuration de la source de données SQLite

1. Connectez-vous à Grafana (http://localhost:3000)
2. Allez dans **Configuration** → **Data sources**
3. Cliquez sur **Add data source**
4. Sélectionnez **SQLite** (le plugin sera installé automatiquement au démarrage)
5. Configurez le chemin vers votre base de données :
   - Pour une base spécifique : `/db/nom_de_la_base.db`
   - Exemple : `/var/lib/grafana/db/2025_12_28.db`
6. Cliquez sur **Save & Test**

## Structure des bases de données

Les bases SQLite contiennent les tables suivantes :

- **bess** : Données BESS (p, q, soc, timestamp)
- **pv** : Données PV (p, q, timestamp)
- **project_data** : Données de projet (name, value, timestamp)

## Exemples de requêtes SQL

### Données BESS

```sql
SELECT
  strftime('%s', datetime(timestamp, 'unixepoch')) as time,
  p,
  q,
  soc
FROM bess
WHERE timestamp IS NOT NULL
ORDER BY timestamp
```

### Données PV

```sql
SELECT
  strftime('%s', datetime(timestamp, 'unixepoch')) as time,
  p,
  q
FROM pv
WHERE timestamp IS NOT NULL
ORDER BY timestamp
```

### Données de projet

```sql
SELECT
  strftime('%s', datetime(timestamp, 'unixepoch')) as time,
  name,
  value
FROM project_data
WHERE name = 'nom_de_la_variable'
  AND timestamp IS NOT NULL
ORDER BY timestamp
```
