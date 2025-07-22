/**
 * 🌐 JARVIS UI - Sphère 3D Audio-Réactive Avancée
 * Composant 3D central avec effets post-processing et émotions
 */
import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Box } from '@mui/material';
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';
import { GlitchPass } from 'three/examples/jsm/postprocessing/GlitchPass';
import { FilmPass } from 'three/examples/jsm/postprocessing/FilmPass';

// Thèmes et modes de visualisation
const SPHERE_THEMES = {
  cyberpunk: {
    colors: [0x00ffff, 0xff00ff, 0xffff00],
    particles: 'matrix',
    shader: 'neon'
  },
  organic: {
    colors: [0x4CAF50, 0x8BC34A, 0xCDDC39],
    particles: 'fireflies',
    shader: 'fluid'
  },
  cosmos: {
    colors: [0x6A0DAD, 0x4B0082, 0x0000FF],
    particles: 'stardust',
    shader: 'galaxy'
  },
  neural: {
    colors: [0xFF5722, 0xFF9800, 0xFFC107],
    particles: 'synapses',
    shader: 'neural'
  },
  quantum: {
    colors: [0x00E5FF, 0x1DE9B6, 0x76FF03],
    particles: 'quantum',
    shader: 'quantum'
  },
  fractal: {
    colors: [0xE040FB, 0xFF4081, 0xFF6EC7],
    particles: 'fractal',
    shader: 'fractal'
  },
  conscience: {
    colors: [0xFFD600, 0xFF8F00, 0xFF3D00],
    particles: 'thoughts',
    shader: 'consciousness'
  },
  holographic: {
    colors: [0x00BCD4, 0x4FC3F7, 0x81D4FA],
    particles: 'hologram',
    shader: 'holographic'
  }
};

const EMOTION_STATES = {
  idle: { intensity: 0.2, speed: 1.0, color: 0x00bcd4 },
  thinking: { intensity: 0.5, speed: 0.5, color: 0xffc107 },
  excited: { intensity: 1.0, speed: 2.0, color: 0x4caf50 },
  processing: { intensity: 0.8, speed: 1.5, color: 0xff9800 },
  error: { intensity: 0.3, speed: 0.3, color: 0xf44336 },
  sleeping: { intensity: 0.1, speed: 0.2, color: 0x9c27b0 }
};

function Sphere3D({ 
  isListening = false, 
  isSpeaking = false, 
  audioLevel = 0,
  size = 200,
  color = '#00bcd4',
  theme = 'cyberpunk',
  emotion = 'idle',
  visualMode = 'spectrum',
  onSphereReady = null 
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const sphereRef = useRef(null);
  const cameraRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const composerRef = useRef(null);
  const particleSystemsRef = useRef([]);
  const emotionTweenRef = useRef(null);
  
  const [isReady, setIsReady] = useState(false);
  const [currentAudioLevel, setCurrentAudioLevel] = useState(0);
  const [currentEmotion, setCurrentEmotion] = useState(emotion);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Configuration des matériaux et shaders
  const sphereConfig = useMemo(() => ({
    baseRadius: size * 0.001,
    pulseMultiplier: 0.3,
    waveFrequency: 0.02,
    haloOpacity: 0.6,
    particleCount: 150,
    theme: SPHERE_THEMES[theme],
    emotion: EMOTION_STATES[currentEmotion]
  }), [size, theme, currentEmotion]);

  // Shaders avancés selon le thème
  const getAdvancedShader = (shaderType) => {
    const shaders = {
      neural: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vElevation;
          varying float vNoise;
          
          // Noise function pour effets organiques
          float noise(vec3 p) {
            return sin(p.x * 10.0) * sin(p.y * 10.0) * sin(p.z * 10.0);
          }
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // Bruit neuronal complexe
            float n1 = noise(position + time * 0.5);
            float n2 = noise(position * 2.0 + time * 0.3);
            float n3 = noise(position * 4.0 + time * 0.1);
            vNoise = (n1 + n2 * 0.5 + n3 * 0.25) / 1.75;
            
            // Synapses - connexions entre points
            float synapseEffect = sin(length(position) * 20.0 + time * 2.0) * audioLevel;
            
            // Déformation émotionnelle
            float emotionWave = sin(position.x * 5.0 + time * emotionIntensity) * 
                               cos(position.y * 5.0 + time * emotionIntensity) * 0.1;
            
            vec3 newPosition = position + normal * (vNoise * 0.1 + synapseEffect * 0.05 + emotionWave);
            vElevation = vNoise + synapseEffect;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform float audioLevel;
          uniform vec3 emotionColor;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vElevation;
          varying float vNoise;
          
          void main() {
            vec3 baseColor = emotionColor;
            
            // Effets de synapses
            float synapseGlow = abs(sin(vNoise * 10.0 + time * 3.0)) * audioLevel;
            
            // Réseau neuronal - lignes d'énergie
            float networkLines = step(0.95, abs(sin(vPosition.x * 50.0))) + 
                               step(0.95, abs(sin(vPosition.y * 50.0))) + 
                               step(0.95, abs(sin(vPosition.z * 50.0)));
            
            vec3 color = baseColor + vec3(synapseGlow) * 2.0 + vec3(networkLines) * 0.5;
            color *= (1.0 + emotionIntensity);
            
            // Effet Fresnel pour la lueur
            float fresnel = pow(1.0 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 2.0);
            color += fresnel * baseColor * 0.5;
            
            float alpha = 0.7 + vElevation * 0.3 + synapseGlow * 0.2;
            gl_FragColor = vec4(color, alpha);
          }
        `
      },
      galaxy: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vDistance;
          
          void main() {
            vPosition = position;
            vNormal = normal;
            vDistance = length(position);
            
            // Rotation spirale galactique
            float angle = time * 0.5 + vDistance * 2.0;
            mat3 rotation = mat3(
              cos(angle), -sin(angle), 0.0,
              sin(angle), cos(angle), 0.0,
              0.0, 0.0, 1.0
            );
            
            vec3 spiralPos = rotation * position;
            
            // Ondulations cosmiques
            float wave1 = sin(vDistance * 10.0 - time * 2.0) * audioLevel * 0.1;
            float wave2 = cos(vDistance * 15.0 + time * 1.5) * audioLevel * 0.05;
            
            vec3 newPosition = spiralPos + normal * (wave1 + wave2);
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vDistance;
          
          void main() {
            // Couleurs cosmiques
            vec3 purple = vec3(0.4, 0.1, 0.8);
            vec3 blue = vec3(0.1, 0.3, 1.0);
            vec3 pink = vec3(1.0, 0.2, 0.8);
            
            float t = sin(vDistance * 3.0 - time) * 0.5 + 0.5;
            vec3 cosmicColor = mix(mix(purple, blue, t), pink, sin(time * 0.5) * 0.5 + 0.5);
            
            // Étoiles scintillantes
            float stars = step(0.98, sin(vPosition.x * 100.0) * sin(vPosition.y * 100.0) * sin(vPosition.z * 100.0));
            cosmicColor += vec3(stars) * 0.8;
            
            // Nébuleuse
            float nebula = sin(vDistance * 5.0 + time) * 0.3 + 0.7;
            cosmicColor *= nebula;
            
            gl_FragColor = vec4(cosmicColor, 0.8);
          }
        `
      },
      neon: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vGlow;
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // Grid cyberpunk
            float gridX = abs(sin(position.x * 20.0 + time));
            float gridY = abs(sin(position.y * 20.0 + time));
            float gridZ = abs(sin(position.z * 20.0 + time));
            vGlow = max(max(gridX, gridY), gridZ) * audioLevel;
            
            // Déformation électronique
            float electronic = sin(position.x * 30.0 + time * 5.0) * 
                             cos(position.y * 30.0 + time * 3.0) * 0.02;
            
            vec3 newPosition = position + normal * electronic * emotionIntensity;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vGlow;
          
          void main() {
            vec3 cyan = vec3(0.0, 1.0, 1.0);
            vec3 magenta = vec3(1.0, 0.0, 1.0);
            vec3 yellow = vec3(1.0, 1.0, 0.0);
            
            // Alternance cyberpunk
            float t = sin(time * 2.0) * 0.5 + 0.5;
            vec3 neonColor = mix(cyan, magenta, t);
            neonColor = mix(neonColor, yellow, vGlow);
            
            // Lignes de code (effet Matrix)
            float codeLines = step(0.9, abs(sin(vPosition.y * 50.0 + time * 10.0)));
            neonColor += vec3(0.0, codeLines * 0.5, 0.0);
            
            // Glow effect
            neonColor *= (1.0 + vGlow * 3.0);
            
            gl_FragColor = vec4(neonColor, 0.9);
          }
        `
      },
      quantum: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vQuantumState;
          varying float vEntanglement;
          
          // Fonction de bruit quantique
          float quantumNoise(vec3 p, float t) {
            return sin(p.x * 15.0 + t) * cos(p.y * 15.0 + t * 1.3) * sin(p.z * 15.0 + t * 0.7);
          }
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // État quantique oscillant
            vQuantumState = quantumNoise(position, time * 2.0) * audioLevel;
            
            // Intrication quantique entre particules
            float dist = length(position);
            vEntanglement = sin(dist * 20.0 + time * 3.0) * audioLevel;
            
            // Superposition d'états - particule dans plusieurs positions
            vec3 state1 = position + normal * vQuantumState * 0.1;
            vec3 state2 = position - normal * vQuantumState * 0.1;
            vec3 quantumPosition = mix(state1, state2, sin(time * 10.0 + dist * 5.0) * 0.5 + 0.5);
            
            // Effet tunnel quantique
            float tunnel = sin(time * 5.0 + dist * 10.0) * emotionIntensity * 0.05;
            quantumPosition += normalize(position) * tunnel;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(quantumPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          uniform float audioLevel;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vQuantumState;
          varying float vEntanglement;
          
          void main() {
            // Couleurs quantiques
            vec3 cyan = vec3(0.0, 0.9, 1.0);
            vec3 green = vec3(0.1, 0.9, 0.3);
            vec3 blue = vec3(0.3, 0.6, 1.0);
            
            // Oscillation entre états quantiques
            float statePhase = sin(time * 5.0 + length(vPosition) * 10.0) * 0.5 + 0.5;
            vec3 quantumColor = mix(cyan, green, statePhase);
            quantumColor = mix(quantumColor, blue, vQuantumState * 0.5 + 0.5);
            
            // Particules intriquées (effet de liens)
            float entanglementGlow = abs(vEntanglement) * 2.0;
            quantumColor += vec3(entanglementGlow * 0.3, entanglementGlow * 0.5, entanglementGlow);
            
            // Probabilité quantique (opacité variable)
            float probability = abs(sin(vQuantumState * 3.0 + time * 2.0)) * 0.5 + 0.5;
            
            // Effet de superposition (flickering quantique)
            float superposition = step(0.7, sin(time * 20.0 + length(vPosition) * 30.0));
            quantumColor *= (1.0 + superposition * 0.5);
            
            gl_FragColor = vec4(quantumColor, probability * 0.8);
          }
        `
      },
      fractal: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vFractalDepth;
          varying float vIteration;
          
          // Fonction fractale Mandelbrot adaptée 3D
          float fractalPattern(vec3 p, float scale) {
            vec3 z = p * scale;
            float bailout = 4.0;
            float iterations = 0.0;
            
            for(int i = 0; i < 8; i++) {
              if(dot(z, z) > bailout) break;
              
              // Transformation fractale 3D
              z = vec3(
                z.x * z.x - z.y * z.y + p.x,
                2.0 * z.x * z.y + p.y,
                z.z * z.z + p.z
              ) * 0.8;
              
              iterations += 1.0;
            }
            
            return iterations / 8.0;
          }
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // Pattern fractal basé sur l'audio
            float scale = 2.0 + audioLevel * 3.0;
            vFractalDepth = fractalPattern(position + time * 0.1, scale);
            vIteration = fractalPattern(position * 2.0, scale + time * 0.2);
            
            // Déformation fractale
            vec3 fractalOffset = normal * vFractalDepth * 0.15 * emotionIntensity;
            
            // Auto-similarité à différentes échelles
            float selfSimilar1 = fractalPattern(position * 4.0, scale);
            float selfSimilar2 = fractalPattern(position * 8.0, scale);
            
            vec3 multiScale = fractalOffset + 
                             normal * selfSimilar1 * 0.05 + 
                             normal * selfSimilar2 * 0.025;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position + multiScale, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          uniform float audioLevel;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vFractalDepth;
          varying float vIteration;
          
          void main() {
            // Palette fractale
            vec3 purple = vec3(0.9, 0.2, 0.9);
            vec3 pink = vec3(1.0, 0.3, 0.5);
            vec3 magenta = vec3(1.0, 0.0, 0.8);
            
            // Couleur basée sur la profondeur fractale
            vec3 fractalColor = mix(purple, pink, vFractalDepth);
            fractalColor = mix(fractalColor, magenta, vIteration);
            
            // Motifs fractals complexes
            float pattern1 = sin(vFractalDepth * 20.0 + time * 2.0);
            float pattern2 = cos(vIteration * 15.0 + time * 1.5);
            float complexPattern = pattern1 * pattern2;
            
            fractalColor += vec3(complexPattern * 0.3);
            
            // Zoom fractal infini (effet psychédélique)
            float zoom = sin(time * 0.5) * 0.1 + 0.1;
            float infinitePattern = sin(length(vPosition) / zoom * 50.0 + time * 5.0);
            fractalColor *= (1.0 + infinitePattern * 0.4);
            
            // Brillance basée sur l'itération
            float brightness = vFractalDepth + vIteration * 0.5;
            fractalColor *= (0.8 + brightness * 0.7);
            
            gl_FragColor = vec4(fractalColor, 0.85);
          }
        `
      },
      consciousness: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vThoughtDensity;
          varying float vAwareness;
          
          // Simulation de "pensées" flottantes
          float thoughtWave(vec3 p, float t, float frequency) {
            return sin(p.x * frequency + t) * 
                   cos(p.y * frequency * 1.3 + t * 0.8) * 
                   sin(p.z * frequency * 0.7 + t * 1.2);
          }
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // Densité des pensées (basée sur l'audio)
            vThoughtDensity = (thoughtWave(position, time * 2.0, 8.0) + 
                              thoughtWave(position, time * 1.5, 12.0) +
                              thoughtWave(position, time * 3.0, 6.0)) / 3.0;
            vThoughtDensity *= audioLevel;
            
            // Niveau de conscience (vagues lentes)
            vAwareness = sin(length(position) * 3.0 + time * 0.8) * emotionIntensity;
            
            // Flux de conscience - mouvement organique
            vec3 consciousnessFlow = vec3(
              sin(time * 1.2 + position.x * 5.0),
              cos(time * 0.9 + position.y * 4.0),
              sin(time * 1.5 + position.z * 3.0)
            ) * 0.03;
            
            // Expansion de la conscience
            float expansion = (sin(time * 0.5) + 1.0) * 0.1 * emotionIntensity;
            vec3 expandedPosition = position * (1.0 + expansion);
            
            // Pensées qui émergent et disparaissent
            float thoughtBurst = vThoughtDensity * 0.1;
            vec3 finalPosition = expandedPosition + normal * thoughtBurst + consciousnessFlow;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(finalPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          uniform float audioLevel;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vThoughtDensity;
          varying float vAwareness;
          
          void main() {
            // Couleurs de la conscience
            vec3 gold = vec3(1.0, 0.8, 0.0);
            vec3 orange = vec3(1.0, 0.5, 0.0);
            vec3 red = vec3(1.0, 0.2, 0.0);
            
            // Mélange basé sur l'intensité des pensées
            float thoughtIntensity = abs(vThoughtDensity) * 0.5 + 0.5;
            vec3 consciousnessColor = mix(gold, orange, thoughtIntensity);
            consciousnessColor = mix(consciousnessColor, red, abs(vAwareness));
            
            // Neurones qui s'allument (pensées actives)
            float neuronFire = step(0.8, sin(vThoughtDensity * 15.0 + time * 10.0));
            consciousnessColor += vec3(neuronFire * 0.6);
            
            // Flux de conscience - ondulations
            float consciousnessRipple = sin(length(vPosition) * 10.0 - time * 3.0) * 0.3 + 0.7;
            consciousnessColor *= consciousnessRipple;
            
            // Moments d'illumination (flashs de compréhension)
            float illumination = sin(time * 0.3) > 0.95 ? 1.0 : 0.0;
            consciousnessColor += vec3(illumination * 0.8, illumination * 0.6, illumination * 0.2);
            
            // Intensité basée sur l'éveil
            consciousnessColor *= (0.7 + abs(vAwareness) * 0.8);
            
            // Transparence variable (pensées éphémères)
            float alpha = 0.6 + thoughtIntensity * 0.4;
            
            gl_FragColor = vec4(consciousnessColor, alpha);
          }
        `
      },
      holographic: {
        vertex: `
          uniform float time;
          uniform float audioLevel;
          uniform float emotionIntensity;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vHologramDepth;
          varying vec3 vHologramUV;
          
          void main() {
            vPosition = position;
            vNormal = normal;
            
            // Effet holographique - interférence de faisceaux
            float interference1 = sin(position.x * 25.0 + time * 2.0);
            float interference2 = sin(position.y * 20.0 + time * 1.5);
            float interference3 = sin(position.z * 30.0 + time * 2.5);
            
            vHologramDepth = (interference1 + interference2 + interference3) / 3.0;
            vHologramDepth *= audioLevel;
            
            // Coordonnées UV holographiques
            vHologramUV = position + vec3(time * 0.1, time * 0.15, time * 0.08);
            
            // Distorsion holographique (effet de projection)
            vec3 hologramDistortion = normal * vHologramDepth * 0.05 * emotionIntensity;
            
            // Stabilité holographique (vacillements)
            float stability = sin(time * 8.0) * 0.01 * audioLevel;
            vec3 flicker = vec3(
              sin(time * 12.0 + position.x * 10.0) * stability,
              cos(time * 10.0 + position.y * 10.0) * stability,
              sin(time * 14.0 + position.z * 10.0) * stability
            );
            
            // Effet de profondeur holographique
            float depth = sin(length(position) * 5.0 + time) * 0.02;
            vec3 depthOffset = normalize(position) * depth;
            
            vec3 finalPosition = position + hologramDistortion + flicker + depthOffset;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(finalPosition, 1.0);
          }
        `,
        fragment: `
          uniform float time;
          uniform vec3 emotionColor;
          uniform float audioLevel;
          varying vec3 vPosition;
          varying vec3 vNormal;
          varying float vHologramDepth;
          varying vec3 vHologramUV;
          
          void main() {
            // Couleurs holographiques
            vec3 cyan = vec3(0.0, 0.8, 1.0);
            vec3 lightBlue = vec3(0.3, 0.9, 1.0);
            vec3 white = vec3(0.9, 0.95, 1.0);
            
            // Lignes d'interférence holographiques
            float scanlines = sin(vHologramUV.y * 150.0 + time * 5.0);
            float verticalLines = sin(vHologramUV.x * 100.0);
            float interference = scanlines * verticalLines * 0.3 + 0.7;
            
            // Couleur base holographique
            float depth = abs(vHologramDepth) * 0.5 + 0.5;
            vec3 hologramColor = mix(cyan, lightBlue, depth);
            hologramColor = mix(hologramColor, white, interference * 0.4);
            
            // Effet de diffraction (prismatique)
            float diffraction = sin(vHologramDepth * 10.0 + time * 3.0);
            vec3 rainbow = vec3(
              sin(diffraction + 0.0) * 0.3 + 0.7,
              sin(diffraction + 2.09) * 0.3 + 0.7,  // 120 degrés
              sin(diffraction + 4.18) * 0.3 + 0.7   // 240 degrés
            );
            hologramColor *= rainbow;
            
            // Scintillement holographique
            float shimmer = sin(length(vHologramUV) * 20.0 + time * 8.0) * 0.2 + 0.8;
            hologramColor *= shimmer;
            
            // Effet de projection (plus transparent sur les bords)
            float projection = 1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0)));
            projection = pow(projection, 1.5);
            
            // Instabilité holographique
            float instability = sin(time * 15.0) * 0.1 + 0.9;
            hologramColor *= instability;
            
            // Alpha basé sur la profondeur et la projection
            float alpha = (depth + projection) * 0.4 + 0.3;
            alpha *= (0.8 + audioLevel * 0.5);
            
            gl_FragColor = vec4(hologramColor, alpha);
          }
        `
      }
    };
    
    return shaders[shaderType] || shaders.neural;
  };

  // Système de transition d'émotions
  const transitionToEmotion = (newEmotion, duration = 2000) => {
    if (isTransitioning || newEmotion === currentEmotion) return;
    
    setIsTransitioning(true);
    const startEmotion = EMOTION_STATES[currentEmotion];
    const targetEmotion = EMOTION_STATES[newEmotion];
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
      
      // Interpoler les propriétés émotionnelles
      const currentIntensity = startEmotion.intensity + (targetEmotion.intensity - startEmotion.intensity) * eased;
      const currentSpeed = startEmotion.speed + (targetEmotion.speed - startEmotion.speed) * eased;
      
      if (sphereRef.current?.material?.uniforms) {
        sphereRef.current.material.uniforms.emotionIntensity.value = currentIntensity;
        sphereRef.current.material.uniforms.emotionSpeed.value = currentSpeed;
      }
      
      if (progress < 1) {
        emotionTweenRef.current = requestAnimationFrame(animate);
      } else {
        setCurrentEmotion(newEmotion);
        setIsTransitioning(false);
      }
    };
    
    animate();
  };

  // Initialisation de la scène 3D
  useEffect(() => {
    if (!mountRef.current) return;

    // Scène, caméra, renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    // Configuration WebGL compatible AMD
    const getWebGLConfig = () => {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      
      if (!gl) {
        console.warn('⚠️ WebGL non supporté, fallback vers Canvas');
        return { antialias: false, alpha: true, powerPreference: "default" };
      }

      // Test support antialiasing
      const maxSamples = gl.getParameter(gl.MAX_SAMPLES);
      const antialiasSupported = maxSamples > 0;

      return {
        antialias: antialiasSupported,
        alpha: true,
        powerPreference: "default", // Laisser le navigateur décider (meilleur pour AMD)
        preserveDrawingBuffer: false, // Performance AMD
        failIfMajorPerformanceCaveat: false, // Autoriser fallbacks AMD
        precision: "mediump" // Meilleure compatibilité AMD
      };
    };

    const webglConfig = getWebGLConfig();
    const renderer = new THREE.WebGLRenderer(webglConfig);

    // Détection GPU et optimisations AMD
    const detectGPU = () => {
      const gl = renderer.getContext();
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      
      if (debugInfo) {
        const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        const rendererInfo = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        
        return {
          vendor: vendor.toLowerCase(),
          isAMD: vendor.includes('AMD') || vendor.includes('ATI') || vendor.includes('Radeon'),
          isNVIDIA: vendor.includes('NVIDIA'),
          renderer: rendererInfo,
          isIntegrated: rendererInfo.includes('Intel') || rendererInfo.includes('UHD')
        };
      }
      
      return { vendor: 'unknown', isAMD: false, isNVIDIA: false, isIntegrated: false };
    };

    const gpuInfo = detectGPU();
    console.log('🎮 GPU détecté:', gpuInfo);

    // Configuration du renderer adaptée AMD
    renderer.setSize(size, size);
    renderer.setClearColor(0x000000, 0);
    
    // Optimisations AMD pour les ombres
    if (gpuInfo.isAMD || gpuInfo.isIntegrated) {
      renderer.shadowMap.enabled = false; // Désactiver sur AMD pour performance
      renderer.shadowMap.type = THREE.BasicShadowMap;
      renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // Meilleur sur AMD
      renderer.toneMapping = THREE.LinearToneMapping; // Plus compatible
      renderer.toneMappingExposure = 1.0;
      console.log('📊 Optimisations AMD appliquées');
    } else {
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
    }

    // Positionnement de la caméra
    camera.position.z = 2;

    // Sphère principale avec matériau réactif avancé
    const sphereGeometry = new THREE.SphereGeometry(sphereConfig.baseRadius, 128, 128);
    
    // Shader personnalisé selon le thème
    const currentShader = getAdvancedShader(sphereConfig.theme.shader);
    const sphereMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioLevel: { value: 0 },
        baseColor: { value: new THREE.Color(color) },
        emotionColor: { value: new THREE.Color(sphereConfig.emotion.color) },
        pulseIntensity: { value: 0 },
        emotionIntensity: { value: sphereConfig.emotion.intensity },
        emotionSpeed: { value: sphereConfig.emotion.speed },
        isListening: { value: false },
        isSpeaking: { value: false },
        themeColors: { 
          value: sphereConfig.theme.colors.map(c => new THREE.Color(c))
        }
      },
      vertexShader: currentShader.vertex,
      fragmentShader: currentShader.fragment,
      transparent: true,
      side: THREE.DoubleSide
    });

    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    scene.add(sphere);
    
    // Post-processing adaptatif selon GPU
    const setupPostProcessing = () => {
      const composer = new EffectComposer(renderer);
      const renderPass = new RenderPass(scene, camera);
      composer.addPass(renderPass);
      
      if (gpuInfo.isAMD || gpuInfo.isIntegrated) {
        // Configuration légère pour AMD
        console.log('🔧 Post-processing allégé pour GPU AMD/Intégré');
        
        const bloomPass = new UnrealBloomPass(
          new THREE.Vector2(size, size),
          0.2,  // strength réduite
          0.6,  // radius augmenté  
          0.3   // threshold augmenté
        );
        composer.addPass(bloomPass);
        
        // Pas de glitch ni film sur AMD (trop lourd)
        
      } else {
        // Configuration complète pour NVIDIA
        console.log('⚡ Post-processing complet pour GPU haute performance');
        
        const bloomPass = new UnrealBloomPass(
          new THREE.Vector2(size, size),
          0.5,  // strength normale
          0.4,  // radius
          0.1   // threshold
        );
        composer.addPass(bloomPass);
        
        const glitchPass = new GlitchPass();
        glitchPass.enabled = false;
        composer.addPass(glitchPass);
        
        const filmPass = new FilmPass(0.1, 0.025, 648, false);
        filmPass.enabled = sphereConfig.theme.shader === 'neural';
        composer.addPass(filmPass);
      }
      
      return composer;
    };

    const composer = setupPostProcessing();
    composerRef.current = composer;

    // Lumières
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(color, 1, 100);
    pointLight.position.set(1, 1, 1);
    pointLight.castShadow = true;
    scene.add(pointLight);

    // Système de particules avancé selon le thème
    const createAdvancedParticles = (particleType) => {
      const systems = [];
      
      switch (particleType) {
        case 'matrix':
          // Particules en cascade (effet Matrix)
          for (let i = 0; i < 3; i++) {
            const geometry = new THREE.BufferGeometry();
            const count = 100;
            const positions = new Float32Array(count * 3);
            const colors = new Float32Array(count * 3);
            
            for (let j = 0; j < count; j++) {
              positions[j * 3] = (Math.random() - 0.5) * 2;
              positions[j * 3 + 1] = Math.random() * 4 - 2;
              positions[j * 3 + 2] = (Math.random() - 0.5) * 2;
              
              colors[j * 3] = 0;
              colors[j * 3 + 1] = Math.random();
              colors[j * 3 + 2] = 0.2;
            }
            
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            const material = new THREE.PointsMaterial({
              size: 0.02,
              vertexColors: true,
              transparent: true,
              opacity: 0.8,
              blending: THREE.AdditiveBlending
            });
            
            systems.push(new THREE.Points(geometry, material));
          }
          break;
          
        case 'stardust':
          // Poussière d'étoiles orbitale
          const starGeometry = new THREE.BufferGeometry();
          const starCount = sphereConfig.particleCount;
          const starPositions = new Float32Array(starCount * 3);
          const starSizes = new Float32Array(starCount);
          
          for (let i = 0; i < starCount; i++) {
            const radius = sphereConfig.baseRadius * (2 + Math.random() * 3);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            starPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            starPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            starPositions[i * 3 + 2] = radius * Math.cos(phi);
            starSizes[i] = Math.random() * 0.03 + 0.01;
          }
          
          starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
          starGeometry.setAttribute('size', new THREE.BufferAttribute(starSizes, 1));
          
          const starMaterial = new THREE.ShaderMaterial({
            uniforms: {
              time: { value: 0 },
              color: { value: new THREE.Color(0x6A0DAD) }
            },
            vertexShader: `
              attribute float size;
              uniform float time;
              varying float vAlpha;
              
              void main() {
                vAlpha = sin(time + position.x * 10.0) * 0.5 + 0.5;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                gl_PointSize = size * 300.0 / -mvPosition.z * vAlpha;
                gl_Position = projectionMatrix * mvPosition;
              }
            `,
            fragmentShader: `
              uniform vec3 color;
              varying float vAlpha;
              
              void main() {
                float dist = distance(gl_PointCoord, vec2(0.5));
                if (dist > 0.5) discard;
                
                float alpha = (1.0 - dist * 2.0) * vAlpha;
                gl_FragColor = vec4(color, alpha);
              }
            `,
            transparent: true,
            blending: THREE.AdditiveBlending
          });
          
          systems.push(new THREE.Points(starGeometry, starMaterial));
          break;
          
        case 'synapses':
          // Connexions synaptiques
          const synapseGeometry = new THREE.BufferGeometry();
          const synapseCount = 50;
          const synapsePositions = new Float32Array(synapseCount * 6); // Lignes
          
          for (let i = 0; i < synapseCount; i++) {
            // Point de départ
            const radius1 = sphereConfig.baseRadius * (1.2 + Math.random() * 0.3);
            const theta1 = Math.random() * Math.PI * 2;
            const phi1 = Math.acos(Math.random() * 2 - 1);
            
            // Point d'arrivée
            const radius2 = sphereConfig.baseRadius * (1.2 + Math.random() * 0.3);
            const theta2 = Math.random() * Math.PI * 2;
            const phi2 = Math.acos(Math.random() * 2 - 1);
            
            synapsePositions[i * 6] = radius1 * Math.sin(phi1) * Math.cos(theta1);
            synapsePositions[i * 6 + 1] = radius1 * Math.sin(phi1) * Math.sin(theta1);
            synapsePositions[i * 6 + 2] = radius1 * Math.cos(phi1);
            
            synapsePositions[i * 6 + 3] = radius2 * Math.sin(phi2) * Math.cos(theta2);
            synapsePositions[i * 6 + 4] = radius2 * Math.sin(phi2) * Math.sin(theta2);
            synapsePositions[i * 6 + 5] = radius2 * Math.cos(phi2);
          }
          
          synapseGeometry.setAttribute('position', new THREE.BufferAttribute(synapsePositions, 3));
          
          const synapseMaterial = new THREE.LineBasicMaterial({
            color: 0xFF5722,
            transparent: true,
            opacity: 0.3,
            blending: THREE.AdditiveBlending
          });
          
          systems.push(new THREE.LineSegments(synapseGeometry, synapseMaterial));
          break;
          
        case 'quantum':
          // Particules quantiques entrelacées
          const quantumGeometry = new THREE.BufferGeometry();
          const quantumCount = sphereConfig.particleCount * 1.5;
          const quantumPositions = new Float32Array(quantumCount * 3);
          const quantumColors = new Float32Array(quantumCount * 3);
          const quantumSizes = new Float32Array(quantumCount);
          
          for (let i = 0; i < quantumCount; i++) {
            // États quantiques superposés
            const radius = sphereConfig.baseRadius * (1.2 + Math.random() * 0.8);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            quantumPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            quantumPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            quantumPositions[i * 3 + 2] = radius * Math.cos(phi);
            
            // Couleurs quantiques
            const quantumPhase = Math.random() * Math.PI * 2;
            quantumColors[i * 3] = 0.2 + Math.sin(quantumPhase) * 0.8;
            quantumColors[i * 3 + 1] = 0.8 + Math.cos(quantumPhase) * 0.2;
            quantumColors[i * 3 + 2] = 0.9 + Math.sin(quantumPhase + Math.PI) * 0.1;
            
            quantumSizes[i] = Math.random() * 0.02 + 0.005;
          }
          
          quantumGeometry.setAttribute('position', new THREE.BufferAttribute(quantumPositions, 3));
          quantumGeometry.setAttribute('color', new THREE.BufferAttribute(quantumColors, 3));
          quantumGeometry.setAttribute('size', new THREE.BufferAttribute(quantumSizes, 1));
          
          const quantumMaterial = new THREE.PointsMaterial({
            size: 0.015,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
          });
          
          quantumMaterial.userData = { type: 'quantum' };
          systems.push(new THREE.Points(quantumGeometry, quantumMaterial));
          break;
          
        case 'fractal':
          // Particules fractales auto-similaires
          const fractalGeometry = new THREE.BufferGeometry();
          const fractalCount = sphereConfig.particleCount * 2;
          const fractalPositions = new Float32Array(fractalCount * 3);
          const fractalColors = new Float32Array(fractalCount * 3);
          
          // Générateur fractal Sierpinski 3D
          const generateSierpinski = (depth, scale, center) => {
            if (depth === 0) return [center];
            
            const subPoints = [];
            const vertices = [
              [-scale, -scale, -scale],
              [scale, -scale, -scale],
              [0, scale, -scale],
              [0, 0, scale]
            ];
            
            vertices.forEach(vertex => {
              const newCenter = [
                center[0] + vertex[0] * 0.5,
                center[1] + vertex[1] * 0.5,
                center[2] + vertex[2] * 0.5
              ];
              subPoints.push(...generateSierpinski(depth - 1, scale * 0.5, newCenter));
            });
            
            return subPoints;
          };
          
          const fractalPoints = generateSierpinski(3, sphereConfig.baseRadius, [0, 0, 0]);
          
          for (let i = 0; i < Math.min(fractalCount, fractalPoints.length); i++) {
            const point = fractalPoints[i];
            fractalPositions[i * 3] = point[0];
            fractalPositions[i * 3 + 1] = point[1];
            fractalPositions[i * 3 + 2] = point[2];
            
            // Couleurs fractales
            const depth = Math.floor(i / Math.pow(4, Math.floor(Math.log(i + 1) / Math.log(4))));
            fractalColors[i * 3] = 0.9;     // R - Magenta
            fractalColors[i * 3 + 1] = 0.2 + depth * 0.2; // G
            fractalColors[i * 3 + 2] = 0.9; // B
          }
          
          fractalGeometry.setAttribute('position', new THREE.BufferAttribute(fractalPositions, 3));
          fractalGeometry.setAttribute('color', new THREE.BufferAttribute(fractalColors, 3));
          
          const fractalMaterial = new THREE.PointsMaterial({
            size: 0.008,
            vertexColors: true,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending
          });
          
          fractalMaterial.userData = { type: 'fractal' };
          systems.push(new THREE.Points(fractalGeometry, fractalMaterial));
          break;
          
        case 'thoughts':
          // Particules de pensées (consciousness)
          const thoughtGeometry = new THREE.BufferGeometry();
          const thoughtCount = sphereConfig.particleCount;
          const thoughtPositions = new Float32Array(thoughtCount * 3);
          const thoughtColors = new Float32Array(thoughtCount * 3);
          const thoughtOpacity = new Float32Array(thoughtCount);
          
          for (let i = 0; i < thoughtCount; i++) {
            // Distribution organique des pensées
            const radius = sphereConfig.baseRadius * (0.8 + Math.random() * 1.2);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            // Ajout de bruit pour mouvement organique
            const noiseX = (Math.random() - 0.5) * 0.3;
            const noiseY = (Math.random() - 0.5) * 0.3;
            const noiseZ = (Math.random() - 0.5) * 0.3;
            
            thoughtPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta) + noiseX;
            thoughtPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta) + noiseY;
            thoughtPositions[i * 3 + 2] = radius * Math.cos(phi) + noiseZ;
            
            // Couleurs de la conscience (doré-orange-rouge)
            const consciousness = Math.random();
            thoughtColors[i * 3] = 1.0;     // R - Or/Rouge
            thoughtColors[i * 3 + 1] = 0.6 + consciousness * 0.4; // G - Vers orange
            thoughtColors[i * 3 + 2] = 0.1 + consciousness * 0.2; // B - Peu de bleu
            
            thoughtOpacity[i] = 0.3 + Math.random() * 0.7; // Pensées éphémères
          }
          
          thoughtGeometry.setAttribute('position', new THREE.BufferAttribute(thoughtPositions, 3));
          thoughtGeometry.setAttribute('color', new THREE.BufferAttribute(thoughtColors, 3));
          
          const thoughtMaterial = new THREE.PointsMaterial({
            size: 0.012,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
          });
          
          thoughtMaterial.userData = { type: 'thoughts' };
          systems.push(new THREE.Points(thoughtGeometry, thoughtMaterial));
          break;
          
        case 'hologram':
          // Particules holographiques avec effet de projection
          const hologramGeometry = new THREE.BufferGeometry();
          const hologramCount = sphereConfig.particleCount * 1.2;
          const hologramPositions = new Float32Array(hologramCount * 3);
          const hologramColors = new Float32Array(hologramCount * 3);
          
          for (let i = 0; i < hologramCount; i++) {
            const radius = sphereConfig.baseRadius * (1.1 + Math.random() * 0.4);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            hologramPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            hologramPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            hologramPositions[i * 3 + 2] = radius * Math.cos(phi);
            
            // Couleurs holographiques cyan-bleu-blanc
            const hologramPhase = (i / hologramCount) * Math.PI * 4; // Cycle de couleur
            hologramColors[i * 3] = 0.3 + Math.sin(hologramPhase) * 0.3;        // R
            hologramColors[i * 3 + 1] = 0.8 + Math.cos(hologramPhase) * 0.2;    // G - Cyan
            hologramColors[i * 3 + 2] = 1.0;                                     // B - Bleu fort
          }
          
          hologramGeometry.setAttribute('position', new THREE.BufferAttribute(hologramPositions, 3));
          hologramGeometry.setAttribute('color', new THREE.BufferAttribute(hologramColors, 3));
          
          const hologramMaterial = new THREE.PointsMaterial({
            size: 0.01,
            vertexColors: true,
            transparent: true,
            opacity: 0.5,
            blending: THREE.AdditiveBlending
          });
          
          hologramMaterial.userData = { type: 'hologram' };
          systems.push(new THREE.Points(hologramGeometry, hologramMaterial));
          break;
          
        default:
          // Particules classiques
          const defaultGeometry = new THREE.BufferGeometry();
          const defaultCount = sphereConfig.particleCount;
          const defaultPositions = new Float32Array(defaultCount * 3);
          
          for (let i = 0; i < defaultCount; i++) {
            const radius = sphereConfig.baseRadius * (1.5 + Math.random() * 0.5);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            defaultPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            defaultPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            defaultPositions[i * 3 + 2] = radius * Math.cos(phi);
          }
          
          defaultGeometry.setAttribute('position', new THREE.BufferAttribute(defaultPositions, 3));
          
          const defaultMaterial = new THREE.PointsMaterial({
            color: color,
            size: 0.01,
            transparent: true,
            opacity: sphereConfig.haloOpacity,
            blending: THREE.AdditiveBlending
          });
          
          systems.push(new THREE.Points(defaultGeometry, defaultMaterial));
      }
      
      return systems;
    };

    const particleSystems = createAdvancedParticles(sphereConfig.theme.particles);
    particleSystems.forEach(system => {
      scene.add(system);
      particleSystemsRef.current.push(system);
    });

    // Stockage des références
    sceneRef.current = scene;
    rendererRef.current = renderer;
    sphereRef.current = sphere;
    cameraRef.current = camera;

    // Ajout au DOM
    mountRef.current.appendChild(renderer.domElement);

    setIsReady(true);
    if (onSphereReady) {
      onSphereReady({ scene, renderer, sphere, camera });
    }

    // Animation loop
    const animate = () => {
      animationRef.current = requestAnimationFrame(animate);
      
      const time = Date.now() * 0.001;
      
      // Mise à jour des uniforms du shader
      if (sphere.material.uniforms) {
        sphere.material.uniforms.time.value = time;
        sphere.material.uniforms.audioLevel.value = currentAudioLevel;
        sphere.material.uniforms.isListening.value = isListening;
        sphere.material.uniforms.isSpeaking.value = isSpeaking;
        sphere.material.uniforms.pulseIntensity.value = Math.max(currentAudioLevel, 0.1);
      }
      
      // Rotation de la sphère selon l'émotion
      const emotionState = EMOTION_STATES[currentEmotion];
      sphere.rotation.y += 0.01 * emotionState.speed;
      sphere.rotation.x += 0.005 * emotionState.speed;
      
      // Animation des systèmes de particules
      particleSystemsRef.current.forEach((system, index) => {
        if (system.material.uniforms?.time) {
          system.material.uniforms.time.value = time;
        }
        
        switch (sphereConfig.theme.particles) {
          case 'matrix':
            system.rotation.y += 0.001;
            // Effet de chute pour les particules Matrix
            const positions = system.geometry.attributes.position.array;
            for (let i = 1; i < positions.length; i += 3) {
              positions[i] -= 0.02; // Chute vers le bas
              if (positions[i] < -2) positions[i] = 2; // Reset en haut
            }
            system.geometry.attributes.position.needsUpdate = true;
            break;
            
          case 'stardust':
            system.rotation.y += 0.003;
            system.rotation.z += 0.001;
            break;
            
          case 'synapses':
            // Pulsation des connexions synaptiques
            if (system.material.opacity) {
              system.material.opacity = 0.3 + Math.sin(time * 3) * 0.2 * currentAudioLevel;
            }
            break;
            
          case 'quantum':
            // Animation quantique - particules en superposition d'états
            if (system.geometry.attributes.position) {
              const positions = system.geometry.attributes.position.array;
              const colors = system.geometry.attributes.color.array;
              
              for (let i = 0; i < positions.length; i += 3) {
                // Oscillation quantique
                const quantumPhase = time * 5.0 + i * 0.1;
                const entanglement = Math.sin(quantumPhase) * currentAudioLevel * 0.1;
                
                positions[i] += entanglement * Math.sin(quantumPhase);
                positions[i + 1] += entanglement * Math.cos(quantumPhase);
                positions[i + 2] += entanglement * Math.sin(quantumPhase * 1.3);
                
                // Couleurs quantiques changeantes
                const colorIndex = Math.floor(i / 3);
                colors[colorIndex * 3] = 0.2 + Math.sin(quantumPhase + time) * 0.4;
                colors[colorIndex * 3 + 1] = 0.8 + Math.cos(quantumPhase + time) * 0.2;
                colors[colorIndex * 3 + 2] = 0.9 + Math.sin(quantumPhase + time + Math.PI) * 0.1;
              }
              
              system.geometry.attributes.position.needsUpdate = true;
              system.geometry.attributes.color.needsUpdate = true;
            }
            
            // Rotation quantique probabiliste
            system.rotation.y += (Math.sin(time * 2) + 1) * 0.002 * currentAudioLevel;
            system.rotation.z += (Math.cos(time * 1.7) + 1) * 0.001 * currentAudioLevel;
            break;
            
          case 'fractal':
            // Animation fractale - zoom et rotation auto-similaires
            system.rotation.y += 0.001 * (1 + currentAudioLevel);
            system.rotation.x += 0.0005 * (1 + currentAudioLevel);
            
            // Pulsation fractale basée sur l'audio
            const fractalPulse = 1 + Math.sin(time * 2) * 0.1 * currentAudioLevel;
            system.scale.setScalar(fractalPulse);
            
            // Couleurs fractales évolutives
            if (system.geometry.attributes.color) {
              const colors = system.geometry.attributes.color.array;
              for (let i = 0; i < colors.length; i += 3) {
                const fractalPhase = time * 0.5 + i * 0.01;
                colors[i] = 0.9;     // R constant
                colors[i + 1] = 0.2 + Math.sin(fractalPhase) * 0.3; // G variable
                colors[i + 2] = 0.9 - Math.cos(fractalPhase) * 0.2; // B variable
              }
              system.geometry.attributes.color.needsUpdate = true;
            }
            break;
            
          case 'thoughts':
            // Animation des pensées - mouvement organique et éphémère
            if (system.geometry.attributes.position) {
              const positions = system.geometry.attributes.position.array;
              
              for (let i = 0; i < positions.length; i += 3) {
                // Flux de conscience - mouvement lent et organique
                const thoughtPhase = time * 0.8 + i * 0.05;
                const consciousnessFlow = currentAudioLevel * 0.05;
                
                positions[i] += Math.sin(thoughtPhase + time * 1.2) * consciousnessFlow;
                positions[i + 1] += Math.cos(thoughtPhase + time * 0.9) * consciousnessFlow;
                positions[i + 2] += Math.sin(thoughtPhase + time * 1.5) * consciousnessFlow;
              }
              
              system.geometry.attributes.position.needsUpdate = true;
            }
            
            // Opacité variable (pensées qui apparaissent et disparaissent)
            system.material.opacity = 0.4 + Math.sin(time * 1.2) * 0.3 * (1 + currentAudioLevel);
            
            // Rotation lente de la conscience
            system.rotation.y += 0.0005;
            break;
            
          case 'hologram':
            // Animation holographique - instabilité et scintillement
            
            // Instabilité holographique (glitch)
            const instability = currentAudioLevel * 0.02;
            system.position.x = Math.sin(time * 15) * instability;
            system.position.y = Math.cos(time * 12) * instability;
            
            // Scintillement holographique
            system.material.opacity = 0.4 + Math.sin(time * 8) * 0.2 + currentAudioLevel * 0.3;
            
            // Rotation holographique stable
            system.rotation.y += 0.002;
            
            // Effet de scan holographique
            if (system.geometry.attributes.color) {
              const colors = system.geometry.attributes.color.array;
              for (let i = 0; i < colors.length; i += 3) {
                const scanPhase = time * 3 + (i / 3) * 0.1;
                const scanIntensity = Math.sin(scanPhase) * 0.3 + 0.7;
                
                colors[i] = (0.3 + Math.sin(scanPhase) * 0.3) * scanIntensity;
                colors[i + 1] = (0.8 + Math.cos(scanPhase) * 0.2) * scanIntensity;
                colors[i + 2] = 1.0 * scanIntensity;
              }
              system.geometry.attributes.color.needsUpdate = true;
            }
            break;
            
          default:
            system.rotation.y += 0.002;
            system.rotation.z += 0.001;
        }
      });
      
      // Pulse basé sur l'audio et l'émotion
      const emotionPulse = 1 + Math.sin(time * emotionState.speed) * emotionState.intensity * 0.1;
      const audioPulse = 1 + currentAudioLevel * sphereConfig.pulseMultiplier;
      sphere.scale.setScalar(emotionPulse * audioPulse);
      
      // Gestion des effets post-processing selon l'émotion
      if (composerRef.current) {
        const composer = composerRef.current;
        const passes = composer.passes;
        
        // Bloom intensity selon l'audio
        if (passes[1] && passes[1].strength !== undefined) {
          passes[1].strength = 0.5 + currentAudioLevel * 0.5;
        }
        
        // Glitch pour les émotions intenses
        if (passes[2] && passes[2].enabled !== undefined) {
          passes[2].enabled = (currentEmotion === 'error' || currentEmotion === 'processing') && currentAudioLevel > 0.5;
        }
        
        composer.render();
      } else {
        renderer.render(scene, camera);
      }
    };
    
    animate();

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
      sphereGeometry.dispose();
      sphereMaterial.dispose();
    };
  }, [size, color, sphereConfig, isListening, isSpeaking, currentAudioLevel]);

  // Mise à jour du niveau audio
  useEffect(() => {
    setCurrentAudioLevel(audioLevel);
  }, [audioLevel]);

  // Méthode pour analyser l'audio en temps réel
  const startAudioAnalysis = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      const updateAudioLevel = () => {
        if (!analyserRef.current) return;
        
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);
        
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        const normalizedLevel = Math.min(average / 255, 1.0);
        
        setCurrentAudioLevel(normalizedLevel);
        
        if (isListening) {
          requestAnimationFrame(updateAudioLevel);
        }
      };
      
      if (isListening) {
        updateAudioLevel();
      }
    } catch (error) {
      console.warn('Impossible d\'accéder au microphone:', error);
    }
  };

  // Démarrer/arrêter l'analyse audio selon l'état
  useEffect(() => {
    if (isListening && !audioContextRef.current) {
      startAudioAnalysis();
    } else if (!isListening && audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
      setCurrentAudioLevel(0);
    }
  }, [isListening]);

  // Transition d'émotion si demandée
  useEffect(() => {
    if (emotion !== currentEmotion) {
      transitionToEmotion(emotion);
    }
  }, [emotion]);

  // Méthodes publiques
  const sphereAPI = {
    pulse: (intensity = 1.0, duration = 1000) => {
      if (!sphereRef.current) return;
      
      const startScale = sphereRef.current.scale.x;
      const targetScale = startScale * (1 + intensity * 0.5);
      const startTime = Date.now();
      
      const animatePulse = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        
        const currentScale = startScale + (targetScale - startScale) * Math.sin(easeProgress * Math.PI);
        sphereRef.current.scale.setScalar(currentScale);
        
        if (progress < 1) {
          requestAnimationFrame(animatePulse);
        } else {
          sphereRef.current.scale.setScalar(startScale);
        }
      };
      
      animatePulse();
    },
    
    setGlow: (intensity = 1.0) => {
      if (!sphereRef.current?.material?.uniforms) return;
      sphereRef.current.material.uniforms.audioLevel.value = intensity;
    }
  };

  // Modes de visualisation
  const switchVisualizationMode = (mode) => {
    if (!sphereRef.current) return;
    
    const newShader = getAdvancedShader(SPHERE_THEMES[mode]?.shader || 'neural');
    sphereRef.current.material.vertexShader = newShader.vertex;
    sphereRef.current.material.fragmentShader = newShader.fragment;
    sphereRef.current.material.needsUpdate = true;
  };

  // API publique étendue
  const extendedSphereAPI = {
    ...sphereAPI,
    
    changeTheme: (newTheme) => {
      if (SPHERE_THEMES[newTheme]) {
        switchVisualizationMode(newTheme);
      }
    },
    
    setEmotion: (newEmotion, duration = 2000) => {
      transitionToEmotion(newEmotion, duration);
    },
    
    activateGlitch: (duration = 1000) => {
      if (composerRef.current?.passes[2]) {
        const glitchPass = composerRef.current.passes[2];
        glitchPass.enabled = true;
        setTimeout(() => {
          glitchPass.enabled = false;
        }, duration);
      }
    },
    
    pulseEmotion: (emotionType = 'excited', intensity = 1.0) => {
      const tempEmotion = currentEmotion;
      transitionToEmotion(emotionType, 500);
      setTimeout(() => {
        transitionToEmotion(tempEmotion, 500);
      }, 1000);
    },
    
    getCurrentEmotion: () => currentEmotion,
    getCurrentTheme: () => theme,
    getAudioLevel: () => currentAudioLevel
  };

  // Exposition de l'API étendue
  useEffect(() => {
    if (isReady && onSphereReady) {
      onSphereReady(extendedSphereAPI);
    }
  }, [isReady, currentEmotion, theme, currentAudioLevel]);

  return (
    <Box
      ref={mountRef}
      sx={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'scale(1.05)'
        }
      }}
    />
  );
}

export default Sphere3D;