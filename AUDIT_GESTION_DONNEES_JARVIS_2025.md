# 🔍 AUDIT COMPLET - GESTION DES DONNÉES JARVIS AI 2025

**Date d'audit :** 1er août 2025  
**Version système :** JARVIS AI 2025  
**Auditeur :** Expert Database Architect  
**Localisation :** G:\test\Jarvis-ai

---

## 📋 RÉSUMÉ EXÉCUTIF

### État Global : ⚠️ **MODÉRÉ - AMÉLIORATIONS NÉCESSAIRES**

L'audit révèle une architecture de données moderne avec plusieurs bases de données (PostgreSQL, Redis, ChromaDB), mais identifie des **lacunes critiques** dans la gestion automatique des sauvegardes, migrations, et politiques de rétention pour un environnement de production.

### Recommandations Prioritaires
1. **Mise en place immédiate** d'un système de backup automatisé PostgreSQL
2. **Implémentation** d'un système de migration de schéma (Alembic/Flyway)
3. **Configuration** de politiques de rétention automatisées
4. **Renforcement** des contraintes d'intégrité des données

---

## 🗄️ 1. BACKUP AUTOMATISÉ

### ❌ État Actuel : INSUFFISANT

#### Systèmes Identifiés
- **PostgreSQL (pgvector)** : Service `memory-db` configuré
- **Redis** : Service configuré avec persistance AOF
- **ChromaDB** : Stockage local dans `/memory`
- **Données applicatives** : Stockage dans volumes Docker

#### Problèmes Identifiés
- ❌ **Aucun script pg_dump automatisé** pour PostgreSQL
- ❌ **Pas de sauvegarde planifiée** des volumes Docker
- ❌ **Pas de rotation automatique** des backups
- ❌ **Pas de vérification d'intégrité** des sauvegardes
- ⚠️ Seule sauvegarde existante : variables d'environnement (generate-secrets.sh)

#### Configuration Actuelle
```yaml
# PostgreSQL Service
memory-db:
  image: pgvector/pgvector:pg16
  volumes:
    - memory_data:/var/lib/postgresql/data
    - ./services/memory-db/init:/docker-entrypoint-initdb.d
```

### ✅ Recommandations BACKUP

#### 1. Système de Backup PostgreSQL
```bash
#!/bin/bash
# scripts/backup-postgres.sh
BACKUP_DIR="./backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup complet
pg_dump -h localhost -U jarvis -d jarvis_memory \
  --verbose --no-password \
  --file="$BACKUP_DIR/jarvis_backup_$DATE.sql"

# Backup avec compression
pg_dump -h localhost -U jarvis -d jarvis_memory \
  --verbose --no-password --format=custom \
  --file="$BACKUP_DIR/jarvis_backup_$DATE.backup"

# Rotation des backups (garder 30 jours)
find $BACKUP_DIR -name "jarvis_backup_*.sql" -mtime +30 -delete
```

#### 2. Planification Cron
```bash
# Sauvegarde quotidienne à 2h du matin
0 2 * * * /app/scripts/backup-postgres.sh >> /var/log/jarvis-backup.log 2>&1

# Sauvegarde hebdomadaire complète le dimanche
0 1 * * 0 /app/scripts/full-backup.sh >> /var/log/jarvis-backup.log 2>&1
```

#### 3. Script de Sauvegarde Complète
```bash
#!/bin/bash
# scripts/full-backup.sh
BACKUP_ROOT="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_ROOT"

# PostgreSQL
pg_dump -h localhost -U jarvis -d jarvis_memory > "$BACKUP_ROOT/postgres.sql"

# Redis
redis-cli --rdb "$BACKUP_ROOT/redis.rdb"

# ChromaDB et mémoire
cp -r ./memory "$BACKUP_ROOT/"

# Fichiers de configuration
cp .env "$BACKUP_ROOT/"
cp -r ./config "$BACKUP_ROOT/"

# Compression finale
tar -czf "./backups/jarvis_full_$(date +%Y%m%d_%H%M%S).tar.gz" -C ./backups .
```

---

## 🔄 2. MIGRATION SCHEMA

### ❌ État Actuel : ABSENT

#### Analyse
- ❌ **Aucun système de migration** détecté (Alembic, Flyway, ou équivalent)
- ❌ **Pas de versioning** des schémas de base de données
- ❌ **Pas de scripts DDL** organisés
- ⚠️ Seules migrations trouvées : ChromaDB (dans venv/Lib/site-packages)

#### Risques Identifiés
- Impossible de suivre l'évolution du schéma
- Déploiements manuels sujets aux erreurs
- Pas de rollback possible
- Incohérences entre environnements

### ✅ Recommandations MIGRATION

#### 1. Implémentation Alembic (Python)
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from core.database.models import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

#### 2. Structure de Migration
```
migrations/
├── alembic.ini
├── env.py
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_user_preferences.py
    ├── 003_add_conversation_index.py
    └── 004_add_memory_constraints.py
```

#### 3. Exemple de Migration
```python
# migrations/versions/001_initial_schema.py
"""Initial schema for JARVIS memory system

Revision ID: 001
Revises: 
Create Date: 2025-08-01 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None

def upgrade():
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # Conversations table
    op.create_table('conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True)
    )
    
    # Vector embeddings with pgvector
    op.create_table('memory_embeddings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    
    # Indexes for performance
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('idx_memory_embeddings_created_at', 'memory_embeddings', ['created_at'])

def downgrade():
    op.drop_table('memory_embeddings')
    op.drop_table('conversations')
    op.drop_table('users')
```

---

## 🗄️ 3. DATA RETENTION

### ⚠️ État Actuel : PARTIEL

#### Systèmes de Rétention Identifiés

##### ✅ Logs - Configuration Avancée
Dans `config/logging_config.py` :
```python
# Rotation configurée
rotation="10 MB"
retention="30 days"

# Logs spécialisés avec rétention différenciée
api_logs: retention="14 days"
memory_logs: retention="30 days" 
voice_logs: retention="7 days"
performance_logs: retention="14 days"
```

##### ✅ Redis - Configuration Basique
```yaml
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

##### ❌ PostgreSQL - Pas de Politique
- Aucune politique de purge automatique
- Pas de partitioning par date
- Croissance illimitée des données

##### ❌ ChromaDB - Maintenance Manuelle
Dans `core/ai/memory_system.py` :
```python
# TODO: Implémenter le nettoyage basé sur l'âge et l'importance
async def cleanup_old_memories(self, days_old: int = 30):
    logger.info(f"🧹 Nettoyage des mémoires > {days_old} jours")
    # Non implémenté
```

### ✅ Recommandations RETENTION

#### 1. Politique PostgreSQL Automatisée
```sql
-- Table partitionnée par mois pour les conversations
CREATE TABLE conversations_partitioned (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    content TEXT,
    metadata JSONB
) PARTITION BY RANGE (created_at);

-- Créer les partitions mensuelles
CREATE TABLE conversations_2025_08 PARTITION OF conversations_partitioned
FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

-- Procédure de purge automatique
CREATE OR REPLACE FUNCTION cleanup_old_conversations()
RETURNS void AS $$
BEGIN
    DELETE FROM conversations_partitioned 
    WHERE created_at < NOW() - INTERVAL '6 months'
    AND metadata->>'importance' < '0.5';
    
    RAISE NOTICE 'Cleanup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Planifier la purge (avec pg_cron)
SELECT cron.schedule('cleanup-conversations', '0 2 * * 0', 'SELECT cleanup_old_conversations();');
```

#### 2. Système de Rétention ChromaDB
```python
# core/ai/memory_maintenance.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

class MemoryRetentionManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.retention_policies = {
            'conversations': {'days': 180, 'importance_threshold': 0.3},
            'commands': {'days': 90, 'importance_threshold': 0.2},
            'preferences': {'days': 365, 'importance_threshold': 0.0},  # Garder longtemps
            'patterns': {'days': 120, 'importance_threshold': 0.4},
            'knowledge': {'days': 365, 'importance_threshold': 0.5}
        }
    
    async def cleanup_expired_memories(self):
        """Nettoie les mémoires expirées selon les politiques"""
        cleanup_stats = {
            'total_processed': 0,
            'total_deleted': 0,
            'categories': {}
        }
        
        for category, policy in self.retention_policies.items():
            cutoff_date = datetime.now() - timedelta(days=policy['days'])
            importance_threshold = policy['importance_threshold']
            
            # Obtenir les mémoires candidates à la suppression
            candidates = await self._get_cleanup_candidates(
                category, cutoff_date, importance_threshold
            )
            
            deleted_count = 0
            for memory in candidates:
                success = self.memory_system.memory_store.delete_memory(category, memory.id)
                if success:
                    deleted_count += 1
            
            cleanup_stats['categories'][category] = {
                'processed': len(candidates),
                'deleted': deleted_count
            }
            cleanup_stats['total_processed'] += len(candidates)
            cleanup_stats['total_deleted'] += deleted_count
        
        return cleanup_stats
    
    async def _get_cleanup_candidates(self, category: str, cutoff_date: datetime, 
                                    importance_threshold: float) -> List:
        """Obtient les mémoires candidates à la suppression"""
        # Implémentation de la sélection basée sur âge et importance
        pass
```

#### 3. Cron Job de Maintenance
```bash
# scripts/maintenance-cron.sh
#!/bin/bash

# Nettoyage hebdomadaire des logs
0 3 * * 0 find /app/logs -name "*.log.*" -mtime +30 -delete

# Nettoyage mensuel des mémoires ChromaDB
0 2 1 * * python -c "
from core.ai.memory_maintenance import MemoryRetentionManager
from core.ai.memory_system import MemorySystem
import asyncio

async def main():
    memory = MemorySystem()
    await memory.initialize()
    manager = MemoryRetentionManager(memory)
    stats = await manager.cleanup_expired_memories()
    print(f'Cleanup completed: {stats}')

asyncio.run(main())
"

# Vacuum PostgreSQL mensuel
0 1 1 * * docker exec jarvis_memory_db vacuumdb -U jarvis -d jarvis_memory --analyze
```

---

## 🔒 4. INTÉGRITÉ DES DONNÉES

### ⚠️ État Actuel : BASIQUE

#### Contraintes Identifiées

##### ✅ Tests de Sécurité - Complets
Dans `tests/security/test_injection.py` :
- Tests d'injection SQL avec contraintes PRIMARY KEY et FOREIGN KEY
- Validation des inputs utilisateur
- Prévention XSS, Command Injection, LDAP injection

##### ❌ Schémas de Production - Absents
- Pas de contraintes formelles dans les modèles de données
- Validation applicative seulement

##### ⚠️ Validation Partielle
Dans `core/ai/memory_system.py` :
```python
# Validation basique des entrées
if not MEMORY_AVAILABLE:
    return False

# Pas de contraintes de données strictes
```

### ✅ Recommandations INTÉGRITÉ

#### 1. Modèles de Données avec Contraintes
```python
# core/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Contraintes
    __table_args__ = (
        CheckConstraint('length(username) >= 3', name='username_min_length'),
        CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name='valid_email'),
    )

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="conversations")
    
    # Contraintes
    __table_args__ = (
        CheckConstraint('message_count >= 0', name='positive_message_count'),
        CheckConstraint('ended_at IS NULL OR ended_at >= created_at', name='valid_end_time'),
    )

class MemoryEmbedding(Base):
    __tablename__ = 'memory_embeddings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    metadata = Column(JSONB, nullable=True)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, nullable=False)
    
    # Contraintes
    __table_args__ = (
        CheckConstraint('length(content) > 0', name='content_not_empty'),
        CheckConstraint('importance >= 0.0 AND importance <= 1.0', name='valid_importance'),
        CheckConstraint('array_length(embedding, 1) = 384', name='valid_embedding_dimension'),
    )
```

#### 2. Validation des Données Renforcée
```python
# core/validation/validators.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator, Field
import re

class ConversationCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="ID utilisateur valide")
    title: Optional[str] = Field(None, max_length=255, description="Titre de la conversation")
    initial_message: str = Field(..., min_length=1, max_length=10000, description="Message initial")
    
    @validator('title')
    def validate_title(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9\s\-_.]+$', v):
            raise ValueError('Titre contient des caractères non autorisés')
        return v
    
    @validator('initial_message')
    def validate_message(cls, v):
        # Vérification anti-injection
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<.*?>'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contient du contenu potentiellement dangereux')
        
        return v

class MemoryEntryValidator(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    @validator('tags')
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 50 or not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValueError(f'Tag invalide: {tag}')
        return v
```

#### 3. Triggers de Cohérence PostgreSQL
```sql
-- Trigger pour maintenir le compteur de messages
CREATE OR REPLACE FUNCTION update_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations 
        SET message_count = message_count + 1 
        WHERE id = NEW.conversation_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations 
        SET message_count = GREATEST(message_count - 1, 0) 
        WHERE id = OLD.conversation_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER message_count_trigger
    AFTER INSERT OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_message_count();

-- Trigger pour audit trail
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    user_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION audit_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, user_id, old_values, new_values)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.user_id, OLD.user_id),
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW) ELSE NULL END
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Appliquer l'audit aux tables critiques
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_changes();
    
CREATE TRIGGER audit_conversations AFTER INSERT OR UPDATE OR DELETE ON conversations
    FOR EACH ROW EXECUTE FUNCTION audit_changes();
```

---

## 📊 5. SCRIPTS D'AMÉLIORATION

### Script 1: Initialisation Complète du Système de Backup

```bash
#!/bin/bash
# scripts/setup-backup-system.sh

set -e

BACKUP_ROOT="./backups"
SCRIPTS_DIR="./scripts"

echo "🚀 Initialisation du système de backup JARVIS..."

# Créer la structure de répertoires
mkdir -p "$BACKUP_ROOT"/{postgres,redis,chromadb,full,logs}
mkdir -p "$SCRIPTS_DIR"/maintenance

# Script de backup PostgreSQL
cat > "$SCRIPTS_DIR/backup-postgres.sh" << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="./backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
POSTGRES_CONTAINER="jarvis_memory_db"

echo "📄 Backup PostgreSQL - $DATE"

# Backup SQL avec schéma et données
docker exec $POSTGRES_CONTAINER pg_dump -U jarvis -d jarvis_memory \
  --verbose --clean --if-exists \
  > "$BACKUP_DIR/jarvis_schema_data_$DATE.sql"

# Backup custom format (pour restauration sélective)
docker exec $POSTGRES_CONTAINER pg_dump -U jarvis -d jarvis_memory \
  --verbose --format=custom \
  > "$BACKUP_DIR/jarvis_custom_$DATE.backup"

# Backup données seulement
docker exec $POSTGRES_CONTAINER pg_dump -U jarvis -d jarvis_memory \
  --verbose --data-only \
  > "$BACKUP_DIR/jarvis_data_only_$DATE.sql"

# Compression et rotation
gzip "$BACKUP_DIR/jarvis_schema_data_$DATE.sql"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.backup" -mtime +7 -delete

echo "✅ Backup PostgreSQL terminé"
EOF

# Script de backup complet
cat > "$SCRIPTS_DIR/full-backup.sh" << 'EOF'
#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/full/jarvis_full_$TIMESTAMP"

echo "🔄 Backup complet JARVIS - $TIMESTAMP"

mkdir -p "$BACKUP_DIR"

# PostgreSQL
echo "📄 Backup PostgreSQL..."
docker exec jarvis_memory_db pg_dump -U jarvis -d jarvis_memory \
  > "$BACKUP_DIR/postgres.sql"

# Redis
echo "🔑 Backup Redis..."
docker exec jarvis_redis redis-cli BGSAVE
sleep 5
docker cp jarvis_redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# ChromaDB et mémoire
echo "🧠 Backup ChromaDB..."
if [ -d "./memory" ]; then
    cp -r ./memory "$BACKUP_DIR/"
fi

# Configuration et secrets
echo "⚙️ Backup configuration..."
cp .env "$BACKUP_DIR/" 2>/dev/null || echo "Fichier .env non trouvé"
cp -r ./config "$BACKUP_DIR/" 2>/dev/null || echo "Dossier config non trouvé"

# Logs récents (7 derniers jours)
echo "📋 Backup logs récents..."
mkdir -p "$BACKUP_DIR/logs"
find ./logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null || true

# Compression finale
echo "🗜️ Compression..."
cd ./backups/full
tar -czf "jarvis_full_$TIMESTAMP.tar.gz" "jarvis_full_$TIMESTAMP"
rm -rf "jarvis_full_$TIMESTAMP"

# Rotation des backups complets (garder 4 semaines)
find . -name "jarvis_full_*.tar.gz" -mtime +28 -delete

echo "✅ Backup complet terminé: jarvis_full_$TIMESTAMP.tar.gz"
EOF

# Script de restauration
cat > "$SCRIPTS_DIR/restore-postgres.sh" << 'EOF'
#!/bin/bash
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Exemple: $0 ./backups/postgres/jarvis_custom_20250801_120000.backup"
    exit 1
fi

BACKUP_FILE="$1"
POSTGRES_CONTAINER="jarvis_memory_db"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Fichier backup non trouvé: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  ATTENTION: Cette opération va écraser la base de données existante!"
read -p "Continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Copier le fichier dans le container
docker cp "$BACKUP_FILE" "$POSTGRES_CONTAINER:/tmp/restore.backup"

# Restauration
if [[ "$BACKUP_FILE" == *.backup ]]; then
    # Format custom
    docker exec $POSTGRES_CONTAINER pg_restore -U jarvis -d jarvis_memory \
      --verbose --clean --if-exists /tmp/restore.backup
elif [[ "$BACKUP_FILE" == *.sql* ]]; then
    # Format SQL
    docker exec -i $POSTGRES_CONTAINER psql -U jarvis -d jarvis_memory < "$BACKUP_FILE"
fi

echo "✅ Restauration terminée"
EOF

# Rendre les scripts exécutables
chmod +x "$SCRIPTS_DIR"/*.sh

# Configuration cron
cat > "$SCRIPTS_DIR/maintenance-cron" << 'EOF'
# JARVIS AI - Maintenance automatique
# Backup PostgreSQL quotidien à 2h
0 2 * * * /app/scripts/backup-postgres.sh >> /var/log/jarvis-backup.log 2>&1

# Backup complet hebdomadaire le dimanche à 1h
0 1 * * 0 /app/scripts/full-backup.sh >> /var/log/jarvis-backup.log 2>&1

# Nettoyage des logs anciens tous les dimanches à 3h
0 3 * * 0 find /app/logs -name "*.log.*" -mtime +30 -delete

# Vérification de l'espace disque tous les jours à 23h
0 23 * * * df -h | grep -E "(8[0-9]|9[0-9])%" && echo "⚠️ Espace disque faible" | mail -s "JARVIS: Espace disque" admin@example.com
EOF

echo "✅ Système de backup initialisé"
echo "📋 Pour activer le cron: crontab scripts/maintenance-cron"
echo "🔧 Pour tester: ./scripts/backup-postgres.sh"
```

### Script 2: Initialisation des Migrations

```bash
#!/bin/bash
# scripts/setup-migrations.sh

set -e

echo "🔄 Initialisation du système de migrations JARVIS..."

# Installer Alembic si nécessaire
pip install alembic psycopg2-binary

# Initialiser Alembic
alembic init migrations

# Configuration personnalisée
cat > alembic.ini << 'EOF'
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://jarvis:%(POSTGRES_PASSWORD)s@localhost:5432/jarvis_memory

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# Créer le modèle de base
mkdir -p core/database
cat > core/database/models.py << 'EOF'
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="conversations")
    memory_entries = relationship("MemoryEntry", back_populates="conversation")

class MemoryEntry(Base):
    __tablename__ = 'memory_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    metadata = Column(JSONB, nullable=True)
    importance = Column(Float, default=0.5)
    memory_type = Column(String(50), default='episodic')  # static, dynamic, episodic
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="memory_entries")
EOF

# Première migration
cat > migrations/versions/001_initial_schema.py << 'EOF'
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-08-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    
    # Conversations table
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Memory entries table
    op.create_table('memory_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('importance', sa.Float(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('idx_memory_entries_conversation_id', 'memory_entries', ['conversation_id'])
    op.create_index('idx_memory_entries_created_at', 'memory_entries', ['created_at'])
    op.create_index('idx_memory_entries_type', 'memory_entries', ['memory_type'])

def downgrade():
    op.drop_index('idx_memory_entries_type', table_name='memory_entries')
    op.drop_index('idx_memory_entries_created_at', table_name='memory_entries')
    op.drop_index('idx_memory_entries_conversation_id', table_name='memory_entries')
    op.drop_index('idx_conversations_created_at', table_name='conversations')
    op.drop_index('idx_conversations_user_id', table_name='conversations')
    op.drop_table('memory_entries')
    op.drop_table('conversations')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')
EOF

echo "✅ Système de migrations initialisé"
echo "🔧 Pour créer une migration: alembic revision --autogenerate -m 'Description'"
echo "🚀 Pour appliquer: alembic upgrade head"
```

### Script 3: Monitoring et Alertes

```bash
#!/bin/bash
# scripts/setup-monitoring.sh

set -e

echo "📊 Configuration du monitoring JARVIS..."

# Script de monitoring des bases de données
cat > scripts/monitor-databases.sh << 'EOF'
#!/bin/bash

ALERT_EMAIL="admin@example.com"
ALERT_THRESHOLD_DISK=80
ALERT_THRESHOLD_MEMORY=85

echo "📊 Monitoring JARVIS - $(date)"

# Fonction d'alerte
send_alert() {
    local subject="$1"
    local message="$2"
    echo "🚨 ALERTE: $subject"
    echo "$message"
    # echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
}

# Vérification PostgreSQL
check_postgres() {
    local container="jarvis_memory_db"
    
    if ! docker exec $container pg_isready -U jarvis -d jarvis_memory >/dev/null 2>&1; then
        send_alert "PostgreSQL Down" "La base de données PostgreSQL JARVIS ne répond pas"
        return 1
    fi
    
    # Taille de la base
    local db_size=$(docker exec $container psql -U jarvis -d jarvis_memory -t -c "SELECT pg_size_pretty(pg_database_size('jarvis_memory'));" | xargs)
    echo "📄 PostgreSQL: $db_size"
    
    # Nombre de connexions
    local connections=$(docker exec $container psql -U jarvis -d jarvis_memory -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='jarvis_memory';" | xargs)
    echo "🔗 Connexions actives: $connections"
    
    # Tables les plus volumineuses
    echo "📊 Tables principales:"
    docker exec $container psql -U jarvis -d jarvis_memory -c "
        SELECT schemaname, tablename, 
               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
               pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 5;
    "
}

# Vérification Redis
check_redis() {
    local container="jarvis_redis"
    
    if ! docker exec $container redis-cli ping >/dev/null 2>&1; then
        send_alert "Redis Down" "Le cache Redis JARVIS ne répond pas"
        return 1
    fi
    
    # Informations mémoire
    local memory_used=$(docker exec $container redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    local memory_peak=$(docker exec $container redis-cli info memory | grep used_memory_peak_human | cut -d: -f2 | tr -d '\r')
    echo "🔑 Redis mémoire: $memory_used (pic: $memory_peak)"
    
    # Nombre de clés
    local keys=$(docker exec $container redis-cli dbsize)
    echo "🗝️  Nombre de clés: $keys"
}

# Vérification de l'espace disque
check_disk_space() {
    local usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    echo "💾 Espace disque utilisé: ${usage}%"
    
    if [ "$usage" -gt "$ALERT_THRESHOLD_DISK" ]; then
        send_alert "Espace disque faible" "Utilisation du disque: ${usage}% (seuil: ${ALERT_THRESHOLD_DISK}%)"
    fi
}

# Vérification des logs
check_logs() {
    local log_dir="./logs"
    
    if [ -d "$log_dir" ]; then
        local log_size=$(du -sh "$log_dir" | cut -f1)
        echo "📋 Taille des logs: $log_size"
        
        # Recherche d'erreurs récentes
        local errors=$(find "$log_dir" -name "*.log" -mtime -1 -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | wc -l)
        if [ "$errors" -gt 0 ]; then
            echo "⚠️  Erreurs détectées dans $errors fichiers de log (dernières 24h)"
        fi
    fi
}

# Vérification des containers Docker
check_containers() {
    echo "🐳 État des containers:"
    
    local containers=("jarvis_memory_db" "jarvis_redis" "jarvis_brain" "jarvis_ollama")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container"; then
            local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2" "$3}')
            echo "  ✅ $container: $status"
        else
            echo "  ❌ $container: DOWN"
            send_alert "Container Down" "Le container $container n'est pas en cours d'exécution"
        fi
    done
}

# Exécution des vérifications
echo "=================================="
check_postgres
echo "----------------------------------"
check_redis
echo "----------------------------------"
check_disk_space
echo "----------------------------------"
check_logs
echo "----------------------------------"
check_containers
echo "=================================="

echo "✅ Monitoring terminé - $(date)"
EOF

# Script de nettoyage intelligent
cat > scripts/intelligent-cleanup.sh << 'EOF'
#!/bin/bash

set -e

echo "🧹 Nettoyage intelligent JARVIS - $(date)"

# Nettoyage des logs avec préservation des erreurs
cleanup_logs() {
    local log_dir="./logs"
    
    if [ ! -d "$log_dir" ]; then
        return 0
    fi
    
    echo "📋 Nettoyage des logs..."
    
    # Archiver les logs avec erreurs avant nettoyage
    find "$log_dir" -name "*.log" -mtime +7 -exec grep -l "ERROR\|CRITICAL" {} \; | while read -r logfile; do
        local basename=$(basename "$logfile")
        local archive_name="errors_${basename}_$(date +%Y%m%d).gz"
        gzip -c "$logfile" > "./backups/logs/$archive_name"
        echo "  📦 Archivé: $archive_name"
    done
    
    # Supprimer les anciens logs
    local deleted=$(find "$log_dir" -name "*.log.*" -mtime +30 -delete -print | wc -l)
    echo "  🗑️  Supprimés: $deleted fichiers de logs anciens"
}

# Nettoyage de la base PostgreSQL
cleanup_postgres() {
    echo "📄 Maintenance PostgreSQL..."
    
    # Statistiques avant
    local size_before=$(docker exec jarvis_memory_db psql -U jarvis -d jarvis_memory -t -c "SELECT pg_size_pretty(pg_database_size('jarvis_memory'));" | xargs)
    echo "  📊 Taille avant: $size_before"
    
    # Vacuum et analyze
    docker exec jarvis_memory_db vacuumdb -U jarvis -d jarvis_memory --analyze --verbose
    
    # Statistiques après
    local size_after=$(docker exec jarvis_memory_db psql -U jarvis -d jarvis_memory -t -c "SELECT pg_size_pretty(pg_database_size('jarvis_memory'));" | xargs)
    echo "  📊 Taille après: $size_after"
}

# Nettoyage Redis
cleanup_redis() {
    echo "🔑 Nettoyage Redis..."
    
    # Informations avant
    local keys_before=$(docker exec jarvis_redis redis-cli dbsize)
    local memory_before=$(docker exec jarvis_redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    
    echo "  📊 Avant: $keys_before clés, $memory_before"
    
    # Expiration des clés temporaires
    docker exec jarvis_redis redis-cli --scan --pattern "temp:*" | xargs -I {} docker exec jarvis_redis redis-cli expire {} 3600
    
    # Informations après
    local keys_after=$(docker exec jarvis_redis redis-cli dbsize)
    local memory_after=$(docker exec jarvis_redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    
    echo "  📊 Après: $keys_after clés, $memory_after"
}

# Nettoyage ChromaDB (si présent)
cleanup_chromadb() {
    if [ -d "./memory" ]; then
        echo "🧠 Vérification ChromaDB..."
        
        local size=$(du -sh ./memory | cut -f1)
        echo "  📊 Taille actuelle: $size"
        
        # Ici on pourrait implémenter un nettoyage intelligent basé sur l'importance
        # Pour l'instant, juste un rapport
        local file_count=$(find ./memory -type f | wc -l)
        echo "  📁 Fichiers: $file_count"
    fi
}

# Nettoyage des backups anciens
cleanup_backups() {
    echo "💾 Nettoyage des backups anciens..."
    
    # Garder 7 backups quotidiens
    find ./backups/postgres -name "jarvis_custom_*.backup" -mtime +7 -delete
    
    # Garder 4 backups complets
    ls -t ./backups/full/jarvis_full_*.tar.gz 2>/dev/null | tail -n +5 | xargs -r rm
    
    local backup_size=$(du -sh ./backups 2>/dev/null | cut -f1 || echo "0")
    echo "  📦 Taille totale des backups: $backup_size"
}

# Rapport d'espace libéré
report_cleanup() {
    echo "📊 Rapport de nettoyage:"
    echo "  🗑️  Logs anciens nettoyés"
    echo "  📄 PostgreSQL optimisé"
    echo "  🔑 Redis nettoyé"
    echo "  💾 Backups anciens supprimés"
    
    local total_size=$(du -sh . | cut -f1)
    echo "  📁 Taille totale du projet: $total_size"
}

# Exécution du nettoyage
mkdir -p ./backups/logs

cleanup_logs
cleanup_postgres
cleanup_redis
cleanup_chromadb
cleanup_backups
report_cleanup

echo "✅ Nettoyage terminé - $(date)"
EOF

# Rendre les scripts exécutables
chmod +x scripts/monitor-databases.sh
chmod +x scripts/intelligent-cleanup.sh

# Configuration de monitoring continu
cat > scripts/monitoring-cron << 'EOF'
# JARVIS AI - Monitoring automatique
# Vérification toutes les heures
0 * * * * /app/scripts/monitor-databases.sh >> /var/log/jarvis-monitor.log 2>&1

# Nettoyage intelligent tous les dimanches à 4h
0 4 * * 0 /app/scripts/intelligent-cleanup.sh >> /var/log/jarvis-cleanup.log 2>&1

# Alerte espace disque toutes les 6h
0 */6 * * * df -h | awk '$5 ~ /^[8-9][0-9]%/ || $5 ~ /^100%/ {print "⚠️ Disque plein: "$5" sur "$1}' | head -1 | grep -q "%" && echo "Espace disque critique" | mail -s "JARVIS: Alerte disque" admin@example.com
EOF

echo "✅ Monitoring configuré"
echo "📋 Pour activer: crontab scripts/monitoring-cron"
echo "🔧 Pour tester: ./scripts/monitor-databases.sh"
```

---

## 🎯 PLAN D'IMPLÉMENTATION PRIORITAIRE

### Phase 1 - URGENT (1-2 semaines)
1. ✅ **Backup PostgreSQL automatisé**
   - Exécuter `scripts/setup-backup-system.sh`
   - Configurer cron pour backups quotidiens
   - Tester la restauration

2. ✅ **Système de migrations**
   - Exécuter `scripts/setup-migrations.sh`
   - Créer le schéma initial
   - Documenter le processus

### Phase 2 - IMPORTANT (2-4 semaines)
3. ✅ **Politique de rétention automatisée**
   - Implémenter le nettoyage PostgreSQL
   - Configurer la purge ChromaDB
   - Tester les triggers de maintenance

4. ✅ **Contraintes d'intégrité**
   - Ajouter les modèles SQLAlchemy
   - Implémenter la validation Pydantic
   - Créer les triggers PostgreSQL

### Phase 3 - AMÉLIORATION (1-2 mois)
5. ✅ **Monitoring et alertes**
   - Exécuter `scripts/setup-monitoring.sh`
   - Configurer les seuils d'alerte
   - Intégrer avec Grafana/Prometheus

6. ✅ **Tests et documentation**
   - Tests de backup/restore
   - Documentation opérationnelle
   - Procédures de récupération d'urgence

---

## 📊 MÉTRIQUES DE SUCCÈS

### Indicateurs de Performance
- **RTO (Recovery Time Objective)** : < 1 heure
- **RPO (Recovery Point Objective)** : < 24 heures
- **Disponibilité des données** : 99.9%
- **Temps de récupération backup** : < 30 minutes

### Indicateurs de Qualité
- **Intégrité des données** : 100% (contraintes respectées)
- **Conformité migrations** : Toutes les migrations versionnées
- **Couverture backup** : 100% des données critiques
- **Rotation des logs** : Automatique selon politique

---

## ⚠️ RISQUES ET MITIGATION

### Risques Identifiés
1. **Perte de données** → Backup automatisé + tests réguliers
2. **Corruption de base** → Contraintes + validation + monitoring
3. **Espace disque insuffisant** → Alertes + nettoyage automatique
4. **Dérive de schéma** → Migrations versionnées + validation
5. **Performance dégradée** → Monitoring + maintenance préventive

### Actions Préventives
- Tests de restauration mensuels
- Monitoring proactif 24/7
- Documentation à jour
- Formation équipe technique
- Plan de récupération d'urgence

---

## 📝 CONCLUSION

L'architecture de données JARVIS AI 2025 présente une base solide avec des technologies modernes (PostgreSQL + pgvector, Redis, ChromaDB), mais nécessite des **améliorations critiques** pour un environnement de production robuste.

### Points Forts
- ✅ Architecture microservices bien structurée
- ✅ Utilisation de technologies adaptées à l'IA
- ✅ Système de logs avancé et configurable
- ✅ Tests de sécurité complets contre les injections
- ✅ Configuration Docker professionnelle

### Points d'Amélioration Critique
- ❌ Système de backup automatisé manquant
- ❌ Gestion des migrations de schéma absente
- ❌ Politiques de rétention partielles
- ❌ Contraintes d'intégrité insuffisantes

### Recommandation Finale
**Implémenter immédiatement les scripts fournis** avant tout déploiement en production. L'investissement de 3-4 semaines pour ces améliorations préviendra des risques de perte de données potentiellement catastrophiques.

---

**Rapport généré le :** 1er août 2025  
**Validité :** 6 mois (révision recommandée février 2026)  
**Prochaine révision :** Après implémentation Phase 1 + 2