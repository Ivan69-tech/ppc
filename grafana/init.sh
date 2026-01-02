#!/bin/bash
# Script d'initialisation pour fixer les permissions du dossier data/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"

echo "Initialisation des permissions pour Grafana..."

# Créer le dossier data s'il n'existe pas
mkdir -p "${DATA_DIR}"/{dashboards,datasources,logs,plugins}

# Supprimer les fichiers créés par Grafana avec de mauvaises permissions
echo "Nettoyage des fichiers existants..."
rm -f "${DATA_DIR}"/grafana.db* 2>/dev/null || true
rm -rf "${DATA_DIR}"/{png,pdf,csv,db} 2>/dev/null || true

# Fixer les permissions (lecture/écriture pour le propriétaire et le groupe)
# Grafana dans le conteneur utilisera l'UID/GID 1000:1000
echo "Configuration des permissions..."
chmod -R 775 "${DATA_DIR}" 2>/dev/null || true

# Essayer de changer le propriétaire (peut nécessiter sudo)
if command -v sudo >/dev/null 2>&1; then
    echo "Tentative de changement de propriétaire (peut nécessiter votre mot de passe sudo)..."
    sudo chown -R 1000:1000 "${DATA_DIR}" 2>/dev/null || {
        echo "⚠️  Impossible de changer le propriétaire automatiquement."
        echo "   Vous pouvez exécuter manuellement : sudo chown -R 1000:1000 ${DATA_DIR}"
    }
else
    echo "⚠️  sudo n'est pas disponible. Si vous avez des problèmes de permissions,"
    echo "   exécutez : sudo chown -R 1000:1000 ${DATA_DIR}"
fi

echo "✅ Permissions initialisées pour ${DATA_DIR}"

