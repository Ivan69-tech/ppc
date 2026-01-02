# Configuration Grafana pour visualisation des bases SQLite

Ce dossier contient la configuration Docker Compose pour lancer Grafana avec accès aux bases de données SQLite présentes
dans le dossier `../db`.

## Prérequis

- Docker
- Docker Compose

## Lancement

**Première fois ou après un problème de permissions :**

1. Exécutez le script d'initialisation pour fixer les permissions :

```bash
cd grafana
./init.sh
```

Si le script demande un mot de passe sudo, entrez-le. Cela est nécessaire pour que Grafana puisse écrire dans le dossier
`data/`.

2. Puis démarrez Grafana :

```bash
docker-compose up -d
```

**Lancements suivants :** Vous pouvez directement lancer :

```bash
cd grafana
docker-compose up -d
```

**En cas de problème de permissions :**

Si vous voyez des erreurs comme "Permission denied" ou "is not writable", exécutez :

```bash
cd grafana
sudo chown -R 1000:1000 data/
sudo chmod -R 775 data/
```

Grafana sera accessible à l'adresse : http://localhost:3000

**Identifiants par défaut :**

- Utilisateur : `admin`
- Mot de passe : `admin`

## Configuration de la source de données SQLite

1. Connectez-vous à Grafana (http://localhost:3000)
2. Allez dans **Configuration** → **Data sources**
3. Cliquez sur **Add data source**
4. Sélectionnez **SQLite** (le plugin sera installé automatiquement au démarrage)
5. Configurez le chemin vers votre base de données :
   - Pour une base spécifique : `/var/lib/grafana/db/nom_de_la_base.db`
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

### Requête pour toutes les données de projet

Si vous voulez voir toutes les variables de projet dans un même graphique :

```sql
SELECT
  strftime('%s', datetime(timestamp, 'unixepoch')) as time,
  name,
  value
FROM project_data
WHERE timestamp IS NOT NULL
ORDER BY timestamp, name
```

Puis dans Grafana, utilisez le format **Table** ou configurez les séries par `name`.

## Structure des fichiers

Les données Grafana sont stockées dans le dossier `data/` :

- `data/dashboards/` : Dashboards JSON (versionnés dans Git)
  - Placez vos fichiers JSON de dashboards ici
  - Ils seront automatiquement chargés par Grafana au démarrage
  - Les modifications dans l'interface Grafana peuvent être exportées ici
- `data/datasources/` : Configurations des sources de données (versionnés dans Git)
- `data/grafana.db` : Base de données SQLite de Grafana (non versionnée)
- `data/logs/` : Logs Grafana (non versionnés)
- `data/plugins/` : Plugins installés (non versionnés)

**Export de dashboards :**

Pour exporter un dashboard depuis l'interface Grafana :

1. Allez dans le dashboard
2. Cliquez sur l'icône d'engrenage (Settings)
3. Cliquez sur **JSON Model**
4. Copiez le contenu JSON
5. Sauvegardez-le dans `data/dashboards/nom-du-dashboard.json`

Les dashboards dans `data/dashboards/` seront automatiquement chargés au démarrage de Grafana grâce à la configuration
de provisioning.

## Arrêt

Pour arrêter Grafana :

```bash
docker-compose down
```

⚠️ **Note** : Les dashboards et configurations sont maintenant stockés dans `grafana/data/` et seront conservés même
après l'arrêt du conteneur. Ils sont également versionnés dans Git.
