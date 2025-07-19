/**
 * Détection du mode développement pour Electron
 */
const isDev = process.env.NODE_ENV === 'development' || 
             process.env.DEBUG_PROD === 'true' ||
             !process.env.NODE_ENV;

module.exports = isDev;