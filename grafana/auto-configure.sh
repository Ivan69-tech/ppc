#!/bin/bash
# Script pour configurer automatiquement Grafana avec la dernière base de données

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="${SCRIPT_DIR}/../db"
PROVISIONING_DIR="${SCRIPT_DIR}/provisioning"
DATASOURCES_DIR="${PROVISIONING_DIR}/datasources"
DASHBOARDS_DIR="${SCRIPT_DIR}/data/dashboards"

echo "🔍 Recherche de la dernière base de données..."

# Trouver la dernière base de données (par date de modification, en excluant test.db)
LATEST_DB=$(find "${DB_DIR}" -name "*.db" -not -name "test.db" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "${LATEST_DB}" ]; then
    echo "❌ Aucune base de données trouvée dans ${DB_DIR}"
    exit 1
fi

DB_FILENAME=$(basename "${LATEST_DB}")
DB_PATH_IN_CONTAINER="/var/lib/grafana/db/${DB_FILENAME}"

echo "✅ Base de données trouvée : ${DB_FILENAME}"
echo "   Chemin dans le conteneur : ${DB_PATH_IN_CONTAINER}"

# Créer le dossier de provisioning s'il n'existe pas
mkdir -p "${DATASOURCES_DIR}"

# Générer le fichier de datasource
cat > "${DATASOURCES_DIR}/datasources.yml" <<EOF
apiVersion: 1

datasources:
  - name: SQLite - ${DB_FILENAME}
    type: frser-sqlite-datasource
    access: proxy
    url: /var/lib/grafana/db
    database: ${DB_FILENAME}
    isDefault: true
    editable: true
    jsonData:
      path: ${DB_PATH_IN_CONTAINER}
EOF

echo "✅ Datasource configurée : SQLite - ${DB_FILENAME}"

# Créer un dashboard par défaut si il n'existe pas
mkdir -p "${DASHBOARDS_DIR}"
DEFAULT_DASHBOARD="${DASHBOARDS_DIR}/default-dashboard.json"

if [ ! -f "${DEFAULT_DASHBOARD}" ]; then
    echo "📊 Création du dashboard par défaut..."
    
    # Générer un dashboard JSON de base
    python3 <<PYTHON_SCRIPT
import json
from datetime import datetime

dashboard = {
    "dashboard": {
        "title": "Dashboard PPC - Données système",
        "tags": ["ppc", "system"],
        "timezone": "browser",
        "schemaVersion": 27,
        "version": 1,
        "refresh": "5s",
        "panels": [
            {
                "id": 1,
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "type": "timeseries",
                "title": "BESS - Puissance Active (P)",
                "targets": [
                    {
                        "datasource": {"type": "frser-sqlite-datasource", "uid": "SQLite - ${DB_FILENAME}"},
                        "rawSql": "SELECT\n  strftime('%s', datetime(timestamp, 'unixepoch')) as time,\n  p as value\nFROM bess\nWHERE timestamp IS NOT NULL\nORDER BY timestamp",
                        "format": "time_series",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "W",
                        "decimals": 2
                    }
                }
            },
            {
                "id": 2,
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "type": "timeseries",
                "title": "BESS - Puissance Réactive (Q)",
                "targets": [
                    {
                        "datasource": {"type": "frser-sqlite-datasource", "uid": "SQLite - ${DB_FILENAME}"},
                        "rawSql": "SELECT\n  strftime('%s', datetime(timestamp, 'unixepoch')) as time,\n  q as value\nFROM bess\nWHERE timestamp IS NOT NULL\nORDER BY timestamp",
                        "format": "time_series",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "var",
                        "decimals": 2
                    }
                }
            },
            {
                "id": 3,
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "type": "timeseries",
                "title": "BESS - State of Charge (SOC)",
                "targets": [
                    {
                        "datasource": {"type": "frser-sqlite-datasource", "uid": "SQLite - ${DB_FILENAME}"},
                        "rawSql": "SELECT\n  strftime('%s', datetime(timestamp, 'unixepoch')) as time,\n  soc as value\nFROM bess\nWHERE timestamp IS NOT NULL\nORDER BY timestamp",
                        "format": "time_series",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100,
                        "decimals": 2
                    }
                }
            },
            {
                "id": 4,
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "type": "timeseries",
                "title": "PV - Puissance Active (P)",
                "targets": [
                    {
                        "datasource": {"type": "frser-sqlite-datasource", "uid": "SQLite - ${DB_FILENAME}"},
                        "rawSql": "SELECT\n  strftime('%s', datetime(timestamp, 'unixepoch')) as time,\n  p as value\nFROM pv\nWHERE timestamp IS NOT NULL\nORDER BY timestamp",
                        "format": "time_series",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "W",
                        "decimals": 2
                    }
                }
            }
        ]
    },
    "overwrite": False
}

with open("${DEFAULT_DASHBOARD}", "w") as f:
    json.dump(dashboard, f, indent=2)

print("✅ Dashboard par défaut créé")
PYTHON_SCRIPT

    echo "✅ Dashboard par défaut créé : ${DEFAULT_DASHBOARD}"
else
    echo "ℹ️  Dashboard par défaut existe déjà"
fi

echo ""
echo "✨ Configuration terminée !"
echo "   Datasource : SQLite - ${DB_FILENAME}"
echo "   Dashboard : default-dashboard.json"
echo ""
echo "💡 Pour mettre à jour la configuration, relancez ce script ou redémarrez Grafana"

