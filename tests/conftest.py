"""
Configuration partagée pour les tests pytest.
"""

import pytest
import time
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.standard_data import Bess, Pv
from datamodel.project_data import ProjectData
from keys.keys import Keys


@pytest.fixture
def sample_bess():
    """Crée un objet Bess de test."""
    return Bess(p=100.0, q=50.0, soc=75.0, timestamp=time.time())


@pytest.fixture
def sample_pv():
    """Crée un objet Pv de test."""
    return Pv(p=200.0, q=0.0, timestamp=time.time())


@pytest.fixture
def sample_project_data():
    """Crée un ProjectData de test."""
    return ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=time.time())


@pytest.fixture
def sample_system_obs(sample_bess, sample_pv, sample_project_data):
    """Crée un SystemObs de test."""
    return SystemObs(
        bess=[sample_bess],
        pv=[sample_pv],
        project_data=[sample_project_data],
    )


@pytest.fixture
def empty_system_obs():
    """Crée un SystemObs vide."""
    return SystemObs()


@pytest.fixture
def sample_command():
    """Crée une Command de test."""
    return Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
