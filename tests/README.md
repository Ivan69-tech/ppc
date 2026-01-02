# Tests unitaires

Ce répertoire contient tous les tests unitaires pour le système EMS.

## Installation des dépendances de test

```bash
pip install -r requirements.txt
```

## Exécution des tests

Pour exécuter tous les tests :

```bash
pytest tests/
```

Pour exécuter un fichier de test spécifique :

```bash
pytest tests/test_datamodel.py
```

Pour exécuter un test spécifique :

```bash
pytest tests/test_datamodel.py::TestSystemObs::test_system_obs_creation_empty
```

Pour obtenir un rapport de couverture :

```bash
pytest --cov=. --cov-report=html tests/
```

## Structure des tests

Les tests sont organisés par module :

- `test_datamodel.py` : Tests pour les modèles de données (SystemObs, Command, EquipmentType)
- `test_adapter.py` : Tests pour l'Adapter
- `test_orchestrator.py` : Tests pour l'Orchestrator
- `test_watchdog.py` : Tests pour le Watchdog
- `test_state_machine.py` : Tests pour la StateMachine
- `test_law.py` : Tests pour les lois de contrôle
- `test_policy.py` : Tests pour la Policy
- `test_voltage_support.py` : Tests pour VoltageSupport
- `test_database.py` : Tests pour la Database
- `test_drivers.py` : Tests pour les drivers (BessDriver, PvDriver)
- `test_modbus_server.py` : Tests pour le ModbusServer
- `test_application.py` : Tests pour l'Application

## Fixtures partagées

Le fichier `conftest.py` contient des fixtures pytest partagées utilisées par tous les tests.
