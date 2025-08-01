# JARVIS AI Database Management System

Un système complet de gestion de base de données pour JARVIS AI comprenant les backups automatisés, migrations, monitoring de santé et politiques de rétention des données.

## 🏗️ Architecture

```
database/
├── backup/              # Système de backup automatisé
│   ├── backup_manager.py     # Gestionnaire central des backups
│   ├── backup_scheduler.py   # Planificateur automatique
│   ├── postgresql_backup.py  # Backup PostgreSQL avec pg_dump
│   ├── redis_backup.py       # Backup Redis (RDB/AOF)
│   └── chromadb_backup.py    # Backup ChromaDB et données vectorielles
├── migrations/          # Migrations Alembic
│   ├── alembic.ini          # Configuration Alembic
│   ├── env.py              # Environnement de migration
│   └── versions/           # Scripts de migration
├── models/             # Modèles SQLAlchemy
│   ├── conversation.py     # Conversations et messages
│   ├── memory.py          # Entrées mémoire et embeddings
│   ├── metrics.py         # Métriques de performance
│   └── user.py            # Utilisateurs et sessions
├── retention/          # Gestion de la rétention des données
│   ├── retention_manager.py  # Gestionnaire de rétention
│   ├── retention_policies.py # Politiques de rétention
│   └── data_archiver.py     # Archivage des données
├── monitoring/         # Monitoring de santé
│   └── health_monitor.py    # Monitoring complet
├── cli/               # Interface en ligne de commande
│   └── jarvis_db_cli.py    # CLI principal
├── scripts/           # Scripts d'administration
│   ├── backup_service.py   # Service de backup en daemon
│   └── init_database.py   # Initialisation de la base
└── tests/             # Tests complets
    └── test_backup_recovery.py
```

## 🚀 Installation et Configuration

### 1. Installation des dépendances

```bash
pip install alembic asyncpg aioredis psutil croniter click
```

### 2. Initialisation de la base de données

```bash
python database/scripts/init_database.py
```

### 3. Configuration

Créez un fichier de configuration JSON ou utilisez les variables d'environnement :

```json
{
  "backup_dir": "./backups",
  "archive_dir": "./archives",
  "database_url": "postgresql://jarvis:password@localhost:5432/jarvis_memory",
  "services": {
    "postgresql": {
      "host": "localhost",
      "port": 5432,
      "database": "jarvis_memory",
      "username": "jarvis",
      "password": "password"
    },
    "redis": {
      "host": "localhost",
      "port": 6379,
      "password": null,
      "db": 0
    },
    "chromadb": {
      "persist_dir": "./memory/chroma"
    }
  }
}
```

## 💾 Système de Backup

### Backup Automatisé

Le système supporte trois types de bases de données :

- **PostgreSQL** : Utilise `pg_dump` pour des backups complets et cohérents
- **Redis** : Supporte les backups RDB (BGSAVE) et AOF
- **ChromaDB** : Archive les données vectorielles et métadonnées

### Utilisation via CLI

```bash
# Backup complet de tous les services
python -m database.cli.jarvis_db_cli backup create --service all --type full

# Backup d'un service spécifique
python -m database.cli.jarvis_db_cli backup create --service postgresql --type full

# Lister les backups disponibles
python -m database.cli.jarvis_db_cli backup list

# Vérifier l'intégrité d'un backup
python -m database.cli.jarvis_db_cli backup verify --service postgresql /path/to/backup.backup.gz

# Restaurer depuis un backup
python -m database.cli.jarvis_db_cli backup restore --service postgresql /path/to/backup.backup.gz
```

### Planification Automatique

```bash
# Voir le statut du planificateur
python -m database.cli.jarvis_db_cli schedule status

# Démarrer le planificateur (daemon)
python -m database.cli.jarvis_db_cli schedule start
```

Configuration par défaut :
- PostgreSQL : Tous les jours à 2h00
- Redis : Tous les jours à 3h00  
- ChromaDB : Tous les jours à 4h00

## 🗃️ Migrations avec Alembic

### Initialisation

```bash
cd /path/to/jarvis-ai
alembic init database/migrations
```

### Créer une migration

```bash
# Migration automatique basée sur les modèles
alembic revision --autogenerate -m "Description des changements"

# Migration manuelle
alembic revision -m "Description des changements"
```

### Appliquer les migrations

```bash
# Appliquer toutes les migrations
alembic upgrade head

# Appliquer jusqu'à une révision spécifique
alembic upgrade <revision_id>

# Revenir à une révision précédente
alembic downgrade <revision_id>
```

### Historique des migrations

```bash
# Voir l'historique
alembic history

# Voir la révision actuelle
alembic current
```

## 🗂️ Politiques de Rétention

### Configuration par défaut

| Catégorie | Archivage | Suppression | Actions |
|-----------|-----------|-------------|---------|
| Conversations | 90 jours | 2 ans | Archive → Suppression |
| Messages | 90 jours | 2 ans | Archive → Suppression |
| Métriques | - | 30 jours | Suppression directe |
| Logs de backup | - | 90 jours | Suppression directe |
| Cache embeddings | - | 7 jours | Suppression directe |
| Sessions | - | 30 jours | Suppression directe |

### Utilisation

```bash
# Aperçu des politiques de rétention
python -m database.cli.jarvis_db_cli retention cleanup --dry-run

# Exécuter le nettoyage
python -m database.cli.jarvis_db_cli retention cleanup

# Nettoyage d'une catégorie spécifique
python -m database.cli.jarvis_db_cli retention cleanup --category conversations

# Statistiques de rétention
python -m database.cli.jarvis_db_cli retention stats
```

## 🏥 Monitoring de Santé

### Contrôles Automatiques

Le système surveille :

- **PostgreSQL** : Connectivité, taille de la base, requêtes lentes, utilisation des connexions
- **Redis** : Connectivité, utilisation mémoire, ratio de cache, clients bloqués
- **ChromaDB** : Taille des données, intégrité des fichiers
- **Système** : CPU, mémoire, espace disque
- **Backups** : Présence de backups récents, intégrité

### Utilisation

```bash
# Vérification complète de santé
python -m database.cli.jarvis_db_cli health check

# Sortie JSON pour intégration
python -m database.cli.jarvis_db_cli health check --json-output
```

### Statuts de Santé

- 🟢 **HEALTHY** : Tout fonctionne normalement
- 🟡 **WARNING** : Problèmes mineurs détectés
- 🔴 **CRITICAL** : Problèmes critiques nécessitant une intervention

## 🤖 Service Automatisé

### Démarrage du service complet

```bash
# Démarrer le service de backup automatisé
python database/scripts/backup_service.py

# Avec fichier de configuration personnalisé
python database/scripts/backup_service.py --config /path/to/config.json

# Vérifier le statut
python database/scripts/backup_service.py --status

# Test de backup
python database/scripts/backup_service.py --test-backup

# Vérification de santé
python database/scripts/backup_service.py --health-check
```

Le service automatisé inclut :
- Planification des backups selon la configuration
- Nettoyage automatique des rétentions
- Monitoring continu de la santé
- Logging complet des opérations

## 🧪 Tests

### Exécution des tests

```bash
# Tests unitaires
pytest database/tests/test_backup_recovery.py -v

# Tests d'intégration (nécessitent des bases de données)
pytest database/tests/test_backup_recovery.py -v -m integration

# Tous les tests
pytest database/tests/ -v
```

### Types de tests

- **Tests unitaires** : Vérification des fonctionnalités de base
- **Tests d'intégration** : Tests avec vraies bases de données
- **Tests de récupération** : Scénarios de disaster recovery
- **Tests de performance** : Benchmarks des opérations

## 📊 Métriques et Dashboards

### Métriques collectées

- Taille des backups et temps d'exécution
- Performances des requêtes de base
- Utilisation des ressources système
- Statistiques de rétention des données
- Alertes et incidents

### Intégration Prometheus

Les métriques sont exposées pour Prometheus via les endpoints de monitoring existants dans JARVIS.

## 🔧 Administration Avancée

### Commandes utiles

```bash
# Configuration du CLI
python -m database.cli.jarvis_db_cli config show
python -m database.cli.jarvis_db_cli config set --backup-dir /new/backup/path

# Test de connectivité
python -c "
import asyncio
from database.monitoring.health_monitor import HealthMonitor
asyncio.run(HealthMonitor({}).run_full_health_check())
"

# Backup d'urgence
python -c "
import asyncio
from database.backup.backup_manager import BackupManager
from pathlib import Path
asyncio.run(
    BackupManager(Path('./emergency_backup'), {})
    .create_full_backup({'emergency': True})
)
"
```

### Disaster Recovery

1. **Sauvegarde préventive** :
   ```bash
   python -m database.cli.jarvis_db_cli backup create --service all --type full
   ```

2. **Restauration complète** :
   ```bash
   # Arrêter JARVIS
   docker-compose down
   
   # Restaurer PostgreSQL
   python -m database.cli.jarvis_db_cli backup restore --service postgresql /path/to/backup
   
   # Restaurer Redis
   python -m database.cli.jarvis_db_cli backup restore --service redis /path/to/backup
   
   # Restaurer ChromaDB
   python -m database.cli.jarvis_db_cli backup restore --service chromadb /path/to/backup
   
   # Redémarrer JARVIS
   docker-compose up -d
   ```

3. **Vérification post-restauration** :
   ```bash
   python -m database.cli.jarvis_db_cli health check
   ```

## 🔐 Sécurité

### Bonnes pratiques

- Les backups sont chiffrés avec compression gzip
- Authentification requise pour tous les accès base
- Rotation automatique des anciens backups
- Logs d'audit de toutes les opérations
- Vérification d'intégrité avec checksums SHA-256

### Variables d'environnement sensibles

```bash
export POSTGRES_PASSWORD="secure_password"
export REDIS_PASSWORD="secure_redis_password"
export JWT_SECRET_KEY="secure_jwt_key"
```

## 📈 Performance et Optimisation

### Optimisations PostgreSQL

- Index automatiques sur les colonnes fréquemment utilisées
- Configuration optimisée pour les workloads JARVIS
- Monitoring des requêtes lentes
- Analyse automatique des statistiques

### Optimisations Redis

- Politique d'éviction configurée (allkeys-lru)
- Persistance AOF et RDB selon les besoins
- Monitoring de l'utilisation mémoire
- Nettoyage automatique des clés expirées

### Optimisations ChromaDB

- Compression des données vectorielles
- Index HNSW pour les recherches sémantiques
- Nettoyage automatique des embeddings inutilisés
- Archivage des anciennes données

## 🆘 Dépannage

### Problèmes courants

1. **Backup qui échoue** :
   - Vérifier les permissions sur les répertoires
   - Contrôler l'espace disque disponible
   - Valider la connectivité aux bases de données

2. **Migration qui échoue** :
   - Vérifier la syntaxe SQL dans les migrations
   - Contrôler les dépendances entre migrations
   - Sauvegarder avant d'appliquer des migrations

3. **Rétention qui ne fonctionne pas** :
   - Vérifier les politiques de rétention
   - Contrôler les permissions sur la base
   - Valider les expressions de condition SQL

### Logs et débogage

```bash
# Logs du service de backup
tail -f logs/backup_service.log

# Logs détaillés avec niveau DEBUG
export LOG_LEVEL=DEBUG
python database/scripts/backup_service.py
```

## 🤝 Contribution

Pour contribuer au système de gestion de base de données :

1. Suivre les conventions de code existantes
2. Ajouter des tests pour toute nouvelle fonctionnalité
3. Documenter les changements dans ce README
4. Tester avec des données réelles avant PR

## 📄 Licence

Ce système fait partie de JARVIS AI et suit la même licence que le projet principal.

---

**🤖 Système développé pour JARVIS AI - Votre assistant intelligent nouvelle génération**