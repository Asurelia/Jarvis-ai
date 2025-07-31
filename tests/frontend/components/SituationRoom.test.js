/**
 * 🎯 Tests unitaires critiques pour SituationRoom
 * Tests pour le mode centre de contrôle, dashboard multi-panneaux, monitoring temps réel
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import SituationRoom from '../../../ui/src/components/SituationRoom';

// Mock des APIs WebSocket et fetch
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1, // OPEN
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
};

global.WebSocket = jest.fn(() => mockWebSocket);
global.fetch = jest.fn();

// Mock des composants dépendants
jest.mock('../../../ui/src/components/GPUStats', () => {
  return {
    __esModule: true,
    default: ({ onDataUpdate, autoRefresh }) => (
      <div data-testid="gpu-stats" data-auto-refresh={autoRefresh}>
        <div>GPU: AMD RX 6700 XT</div>
        <div>Temperature: 65°C</div>
        <div>Utilization: 78%</div>
        <button onClick={() => onDataUpdate?.({
          temperature: 67,
          utilization: 82,
          memory_used: 8500
        })}>
          Update GPU Data
        </button>
      </div>
    )
  };
});

jest.mock('../../../ui/src/components/MemoryViewer', () => {
  return {
    __esModule: true,
    default: ({ memoryData, showDetails }) => (
      <div data-testid="memory-viewer" data-show-details={showDetails}>
        <div>Memory Usage: {memoryData?.usage || 0}%</div>
        <div>Available: {memoryData?.available || 0} MB</div>
        <div>Active Processes: {memoryData?.processes || 0}</div>
      </div>
    )
  };
});

jest.mock('../../../ui/src/components/PerformanceMonitor', () => {
  return {
    __esModule: true,
    default: ({ metrics, refreshInterval }) => (
      <div data-testid="performance-monitor" data-refresh-interval={refreshInterval}>
        <div>CPU: {metrics?.cpu || 0}%</div>
        <div>RAM: {metrics?.ram || 0}%</div>
        <div>Network: {metrics?.network || 'Unknown'}</div>
        <div>FPS: {metrics?.fps || 0}</div>
      </div>
    )
  };
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16));
global.cancelAnimationFrame = jest.fn();

describe('SituationRoom', () => {
  const defaultProps = {
    layout: 'grid',
    autoRefresh: true,
    refreshInterval: 1000,
    showAlerts: true,
    theme: 'jarvis',
    onPanelUpdate: jest.fn(),
    onAlertTriggered: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    global.fetch.mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        gpu: { temperature: 65, utilization: 78 },
        memory: { usage: 67, available: 8192 },
        performance: { cpu: 45, ram: 62, network: 'stable', fps: 60 }
      })
    });
  });

  describe('Rendu de base', () => {
    test('affiche le titre du centre de contrôle', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByText(/situation room/i)).toBeInTheDocument();
      expect(screen.getByText(/command center/i)).toBeInTheDocument();
    });

    test('affiche les panneaux principaux', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByTestId('gpu-stats')).toBeInTheDocument();
      expect(screen.getByTestId('memory-viewer')).toBeInTheDocument();
      expect(screen.getByTestId('performance-monitor')).toBeInTheDocument();
    });

    test('applique le thème correct', () => {
      render(<SituationRoom {...defaultProps} theme="friday" />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('situation-room-friday');
    });

    test('utilise le layout grid par défaut', () => {
      render(<SituationRoom {...defaultProps} layout="grid" />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-grid');
    });

    test('supporte le layout en colonnes', () => {
      render(<SituationRoom {...defaultProps} layout="columns" />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-columns');
    });

    test('supporte le layout en lignes', () => {
      render(<SituationRoom {...defaultProps} layout="rows" />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-rows');
    });
  });

  describe('Contrôles et navigation', () => {
    test('affiche les contrôles de layout', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByText('Grid')).toBeInTheDocument();
      expect(screen.getByText('Columns')).toBeInTheDocument();
      expect(screen.getByText('Rows')).toBeInTheDocument();
    });

    test('change le layout via les contrôles', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      const columnsButton = screen.getByText('Columns');
      await user.click(columnsButton);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-columns');
    });

    test('affiche le toggle auto-refresh', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByText(/auto refresh/i)).toBeInTheDocument();
    });

    test('toggle auto-refresh', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} autoRefresh={true} />);
      
      const refreshToggle = screen.getByRole('checkbox', { name: /auto refresh/i });
      expect(refreshToggle).toBeChecked();
      
      await user.click(refreshToggle);
      expect(refreshToggle).not.toBeChecked();
    });

    test('affiche les contrôles d\'intervalle de rafraîchissement', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByDisplayValue('1000')).toBeInTheDocument(); // Intervalle par défaut
    });

    test('change l\'intervalle de rafraîchissement', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      const intervalInput = screen.getByDisplayValue('1000');
      await user.clear(intervalInput);
      await user.type(intervalInput, '2000');
      
      expect(intervalInput).toHaveValue(2000);
    });

    test('affiche le bouton de rafraîchissement manuel', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByText(/refresh now/i)).toBeInTheDocument();
    });

    test('déclenche un rafraîchissement manuel', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      const refreshButton = screen.getByText(/refresh now/i);
      await user.click(refreshButton);
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Données en temps réel', () => {
    test('établit une connexion WebSocket', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      await waitFor(() => {
        expect(global.WebSocket).toHaveBeenCalledWith(
          expect.stringContaining('ws://')
        );
      });
    });

    test('gère les messages WebSocket', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler un message WebSocket
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'gpu_update',
          data: { temperature: 70, utilization: 85 }
        })
      });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](messageEvent);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/85%/)).toBeInTheDocument();
      });
    });

    test('reconnecte automatiquement en cas de déconnexion', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler une déconnexion
      const closeEvent = new CloseEvent('close', { code: 1006 });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'close')[1](closeEvent);
      });
      
      // Attendre la tentative de reconnexion
      await waitFor(() => {
        expect(global.WebSocket).toHaveBeenCalledTimes(2);
      }, { timeout: 3000 });
    });

    test('affiche le statut de connexion', () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByTestId('connection-status')).toBeInTheDocument();
    });

    test('indique quand la connexion est établie', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler une connexion réussie
      const openEvent = new Event('open');
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'open')[1](openEvent);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/connected/i)).toBeInTheDocument();
      });
    });

    test('indique quand la connexion est perdue', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler une perte de connexion
      const closeEvent = new CloseEvent('close', { code: 1001 });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'close')[1](closeEvent);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Alertes et monitoring', () => {
    test('affiche le panneau d\'alertes', () => {
      render(<SituationRoom {...defaultProps} showAlerts={true} />);
      
      expect(screen.getByTestId('alerts-panel')).toBeInTheDocument();
    });

    test('cache le panneau d\'alertes quand désactivé', () => {
      render(<SituationRoom {...defaultProps} showAlerts={false} />);
      
      expect(screen.queryByTestId('alerts-panel')).not.toBeInTheDocument();
    });

    test('déclenche une alerte de température élevée', async () => {
      const mockOnAlertTriggered = jest.fn();
      render(<SituationRoom {...defaultProps} onAlertTriggered={mockOnAlertTriggered} />);
      
      // Simuler des données de température élevée
      const highTempEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'gpu_update',
          data: { temperature: 95, utilization: 78 }
        })
      });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](highTempEvent);
      });
      
      await waitFor(() => {
        expect(mockOnAlertTriggered).toHaveBeenCalledWith({
          type: 'temperature_high',
          severity: 'warning',
          message: expect.stringContaining('95°C')
        });
      });
    });

    test('déclenche une alerte de mémoire faible', async () => {
      const mockOnAlertTriggered = jest.fn();
      render(<SituationRoom {...defaultProps} onAlertTriggered={mockOnAlertTriggered} />);
      
      // Simuler des données de mémoire faible
      const lowMemoryEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'memory_update',
          data: { usage: 95, available: 512 }
        })
      });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](lowMemoryEvent);
      });
      
      await waitFor(() => {
        expect(mockOnAlertTriggered).toHaveBeenCalledWith({
          type: 'memory_low',
          severity: 'critical',
          message: expect.stringContaining('95%')
        });
      });
    });

    test('affiche l\'historique des alertes', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      expect(screen.getByText(/alert history/i)).toBeInTheDocument();
    });

    test('efface l\'historique des alertes', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      const clearButton = screen.getByText(/clear alerts/i);
      await user.click(clearButton);
      
      // Vérifier que l'historique est vidé
      const alertsList = screen.queryByTestId('alerts-list');
      expect(alertsList?.children).toHaveLength(0);
    });
  });

  describe('Panneaux et widgets', () => {
    test('permet de redimensionner les panneaux', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      const resizeHandle = screen.getByTestId('panel-resize-handle');
      expect(resizeHandle).toBeInTheDocument();
      
      // Simuler un redimensionnement
      fireEvent.mouseDown(resizeHandle, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(resizeHandle, { clientX: 200, clientY: 100 });
      fireEvent.mouseUp(resizeHandle);
      
      // Le panneau devrait avoir changé de taille
      await waitFor(() => {
        const panel = resizeHandle.closest('.situation-panel');
        expect(panel).toHaveStyle({ width: expect.any(String) });
      });
    });

    test('permet de déplacer les panneaux', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      const panelHeader = screen.getByTestId('panel-drag-handle');
      expect(panelHeader).toBeInTheDocument();
      
      // Simuler un déplacement
      fireEvent.mouseDown(panelHeader, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(panelHeader, { clientX: 200, clientY: 200 });
      fireEvent.mouseUp(panelHeader);
      
      // Le panneau devrait avoir changé de position
      await waitFor(() => {
        const panel = panelHeader.closest('.situation-panel');
        expect(panel).toHaveStyle({ 
          transform: expect.stringContaining('translate') 
        });
      });
    });

    test('permet de minimiser/maximiser les panneaux', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      const minimizeButton = screen.getByTestId('panel-minimize');
      await user.click(minimizeButton);
      
      const panel = minimizeButton.closest('.situation-panel');
      expect(panel).toHaveClass('minimized');
      
      // Maximiser à nouveau
      const maximizeButton = screen.getByTestId('panel-maximize');
      await user.click(maximizeButton);
      
      expect(panel).not.toHaveClass('minimized');
    });

    test('sauvegarde la configuration des panneaux', async () => {
      const mockOnPanelUpdate = jest.fn();
      render(<SituationRoom {...defaultProps} onPanelUpdate={mockOnPanelUpdate} />);
      
      // Modifier un panneau
      const resizeHandle = screen.getByTestId('panel-resize-handle');
      fireEvent.mouseDown(resizeHandle, { clientX: 100, clientY: 100 });
      fireEvent.mouseUp(resizeHandle);
      
      await waitFor(() => {
        expect(mockOnPanelUpdate).toHaveBeenCalledWith({
          panelId: expect.any(String),
          configuration: expect.objectContaining({
            width: expect.any(Number),
            height: expect.any(Number),
            position: expect.any(Object)
          })
        });
      });
    });
  });

  describe('Performance et optimisation', () => {
    test('limite les mises à jour pour éviter les spam', async () => {
      jest.useFakeTimers();
      render(<SituationRoom {...defaultProps} refreshInterval={100} />);
      
      // Envoyer plusieurs messages rapidement
      for (let i = 0; i < 10; i++) {
        const event = new MessageEvent('message', {
          data: JSON.stringify({
            type: 'gpu_update',
            data: { temperature: 65 + i, utilization: 78 }
          })
        });
        
        act(() => {
          mockWebSocket.addEventListener.mock.calls
            .find(call => call[0] === 'message')[1](event);
        });
      }
      
      // Avancer le temps
      act(() => {
        jest.advanceTimersByTime(500);
      });
      
      // Seules quelques mises à jour devraient avoir été traitées
      expect(screen.getByText(/74°C/)).toBeInTheDocument(); // Dernière valeur
      
      jest.useRealTimers();
    });

    test('utilise la virtualisation pour les listes longues', () => {
      render(<SituationRoom {...defaultProps} />);
      
      const alertsList = screen.getByTestId('alerts-list');
      expect(alertsList).toHaveAttribute('data-virtualized', 'true');
    });

    test('nettoie les ressources au démontage', () => {
      const { unmount } = render(<SituationRoom {...defaultProps} />);
      
      unmount();
      
      expect(mockWebSocket.close).toHaveBeenCalled();
      expect(global.cancelAnimationFrame).toHaveBeenCalled();
    });

    test('suspend les mises à jour quand l\'onglet n\'est pas visible', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler l'onglet qui devient invisible
      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true
      });
      
      document.dispatchEvent(new Event('visibilitychange'));
      
      await waitFor(() => {
        // Les mises à jour devraient être suspendues
        expect(global.fetch).not.toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Responsive design', () => {
    test('adapte le layout pour les petits écrans', () => {
      // Simuler un petit écran
      Object.defineProperty(window, 'innerWidth', { value: 768 });
      Object.defineProperty(window, 'innerHeight', { value: 1024 });
      
      render(<SituationRoom {...defaultProps} />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('mobile-layout');
    });

    test('masque certains panneaux sur mobile', () => {
      Object.defineProperty(window, 'innerWidth', { value: 480 });
      
      render(<SituationRoom {...defaultProps} />);
      
      // Certains panneaux moins critiques devraient être masqués
      const secondaryPanels = screen.queryAllByTestId('secondary-panel');
      secondaryPanels.forEach(panel => {
        expect(panel).toHaveClass('hidden-mobile');
      });
    });

    test('utilise un layout en pile sur très petits écrans', () => {
      Object.defineProperty(window, 'innerWidth', { value: 320 });
      
      render(<SituationRoom {...defaultProps} />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-stack');
    });
  });

  describe('Accessibilité', () => {
    test('fournit des labels appropriés aux panneaux', () => {
      render(<SituationRoom {...defaultProps} />);
      
      const gpuPanel = screen.getByLabelText(/gpu statistics/i);
      const memoryPanel = screen.getByLabelText(/memory usage/i);
      
      expect(gpuPanel).toBeInTheDocument();
      expect(memoryPanel).toBeInTheDocument();
    });

    test('supporte la navigation au clavier', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      // Naviguer avec Tab
      await user.tab();
      expect(document.activeElement).toHaveAttribute('role', 'button');
      
      // Utiliser les flèches pour naviguer entre panneaux
      await user.keyboard('{ArrowRight}');
      expect(document.activeElement).toHaveAttribute('data-panel-id');
    });

    test('annonce les alertes aux lecteurs d\'écran', async () => {
      render(<SituationRoom {...defaultProps} />);
      
      // Simuler une alerte
      const alertEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'alert',
          data: { 
            type: 'temperature_high',
            message: 'GPU temperature is 95°C'
          }
        })
      });
      
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](alertEvent);
      });
      
      await waitFor(() => {
        const alertRegion = screen.getByRole('alert');
        expect(alertRegion).toHaveTextContent(/95°C/);
      });
    });

    test('fournit des descriptions pour les données complexes', () => {
      render(<SituationRoom {...defaultProps} />);
      
      const gpuStats = screen.getByTestId('gpu-stats');
      expect(gpuStats).toHaveAttribute('aria-describedby');
      
      const description = document.getElementById(
        gpuStats.getAttribute('aria-describedby')
      );
      expect(description).toHaveTextContent(/gpu performance metrics/i);
    });
  });

  describe('Configuration et personnalisation', () => {
    test('charge la configuration sauvegardée', () => {
      const savedConfig = {
        layout: 'columns',
        panels: {
          gpu: { width: 400, height: 300, position: { x: 100, y: 50 } },
          memory: { width: 350, height: 250, position: { x: 500, y: 50 } }
        }
      };
      
      localStorage.setItem('situationRoomConfig', JSON.stringify(savedConfig));
      
      render(<SituationRoom {...defaultProps} />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveClass('layout-columns');
    });

    test('sauvegarde la configuration modifiée', async () => {
      const user = userEvent.setup();
      render(<SituationRoom {...defaultProps} />);
      
      // Modifier le layout
      const columnsButton = screen.getByText('Columns');
      await user.click(columnsButton);
      
      await waitFor(() => {
        const savedConfig = JSON.parse(
          localStorage.getItem('situationRoomConfig') || '{}'
        );
        expect(savedConfig.layout).toBe('columns');
      });
    });

    test('permet d\'ajouter des panneaux personnalisés', async () => {
      const customPanel = {
        id: 'custom-panel',
        title: 'Custom Metrics',
        component: () => <div>Custom Content</div>
      };
      
      render(<SituationRoom {...defaultProps} customPanels={[customPanel]} />);
      
      expect(screen.getByText('Custom Metrics')).toBeInTheDocument();
      expect(screen.getByText('Custom Content')).toBeInTheDocument();
    });

    test('supporte les thèmes personnalisés', () => {
      const customTheme = {
        name: 'custom',
        colors: {
          primary: '#ff0000',
          secondary: '#00ff00',
          background: '#000000'
        }
      };
      
      render(<SituationRoom {...defaultProps} customTheme={customTheme} />);
      
      const container = screen.getByTestId('situation-room-container');
      expect(container).toHaveStyle({
        '--primary-color': '#ff0000',
        '--secondary-color': '#00ff00',
        '--background-color': '#000000'
      });
    });
  });
});

// Tests d'intégration
describe('SituationRoom - Tests d\'intégration', () => {
  test('workflow complet de monitoring', async () => {
    const user = userEvent.setup();
    const mockOnAlertTriggered = jest.fn();
    
    render(<SituationRoom {...defaultProps} onAlertTriggered={mockOnAlertTriggered} />);
    
    // 1. Vérifier la connexion initiale
    await waitFor(() => {
      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });
    
    // 2. Recevoir des données normales
    const normalDataEvent = new MessageEvent('message', {
      data: JSON.stringify({
        type: 'system_update',
        data: {
          gpu: { temperature: 65, utilization: 78 },
          memory: { usage: 60, available: 6144 },
          performance: { cpu: 45, ram: 55, network: 'stable' }
        }
      })
    });
    
    act(() => {
      mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'message')[1](normalDataEvent);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/65°C/)).toBeInTheDocument();
      expect(screen.getByText(/78%/)).toBeInTheDocument();
    });
    
    // 3. Recevoir des données d'alerte
    const alertDataEvent = new MessageEvent('message', {
      data: JSON.stringify({
        type: 'system_update',
        data: {
          gpu: { temperature: 95, utilization: 98 },
          memory: { usage: 95, available: 512 }
        }
      })
    });
    
    act(() => {
      mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'message')[1](alertDataEvent);
    });
    
    // 4. Vérifier que les alertes sont déclenchées
    await waitFor(() => {
      expect(mockOnAlertTriggered).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'temperature_high',
          severity: 'critical'
        })
      );
    });
    
    // 5. Modifier le layout
    const columnsButton = screen.getByText('Columns');
    await user.click(columnsButton);
    
    const container = screen.getByTestId('situation-room-container');
    expect(container).toHaveClass('layout-columns');
    
    // 6. Désactiver auto-refresh
    const refreshToggle = screen.getByRole('checkbox', { name: /auto refresh/i });
    await user.click(refreshToggle);
    
    expect(refreshToggle).not.toBeChecked();
  });

  test('gestion d\'erreur et récupération', async () => {
    // Simuler une erreur API
    global.fetch.mockRejectedValueOnce(new Error('API Error'));
    
    render(<SituationRoom {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText(/connection error/i)).toBeInTheDocument();
    });
    
    // Simuler le retour de l'API
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({
        gpu: { temperature: 65, utilization: 78 }
      })
    });
    
    // Déclencher une nouvelle tentative
    const retryButton = screen.getByText(/retry/i);
    fireEvent.click(retryButton);
    
    await waitFor(() => {
      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });
  });
});