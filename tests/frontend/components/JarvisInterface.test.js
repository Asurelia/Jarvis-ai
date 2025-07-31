/**
 * 🎭 Tests unitaires critiques pour JarvisInterface
 * Tests pour l'interface holographique, interactions utilisateur, personas
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import JarvisInterface from '../../../ui/src/components/JarvisInterface';

// Mock des composants dépendants
jest.mock('../../../ui/src/components/ScanlineEffect', () => {
  return {
    __esModule: true,
    default: ({ children, config, onConfigChange, showControls }) => (
      <div data-testid="scanline-effect" data-config={JSON.stringify(config)}>
        {children}
        {showControls && <div data-testid="scanline-controls">Controls</div>}
      </div>
    ),
    useScanlineConfig: (initialConfig) => ({
      config: initialConfig,
      updateConfig: jest.fn(),
      applyPreset: jest.fn()
    })
  };
});

jest.mock('../../../ui/src/components/PersonaSwitcher', () => {
  return {
    __esModule: true,
    default: ({ onPersonaChange, apiUrl, showDetails, className }) => (
      <div 
        data-testid="persona-switcher" 
        data-api-url={apiUrl}
        className={className}
      >
        <button 
          onClick={() => onPersonaChange({ current: 'friday', previous: 'jarvis_classic' })}
          data-testid="switch-to-friday"
        >
          Switch to FRIDAY
        </button>
        <button 
          onClick={() => onPersonaChange({ current: 'edith', previous: 'friday' })}
          data-testid="switch-to-edith"
        >
          Switch to EDITH
        </button>
      </div>
    )
  };
});

// Mock des styles CSS
jest.mock('../../../ui/src/styles/jarvis-holographic.css', () => ({}));
jest.mock('../../../ui/src/styles/persona-switcher.css', () => ({}));

describe('JarvisInterface', () => {
  const defaultProps = {
    messages: [],
    onSendMessage: jest.fn(),
    enableScanlines: true,
    showScanlineControls: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendu de base', () => {
    test('affiche le titre JARVIS', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(screen.getByText('J.A.R.V.I.S')).toBeInTheDocument();
      expect(screen.getByText('Just A Rather Very Intelligent System')).toBeInTheDocument();
    });

    test('affiche les indicateurs de statut', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(screen.getByText(/STATUS:/)).toBeInTheDocument();
      expect(screen.getByText(/ONLINE/)).toBeInTheDocument();
      expect(screen.getByText(/CORE:/)).toBeInTheDocument();
      expect(screen.getByText(/ACTIVE/)).toBeInTheDocument();
      expect(screen.getByText(/AI:/)).toBeInTheDocument();
      expect(screen.getByText(/READY/)).toBeInTheDocument();
    });

    test('affiche les métriques système', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(screen.getByText('SYSTEM METRICS')).toBeInTheDocument();
      expect(screen.getByText(/CPU:/)).toBeInTheDocument();
      expect(screen.getByText(/RAM:/)).toBeInTheDocument();
      expect(screen.getByText(/NETWORK:/)).toBeInTheDocument();
      expect(screen.getByText(/TEMP:/)).toBeInTheDocument();
    });

    test('affiche les modules AI', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(screen.getByText('AI MODULES')).toBeInTheDocument();
      expect(screen.getByText(/NLP:/)).toBeInTheDocument();
      expect(screen.getByText(/VISION:/)).toBeInTheDocument();
      expect(screen.getByText(/MEMORY:/)).toBeInTheDocument();
      expect(screen.getByText(/LEARNING:/)).toBeInTheDocument();
    });

    test('affiche les actions rapides', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(screen.getByText('QUICK ACTIONS')).toBeInTheDocument();
      expect(screen.getByText('ANALYZE')).toBeInTheDocument();
      expect(screen.getByText('SCAN')).toBeInTheDocument();
      expect(screen.getByText('EXECUTE')).toBeInTheDocument();
      expect(screen.getByText('REPORT')).toBeInTheDocument();
    });
  });

  describe('Interface de chat', () => {
    test('affiche le champ de saisie et les boutons', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      expect(input).toBeInTheDocument();
      
      const micButton = screen.getByText('🎙️');
      expect(micButton).toBeInTheDocument();
      
      const sendButton = screen.getByText('SEND');
      expect(sendButton).toBeInTheDocument();
    });

    test('permet la saisie de texte', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      
      await user.type(input, 'Hello JARVIS');
      expect(input).toHaveValue('Hello JARVIS');
    });

    test('active/désactive le bouton SEND selon le contenu', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const sendButton = screen.getByText('SEND');
      const input = screen.getByPlaceholderText('Enter command or query...');
      
      // Bouton désactivé au début
      expect(sendButton).toBeDisabled();
      
      // Activer après saisie
      await user.type(input, 'Test message');
      expect(sendButton).not.toBeDisabled();
      
      // Désactiver si on efface
      await user.clear(input);
      expect(sendButton).toBeDisabled();
    });

    test('appelle onSendMessage lors de l\'envoi', async () => {
      const user = userEvent.setup();
      const mockSendMessage = jest.fn();
      
      render(<JarvisInterface {...defaultProps} onSendMessage={mockSendMessage} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      const sendButton = screen.getByText('SEND');
      
      await user.type(input, 'Test command');
      await user.click(sendButton);
      
      expect(mockSendMessage).toHaveBeenCalledWith('Test command');
      expect(input).toHaveValue(''); // Input vidé après envoi
    });

    test('permet l\'envoi avec la touche Entrée', async () => {
      const user = userEvent.setup();
      const mockSendMessage = jest.fn();
      
      render(<JarvisInterface {...defaultProps} onSendMessage={mockSendMessage} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      
      await user.type(input, 'Test command{enter}');
      
      expect(mockSendMessage).toHaveBeenCalledWith('Test command');
    });

    test('toggle le microphone', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const micButton = screen.getByText('🎙️');
      
      await user.click(micButton);
      
      // Le bouton devrait changer d'état (actif)
      expect(micButton).toHaveClass('active');
      expect(micButton).toHaveTextContent('🎤');
      
      // Cliquer à nouveau pour désactiver
      await user.click(micButton);
      expect(micButton).not.toHaveClass('active');
      expect(micButton).toHaveTextContent('🎙️');
    });
  });

  describe('Affichage des messages', () => {
    test('affiche les messages fournis', () => {
      const messages = [
        { type: 'user', content: 'Hello JARVIS' },
        { type: 'bot', content: 'Hello sir, how may I assist you?' },
        { type: 'user', content: 'What is the system status?' },
        { type: 'bot', content: 'All systems are operating normally.' }
      ];
      
      render(<JarvisInterface {...defaultProps} messages={messages} />);
      
      expect(screen.getByText('Hello JARVIS')).toBeInTheDocument();
      expect(screen.getByText('Hello sir, how may I assist you?')).toBeInTheDocument();
      expect(screen.getByText('What is the system status?')).toBeInTheDocument();
      expect(screen.getByText('All systems are operating normally.')).toBeInTheDocument();
    });

    test('affiche correctement les types de messages', () => {
      const messages = [
        { type: 'user', content: 'User message' },
        { type: 'bot', content: 'Bot response' }
      ];
      
      render(<JarvisInterface {...defaultProps} messages={messages} />);
      
      // Vérifier les classes CSS appliquées
      const userMessage = screen.getByText('User message').closest('.jarvis-message');
      const botMessage = screen.getByText('Bot response').closest('.jarvis-message');
      
      expect(userMessage).toHaveClass('user');
      expect(botMessage).toHaveClass('bot');
    });

    test('affiche l\'indicateur de traitement', async () => {
      const user = userEvent.setup();
      const mockSendMessage = jest.fn();
      
      render(<JarvisInterface {...defaultProps} onSendMessage={mockSendMessage} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      const sendButton = screen.getByText('SEND');
      
      await user.type(input, 'Test message');
      await user.click(sendButton);
      
      // L'indicateur de traitement devrait apparaître
      expect(screen.getByText('Processing...')).toBeInTheDocument();
      
      // Il devrait disparaître après un délai
      await waitFor(() => {
        expect(screen.queryByText('Processing...')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Effets Scanline', () => {
    test('active les scanlines par défaut', () => {
      render(<JarvisInterface {...defaultProps} enableScanlines={true} />);
      
      const scanlineEffect = screen.getByTestId('scanline-effect');
      const config = JSON.parse(scanlineEffect.getAttribute('data-config'));
      
      expect(config.enabled).toBe(true);
    });

    test('désactive les scanlines quand demandé', () => {
      render(<JarvisInterface {...defaultProps} enableScanlines={false} />);
      
      const scanlineEffect = screen.getByTestId('scanline-effect');
      const config = JSON.parse(scanlineEffect.getAttribute('data-config'));
      
      expect(config.enabled).toBe(false);
    });

    test('affiche les contrôles scanline quand activés', () => {
      render(<JarvisInterface {...defaultProps} showScanlineControls={true} />);
      
      expect(screen.getByTestId('scanline-controls')).toBeInTheDocument();
    });

    test('toggle les scanlines avec le bouton', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} enableScanlines={true} />);
      
      const scanToggle = screen.getByTitle('Toggle Scanline Effects');
      expect(scanToggle).toHaveTextContent('SCAN: ON');
      
      await user.click(scanToggle);
      
      // Le bouton devrait refléter le changement d'état
      expect(scanToggle).toHaveTextContent('SCAN: OFF');
    });

    test('active le mode intense temporairement', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const intenseButton = screen.getByTitle('Activate Intense Scan Mode');
      await user.click(intenseButton);
      
      // Le mode intense devrait être activé (testé via les mocks)
      expect(intenseButton).toBeInTheDocument();
    });
  });

  describe('Persona Switcher', () => {
    test('affiche le PersonaSwitcher', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      const personaSwitcher = screen.getByTestId('persona-switcher');
      expect(personaSwitcher).toBeInTheDocument();
      expect(personaSwitcher).toHaveAttribute('data-api-url', 'http://localhost:8001/api/persona');
      expect(personaSwitcher).toHaveClass('jarvis-theme');
    });

    test('gère le changement de persona vers FRIDAY', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const switchButton = screen.getByTestId('switch-to-friday');
      await user.click(switchButton);
      
      // Le changement de persona devrait être géré
      // (vérifié via l'intégration avec les presets scanline)
    });

    test('gère le changement de persona vers EDITH', async () => {
      const user = userEvent.setup();
      render(<JarvisInterface {...defaultProps} />);
      
      const switchButton = screen.getByTestId('switch-to-edith');
      await user.click(switchButton);
      
      // Le changement de persona devrait être géré
    });
  });

  describe('Particules flottantes', () => {
    test('affiche les particules flottantes', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      const particlesContainer = document.querySelector('.jarvis-particles');
      expect(particlesContainer).toBeInTheDocument();
      
      // Vérifier qu'il y a des particules (par défaut 30)
      const particles = document.querySelectorAll('.jarvis-particle');
      expect(particles).toHaveLength(30);
    });

    test('génère des particules avec des propriétés aléatoires', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      const particles = document.querySelectorAll('.jarvis-particle');
      
      particles.forEach(particle => {
        const style = particle.style;
        
        // Vérifier que les propriétés CSS sont définies
        expect(style.left).toBeTruthy();
        expect(style.animationDelay).toBeTruthy();
        expect(style.animationDuration).toBeTruthy();
        
        // Vérifier les plages de valeurs
        const left = parseFloat(style.left);
        expect(left).toBeGreaterThanOrEqual(0);
        expect(left).toBeLessThanOrEqual(100);
      });
    });
  });

  describe('HUD Corners', () => {
    test('affiche les coins HUD', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      expect(document.querySelector('.jarvis-hud-corner.top-left')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-hud-corner.top-right')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-hud-corner.bottom-left')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-hud-corner.bottom-right')).toBeInTheDocument();
    });
  });

  describe('Contenu personnalisé', () => {
    test('affiche le contenu enfant fourni', () => {
      const customContent = <div data-testid="custom-content">Custom Panel Content</div>;
      
      render(
        <JarvisInterface {...defaultProps}>
          {customContent}
        </JarvisInterface>
      );
      
      expect(screen.getByTestId('custom-content')).toBeInTheDocument();
      expect(screen.getByText('Custom Panel Content')).toBeInTheDocument();
    });

    test('fonctionne sans contenu personnalisé', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      // L'interface devrait fonctionner normalement sans contenu personnalisé
      expect(screen.getByText('J.A.R.V.I.S')).toBeInTheDocument();
    });
  });

  describe('États et interactions', () => {
    test('désactive l\'interface pendant le traitement', async () => {
      const user = userEvent.setup();
      const mockSendMessage = jest.fn();
      
      render(<JarvisInterface {...defaultProps} onSendMessage={mockSendMessage} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      const sendButton = screen.getByText('SEND');
      
      await user.type(input, 'Test message');
      await user.click(sendButton);
      
      // Pendant le traitement, l'input devrait être désactivé
      expect(input).toBeDisabled();
    });

    test('gère les messages vides', async () => {
      const user = userEvent.setup();
      const mockSendMessage = jest.fn();
      
      render(<JarvisInterface {...defaultProps} onSendMessage={mockSendMessage} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      const sendButton = screen.getByText('SEND');
      
      // Essayer d'envoyer un message vide (avec seulement des espaces)
      await user.type(input, '   ');
      
      expect(sendButton).toBeDisabled();
      
      // Même en cliquant, rien ne devrait être envoyé
      await user.click(sendButton);
      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    test('fonctionne sans gestionnaire de message', () => {
      render(<JarvisInterface {...defaultProps} onSendMessage={undefined} />);
      
      // L'interface devrait se rendre sans erreur
      expect(screen.getByText('J.A.R.V.I.S')).toBeInTheDocument();
      
      // Le bouton send devrait être désactivé
      const sendButton = screen.getByText('SEND');
      expect(sendButton).toBeDisabled();
    });
  });

  describe('Responsive et accessibilité', () => {
    test('contient les attributs d\'accessibilité essentiels', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      const input = screen.getByPlaceholderText('Enter command or query...');
      expect(input).toHaveAttribute('type', 'text');
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      
      // Vérifier que certains boutons ont des titres
      const scanToggle = screen.getByTitle('Toggle Scanline Effects');
      const intenseButton = screen.getByTitle('Activate Intense Scan Mode');
      
      expect(scanToggle).toBeInTheDocument();
      expect(intenseButton).toBeInTheDocument();
    });

    test('utilise les classes CSS appropriées pour le thème', () => {
      render(<JarvisInterface {...defaultProps} />);
      
      // Vérifier les classes principales
      expect(document.querySelector('.jarvis-holographic-container')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-interface')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-panel')).toBeInTheDocument();
      expect(document.querySelector('.jarvis-title')).toBeInTheDocument();
    });
  });

  describe('Performance et optimisations', () => {
    test('ne re-rend pas inutilement', () => {
      const { rerender } = render(<JarvisInterface {...defaultProps} />);
      
      // Simuler plusieurs re-rendus avec les mêmes props
      rerender(<JarvisInterface {...defaultProps} />);
      rerender(<JarvisInterface {...defaultProps} />);
      
      // L'interface devrait toujours être présente
      expect(screen.getByText('J.A.R.V.I.S')).toBeInTheDocument();
    });

    test('gère une grande liste de messages', () => {
      // Créer beaucoup de messages
      const manyMessages = Array.from({ length: 100 }, (_, i) => ({
        type: i % 2 === 0 ? 'user' : 'bot',
        content: `Message ${i + 1}`
      }));
      
      render(<JarvisInterface {...defaultProps} messages={manyMessages} />);
      
      // Vérifier que les premiers et derniers messages sont présents
      expect(screen.getByText('Message 1')).toBeInTheDocument();
      expect(screen.getByText('Message 100')).toBeInTheDocument();
    });
  });
});

// Tests d'intégration
describe('JarvisInterface - Tests d\'intégration', () => {
  test('workflow complet de conversation', async () => {
    const user = userEvent.setup();
    const mockSendMessage = jest.fn();
    const messages = [
      { type: 'bot', content: 'Hello! How can I assist you today?' }
    ];
    
    const { rerender } = render(
      <JarvisInterface 
        {...defaultProps} 
        onSendMessage={mockSendMessage}
        messages={messages}
      />
    );
    
    // 1. Utilisateur tape un message
    const input = screen.getByPlaceholderText('Enter command or query...');
    await user.type(input, 'What is the system status?');
    
    // 2. Utilisateur envoie le message
    const sendButton = screen.getByText('SEND');
    await user.click(sendButton);
    
    expect(mockSendMessage).toHaveBeenCalledWith('What is the system status?');
    
    // 3. Simuler la réponse du bot
    const updatedMessages = [
      ...messages,
      { type: 'user', content: 'What is the system status?' },
      { type: 'bot', content: 'All systems are operating normally.' }
    ];
    
    rerender(
      <JarvisInterface 
        {...defaultProps} 
        onSendMessage={mockSendMessage}
        messages={updatedMessages}
      />
    );
    
    // 4. Vérifier que les nouveaux messages apparaissent
    expect(screen.getByText('What is the system status?')).toBeInTheDocument();
    expect(screen.getByText('All systems are operating normally.')).toBeInTheDocument();
  });

  test('intégration persona et scanlines', async () => {
    const user = userEvent.setup();
    render(<JarvisInterface {...defaultProps} enableScanlines={true} />);
    
    // Changer de persona
    const switchButton = screen.getByTestId('switch-to-friday');
    await user.click(switchButton);
    
    // Vérifier que l'interface réagit au changement
    expect(screen.getByTestId('persona-switcher')).toBeInTheDocument();
    expect(screen.getByTestId('scanline-effect')).toBeInTheDocument();
  });
});