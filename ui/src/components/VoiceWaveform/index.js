/**
 * 🎵 Voice Waveform Components Export
 * Point d'entrée centralisé pour tous les composants de visualisation audio
 */

// Composants principaux
export { default as VoiceWaveform } from '../VoiceWaveform';
export { default as VoiceWaveformAdvanced } from '../VoiceWaveformAdvanced';

// Composants d'exemple et de démonstration
export { default as VoiceWaveformExample } from '../VoiceWaveformExample';
export { default as VoiceWaveformDemo } from '../VoiceWaveformDemo';

// Configurations par défaut
export const WAVEFORM_CONFIGS = {
  // Configuration standard
  standard: {
    width: 400,
    height: 150,
    barCount: 64,
    barWidth: 3,
    barSpacing: 2,
    color: '#00d4ff',
    glowColor: '#00d4ff'
  },
  
  // Configuration compacte
  compact: {
    width: 300,
    height: 100,
    barCount: 48,
    barWidth: 2,
    barSpacing: 1,
    color: '#00ff88',
    glowColor: '#00ff88'
  },
  
  // Configuration large
  large: {
    width: 600,
    height: 250,
    barCount: 96,
    barWidth: 4,
    barSpacing: 2,
    color: '#ff6b00',
    glowColor: '#ff6b00'
  }
};

// Thèmes de couleurs prédéfinis
export const WAVEFORM_THEMES = {
  jarvis: {
    primary: '#00d4ff',
    secondary: '#00ff88',
    accent: '#ff6b00'
  },
  
  matrix: {
    primary: '#00ff88',
    secondary: '#44ff88',
    accent: '#88ffaa'
  },
  
  reactor: {
    primary: '#ff6b00',
    secondary: '#ffaa44',
    accent: '#ffcc66'
  },
  
  plasma: {
    primary: '#aa44ff',
    secondary: '#cc66ff',
    accent: '#ee88ff'
  },
  
  ice: {
    primary: '#88ccff',
    secondary: '#aaddff',
    accent: '#cceeff'
  }
};

// Styles de visualisation disponibles
export const VISUALIZATION_STYLES = {
  BARS: 'bars',
  CIRCULAR: 'circular',
  WAVE: 'wave'
};

// Configuration audio par défaut
export const AUDIO_CONFIG = {
  fftSize: 2048,
  smoothingTimeConstant: 0.8,
  minDecibels: -80,
  maxDecibels: -10,
  sampleRate: 44100
};

// Utilitaires
export const WaveformUtils = {
  /**
   * Génère une configuration personnalisée
   */
  createConfig: (overrides = {}) => ({
    ...WAVEFORM_CONFIGS.standard,
    ...overrides
  }),
  
  /**
   * Applique un thème à une configuration
   */
  applyTheme: (config, themeName) => ({
    ...config,
    ...WAVEFORM_THEMES[themeName]
  }),
  
  /**
   * Calcule les dimensions optimales selon le conteneur
   */
  calculateDimensions: (containerWidth, containerHeight, aspectRatio = 2.67) => ({
    width: Math.min(containerWidth - 40, 800),
    height: Math.min((containerWidth - 40) / aspectRatio, containerHeight - 100)
  })
};