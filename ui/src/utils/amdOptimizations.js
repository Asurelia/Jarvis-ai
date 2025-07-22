/**
 * 🔴 Optimisations spécifiques GPU AMD pour JARVIS
 * Configuration WebGL et Three.js adaptée aux cartes graphiques AMD
 */

// Détection GPU avancée
export const detectGPUCapabilities = () => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    
    if (!gl) {
      return { 
        vendor: 'unknown', 
        isAMD: false, 
        isNVIDIA: false, 
        isIntegrated: true,
        webglVersion: 'none'
      };
    }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    let vendor = 'unknown';
    let renderer = 'unknown';
    
    if (debugInfo) {
      vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
    }

    // Détection AMD précise
    const isAMD = vendor.toLowerCase().includes('amd') || 
                  vendor.toLowerCase().includes('ati') || 
                  renderer.toLowerCase().includes('radeon') ||
                  renderer.toLowerCase().includes('amd');

    const isNVIDIA = vendor.toLowerCase().includes('nvidia') ||
                     renderer.toLowerCase().includes('geforce') ||
                     renderer.toLowerCase().includes('quadro');

    const isIntegrated = renderer.toLowerCase().includes('intel') ||
                        renderer.toLowerCase().includes('uhd') ||
                        renderer.toLowerCase().includes('iris');

    // Test des extensions WebGL pour AMD
    const extensions = {
      anisotropicFiltering: !!gl.getExtension('EXT_texture_filter_anisotropic'),
      floatTextures: !!gl.getExtension('OES_texture_float'),
      standardDerivatives: !!gl.getExtension('OES_standard_derivatives'),
      vertexArrayObjects: !!gl.getExtension('OES_vertex_array_object'),
      instancing: !!gl.getExtension('ANGLE_instanced_arrays')
    };

    // Limites GPU
    const limits = {
      maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
      maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
      maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
      maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
      maxFragmentUniforms: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),
      maxVertexUniforms: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS)
    };

    canvas.remove();

    return {
      vendor: vendor.toLowerCase(),
      renderer: renderer.toLowerCase(),
      isAMD,
      isNVIDIA,
      isIntegrated,
      webglVersion: gl.getParameter(gl.VERSION),
      extensions,
      limits,
      // Score de performance estimé
      performanceScore: calculatePerformanceScore(isAMD, isNVIDIA, isIntegrated, extensions, limits)
    };
    
  } catch (error) {
    console.warn('Erreur détection GPU:', error);
    return { 
      vendor: 'unknown', 
      isAMD: false, 
      isNVIDIA: false, 
      isIntegrated: true,
      performanceScore: 1
    };
  }
};

// Calcul score de performance
const calculatePerformanceScore = (isAMD, isNVIDIA, isIntegrated, extensions, limits) => {
  let score = 5; // Score de base

  if (isIntegrated) score = 1;
  else if (isAMD) score = 3;
  else if (isNVIDIA) score = 4;

  // Bonus pour les extensions
  if (extensions.anisotropicFiltering) score += 0.5;
  if (extensions.floatTextures) score += 0.5;
  if (extensions.instancing) score += 0.3;

  // Bonus selon les limites
  if (limits.maxTextureSize >= 4096) score += 0.5;
  if (limits.maxFragmentUniforms >= 256) score += 0.3;

  return Math.min(score, 5);
};

// Configuration WebGL optimisée AMD
export const getOptimalWebGLConfig = (gpuInfo) => {
  const baseConfig = {
    alpha: true,
    antialias: false, // Par défaut désactivé
    powerPreference: "default",
    preserveDrawingBuffer: false,
    failIfMajorPerformanceCaveat: false,
    depth: true,
    stencil: false
  };

  if (gpuInfo.isAMD) {
    return {
      ...baseConfig,
      // Configuration AMD optimisée
      antialias: gpuInfo.performanceScore >= 3, // Antialiasing seulement sur bonnes AMD
      powerPreference: "default", // Laisser AMD décider
      precision: "mediump", // Meilleure compatibilité
      premultipliedAlpha: false, // Éviter problèmes transparence AMD
    };
  }

  if (gpuInfo.isIntegrated) {
    return {
      ...baseConfig,
      // Configuration ultra-légère
      antialias: false,
      powerPreference: "low-power",
      precision: "lowp"
    };
  }

  // Configuration NVIDIA (haute performance)
  return {
    ...baseConfig,
    antialias: true,
    powerPreference: "high-performance",
    precision: "highp",
    premultipliedAlpha: true
  };
};

// Paramètres de rendu adaptatifs
export const getAdaptiveRenderSettings = (gpuInfo) => {
  const settings = {
    // Paramètres de base
    shadowsEnabled: false,
    shadowMapType: 'BasicShadowMap',
    toneMapping: 'LinearToneMapping',
    toneMappingExposure: 1.0,
    outputColorSpace: 'LinearSRGBColorSpace',
    
    // Post-processing
    bloomEnabled: true,
    bloomStrength: 0.2,
    bloomThreshold: 0.3,
    glitchEnabled: false,
    filmEnabled: false,
    
    // Particules
    particleCount: 50,
    particleComplexity: 'low',
    
    // Shaders
    shaderPrecision: 'mediump',
    shaderComplexity: 'simple'
  };

  if (gpuInfo.isAMD && gpuInfo.performanceScore >= 3) {
    // AMD moyenne-haute performance
    return {
      ...settings,
      bloomStrength: 0.3,
      bloomThreshold: 0.2,
      particleCount: 75,
      particleComplexity: 'medium',
      shaderComplexity: 'medium'
    };
  }

  if (gpuInfo.isAMD && gpuInfo.performanceScore >= 4) {
    // AMD haute performance (RX 6000+, RX 7000+)
    return {
      ...settings,
      shadowsEnabled: true,
      shadowMapType: 'PCFShadowMap', // Éviter PCFSoft sur AMD
      bloomStrength: 0.4,
      bloomThreshold: 0.15,
      glitchEnabled: true, // Activer sur bonnes AMD
      particleCount: 100,
      particleComplexity: 'high',
      shaderPrecision: 'highp',
      shaderComplexity: 'advanced'
    };
  }

  if (gpuInfo.isNVIDIA) {
    // Configuration NVIDIA complète
    return {
      ...settings,
      shadowsEnabled: true,
      shadowMapType: 'PCFSoftShadowMap',
      toneMapping: 'ACESFilmicToneMapping',
      toneMappingExposure: 1.2,
      outputColorSpace: 'SRGBColorSpace',
      bloomStrength: 0.5,
      bloomThreshold: 0.1,
      glitchEnabled: true,
      filmEnabled: true,
      particleCount: 150,
      particleComplexity: 'high',
      shaderPrecision: 'highp',
      shaderComplexity: 'advanced'
    };
  }

  if (gpuInfo.isIntegrated) {
    // Configuration minimale
    return {
      ...settings,
      bloomEnabled: false,
      particleCount: 25,
      particleComplexity: 'minimal',
      shaderPrecision: 'lowp',
      shaderComplexity: 'basic'
    };
  }

  return settings;
};

// Shaders simplifiés pour AMD
export const getAMDOptimizedShaders = () => ({
  vertex: `
    uniform float time;
    uniform float audioLevel;
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying float vElevation;
    
    // Fonction bruit simplifiée pour AMD
    float simpleNoise(vec3 p) {
      return sin(p.x * 5.0) * sin(p.y * 5.0) * sin(p.z * 5.0) * 0.5;
    }
    
    void main() {
      vPosition = position;
      vNormal = normal;
      
      // Déformation simple audio-réactive
      float elevation = simpleNoise(position + time * 0.3) * audioLevel * 0.05;
      float pulse = 1.0 + sin(time) * audioLevel * 0.1;
      
      vec3 newPosition = position * pulse + normal * elevation;
      vElevation = elevation;
      
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `,
  
  fragment: `
    #ifdef GL_ES
    precision mediump float;
    #endif
    
    uniform float time;
    uniform float audioLevel;
    uniform vec3 baseColor;
    uniform bool isListening;
    uniform bool isSpeaking;
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying float vElevation;
    
    void main() {
      vec3 color = baseColor;
      
      // États simples pour AMD
      if (isListening) {
        color = mix(baseColor, vec3(0.2, 0.8, 0.4), 0.5);
      } else if (isSpeaking) {
        color = mix(baseColor, vec3(0.9, 0.4, 0.1), 0.5);
      }
      
      // Intensité audio simple
      float intensity = 1.0 + audioLevel;
      color *= intensity;
      
      // Fresnel simple
      float fresnel = 1.0 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0));
      color += fresnel * 0.2;
      
      gl_FragColor = vec4(color, 0.8 + vElevation);
    }
  `
});

// Monitoring performance en temps réel
export class AMDPerformanceMonitor {
  constructor() {
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.fps = 60;
    this.adaptiveQuality = 1.0;
    this.targetFPS = 60;
  }
  
  update() {
    this.frameCount++;
    const currentTime = performance.now();
    
    if (currentTime - this.lastTime >= 1000) {
      this.fps = this.frameCount;
      this.frameCount = 0;
      this.lastTime = currentTime;
      
      // Adaptation automatique qualité
      if (this.fps < this.targetFPS * 0.8) {
        this.adaptiveQuality = Math.max(0.5, this.adaptiveQuality - 0.1);
        console.log('🔧 Qualité réduite pour AMD:', this.adaptiveQuality);
      } else if (this.fps > this.targetFPS * 0.95) {
        this.adaptiveQuality = Math.min(1.0, this.adaptiveQuality + 0.05);
      }
    }
  }
  
  getQualitySettings() {
    return {
      particleMultiplier: this.adaptiveQuality,
      bloomStrength: 0.2 * this.adaptiveQuality,
      renderScale: this.adaptiveQuality,
      fps: this.fps
    };
  }
}

export default {
  detectGPUCapabilities,
  getOptimalWebGLConfig,
  getAdaptiveRenderSettings,
  getAMDOptimizedShaders,
  AMDPerformanceMonitor
};