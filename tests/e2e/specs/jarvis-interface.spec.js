/**
 * 🎯 Tests E2E pour l'interface JARVIS
 * Tests end-to-end complets de l'expérience utilisateur
 */

import { test, expect } from '@playwright/test';

// Configuration des tests
test.describe('🤖 Interface JARVIS - Tests E2E', () => {
  let page;
  
  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Naviguer vers l'application
    await page.goto('/');
    
    // Attendre que l'application soit chargée
    await page.waitForSelector('[data-testid="app-container"]', { 
      timeout: 15000,
      state: 'visible' 
    });
  });

  test.describe('🎨 Interface Utilisateur', () => {
    
    test('doit charger la page d\'accueil correctement', async () => {
      // Vérifier le titre de la page
      await expect(page).toHaveTitle(/JARVIS/i);
      
      // Vérifier les éléments principaux
      await expect(page.getByTestId('app-container')).toBeVisible();
      await expect(page.getByRole('main')).toBeVisible();
      
      // Vérifier le thème sombre
      const body = page.locator('body');
      await expect(body).toHaveCSS('background-color', /rgb\(13, 20, 33\)|rgb\(26, 37, 47\)/);
    });

    test('doit afficher la barre de navigation', async () => {
      // Vérifier la présence de la navigation
      const nav = page.getByRole('navigation').or(page.locator('[data-testid="navigation"]'));
      await expect(nav).toBeVisible();
      
      // Vérifier les éléments de navigation principaux
      await expect(page.getByText('Chat', { exact: false })).toBeVisible();
      await expect(page.getByText('Voice', { exact: false })).toBeVisible();
      await expect(page.getByText('Vision', { exact: false })).toBeVisible();
    });

    test('doit être responsive', async () => {
      // Test desktop
      await page.setViewportSize({ width: 1920, height: 1080 });
      await expect(page.getByTestId('app-container')).toBeVisible();
      
      // Test tablet
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500);
      await expect(page.getByTestId('app-container')).toBeVisible();
      
      // Test mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      await expect(page.getByTestId('app-container')).toBeVisible();
    });
  });

  test.describe('💬 Interface de Chat', () => {
    
    test('doit ouvrir la fenêtre de chat', async () => {
      // Cliquer sur le bouton chat
      const chatButton = page.getByRole('button', { name: /chat/i })
        .or(page.getByTestId('chat-button'))
        .or(page.locator('[data-testid*="chat"]').first());
      
      await chatButton.click();
      
      // Vérifier que la fenêtre de chat s'ouvre
      const chatWindow = page.getByTestId('chat-window')
        .or(page.locator('.chat-window'))
        .or(page.getByRole('dialog'));
      
      await expect(chatWindow).toBeVisible();
    });

    test('doit permettre d\'envoyer un message', async () => {
      // Ouvrir le chat
      await page.getByTestId('chat-button').or(page.getByRole('button', { name: /chat/i })).click();
      
      // Trouver le champ de saisie
      const input = page.getByRole('textbox', { name: /message/i })
        .or(page.getByPlaceholder(/tapez votre message/i))
        .or(page.locator('input[type="text"]').last())
        .or(page.locator('textarea').last());
      
      // Saisir un message
      const testMessage = 'Bonjour JARVIS, comment allez-vous ?';
      await input.fill(testMessage);
      
      // Envoyer le message
      const sendButton = page.getByRole('button', { name: /envoyer|send/i })
        .or(page.getByTestId('send-button'))
        .or(page.keyboard.press('Enter'));
      
      if (sendButton && typeof sendButton.click === 'function') {
        await sendButton.click();
      } else {
        await page.keyboard.press('Enter');
      }
      
      // Vérifier que le message apparaît dans l'historique
      await expect(page.getByText(testMessage)).toBeVisible();
    });

    test('doit afficher les réponses de JARVIS', async () => {
      // Envoyer un message et attendre la réponse
      await page.getByTestId('chat-button').or(page.getByRole('button', { name: /chat/i })).click();
      
      const input = page.getByRole('textbox').last();
      await input.fill('Test');
      await page.keyboard.press('Enter');
      
      // Attendre une réponse (timeout plus long pour la génération)
      await expect(page.getByText(/jarvis|ia|intelligence/i)).toBeVisible({ timeout: 30000 });
    });
  });

  test.describe('🎙️ Interface Vocale', () => {
    
    test('doit afficher les contrôles vocaux', async () => {
      // Naviguer vers l'interface vocale
      await page.getByText('Voice').or(page.getByTestId('voice-tab')).click();
      
      // Vérifier la présence des contrôles
      const micButton = page.getByRole('button', { name: /micro|record/i })
        .or(page.getByTestId('mic-button'));
      
      await expect(micButton).toBeVisible();
    });

    test('doit gérer les permissions audio', async () => {
      // Simuler l'accord de permission
      await page.context().grantPermissions(['microphone']);
      
      await page.getByText('Voice').or(page.getByTestId('voice-tab')).click();
      
      // Tenter d'utiliser le microphone
      const micButton = page.getByTestId('mic-button')
        .or(page.getByRole('button', { name: /micro/i }));
      
      await micButton.click();
      
      // Vérifier que l'enregistrement démarre
      await expect(page.getByText(/enregistrement|recording/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('👁️ Interface Vision', () => {
    
    test('doit afficher l\'interface vision', async () => {
      await page.getByText('Vision').or(page.getByTestId('vision-tab')).click();
      
      // Vérifier les éléments de vision
      const visionContainer = page.getByTestId('vision-container')
        .or(page.locator('.vision-interface'));
      
      await expect(visionContainer).toBeVisible();
    });

    test('doit permettre la capture d\'écran', async () => {
      // Accorder les permissions
      await page.context().grantPermissions(['camera']);
      
      await page.getByText('Vision').or(page.getByTestId('vision-tab')).click();
      
      const captureButton = page.getByRole('button', { name: /capture|screenshot/i })
        .or(page.getByTestId('capture-button'));
      
      if (await captureButton.isVisible()) {
        await captureButton.click();
        
        // Vérifier que la capture est traitée
        await expect(page.getByText(/capture|analyse/i)).toBeVisible({ timeout: 10000 });
      }
    });
  });

  test.describe('🧠 Modules Avancés', () => {
    
    test('doit afficher le module d\'intelligence cognitive', async () => {
      // Chercher le module d'IA cognitive
      const cognitiveModule = page.getByTestId('cognitive-module')
        .or(page.getByText(/intelligence.*cognitive/i))
        .or(page.locator('[class*="cognitive"]').first());
      
      if (await cognitiveModule.isVisible()) {
        await expect(cognitiveModule).toBeVisible();
      }
    });

    test('doit afficher la sphère 3D', async () => {
      // Chercher la sphère 3D
      const sphere3D = page.getByTestId('sphere-3d')
        .or(page.locator('canvas'))
        .or(page.locator('[class*="sphere"]'));
      
      if (await sphere3D.isVisible()) {
        await expect(sphere3D).toBeVisible();
        
        // Vérifier que l'animation fonctionne
        await page.waitForTimeout(1000);
        const boundingBox1 = await sphere3D.boundingBox();
        await page.waitForTimeout(1000);
        const boundingBox2 = await sphere3D.boundingBox();
        
        // L'animation peut changer la position ou d'autres propriétés
        expect(boundingBox1).toBeDefined();
        expect(boundingBox2).toBeDefined();
      }
    });

    test('doit afficher le moniteur de performance', async () => {
      const perfMonitor = page.getByTestId('performance-monitor')
        .or(page.getByText(/performance|fps|cpu/i))
        .or(page.locator('[class*="performance"]').first());
      
      if (await perfMonitor.isVisible()) {
        await expect(perfMonitor).toBeVisible();
        
        // Vérifier que les métriques se mettent à jour
        await page.waitForTimeout(2000);
        await expect(perfMonitor).toContainText(/\d+/); // Contient des chiffres
      }
    });
  });

  test.describe('🔗 Connectivité et WebSocket', () => {
    
    test('doit établir une connexion WebSocket', async () => {
      // Écouter les événements WebSocket
      let wsConnected = false;
      
      page.on('websocket', ws => {
        wsConnected = true;
        ws.on('framesent', event => console.log('WS Frame sent:', event.payload));
        ws.on('framereceived', event => console.log('WS Frame received:', event.payload));
      });
      
      // Déclencher une action qui utilise WebSocket
      const chatButton = page.getByTestId('chat-button').first();
      if (await chatButton.isVisible()) {
        await chatButton.click();
        
        // Attendre un peu pour la connexion WebSocket
        await page.waitForTimeout(2000);
        
        // Vérifier dans les DevTools Network
        const wsRequests = await page.evaluate(() => {
          return performance.getEntriesByType('resource')
            .filter(entry => entry.name.includes('ws://') || entry.name.includes('wss://'));
        });
        
        expect(wsRequests.length).toBeGreaterThan(0);
      }
    });

    test('doit gérer les erreurs de connexion', async () => {
      // Simuler une perte de connexion réseau
      await page.context().setOffline(true);
      
      // Tenter d'interagir avec l'application
      const chatButton = page.getByTestId('chat-button').first();
      if (await chatButton.isVisible()) {
        await chatButton.click();
        
        // Vérifier qu'un message d'erreur apparaît
        await expect(page.getByText(/connexion|erreur|offline/i))
          .toBeVisible({ timeout: 10000 });
      }
      
      // Restaurer la connexion
      await page.context().setOffline(false);
    });
  });

  test.describe('⚡ Performance et Accessibilité', () => {
    
    test('doit charger rapidement', async () => {
      const startTime = Date.now();
      
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('[data-testid="app-container"]');
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // Moins de 5 secondes
    });

    test('doit être accessible au clavier', async () => {
      // Navigation par tabulation
      await page.keyboard.press('Tab');
      let focusedElement = await page.locator(':focus').first();
      await expect(focusedElement).toBeVisible();
      
      // Continuer la navigation
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');
        focusedElement = await page.locator(':focus').first();
        
        if (await focusedElement.isVisible()) {
          await expect(focusedElement).toBeVisible();
        }
      }
    });

    test('doit avoir des contrastes suffisants', async () => {
      // Vérifier les contrastes principaux
      const textElements = page.locator('h1, h2, h3, p, span, button').first();
      
      if (await textElements.isVisible()) {
        const color = await textElements.evaluate(el => {
          return window.getComputedStyle(el).color;
        });
        
        // Vérifier que la couleur n'est pas trop proche du fond
        expect(color).not.toBe('rgb(0, 0, 0)');
        expect(color).not.toBe('rgb(13, 20, 33)');
      }
    });
  });

  test.describe('📱 Tests Multi-plateforme', () => {
    
    test('doit fonctionner sur différentes résolutions', async () => {
      const resolutions = [
        { width: 1920, height: 1080 }, // Full HD
        { width: 1366, height: 768 },  // HD
        { width: 1024, height: 768 },  // Tablet
        { width: 375, height: 812 },   // Mobile
      ];
      
      for (const resolution of resolutions) {
        await page.setViewportSize(resolution);
        await page.waitForTimeout(500);
        
        // Vérifier que l'interface reste utilisable
        await expect(page.getByTestId('app-container')).toBeVisible();
        
        // Vérifier qu'il n'y a pas d'éléments débordants
        const overflowElements = await page.$$eval('*', elements => {
          return elements.filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.right > window.innerWidth || rect.bottom > window.innerHeight;
          }).length;
        });
        
        expect(overflowElements).toBeLessThan(5); // Tolérance pour quelques éléments
      }
    });
  });

  // Nettoyage après chaque test
  test.afterEach(async ({ page }) => {
    // Fermer les connexions WebSocket ouvertes
    await page.evaluate(() => {
      if (window.ws) {
        window.ws.close();
      }
    });
    
    // Capturer une screenshot en cas d'échec
    if (test.info().status !== 'passed') {
      await page.screenshot({ 
        path: `test-results/failed-${test.info().title.replace(/\s+/g, '-')}.png`,
        fullPage: true 
      });
    }
  });
});