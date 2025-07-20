/**
 * 🌐 JARVIS UI - Sphère 3D Audio-Réactive
 * Composant 3D central qui réagit aux sons de l'utilisateur et de JARVIS
 */
import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Box } from '@mui/material';
import * as THREE from 'three';

function Sphere3D({ 
  isListening = false, 
  isSpeaking = false, 
  audioLevel = 0,
  size = 200,
  color = '#00bcd4',
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
  
  const [isReady, setIsReady] = useState(false);
  const [currentAudioLevel, setCurrentAudioLevel] = useState(0);

  // Configuration des matériaux et shaders
  const sphereConfig = useMemo(() => ({
    baseRadius: size * 0.001,
    pulseMultiplier: 0.3,
    waveFrequency: 0.02,
    haloOpacity: 0.6,
    particleCount: 100
  }), [size]);

  // Initialisation de la scène 3D
  useEffect(() => {
    if (!mountRef.current) return;

    // Scène, caméra, renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: "high-performance"
    });

    // Configuration du renderer
    renderer.setSize(size, size);
    renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Positionnement de la caméra
    camera.position.z = 2;

    // Sphère principale avec matériau réactif
    const sphereGeometry = new THREE.SphereGeometry(sphereConfig.baseRadius, 64, 64);
    
    // Shader personnalisé pour les effets audio
    const sphereMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        audioLevel: { value: 0 },
        baseColor: { value: new THREE.Color(color) },
        pulseIntensity: { value: 0 },
        isListening: { value: false },
        isSpeaking: { value: false }
      },
      vertexShader: `
        uniform float time;
        uniform float audioLevel;
        uniform float pulseIntensity;
        varying vec3 vPosition;
        varying vec3 vNormal;
        varying float vElevation;
        
        void main() {
          vPosition = position;
          vNormal = normal;
          
          // Déformation basée sur l'audio
          float elevation = sin(position.x * 10.0 + time) * 
                          sin(position.y * 10.0 + time) * 
                          sin(position.z * 10.0 + time) * 
                          audioLevel * 0.1;
          
          // Pulse global
          float pulse = 1.0 + sin(time * 2.0) * pulseIntensity * 0.2;
          
          vec3 newPosition = position * pulse + normal * elevation;
          vElevation = elevation;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
        }
      `,
      fragmentShader: `
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
          
          // Couleur selon l'état
          if (isListening) {
            color = mix(baseColor, vec3(0.0, 1.0, 0.3), 0.5); // Vert pour écoute
          } else if (isSpeaking) {
            color = mix(baseColor, vec3(1.0, 0.3, 0.0), 0.5); // Orange pour parole
          }
          
          // Effets audio
          float intensity = 1.0 + audioLevel * 2.0;
          color *= intensity;
          
          // Effet de Fresnel
          float fresnel = pow(1.0 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 2.0);
          color = mix(color, vec3(1.0), fresnel * 0.3);
          
          // Alpha basé sur l'élévation pour l'effet de halo
          float alpha = 0.8 + vElevation * 2.0;
          
          gl_FragColor = vec4(color, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide
    });

    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    scene.add(sphere);

    // Lumières
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(color, 1, 100);
    pointLight.position.set(1, 1, 1);
    pointLight.castShadow = true;
    scene.add(pointLight);

    // Particules orbitales (halo)
    const createParticles = () => {
      const particlesGeometry = new THREE.BufferGeometry();
      const particleCount = sphereConfig.particleCount;
      const positions = new Float32Array(particleCount * 3);
      
      for (let i = 0; i < particleCount; i++) {
        // Distribution sphérique
        const radius = sphereConfig.baseRadius * (1.5 + Math.random() * 0.5);
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        
        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);
      }
      
      particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      
      const particleMaterial = new THREE.PointsMaterial({
        color: color,
        size: 0.01,
        transparent: true,
        opacity: sphereConfig.haloOpacity,
        blending: THREE.AdditiveBlending
      });
      
      return new THREE.Points(particlesGeometry, particleMaterial);
    };

    const particles = createParticles();
    scene.add(particles);

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
      
      // Rotation de la sphère
      sphere.rotation.y += 0.01;
      sphere.rotation.x += 0.005;
      
      // Animation des particules
      particles.rotation.y += 0.002;
      particles.rotation.z += 0.001;
      
      // Pulse basé sur l'audio
      const pulseScale = 1 + currentAudioLevel * sphereConfig.pulseMultiplier;
      sphere.scale.setScalar(pulseScale);
      
      renderer.render(scene, camera);
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

  // Exposition de l'API
  useEffect(() => {
    if (isReady && onSphereReady) {
      onSphereReady(sphereAPI);
    }
  }, [isReady]);

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