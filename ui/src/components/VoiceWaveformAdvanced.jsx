/**
 * 🎤 Advanced Voice Waveform Component - Intégration WebSocket complète
 * Visualisation audio avancée avec synchronisation backend JARVIS
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useJarvis } from '../contexts/JarvisContext';

const VoiceWaveformAdvanced = ({ 
  width = 500, 
  height = 200,
  style = 'circular', // 'bars', 'circular', 'wave'
  primaryColor = '#00d4ff',
  secondaryColor = '#00ff88',
  accentColor = '#ff6b00'
}) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  
  const [status, setStatus] = useState('INITIALIZING');
  const [audioLevel, setAudioLevel] = useState(0);
  const [peakLevel, setPeakLevel] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [audioData, setAudioData] = useState(null);
  
  const { state, actions } = useJarvis();
  
  // Configuration audio optimisée pour JARVIS
  const audioConfig = {
    fftSize: 2048,
    smoothingTimeConstant: 0.85,
    minDecibels: -85,
    maxDecibels: -10,
    sampleRate: 44100
  };
  
  // Initialisation de Web Audio API avec gestion d'erreurs avancée
  const initializeAudio = useCallback(async () => {
    try {
      setStatus('CONNECTING');
      
      // Vérifier la compatibilité du navigateur
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Web Audio API not supported');
      }
      
      // Créer le contexte audio avec gestion de l'état suspendu
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioContextRef.current = new AudioContext({ sampleRate: audioConfig.sampleRate });
      
      // Reprendre le contexte si suspendu
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
      
      // Configurer l'analyseur
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = audioConfig.fftSize;
      analyserRef.current.smoothingTimeConstant = audioConfig.smoothingTimeConstant;
      analyserRef.current.minDecibels = audioConfig.minDecibels;
      analyserRef.current.maxDecibels = audioConfig.maxDecibels;
      
      // Créer les tableaux de données
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
      
      // Obtenir l'accès au microphone avec contraintes optimisées
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: audioConfig.sampleRate,
          channelCount: 1
        } 
      });
      streamRef.current = stream;
      
      // Connecter le microphone à l'analyseur
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);
      
      setStatus('READY');
      setIsConnected(true);
      
      // Commencer l'animation
      startAnimation();
      
    } catch (error) {
      console.error('Erreur lors de l\'initialisation audio:', error);
      setStatus('ERROR');
      actions?.addLog('error', `Audio initialization failed: ${error.message}`, 'audio');
    }
  }, [actions]);
  
  // Fonction de dessin pour style 'bars'
  const drawBars = useCallback((ctx, dataArray) => {
    const barCount = 64;
    const barWidth = Math.max(2, Math.floor(width / barCount) - 2);
    const barSpacing = 2;
    
    // Nettoyer le canvas avec effet de traînée
    ctx.fillStyle = 'rgba(0, 18, 32, 0.15)';
    ctx.fillRect(0, 0, width, height);
    
    let totalEnergy = 0;
    let maxValue = 0;
    
    for (let i = 0; i < barCount; i++) {
      const dataIndex = Math.floor((i / barCount) * dataArray.length);
      const value = dataArray[dataIndex] / 255;
      totalEnergy += value;
      maxValue = Math.max(maxValue, value);
      
      const barHeight = Math.max(3, value * height * 0.9);
      const x = i * (barWidth + barSpacing);
      const y = (height - barHeight) / 2;
      
      // Gradient selon l'intensité
      let color = primaryColor;
      if (value > 0.7) color = accentColor;
      else if (value > 0.4) color = secondaryColor;
      
      // Dessiner avec effet de glow
      ctx.shadowBlur = 8 + value * 15;
      ctx.shadowColor = color;
      
      const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
      gradient.addColorStop(0, `${color}ff`);
      gradient.addColorStop(0.5, `${color}cc`);
      gradient.addColorStop(1, `${color}44`);
      
      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, barWidth, barHeight);
      
      // Pic lumineux si très actif
      if (value > 0.8) {
        ctx.beginPath();
        ctx.arc(x + barWidth / 2, y - 5, 3, 0, Math.PI * 2);
        ctx.fillStyle = `${color}ff`;
        ctx.fill();
      }
    }
    
    const avgLevel = totalEnergy / barCount;
    setAudioLevel(avgLevel);
    setPeakLevel(maxValue);
    
    ctx.shadowBlur = 0;
  }, [width, height, primaryColor, secondaryColor, accentColor]);
  
  // Fonction de dessin pour style 'circular'
  const drawCircular = useCallback((ctx, dataArray) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const baseRadius = Math.min(width, height) * 0.15;
    const maxRadius = Math.min(width, height) * 0.4;
    
    // Nettoyer le canvas
    ctx.fillStyle = 'rgba(0, 18, 32, 0.1)';
    ctx.fillRect(0, 0, width, height);
    
    // Cercle central
    ctx.beginPath();
    ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
    ctx.strokeStyle = `${primaryColor}44`;
    ctx.lineWidth = 2;
    ctx.stroke();
    
    const barCount = 72;
    let totalEnergy = 0;
    
    for (let i = 0; i < barCount; i++) {
      const angle = (i / barCount) * Math.PI * 2;
      const dataIndex = Math.floor((i / barCount) * dataArray.length);
      const value = dataArray[dataIndex] / 255;
      totalEnergy += value;
      
      const barLength = value * (maxRadius - baseRadius);
      const innerRadius = baseRadius;
      const outerRadius = baseRadius + barLength;
      
      // Couleur selon la position et l'intensité
      let color = primaryColor;
      if (i % 12 === 0) color = accentColor;
      else if (i % 6 === 0) color = secondaryColor;
      
      // Dessiner la barre radiale
      ctx.beginPath();
      ctx.strokeStyle = `${color}${Math.floor(value * 255).toString(16).padStart(2, '0')}`;
      ctx.lineWidth = 3;
      ctx.moveTo(
        centerX + Math.cos(angle) * innerRadius,
        centerY + Math.sin(angle) * innerRadius
      );
      ctx.lineTo(
        centerX + Math.cos(angle) * outerRadius,
        centerY + Math.sin(angle) * outerRadius
      );
      ctx.stroke();
      
      // Points lumineux pour les pics
      if (value > 0.7) {
        ctx.beginPath();
        ctx.arc(
          centerX + Math.cos(angle) * outerRadius,
          centerY + Math.sin(angle) * outerRadius,
          2, 0, Math.PI * 2
        );
        ctx.fillStyle = `${color}ff`;
        ctx.fill();
      }
    }
    
    // Cercle central pulsant
    const avgLevel = totalEnergy / barCount;
    setAudioLevel(avgLevel);
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, baseRadius * (0.5 + avgLevel * 0.5), 0, Math.PI * 2);
    ctx.fillStyle = `${primaryColor}${Math.floor(avgLevel * 100).toString(16).padStart(2, '0')}`;
    ctx.fill();
    
  }, [width, height, primaryColor, secondaryColor, accentColor]);
  
  // Fonction de dessin pour style 'wave'
  const drawWave = useCallback((ctx, dataArray) => {
    ctx.fillStyle = 'rgba(0, 18, 32, 0.1)';
    ctx.fillRect(0, 0, width, height);
    
    const centerY = height / 2;
    const step = width / dataArray.length;
    let totalEnergy = 0;
    
    // Dessiner la forme d'onde
    ctx.beginPath();
    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 2;
    
    for (let i = 0; i < dataArray.length; i++) {
      const value = (dataArray[i] / 255) - 0.5;
      totalEnergy += Math.abs(value);
      
      const x = i * step;
      const y = centerY + value * height * 0.8;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
    
    // Remplissage avec gradient
    ctx.lineTo(width, centerY);
    ctx.lineTo(0, centerY);
    ctx.closePath();
    
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, `${primaryColor}44`);
    gradient.addColorStop(0.5, `${primaryColor}22`);
    gradient.addColorStop(1, `${primaryColor}44`);
    
    ctx.fillStyle = gradient;
    ctx.fill();
    
    const avgLevel = totalEnergy / dataArray.length;
    setAudioLevel(avgLevel);
    
  }, [width, height, primaryColor]);
  
  // Fonction d'animation principale
  const animate = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current || !canvasRef.current) return;
    
    analyserRef.current.getByteFrequencyData(dataArrayRef.current);
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    
    // Choisir le style de rendu
    switch (style) {
      case 'circular':
        drawCircular(ctx, dataArrayRef.current);
        break;
      case 'wave':
        drawWave(ctx, dataArrayRef.current);
        break;
      default:
        drawBars(ctx, dataArrayRef.current);
    }
    
    animationRef.current = requestAnimationFrame(animate);
  }, [style, drawBars, drawCircular, drawWave]);
  
  // Démarrer l'animation
  const startAnimation = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    animate();
  }, [animate]);
  
  // Gérer les messages WebSocket
  useEffect(() => {
    if (state.websocket) {
      // Écouter les changements d'état
      if (state.isRecording) {
        setStatus('LISTENING');
      } else if (state.isSpeaking) {
        setStatus('SPEAKING');
      } else {
        setStatus('READY');
      }
    }
  }, [state.websocket, state.isRecording, state.isSpeaking]);
  
  // Initialisation et nettoyage
  useEffect(() => {
    initializeAudio();
    
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
  }, []);
  
  // Rendu du composant
  return (
    <div className="voice-waveform-advanced" style={{
      position: 'relative',
      width: width,
      height: height + 60,
      background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 18, 32, 0.95) 100%)',
      border: '1px solid rgba(0, 212, 255, 0.4)',
      borderRadius: '15px',
      padding: '15px',
      overflow: 'hidden',
      boxShadow: `
        0 0 30px ${primaryColor}22,
        inset 0 0 30px ${primaryColor}11,
        0 0 60px ${primaryColor}11
      `
    }}>
      {/* Canvas principal */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          display: 'block',
          width: '100%',
          height: height,
          borderRadius: '10px'
        }}
      />
      
      {/* HUD d'informations */}
      <div style={{
        position: 'absolute',
        bottom: '15px',
        left: '15px',
        right: '15px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontFamily: 'Orbitron, monospace',
        fontSize: '11px',
        color: primaryColor
      }}>
        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: status === 'ERROR' ? '#ff3b30' : primaryColor,
            boxShadow: `0 0 10px ${status === 'ERROR' ? '#ff3b30' : primaryColor}`,
            animation: status !== 'READY' ? 'pulse 1.5s ease-in-out infinite' : 'none'
          }} />
          <span style={{ letterSpacing: '1px' }}>{status}</span>
        </div>
        
        {/* Niveaux audio */}
        <div style={{ display: 'flex', gap: '15px', fontSize: '10px' }}>
          <span>AVG: {Math.round(audioLevel * 100)}%</span>
          <span>PEAK: {Math.round(peakLevel * 100)}%</span>
          <span>STYLE: {style.toUpperCase()}</span>
        </div>
      </div>
      
      {/* Ligne de scan */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '-100%',
        width: '100%',
        height: '1px',
        background: `linear-gradient(90deg, transparent 0%, ${primaryColor} 50%, transparent 100%)`,
        animation: 'scan 4s linear infinite',
        opacity: 0.5
      }} />
      
      {/* Coins décoratifs animés */}
      <div className="corner-decoration" style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        width: '25px',
        height: '25px',
        borderTop: `2px solid ${primaryColor}`,
        borderLeft: `2px solid ${primaryColor}`,
        opacity: 0.8
      }} />
      <div className="corner-decoration" style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        width: '25px',
        height: '25px',
        borderTop: `2px solid ${primaryColor}`,
        borderRight: `2px solid ${primaryColor}`,
        opacity: 0.8
      }} />
      
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.3); }
        }
        
        @keyframes scan {
          0% { left: -100%; }
          100% { left: 100%; }
        }
        
        .corner-decoration {
          animation: corner-glow 3s ease-in-out infinite;
        }
        
        @keyframes corner-glow {
          0%, 100% { opacity: 0.8; }
          50% { opacity: 1; box-shadow: 0 0 10px ${primaryColor}44; }
        }
      `}</style>
    </div>
  );
};

export default VoiceWaveformAdvanced;