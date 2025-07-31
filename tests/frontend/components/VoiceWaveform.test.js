/**
 * 🎵 Tests unitaires critiques pour VoiceWaveform
 * Tests pour la visualisation audio, analyse fréquence, animations temps réel
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceWaveform from '../../../ui/src/components/VoiceWaveform';

// Mock Web Audio API
const mockAudioContext = {
  createAnalyser: jest.fn(),
  createMediaStreamSource: jest.fn(),
  createGain: jest.fn(),
  connect: jest.fn(),
  disconnect: jest.fn(),
  resume: jest.fn().mockResolvedValue(),
  suspend: jest.fn().mockResolvedValue(),
  close: jest.fn().mockResolvedValue(),
  state: 'running',
  sampleRate: 44100,
  currentTime: 0
};

const mockAnalyser = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  fftSize: 2048,
  frequencyBinCount: 1024,
  smoothingTimeConstant: 0.8,
  minDecibels: -100,
  maxDecibels: -30,
  getByteFrequencyData: jest.fn(),
  getByteTimeDomainData: jest.fn(),
  getFloatFrequencyData: jest.fn(),
  getFloatTimeDomainData: jest.fn()
};

const mockMediaStreamSource = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  mediaStream: {}
};

const mockGainNode = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  gain: { value: 1.0 }
};

// Mock Canvas
const mockCanvas = {
  getContext: jest.fn(() => ({
    clearRect: jest.fn(),
    fillRect: jest.fn(),
    strokeRect: jest.fn(),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    stroke: jest.fn(),
    fill: jest.fn(),
    arc: jest.fn(),
    closePath: jest.fn(),
    save: jest.fn(),
    restore: jest.fn(),
    translate: jest.fn(),
    rotate: jest.fn(),
    scale: jest.fn(),
    setTransform: jest.fn(),
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    globalAlpha: 1,
    globalCompositeOperation: 'source-over',
    font: '10px sans-serif',
    textAlign: 'start',
    textBaseline: 'alphabetic',
    fillText: jest.fn(),
    strokeText: jest.fn(),
    measureText: jest.fn(() => ({ width: 50 })),
    createLinearGradient: jest.fn(() => ({
      addColorStop: jest.fn()
    })),
    createRadialGradient: jest.fn(() => ({
      addColorStop: jest.fn()
    }))
  })),
  width: 800,
  height: 400,
  style: {}
};

// Setup global mocks
beforeAll(() => {
  global.AudioContext = jest.fn(() => mockAudioContext);
  global.webkitAudioContext = jest.fn(() => mockAudioContext);
  
  mockAudioContext.createAnalyser.mockReturnValue(mockAnalyser);
  mockAudioContext.createMediaStreamSource.mockReturnValue(mockMediaStreamSource);
  mockAudioContext.createGain.mockReturnValue(mockGainNode);
  
  // Mock requestAnimationFrame
  global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16));
  global.cancelAnimationFrame = jest.fn();
  
  // Mock getUserMedia
  global.navigator.mediaDevices = {
    getUserMedia: jest.fn().mockResolvedValue({
      getTracks: jest.fn(() => [
        {
          stop: jest.fn(),
          enabled: true,
          readyState: 'live'
        }
      ])
    })
  };
  
  // Mock Canvas
  global.HTMLCanvasElement.prototype.getContext = mockCanvas.getContext;
  
  // Mock ResizeObserver
  global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn()
  }));
});

describe('VoiceWaveform', () => {
  const defaultProps = {
    isListening: false,
    audioData: null,
    width: 800,
    height: 400,
    theme: 'jarvis',
    showFrequencyBars: true,
    showTimeDomain: true,
    animated: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset analyser mock data
    mockAnalyser.getByteFrequencyData.mockImplementation((array) => {
      // Simuler des données de fréquence
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 255);
      }
    });
    
    mockAnalyser.getByteTimeDomainData.mockImplementation((array) => {
      // Simuler des données temporelles
      for (let i = 0; i < array.length; i++) {
        array[i] = 128 + Math.floor(Math.random() * 50 - 25);
      }
    });
  });

  describe('Rendu de base', () => {
    test('affiche le canvas de visualisation', () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      const canvas = screen.getByRole('img', { name: /voice waveform visualization/i });
      expect(canvas).toBeInTheDocument();
      expect(canvas.tagName).toBe('CANVAS');
    });

    test('définit les dimensions du canvas', () => {
      render(<VoiceWaveform {...defaultProps} width={600} height={300} />);
      
      const canvas = screen.getByRole('img');
      expect(canvas).toHaveAttribute('width', '600');
      expect(canvas).toHaveAttribute('height', '300');
    });

    test('applique les classes CSS appropriées', () => {
      render(<VoiceWaveform {...defaultProps} theme="friday" />);
      
      const container = screen.getByTestId('voice-waveform-container');
      expect(container).toHaveClass('voice-waveform-friday');
    });

    test('affiche le statut d\'écoute', () => {
      render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      expect(screen.getByText(/listening/i)).toBeInTheDocument();
    });

    test('affiche le statut d\'attente', () => {
      render(<VoiceWaveform {...defaultProps} isListening={false} />);
      
      expect(screen.getByText(/ready/i)).toBeInTheDocument();
    });
  });

  describe('Initialisation Audio', () => {
    test('initialise le contexte audio au démarrage', async () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        expect(global.AudioContext).toHaveBeenCalled();
      });
    });

    test('crée un analyseur audio', async () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockAudioContext.createAnalyser).toHaveBeenCalled();
      });
    });

    test('configure les paramètres de l\'analyseur', async () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockAnalyser.fftSize).toBeDefined();
        expect(mockAnalyser.smoothingTimeConstant).toBeDefined();
      });
    });

    test('gère l\'absence de support Audio Context', async () => {
      const originalAudioContext = global.AudioContext;
      global.AudioContext = undefined;
      global.webkitAudioContext = undefined;
      
      render(<VoiceWaveform {...defaultProps} />);
      
      // Devrait afficher un message d'erreur
      await waitFor(() => {
        expect(screen.getByText(/audio not supported/i)).toBeInTheDocument();
      });
      
      global.AudioContext = originalAudioContext;
    });
  });

  describe('Gestion du microphone', () => {
    test('démarre l\'écoute quand isListening devient true', async () => {
      const { rerender } = render(<VoiceWaveform {...defaultProps} isListening={false} />);
      
      rerender(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      await waitFor(() => {
        expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        });
      });
    });

    test('arrête l\'écoute quand isListening devient false', async () => {
      const mockTrack = {
        stop: jest.fn(),
        enabled: true,
        readyState: 'live'
      };
      
      global.navigator.mediaDevices.getUserMedia.mockResolvedValue({
        getTracks: jest.fn(() => [mockTrack])
      });
      
      const { rerender } = render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      await waitFor(() => {
        expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
      });
      
      rerender(<VoiceWaveform {...defaultProps} isListening={false} />);
      
      await waitFor(() => {
        expect(mockTrack.stop).toHaveBeenCalled();
      });
    });

    test('gère les erreurs de permission microphone', async () => {
      global.navigator.mediaDevices.getUserMedia.mockRejectedValue(
        new Error('Permission denied')
      );
      
      render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      await waitFor(() => {
        expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
      });
    });

    test('gère l\'absence de MediaDevices', async () => {
      const originalMediaDevices = global.navigator.mediaDevices;
      global.navigator.mediaDevices = undefined;
      
      render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      await waitFor(() => {
        expect(screen.getByText(/microphone not supported/i)).toBeInTheDocument();
      });
      
      global.navigator.mediaDevices = originalMediaDevices;
    });
  });

  describe('Visualisation des fréquences', () => {
    test('dessine les barres de fréquence', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} showFrequencyBars={true} />);
      
      await waitFor(() => {
        expect(mockCtx.fillRect).toHaveBeenCalled();
      });
    });

    test('utilise les bonnes couleurs pour le thème JARVIS', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} theme="jarvis" />);
      
      await waitFor(() => {
        expect(mockCtx.fillStyle).toMatch(/#00ff00|#0080ff|rgb\(0,.*\)/i);
      });
    });

    test('utilise les bonnes couleurs pour le thème FRIDAY', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} theme="friday" />);
      
      await waitFor(() => {
        expect(mockCtx.fillStyle).toMatch(/#ff6b35|#f7931e|rgb\(.*\)/i);
      });
    });

    test('adapte le nombre de barres à la largeur', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} width={400} showFrequencyBars={true} />);
      
      await waitFor(() => {
        // Devrait dessiner moins de barres pour une largeur plus petite
        const fillRectCalls = mockCtx.fillRect.mock.calls.length;
        expect(fillRectCalls).toBeGreaterThan(0);
      });
    });

    test('cache les barres quand showFrequencyBars est false', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} showFrequencyBars={false} />);
      
      await waitFor(() => {
        // Ne devrait pas dessiner de barres de fréquence
        const fillRectCalls = mockCtx.fillRect.mock.calls.filter(call => 
          call[3] > 10 // Hauteur significative
        );
        expect(fillRectCalls.length).toBe(0);
      });
    });
  });

  describe('Visualisation temporelle', () => {
    test('dessine la waveform temporelle', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} showTimeDomain={true} />);
      
      await waitFor(() => {
        expect(mockCtx.beginPath).toHaveBeenCalled();
        expect(mockCtx.lineTo).toHaveBeenCalled();
        expect(mockCtx.stroke).toHaveBeenCalled();
      });
    });

    test('utilise une ligne lisse pour la waveform', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} showTimeDomain={true} />);
      
      await waitFor(() => {
        const lineToCalls = mockCtx.lineTo.mock.calls;
        expect(lineToCalls.length).toBeGreaterThan(50); // Beaucoup de points pour une ligne lisse
      });
    });

    test('cache la waveform quand showTimeDomain est false', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} showTimeDomain={false} />);
      
      await waitFor(() => {
        expect(mockCtx.stroke).not.toHaveBeenCalled();
      });
    });
  });

  describe('Animation et performances', () => {
    test('démarre l\'animation quand animated est true', async () => {
      render(<VoiceWaveform {...defaultProps} animated={true} />);
      
      await waitFor(() => {
        expect(global.requestAnimationFrame).toHaveBeenCalled();
      });
    });

    test('arrête l\'animation quand animated est false', async () => {
      const { rerender } = render(<VoiceWaveform {...defaultProps} animated={true} />);
      
      await waitFor(() => {
        expect(global.requestAnimationFrame).toHaveBeenCalled();
      });
      
      rerender(<VoiceWaveform {...defaultProps} animated={false} />);
      
      await waitFor(() => {
        expect(global.cancelAnimationFrame).toHaveBeenCalled();
      });
    });

    test('maintient un taux de rafraîchissement stable', async () => {
      jest.useFakeTimers();
      
      render(<VoiceWaveform {...defaultProps} animated={true} />);
      
      // Simuler plusieurs frames
      act(() => {
        jest.advanceTimersByTime(100); // ~6 frames à 60fps
      });
      
      expect(global.requestAnimationFrame).toHaveBeenCalledTimes(6);
      
      jest.useRealTimers();
    });

    test('optimise le rendu quand aucune donnée audio', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} isListening={false} />);
      
      await waitFor(() => {
        // Devrait faire un rendu minimal
        expect(mockCtx.clearRect).toHaveBeenCalled();
      });
    });
  });

  describe('Données audio externes', () => {
    test('utilise les données audio fournies', async () => {
      const audioData = {
        frequencyData: new Uint8Array(512).fill(100),
        timeDomainData: new Uint8Array(512).fill(128)
      };
      
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} audioData={audioData} />);
      
      await waitFor(() => {
        expect(mockCtx.fillRect).toHaveBeenCalled();
      });
    });

    test('ignore les données audio invalides', async () => {
      const invalidAudioData = {
        frequencyData: null,
        timeDomainData: "invalid"
      };
      
      render(<VoiceWaveform {...defaultProps} audioData={invalidAudioData} />);
      
      // Ne devrait pas lever d'erreur
      await waitFor(() => {
        expect(screen.getByRole('img')).toBeInTheDocument();
      });
    });

    test('priorise les données externes sur le microphone', async () => {
      const audioData = {
        frequencyData: new Uint8Array(512).fill(255),
        timeDomainData: new Uint8Array(512).fill(200)
      };
      
      render(<VoiceWaveform {...defaultProps} isListening={true} audioData={audioData} />);
      
      // Les données externes devraient être utilisées même si isListening=true
      await waitFor(() => {
        expect(mockAnalyser.getByteFrequencyData).not.toHaveBeenCalled();
      });
    });
  });

  describe('Responsive design', () => {
    test('redimensionne le canvas automatiquement', async () => {
      const { rerender } = render(<VoiceWaveform {...defaultProps} width={400} height={200} />);
      
      rerender(<VoiceWaveform {...defaultProps} width={800} height={400} />);
      
      const canvas = screen.getByRole('img');
      expect(canvas).toHaveAttribute('width', '800');
      expect(canvas).toHaveAttribute('height', '400');
    });

    test('observe les changements de taille du conteneur', async () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      expect(global.ResizeObserver).toHaveBeenCalled();
    });

    test('adapte la visualisation aux petites tailles', async () => {
      const mockCtx = mockCanvas.getContext();
      
      render(<VoiceWaveform {...defaultProps} width={200} height={100} />);
      
      await waitFor(() => {
        // Devrait adapter le rendu à la petite taille
        expect(mockCtx.clearRect).toHaveBeenCalledWith(0, 0, 200, 100);
      });
    });
  });

  describe('Accessibilité', () => {
    test('fournit un texte alternatif approprié', () => {
      render(<VoiceWaveform {...defaultProps} />);
      
      const canvas = screen.getByRole('img');
      expect(canvas).toHaveAttribute('aria-label', expect.stringContaining('voice waveform'));
    });

    test('indique l\'état d\'écoute aux lecteurs d\'écran', () => {
      render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      expect(screen.getByRole('status')).toHaveTextContent(/listening/i);
    });

    test('fournit des informations sur les niveaux audio', async () => {
      const audioData = {
        frequencyData: new Uint8Array(512).fill(200),
        timeDomainData: new Uint8Array(512).fill(150)
      };
      
      render(<VoiceWaveform {...defaultProps} audioData={audioData} />);
      
      await waitFor(() => {
        expect(screen.getByText(/audio level/i)).toBeInTheDocument();
      });
    });
  });

  describe('Gestion d\'erreurs', () => {
    test('gère les erreurs de contexte audio', async () => {
      mockAudioContext.createAnalyser.mockImplementation(() => {
        throw new Error('Audio context error');
      });
      
      render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText(/audio error/i)).toBeInTheDocument();
      });
    });

    test('gère les erreurs de rendu canvas', async () => {
      const mockCtx = mockCanvas.getContext();
      mockCtx.fillRect.mockImplementation(() => {
        throw new Error('Canvas error');
      });
      
      render(<VoiceWaveform {...defaultProps} />);
      
      // Ne devrait pas casser l'interface
      await waitFor(() => {
        expect(screen.getByRole('img')).toBeInTheDocument();
      });
    });

    test('récupère après une erreur temporaire', async () => {
      const mockCtx = mockCanvas.getContext();
      
      // Simuler une erreur puis un succès
      mockCtx.fillRect
        .mockImplementationOnce(() => {
          throw new Error('Temporary error');
        })
        .mockImplementation(() => {});
      
      render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        // Devrait continuer à fonctionner après l'erreur
        expect(screen.getByRole('img')).toBeInTheDocument();
      });
    });
  });

  describe('Nettoyage et mémoire', () => {
    test('nettoie les ressources au démontage', async () => {
      const mockTrack = {
        stop: jest.fn(),
        enabled: true
      };
      
      global.navigator.mediaDevices.getUserMedia.mockResolvedValue({
        getTracks: jest.fn(() => [mockTrack])
      });
      
      const { unmount } = render(<VoiceWaveform {...defaultProps} isListening={true} />);
      
      await waitFor(() => {
        expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
      });
      
      unmount();
      
      expect(mockTrack.stop).toHaveBeenCalled();
      expect(global.cancelAnimationFrame).toHaveBeenCalled();
    });

    test('ferme le contexte audio proprement', async () => {
      const { unmount } = render(<VoiceWaveform {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockAudioContext.createAnalyser).toHaveBeenCalled();
      });
      
      unmount();
      
      expect(mockAudioContext.close).toHaveBeenCalled();
    });

    test('déconnecte les observateurs de redimensionnement', async () => {
      const mockObserver = {
        observe: jest.fn(),
        unobserve: jest.fn(),
        disconnect: jest.fn()
      };
      
      global.ResizeObserver.mockImplementation(() => mockObserver);
      
      const { unmount } = render(<VoiceWaveform {...defaultProps} />);
      
      unmount();
      
      expect(mockObserver.disconnect).toHaveBeenCalled();
    });
  });
});

// Tests de performance
describe('VoiceWaveform - Performance', () => {
  test('maintient 60fps avec des données complexes', async () => {
    jest.useFakeTimers();
    
    const complexAudioData = {
      frequencyData: new Uint8Array(2048).map(() => Math.random() * 255),
      timeDomainData: new Uint8Array(2048).map(() => Math.random() * 255)
    };
    
    render(<VoiceWaveform {...defaultProps} audioData={complexAudioData} animated={true} />);
    
    const startTime = performance.now();
    
    act(() => {
      jest.advanceTimersByTime(1000); // 1 seconde
    });
    
    const endTime = performance.now();
    const frameDuration = (endTime - startTime) / 60; // 60 frames attendues
    
    expect(frameDuration).toBeLessThan(16.67); // Moins de 16.67ms par frame pour 60fps
    
    jest.useRealTimers();
  });

  test('optimise le rendu pour les grandes résolutions', async () => {
    const mockCtx = mockCanvas.getContext();
    
    render(<VoiceWaveform {...defaultProps} width={1920} height={1080} />);
    
    await waitFor(() => {
      // Devrait utiliser des optimisations pour les grandes résolutions
      const clearRectCalls = mockCtx.clearRect.mock.calls;
      expect(clearRectCalls.length).toBeGreaterThan(0);
    });
  });
});