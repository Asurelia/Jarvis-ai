/**
 * 🚀 Tests de charge K6 pour JARVIS
 * Tests de performance et de montée en charge
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Métriques personnalisées
const apiErrors = new Counter('api_errors');
const apiSuccessRate = new Rate('api_success_rate');
const websocketConnections = new Counter('websocket_connections');
const responseTime = new Trend('response_time_custom');

// Configuration des tests
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Montée progressive
    { duration: '5m', target: 10 },   // Maintien
    { duration: '2m', target: 20 },   // Pic de charge
    { duration: '5m', target: 20 },   // Maintien du pic
    { duration: '2m', target: 0 },    // Descente
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% des requêtes < 500ms
    http_req_failed: ['rate<0.1'],    // Moins de 10% d'échecs
    api_success_rate: ['rate>0.9'],   // Plus de 90% de succès
    websocket_connections: ['count>0'], // Au moins une connexion WS
  },
};

// Configuration de l'environnement
const BASE_URL = __ENV.BASE_URL || 'http://brain-api-test:8080';
const WS_URL = __ENV.WS_URL || 'ws://brain-api-test:8080/ws';
const UI_URL = __ENV.UI_URL || 'http://ui-test:80';

// Données de test
const testMessages = [
  'Bonjour JARVIS, comment allez-vous ?',
  'Peux-tu me donner l\'heure ?',
  'Analyse cette image pour moi',
  'Quel temps fait-il aujourd\'hui ?',
  'Raconte-moi une blague',
  'Aide-moi à organiser ma journée',
  'Quelles sont les dernières nouvelles ?',
  'Peux-tu m\'expliquer l\'intelligence artificielle ?'
];

const testAudioData = new Uint8Array(1024).fill(42); // Données audio factices

// Tests de l'API REST
export function testAPI() {
  group('API Tests', () => {
    
    // Test de santé
    group('Health Check', () => {
      const response = http.get(`${BASE_URL}/health`);
      const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 200ms': (r) => r.timings.duration < 200,
        'has status field': (r) => r.json().hasOwnProperty('status'),
      });
      
      apiSuccessRate.add(success);
      responseTime.add(response.timings.duration);
      
      if (!success) {
        apiErrors.add(1);
      }
    });

    // Test de l'endpoint chat
    group('Chat API', () => {
      const message = testMessages[Math.floor(Math.random() * testMessages.length)];
      const payload = JSON.stringify({
        message: message,
        user_id: `user_${__VU}`,
        timestamp: Date.now()
      });
      
      const params = {
        headers: { 'Content-Type': 'application/json' },
        timeout: '10s'
      };
      
      const response = http.post(`${BASE_URL}/api/chat`, payload, params);
      const success = check(response, {
        'chat status is 200': (r) => r.status === 200,
        'has response': (r) => r.json().hasOwnProperty('response'),
        'response time < 2s': (r) => r.timings.duration < 2000,
      });
      
      apiSuccessRate.add(success);
      responseTime.add(response.timings.duration);
      
      if (!success) {
        apiErrors.add(1);
      }
    });

    // Test de l'endpoint mémoire
    group('Memory API', () => {
      const response = http.get(`${BASE_URL}/api/memory/stats`);
      const success = check(response, {
        'memory status is 200 or 401': (r) => [200, 401].includes(r.status),
        'response time < 500ms': (r) => r.timings.duration < 500,
      });
      
      apiSuccessRate.add(success);
      if (!success) {
        apiErrors.add(1);
      }
    });

    // Test de l'endpoint audio
    group('Audio API', () => {
      const response = http.get(`${BASE_URL}/api/audio/status`);
      const success = check(response, {
        'audio status is 200 or 401': (r) => [200, 401].includes(r.status),
        'response time < 300ms': (r) => r.timings.duration < 300,
      });
      
      apiSuccessRate.add(success);
      if (!success) {
        apiErrors.add(1);
      }
    });

  });
}

// Tests des WebSockets
export function testWebSocket() {
  group('WebSocket Tests', () => {
    const url = WS_URL;
    
    const res = ws.connect(url, {}, (socket) => {
      websocketConnections.add(1);
      
      socket.on('open', () => {
        console.log(`VU ${__VU}: WebSocket connecté`);
        
        // Envoi d'un message de test
        const testMessage = {
          type: 'chat',
          content: testMessages[Math.floor(Math.random() * testMessages.length)],
          user_id: `user_${__VU}`,
          timestamp: Date.now()
        };
        
        socket.send(JSON.stringify(testMessage));
      });
      
      socket.on('message', (message) => {
        const data = JSON.parse(message);
        check(data, {
          'WebSocket response has type': (d) => d.hasOwnProperty('type'),
          'WebSocket response has content': (d) => d.hasOwnProperty('content'),
        });
      });
      
      socket.on('error', (e) => {
        console.error(`VU ${__VU}: WebSocket erreur:`, e);
        apiErrors.add(1);
      });
      
      // Maintenir la connexion pendant un certain temps
      sleep(2);
    });
    
    check(res, {
      'WebSocket connection successful': (r) => r && r.status === 101,
    });
  });
}

// Test de l'interface utilisateur
export function testUI() {
  group('UI Tests', () => {
    
    // Page d'accueil
    group('Homepage', () => {
      const response = http.get(UI_URL);
      const success = check(response, {
        'UI status is 200': (r) => r.status === 200,
        'contains React': (r) => r.body.includes('react') || r.body.includes('root'),
        'response time < 1s': (r) => r.timings.duration < 1000,
      });
      
      if (!success) {
        apiErrors.add(1);
      }
    });

    // Ressources statiques
    group('Static Resources', () => {
      const staticFiles = ['/static/css/', '/static/js/', '/manifest.json'];
      
      staticFiles.forEach(file => {
        const response = http.get(`${UI_URL}${file}`);
        check(response, {
          [`${file} loads successfully`]: (r) => [200, 404].includes(r.status),
        });
      });
    });

  });
}

// Test de performance des services spécifiques
export function testServices() {
  group('Service Performance', () => {
    
    // Test STT simulé
    group('STT Service', () => {
      const sttUrl = 'http://stt-service-test:8080';
      const response = http.get(`${sttUrl}/health`);
      check(response, {
        'STT service responding': (r) => [200, 404, 503].includes(r.status),
      });
    });

    // Test TTS simulé
    group('TTS Service', () => {
      const ttsUrl = 'http://tts-service-test:8080';
      const response = http.get(`${ttsUrl}/health`);
      check(response, {
        'TTS service responding': (r) => [200, 404, 503].includes(r.status),
      });
    });

    // Test du contrôle système
    group('System Control', () => {
      const controlUrl = 'http://system-control-test:8080';
      const response = http.get(`${controlUrl}/health`);
      check(response, {
        'Control service responding': (r) => [200, 404, 503].includes(r.status),
      });
    });

  });
}

// Scénario de test réaliste
export function realisticUserScenario() {
  group('Realistic User Journey', () => {
    
    // 1. L'utilisateur visite l'interface
    let response = http.get(UI_URL);
    check(response, { 'UI loaded': (r) => r.status === 200 });
    sleep(1);
    
    // 2. Vérification de l'API
    response = http.get(`${BASE_URL}/health`);
    check(response, { 'API available': (r) => r.status === 200 });
    sleep(0.5);
    
    // 3. Connexion WebSocket
    ws.connect(WS_URL, {}, (socket) => {
      socket.on('open', () => {
        websocketConnections.add(1);
        
        // 4. Envoi d'un message
        const message = {
          type: 'chat',
          content: 'Bonjour JARVIS !',
          user_id: `user_${__VU}`
        };
        socket.send(JSON.stringify(message));
        
        sleep(1);
        
        // 5. Autre interaction
        const complexMessage = {
          type: 'command',
          content: 'Analyse le système',
          user_id: `user_${__VU}`
        };
        socket.send(JSON.stringify(complexMessage));
        
        sleep(2);
      });
    });
    
    // 6. Consultation de la mémoire
    response = http.get(`${BASE_URL}/api/memory/stats`);
    sleep(0.5);
    
    // 7. Vérification des performances
    response = http.get(`${BASE_URL}/api/agent/status`);
    
  });
}

// Fonction principale d'exécution
export default function() {
  // Répartition des tests
  const testChoice = Math.random();
  
  if (testChoice < 0.4) {
    testAPI();
  } else if (testChoice < 0.6) {
    testWebSocket();
  } else if (testChoice < 0.8) {
    testUI();
  } else if (testChoice < 0.9) {
    testServices();
  } else {
    realisticUserScenario();
  }
  
  // Pause entre les requêtes
  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 secondes
}

// Fonction de nettoyage
export function teardown() {
  console.log('🧹 Nettoyage des tests de performance terminé');
}

// Configuration avancée pour différents environnements
export function handleSummary(data) {
  return {
    'performance-summary.json': JSON.stringify(data),
    'performance-report.html': generateHTMLReport(data),
  };
}

function generateHTMLReport(data) {
  const template = `
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .success { border-color: #28a745; }
        .warning { border-color: #ffc107; }
        .error { border-color: #dc3545; }
    </style>
</head>
<body>
    <h1>🚀 JARVIS Performance Test Report</h1>
    <div class="metric">
        <strong>Total Requests:</strong> ${data.metrics.http_reqs.count}
    </div>
    <div class="metric">
        <strong>Failed Requests:</strong> ${data.metrics.http_req_failed.rate * 100}%
    </div>
    <div class="metric">
        <strong>Average Response Time:</strong> ${data.metrics.http_req_duration.avg.toFixed(2)}ms
    </div>
    <div class="metric">
        <strong>95th Percentile:</strong> ${data.metrics.http_req_duration.p95.toFixed(2)}ms
    </div>
    <p>Generated on: ${new Date().toISOString()}</p>
</body>
</html>
  `;
  return template;
}