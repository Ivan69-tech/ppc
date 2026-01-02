"""
Tests unitaires pour le module metier/utils/watchog.
"""

import pytest
import time
from metier.utils.watchog import Watchdog, WatchdogState, WatchdogStatus


class TestWatchdog:
    """Tests pour la classe Watchdog."""

    @pytest.fixture
    def watchdog(self):
        """Crée un Watchdog avec timeout de 1 seconde pour les tests."""
        return Watchdog(timeout_seconds=1.0, min_heartbeat_interval=0.1)

    def test_watchdog_initialization(self, watchdog):
        """Test l'initialisation du Watchdog."""
        assert watchdog.timeout_seconds == 1.0
        assert watchdog.min_heartbeat_interval == 0.1
        assert watchdog.get_state() == WatchdogState.UNKNOWN

    def test_update_first_value(self, watchdog):
        """Test update avec la première valeur."""
        watchdog.update(1.0, time.time())
        # Après la première valeur, l'état devrait être DISCONNECTED
        assert watchdog.get_state() == WatchdogState.DISCONNECTED

    def test_update_value_change_heartbeat(self, watchdog):
        """Test update avec changement de valeur (heartbeat valide)."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        # Attendre un peu pour que le timestamp soit différent
        time.sleep(0.01)
        watchdog.update(2.0, time.time())

        # Après un changement de valeur, l'état devrait être ONLINE
        assert watchdog.get_state() == WatchdogState.ONLINE

    def test_update_same_value_no_heartbeat(self, watchdog):
        """Test update avec la même valeur (pas de heartbeat)."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(1.0, time.time())  # Même valeur

        # Pas de heartbeat, l'état devrait rester DISCONNECTED
        assert watchdog.get_state() == WatchdogState.DISCONNECTED

    def test_timeout_detection(self, watchdog):
        """Test la détection de timeout."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(2.0, time.time())  # Heartbeat valide

        assert watchdog.get_state() == WatchdogState.ONLINE

        # Attendre plus que le timeout
        time.sleep(1.1)

        # L'état devrait passer à DISCONNECTED
        assert watchdog.get_state() == WatchdogState.DISCONNECTED

    def test_get_status(self, watchdog):
        """Test get_status."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(2.0, time.time())

        status = watchdog.get_status()

        assert isinstance(status, WatchdogStatus)
        assert status.state == WatchdogState.ONLINE
        assert status.last_value == 2.0
        assert status.timeout_seconds == 1.0

    def test_is_online(self, watchdog):
        """Test is_online."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(2.0, time.time())

        assert watchdog.is_online() is True
        assert watchdog.is_disconnected() is False

    def test_is_disconnected(self, watchdog):
        """Test is_disconnected."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)

        assert watchdog.is_disconnected() is True
        assert watchdog.is_online() is False

    def test_timeout_without_heartbeat(self, watchdog):
        """Test timeout quand il n'y a jamais eu de heartbeat valide."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)

        # Attendre plus que le timeout
        time.sleep(1.1)

        assert watchdog.get_state() == WatchdogState.DISCONNECTED

    def test_multiple_updates_same_value(self, watchdog):
        """Test plusieurs updates avec la même valeur."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(1.0, time.time())
        time.sleep(0.01)
        watchdog.update(1.0, time.time())

        # Jamais de heartbeat valide, devrait rester DISCONNECTED
        assert watchdog.get_state() == WatchdogState.DISCONNECTED

    def test_multiple_updates_changing_values(self, watchdog):
        """Test plusieurs updates avec des valeurs changeantes."""
        timestamp = time.time()
        watchdog.update(1.0, timestamp)
        time.sleep(0.01)
        watchdog.update(2.0, time.time())
        time.sleep(0.01)
        watchdog.update(3.0, time.time())

        # Devrait être ONLINE car il y a eu des heartbeats valides
        assert watchdog.get_state() == WatchdogState.ONLINE

    def test_update_without_timestamp(self, watchdog):
        """Test update sans timestamp (utilise time.time() automatiquement)."""
        watchdog.update(1.0)
        time.sleep(0.01)
        watchdog.update(2.0)

        assert watchdog.get_state() == WatchdogState.ONLINE
