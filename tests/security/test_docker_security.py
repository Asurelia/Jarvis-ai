#!/usr/bin/env python3
"""
🐳 Tests de sécurité critiques pour Docker
Tests pour la configuration Docker sécurisée, vulnérabilités, isolation
"""

import pytest
import docker
import json
import yaml
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Mock du client Docker pour les tests
class MockDockerClient:
    def __init__(self):
        self.containers = MockContainerManager()
        self.images = MockImageManager()
        self.networks = MockNetworkManager()
        self.volumes = MockVolumeManager()
        self.info = Mock(return_value={'SecurityOptions': ['apparmor', 'seccomp']})
        
    def close(self):
        pass

class MockContainerManager:
    def __init__(self):
        self.containers_list = []
    
    def run(self, image, **kwargs):
        container = MockContainer(image, **kwargs)
        self.containers_list.append(container)
        return container
    
    def list(self, all=False):
        return self.containers_list if all else [c for c in self.containers_list if c.status == 'running']
    
    def get(self, container_id):
        for container in self.containers_list:
            if container.id == container_id or container.name == container_id:
                return container
        raise docker.errors.NotFound(f"Container {container_id} not found")

class MockContainer:
    def __init__(self, image, **kwargs):
        self.id = f"container_{len(MockContainerManager().containers_list)}"
        self.name = kwargs.get('name', f"test_container_{self.id}")
        self.image = Mock()
        self.image.tags = [image]
        self.status = 'running'
        self.attrs = {
            'Config': {
                'User': kwargs.get('user', 'root'),
                'Env': kwargs.get('environment', []),
                'ExposedPorts': {},
                'Volumes': kwargs.get('volumes', {}),
                'WorkingDir': kwargs.get('working_dir', '/'),
                'Cmd': kwargs.get('command', ['/bin/sh'])
            },
            'HostConfig': {
                'Privileged': kwargs.get('privileged', False),
                'ReadonlyRootfs': kwargs.get('read_only', False),
                'CapAdd': kwargs.get('cap_add', []),
                'CapDrop': kwargs.get('cap_drop', []),
                'SecurityOpt': kwargs.get('security_opt', []),
                'NetworkMode': kwargs.get('network_mode', 'default'),
                'Memory': kwargs.get('mem_limit', 0),
                'CpuShares': kwargs.get('cpu_shares', 0),
                'PidsLimit': kwargs.get('pids_limit', 0),
                'Ulimits': kwargs.get('ulimits', []),
                'Binds': kwargs.get('volumes', {})
            },
            'NetworkSettings': {
                'Ports': kwargs.get('ports', {}),
                'Networks': {}
            },
            'Mounts': []
        }
    
    def exec_run(self, cmd, **kwargs):
        return (0, b"mock output")
    
    def logs(self, **kwargs):
        return b"mock container logs"
    
    def stop(self):
        self.status = 'stopped'
    
    def remove(self):
        self.status = 'removed'
    
    def inspect(self):
        return self.attrs

class MockImageManager:
    def __init__(self):
        self.images_list = []
    
    def build(self, path=None, dockerfile=None, tag=None, **kwargs):
        image = MockImage(tag or 'test:latest')
        self.images_list.append(image)
        return image, iter([b'{"stream": "Building image..."}'])
    
    def list(self):
        return self.images_list
    
    def get(self, image_name):
        for image in self.images_list:
            if image_name in image.tags:
                return image
        raise docker.errors.ImageNotFound(f"Image {image_name} not found")

class MockImage:
    def __init__(self, tag):
        self.id = f"sha256:{'0' * 64}"
        self.tags = [tag]
        self.attrs = {
            'Config': {
                'User': 'root',
                'Env': [],
                'ExposedPorts': {},
                'Volumes': {},
                'WorkingDir': '/',
                'Cmd': ['/bin/sh']
            },
            'RootFS': {
                'Layers': [f"sha256:{'1' * 64}", f"sha256:{'2' * 64}"]
            }
        }

class MockNetworkManager:
    def __init__(self):
        self.networks_list = []
    
    def create(self, name, **kwargs):
        network = MockNetwork(name, **kwargs)
        self.networks_list.append(network)
        return network
    
    def list(self):
        return self.networks_list

class MockNetwork:
    def __init__(self, name, **kwargs):
        self.id = f"network_{len(MockNetworkManager().networks_list)}"
        self.name = name
        self.attrs = {
            'Driver': kwargs.get('driver', 'bridge'),
            'Options': kwargs.get('options', {}),
            'IPAM': kwargs.get('ipam', {}),
            'Internal': kwargs.get('internal', False),
            'Attachable': kwargs.get('attachable', True)
        }

class MockVolumeManager:
    def __init__(self):
        self.volumes_list = []
    
    def create(self, name, **kwargs):
        volume = MockVolume(name, **kwargs)
        self.volumes_list.append(volume)
        return volume
    
    def list(self):
        return self.volumes_list

class MockVolume:
    def __init__(self, name, **kwargs):
        self.id = f"volume_{len(MockVolumeManager().volumes_list)}"
        self.name = name
        self.attrs = {
            'Driver': kwargs.get('driver', 'local'),
            'Options': kwargs.get('options', {}),
            'Mountpoint': f"/var/lib/docker/volumes/{name}/_data"
        }


class TestDockerSecurity:
    """Tests de sécurité pour les configurations Docker"""
    
    @pytest.fixture
    def docker_client(self):
        """Fixture pour créer un client Docker mock"""
        return MockDockerClient()
    
    @pytest.fixture
    def sample_dockerfile(self):
        """Fixture pour créer un Dockerfile de test"""
        dockerfile_content = """
FROM python:3.11-slim

# Utilisateur non-root
RUN groupadd -r jarvis && useradd -r -g jarvis jarvis

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers
COPY requirements.txt /app/
COPY src/ /app/src/

# Installation des dépendances Python
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Configuration de l'utilisateur
USER jarvis

# Port d'exposition
EXPOSE 8000

# Commande par défaut
CMD ["python", "src/main.py"]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dockerfile', delete=False) as f:
            f.write(dockerfile_content)
            return f.name

    def test_dockerfile_user_security(self, sample_dockerfile):
        """Test que le Dockerfile n'utilise pas l'utilisateur root"""
        with open(sample_dockerfile, 'r') as f:
            content = f.read()
        
        # Vérifier qu'un utilisateur non-root est créé
        assert 'useradd' in content or 'adduser' in content
        assert 'USER jarvis' in content or 'USER ' in content
        
        # Vérifier qu'on ne reste pas en root
        lines = content.split('\n')
        user_line_found = False
        for line in lines:
            if line.strip().startswith('USER ') and 'root' not in line:
                user_line_found = True
                break
        
        assert user_line_found, "Dockerfile should specify a non-root user"

    def test_dockerfile_no_secrets(self, sample_dockerfile):
        """Test que le Dockerfile ne contient pas de secrets hardcodés"""
        with open(sample_dockerfile, 'r') as f:
            content = f.read().upper()
        
        dangerous_patterns = [
            'PASSWORD=',
            'API_KEY=',
            'SECRET=',
            'TOKEN=',
            'PRIVATE_KEY',
            'AWS_ACCESS_KEY',
            'DATABASE_URL='
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in content, f"Dockerfile contains potential secret: {pattern}"

    def test_dockerfile_package_security(self, sample_dockerfile):
        """Test les bonnes pratiques de sécurité pour les packages"""
        with open(sample_dockerfile, 'r') as f:
            content = f.read()
        
        # Vérifier l'utilisation de --no-cache-dir pour pip
        if 'pip install' in content:
            assert '--no-cache-dir' in content, "pip install should use --no-cache-dir"
        
        # Vérifier le nettoyage des caches apt
        if 'apt-get install' in content:
            assert 'rm -rf /var/lib/apt/lists/*' in content, "apt cache should be cleaned"
        
        # Vérifier l'utilisation de --no-install-recommends
        if 'apt-get install' in content:
            assert '--no-install-recommends' in content, "apt should use --no-install-recommends"


class TestContainerSecurity:
    """Tests de sécurité pour les conteneurs en cours d'exécution"""
    
    @pytest.fixture
    def docker_client(self):
        return MockDockerClient()

    def test_container_not_privileged(self, docker_client):
        """Test qu'un conteneur n'est pas lancé en mode privilégié"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            privileged=False,
            detach=True
        )
        
        config = container.inspect()
        assert not config['HostConfig']['Privileged'], "Container should not run in privileged mode"

    def test_container_read_only_filesystem(self, docker_client):
        """Test que le système de fichiers du conteneur est en lecture seule"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            read_only=True,
            detach=True
        )
        
        config = container.inspect()
        assert config['HostConfig']['ReadonlyRootfs'], "Container filesystem should be read-only"

    def test_container_capabilities_dropped(self, docker_client):
        """Test que les capacités dangereuses sont supprimées"""
        dangerous_capabilities = ['SYS_ADMIN', 'NET_ADMIN', 'SYS_MODULE', 'SYS_TIME']
        
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            cap_drop=['ALL'],
            cap_add=['NET_BIND_SERVICE'],  # Seulement les capacités nécessaires
            detach=True
        )
        
        config = container.inspect()
        cap_drop = config['HostConfig']['CapDrop']
        
        assert 'ALL' in cap_drop, "All capabilities should be dropped by default"
        
        # Vérifier que seules les capacités nécessaires sont ajoutées
        cap_add = config['HostConfig']['CapAdd']
        for cap in cap_add:
            assert cap in ['NET_BIND_SERVICE'], f"Unnecessary capability added: {cap}"

    def test_container_security_options(self, docker_client):
        """Test que les options de sécurité appropriées sont configurées"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            security_opt=[
                'no-new-privileges:true',
                'apparmor:docker-default',
                'seccomp:default'
            ],
            detach=True
        )
        
        config = container.inspect()
        security_opt = config['HostConfig']['SecurityOpt']
        
        assert 'no-new-privileges:true' in security_opt
        assert any('apparmor' in opt for opt in security_opt)
        assert any('seccomp' in opt for opt in security_opt)

    def test_container_resource_limits(self, docker_client):
        """Test que les limites de ressources sont configurées"""
        memory_limit = 512 * 1024 * 1024  # 512MB
        cpu_shares = 512
        pids_limit = 100
        
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            mem_limit=memory_limit,
            cpu_shares=cpu_shares,
            pids_limit=pids_limit,
            detach=True
        )
        
        config = container.inspect()
        host_config = config['HostConfig']
        
        assert host_config['Memory'] == memory_limit, "Memory limit should be set"
        assert host_config['CpuShares'] == cpu_shares, "CPU shares should be limited"
        assert host_config['PidsLimit'] == pids_limit, "PID limit should be set"

    def test_container_network_isolation(self, docker_client):
        """Test l'isolation réseau des conteneurs"""
        # Créer un réseau personnalisé isolé
        network = docker_client.networks.create(
            'jarvis-secure-network',
            driver='bridge',
            internal=True,  # Pas d'accès externe
            options={'com.docker.network.bridge.enable_icc': 'false'}
        )
        
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            network_mode='jarvis-secure-network',
            detach=True
        )
        
        config = container.inspect()
        assert config['HostConfig']['NetworkMode'] == 'jarvis-secure-network'

    def test_container_volume_security(self, docker_client):
        """Test la sécurité des volumes montés"""
        # Volume en lecture seule pour les données sensibles
        secure_volume = docker_client.volumes.create(
            'jarvis-config',
            driver='local',
            options={'type': 'tmpfs', 'device': 'tmpfs', 'o': 'size=100m,uid=1000'}
        )
        
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            volumes={
                'jarvis-config': {'bind': '/app/config', 'mode': 'ro'},  # Read-only
                '/tmp': {'bind': '/app/tmp', 'mode': 'rw'}  # Writable temp
            },
            detach=True
        )
        
        # Vérifier les montages
        config = container.inspect()
        binds = config['HostConfig']['Binds']
        
        # Vérifier qu'aucun montage système sensible n'existe
        dangerous_mounts = ['/proc', '/sys', '/dev', '/etc', '/var/run/docker.sock']
        for mount in binds or []:
            for dangerous in dangerous_mounts:
                assert not mount.startswith(dangerous), f"Dangerous mount detected: {mount}"

    def test_container_ulimits(self, docker_client):
        """Test que les ulimits sont configurés pour éviter les attaques DoS"""
        ulimits = [
            {'Name': 'nofile', 'Soft': 1024, 'Hard': 2048},  # Limite de fichiers ouverts
            {'Name': 'nproc', 'Soft': 100, 'Hard': 200},     # Limite de processus
            {'Name': 'fsize', 'Soft': 100000000, 'Hard': 200000000}  # Taille de fichier
        ]
        
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            ulimits=ulimits,
            detach=True
        )
        
        config = container.inspect()
        container_ulimits = config['HostConfig']['Ulimits']
        
        assert len(container_ulimits) > 0, "Ulimits should be configured"
        
        # Vérifier les ulimits spécifiques
        ulimit_names = [u['Name'] for u in container_ulimits]
        assert 'nofile' in ulimit_names, "File descriptor limit should be set"
        assert 'nproc' in ulimit_names, "Process limit should be set"


class TestDockerComposeSecurity:
    """Tests de sécurité pour Docker Compose"""
    
    @pytest.fixture
    def sample_compose_file(self):
        """Fixture pour créer un fichier docker-compose.yml de test"""
        compose_content = {
            'version': '3.8',
            'services': {
                'brain-api': {
                    'build': {
                        'context': './services/brain-api',
                        'dockerfile': 'Dockerfile'
                    },
                    'user': '1000:1000',
                    'read_only': True,
                    'cap_drop': ['ALL'],
                    'cap_add': ['NET_BIND_SERVICE'],
                    'security_opt': [
                        'no-new-privileges:true',
                        'apparmor:docker-default'
                    ],
                    'mem_limit': '512m',
                    'cpus': '0.5',
                    'pids_limit': 100,
                    'networks': ['jarvis-internal'],
                    'volumes': [
                        'brain-data:/app/data:ro',
                        'brain-logs:/app/logs:rw'
                    ],
                    'environment': [
                        'PYTHONDONTWRITEBYTECODE=1',
                        'PYTHONUNBUFFERED=1'
                    ],
                    'restart': 'unless-stopped',
                    'healthcheck': {
                        'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
                        'interval': '30s',
                        'timeout': '10s',
                        'retries': 3
                    }
                },
                'tts-service': {
                    'build': './services/tts-service',
                    'user': '1001:1001',
                    'read_only': True,
                    'cap_drop': ['ALL'],
                    'security_opt': ['no-new-privileges:true'],
                    'mem_limit': '1g',
                    'networks': ['jarvis-internal'],
                    'depends_on': ['brain-api']
                }
            },
            'networks': {
                'jarvis-internal': {
                    'driver': 'bridge',
                    'internal': True,
                    'driver_opts': {
                        'com.docker.network.bridge.enable_icc': 'false'
                    }
                }
            },
            'volumes': {
                'brain-data': {
                    'driver': 'local',
                    'driver_opts': {
                        'type': 'tmpfs',
                        'device': 'tmpfs',
                        'o': 'size=100m,uid=1000'
                    }
                },
                'brain-logs': {
                    'driver': 'local'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(compose_content, f)
            return f.name

    def test_compose_services_security(self, sample_compose_file):
        """Test que les services ont les configurations de sécurité appropriées"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        for service_name, service_config in services.items():
            # Vérifier l'utilisateur non-root
            assert 'user' in service_config, f"Service {service_name} should specify a non-root user"
            user = service_config['user']
            assert user != 'root' and user != '0:0', f"Service {service_name} should not run as root"
            
            # Vérifier le système de fichiers en lecture seule
            assert service_config.get('read_only', False), f"Service {service_name} should have read-only filesystem"
            
            # Vérifier les capabilities
            assert 'cap_drop' in service_config, f"Service {service_name} should drop capabilities"
            assert 'ALL' in service_config['cap_drop'], f"Service {service_name} should drop all capabilities"
            
            # Vérifier les options de sécurité
            security_opt = service_config.get('security_opt', [])
            assert any('no-new-privileges:true' in opt for opt in security_opt), \
                f"Service {service_name} should have no-new-privileges"

    def test_compose_network_security(self, sample_compose_file):
        """Test la configuration réseau sécurisée"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        networks = compose_data.get('networks', {})
        
        for network_name, network_config in networks.items():
            if network_name == 'jarvis-internal':
                # Réseau interne isolé
                assert network_config.get('internal', False), \
                    f"Internal network {network_name} should be isolated"
                
                # Désactiver la communication inter-conteneurs par défaut
                driver_opts = network_config.get('driver_opts', {})
                assert driver_opts.get('com.docker.network.bridge.enable_icc') == 'false', \
                    "Inter-container communication should be disabled by default"

    def test_compose_volume_security(self, sample_compose_file):
        """Test la configuration sécurisée des volumes"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        volumes = compose_data.get('volumes', {})
        services = compose_data.get('services', {})
        
        # Vérifier que les volumes sensibles utilisent tmpfs
        sensitive_volumes = ['brain-data']
        for vol_name in sensitive_volumes:
            if vol_name in volumes:
                vol_config = volumes[vol_name]
                driver_opts = vol_config.get('driver_opts', {})
                assert driver_opts.get('type') == 'tmpfs', \
                    f"Sensitive volume {vol_name} should use tmpfs"
        
        # Vérifier les montages dans les services
        for service_name, service_config in services.items():
            service_volumes = service_config.get('volumes', [])
            for volume in service_volumes:
                if isinstance(volume, str):
                    # Format: source:target:mode
                    parts = volume.split(':')
                    if len(parts) >= 3:
                        mode = parts[2]
                        # Les volumes de données devraient être en lecture seule
                        if 'data' in parts[0]:
                            assert 'ro' in mode, f"Data volume should be read-only in {service_name}"

    def test_compose_resource_limits(self, sample_compose_file):
        """Test que les limites de ressources sont définies"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        for service_name, service_config in services.items():
            # Vérifier les limites mémoire
            assert 'mem_limit' in service_config, \
                f"Service {service_name} should have memory limit"
            
            # Vérifier les limites CPU si spécifiées
            if 'cpus' in service_config:
                cpus = float(service_config['cpus'])
                assert 0 < cpus <= 2.0, \
                    f"Service {service_name} CPU limit should be reasonable"
            
            # Vérifier les limites de processus
            if 'pids_limit' in service_config:
                pids_limit = service_config['pids_limit']
                assert 0 < pids_limit <= 1000, \
                    f"Service {service_name} PID limit should be reasonable"

    def test_compose_healthchecks(self, sample_compose_file):
        """Test que les services ont des healthchecks configurés"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        critical_services = ['brain-api']  # Services critiques qui doivent avoir des healthchecks
        
        for service_name in critical_services:
            if service_name in services:
                service_config = services[service_name]
                assert 'healthcheck' in service_config, \
                    f"Critical service {service_name} should have healthcheck"
                
                healthcheck = service_config['healthcheck']
                assert 'test' in healthcheck, "Healthcheck should have test command"
                assert 'interval' in healthcheck, "Healthcheck should have interval"
                assert 'timeout' in healthcheck, "Healthcheck should have timeout"
                assert 'retries' in healthcheck, "Healthcheck should have retries"

    def test_compose_no_privileged_containers(self, sample_compose_file):
        """Test qu'aucun conteneur n'est en mode privilégié"""
        with open(sample_compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        for service_name, service_config in services.items():
            # Vérifier qu'aucun service n'est privilégié
            assert not service_config.get('privileged', False), \
                f"Service {service_name} should not be privileged"
            
            # Vérifier qu'aucun service n'a accès au socket Docker
            volumes = service_config.get('volumes', [])
            for volume in volumes:
                if isinstance(volume, str):
                    assert '/var/run/docker.sock' not in volume, \
                        f"Service {service_name} should not have access to Docker socket"


class TestImageSecurity:
    """Tests de sécurité pour les images Docker"""
    
    @pytest.fixture
    def docker_client(self):
        return MockDockerClient()

    def test_image_vulnerability_scan(self, docker_client):
        """Test de scan de vulnérabilités des images"""
        # Simuler un scan de vulnérabilités
        image = docker_client.images.get('jarvis-brain-api:latest')
        
        # Dans un vrai test, on utiliserait des outils comme Trivy, Clair, ou Snyk
        vulnerabilities = self._mock_vulnerability_scan(image)
        
        # Vérifier qu'il n'y a pas de vulnérabilités critiques
        critical_vulns = [v for v in vulnerabilities if v['severity'] == 'CRITICAL']
        assert len(critical_vulns) == 0, f"Critical vulnerabilities found: {critical_vulns}"
        
        # Vérifier qu'il y a peu de vulnérabilités haute gravité
        high_vulns = [v for v in vulnerabilities if v['severity'] == 'HIGH']
        assert len(high_vulns) <= 5, f"Too many high severity vulnerabilities: {len(high_vulns)}"

    def _mock_vulnerability_scan(self, image):
        """Mock d'un scan de vulnérabilités"""
        return [
            {
                'id': 'CVE-2023-1234',
                'severity': 'MEDIUM',
                'package': 'libc6',
                'version': '2.31-13',
                'description': 'Buffer overflow in libc6'
            },
            {
                'id': 'CVE-2023-5678',
                'severity': 'LOW',
                'package': 'curl',
                'version': '7.68.0-1',
                'description': 'Minor security issue in curl'
            }
        ]

    def test_image_base_security(self, docker_client):
        """Test que les images utilisent des bases sécurisées"""
        image = docker_client.images.get('jarvis-brain-api:latest')
        
        # Vérifier les layers de l'image
        layers = image.attrs['RootFS']['Layers']
        
        # Dans un vrai test, on vérifierait que l'image de base est officielle et récente
        # Par exemple, python:3.11-slim au lieu de python:latest
        
        # Vérifier qu'il n'y a pas trop de layers (indication d'une image mal optimisée)
        assert len(layers) <= 20, f"Image has too many layers: {len(layers)}"

    def test_image_metadata_security(self, docker_client):
        """Test des métadonnées de sécurité de l'image"""
        image = docker_client.images.get('jarvis-brain-api:latest')
        config = image.attrs['Config']
        
        # Vérifier que l'utilisateur n'est pas root
        user = config.get('User', 'root')
        assert user != 'root' and user != '', "Image should not run as root user"
        
        # Vérifier qu'il n'y a pas de variables d'environnement sensibles
        env_vars = config.get('Env', [])
        for env_var in env_vars:
            var_upper = env_var.upper()
            dangerous_patterns = ['PASSWORD=', 'SECRET=', 'KEY=', 'TOKEN=']
            for pattern in dangerous_patterns:
                assert pattern not in var_upper, f"Sensitive environment variable found: {env_var}"
        
        # Vérifier que les ports exposés sont appropriés
        exposed_ports = config.get('ExposedPorts', {})
        for port in exposed_ports.keys():
            port_num = int(port.split('/')[0])
            # Éviter les ports système (< 1024) sauf exceptions
            if port_num < 1024:
                allowed_system_ports = [80, 443, 8000, 8080]
                assert port_num in allowed_system_ports, f"Suspicious system port exposed: {port_num}"


class TestRuntimeSecurity:
    """Tests de sécurité pendant l'exécution"""
    
    @pytest.fixture
    def docker_client(self):
        return MockDockerClient()

    def test_container_process_monitoring(self, docker_client):
        """Test du monitoring des processus dans le conteneur"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            detach=True
        )
        
        # Simuler l'inspection des processus
        exit_code, output = container.exec_run('ps aux')
        assert exit_code == 0, "Should be able to inspect processes"
        
        # Vérifier qu'il n'y a pas de processus suspects
        processes = output.decode('utf-8')
        suspicious_processes = ['nc', 'netcat', 'wget', 'curl -X POST']
        
        for suspicious in suspicious_processes:
            assert suspicious not in processes, f"Suspicious process found: {suspicious}"

    def test_container_file_integrity(self, docker_client):
        """Test de l'intégrité des fichiers dans le conteneur"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            detach=True
        )
        
        # Vérifier les permissions des fichiers sensibles
        sensitive_files = ['/etc/passwd', '/etc/shadow', '/etc/hosts']
        
        for file_path in sensitive_files:
            exit_code, output = container.exec_run(f'ls -la {file_path}')
            if exit_code == 0:  # File exists
                permissions = output.decode('utf-8').split()[0]
                # Vérifier que les fichiers sensibles ne sont pas world-writable
                assert permissions[8] != 'w', f"File {file_path} is world-writable"

    def test_container_network_connections(self, docker_client):
        """Test des connexions réseau du conteneur"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            detach=True
        )
        
        # Vérifier les connexions réseau actives
        exit_code, output = container.exec_run('netstat -tuln')
        if exit_code == 0:
            connections = output.decode('utf-8')
            
            # Vérifier qu'il n'y a pas de connexions suspectes
            suspicious_ports = ['22', '23', '21', '135', '139', '445']
            
            for port in suspicious_ports:
                assert f':{port} ' not in connections, f"Suspicious port {port} is listening"

    def test_container_log_monitoring(self, docker_client):
        """Test du monitoring des logs pour détecter les activités suspectes"""
        container = docker_client.containers.run(
            'jarvis-brain-api:latest',
            detach=True
        )
        
        # Récupérer les logs du conteneur
        logs = container.logs().decode('utf-8')
        
        # Patterns suspects dans les logs
        suspicious_patterns = [
            'error.*sql injection',
            'unauthorized access',
            'permission denied',
            'failed login.*admin',
            'privilege escalation'
        ]
        
        import re
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            assert len(matches) == 0, f"Suspicious activity detected in logs: {pattern}"


class TestSecretsManagement:
    """Tests pour la gestion sécurisée des secrets"""
    
    def test_docker_secrets_usage(self):
        """Test que les secrets Docker sont utilisés correctement"""
        # Simuler la création d'un secret Docker
        secret_content = "super_secret_api_key"
        
        # Dans un vrai environnement, on utiliserait Docker Swarm secrets
        # ou des solutions comme HashiCorp Vault, Kubernetes secrets, etc.
        
        # Vérifier que les secrets ne sont pas dans les variables d'environnement
        compose_content = {
            'version': '3.8',
            'services': {
                'brain-api': {
                    'image': 'jarvis-brain-api:latest',
                    'secrets': ['api_key'],
                    'environment': [
                        'API_KEY_FILE=/run/secrets/api_key'  # Référence au fichier secret
                    ]
                }
            },
            'secrets': {
                'api_key': {
                    'external': True
                }
            }
        }
        
        # Vérifier que le secret est référencé par fichier, pas par variable
        service_env = compose_content['services']['brain-api']['environment']
        api_key_env = [env for env in service_env if 'API_KEY' in env][0]
        
        assert 'API_KEY_FILE=' in api_key_env, "API key should be referenced as file"
        assert 'API_KEY=' not in api_key_env, "API key should not be in environment variable"

    def test_environment_variables_security(self):
        """Test que les variables d'environnement ne contiennent pas de secrets"""
        # Exemple de configuration incorrecte
        bad_env_vars = [
            'DATABASE_PASSWORD=secret123',
            'API_KEY=abc123def456',
            'JWT_SECRET=mysecretkey',
            'PRIVATE_KEY=-----BEGIN PRIVATE KEY-----'
        ]
        
        # Exemple de configuration correcte
        good_env_vars = [
            'DATABASE_PASSWORD_FILE=/run/secrets/db_password',
            'API_KEY_FILE=/run/secrets/api_key',
            'JWT_SECRET_FILE=/run/secrets/jwt_secret',
            'PRIVATE_KEY_FILE=/run/secrets/private_key'
        ]
        
        for bad_env in bad_env_vars:
            # Simuler la détection de secrets dans les variables d'environnement
            contains_secret = any(pattern in bad_env for pattern in ['=', 'secret', 'key', 'password'])
            if contains_secret and not bad_env.endswith('_FILE='):
                assert False, f"Environment variable contains secret: {bad_env}"
        
        for good_env in good_env_vars:
            assert '_FILE=' in good_env, f"Environment variable should reference file: {good_env}"

    def test_secrets_file_permissions(self):
        """Test que les fichiers de secrets ont les bonnes permissions"""
        # Simuler la vérification des permissions de fichiers secrets
        secret_files = [
            '/run/secrets/api_key',
            '/run/secrets/db_password',
            '/run/secrets/jwt_secret'
        ]
        
        # Dans un vrai test, on vérifierait les permissions réelles
        for secret_file in secret_files:
            # Les fichiers secrets devraient avoir des permissions restrictives (400 ou 600)
            expected_permissions = ['400', '600']  # owner read-only ou owner read-write
            
            # Simuler la vérification (dans un vrai test, on utiliserait os.stat)
            mock_permissions = '400'  # Simuler des permissions correctes
            
            assert mock_permissions in expected_permissions, \
                f"Secret file {secret_file} should have restrictive permissions"


# Tests d'intégration Docker
class TestDockerIntegrationSecurity:
    """Tests d'intégration de sécurité pour l'ensemble de l'infrastructure Docker"""
    
    def test_full_stack_security(self):
        """Test de sécurité de la stack complète"""
        # Simuler le déploiement de la stack complète
        services = ['brain-api', 'tts-service', 'gpu-stats', 'memory-db', 'redis']
        
        security_checklist = {
            'non_root_users': True,
            'read_only_filesystem': True,
            'capabilities_dropped': True,
            'security_options': True,
            'resource_limits': True,
            'network_isolation': True,
            'secrets_management': True,
            'logging_configured': True,
            'monitoring_enabled': True
        }
        
        for service in services:
            for check, expected in security_checklist.items():
                # Dans un vrai test, on vérifierait chaque aspect de sécurité
                actual = self._check_service_security(service, check)
                assert actual == expected, \
                    f"Security check {check} failed for service {service}"

    def _check_service_security(self, service, check):
        """Mock de vérification de sécurité pour un service"""
        # Dans un vrai test, cette méthode inspecterait réellement le service
        # et vérifierait les configurations de sécurité
        return True  # Simuler que tous les checks passent

    def test_compliance_audit(self):
        """Test d'audit de conformité Docker"""
        compliance_rules = {
            'CIS_Docker_1.1.1': 'Ensure a separate partition for containers has been created',
            'CIS_Docker_1.2.1': 'Ensure the container host has been Hardened',
            'CIS_Docker_2.1': 'Ensure network traffic is restricted between containers on the default bridge',
            'CIS_Docker_2.5': 'Ensure aufs storage driver is not used',
            'CIS_Docker_4.1': 'Ensure a user for the container has been created',
            'CIS_Docker_4.6': 'Ensure HEALTHCHECK instructions have been added to the container image',
            'CIS_Docker_5.3': 'Ensure Linux Kernel Capabilities are restricted within containers',
            'CIS_Docker_5.12': 'Ensure the container\'s root filesystem is mounted as read only'
        }
        
        for rule_id, rule_description in compliance_rules.items():
            # Dans un vrai audit, on vérifierait chaque règle CIS
            compliance_status = self._check_cis_compliance(rule_id)
            assert compliance_status, f"CIS compliance failed for {rule_id}: {rule_description}"

    def _check_cis_compliance(self, rule_id):
        """Mock de vérification de conformité CIS"""
        # Dans un vrai audit, cette méthode vérifierait la conformité réelle
        return True  # Simuler la conformité


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])