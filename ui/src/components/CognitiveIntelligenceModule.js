/**
 * 🧠 JARVIS - Module d'Intelligence Cognitive Avancée
 * Système de "pensée profonde" avec visualisation temps réel
 */
import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { 
  Box, Card, CardContent, Typography, Chip, LinearProgress, 
  Switch, FormControlLabel, Accordion, AccordionSummary, 
  AccordionDetails, Grid, Slider, Paper 
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import * as THREE from 'three';

// États cognitifs du système
const COGNITIVE_STATES = {
  IDLE: { 
    name: 'Repos', 
    color: '#2196F3', 
    intensity: 0.2,
    patterns: ['breathing', 'ambient'] 
  },
  THINKING: { 
    name: 'Réflexion', 
    color: '#FF9800', 
    intensity: 0.6,
    patterns: ['neural', 'synapses', 'waves'] 
  },
  DEEP_ANALYSIS: { 
    name: 'Analyse Profonde', 
    color: '#9C27B0', 
    intensity: 0.8,
    patterns: ['fractal', 'complex', 'multi_layer'] 
  },
  CREATIVE: { 
    name: 'Créatif', 
    color: '#E91E63', 
    intensity: 0.9,
    patterns: ['explosion', 'creative', 'chaotic'] 
  },
  PROBLEM_SOLVING: { 
    name: 'Résolution', 
    color: '#4CAF50', 
    intensity: 0.7,
    patterns: ['structured', 'logical', 'convergent'] 
  },
  MEMORY_ACCESS: { 
    name: 'Accès Mémoire', 
    color: '#00BCD4', 
    intensity: 0.5,
    patterns: ['retrieval', 'connections', 'web'] 
  }
};

// Multi-agents avec personnalités différentes
const COGNITIVE_AGENTS = {
  ANALYTICAL: {
    name: 'Agent Analytique',
    color: '#2196F3',
    role: 'Analyse logique et décomposition des problèmes',
    patterns: ['grid', 'structured', 'linear']
  },
  CREATIVE: {
    name: 'Agent Créatif', 
    color: '#E91E63',
    role: 'Génération d\'idées et pensée latérale',
    patterns: ['organic', 'fluid', 'random']
  },
  CRITIC: {
    name: 'Agent Critique',
    color: '#FF5722',
    role: 'Évaluation et validation des solutions',
    patterns: ['focused', 'sharp', 'selective']
  },
  SYNTHESIZER: {
    name: 'Agent Synthétiseur',
    color: '#9C27B0',
    role: 'Intégration et synthèse des résultats',
    patterns: ['merge', 'combine', 'unify']
  },
  MEMORY: {
    name: 'Agent Mémoire',
    color: '#00BCD4',
    role: 'Accès aux connaissances et contexte',
    patterns: ['network', 'web', 'connections']
  }
};

function CognitiveIntelligenceModule({ 
  sphereRef, 
  isEnabled = true, 
  currentTask = null,
  onCognitiveUpdate = null,
  visualizationMode = 'full' 
}) {
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cognitiveNodesRef = useRef([]);
  const decisionTreeRef = useRef(null);
  const knowledgeGraphRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  const [cognitiveState, setCognitiveState] = useState('IDLE');
  const [activeAgents, setActiveAgents] = useState(new Set());
  const [thinkingProcess, setThinkingProcess] = useState([]);
  const [decisionTree, setDecisionTree] = useState(null);
  const [memoryGraph, setMemoryGraph] = useState(new Map());
  const [processingIntensity, setProcessingIntensity] = useState(0.2);
  const [showDebugInfo, setShowDebugInfo] = useState(false);

  // Configuration des visualisations cognitives
  const cognitiveConfig = useMemo(() => ({
    nodeCount: 50,
    connectionStrength: 0.3,
    pulseSpeed: 1.0,
    layerDepth: 3,
    brainwaveFreq: 0.05,
    synapseThreshold: 0.6
  }), []);

  // Initialisation de la scène cognitive 3D
  useEffect(() => {
    if (!canvasRef.current || !isEnabled) return;

    // Setup Three.js scene pour visualisations cognitives
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 400/300, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
      canvas: canvasRef.current, 
      alpha: true,
      antialias: true 
    });
    
    renderer.setSize(400, 300);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    camera.position.z = 5;

    sceneRef.current = scene;
    rendererRef.current = renderer;

    // Création du réseau neuronal 3D
    createNeuralNetwork(scene);
    createKnowledgeGraph(scene);
    createDecisionTreeVisualization(scene);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      renderer.dispose();
    };
  }, [isEnabled, cognitiveConfig]);

  // Animation des processus cognitifs
  useEffect(() => {
    if (!sceneRef.current || !isEnabled) return;

    const animate = (timestamp) => {
      updateCognitiveVisualizations(timestamp);
      updateNeuralActivity();
      updateDecisionTree();
      updateKnowledgeGraph();
      
      if (rendererRef.current && sceneRef.current) {
        rendererRef.current.render(sceneRef.current, rendererRef.current.camera || new THREE.PerspectiveCamera());
      }
      
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [cognitiveState, activeAgents, processingIntensity]);

  // Création du réseau neuronal 3D
  const createNeuralNetwork = useCallback((scene) => {
    const nodes = [];
    const connections = [];
    
    // Création des nœuds neuronaux
    for (let i = 0; i < cognitiveConfig.nodeCount; i++) {
      const nodeGeometry = new THREE.SphereGeometry(0.02 + Math.random() * 0.03, 8, 8);
      const nodeMaterial = new THREE.MeshBasicMaterial({ 
        color: new THREE.Color().setHSL(Math.random(), 0.7, 0.6),
        transparent: true,
        opacity: 0.8
      });
      
      const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
      node.position.set(
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 2
      );
      
      node.userData = {
        activation: 0,
        connections: [],
        agentType: Object.keys(COGNITIVE_AGENTS)[Math.floor(Math.random() * Object.keys(COGNITIVE_AGENTS).length)]
      };
      
      scene.add(node);
      nodes.push(node);
    }
    
    // Création des connexions synaptiques
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const distance = nodes[i].position.distanceTo(nodes[j].position);
        
        if (distance < 1.5 && Math.random() > 0.7) {
          const connectionGeometry = new THREE.BufferGeometry().setFromPoints([
            nodes[i].position,
            nodes[j].position
          ]);
          
          const connectionMaterial = new THREE.LineBasicMaterial({ 
            color: 0x4FC3F7,
            transparent: true,
            opacity: 0.3
          });
          
          const connection = new THREE.Line(connectionGeometry, connectionMaterial);
          connection.userData = { 
            nodes: [nodes[i], nodes[j]], 
            strength: Math.random(),
            activity: 0
          };
          
          scene.add(connection);
          connections.push(connection);
          
          nodes[i].userData.connections.push(connection);
          nodes[j].userData.connections.push(connection);
        }
      }
    }
    
    cognitiveNodesRef.current = { nodes, connections };
  }, [cognitiveConfig]);

  // Création du graphe de connaissances
  const createKnowledgeGraph = useCallback((scene) => {
    const knowledgeNodes = new THREE.Group();
    knowledgeNodes.position.set(2, 0, 0);
    
    // Nœuds de concepts
    const concepts = ['Mémoire', 'Logique', 'Créativité', 'Analyse', 'Synthèse'];
    concepts.forEach((concept, index) => {
      const geometry = new THREE.OctahedronGeometry(0.1);
      const material = new THREE.MeshBasicMaterial({ 
        color: new THREE.Color().setHSL(index / concepts.length, 0.8, 0.6),
        wireframe: true
      });
      
      const conceptNode = new THREE.Mesh(geometry, material);
      conceptNode.position.set(
        Math.cos(index / concepts.length * Math.PI * 2) * 0.8,
        Math.sin(index / concepts.length * Math.PI * 2) * 0.8,
        0
      );
      
      conceptNode.userData = { concept, relevance: 0, activity: 0 };
      knowledgeNodes.add(conceptNode);
    });
    
    scene.add(knowledgeNodes);
    knowledgeGraphRef.current = knowledgeNodes;
  }, []);

  // Création de la visualisation de l'arbre de décision
  const createDecisionTreeVisualization = useCallback((scene) => {
    const treeGroup = new THREE.Group();
    treeGroup.position.set(-2, 0, 0);
    
    // Nœud racine
    const rootGeometry = new THREE.BoxGeometry(0.2, 0.2, 0.2);
    const rootMaterial = new THREE.MeshBasicMaterial({ color: 0x4CAF50 });
    const root = new THREE.Mesh(rootGeometry, rootMaterial);
    
    treeGroup.add(root);
    
    // Branches de décision
    for (let level = 1; level <= 3; level++) {
      const branchCount = Math.pow(2, level);
      
      for (let i = 0; i < branchCount; i++) {
        const branchGeometry = new THREE.SphereGeometry(0.05, 6, 6);
        const branchMaterial = new THREE.MeshBasicMaterial({ 
          color: new THREE.Color().setHSL(0.3 - level * 0.1, 0.7, 0.6)
        });
        
        const branch = new THREE.Mesh(branchGeometry, branchMaterial);
        branch.position.set(
          (i - branchCount/2) * 0.5,
          -level * 0.3,
          0
        );
        
        // Ligne de connexion
        const lineGeometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, -(level-1) * 0.3, 0),
          branch.position
        ]);
        const lineMaterial = new THREE.LineBasicMaterial({ color: 0x795548 });
        const line = new THREE.Line(lineGeometry, lineMaterial);
        
        treeGroup.add(branch);
        treeGroup.add(line);
      }
    }
    
    scene.add(treeGroup);
    decisionTreeRef.current = treeGroup;
  }, []);

  // Mise à jour des visualisations cognitives
  const updateCognitiveVisualizations = useCallback((timestamp) => {
    if (!cognitiveNodesRef.current) return;
    
    const state = COGNITIVE_STATES[cognitiveState];
    const { nodes, connections } = cognitiveNodesRef.current;
    
    // Animation des nœuds neuronaux
    nodes.forEach((node, index) => {
      const time = timestamp * 0.001;
      const baseActivity = state.intensity;
      const pulsePhase = time * 2 + index * 0.1;
      
      // Activation basée sur l'état cognitif
      node.userData.activation = baseActivity + 
        Math.sin(pulsePhase) * 0.2 * processingIntensity;
      
      // Mise à jour visuelle
      node.material.opacity = 0.3 + node.userData.activation * 0.7;
      node.scale.setScalar(1 + node.userData.activation * 0.5);
      
      // Couleur selon l'agent
      const agent = COGNITIVE_AGENTS[node.userData.agentType];
      if (activeAgents.has(node.userData.agentType)) {
        node.material.color.setHex(parseInt(agent.color.replace('#', ''), 16));
        node.material.opacity *= 1.5;
      }
    });
    
    // Animation des connexions
    connections.forEach((connection) => {
      const [nodeA, nodeB] = connection.userData.nodes;
      const activity = (nodeA.userData.activation + nodeB.userData.activation) / 2;
      
      connection.material.opacity = activity * 0.5;
      connection.userData.activity = activity;
    });
  }, [cognitiveState, activeAgents, processingIntensity]);

  // Mise à jour de l'activité neuronale
  const updateNeuralActivity = useCallback(() => {
    // Simulation de la propagation des signaux neuronaux
    if (Math.random() < 0.1) {
      const randomNode = cognitiveNodesRef.current?.nodes?.[
        Math.floor(Math.random() * cognitiveNodesRef.current.nodes.length)
      ];
      
      if (randomNode) {
        randomNode.userData.activation = Math.min(1, randomNode.userData.activation + 0.3);
        
        // Propagation aux connexions
        randomNode.userData.connections.forEach(connection => {
          setTimeout(() => {
            connection.userData.activity = Math.min(1, connection.userData.activity + 0.2);
          }, 50);
        });
      }
    }
  }, []);

  // Mise à jour de l'arbre de décision
  const updateDecisionTree = useCallback(() => {
    if (!decisionTreeRef.current) return;
    
    // Animation des nœuds de décision selon l'état
    decisionTreeRef.current.children.forEach((child, index) => {
      if (child.material) {
        const activity = Math.sin(Date.now() * 0.001 + index * 0.5) * 0.5 + 0.5;
        child.material.opacity = 0.4 + activity * 0.6 * processingIntensity;
      }
    });
  }, [processingIntensity]);

  // Mise à jour du graphe de connaissances
  const updateKnowledgeGraph = useCallback(() => {
    if (!knowledgeGraphRef.current) return;
    
    // Rotation du graphe
    knowledgeGraphRef.current.rotation.y += 0.005 * processingIntensity;
    
    // Animation des nœuds de concepts
    knowledgeGraphRef.current.children.forEach((child, index) => {
      if (child.material) {
        const pulse = Math.sin(Date.now() * 0.002 + index) * 0.3 + 0.7;
        child.scale.setScalar(pulse);
      }
    });
  }, [processingIntensity]);

  // Déclenchement d'un processus cognitif
  const triggerCognitiveProcess = useCallback((processType, agents = []) => {
    setCognitiveState(processType);
    setActiveAgents(new Set(agents));
    
    // Simulation du processus de pensée
    const process = {
      id: Date.now(),
      type: processType,
      agents: agents,
      startTime: Date.now(),
      steps: []
    };
    
    setThinkingProcess(prev => [process, ...prev.slice(0, 9)]);
    
    if (onCognitiveUpdate) {
      onCognitiveUpdate({
        state: processType,
        agents: agents,
        intensity: COGNITIVE_STATES[processType].intensity
      });
    }
    
    // Retour à l'état idle après un délai
    setTimeout(() => {
      setCognitiveState('IDLE');
      setActiveAgents(new Set());
    }, 3000 + Math.random() * 2000);
  }, [onCognitiveUpdate]);

  // Interface utilisateur
  if (!isEnabled) return null;

  return (
    <Card sx={{ mb: 2, backgroundColor: 'rgba(0,0,0,0.8)' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ color: '#00BCD4' }}>
          🧠 Module d'Intelligence Cognitive Avancée
        </Typography>
        
        <Grid container spacing={2}>
          {/* Visualisation 3D des processus cognitifs */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 1, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="subtitle2" gutterBottom>
                Réseau Neuronal Cognitif
              </Typography>
              <canvas 
                ref={canvasRef} 
                style={{ 
                  width: '100%', 
                  height: '300px',
                  border: '1px solid #333',
                  borderRadius: '8px'
                }} 
              />
            </Paper>
          </Grid>
          
          {/* Panel de contrôle */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* État cognitif actuel */}
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
                <Typography variant="subtitle2" gutterBottom>
                  État Cognitif Actuel
                </Typography>
                <Chip 
                  label={COGNITIVE_STATES[cognitiveState].name}
                  sx={{ 
                    backgroundColor: COGNITIVE_STATES[cognitiveState].color,
                    color: 'white'
                  }}
                />
                
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption">Intensité de Traitement</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={processingIntensity * 100}
                    sx={{ mt: 0.5, height: 6, borderRadius: 3 }}
                  />
                </Box>
                
                <Slider
                  value={processingIntensity}
                  onChange={(e, val) => setProcessingIntensity(val)}
                  min={0}
                  max={1}
                  step={0.1}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Paper>
              
              {/* Agents cognitifs actifs */}
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Agents Cognitifs Actifs
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(COGNITIVE_AGENTS).map(([key, agent]) => (
                    <Chip
                      key={key}
                      label={agent.name}
                      size="small"
                      variant={activeAgents.has(key) ? "filled" : "outlined"}
                      sx={{ 
                        color: agent.color,
                        borderColor: agent.color,
                        ...(activeAgents.has(key) && {
                          backgroundColor: agent.color + '33',
                        })
                      }}
                    />
                  ))}
                </Box>
              </Paper>
              
              {/* Processus de pensée */}
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Processus de Pensée
                </Typography>
                <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                  {thinkingProcess.slice(0, 5).map((process, index) => (
                    <Box key={process.id} sx={{ mb: 1, opacity: 1 - index * 0.2 }}>
                      <Typography variant="caption" color="textSecondary">
                        {new Date(process.startTime).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="body2">
                        {COGNITIVE_STATES[process.type]?.name} - {process.agents.length} agents
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Paper>
            </Box>
          </Grid>
          
          {/* Contrôles de démo */}
          <Grid item xs={12}>
            <Accordion sx={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Contrôles de Démonstration</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(COGNITIVE_STATES).map(([state, config]) => (
                    <Chip
                      key={state}
                      label={config.name}
                      onClick={() => triggerCognitiveProcess(state, ['ANALYTICAL', 'CREATIVE'])}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { opacity: 0.8 }
                      }}
                    />
                  ))}
                </Box>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={showDebugInfo}
                      onChange={(e) => setShowDebugInfo(e.target.checked)}
                    />
                  }
                  label="Affichage Debug"
                  sx={{ mt: 1 }}
                />
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default CognitiveIntelligenceModule;