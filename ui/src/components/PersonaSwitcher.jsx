/**
 * 🎭 PersonaSwitcher - Composant de changement de persona JARVIS
 * Permet de switcher entre les différentes personnalités IA (JARVIS, FRIDAY, EDITH)
 */
import React, { useState, useEffect } from 'react';
import '../styles/persona-switcher.css';

const PersonaSwitcher = ({ 
  onPersonaChange, 
  apiUrl = 'http://localhost:8001/api/persona',
  className = '',
  showDetails = false 
}) => {
  const [personas, setPersonas] = useState({});
  const [currentPersona, setCurrentPersona] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Charger les personas disponibles au montage
  useEffect(() => {
    loadPersonas();
  }, []);

  const loadPersonas = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/`);
      
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setPersonas(data);

      // Trouver la persona active
      const activePersona = Object.keys(data).find(name => data[name].is_active);
      if (activePersona) {
        setCurrentPersona(activePersona);
      }

    } catch (err) {
      console.error('Erreur chargement personas:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchPersona = async (personaName) => {
    if (personaName === currentPersona || loading) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/switch/${personaName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason: 'user_interface_selection',
          user_id: 'ui_user',
          context: {
            interface_type: 'react_component',
            timestamp: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setCurrentPersona(result.current_persona);
        
        // Notifier le parent du changement
        if (onPersonaChange) {
          onPersonaChange({
            previous: result.previous_persona,
            current: result.current_persona,
            persona: personas[result.current_persona]
          });
        }

        // Recharger les données pour mettre à jour les statistiques
        await loadPersonas();
      } else {
        throw new Error('Échec du changement de persona');
      }

    } catch (err) {
      console.error('Erreur changement persona:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPersonaIcon = (personaName) => {
    const icons = {
      'jarvis_classic': '🎩',
      'friday': '🌟', 
      'edith': '🔒'
    };
    return icons[personaName] || '🤖';
  };

  const getPersonaColor = (personaName) => {
    const colors = {
      'jarvis_classic': 'var(--jarvis-primary)',
      'friday': 'var(--jarvis-secondary)',
      'edith': 'var(--jarvis-warning)'
    };
    return colors[personaName] || 'var(--jarvis-primary)';
  };

  const formatPersonalityTrait = (trait, value) => {
    const traitNames = {
      formality: 'Formalité',
      humor: 'Humour', 
      proactivity: 'Proactivité',
      verbosity: 'Verbosité',
      empathy: 'Empathie',
      confidence: 'Confiance'
    };
    
    const percentage = Math.round(value * 100);
    return {
      name: traitNames[trait] || trait,
      value: percentage,
      level: percentage >= 80 ? 'high' : percentage >= 50 ? 'medium' : 'low'
    };
  };

  if (loading && Object.keys(personas).length === 0) {
    return (
      <div className={`persona-switcher loading ${className}`}>
        <div className="persona-loading">
          <span className="jarvis-loading"></span>
          <span className="jarvis-text-glow">Loading personas...</span>
        </div>
      </div>
    );
  }

  if (error && Object.keys(personas).length === 0) {
    return (
      <div className={`persona-switcher error ${className}`}>
        <div className="persona-error">
          <span>⚠️ Erreur: {error}</span>
          <button onClick={loadPersonas} className="retry-button">
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`persona-switcher ${className} ${isExpanded ? 'expanded' : ''}`}>
      {/* Header avec persona actuel */}
      <div className="persona-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="current-persona">
          <span className="persona-icon">
            {getPersonaIcon(currentPersona)}
          </span>
          <div className="persona-info">
            <span className="persona-name jarvis-text-glow">
              {currentPersona ? personas[currentPersona]?.name : 'Chargement...'}
            </span>
            {currentPersona && personas[currentPersona] && (
              <span className="persona-style">
                {personas[currentPersona].response_style}
              </span>
            )}
          </div>
        </div>
        <button 
          className={`expand-button ${isExpanded ? 'expanded' : ''}`}
          disabled={loading}
        >
          ▼
        </button>
      </div>

      {/* Liste des personas */}
      {isExpanded && (
        <div className="personas-list">
          {Object.entries(personas).map(([name, persona]) => (
            <div 
              key={name}
              className={`persona-option ${name === currentPersona ? 'active' : ''} ${loading ? 'disabled' : ''}`}
              onClick={() => switchPersona(name)}
              style={{ '--persona-color': getPersonaColor(name) }}
            >
              <div className="persona-option-header">
                <span className="persona-icon">{getPersonaIcon(name)}</span>
                <div className="persona-details">
                  <span className="persona-name jarvis-text-glow">
                    {persona.name}
                  </span>
                  <span className="persona-description">
                    {persona.description}
                  </span>
                </div>
                {name === currentPersona && (
                  <span className="active-indicator">✓</span>
                )}
              </div>

              {showDetails && (
                <div className="persona-traits">
                  {Object.entries(persona.personality).map(([trait, value]) => {
                    const formatted = formatPersonalityTrait(trait, value);
                    return (
                      <div key={trait} className="trait">
                        <span className="trait-name">{formatted.name}</span>
                        <div className="trait-bar">
                          <div 
                            className={`trait-fill ${formatted.level}`}
                            style={{ width: `${formatted.value}%` }}
                          ></div>
                        </div>
                        <span className="trait-value">{formatted.value}%</span>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="persona-stats">
                <span className="stat">
                  <span className="stat-label">Utilisations:</span>
                  <span className="stat-value">{persona.usage_count}</span>
                </span>
                {persona.last_used && (
                  <span className="stat">
                    <span className="stat-label">Dernière:</span>
                    <span className="stat-value">
                      {new Date(persona.last_used).toLocaleDateString()}
                    </span>
                  </span>
                )}
              </div>

              {/* Phrase d'exemple */}
              <div className="sample-phrase">
                <em>"{persona.sample_phrases?.greeting || 'Prêt à vous assister'}"</em>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Indicateur de chargement */}
      {loading && (
        <div className="loading-overlay">
          <span className="jarvis-loading"></span>
        </div>
      )}

      {/* Message d'erreur */}
      {error && (
        <div className="persona-error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="dismiss-error">
            ×
          </button>
        </div>
      )}

      {/* Actions rapides */}
      <div className="persona-actions">
        <button 
          onClick={loadPersonas}
          className="action-button refresh"
          disabled={loading}
          title="Actualiser"
        >
          🔄
        </button>
        <button 
          onClick={() => setShowDetails && setShowDetails(!showDetails)}
          className="action-button details"
          title="Basculer détails"
        >
          📊
        </button>
      </div>
    </div>
  );
};

export default PersonaSwitcher;