/**
 * 🎤 Voice Waveform Component - Visualisation audio style JARVIS
 * Affiche des ondes audio animées en temps réel avec effets holographiques
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useJarvis } from '../contexts/JarvisContext';

const VoiceWaveform = ({ 
  width = 400, 
  height = 150, 
  barCount = 64,
  barWidth = 3,
  barSpacing = 2,
  color = '#00d4ff',
  glowColor = '#00d4ff',
  showStatus = true,
  fftSize = 2048,
  smoothingTimeConstant = 0.8,
  minDecibels = -80,
  maxDecibels = -10
}) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  
  const [status, setStatus] = useState('IDLE');
  const [isInitialized, setIsInitialized] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const { state } = useJarvis();
  
  // Initialisation de Web Audio API
  const initializeAudio = useCallback(async () => {
    try {
      // Créer le contexte audio
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      
      // Créer l'analyseur
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = fftSize;
      analyserRef.current.smoothingTimeConstant = smoothingTimeConstant;
      analyserRef.current.minDecibels = minDecibels;
      analyserRef.current.maxDecibels = maxDecibels;
      
      // Créer le tableau de données
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
      
      // Obtenir l'accès au microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      streamRef.current = stream;
      
      // Connecter le microphone à l'analyseur
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);
      
      setIsInitialized(true);
      setStatus('LISTENING');
      
    } catch (error) {
      console.error('Erreur lors de l\'initialisation audio:', error);
      setStatus('ERROR');
    }
  }, [fftSize, smoothingTimeConstant, minDecibels, maxDecibels]);
  
  // Fonction de dessin des barres
  const drawBars = useCallback((ctx, dataArray) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Effacer le canvas avec un effet de traînée
    ctx.fillStyle = 'rgba(0, 18, 32, 0.2)';
    ctx.fillRect(0, 0, width, height);
    
    // Calculer la largeur totale des barres
    const totalBarsWidth = barCount * (barWidth + barSpacing) - barSpacing;
    const startX = (width - totalBarsWidth) / 2;
    
    // Calculer le niveau audio moyen
    let sum = 0;
    
    // Dessiner les barres
    for (let i = 0; i < barCount; i++) {
      const dataIndex = Math.floor((i / barCount) * dataArray.length);
      const value = dataArray[dataIndex] / 255;
      sum += value;
      
      // Hauteur de la barre avec un minimum pour l'animation
      const barHeight = Math.max(5, value * height * 0.8);
      
      // Position X de la barre
      const x = startX + i * (barWidth + barSpacing);
      
      // Position Y centrée
      const y = (height - barHeight) / 2;
      
      // Créer un gradient pour chaque barre
      const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
      gradient.addColorStop(0, `${color}ff`);
      gradient.addColorStop(0.5, `${color}aa`);
      gradient.addColorStop(1, `${color}33`);
      
      // Dessiner la barre avec effet de glow
      ctx.shadowBlur = 10 + value * 20;
      ctx.shadowColor = glowColor;
      
      // Barre principale
      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, barWidth, barHeight);
      
      // Effet de réflexion
      ctx.fillStyle = `${color}22`;
      ctx.fillRect(x, height - y - barHeight, barWidth, barHeight * 0.3);
      
      // Points lumineux en haut et en bas
      if (value > 0.7) {
        ctx.beginPath();
        ctx.arc(x + barWidth / 2, y, barWidth / 2, 0, Math.PI * 2);
        ctx.fillStyle = `${color}ff`;
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(x + barWidth / 2, y + barHeight, barWidth / 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    
    // Mettre à jour le niveau audio
    const avgLevel = sum / barCount;
    setAudioLevel(avgLevel);
    
    // Réinitialiser l'ombre
    ctx.shadowBlur = 0;
    
    // Dessiner les lignes horizontales d'effet
    ctx.strokeStyle = `${color}22`;
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 15]);
    
    ctx.beginPath();
    ctx.moveTo(0, height * 0.25);
    ctx.lineTo(width, height * 0.25);
    ctx.moveTo(0, height * 0.75);
    ctx.lineTo(width, height * 0.75);
    ctx.stroke();
    
    ctx.setLineDash([]);
  }, [width, height, barCount, barWidth, barSpacing, color, glowColor]);
  
  // Fonction d'animation
  const animate = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current) return;
    
    // Obtenir les données de fréquence
    analyserRef.current.getByteFrequencyData(dataArrayRef.current);
    
    // Dessiner
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (ctx) {
      drawBars(ctx, dataArrayRef.current);
    }
    
    // Continuer l'animation
    animationRef.current = requestAnimationFrame(animate);
  }, [drawBars]);
  
  // Gérer les changements d'état depuis le contexte
  useEffect(() => {
    if (state.websocket && state.isRecording) {
      setStatus('LISTENING');
    } else if (state.isSpeaking) {
      setStatus('SPEAKING');
    } else {
      setStatus('IDLE');
    }
  }, [state.websocket, state.isRecording, state.isSpeaking]);
  
  // Initialisation et nettoyage
  useEffect(() => {
    // Initialiser l'audio au premier rendu
    if (!isInitialized) {
      initializeAudio();
    }
    
    // Démarrer l'animation
    if (isInitialized) {
      animate();
    }
    
    // Nettoyage
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (sourceRef.current) {
        sourceRef.current.disconnect();
      }
      
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [isInitialized, initializeAudio, animate]);
  
  // Rendu
  return (
    <div className="voice-waveform-container" style={{
      position: 'relative',
      width: width,
      height: height + (showStatus ? 30 : 0),
      background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(0, 18, 32, 0.9) 100%)',
      border: '1px solid rgba(0, 212, 255, 0.3)',
      borderRadius: '10px',
      padding: '10px',
      overflow: 'hidden',
      boxShadow: `0 0 20px ${glowColor}33, inset 0 0 20px ${glowColor}11`
    }}>
      {/* Canvas pour les ondes */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          display: 'block',
          width: '100%',
          height: height
        }}
      />
      
      {/* Indicateur d'état */}
      {showStatus && (
        <div style={{
          position: 'absolute',
          bottom: '5px',
          left: '50%',
          transform: 'translateX(-50%)',
          fontFamily: 'Orbitron, monospace',
          fontSize: '12px',
          color: status === 'ERROR' ? '#ff3b30' : color,
          textShadow: `0 0 10px ${status === 'ERROR' ? '#ff3b30' : color}`,
          letterSpacing: '2px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: status === 'ERROR' ? '#ff3b30' : color,
            boxShadow: `0 0 10px ${status === 'ERROR' ? '#ff3b30' : color}`,
            animation: status !== 'IDLE' ? 'pulse 1.5s ease-in-out infinite' : 'none'
          }} />
          {status}
        </div>
      )}
      
      {/* Effet de scan horizontal */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: '-100%',
        width: '100%',
        height: '2px',
        background: `linear-gradient(90deg, transparent 0%, ${color} 50%, transparent 100%)`,
        animation: 'scan 3s linear infinite',
        opacity: 0.6
      }} />
      
      {/* Coins décoratifs */}
      <div style={{
        position: 'absolute',
        top: '0',
        left: '0',
        width: '20px',
        height: '20px',
        borderTop: `2px solid ${color}`,
        borderLeft: `2px solid ${color}`,
        borderRadius: '10px 0 0 0'
      }} />
      <div style={{
        position: 'absolute',
        top: '0',
        right: '0',
        width: '20px',
        height: '20px',
        borderTop: `2px solid ${color}`,
        borderRight: `2px solid ${color}`,
        borderRadius: '0 10px 0 0'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '0',
        left: '0',
        width: '20px',
        height: '20px',
        borderBottom: `2px solid ${color}`,
        borderLeft: `2px solid ${color}`,
        borderRadius: '0 0 0 10px'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '0',
        right: '0',
        width: '20px',
        height: '20px',
        borderBottom: `2px solid ${color}`,
        borderRight: `2px solid ${color}`,
        borderRadius: '0 0 10px 0'
      }} />
      
      {/* Niveau audio indicator */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        fontSize: '10px',
        fontFamily: 'Orbitron, monospace',
        color: `${color}aa`,
        opacity: 0.7
      }}>
        {Math.round(audioLevel * 100)}%
      </div>
      
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.2);
          }
        }
        
        @keyframes scan {
          0% {
            left: -100%;
          }
          100% {
            left: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default VoiceWaveform;