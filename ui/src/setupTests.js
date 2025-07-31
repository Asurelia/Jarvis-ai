/**
 * 🧪 Configuration des tests pour JARVIS UI
 * Setup global pour Jest et React Testing Library
 */

import '@testing-library/jest-dom';

// Mock des APIs Web non disponibles dans jsdom
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock de l'API WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1,
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
}));

// Mock de l'API Web Audio
global.AudioContext = jest.fn().mockImplementation(() => ({
  createAnalyser: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    fftSize: 2048,
    frequencyBinCount: 1024,
    getByteFrequencyData: jest.fn(),
    getByteTimeDomainData: jest.fn(),
  })),
  createGain: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    gain: { value: 1 },
  })),
  createMediaStreamSource: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
  })),
  resume: jest.fn().mockResolvedValue(),
  close: jest.fn().mockResolvedValue(),
  state: 'running',
  sampleRate: 44100,
}));

global.webkitAudioContext = global.AudioContext;

// Mock de l'API getUserMedia
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn().mockResolvedValue({
      getTracks: jest.fn(() => [
        {
          stop: jest.fn(),
          enabled: true,
          readyState: 'live',
        },
      ]),
    }),
  },
  writable: true,
});

// Mock de requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 16));
global.cancelAnimationFrame = jest.fn();

// Mock de HTMLCanvasElement
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
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
  font: '10px sans-serif',
  textAlign: 'start',
  textBaseline: 'alphabetic',
  fillText: jest.fn(),
  strokeText: jest.fn(),
  measureText: jest.fn(() => ({ width: 50 })),
  createLinearGradient: jest.fn(() => ({
    addColorStop: jest.fn(),
  })),
  createRadialGradient: jest.fn(() => ({
    addColorStop: jest.fn(),
  })),
}));

// Mock de HTMLMediaElement
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: jest.fn().mockResolvedValue(),
});

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  writable: true,
  value: jest.fn(),
});

// Mock des propriétés CSS non supportées par jsdom
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
    display: 'none',
    appearance: ['-webkit-appearance'],
  }),
});

// Mock de localStorage et sessionStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Mock de window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock de fetch global
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
  })
);

// Mock des variables d'environnement de test
process.env.REACT_APP_API_URL = 'http://localhost:8001';
process.env.REACT_APP_WS_URL = 'ws://localhost:8001/ws';
process.env.NODE_ENV = 'test';

// Configuration globale des timeouts pour les tests
jest.setTimeout(10000);

// Suppression des erreurs console pendant les tests
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('componentWillReceiveProps') ||
       args[0].includes('componentWillMount') ||
       args[0].includes('componentWillUpdate'))
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Nettoyage après chaque test
afterEach(() => {
  jest.clearAllMocks();
  localStorageMock.clear();
  sessionStorageMock.clear();
});

// Helper pour créer des mocks de données de test
global.createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@jarvis.ai',
  role: 'user',
  ...overrides,
});

global.createMockMessage = (overrides = {}) => ({
  id: Date.now(),
  type: 'user',
  content: 'Test message',
  timestamp: new Date().toISOString(),
  ...overrides,
});

global.createMockSystemStats = (overrides = {}) => ({
  cpu: 45,
  memory: 67,
  gpu: {
    temperature: 65,
    utilization: 78,
    memory: 8372,
  },
  network: 'stable',
  ...overrides,
});

// Helper pour les tests d'accessibilité 
global.expectAccessibleElement = (element) => {
  expect(element).toHaveAttribute('role');
  if (element.tagName.toLowerCase() === 'button') {
    expect(element).not.toHaveAttribute('aria-disabled', 'true');
  }
  if (element.hasAttribute('aria-describedby')) {
    const describedById = element.getAttribute('aria-describedby');
    expect(document.getElementById(describedById)).toBeInTheDocument();
  }
};

// Helper pour attendre les mises à jour asynchrones
global.waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Configuration des matchers personnalisés
expect.extend({
  toHaveValidJarvisTheme(received) {
    const validThemes = ['jarvis', 'friday', 'edith'];
    const pass = validThemes.includes(received);
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid JARVIS theme`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid JARVIS theme (${validThemes.join(', ')})`,
        pass: false,
      };
    }
  },
  
  toHaveValidApiResponse(received) {
    const pass = received && 
                 typeof received === 'object' && 
                 received.hasOwnProperty('success') &&
                 typeof received.success === 'boolean';
    
    if (pass) {
      return {
        message: () => `expected ${JSON.stringify(received)} not to be a valid API response`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${JSON.stringify(received)} to have a valid API response structure with 'success' boolean property`,
        pass: false,
      };
    }
  },
});

// Gestion des erreurs React non gérées pendant les tests
const originalConsoleError = console.error;
console.error = (...args) => {
  // Ignorer certaines erreurs React communes dans les tests
  if (
    args[0] &&
    typeof args[0] === 'string' &&
    (args[0].includes('Warning: An invalid form control') ||
     args[0].includes('Warning: Failed prop type') ||
     args[0].includes('The above error occurred'))
  ) {
    return;
  }
  originalConsoleError(...args);
};

// Configuration pour les tests de performance
global.markTestStart = (testName) => {
  if (global.performance && global.performance.mark) {
    global.performance.mark(`${testName}-start`);
  }
};

global.markTestEnd = (testName) => {
  if (global.performance && global.performance.mark && global.performance.measure) {
    global.performance.mark(`${testName}-end`);
    global.performance.measure(testName, `${testName}-start`, `${testName}-end`);
  }
};

// Configuration des timeouts spécifiques par type de test
global.testTimeouts = {
  unit: 5000,
  integration: 10000,
  e2e: 30000,
};

// Mock des composants Three.js pour les tests
jest.mock('three', () => ({
  Scene: jest.fn(),
  PerspectiveCamera: jest.fn(),
  WebGLRenderer: jest.fn(() => ({
    setSize: jest.fn(),
    render: jest.fn(),
    domElement: document.createElement('canvas'),
  })),
  Mesh: jest.fn(),
  SphereGeometry: jest.fn(),
  MeshBasicMaterial: jest.fn(),
  Color: jest.fn(),
}));

// Mock des hooks personnalisés pour les tests
jest.mock('../hooks/useJarvisAPI', () => ({
  useJarvisAPI: () => ({
    sendMessage: jest.fn().mockResolvedValue({ success: true }),
    isConnected: true,
    connectionStatus: 'connected',
  }),
}));

jest.mock('../hooks/useAudioAnalyzer', () => ({
  useAudioAnalyzer: () => ({
    audioData: null,
    isAnalyzing: false,
    startAnalysis: jest.fn(),
    stopAnalysis: jest.fn(),
  }),
}));

// Configuration finale
console.log('🧪 JARVIS UI Test Environment initialized');
console.log(`📦 Running in ${process.env.NODE_ENV} mode`);
console.log(`🔗 API URL: ${process.env.REACT_APP_API_URL}`);
console.log(`🔌 WebSocket URL: ${process.env.REACT_APP_WS_URL}`);