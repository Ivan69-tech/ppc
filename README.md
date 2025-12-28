# EMS

Système de contrôle et de gestion pour centrales électriques hybrides, intégrant des équipements BESS (Battery Energy
Storage System) et PV (Photovoltaic). Le système collecte les données des équipements, applique des fonctions de
contrôle métier, et génère des commandes pour piloter les équipements.

## Architecture

Le système suit une architecture en couches avec séparation claire des responsabilités :

- **Communication** : Interface avec les équipements physiques via des drivers (Modbus, etc.)
- **Adapter** : Adaptation entre le monde externe (drivers) et le domaine applicatif
- **Application** : Orchestration du flux de données et gestion des threads
- **Core** : Orchestration des fonctions métier
- **Métier** : Fonctions de contrôle (voltage support, etc.)
- **Database** : Persistance des données agrégées

## Schéma des flux de données

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                             │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │ Aggregation Loop │         │  Process Loop    │              │
│  │  (Thread 1)      │         │   (Thread 2)     │              │
│  └────────┬─────────┘         └────────┬─────────┘              │
│           │                            │                        │
│           │                            │                        │
└───────────┼────────────────────────────┼────────────────────────┘
            │                            │
            │                            │
            ▼                            │
┌────────────────────────────────────────┴───────────────────────┐
│                          Adapter                               │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ read_and_        │         │ send_commands()  │             │
│  │ aggregate()      │         │                  │             │
│  └────────┬─────────┘         └────────┬─────────┘             │
│           │                            │                       │
│           │                            │                       │
│           ▼                            │                       │
│  ┌──────────────────┐                  │                       │
│  │  _aggregate()    │                  │                       │
│  └──────────────────┘                  │                       │
└───────────┬────────────────────────────┘                       │
            │                                                    │
            │                                                    │
    ┌───────┴────────┐                              ┌────────────┴──────────┐
    │                │                              │                       │
    ▼                ▼                              ▼                       ▼
┌───────────┐  ┌───────────┐                ┌───────────┐         ┌──────────────┐
│BessDriver │  │ PvDriver  │                │ Database  │         │ Orchestrator │
│           │  │           │                │           │         │              │
│ read()    │  │ read()    │                │ save()    │         │  step()      │
│ write()   │  │ write()   │                │           │         │              │
└─────┬─────┘  └─────┬─────┘                └───────────┘         └──────┬───────┘
      │              │                                                   │
      │              │                                                   │
      └──────┬───────┘                                                   │
             │                                                           │
             │                                                           │
             ▼                                                           │
      ┌──────────────┐                                                   │
      │  SystemObs   │                                                   │
      │  (agrégé)    │                                                   │
      └──────┬───────┘                                                   │
             │                                                           │
             │                                                           │
             └───────────────────────────────┬───────────────────────────┘
                                             │
                                             │
                                             ▼
                                    ┌──────────────┐
                                    │ ControlFunc  │
                                    │ (VoltageSup.)│
                                    │  compute()   │
                                    └──────┬───────┘
                                           │
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   Command    │
                                    │   (List)     │
                                    └──────┬───────┘
                                           │
                                           │ (retour vers Adapter)
                                           │
```

### Description du flux

1. **Collecte des données** (Thread d'agrégation)

   - L'Adapter lit les données de tous les drivers (BessDriver, PvDriver)
   - Chaque driver retourne un `SystemObs` avec ses données spécifiques
   - L'Adapter agrège tous les `SystemObs` en un seul `SystemObs` global
   - Les données agrégées sont stockées dans une queue thread-safe
   - Les données sont sauvegardées dans la base de données SQLite

2. **Traitement métier** (Thread de traitement)

   - L'Application récupère le dernier `SystemObs` agrégé
   - L'Orchestrator exécute toutes les fonctions de contrôle (ControlFunction)
   - Chaque fonction métier génère une liste de `Command`
   - Les commandes sont stockées dans une queue thread-safe

3. **Envoi des commandes** (Thread d'agrégation)
   - L'Adapter récupère les commandes de la queue
   - Chaque commande est routée vers le driver approprié selon son `equipment_type`
   - Les drivers exécutent les commandes (écriture Modbus, etc.)

## Structure du projet

```
ppc/
├── adapter/              # Adaptation entre drivers et domaine
│   └── adapter.py        # Lecture, agrégation, envoi de commandes
├── application/          # Couche d'orchestration
│   └── application.py    # Gestion des threads et coordination
├── communication/        # Interface avec les équipements
│   ├── interface.py      # Interface Driver (ABC)
│   └── driver/
│       ├── bess_driver.py    # Driver pour équipements BESS
│       └── pv_driver.py      # Driver pour équipements PV
├── core/                 # Logique métier de coordination
│   └── orchestrator.py   # Orchestration des fonctions de contrôle
├── database/             # Persistance des données
│   └── database.py       # Interface SQLite pour SystemObs
├── datamodel/            # Modèles de données
│   ├── datamodel.py      # SystemObs, Command, EquipmentType
│   ├── standard_data.py  # Bess, Pv
│   └── project_data.py   # ProjectData
├── keys/                 # Constantes et clés
│   └── keys.py           # Clés pour ProjectData
├── metier/               # Fonctions de contrôle métier
│   ├── interface.py      # Interface ControlFunction
│   └── voltage_support/
│       └── voltage_support.py  # Fonction de contrôle voltage support
├── db/                   # Base de données SQLite (générée automatiquement)
│   └── YYYY_MM_DD.db     # Fichiers de base de données par jour
├── main.py               # Point d'entrée principal
└── README.md             # Documentation
```

## Installation

### Prérequis

- Python 3.10 ou supérieur
- pip

### Installation des dépendances

```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate  # Sur Windows

# Les dépendances sont minimales (SQLite est intégré à Python)
# Aucune installation supplémentaire requise pour le moment
```

## Utilisation

### Lancement du système

```bash
python main.py
```

Le système démarre deux threads :

- Thread d'agrégation : collecte et agrégation des données toutes les secondes (par défaut)
- Thread de traitement : traitement métier et génération de commandes toutes les secondes (par défaut)
