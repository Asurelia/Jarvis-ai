#!/usr/bin/env python3
"""
🧪 Configuration globale pytest pour JARVIS AI
Fixtures communes et configuration de test
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import pytest
import structlog
from faker import Faker

# Ajouter les paths du projet pour les imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services" / "brain-api"))
sys.path.insert(0, str(project_root / "services" / "tts-service"))
sys.path.insert(0, str(project_root / "services" / "gpu-stats-service"))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "tools"))

# Configuration des variables d'environnement de test
os.environ.update({
    "TESTING": "1",
    "JARVIS_ENV": "test",
    "LOG_LEVEL": "DEBUG",
    "DISABLE_OLLAMA": "1",
    "DISABLE_EXTERNAL_APIS": "1",
    "REDIS_URL": "redis://localhost:6379/1",
    "DATABASE_URL": "sqlite:///test.db",
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "JWT_SECRET": "test-jwt-secret",
    "MOCK_GPU_STATS": "1",
    "AMD_GPU_TEST_MODE": "1",
    "TTS_MODEL": "mock-model",
    "TTS_DEVICE": "cpu",
    "ANTI_HALLUCINATION": "true",
    "SAMPLE_RATE": "22050",
    "CHANNELS": "1",
    "CHUNK_SIZE": "1024"
})

# Configuration logging pour les tests
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.testing.LogCapture(),
    ],
    wrapper_class=structlog.testing.BoundLogger,
    logger_factory=structlog.testing.TestingLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Instance Faker pour génération de données
fake = Faker('fr_FR')  # Français pour JARVIS

# ==========================================
# FIXTURES DE BASE
# ==========================================

@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Répertoire temporaire pour les tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_logger():
    """Logger mock pour les tests"""
    return Mock(spec=structlog.BoundLogger)

@pytest.fixture
def test_config():
    """Configuration de test commune"""
    return {
        "testing": True,
        "debug": True,
        "secret_key": "test-secret",
        "database_url": "sqlite:///test.db",
        "redis_url": "redis://localhost:6379/1",
        "log_level": "DEBUG",
        "jwt_secret": "test-jwt-secret",
        "cors_origins": ["http://localhost:3000"],
        "websocket_ping_interval": 10,
        "websocket_ping_timeout": 5
    }

# ==========================================
# FIXTURES POUR DONNÉES DE TEST
# ==========================================

@pytest.fixture
def mock_user():
    """Utilisateur de test"""
    return {
        "id": fake.uuid4(),
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_active": True,
        "is_admin": False,
        "created_at": fake.date_time(),
        "last_login": fake.date_time()
    }

@pytest.fixture
def mock_message():
    """Message de conversation de test"""
    return {
        "id": fake.uuid4(),
        "content": fake.text(max_nb_chars=200),
        "type": fake.random_element(["user", "assistant", "system"]),
        "timestamp": fake.date_time(),
        "metadata": {
            "persona": fake.random_element(["jarvis_classic", "friday", "edith"]),
            "confidence": fake.random.uniform(0.7, 1.0),
            "processing_time": fake.random.uniform(0.1, 2.0)
        }
    }

@pytest.fixture
def mock_conversation():
    """Conversation de test avec plusieurs messages"""
    messages = []
    for _ in range(fake.random_int(min=3, max=10)):
        messages.append({
            "id": fake.uuid4(),
            "content": fake.text(max_nb_chars=150),
            "type": fake.random_element(["user", "assistant"]),
            "timestamp": fake.date_time(),
            "metadata": {}
        })
    
    return {
        "id": fake.uuid4(),
        "title": fake.catch_phrase(),
        "messages": messages,
        "created_at": fake.date_time(),
        "updated_at": fake.date_time(),
        "user_id": fake.uuid4()
    }

@pytest.fixture
def mock_gpu_stats():
    """Statistiques GPU de test"""
    return {
        "gpu_id": 0,
        "name": "AMD Radeon RX 7900 XTX",
        "temperature": fake.random_int(min=45, max=85),
        "utilization": fake.random_int(min=0, max=100),
        "memory_used": fake.random_int(min=2048, max=20480),
        "memory_total": 24576,
        "memory_free": fake.random_int(min=4096, max=22528),
        "power_draw": fake.random_int(min=50, max=300),
        "fan_speed": fake.random_int(min=800, max=3000),
        "timestamp": time.time()
    }

@pytest.fixture
def mock_system_stats():
    """Statistiques système de test"""
    return {
        "cpu": {
            "usage": fake.random_int(min=10, max=90),
            "temperature": fake.random_int(min=40, max=80),
            "cores": fake.random_int(min=4, max=32)
        },
        "memory": {
            "usage": fake.random_int(min=20, max=85),
            "total": fake.random_int(min=8192, max=65536),
            "available": fake.random_int(min=2048, max=32768)
        },
        "disk": {
            "usage": fake.random_int(min=30, max=90),
            "total": fake.random_int(min=256, max=4096),
            "free": fake.random_int(min=64, max=2048)
        },
        "network": {
            "status": "connected",
            "latency": fake.random.uniform(1.0, 50.0),
            "download_speed": fake.random.uniform(50.0, 1000.0),
            "upload_speed": fake.random.uniform(10.0, 100.0)
        },
        "timestamp": time.time()
    }

# ==========================================
# FIXTURES POUR MOCKS DE SERVICES
# ==========================================

@pytest.fixture
def mock_redis():
    """Mock Redis pour les tests"""
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.flushdb = AsyncMock(return_value=True)
    redis_mock.ping = AsyncMock(return_value=True)
    return redis_mock

@pytest.fixture
def mock_database():
    """Mock base de données pour les tests"""
    db_mock = Mock()
    db_mock.connect = AsyncMock()
    db_mock.disconnect = AsyncMock()
    db_mock.execute = AsyncMock()
    db_mock.fetch_all = AsyncMock(return_value=[])
    db_mock.fetch_one = AsyncMock(return_value=None)
    return db_mock

@pytest.fixture
def mock_websocket():
    """Mock WebSocket pour les tests"""
    ws_mock = Mock()
    ws_mock.accept = AsyncMock()
    ws_mock.send_text = AsyncMock()
    ws_mock.send_json = AsyncMock()
    ws_mock.receive_text = AsyncMock()
    ws_mock.receive_json = AsyncMock()
    ws_mock.close = AsyncMock()
    ws_mock.client_state = "CONNECTED"
    return ws_mock

@pytest.fixture
def mock_ollama_client():
    """Mock client Ollama pour les tests"""
    client_mock = Mock()
    client_mock.generate = AsyncMock(return_value={
        "response": fake.text(max_nb_chars=300),
        "model": "llama2",
        "created_at": fake.iso8601(),
        "done": True,
        "context": []
    })
    client_mock.list = AsyncMock(return_value={
        "models": [
            {"name": "llama2", "size": 3800000000},
            {"name": "codellama", "size": 3800000000}
        ]
    })
    return client_mock

# ==========================================
# FIXTURES SPÉCIFIQUES JARVIS
# ==========================================

@pytest.fixture
def mock_tts_engine():
    """Mock TTS Engine pour les tests"""
    engine_mock = Mock()
    engine_mock.initialize = AsyncMock(return_value=True)
    engine_mock.shutdown = AsyncMock()
    engine_mock.is_model_loaded = Mock(return_value=True)
    engine_mock.synthesize = AsyncMock(return_value=b"fake_audio_data")
    engine_mock.list_voices = AsyncMock(return_value=[
        {"id": "french_male", "name": "Français Masculin"},
        {"id": "french_female", "name": "Français Féminin"}
    ])
    engine_mock.clone_voice = AsyncMock(return_value="cloned_voice_id")
    return engine_mock

@pytest.fixture
def mock_audio_processor():
    """Mock Audio Processor pour les tests"""
    processor_mock = Mock()
    processor_mock.initialize = AsyncMock(return_value=True)
    processor_mock.shutdown = AsyncMock()
    processor_mock.process = AsyncMock(return_value=b"processed_audio_data")
    processor_mock.normalize = Mock(return_value=b"normalized_audio")
    processor_mock.remove_silence = Mock(return_value=b"cleaned_audio")
    return processor_mock

@pytest.fixture
def mock_stream_manager():
    """Mock Stream Manager pour les tests"""
    manager_mock = Mock()
    manager_mock.initialize = AsyncMock(return_value=True)
    manager_mock.shutdown = AsyncMock()
    manager_mock.get_active_streams_count = Mock(return_value=0)
    
    async def mock_stream_synthesis(*args, **kwargs):
        # Simuler des chunks audio
        for i in range(3):
            yield f"audio_chunk_{i}".encode()
    
    manager_mock.stream_synthesis = mock_stream_synthesis
    return manager_mock

@pytest.fixture
def mock_amd_gpu_monitor():
    """Mock moniteur GPU AMD pour les tests"""
    monitor_mock = Mock()
    monitor_mock.initialize = AsyncMock(return_value=True)
    monitor_mock.shutdown = AsyncMock()
    monitor_mock.get_gpu_stats = AsyncMock()
    monitor_mock.get_temperature = Mock(return_value=65.0)
    monitor_mock.get_utilization = Mock(return_value=45.0)
    monitor_mock.get_memory_info = Mock(return_value={
        "used": 8192,
        "total": 24576,
        "free": 16384
    })
    return monitor_mock

@pytest.fixture
def mock_metacognition_engine():
    """Mock Metacognition Engine pour les tests"""
    engine_mock = Mock()
    engine_mock.initialize = AsyncMock(return_value=True)
    engine_mock.shutdown = AsyncMock()
    engine_mock.detect_hallucination = AsyncMock(return_value={
        "is_hallucination": False,
        "confidence": 0.95,
        "reasons": []
    })
    engine_mock.analyze_confidence = Mock(return_value=0.87)
    engine_mock.should_escalate = Mock(return_value=False)
    return engine_mock

# ==========================================
# FIXTURES POUR PERSONAS
# ==========================================

@pytest.fixture
def mock_persona_config():
    """Configuration de persona de test"""
    return {
        "name": fake.random_element(["JARVIS Classic", "FRIDAY", "EDITH"]),
        "description": fake.text(max_nb_chars=100),
        "personality_traits": fake.words(nb=5, unique=True),
        "voice_settings": {
            "pitch": fake.random.uniform(-3.0, 3.0),
            "speed": fake.random.uniform(0.5, 2.0),
            "voice_id": fake.random_element(["french_male", "french_female"]),
            "effects": {
                "reverb": fake.random.uniform(0.0, 1.0),
                "chorus": fake.random.uniform(0.0, 1.0)
            }
        },
        "response_style": fake.random_element(["formal", "casual", "technical"]),
        "greeting_phrases": [fake.catch_phrase() for _ in range(3)],
        "error_phrases": [fake.sentence() for _ in range(3)],
        "confirmation_phrases": [fake.word() for _ in range(3)]
    }

# ==========================================
# FIXTURES POUR SÉCURITÉ
# ==========================================

@pytest.fixture
def mock_jwt_token():
    """Token JWT de test"""
    import jwt
    payload = {
        "sub": fake.uuid4(),
        "username": fake.user_name(),
        "exp": fake.future_datetime(),
        "iat": fake.past_datetime(),
        "role": "user"
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")

@pytest.fixture
def malicious_payloads():
    """Payloads malveillants pour tests de sécurité"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT password FROM users WHERE username='admin'--"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>"
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| whoami",
            "&& rm -rf /",
            "`id`"
        ],
        "ldap_injection": [
            "*)(uid=*",
            "*)(objectClass=*",
            "admin)(&(password=*)",
            "*))%00"
        ]
    }

# ==========================================
# HELPERS ET UTILITAIRES
# ==========================================

@pytest.fixture
def assert_response_structure():
    """Helper pour vérifier la structure des réponses API"""
    def _assert_structure(response, required_fields):
        """Vérifie que la réponse contient tous les champs requis"""
        assert isinstance(response, dict), "La réponse doit être un dictionnaire"
        
        for field in required_fields:
            assert field in response, f"Champ manquant: {field}"
        
        if "status" in response:
            assert response["status"] in ["success", "error"], "Status invalide"
        
        if "timestamp" in response:
            assert isinstance(response["timestamp"], (int, float)), "Timestamp invalide"
    
    return _assert_structure

@pytest.fixture
def performance_timer():
    """Timer pour mesurer les performances"""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return PerformanceTimer()

# ==========================================
# FIXTURES AUTO-USE
# ==========================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuration automatique pour chaque test"""
    # Désactiver les logs externes bruyants
    import logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    yield
    
    # Nettoyage après chaque test
    # (si nécessaire)

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock automatique des services externes"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('aiohttp.ClientSession') as mock_session:
        
        # Configuration des mocks par défaut
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        
        yield {
            "requests_get": mock_get,
            "requests_post": mock_post,
            "aiohttp_session": mock_session
        }

# ==========================================
# MARQUEURS PERSONNALISÉS
# ==========================================

def pytest_configure(config):
    """Configuration des marqueurs personnalisés"""
    config.addinivalue_line(
        "markers", "slow: marque les tests comme lents (désactive avec -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration avec services externes"
    )
    config.addinivalue_line(
        "markers", "security: tests de sécurité"
    )
    config.addinivalue_line(
        "markers", "gpu: tests nécessitant un GPU AMD"
    )

def pytest_collection_modifyitems(config, items):
    """Modification automatique des items de test"""
    for item in items:
        # Marquer automatiquement les tests lents
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)
        
        # Marquer les tests asynchrones
        if "async" in item.name or "asyncio" in item.keywords:
            item.add_marker(pytest.mark.asyncio)

# ==========================================
# RAPPORT DE FIN DE SESSION
# ==========================================

@pytest.fixture(scope="session", autouse=True)
def test_session_info():
    """Informations sur la session de test"""
    start_time = time.time()
    
    print(f"\n🧪 Démarrage session de tests JARVIS AI")
    print(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python {sys.version}")
    print(f"📁 Répertoire: {os.getcwd()}")
    
    yield
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Session de tests terminée")
    print(f"⏱️  Durée totale: {duration:.2f}s")
    print(f"📊 Rapports disponibles dans tests/reports/")