/**
 * 🔗 Tests d'intégration critiques pour l'API Frontend
 * Tests pour l'intégration API/WebSocket, gestion d'erreurs, authentification
 */

import { 
  apiClient, 
  wsManager, 
  authManager,
  errorHandler,
  retryManager
} from '../../../ui/src/utils/api';

// Mock fetch global
global.fetch = jest.fn();

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1, // OPEN
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
};

global.WebSocket = jest.fn(() => mockWebSocket);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.sessionStorage = sessionStorageMock;

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  describe('Configuration de base', () => {
    test('utilise l\'URL de base correcte', () => {
      expect(apiClient.baseURL).toBe('http://localhost:8001');
    });

    test('inclut les headers par défaut', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ success: true })
      });

      await apiClient.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          })
        })
      );
    });

    test('ajoute les headers d\'authentification si disponibles', async () => {
      const mockToken = 'mock-jwt-token';
      authManager.getToken = jest.fn().mockReturnValue(mockToken);

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ success: true })
      });

      await apiClient.get('/protected');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/protected',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockToken}`
          })
        })
      );
    });
  });

  describe('Méthodes HTTP', () => {
    test('effectue une requête GET', async () => {
      const mockResponse = { data: 'test data' };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      });

      const result = await apiClient.get('/api/test');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/test',
        expect.objectContaining({
          method: 'GET'
        })
      );
      expect(result).toEqual(mockResponse);
    });

    test('effectue une requête POST avec données', async () => {
      const postData = { message: 'Hello JARVIS' };
      const mockResponse = { status: 'sent' };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      });

      const result = await apiClient.post('/api/chat', postData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/chat',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData)
        })
      );
      expect(result).toEqual(mockResponse);
    });

    test('effectue une requête PUT', async () => {
      const putData = { name: 'Updated Name' };
      const mockResponse = { updated: true };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      });

      const result = await apiClient.put('/api/user/123', putData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/user/123',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData)
        })
      );
      expect(result).toEqual(mockResponse);
    });

    test('effectue une requête DELETE', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ deleted: true })
      });

      const result = await apiClient.delete('/api/user/123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/user/123',
        expect.objectContaining({
          method: 'DELETE'
        })
      );
      expect(result).toEqual({ deleted: true });
    });
  });

  describe('Gestion des paramètres de requête', () => {
    test('ajoute les paramètres de requête à l\'URL', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ results: [] })
      });

      await apiClient.get('/api/search', { 
        params: { q: 'test query', limit: 10, offset: 0 } 
      });

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/search?q=test%20query&limit=10&offset=0',
        expect.any(Object)
      );
    });

    test('encode correctement les paramètres spéciaux', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({})
      });

      await apiClient.get('/api/search', { 
        params: { 
          query: 'special chars: @#$%^&*()',
          filter: 'category=AI & ML'
        } 
      });

      const expectedUrl = 'http://localhost:8001/api/search?query=special%20chars%3A%20%40%23%24%25%5E%26*()&filter=category%3DAI%20%26%20ML';
      expect(fetch).toHaveBeenCalledWith(expectedUrl, expect.any(Object));
    });
  });

  describe('Gestion des erreurs HTTP', () => {
    test('lance une erreur pour les statuts 4xx', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: jest.fn().mockResolvedValue({ error: 'Resource not found' })
      });

      await expect(apiClient.get('/api/nonexistent')).rejects.toThrow('404: Not Found');
    });

    test('lance une erreur pour les statuts 5xx', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: jest.fn().mockResolvedValue({ error: 'Server error' })
      });

      await expect(apiClient.get('/api/error')).rejects.toThrow('500: Internal Server Error');
    });

    test('gère les erreurs de réseau', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/api/test')).rejects.toThrow('Network error');
    });

    test('gère les timeouts', async () => {
      jest.useFakeTimers();
      
      const slowPromise = new Promise((resolve) => {
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ data: 'slow response' })
        }), 10000);
      });
      
      fetch.mockReturnValueOnce(slowPromise);

      const requestPromise = apiClient.get('/api/slow', { timeout: 5000 });

      jest.advanceTimersByTime(5000);

      await expect(requestPromise).rejects.toThrow('Request timeout');

      jest.useRealTimers();
    });
  });

  describe('Intercepteurs de requête', () => {
    test('applique les intercepteurs de requête', async () => {
      const requestInterceptor = jest.fn((config) => ({
        ...config,
        headers: { ...config.headers, 'X-Custom-Header': 'test-value' }
      }));

      apiClient.addRequestInterceptor(requestInterceptor);

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({})
      });

      await apiClient.get('/api/test');

      expect(requestInterceptor).toHaveBeenCalled();
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'test-value'
          })
        })
      );
    });

    test('applique les intercepteurs de réponse', async () => {
      const responseInterceptor = jest.fn((response) => ({
        ...response,
        timestamp: Date.now()
      }));

      apiClient.addResponseInterceptor(responseInterceptor);

      const mockResponse = { data: 'test' };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse)
      });

      const result = await apiClient.get('/api/test');

      expect(responseInterceptor).toHaveBeenCalled();
      expect(result).toHaveProperty('timestamp');
    });
  });
});

describe('WebSocket Manager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockWebSocket.addEventListener.mockClear();
    mockWebSocket.removeEventListener.mockClear();
  });

  describe('Connexion WebSocket', () => {
    test('établit une connexion WebSocket', () => {
      wsManager.connect('ws://localhost:8001/ws');

      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8001/ws');
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('open', expect.any(Function));
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('close', expect.any(Function));
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
    });

    test('gère les événements de connexion', () => {
      const onConnect = jest.fn();
      wsManager.on('connect', onConnect);

      wsManager.connect('ws://localhost:8001/ws');

      // Simuler l'événement open
      const openHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'open')[1];
      openHandler(new Event('open'));

      expect(onConnect).toHaveBeenCalled();
    });

    test('gère les messages entrants', () => {
      const onMessage = jest.fn();
      wsManager.on('message', onMessage);

      wsManager.connect('ws://localhost:8001/ws');

      // Simuler un message
      const messageHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'message')[1];
      
      const testMessage = { type: 'test', data: 'hello' };
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(testMessage)
      });

      messageHandler(messageEvent);

      expect(onMessage).toHaveBeenCalledWith(testMessage);
    });

    test('gère les erreurs de connexion', () => {
      const onError = jest.fn();
      wsManager.on('error', onError);

      wsManager.connect('ws://localhost:8001/ws');

      // Simuler une erreur
      const errorHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'error')[1];
      
      const errorEvent = new Event('error');
      errorHandler(errorEvent);

      expect(onError).toHaveBeenCalledWith(errorEvent);
    });

    test('gère les déconnexions', () => {
      const onDisconnect = jest.fn();
      wsManager.on('disconnect', onDisconnect);

      wsManager.connect('ws://localhost:8001/ws');

      // Simuler une déconnexion
      const closeHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'close')[1];
      
      const closeEvent = new CloseEvent('close', { 
        code: 1000, 
        reason: 'Normal closure' 
      });
      closeHandler(closeEvent);

      expect(onDisconnect).toHaveBeenCalledWith({
        code: 1000,
        reason: 'Normal closure'
      });
    });
  });

  describe('Envoi de messages', () => {
    test('envoie des messages JSON', () => {
      wsManager.connect('ws://localhost:8001/ws');
      
      const message = { type: 'chat', content: 'Hello JARVIS' };
      wsManager.send(message);

      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message));
    });

    test('met en file d\'attente les messages si non connecté', () => {
      mockWebSocket.readyState = WebSocket.CONNECTING;

      const message = { type: 'chat', content: 'Queued message' };
      wsManager.send(message);

      // Le message ne devrait pas être envoyé immédiatement
      expect(mockWebSocket.send).not.toHaveBeenCalled();

      // Simuler la connexion
      mockWebSocket.readyState = WebSocket.OPEN;
      const openHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'open')[1];
      openHandler(new Event('open'));

      // Le message en file d'attente devrait être envoyé
      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message));
    });

    test('gère les erreurs d\'envoi', () => {
      wsManager.connect('ws://localhost:8001/ws');
      mockWebSocket.send.mockImplementation(() => {
        throw new Error('Send failed');
      });

      const onError = jest.fn();
      wsManager.on('sendError', onError);

      const message = { type: 'test' };
      wsManager.send(message);

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Send failed' })
      );
    });
  });

  describe('Reconnexion automatique', () => {
    test('tente de se reconnecter après une déconnexion', () => {
      jest.useFakeTimers();
      
      wsManager.connect('ws://localhost:8001/ws', { autoReconnect: true });

      // Simuler une déconnexion inattendue
      const closeHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'close')[1];
      
      const closeEvent = new CloseEvent('close', { 
        code: 1006, // Abnormal closure
        reason: 'Connection lost' 
      });
      closeHandler(closeEvent);

      // Avancer le temps pour déclencher la reconnexion
      jest.advanceTimersByTime(1000);

      expect(global.WebSocket).toHaveBeenCalledTimes(2);

      jest.useRealTimers();
    });

    test('respecte le délai de reconnexion exponentiel', () => {
      jest.useFakeTimers();
      
      wsManager.connect('ws://localhost:8001/ws', { 
        autoReconnect: true,
        reconnectDelay: 1000
      });

      // Première déconnexion
      const closeHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'close')[1];
      
      closeHandler(new CloseEvent('close', { code: 1006 }));
      
      // Première tentative après 1s
      jest.advanceTimersByTime(1000);
      expect(global.WebSocket).toHaveBeenCalledTimes(2);

      // Simuler un échec de reconnexion
      closeHandler(new CloseEvent('close', { code: 1006 }));

      // Deuxième tentative après 2s (délai doublé)
      jest.advanceTimersByTime(2000);
      expect(global.WebSocket).toHaveBeenCalledTimes(3);

      jest.useRealTimers();
    });

    test('limite le nombre de tentatives de reconnexion', () => {
      jest.useFakeTimers();
      
      wsManager.connect('ws://localhost:8001/ws', { 
        autoReconnect: true,
        maxReconnectAttempts: 3
      });

      const closeHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'close')[1];

      // Simuler 4 déconnexions consécutives
      for (let i = 0; i < 4; i++) {
        closeHandler(new CloseEvent('close', { code: 1006 }));
        jest.advanceTimersByTime(Math.pow(2, i) * 1000);
      }

      // Seulement 4 tentatives au total (1 initiale + 3 reconnexions)
      expect(global.WebSocket).toHaveBeenCalledTimes(4);

      jest.useRealTimers();
    });
  });

  describe('Heartbeat et keep-alive', () => {
    test('envoie des pings périodiques', () => {
      jest.useFakeTimers();
      
      wsManager.connect('ws://localhost:8001/ws', { 
        heartbeat: true,
        heartbeatInterval: 30000
      });

      // Simuler la connexion
      const openHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'open')[1];
      openHandler(new Event('open'));

      // Avancer le temps pour déclencher le heartbeat
      jest.advanceTimersByTime(30000);

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'ping', timestamp: expect.any(Number) })
      );

      jest.useRealTimers();
    });

    test('détecte les connexions mortes', () => {
      jest.useFakeTimers();
      
      const onConnectionDead = jest.fn();
      wsManager.on('connectionDead', onConnectionDead);

      wsManager.connect('ws://localhost:8001/ws', { 
        heartbeat: true,
        heartbeatInterval: 30000,
        heartbeatTimeout: 10000
      });

      // Simuler la connexion
      const openHandler = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'open')[1];
      openHandler(new Event('open'));

      // Envoyer un ping
      jest.advanceTimersByTime(30000);

      // Ne pas recevoir de pong dans le délai imparti
      jest.advanceTimersByTime(10000);

      expect(onConnectionDead).toHaveBeenCalled();

      jest.useRealTimers();
    });
  });
});

describe('Gestionnaire d\'authentification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
  });

  describe('Gestion des tokens', () => {
    test('stocke le token d\'authentification', () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
      
      authManager.setToken(token);

      expect(localStorageMock.setItem).toHaveBeenCalledWith('jarvis_auth_token', token);
    });

    test('récupère le token stocké', () => {
      const token = 'stored_token_123';
      localStorageMock.getItem.mockReturnValue(token);

      const retrievedToken = authManager.getToken();

      expect(localStorageMock.getItem).toHaveBeenCalledWith('jarvis_auth_token');
      expect(retrievedToken).toBe(token);
    });

    test('supprime le token lors de la déconnexion', () => {
      authManager.clearToken();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('jarvis_auth_token');
    });

    test('vérifie la validité du token JWT', () => {
      // Token JWT valide avec exp dans le futur
      const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.Lp-38mkSzgIsOW5u_7yBsOCJFGS5xfBbKMkNlmQrQLk';
      
      expect(authManager.isTokenValid(validToken)).toBe(true);
    });

    test('détecte les tokens expirés', () => {
      // Token JWT expiré (exp dans le passé)
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o';
      
      expect(authManager.isTokenValid(expiredToken)).toBe(false);
    });

    test('décode les informations du token', () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4ifQ.EfiMHWOZ3CovKCRA8CIZLVnSGfBqFbE9U3Y5ZPMQHJ4';
      
      const decoded = authManager.decodeToken(token);

      expect(decoded).toEqual({
        sub: '1234567890',
        name: 'John Doe',
        iat: 1516239022,
        role: 'admin'
      });
    });
  });

  describe('Login et logout', () => {
    test('effectue la connexion avec succès', async () => {
      const credentials = { username: 'jarvis', password: 'stark_industries' };
      const authResponse = { 
        token: 'auth_token_123', 
        user: { id: 1, username: 'jarvis', role: 'admin' }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(authResponse)
      });

      const result = await authManager.login(credentials);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(credentials)
        })
      );

      expect(localStorageMock.setItem).toHaveBeenCalledWith('jarvis_auth_token', 'auth_token_123');
      expect(result).toEqual(authResponse);
    });

    test('gère les erreurs de connexion', async () => {
      const credentials = { username: 'wrong', password: 'credentials' };

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ error: 'Invalid credentials' })
      });

      await expect(authManager.login(credentials)).rejects.toThrow('401');
    });

    test('effectue la déconnexion', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ success: true })
      });

      await authManager.logout();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/auth/logout',
        expect.objectContaining({
          method: 'POST'
        })
      );

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('jarvis_auth_token');
    });

    test('rafraîchit le token automatiquement', async () => {
      const newToken = 'refreshed_token_456';
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ token: newToken })
      });

      const result = await authManager.refreshToken();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/auth/refresh',
        expect.objectContaining({
          method: 'POST'
        })
      );

      expect(localStorageMock.setItem).toHaveBeenCalledWith('jarvis_auth_token', newToken);
      expect(result).toBe(newToken);
    });
  });

  describe('Permissions et rôles', () => {
    test('vérifie les permissions utilisateur', () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4iLCJwZXJtaXNzaW9ucyI6WyJyZWFkIiwid3JpdGUiLCJkZWxldGUiXX0.UqVjKKmBZZMVYKR3yNHayRNwOYVvqSGxQoNNFz-Vn9Y';
      
      localStorageMock.getItem.mockReturnValue(token);

      expect(authManager.hasPermission('read')).toBe(true);
      expect(authManager.hasPermission('write')).toBe(true);
      expect(authManager.hasPermission('admin')).toBe(false);
    });

    test('vérifie les rôles utilisateur', () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4ifQ.EfiMHWOZ3CovKCRA8CIZLVnSGfBqFbE9U3Y5ZPMQHJ4';
      
      localStorageMock.getItem.mockReturnValue(token);

      expect(authManager.hasRole('admin')).toBe(true);
      expect(authManager.hasRole('user')).toBe(false);
    });
  });
});

describe('Gestionnaire de retry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Politique de retry', () => {
    test('retry les requêtes échouées', async () => {
      let callCount = 0;
      
      fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: jest.fn().mockResolvedValue({ success: true })
        });

      const result = await retryManager.executeWithRetry(
        () => apiClient.get('/api/test'),
        { maxRetries: 3, delay: 100 }
      );

      expect(fetch).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ success: true });
    });

    test('respecte le nombre maximum de tentatives', async () => {
      fetch.mockRejectedValue(new Error('Persistent error'));

      await expect(
        retryManager.executeWithRetry(
          () => apiClient.get('/api/test'),
          { maxRetries: 2, delay: 10 }
        )
      ).rejects.toThrow('Persistent error');

      expect(fetch).toHaveBeenCalledTimes(3); // 1 initial + 2 retries
    });

    test('utilise le délai exponentiel', async () => {
      jest.useFakeTimers();
      
      fetch.mockRejectedValue(new Error('Always fails'));

      const promise = retryManager.executeWithRetry(
        () => apiClient.get('/api/test'),
        { maxRetries: 2, delay: 1000, exponentialBackoff: true }
      );

      // Première tentative immédiate
      await Promise.resolve();
      expect(fetch).toHaveBeenCalledTimes(1);

      // Deuxième tentative après 1s
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
      expect(fetch).toHaveBeenCalledTimes(2);

      // Troisième tentative après 2s
      jest.advanceTimersByTime(2000);
      await Promise.resolve();
      expect(fetch).toHaveBeenCalledTimes(3);

      jest.useRealTimers();
    });

    test('ajoute du jitter au délai', async () => {
      jest.useFakeTimers();
      jest.spyOn(Math, 'random').mockReturnValue(0.5); // Jitter de 50%
      
      fetch.mockRejectedValue(new Error('Always fails'));

      const promise = retryManager.executeWithRetry(
        () => apiClient.get('/api/test'),
        { maxRetries: 1, delay: 1000, jitter: true }
      );

      await Promise.resolve();
      
      // Le délai devrait être ~500ms (50% de 1000ms)
      jest.advanceTimersByTime(500);
      await Promise.resolve();
      expect(fetch).toHaveBeenCalledTimes(2);

      Math.random.mockRestore();
      jest.useRealTimers();
    });
  });

  describe('Conditions de retry', () => {
    test('retry seulement pour certains types d\'erreurs', async () => {
      const retryCondition = (error) => {
        return error.message.includes('Network') || 
               error.message.includes('timeout');
      };

      // Erreur qui devrait être retryée
      fetch.mockRejectedValueOnce(new Error('Network timeout'));
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ success: true })
      });

      const result = await retryManager.executeWithRetry(
        () => apiClient.get('/api/test'),
        { maxRetries: 1, retryCondition }
      );

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ success: true });
    });

    test('ne retry pas pour certains types d\'erreurs', async () => {
      const retryCondition = (error) => {
        return !error.message.includes('Authentication');
      };

      fetch.mockRejectedValueOnce(new Error('Authentication failed'));

      await expect(
        retryManager.executeWithRetry(
          () => apiClient.get('/api/test'),
          { maxRetries: 2, retryCondition }
        )
      ).rejects.toThrow('Authentication failed');

      expect(fetch).toHaveBeenCalledTimes(1); // Pas de retry
    });

    test('retry pour les erreurs 5xx mais pas 4xx', async () => {
      const retryCondition = (error) => {
        const status = error.status;
        return status >= 500 && status < 600;
      };

      // Erreur 500 - devrait être retryée
      fetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        })
        .mockResolvedValueOnce({
          ok: true,
          json: jest.fn().mockResolvedValue({ success: true })
        });

      const error500 = new Error('500: Internal Server Error');
      error500.status = 500;

      let callCount = 0;
      const mockFunction = jest.fn().mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          throw error500;
        }
        return Promise.resolve({ success: true });
      });

      const result = await retryManager.executeWithRetry(
        mockFunction,
        { maxRetries: 1, retryCondition }
      );

      expect(mockFunction).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ success: true });
    });
  });
});

describe('Gestionnaire d\'erreurs global', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Interception d\'erreurs', () => {
    test('intercepte et transforme les erreurs d\'API', async () => {
      const onError = jest.fn();
      errorHandler.setErrorCallback(onError);

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: jest.fn().mockResolvedValue({ 
          error: 'Database connection failed',
          code: 'DB_ERROR'
        })
      });

      try {
        await apiClient.get('/api/test');
      } catch (error) {
        // L'erreur devrait être interceptée
      }

      expect(onError).toHaveBeenCalledWith({
        type: 'API_ERROR',
        status: 500,
        message: 'Internal Server Error',
        details: {
          error: 'Database connection failed',
          code: 'DB_ERROR'
        },
        url: 'http://localhost:8001/api/test',
        timestamp: expect.any(Number)
      });
    });

    test('intercepte les erreurs WebSocket', () => {
      const onError = jest.fn();
      errorHandler.setErrorCallback(onError);

      wsManager.connect('ws://localhost:8001/ws');

      // Simuler une erreur WebSocket
      const errorHandler_ws = mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'error')[1];
      
      const errorEvent = new Event('error');
      errorEvent.type = 'error';
      errorEvent.message = 'WebSocket connection failed';

      errorHandler_ws(errorEvent);

      expect(onError).toHaveBeenCalledWith({
        type: 'WEBSOCKET_ERROR',
        message: 'WebSocket connection failed',
        event: errorEvent,
        timestamp: expect.any(Number)
      });
    });

    test('catégorise les erreurs par type', () => {
      const errors = [
        { status: 401, message: 'Unauthorized' },
        { status: 403, message: 'Forbidden' },
        { status: 404, message: 'Not Found' },
        { status: 500, message: 'Internal Server Error' },
        { message: 'Network Error' }
      ];

      const categorized = errors.map(error => 
        errorHandler.categorizeError(error)
      );

      expect(categorized).toEqual([
        { category: 'AUTHENTICATION', severity: 'medium' },
        { category: 'AUTHORIZATION', severity: 'medium' },
        { category: 'NOT_FOUND', severity: 'low' },
        { category: 'SERVER_ERROR', severity: 'high' },
        { category: 'NETWORK_ERROR', severity: 'high' }
      ]);
    });
  });

  describe('Notifications d\'erreur', () => {
    test('affiche des notifications pour les erreurs critiques', () => {
      const mockNotification = jest.fn();
      errorHandler.setNotificationHandler(mockNotification);

      const criticalError = {
        type: 'API_ERROR',
        status: 500,
        message: 'Critical system error',
        severity: 'critical'
      };

      errorHandler.handleError(criticalError);

      expect(mockNotification).toHaveBeenCalledWith({
        type: 'error',
        title: 'System Error',
        message: 'Critical system error',
        severity: 'critical',
        persistent: true
      });
    });

    test('groupe les erreurs similaires', () => {
      const mockNotification = jest.fn();
      errorHandler.setNotificationHandler(mockNotification);

      // Simuler plusieurs erreurs identiques
      for (let i = 0; i < 5; i++) {
        errorHandler.handleError({
          type: 'API_ERROR',
          status: 429,
          message: 'Rate limit exceeded'
        });
      }

      expect(mockNotification).toHaveBeenCalledWith({
        type: 'warning',
        title: 'Rate Limit',
        message: 'Rate limit exceeded (5 occurrences)',
        severity: 'medium',
        grouped: true
      });
    });
  });

  describe('Reporting d\'erreurs', () => {
    test('envoie les erreurs au service de monitoring', async () => {
      const reportingEndpoint = 'http://localhost:8001/api/errors/report';
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ reported: true })
      });

      const error = {
        type: 'JAVASCRIPT_ERROR',
        message: 'Uncaught TypeError',
        stack: 'Error stack trace...',
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: Date.now()
      };

      await errorHandler.reportError(error);

      expect(fetch).toHaveBeenCalledWith(
        reportingEndpoint,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(error)
        })
      );
    });

    test('inclut le contexte utilisateur dans les rapports', async () => {
      const mockGetUserContext = jest.fn().mockReturnValue({
        userId: 'user123',
        sessionId: 'session456',
        userAgent: 'Test Browser',
        timestamp: Date.now()
      });

      errorHandler.setUserContextProvider(mockGetUserContext);

      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ reported: true })
      });

      const error = { type: 'TEST_ERROR', message: 'Test error' };
      await errorHandler.reportError(error);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({
            ...error,
            userContext: {
              userId: 'user123',
              sessionId: 'session456',
              userAgent: 'Test Browser',
              timestamp: expect.any(Number)
            }
          })
        })
      );
    });
  });
});

// Tests d'intégration bout en bout
describe('Intégration API complète', () => {
  test('workflow de chat complet avec WebSocket', async () => {
    // Établir la connexion WebSocket
    wsManager.connect('ws://localhost:8001/ws');
    
    // Simuler la connexion réussie
    const openHandler = mockWebSocket.addEventListener.mock.calls
      .find(call => call[0] === 'open')[1];
    openHandler(new Event('open'));

    // Envoyer un message de chat
    const chatMessage = {
      type: 'chat_message',
      content: 'Hello JARVIS, what is the system status?'
    };

    wsManager.send(chatMessage);
    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(chatMessage));

    // Simuler la réponse du serveur
    const messageHandler = mockWebSocket.addEventListener.mock.calls
      .find(call => call[0] === 'message')[1];
    
    const response = {
      type: 'chat_response',
      content: 'All systems are operating normally, sir.',
      timestamp: Date.now()
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(response)
    });

    let receivedMessage;
    wsManager.on('message', (message) => {
      receivedMessage = message;
    });

    messageHandler(messageEvent);

    expect(receivedMessage).toEqual(response);
  });

  test('gestion de l\'authentification avec retry automatique', async () => {
    // Simuler un token expiré
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o';
    localStorageMock.getItem.mockReturnValue(expiredToken);

    // Première requête échoue avec 401
    fetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ error: 'Token expired' })
      })
      // Refresh token réussit
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ token: 'new_fresh_token' })
      })
      // Retry de la requête originale réussit
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ data: 'protected data' })
      });

    const result = await apiClient.get('/api/protected');

    expect(result).toEqual({ data: 'protected data' });
    expect(localStorageMock.setItem).toHaveBeenCalledWith('jarvis_auth_token', 'new_fresh_token');
  });

  test('récupération d\'erreur avec fallback gracieux', async () => {
    // Simuler une panne de service primaire
    fetch.mockRejectedValue(new Error('Service unavailable'));

    // Configurer un service de fallback
    apiClient.setFallbackURL('http://backup.localhost:8002');

    // Le client devrait automatiquement utiliser le fallback
    fetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ data: 'fallback data', source: 'backup' })
    });

    const result = await apiClient.get('/api/data');

    expect(result).toEqual({ data: 'fallback data', source: 'backup' });
  });
});