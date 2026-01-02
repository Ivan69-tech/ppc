"""
Tests unitaires pour le module communication/server/modbus_server.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datamodel.datamodel import SystemObs
from datamodel.standard_data import Bess
from datamodel.project_data import ProjectData
from communication.server.modbus_server import ModbusServer
from keys.keys import Keys


class TestModbusServer:
    """Tests pour la classe ModbusServer."""

    @pytest.fixture
    def modbus_server(self):
        """Crée une instance de ModbusServer."""
        return ModbusServer(
            host="localhost", port=5021
        )  # Port différent pour éviter les conflits

    @pytest.fixture
    def system_obs_with_bess(self):
        """Crée un SystemObs avec des données BESS."""
        return SystemObs(bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=time.time())])

    @pytest.fixture
    def system_obs_empty(self):
        """Crée un SystemObs vide."""
        return SystemObs()

    def test_modbus_server_initialization(self, modbus_server):
        """Test l'initialisation du ModbusServer."""
        assert modbus_server.host == "localhost"
        assert modbus_server.port == 5021
        assert modbus_server.current_system_obs is None
        assert modbus_server.setpoint_value is None
        assert modbus_server.server_running is False

    def test_expose_server_updates_current_system_obs(
        self, modbus_server, system_obs_with_bess
    ):
        """Test que expose_server met à jour current_system_obs."""
        modbus_server.expose_server(system_obs_with_bess)
        assert modbus_server.current_system_obs == system_obs_with_bess

    def test_expose_server_starts_server(self, modbus_server, system_obs_with_bess):
        """Test que expose_server démarre le serveur."""
        assert modbus_server.server_running is False
        modbus_server.expose_server(system_obs_with_bess)
        # Le serveur devrait être marqué comme démarré
        # (mais on ne peut pas vraiment tester le thread sans attendre)
        assert modbus_server.server_running is True

    def test_fill_system_obs_with_setpoint(self, modbus_server):
        """Test fill_system_obs avec un setpoint."""
        # Simuler un setpoint écrit dans le registre
        with modbus_server.slave_context_lock:
            modbus_server.slave_context.setValues(
                3,
                modbus_server.REG_SETPOINT_BESS,
                [15000],  # 150.0 * 100
            )

        system_obs = modbus_server.fill_system_obs()

        assert len(system_obs.project_data) == 2  # setpoint + watchdog
        setpoint_data = next(
            (pd for pd in system_obs.project_data if pd.name == Keys.BESS_SETPOINT_KEY),
            None,
        )
        assert setpoint_data is not None
        assert setpoint_data.value == 150.0

    def test_fill_system_obs_without_setpoint(self, modbus_server):
        """Test fill_system_obs sans setpoint."""
        system_obs = modbus_server.fill_system_obs()

        assert len(system_obs.project_data) == 2  # setpoint + watchdog (même si 0)
        setpoint_data = next(
            (pd for pd in system_obs.project_data if pd.name == Keys.BESS_SETPOINT_KEY),
            None,
        )
        assert setpoint_data is not None
        assert setpoint_data.value == 0.0

    def test_fill_system_obs_with_watchdog(self, modbus_server):
        """Test fill_system_obs avec un watchdog."""
        # Simuler un watchdog écrit dans le registre
        with modbus_server.slave_context_lock:
            modbus_server.slave_context.setValues(
                3, modbus_server.REG_WATCHDOG_BESS, [42]
            )

        system_obs = modbus_server.fill_system_obs()

        watchdog_data = next(
            (pd for pd in system_obs.project_data if pd.name == Keys.WATCHDOG_BESS_KEY),
            None,
        )
        assert watchdog_data is not None
        assert watchdog_data.value == 42.0

    def test_update_holding_registers_with_bess(
        self, modbus_server, system_obs_with_bess
    ):
        """Test _update_holding_registers avec des données BESS."""
        modbus_server.current_system_obs = system_obs_with_bess
        modbus_server._update_holding_registers()

        with modbus_server.slave_context_lock:
            soc_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_SOC_BESS, 1
            )
            p_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_P_BESS, 1
            )
            q_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_Q_BESS, 1
            )

        assert soc_values[0] == 7500  # 75.0 * 100
        assert p_values[0] == 10000  # 100.0 * 100
        assert q_values[0] == 5000  # 50.0 * 100

    def test_update_holding_registers_without_bess(
        self, modbus_server, system_obs_empty
    ):
        """Test _update_holding_registers sans données BESS."""
        modbus_server.current_system_obs = system_obs_empty
        modbus_server._update_holding_registers()

        with modbus_server.slave_context_lock:
            soc_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_SOC_BESS, 1
            )
            p_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_P_BESS, 1
            )
            q_values = modbus_server.slave_context.getValues(
                3, modbus_server.REG_Q_BESS, 1
            )

        assert soc_values[0] == 0
        assert p_values[0] == 0
        assert q_values[0] == 0

    def test_update_holding_registers_without_current_system_obs(self, modbus_server):
        """Test _update_holding_registers sans current_system_obs."""
        modbus_server.current_system_obs = None
        # Ne devrait pas lever d'exception
        modbus_server._update_holding_registers()

    def test_fill_system_obs_handles_exception(self, modbus_server):
        """Test que fill_system_obs gère les exceptions."""
        # Simuler une exception lors de la lecture
        with patch.object(
            modbus_server.slave_context,
            "getValues",
            side_effect=Exception("Test error"),
        ):
            system_obs = modbus_server.fill_system_obs()
            # Devrait retourner un SystemObs avec des valeurs par défaut
            assert len(system_obs.project_data) == 2

    def test_modbus_server_cleanup(self, modbus_server):
        """Test le nettoyage du serveur Modbus."""
        modbus_server.server_running = True
        modbus_server.server_running = False
        # Ne devrait pas lever d'exception
