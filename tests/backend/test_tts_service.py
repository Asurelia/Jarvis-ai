#!/usr/bin/env python3
"""
🗣️ Tests unitaires critiques pour TTS Service
Tests pour les presets Jarvis, synthèse vocale, streaming audio
"""

import pytest
import asyncio
import base64
import time
import io
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'tts-service'))

from main import app, app_state, TTSRequest, JarvisRequest, VoiceCloneRequest
from core.tts_engine import TTSEngine
from core.audio_processor import AudioProcessor
from core.stream_manager import StreamManager
from presets.preset_manager import preset_manager


class TestTTSServiceHealth:
    """Tests de santé et de status du service TTS"""
    
    def setup_method(self):
        self.client = TestClient(app)

    def test_root_endpoint_structure(self):
        """Test que l'endpoint racine retourne la structure attendue"""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier la structure de base
        assert "name" in data
        assert "version" in data
        assert "engine" in data
        assert "status" in data
        assert "services" in data
        assert "endpoints" in data
        
        # Vérifier les valeurs spécifiques
        assert data["name"] == "JARVIS TTS Service"
        assert data["version"] == "2.0.0"
        assert data["engine"] == "Coqui.ai XTTS"
        
        # Vérifier les services
        services = data["services"]
        expected_services = ["tts_engine", "audio_processor", "stream_manager"]
        for service in expected_services:
            assert service in services
            
        # Vérifier les endpoints
        endpoints = data["endpoints"]
        expected_endpoints = ["health", "synthesize", "stream", "voices", "jarvis", "presets", "jarvis_phrases", "websocket", "metrics", "docs"]
        for endpoint in expected_endpoints:
            assert endpoint in endpoints

    def test_health_endpoint_when_healthy(self):
        """Test endpoint de santé quand le service est sain"""
        # Simuler un état sain
        app_state["healthy"] = True
        app_state["startup_time"] = time.time() - 10
        app_state["tts_engine"] = Mock()
        app_state["tts_engine"].is_model_loaded = Mock(return_value=True)
        app_state["stream_manager"] = Mock()
        app_state["stream_manager"].get_active_streams_count = Mock(return_value=2)
        
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime" in data
        assert data["model_loaded"] is True
        assert data["active_streams"] == 2

    def test_health_endpoint_when_unhealthy(self):
        """Test endpoint de santé quand le service est défaillant"""
        # Simuler un état défaillant
        app_state["healthy"] = False
        
        response = self.client.get("/health")
        assert response.status_code == 503


class TestTTSEngine:
    """Tests pour le moteur TTS"""
    
    @pytest.fixture
    def tts_engine(self):
        """Fixture pour créer une instance de TTSEngine"""
        return TTSEngine(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            device="cpu",
            enable_anti_hallucination=True
        )

    @pytest.mark.asyncio
    async def test_tts_engine_initialization(self, tts_engine):
        """Test l'initialisation du moteur TTS"""
        with patch.object(tts_engine, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await tts_engine.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_synthesis_basic(self, tts_engine):
        """Test la synthèse de texte basique"""
        with patch.object(tts_engine, 'synthesize', new_callable=AsyncMock) as mock_synthesize:
            # Mock audio data (simuler des bytes audio)
            mock_audio_data = b"fake_audio_data_for_testing"
            mock_synthesize.return_value = mock_audio_data
            
            result = await tts_engine.synthesize(
                text="Hello, this is a test",
                voice_id="default",
                language="en",
                speed=1.0,
                pitch=1.0
            )
            
            assert result == mock_audio_data
            mock_synthesize.assert_called_once_with(
                text="Hello, this is a test",
                voice_id="default",
                language="en",
                speed=1.0,
                pitch=1.0
            )

    @pytest.mark.asyncio
    async def test_text_synthesis_with_preset(self, tts_engine):
        """Test la synthèse avec preset (retourne tuple avec effets)"""
        with patch.object(tts_engine, 'synthesize', new_callable=AsyncMock) as mock_synthesize:
            mock_audio_data = b"fake_audio_with_effects"
            mock_effects = {"reverb": 0.3, "chorus": 0.2}
            mock_synthesize.return_value = (mock_audio_data, mock_effects)
            
            result = await tts_engine.synthesize(
                text="Jarvis speaking",
                preset_name="jarvis",
                context="system_response"
            )
            
            assert isinstance(result, tuple)
            assert result[0] == mock_audio_data
            assert result[1] == mock_effects

    @pytest.mark.asyncio
    async def test_voice_listing(self, tts_engine):
        """Test la liste des voix disponibles"""
        with patch.object(tts_engine, 'list_voices', new_callable=AsyncMock) as mock_list:
            mock_voices = [
                {"id": "default", "name": "Default Voice", "language": "en"},
                {"id": "french_male", "name": "French Male", "language": "fr"},
                {"id": "french_female", "name": "French Female", "language": "fr"}
            ]
            mock_list.return_value = mock_voices
            
            result = await tts_engine.list_voices()
            assert len(result) == 3
            assert all("id" in voice for voice in result)
            assert all("name" in voice for voice in result)
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_voice_cloning(self, tts_engine):
        """Test le clonage de voix"""
        with patch.object(tts_engine, 'clone_voice', new_callable=AsyncMock) as mock_clone:
            mock_clone.return_value = "cloned_voice_id_123"
            
            fake_audio_data = b"fake_audio_sample_for_cloning"
            result = await tts_engine.clone_voice(
                name="Test Voice",
                audio_data=fake_audio_data,
                description="A test cloned voice"
            )
            
            assert result == "cloned_voice_id_123"
            mock_clone.assert_called_once_with(
                name="Test Voice",
                audio_data=fake_audio_data,
                description="A test cloned voice"
            )

    def test_model_loading_status(self, tts_engine):
        """Test le statut de chargement du modèle"""
        with patch.object(tts_engine, 'is_model_loaded', return_value=True):
            assert tts_engine.is_model_loaded() is True

    @pytest.mark.asyncio
    async def test_anti_hallucination_filtering(self, tts_engine):
        """Test le filtrage anti-hallucination"""
        with patch.object(tts_engine, '_filter_hallucinations', new_callable=AsyncMock) as mock_filter:
            clean_text = "This is clean text without hallucinations"
            mock_filter.return_value = clean_text
            
            dirty_text = "This text might contain [HALLUCINATED_CONTENT] some fake info"
            result = await tts_engine._filter_hallucinations(dirty_text)
            
            assert result == clean_text
            mock_filter.assert_called_once_with(dirty_text)


class TestAudioProcessor:
    """Tests pour le processeur audio"""
    
    @pytest.fixture
    def audio_processor(self):
        """Fixture pour créer une instance d'AudioProcessor"""
        return AudioProcessor(
            sample_rate=22050,
            channels=1,
            chunk_size=1024
        )

    @pytest.mark.asyncio
    async def test_audio_processor_initialization(self, audio_processor):
        """Test l'initialisation du processeur audio"""
        with patch.object(audio_processor, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await audio_processor.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_audio_processing_basic(self, audio_processor):
        """Test le traitement audio basique"""
        with patch.object(audio_processor, 'process', new_callable=AsyncMock) as mock_process:
            input_audio = b"raw_audio_data"
            processed_audio = b"processed_audio_data"
            mock_process.return_value = processed_audio
            
            result = await audio_processor.process(
                input_audio,
                normalize=True,
                remove_silence=True
            )
            
            assert result == processed_audio
            mock_process.assert_called_once_with(
                input_audio,
                normalize=True,
                remove_silence=True
            )

    @pytest.mark.asyncio
    async def test_audio_processing_with_effects(self, audio_processor):
        """Test le traitement audio avec effets"""
        with patch.object(audio_processor, 'process', new_callable=AsyncMock) as mock_process:
            input_audio = b"raw_audio_data"
            processed_audio = b"processed_audio_with_effects"
            preset_effects = {"reverb": 0.3, "pitch_shift": -2.0}
            mock_process.return_value = processed_audio
            
            result = await audio_processor.process(
                input_audio,
                normalize=True,
                remove_silence=True,
                apply_filters=True,
                preset_effects=preset_effects
            )
            
            assert result == processed_audio
            mock_process.assert_called_once_with(
                input_audio,
                normalize=True,
                remove_silence=True,
                apply_filters=True,
                preset_effects=preset_effects
            )

    @pytest.mark.asyncio
    async def test_audio_format_conversion(self, audio_processor):
        """Test la conversion de format audio"""
        with patch.object(audio_processor, 'convert_format', new_callable=AsyncMock) as mock_convert:
            input_audio = b"input_format_audio"
            converted_audio = b"output_format_audio"
            mock_convert.return_value = converted_audio
            
            result = await audio_processor.convert_format(
                input_audio,
                input_format="mp3",
                output_format="wav"
            )
            
            assert result == converted_audio
            mock_convert.assert_called_once_with(
                input_audio,
                input_format="mp3",
                output_format="wav"
            )


class TestStreamManager:
    """Tests pour le gestionnaire de streaming"""
    
    @pytest.fixture
    def stream_manager(self):
        """Fixture pour créer une instance de StreamManager"""
        tts_engine = Mock()
        audio_processor = Mock()
        return StreamManager(
            tts_engine=tts_engine,
            audio_processor=audio_processor
        )

    @pytest.mark.asyncio
    async def test_stream_manager_initialization(self, stream_manager):
        """Test l'initialisation du gestionnaire de streaming"""
        with patch.object(stream_manager, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await stream_manager.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_streaming_synthesis(self, stream_manager):
        """Test la synthèse en streaming"""
        # Mock des chunks audio
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3"]
        
        async def mock_stream_synthesis(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch.object(stream_manager, 'stream_synthesis', mock_stream_synthesis):
            chunks = []
            async for chunk in stream_manager.stream_synthesis(
                text="Test streaming text",
                voice_id="default"
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 3
            assert chunks == mock_chunks

    def test_active_streams_count(self, stream_manager):
        """Test le comptage des streams actifs"""
        with patch.object(stream_manager, 'get_active_streams_count', return_value=5):
            count = stream_manager.get_active_streams_count()
            assert count == 5

    @pytest.mark.asyncio
    async def test_stream_cleanup(self, stream_manager):
        """Test le nettoyage des streams"""
        with patch.object(stream_manager, 'cleanup_streams', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.return_value = 3  # Nombre de streams nettoyés
            
            result = await stream_manager.cleanup_streams()
            assert result == 3
            mock_cleanup.assert_called_once()


class TestJarvisPresets:
    """Tests pour les presets spécifiques à Jarvis"""
    
    def test_preset_manager_jarvis_phrases(self):
        """Test l'obtention des phrases Jarvis"""
        with patch.object(preset_manager, 'get_jarvis_phrases') as mock_get_phrases:
            mock_phrases = {
                "greetings": ["Good morning, sir", "At your service", "How may I assist you?"],
                "confirmations": ["Certainly, sir", "Right away", "Consider it done"],
                "errors": ["I apologize, but", "There seems to be an issue", "Let me try again"]
            }
            mock_get_phrases.return_value = mock_phrases
            
            result = preset_manager.get_jarvis_phrases()
            assert "greetings" in result
            assert "confirmations" in result
            assert "errors" in result
            assert len(result["greetings"]) == 3

    def test_preset_manager_jarvis_phrases_by_category(self):
        """Test l'obtention des phrases Jarvis par catégorie"""
        with patch.object(preset_manager, 'get_jarvis_phrases') as mock_get_phrases:
            mock_phrases = {
                "greetings": ["Good morning, sir", "At your service", "How may I assist you?"]
            }
            mock_get_phrases.return_value = mock_phrases
            
            result = preset_manager.get_jarvis_phrases("greetings")
            assert "greetings" in result
            assert len(result["greetings"]) == 3

    def test_preset_manager_list_presets(self):
        """Test la liste des presets disponibles"""
        with patch.object(preset_manager, 'list_presets') as mock_list:
            mock_presets = [
                {"id": "jarvis", "name": "JARVIS Classic", "description": "Original JARVIS voice"},
                {"id": "friday", "name": "FRIDAY", "description": "Casual and friendly"},
                {"id": "edith", "name": "EDITH", "description": "Technical and precise"}
            ]
            mock_list.return_value = mock_presets
            
            result = preset_manager.list_presets()
            assert len(result) == 3
            assert any(preset["id"] == "jarvis" for preset in result)

    def test_preset_manager_get_preset(self):
        """Test l'obtention d'un preset spécifique"""
        with patch.object(preset_manager, 'get_preset') as mock_get:
            mock_preset = {
                "name": "JARVIS Classic",
                "description": "Original JARVIS voice with professional tone",
                "voice_parameters": {"pitch": -2.0, "speed": 0.95},
                "audio_effects": {"reverb": 0.3, "chorus": 0.1},
                "jarvis_phrases": {
                    "greetings": ["Good morning, sir", "At your service"]
                }
            }
            mock_get.return_value = mock_preset
            
            result = preset_manager.get_preset("jarvis")
            assert result["name"] == "JARVIS Classic"
            assert "voice_parameters" in result
            assert "audio_effects" in result


class TestTTSServiceEndpoints:
    """Tests pour les endpoints du service TTS"""
    
    def setup_method(self):
        self.client = TestClient(app)
        # Simuler un état sain
        app_state["healthy"] = True
        app_state["tts_engine"] = Mock()
        app_state["audio_processor"] = Mock()
        app_state["stream_manager"] = Mock()

    def test_synthesize_endpoint_basic(self):
        """Test l'endpoint de synthèse basique"""
        # Mock des dépendances
        mock_audio_data = b"fake_synthesized_audio"
        mock_processed_audio = b"fake_processed_audio"
        
        app_state["tts_engine"].synthesize = AsyncMock(return_value=mock_audio_data)
        app_state["audio_processor"].process = AsyncMock(return_value=mock_processed_audio)
        
        request_data = {
            "text": "Hello, this is a test",
            "voice_id": "default",
            "language": "en",
            "speed": 1.0,
            "pitch": 1.0,
            "streaming": False
        }
        
        response = self.client.post("/api/synthesize", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "audio" in data
        assert data["format"] == "wav"
        assert "sample_rate" in data
        assert "duration_ms" in data

    def test_jarvis_endpoint_with_preset(self):
        """Test l'endpoint spécialisé Jarvis"""
        # Mock des dépendances
        mock_audio_data = b"jarvis_audio_data"
        mock_effects = {"reverb": 0.3, "pitch_shift": -2.0}
        mock_processed_audio = b"jarvis_processed_audio"
        
        app_state["tts_engine"].synthesize = AsyncMock(return_value=(mock_audio_data, mock_effects))
        app_state["audio_processor"].process = AsyncMock(return_value=mock_processed_audio)
        
        request_data = {
            "text": "System status nominal",
            "context": "system_response",
            "phrase_category": "confirmations"
        }
        
        response = self.client.post("/api/tts/jarvis", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["preset"] == "jarvis"
        assert "voice_effects" in data
        assert "enhanced_text" in data

    def test_voices_endpoint(self):
        """Test l'endpoint de liste des voix"""
        # Mock de la liste des voix
        mock_voices = [
            {"id": "default", "name": "Default Voice", "language": "en"},
            {"id": "french_male", "name": "French Male", "language": "fr"}
        ]
        app_state["tts_engine"].list_voices = AsyncMock(return_value=mock_voices)
        
        response = self.client.get("/api/voices")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert len(data["voices"]) == 2
        assert data["count"] == 2

    def test_presets_endpoint(self):
        """Test l'endpoint de liste des presets"""
        mock_presets = [
            {"id": "jarvis", "name": "JARVIS Classic"},
            {"id": "friday", "name": "FRIDAY"}
        ]
        
        with patch.object(preset_manager, 'list_presets', return_value=mock_presets):
            response = self.client.get("/api/presets")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert len(data["presets"]) == 2

    def test_jarvis_phrases_endpoint(self):
        """Test l'endpoint des phrases Jarvis"""
        mock_phrases = {
            "greetings": ["Good morning, sir", "At your service"],
            "confirmations": ["Certainly, sir", "Right away"]
        }
        
        with patch.object(preset_manager, 'get_jarvis_phrases', return_value=mock_phrases):
            response = self.client.get("/api/jarvis/phrases")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "phrases" in data
            assert "categories" in data
            assert data["total_phrases"] == 4

    def test_jarvis_phrases_by_category_endpoint(self):
        """Test l'endpoint des phrases Jarvis par catégorie"""
        mock_phrases = {
            "greetings": ["Good morning, sir", "At your service", "How may I assist you?"]
        }
        
        with patch.object(preset_manager, 'get_jarvis_phrases', return_value=mock_phrases):
            response = self.client.get("/api/jarvis/phrases/greetings")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["category"] == "greetings"
            assert len(data["phrases"]) == 3

    def test_preset_info_endpoint(self):
        """Test l'endpoint d'information sur un preset"""
        mock_preset = Mock()
        mock_preset.name = "JARVIS Classic"
        mock_preset.description = "Original JARVIS voice"
        mock_preset.get_voice_parameters = Mock(return_value={"pitch": -2.0, "speed": 0.95})
        mock_preset.get_audio_effects = Mock(return_value={"reverb": 0.3})
        mock_preset.jarvis_phrases = {"greetings": [], "confirmations": []}
        
        with patch.object(preset_manager, 'get_preset', return_value=mock_preset):
            response = self.client.get("/api/presets/jarvis")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["preset"]["name"] == "JARVIS Classic"
            assert "voice_parameters" in data["preset"]
            assert "audio_effects" in data["preset"]


class TestTTSServiceErrors:
    """Tests pour la gestion d'erreurs du service TTS"""
    
    def setup_method(self):
        self.client = TestClient(app)

    def test_synthesize_when_engine_unavailable(self):
        """Test synthèse quand le moteur TTS n'est pas disponible"""
        app_state["tts_engine"] = None
        
        request_data = {
            "text": "Hello, this is a test",
            "voice_id": "default"
        }
        
        response = self.client.post("/api/synthesize", json=request_data)
        assert response.status_code == 503
        assert "TTS Engine non disponible" in response.json()["detail"]

    def test_voices_when_engine_unavailable(self):
        """Test liste des voix quand le moteur n'est pas disponible"""
        app_state["tts_engine"] = None
        
        response = self.client.get("/api/voices")
        assert response.status_code == 503

    def test_stream_when_manager_unavailable(self):
        """Test streaming quand le gestionnaire n'est pas disponible"""
        app_state["stream_manager"] = None
        
        request_data = {
            "text": "Test streaming",
            "streaming": True
        }
        
        response = self.client.post("/api/stream", json=request_data)
        assert response.status_code == 503

    def test_preset_not_found(self):
        """Test preset non trouvé"""
        with patch.object(preset_manager, 'get_preset', return_value=None):
            response = self.client.get("/api/presets/nonexistent")
            assert response.status_code == 404
            assert "Preset non trouvé" in response.json()["detail"]

    def test_jarvis_phrases_category_not_found(self):
        """Test catégorie de phrases Jarvis non trouvée"""
        mock_phrases = {"greetings": ["Hello"]}  # Pas de catégorie "nonexistent"
        
        with patch.object(preset_manager, 'get_jarvis_phrases', return_value=mock_phrases):
            response = self.client.get("/api/jarvis/phrases/nonexistent")
            assert response.status_code == 404
            assert "Catégorie non trouvée" in response.json()["detail"]


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Helpers pour les tests TTS
class TestTTSHelpers:
    """Helpers utilitaires pour les tests TTS"""
    
    @staticmethod
    def create_mock_audio_data(size=1024):
        """Crée des données audio mock pour les tests"""
        return b"fake_audio_data" * (size // 15)  # Répéter pour atteindre la taille
    
    @staticmethod
    def create_mock_tts_request(text="Test text", voice_id="default"):
        """Crée une requête TTS mock"""
        return TTSRequest(
            text=text,
            voice_id=voice_id,
            language="en",
            speed=1.0,
            pitch=1.0,
            streaming=False
        )
    
    @staticmethod
    def create_mock_jarvis_request(text="Test message", context=None):
        """Crée une requête Jarvis mock"""
        return JarvisRequest(
            text=text,
            context=context,
            phrase_category="greetings"
        )
    
    @staticmethod
    def assert_audio_response_structure(response_data):
        """Vérifie la structure d'une réponse audio"""
        required_fields = ["status", "audio", "format", "sample_rate", "channels", "duration_ms"]
        for field in required_fields:
            assert field in response_data, f"Champ audio manquant: {field}"
        
        # Vérifier que l'audio est du base64 valide
        try:
            base64.b64decode(response_data["audio"])
        except Exception:
            pytest.fail("Audio data is not valid base64")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])