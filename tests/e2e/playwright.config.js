/**
 * 🎭 Configuration Playwright pour les tests E2E JARVIS
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Répertoire des tests
  testDir: './specs',
  
  // Timeout global des tests (30 secondes)
  timeout: 30 * 1000,
  
  // Configuration pour les assertions
  expect: {
    timeout: 5000,
  },
  
  // Configuration pour les retries et parallélisation
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // Configuration des rapports
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-junit.xml' }],
  ],
  
  // Configuration globale
  use: {
    baseURL: process.env.BASE_URL || 'http://ui-test:80',
    
    // Traces et screenshots
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Timeout pour les actions
    actionTimeout: 10000,
    navigationTimeout: 15000,
    
    // Configuration du navigateur
    ignoreHTTPSErrors: true,
    colorScheme: 'dark',
    viewport: { width: 1280, height: 720 },
  },

  // Configuration des projets de test
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Configuration spéciale pour JARVIS
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--allow-running-insecure-content',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-ipc-flooding-protection',
          ]
        }
      },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Tests mobiles
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Configuration du serveur local (si nécessaire)
  webServer: process.env.CI ? undefined : {
    command: 'echo "Serveur déjà démarré par Docker"',
    port: 3001,
    reuseExistingServer: true,
  },
});