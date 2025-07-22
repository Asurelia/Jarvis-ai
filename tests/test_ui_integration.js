#!/usr/bin/env node
/**
 * 🎨 JARVIS AI 2025 - Tests d'Intégration UI
 * Tests des composants React et interactions utilisateur
 */

const fs = require('fs');
const path = require('path');

// Configuration des tests
const TEST_CONFIG = {
  timeout: 30000,
  verbose: true,
  components: [
    'CognitiveIntelligenceModule.js',
    'PredictionSystem.js',
    'NeuralInterface.js', 
    'PerformanceMonitor.js',
    'Sphere3D.js'
  ],
  utilities: [
    'PerformanceOptimizer.js'
  ]
};

class UITestSuite {
  constructor() {
    this.results = [];
    this.startTime = Date.now();
    this.projectRoot = path.resolve(__dirname, '..');
  }

  log(message, level = 'INFO') {
    if (TEST_CONFIG.verbose) {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] ${level}: ${message}`);
    }
  }

  addResult(testName, passed, duration, details = {}, errors = []) {
    this.results.push({
      testName,
      passed,
      duration,
      details,
      errors,
      timestamp: Date.now()
    });
  }

  // Test 1: Vérification de l'existence des fichiers
  testComponentFiles() {
    this.log("Test 1: Verification des fichiers composants...");
    const startTime = Date.now();
    let filesFound = 0;
    let totalFiles = 0;
    const errors = [];

    // Test des composants UI
    TEST_CONFIG.components.forEach(componentName => {
      totalFiles++;
      const filePath = path.join(this.projectRoot, 'ui', 'src', 'components', componentName);
      
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(1);
        this.log(`  ✅ ${componentName} (${sizeKB}KB)`);
        filesFound++;
      } else {
        this.log(`  ❌ MANQUANT: ${componentName}`);
        errors.push(`File not found: ${componentName}`);
      }
    });

    // Test des utilitaires
    TEST_CONFIG.utilities.forEach(utilName => {
      totalFiles++;
      const filePath = path.join(this.projectRoot, 'ui', 'src', 'utils', utilName);
      
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(1);
        this.log(`  ✅ ${utilName} (${sizeKB}KB)`);
        filesFound++;
      } else {
        this.log(`  ❌ MANQUANT: ${utilName}`);
        errors.push(`File not found: ${utilName}`);
      }
    });

    const duration = Date.now() - startTime;
    const success = filesFound === totalFiles;
    
    this.log(`Fichiers trouvés: ${filesFound}/${totalFiles}`);
    this.addResult('component_files', success, duration, { filesFound, totalFiles }, errors);
    
    return success;
  }

  // Test 2: Analyse syntaxique des composants React
  testComponentSyntax() {
    this.log("Test 2: Analyse syntaxique des composants...");
    const startTime = Date.now();
    let validComponents = 0;
    let totalComponents = 0;
    const errors = [];

    TEST_CONFIG.components.forEach(componentName => {
      totalComponents++;
      const filePath = path.join(this.projectRoot, 'ui', 'src', 'components', componentName);
      
      if (fs.existsSync(filePath)) {
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          
          // Tests syntaxiques basiques
          const checks = {
            hasImports: /import.*from/g.test(content),
            hasReact: /import.*React/g.test(content),
            hasExport: /export.*default/g.test(content),
            hasFunction: /function\s+\w+|const\s+\w+\s*=/g.test(content),
            hasJSX: /<[A-Z]\w*|<[a-z]\w*/g.test(content),
            hasProps: /props|{.*}/g.test(content)
          };

          const passedChecks = Object.values(checks).filter(Boolean).length;
          const totalChecks = Object.keys(checks).length;

          if (passedChecks >= totalChecks - 1) { // Au moins 5/6 checks
            this.log(`  ✅ ${componentName}: ${passedChecks}/${totalChecks} checks`);
            validComponents++;
          } else {
            this.log(`  ⚠️ ${componentName}: ${passedChecks}/${totalChecks} checks`);
            errors.push(`${componentName}: Failed syntax checks (${passedChecks}/${totalChecks})`);
          }

        } catch (error) {
          this.log(`  ❌ ${componentName}: Parse error - ${error.message}`);
          errors.push(`${componentName}: Parse error - ${error.message}`);
        }
      }
    });

    const duration = Date.now() - startTime;
    const success = validComponents === totalComponents;
    
    this.log(`Composants valides: ${validComponents}/${totalComponents}`);
    this.addResult('component_syntax', success, duration, { validComponents, totalComponents }, errors);
    
    return success;
  }

  // Test 3: Analyse des dépendances et imports
  testComponentDependencies() {
    this.log("Test 3: Analyse des dépendances...");
    const startTime = Date.now();
    let validDependencies = 0;
    let totalComponents = 0;
    const errors = [];
    const dependencyMap = new Map();

    TEST_CONFIG.components.forEach(componentName => {
      totalComponents++;
      const filePath = path.join(this.projectRoot, 'ui', 'src', 'components', componentName);
      
      if (fs.existsSync(filePath)) {
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          
          // Extraction des imports
          const imports = [];
          const importRegex = /import\s+.*?\s+from\s+['"](.+?)['"]/g;
          let match;
          
          while ((match = importRegex.exec(content)) !== null) {
            imports.push(match[1]);
          }

          // Analyse des dépendances
          const dependencies = {
            react: imports.some(imp => imp === 'react'),
            mui: imports.some(imp => imp.includes('@mui')),
            threejs: imports.some(imp => imp.includes('three')),
            localComponents: imports.filter(imp => imp.startsWith('./') || imp.startsWith('../')).length,
            externalLibs: imports.filter(imp => !imp.startsWith('./') && !imp.startsWith('../')).length
          };

          dependencyMap.set(componentName, dependencies);

          // Validation des dépendances critiques
          const criticalChecks = [
            dependencies.react, // React requis
            dependencies.externalLibs > 0 // Au moins une lib externe
          ];

          const passedCritical = criticalChecks.filter(Boolean).length;
          
          if (passedCritical >= 1) { // Au moins React
            this.log(`  ✅ ${componentName}: ${imports.length} imports`);
            validDependencies++;
          } else {
            this.log(`  ❌ ${componentName}: Missing critical dependencies`);
            errors.push(`${componentName}: Missing critical dependencies`);
          }

        } catch (error) {
          this.log(`  ❌ ${componentName}: Dependency analysis failed - ${error.message}`);
          errors.push(`${componentName}: Dependency analysis failed`);
        }
      }
    });

    const duration = Date.now() - startTime;
    const success = validDependencies === totalComponents;
    
    this.log(`Dépendances valides: ${validDependencies}/${totalComponents}`);
    this.addResult('component_dependencies', success, duration, { 
      validDependencies, 
      totalComponents,
      dependencyMap: Object.fromEntries(dependencyMap)
    }, errors);
    
    return success;
  }

  // Test 4: Analyse des fonctionnalités spécifiques
  testComponentFeatures() {
    this.log("Test 4: Analyse des fonctionnalités spécifiques...");
    const startTime = Date.now();
    let validFeatures = 0;
    let totalComponents = 0;
    const errors = [];

    const featureTests = {
      'CognitiveIntelligenceModule.js': [
        /COGNITIVE_STATES/g,
        /COGNITIVE_AGENTS/g,
        /THREE\.Scene/g,
        /createNeuralNetwork/g
      ],
      'PredictionSystem.js': [
        /PREDICTION_TYPES/g,
        /BEHAVIOR_CATEGORIES/g,
        /predictFutureActions/g,
        /Timeline/g
      ],
      'NeuralInterface.js': [
        /INPUT_MODALITIES/g,
        /NEURAL_PATTERNS/g,
        /checkCircularGesture/g,
        /eyePosition/g
      ],
      'PerformanceMonitor.js': [
        /performanceOptimizer/g,
        /runPerformanceTest/g,
        /realtimeMetrics/g,
        /capabilities/g
      ],
      'Sphere3D.js': [
        /SPHERE_THEMES/g,
        /getAdvancedShader/g,
        /createAdvancedParticles/g,
        /quantum|fractal|holographic/gi
      ]
    };

    Object.entries(featureTests).forEach(([componentName, patterns]) => {
      totalComponents++;
      const filePath = path.join(this.projectRoot, 'ui', 'src', 'components', componentName);
      
      if (fs.existsSync(filePath)) {
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          
          const matchedPatterns = patterns.filter(pattern => pattern.test(content));
          const featureScore = matchedPatterns.length / patterns.length;

          if (featureScore >= 0.7) { // Au moins 70% des fonctionnalités
            this.log(`  ✅ ${componentName}: ${matchedPatterns.length}/${patterns.length} features`);
            validFeatures++;
          } else {
            this.log(`  ⚠️ ${componentName}: ${matchedPatterns.length}/${patterns.length} features`);
            errors.push(`${componentName}: Missing features (${matchedPatterns.length}/${patterns.length})`);
          }

        } catch (error) {
          this.log(`  ❌ ${componentName}: Feature analysis failed - ${error.message}`);
          errors.push(`${componentName}: Feature analysis failed`);
        }
      }
    });

    const duration = Date.now() - startTime;
    const success = validFeatures >= Math.floor(totalComponents * 0.8); // 80% des composants
    
    this.log(`Fonctionnalités valides: ${validFeatures}/${totalComponents}`);
    this.addResult('component_features', success, duration, { validFeatures, totalComponents }, errors);
    
    return success;
  }

  // Test 5: Test de performance des fichiers
  testPerformanceOptimizer() {
    this.log("Test 5: Analyse de PerformanceOptimizer...");
    const startTime = Date.now();
    const errors = [];

    const filePath = path.join(this.projectRoot, 'ui', 'src', 'utils', 'PerformanceOptimizer.js');
    
    if (fs.existsSync(filePath)) {
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        
        const performanceFeatures = [
          /WorkerManager/g,
          /WASMManager/g,
          /GPUComputeManager/g,
          /WebAssembly/g,
          /WebGL/g,
          /ThreadPoolExecutor|Worker/g
        ];

        const matchedFeatures = performanceFeatures.filter(pattern => pattern.test(content));
        const featureScore = matchedFeatures.length / performanceFeatures.length;

        const sizeKB = (fs.statSync(filePath).size / 1024).toFixed(1);
        
        if (featureScore >= 0.8) {
          this.log(`  ✅ PerformanceOptimizer: ${matchedFeatures.length}/${performanceFeatures.length} features (${sizeKB}KB)`);
          
          const duration = Date.now() - startTime;
          this.addResult('performance_optimizer', true, duration, { 
            features: matchedFeatures.length,
            total: performanceFeatures.length,
            sizeKB: parseFloat(sizeKB)
          }, errors);
          
          return true;
        } else {
          errors.push(`PerformanceOptimizer: Missing features (${matchedFeatures.length}/${performanceFeatures.length})`);
        }

      } catch (error) {
        this.log(`  ❌ PerformanceOptimizer: Analysis failed - ${error.message}`);
        errors.push(`PerformanceOptimizer: Analysis failed`);
      }
    } else {
      errors.push('PerformanceOptimizer.js not found');
    }

    const duration = Date.now() - startTime;
    this.addResult('performance_optimizer', false, duration, {}, errors);
    return false;
  }

  // Test 6: Simulation d'intégration avec package.json
  testPackageIntegration() {
    this.log("Test 6: Vérification package.json...");
    const startTime = Date.now();
    const errors = [];

    const packageJsonPath = path.join(this.projectRoot, 'ui', 'package.json');
    
    if (fs.existsSync(packageJsonPath)) {
      try {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // Vérification des dépendances critiques
        const requiredDeps = [
          'react',
          '@mui/material',
          'three'
        ];

        const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
        const missingDeps = requiredDeps.filter(dep => !allDeps[dep]);

        if (missingDeps.length === 0) {
          this.log(`  ✅ package.json: Toutes les dépendances critiques présentes`);
          
          const duration = Date.now() - startTime;
          this.addResult('package_integration', true, duration, { 
            totalDeps: Object.keys(allDeps).length,
            requiredDeps: requiredDeps.length
          }, errors);
          
          return true;
        } else {
          this.log(`  ❌ package.json: Dépendances manquantes: ${missingDeps.join(', ')}`);
          errors.push(`Missing dependencies: ${missingDeps.join(', ')}`);
        }

      } catch (error) {
        this.log(`  ❌ package.json: Parse error - ${error.message}`);
        errors.push(`package.json parse error`);
      }
    } else {
      this.log(`  ❌ package.json non trouvé`);
      errors.push('package.json not found');
    }

    const duration = Date.now() - startTime;
    this.addResult('package_integration', false, duration, {}, errors);
    return false;
  }

  // Exécution de tous les tests
  async runAllTests() {
    this.log("JARVIS AI 2025 - Tests d'Integration UI");
    this.log("=" * 50);

    const tests = [
      () => this.testComponentFiles(),
      () => this.testComponentSyntax(), 
      () => this.testComponentDependencies(),
      () => this.testComponentFeatures(),
      () => this.testPerformanceOptimizer(),
      () => this.testPackageIntegration()
    ];

    let passedTests = 0;

    for (const test of tests) {
      const success = test();
      if (success) passedTests++;
      
      // Petite pause entre les tests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Rapport final
    const totalDuration = Date.now() - this.startTime;
    const successRate = passedTests / tests.length;

    this.log("=" * 50);
    this.log("RAPPORT FINAL");
    this.log("=" * 50);
    
    this.results.forEach(result => {
      const status = result.passed ? "PASSE" : "ECHEC";
      this.log(`${result.testName.toUpperCase()}: ${status} (${result.duration}ms)`);
      
      if (result.errors.length > 0) {
        result.errors.forEach(error => this.log(`  - ${error}`));
      }
    });

    this.log(`\nTests passes: ${passedTests}/${tests.length}`);
    this.log(`Taux de reussite: ${(successRate * 100).toFixed(1)}%`);
    this.log(`Duree totale: ${totalDuration}ms`);

    if (passedTests === tests.length) {
      this.log("\n🎉 TOUS LES TESTS UI SONT PASSES ! Interface prête pour l'integration !");
      return true;
    } else {
      this.log(`\n⚠️ ${tests.length - passedTests} tests ont echoue. Verifiez les logs ci-dessus.`);
      return false;
    }
  }
}

// Point d'entrée
if (require.main === module) {
  const testSuite = new UITestSuite();
  
  testSuite.runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error("Erreur lors des tests:", error);
    process.exit(1);
  });
}

module.exports = UITestSuite;