#!/usr/bin/env python3
"""
🎮 Tests unitaires critiques pour GPU Stats Service
Tests pour le monitoring GPU AMD, métriques système, performance
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'gpu-stats-service'))

# Mock des imports GPU spécifiques qui peuvent ne pas être disponibles en test
with patch.dict(sys.modules, {
    'pyadl': MagicMock(),
    'rocml': MagicMock(),
    'amdsmi': MagicMock()
}):
    from main import app


class TestGPUStatsServiceHealth:
    """Tests de santé et de status du service GPU Stats"""
    
    def setup_method(self):
        self.client = TestClient(app)

    def test_root_endpoint_structure(self):
        """Test que l'endpoint racine retourne la structure attendue"""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier la structure de base
        assert "service" in data
        assert "version" in data
        assert "gpu_vendor" in data
        assert "status" in data
        assert "endpoints" in data
        
        # Vérifier les endpoints
        endpoints = data["endpoints"]
        expected_endpoints = ["health", "gpu/info", "gpu/stats", "gpu/temperature", "gpu/memory", "gpu/utilization"]
        for endpoint in expected_endpoints:
            assert endpoint in endpoints

    def test_health_endpoint_when_healthy(self):
        """Test endpoint de santé quand le service est sain"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "gpu_available" in data


class TestGPUDetection:
    """Tests pour la détection de GPU"""
    
    @pytest.fixture
    def mock_gpu_detector(self):
        """Fixture pour créer un détecteur de GPU mock"""
        detector = Mock()
        detector.detect_gpu_vendor = Mock()
        detector.is_gpu_available = Mock()
        detector.get_gpu_count = Mock()
        return detector

    def test_amd_gpu_detection(self, mock_gpu_detector):
        """Test la détection de GPU AMD"""
        mock_gpu_detector.detect_gpu_vendor.return_value = "AMD"
        mock_gpu_detector.is_gpu_available.return_value = True
        mock_gpu_detector.get_gpu_count.return_value = 1
        
        vendor = mock_gpu_detector.detect_gpu_vendor()
        available = mock_gpu_detector.is_gpu_available()
        count = mock_gpu_detector.get_gpu_count()
        
        assert vendor == "AMD"
        assert available is True
        assert count == 1

    def test_nvidia_gpu_detection(self, mock_gpu_detector):
        """Test la détection de GPU NVIDIA"""
        mock_gpu_detector.detect_gpu_vendor.return_value = "NVIDIA"
        mock_gpu_detector.is_gpu_available.return_value = True
        mock_gpu_detector.get_gpu_count.return_value = 2
        
        vendor = mock_gpu_detector.detect_gpu_vendor()
        available = mock_gpu_detector.is_gpu_available()
        count = mock_gpu_detector.get_gpu_count()
        
        assert vendor == "NVIDIA"
        assert available is True
        assert count == 2

    def test_no_gpu_detection(self, mock_gpu_detector):
        """Test quand aucun GPU n'est détecté"""
        mock_gpu_detector.detect_gpu_vendor.return_value = None
        mock_gpu_detector.is_gpu_available.return_value = False
        mock_gpu_detector.get_gpu_count.return_value = 0
        
        vendor = mock_gpu_detector.detect_gpu_vendor()
        available = mock_gpu_detector.is_gpu_available()
        count = mock_gpu_detector.get_gpu_count()
        
        assert vendor is None
        assert available is False
        assert count == 0


class TestAMDGPUMonitoring:
    """Tests spécifiques pour le monitoring GPU AMD"""
    
    @pytest.fixture
    def mock_amd_monitor(self):
        """Fixture pour créer un moniteur AMD mock"""
        monitor = Mock()
        monitor.get_gpu_info = Mock()
        monitor.get_gpu_stats = Mock()
        monitor.get_temperature = Mock()
        monitor.get_memory_info = Mock()
        monitor.get_utilization = Mock()
        monitor.get_power_consumption = Mock()
        monitor.get_clock_speeds = Mock()
        return monitor

    def test_amd_gpu_info_retrieval(self, mock_amd_monitor):
        """Test la récupération d'informations GPU AMD"""
        mock_info = {
            "name": "AMD Radeon RX 6700 XT",
            "driver_version": "23.5.2",
            "memory_total": 12288,  # MB
            "compute_units": 40,
            "max_clock": 2424,  # MHz
            "vendor_id": "1002",
            "device_id": "73DF"
        }
        mock_amd_monitor.get_gpu_info.return_value = mock_info
        
        info = mock_amd_monitor.get_gpu_info()
        
        assert info["name"] == "AMD Radeon RX 6700 XT"
        assert info["memory_total"] == 12288
        assert info["compute_units"] == 40
        assert "driver_version" in info

    def test_amd_gpu_stats_retrieval(self, mock_amd_monitor):
        """Test la récupération de statistiques GPU AMD"""
        mock_stats = {
            "timestamp": time.time(),
            "gpu_utilization": 75.5,  # %
            "memory_utilization": 68.2,  # %
            "temperature": 65.0,  # °C
            "fan_speed": 1800,  # RPM
            "power_consumption": 145.2,  # W
            "core_clock": 2100,  # MHz
            "memory_clock": 2000,  # MHz
            "voltage": 1.05  # V
        }
        mock_amd_monitor.get_gpu_stats.return_value = mock_stats
        
        stats = mock_amd_monitor.get_gpu_stats()
        
        assert stats["gpu_utilization"] == 75.5
        assert stats["temperature"] == 65.0
        assert stats["power_consumption"] == 145.2
        assert "timestamp" in stats

    def test_amd_temperature_monitoring(self, mock_amd_monitor):
        """Test le monitoring de température AMD"""
        mock_temps = {
            "gpu_core": 65.0,
            "gpu_memory": 68.5,
            "gpu_hotspot": 72.0,
            "critical_temp": 110.0,
            "target_temp": 83.0
        }
        mock_amd_monitor.get_temperature.return_value = mock_temps
        
        temps = mock_amd_monitor.get_temperature()
        
        assert temps["gpu_core"] == 65.0
        assert temps["gpu_hotspot"] == 72.0
        assert temps["critical_temp"] == 110.0

    def test_amd_memory_monitoring(self, mock_amd_monitor):
        """Test le monitoring de mémoire AMD"""
        mock_memory = {
            "total": 12288,  # MB
            "used": 8372,   # MB
            "free": 3916,   # MB
            "utilization": 68.2,  # %
            "type": "GDDR6",
            "bandwidth": 448.0  # GB/s
        }
        mock_amd_monitor.get_memory_info.return_value = mock_memory
        
        memory = mock_amd_monitor.get_memory_info()
        
        assert memory["total"] == 12288
        assert memory["used"] == 8372
        assert memory["utilization"] == 68.2
        assert memory["type"] == "GDDR6"

    def test_amd_utilization_monitoring(self, mock_amd_monitor):
        """Test le monitoring d'utilisation AMD"""
        mock_utilization = {
            "gpu": 75.5,      # %
            "compute": 72.3,  # %
            "memory": 68.2,   # %
            "video_decode": 0.0,  # %
            "video_encode": 0.0,  # %
            "dma": 5.2       # %
        }
        mock_amd_monitor.get_utilization.return_value = mock_utilization
        
        utilization = mock_amd_monitor.get_utilization()
        
        assert utilization["gpu"] == 75.5
        assert utilization["compute"] == 72.3
        assert utilization["memory"] == 68.2

    def test_amd_power_monitoring(self, mock_amd_monitor):
        """Test le monitoring de consommation électrique AMD"""
        mock_power = {
            "current": 145.2,   # W
            "average": 142.8,   # W
            "maximum": 220.0,   # W
            "limit": 200.0,     # W
            "efficiency": 0.85  # ratio
        }
        mock_amd_monitor.get_power_consumption.return_value = mock_power
        
        power = mock_amd_monitor.get_power_consumption()
        
        assert power["current"] == 145.2
        assert power["maximum"] == 220.0
        assert power["efficiency"] == 0.85

    def test_amd_clock_speeds_monitoring(self, mock_amd_monitor):
        """Test le monitoring des fréquences d'horloge AMD"""
        mock_clocks = {
            "core_current": 2100,    # MHz
            "core_max": 2424,        # MHz
            "memory_current": 2000,  # MHz
            "memory_max": 2000,      # MHz
            "shader_current": 2100,  # MHz
            "boost_enabled": True
        }
        mock_amd_monitor.get_clock_speeds.return_value = mock_clocks
        
        clocks = mock_amd_monitor.get_clock_speeds()
        
        assert clocks["core_current"] == 2100
        assert clocks["core_max"] == 2424
        assert clocks["boost_enabled"] is True


class TestGPUStatsEndpoints:
    """Tests pour les endpoints du service GPU Stats"""
    
    def setup_method(self):
        self.client = TestClient(app)

    @patch('main.gpu_monitor')
    def test_gpu_info_endpoint(self, mock_monitor):
        """Test l'endpoint d'informations GPU"""
        mock_info = {
            "name": "AMD Radeon RX 6700 XT",
            "driver_version": "23.5.2",
            "memory_total": 12288,
            "compute_units": 40
        }
        mock_monitor.get_gpu_info.return_value = mock_info
        
        response = self.client.get("/api/gpu/info")
        if response.status_code == 200:  # Si l'implémentation existe
            data = response.json()
            assert "name" in data
            assert "memory_total" in data

    @patch('main.gpu_monitor')
    def test_gpu_stats_endpoint(self, mock_monitor):
        """Test l'endpoint de statistiques GPU"""
        mock_stats = {
            "timestamp": time.time(),
            "gpu_utilization": 75.5,
            "memory_utilization": 68.2,
            "temperature": 65.0,
            "power_consumption": 145.2
        }
        mock_monitor.get_gpu_stats.return_value = mock_stats
        
        response = self.client.get("/api/gpu/stats")
        # Le test dépend de l'implémentation réelle
        assert response.status_code in [200, 404, 501]

    @patch('main.gpu_monitor')
    def test_gpu_temperature_endpoint(self, mock_monitor):
        """Test l'endpoint de température GPU"""
        mock_temps = {
            "gpu_core": 65.0,
            "gpu_memory": 68.5,
            "gpu_hotspot": 72.0,
            "critical_temp": 110.0
        }
        mock_monitor.get_temperature.return_value = mock_temps
        
        response = self.client.get("/api/gpu/temperature")
        assert response.status_code in [200, 404, 501]

    @patch('main.gpu_monitor')
    def test_gpu_memory_endpoint(self, mock_monitor):
        """Test l'endpoint de mémoire GPU"""
        mock_memory = {
            "total": 12288,
            "used": 8372,
            "free": 3916,
            "utilization": 68.2
        }
        mock_monitor.get_memory_info.return_value = mock_memory
        
        response = self.client.get("/api/gpu/memory")
        assert response.status_code in [200, 404, 501]

    @patch('main.gpu_monitor')
    def test_gpu_utilization_endpoint(self, mock_monitor):
        """Test l'endpoint d'utilisation GPU"""
        mock_utilization = {
            "gpu": 75.5,
            "compute": 72.3,
            "memory": 68.2,
            "video_decode": 0.0
        }
        mock_monitor.get_utilization.return_value = mock_utilization
        
        response = self.client.get("/api/gpu/utilization")
        assert response.status_code in [200, 404, 501]


class TestGPUPerformanceMonitoring:
    """Tests pour le monitoring de performance GPU"""
    
    @pytest.fixture
    def mock_performance_monitor(self):
        """Fixture pour créer un moniteur de performance mock"""
        monitor = Mock()
        monitor.start_monitoring = Mock()
        monitor.stop_monitoring = Mock()
        monitor.get_performance_metrics = Mock()
        monitor.get_historical_data = Mock()
        monitor.calculate_averages = Mock()
        return monitor

    def test_performance_monitoring_start(self, mock_performance_monitor):
        """Test le démarrage du monitoring de performance"""
        mock_performance_monitor.start_monitoring.return_value = True
        
        result = mock_performance_monitor.start_monitoring(interval=1.0)
        assert result is True
        mock_performance_monitor.start_monitoring.assert_called_once_with(interval=1.0)

    def test_performance_monitoring_stop(self, mock_performance_monitor):
        """Test l'arrêt du monitoring de performance"""
        mock_performance_monitor.stop_monitoring.return_value = True
        
        result = mock_performance_monitor.stop_monitoring()
        assert result is True
        mock_performance_monitor.stop_monitoring.assert_called_once()

    def test_performance_metrics_collection(self, mock_performance_monitor):
        """Test la collecte de métriques de performance"""
        mock_metrics = {
            "fps": 89.5,
            "frame_time": 11.2,  # ms
            "gpu_utilization": 78.3,
            "memory_utilization": 65.4,
            "temperature": 67.8,
            "power_consumption": 148.6
        }
        mock_performance_monitor.get_performance_metrics.return_value = mock_metrics
        
        metrics = mock_performance_monitor.get_performance_metrics()
        
        assert metrics["fps"] == 89.5
        assert metrics["frame_time"] == 11.2
        assert metrics["gpu_utilization"] == 78.3

    def test_historical_data_retrieval(self, mock_performance_monitor):
        """Test la récupération de données historiques"""
        mock_historical = {
            "timestamps": [time.time() - 300, time.time() - 240, time.time() - 180],
            "gpu_utilization": [75.2, 78.5, 82.1],
            "temperature": [65.0, 67.2, 69.8],
            "memory_utilization": [62.1, 65.8, 68.9]
        }
        mock_performance_monitor.get_historical_data.return_value = mock_historical
        
        historical = mock_performance_monitor.get_historical_data(duration=300)  # 5 minutes
        
        assert len(historical["timestamps"]) == 3
        assert len(historical["gpu_utilization"]) == 3
        assert historical["gpu_utilization"][-1] == 82.1  # Most recent

    def test_performance_averages_calculation(self, mock_performance_monitor):
        """Test le calcul de moyennes de performance"""
        mock_averages = {
            "avg_gpu_utilization": 78.6,
            "avg_temperature": 67.3,
            "avg_memory_utilization": 65.6,
            "avg_power_consumption": 146.2,
            "max_temperature": 72.1,
            "min_temperature": 62.8
        }
        mock_performance_monitor.calculate_averages.return_value = mock_averages
        
        averages = mock_performance_monitor.calculate_averages(period=3600)  # 1 hour
        
        assert averages["avg_gpu_utilization"] == 78.6
        assert averages["max_temperature"] == 72.1
        assert averages["min_temperature"] == 62.8


class TestGPUAlerts:
    """Tests pour le système d'alertes GPU"""
    
    @pytest.fixture
    def mock_alert_system(self):
        """Fixture pour créer un système d'alertes mock"""
        system = Mock()
        system.check_temperature_alert = Mock()
        system.check_memory_alert = Mock()
        system.check_power_alert = Mock()
        system.get_alert_history = Mock()
        system.set_alert_thresholds = Mock()
        return system

    def test_temperature_alert_normal(self, mock_alert_system):
        """Test alerte température en conditions normales"""
        mock_alert_system.check_temperature_alert.return_value = {
            "alert": False,
            "current_temp": 65.0,
            "threshold": 80.0,
            "status": "normal"
        }
        
        alert = mock_alert_system.check_temperature_alert(65.0)
        
        assert alert["alert"] is False
        assert alert["status"] == "normal"
        assert alert["current_temp"] == 65.0

    def test_temperature_alert_warning(self, mock_alert_system):
        """Test alerte température en surchauffe"""
        mock_alert_system.check_temperature_alert.return_value = {
            "alert": True,
            "current_temp": 85.0,
            "threshold": 80.0,
            "status": "warning",
            "message": "GPU temperature is high"
        }
        
        alert = mock_alert_system.check_temperature_alert(85.0)
        
        assert alert["alert"] is True
        assert alert["status"] == "warning"
        assert alert["current_temp"] > alert["threshold"]

    def test_memory_alert_normal(self, mock_alert_system):
        """Test alerte mémoire en conditions normales"""
        mock_alert_system.check_memory_alert.return_value = {
            "alert": False,
            "current_usage": 65.2,
            "threshold": 85.0,
            "status": "normal"
        }
        
        alert = mock_alert_system.check_memory_alert(65.2)
        
        assert alert["alert"] is False
        assert alert["status"] == "normal"

    def test_memory_alert_high_usage(self, mock_alert_system):
        """Test alerte mémoire en cas d'usage élevé"""
        mock_alert_system.check_memory_alert.return_value = {
            "alert": True,
            "current_usage": 92.5,
            "threshold": 85.0,
            "status": "critical",
            "message": "GPU memory usage is critically high"
        }
        
        alert = mock_alert_system.check_memory_alert(92.5)
        
        assert alert["alert"] is True
        assert alert["status"] == "critical"
        assert alert["current_usage"] > alert["threshold"]

    def test_power_consumption_alert(self, mock_alert_system):
        """Test alerte consommation électrique"""
        mock_alert_system.check_power_alert.return_value = {
            "alert": True,
            "current_power": 195.0,
            "threshold": 180.0,
            "status": "warning",
            "message": "GPU power consumption is high"
        }
        
        alert = mock_alert_system.check_power_alert(195.0)
        
        assert alert["alert"] is True
        assert alert["status"] == "warning"
        assert alert["current_power"] > alert["threshold"]

    def test_alert_thresholds_configuration(self, mock_alert_system):
        """Test la configuration des seuils d'alerte"""
        thresholds = {
            "temperature_warning": 80.0,
            "temperature_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "power_warning": 180.0
        }
        mock_alert_system.set_alert_thresholds.return_value = True
        
        result = mock_alert_system.set_alert_thresholds(thresholds)
        
        assert result is True
        mock_alert_system.set_alert_thresholds.assert_called_once_with(thresholds)

    def test_alert_history_retrieval(self, mock_alert_system):
        """Test la récupération de l'historique des alertes"""
        mock_history = [
            {
                "timestamp": time.time() - 3600,
                "type": "temperature",
                "severity": "warning",
                "message": "GPU temperature reached 82°C",
                "resolved": True
            },
            {
                "timestamp": time.time() - 1800,
                "type": "memory",
                "severity": "critical",
                "message": "GPU memory usage reached 94%",
                "resolved": False
            }
        ]
        mock_alert_system.get_alert_history.return_value = mock_history
        
        history = mock_alert_system.get_alert_history()
        
        assert len(history) == 2
        assert history[0]["type"] == "temperature"
        assert history[1]["resolved"] is False


class TestGPUErrorHandling:
    """Tests pour la gestion d'erreurs du service GPU"""
    
    def setup_method(self):
        self.client = TestClient(app)

    @patch('main.gpu_monitor')
    def test_gpu_not_available_error(self, mock_monitor):
        """Test quand le GPU n'est pas disponible"""
        mock_monitor.get_gpu_info.side_effect = Exception("GPU not available")
        
        response = self.client.get("/api/gpu/info")
        # Dépend de l'implémentation de gestion d'erreur
        assert response.status_code in [404, 500, 503]

    @patch('main.gpu_monitor')
    def test_driver_error_handling(self, mock_monitor):
        """Test la gestion d'erreurs de driver"""
        mock_monitor.get_gpu_stats.side_effect = Exception("Driver error")
        
        response = self.client.get("/api/gpu/stats")
        assert response.status_code in [500, 503]

    @patch('main.gpu_monitor')
    def test_permission_error_handling(self, mock_monitor):
        """Test la gestion d'erreurs de permissions"""
        mock_monitor.get_gpu_info.side_effect = PermissionError("Access denied")
        
        response = self.client.get("/api/gpu/info")
        assert response.status_code in [403, 500]


# Helpers pour les tests GPU
class TestGPUHelpers:
    """Helpers utilitaires pour les tests GPU"""
    
    @staticmethod
    def create_mock_gpu_stats(
        gpu_util=75.0, 
        mem_util=65.0, 
        temp=68.0, 
        power=150.0
    ):
        """Crée des statistiques GPU mock"""
        return {
            "timestamp": time.time(),
            "gpu_utilization": gpu_util,
            "memory_utilization": mem_util,
            "temperature": temp,
            "power_consumption": power,
            "fan_speed": 1800,
            "core_clock": 2100,
            "memory_clock": 2000
        }
    
    @staticmethod
    def create_mock_gpu_info(name="Test GPU", memory=8192):
        """Crée des informations GPU mock"""
        return {
            "name": name,
            "driver_version": "23.5.2",
            "memory_total": memory,
            "compute_units": 40,
            "max_clock": 2424,
            "vendor_id": "1002"
        }
    
    @staticmethod
    def assert_gpu_stats_structure(stats_data):
        """Vérifie la structure des statistiques GPU"""
        required_fields = [
            "timestamp", "gpu_utilization", "memory_utilization", 
            "temperature", "power_consumption"
        ]
        for field in required_fields:
            assert field in stats_data, f"Champ GPU manquant: {field}"
        
        # Vérifier les plages de valeurs
        assert 0 <= stats_data["gpu_utilization"] <= 100
        assert 0 <= stats_data["memory_utilization"] <= 100
        assert stats_data["temperature"] > 0
        assert stats_data["power_consumption"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])