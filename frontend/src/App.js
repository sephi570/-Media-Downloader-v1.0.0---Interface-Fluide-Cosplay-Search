import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [url, setUrl] = useState('');
  const [mediaInfo, setMediaInfo] = useState(null);
  const [downloads, setDownloads] = useState([]);
  const [stats, setStats] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [authStatus, setAuthStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [searchMode, setSearchMode] = useState('url'); // 'url' or 'cosplay'
  
  // Cosplay search states
  const [cosplayQuery, setCosplayQuery] = useState('');
  const [cosplayResults, setCosplayResults] = useState([]);
  const [selectedCosplays, setSelectedCosplays] = useState([]);
  const [cosplaySuggestions, setCosplaySuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [downloadOptions, setDownloadOptions] = useState({
    quality: 'best',
    audio_only: false,
    output_format: 'mp4',
    platform: 'auto'
  });

  // Auth configuration states
  const [authConfig, setAuthConfig] = useState({
    platform: '',
    username: '',
    password: '',
    client_id: '',
    client_secret: ''
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Platform detection from URL
  const detectPlatformFromUrl = (url) => {
    const urlLower = url.toLowerCase();
    if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) return 'youtube';
    if (urlLower.includes('instagram.com')) return 'instagram';
    if (urlLower.includes('reddit.com')) return 'reddit';
    if (urlLower.includes('pornhub.com')) return 'pornhub';
    if (urlLower.includes('redtube.com')) return 'redtube';
    if (urlLower.includes('nhentai.net')) return 'nhentai';
    if (urlLower.includes('luscious.net')) return 'luscious';
    if (urlLower.includes('nutaku.net')) return 'nutaku';
    if (urlLower.includes('cosplaytele')) return 'cosplaytele';
    if (urlLower.includes('imhentai.xxx')) return 'imhentai';
    if (urlLower.includes('spotify.com') || urlLower.includes('open.spotify.com')) return 'spotify';
    return 'unknown';
  };

  // Fetch cosplay suggestions
  const fetchCosplaySuggestions = async (query) => {
    if (query.length < 2) {
      setCosplaySuggestions([]);
      return;
    }
    
    try {
      const response = await axios.get(`${BACKEND_URL}/api/cosplay/suggestions/${query}`);
      setCosplaySuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Échec de récupération des suggestions:', error);
    }
  };

  // Search cosplay galleries
  const searchCosplay = async () => {
    if (!cosplayQuery.trim()) {
      alert('Veuillez entrer un nom de cosplay');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/cosplay/search`, {
        query: cosplayQuery,
        platforms: ["all"],
        limit: 20
      });
      
      setCosplayResults(response.data.results);
      setShowSuggestions(false);
    } catch (error) {
      alert('Échec de recherche cosplay: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Toggle cosplay selection
  const toggleCosplaySelection = (resultId) => {
    setSelectedCosplays(prev => {
      if (prev.includes(resultId)) {
        return prev.filter(id => id !== resultId);
      } else {
        return [...prev, resultId];
      }
    });
  };

  // Download selected cosplays
  const downloadSelectedCosplays = async () => {
    if (selectedCosplays.length === 0) {
      alert('Veuillez sélectionner au moins une gallery');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/cosplay/download`, {
        cosplay_results: selectedCosplays,
        quality: downloadOptions.quality
      });
      
      alert(`${selectedCosplays.length} galleries de cosplay ajoutées au téléchargement !`);
      setSelectedCosplays([]);
      setCosplayResults([]);
      setCosplayQuery('');
      fetchDownloads(); // Refresh downloads
    } catch (error) {
      alert('Échec du téléchargement cosplay: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Fetch auth status
  const fetchAuthStatus = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/status`);
      setAuthStatus(response.data);
    } catch (error) {
      console.error('Échec de récupération du statut d\'authentification:', error);
    }
  };

  // Configure authentication
  const configureAuth = async (platform) => {
    if (!authConfig.platform) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/configure`, authConfig);
      alert(`Configuration ${platform} : ${response.data.message}`);
      
      // Reset form
      setAuthConfig({
        platform: '',
        username: '',
        password: '',
        client_id: '',
        client_secret: ''
      });
      
      // Refresh auth status
      fetchAuthStatus();
    } catch (error) {
      alert('Échec de configuration: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Delete authentication
  const deleteAuth = async (platform) => {
    if (!window.confirm(`Supprimer l'authentification pour ${platform} ?`)) return;
    
    try {
      await axios.delete(`${BACKEND_URL}/api/auth/${platform}`);
      alert(`Authentification ${platform} supprimée`);
      fetchAuthStatus();
    } catch (error) {
      alert('Échec de suppression: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Fetch media information
  const fetchMediaInfo = async () => {
    if (!url) {
      alert('Veuillez entrer une URL valide');
      return;
    }
    
    const detectedPlatform = detectPlatformFromUrl(url);
    setSelectedPlatform(detectedPlatform);
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/media/info`, { url });
      setMediaInfo(response.data);
    } catch (error) {
      alert('Échec de récupération des informations média: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Start download
  const startDownload = async () => {
    if (!url) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/media/download`, {
        url,
        ...downloadOptions
      });
      
      alert(`Téléchargement commencé! Plateforme: ${response.data.platform}, ID: ${response.data.download_id}`);
      fetchDownloads();
      setUrl('');
      setMediaInfo(null);
      setSelectedPlatform('');
    } catch (error) {
      alert('Échec du démarrage du téléchargement: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Fetch downloads list
  const fetchDownloads = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/media/downloads`);
      setDownloads(response.data);
    } catch (error) {
      console.error('Échec de récupération des téléchargements:', error);
    }
  };

  // Fetch supported platforms
  const fetchPlatforms = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/platforms`);
      setPlatforms(response.data.supported_platforms);
    } catch (error) {
      console.error('Échec de récupération des plateformes:', error);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Échec de récupération des statistiques:', error);
    }
  };

  // Delete download
  const deleteDownload = async (downloadId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce téléchargement?')) return;
    
    try {
      await axios.delete(`${BACKEND_URL}/api/media/download/${downloadId}`);
      fetchDownloads();
    } catch (error) {
      alert('Échec de suppression du téléchargement: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Download file
  const downloadFile = async (downloadId, filename) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/media/download/${downloadId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Échec du téléchargement du fichier: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Auto-refresh downloads and stats
  useEffect(() => {
    fetchDownloads();
    fetchStats();
    fetchPlatforms();
    fetchAuthStatus();
    const interval = setInterval(() => {
      fetchDownloads();
      fetchStats();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Debounced suggestions
  useEffect(() => {
    const timer = setTimeout(() => {
      if (cosplayQuery) {
        fetchCosplaySuggestions(cosplayQuery);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [cosplayQuery]);

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Inconnu';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'Inconnu';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-300 bg-green-900 bg-opacity-30';
      case 'failed': return 'text-red-300 bg-red-900 bg-opacity-30';
      case 'downloading': return 'text-yellow-300 bg-yellow-900 bg-opacity-30';
      case 'pending': return 'text-blue-300 bg-blue-900 bg-opacity-30';
      default: return 'text-gray-300 bg-gray-900 bg-opacity-30';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'failed': return 'Échec';
      case 'downloading': return 'Téléchargement';
      case 'pending': return 'En attente';
      default: return status;
    }
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'youtube': return '🎥';
      case 'instagram': return '📷';
      case 'reddit': return '🔴';
      case 'pornhub': return '🔞';
      case 'redtube': return '🔞';
      case 'nhentai': return '📚';
      case 'luscious': return '💋';
      case 'nutaku': return '🎮';
      case 'cosplaytele': return '👘';
      case 'imhentai': return '📖';
      case 'spotify': return '🎵';
      default: return '📱';
    }
  };

  const getPlatformName = (platform) => {
    switch (platform) {
      case 'youtube': return 'YouTube';
      case 'instagram': return 'Instagram';
      case 'reddit': return 'Reddit';
      case 'pornhub': return 'PornHub';
      case 'redtube': return 'RedTube';
      case 'nhentai': return 'NHentai';
      case 'luscious': return 'Luscious';
      case 'nutaku': return 'Nutaku';
      case 'cosplaytele': return 'CosplayTele';
      case 'imhentai': return 'ImHentai';
      case 'spotify': return 'Spotify';
      default: return platform || 'Inconnu';
    }
  };

  const getAuthStatusIcon = (platform) => {
    const status = authStatus[platform];
    if (!status) return '❓';
    if (status.configured) return '✅';
    return '❌';
  };

  return (
    <div className="min-h-screen relative">
      {/* Animated background elements */}
      <div className="fluid-wave"></div>
      
      {/* Header */}
      <div className="glass-card shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                🌐 Téléchargeur Multi-Plateformes
              </h1>
              <p className="text-gray-300 mt-1">
                Téléchargez vos médias préférés depuis {platforms.length} plateformes différentes
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Search Mode Toggle */}
              <div className="flex bg-black bg-opacity-20 rounded-lg p-1">
                <button
                  onClick={() => setSearchMode('url')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    searchMode === 'url' 
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  🔗 URL
                </button>
                <button
                  onClick={() => setSearchMode('cosplay')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    searchMode === 'cosplay' 
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  👘 Cosplay
                </button>
              </div>
              
              {/* Settings Button */}
              <button 
                onClick={() => setShowSettings(!showSettings)}
                className="px-4 py-2 bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600 text-white rounded-lg transition-all duration-200 transform hover:scale-105"
              >
                ⚙️ Paramètres
              </button>
              
              {/* Stats */}
              {stats && (
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg">
                    <div className="text-2xl font-bold">{stats.total_downloads}</div>
                    <div className="text-xs opacity-90">Total</div>
                  </div>
                  <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-4 py-2 rounded-lg">
                    <div className="text-2xl font-bold">{stats.completed_downloads}</div>
                    <div className="text-xs opacity-90">Terminés</div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg">
                    <div className="text-2xl font-bold">{stats.currently_downloading}</div>
                    <div className="text-xs opacity-90">En cours</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Settings Panel */}
        {showSettings && (
          <div className="main-card rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-6 text-white">⚙️ Configuration des Identifiants</h2>
            
            {/* Current Auth Status */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-4 text-gray-300">État actuel :</h3>
              <div className="grid md:grid-cols-3 gap-4">
                {Object.entries(authStatus).map(([platform, status]) => (
                  <div key={platform} className="glass-card p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{getPlatformIcon(platform)} {getPlatformName(platform)}</span>
                      <span className="text-2xl">{getAuthStatusIcon(platform)}</span>
                    </div>
                    <div className="text-sm text-gray-300">
                      {status.configured ? 'Configuré' : 'Non configuré'}
                      {status.username && <div>Utilisateur: {status.username}</div>}
                      {status.client_id && <div>Client ID: {status.client_id.substring(0, 8)}...</div>}
                    </div>
                    {status.configured && (
                      <button
                        onClick={() => deleteAuth(platform)}
                        className="mt-2 px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded"
                      >
                        Supprimer
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Auth Configuration Form */}
            <div className="border-t border-gray-600 pt-6">
              <h3 className="text-lg font-medium mb-4 text-gray-300">Configurer une nouvelle authentification :</h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Plateforme :</label>
                  <select
                    value={authConfig.platform}
                    onChange={(e) => setAuthConfig({...authConfig, platform: e.target.value})}
                    className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Sélectionner une plateforme</option>
                    <option value="instagram">Instagram</option>
                    <option value="reddit">Reddit</option>
                  </select>
                </div>

                {authConfig.platform === 'instagram' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Nom d'utilisateur Instagram :</label>
                      <input
                        type="text"
                        value={authConfig.username}
                        onChange={(e) => setAuthConfig({...authConfig, username: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="votre_nom_utilisateur"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Mot de passe Instagram :</label>
                      <input
                        type="password"
                        value={authConfig.password}
                        onChange={(e) => setAuthConfig({...authConfig, password: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="votre_mot_de_passe"
                      />
                    </div>
                  </>
                )}

                {authConfig.platform === 'reddit' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Reddit Client ID :</label>
                      <input
                        type="text"
                        value={authConfig.client_id}
                        onChange={(e) => setAuthConfig({...authConfig, client_id: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="Votre client ID Reddit"
                      />
                      <p className="text-xs text-gray-400 mt-1">
                        Créez une app sur <a href="https://www.reddit.com/prefs/apps" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:underline">reddit.com/prefs/apps</a>
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Reddit Client Secret :</label>
                      <input
                        type="password"
                        value={authConfig.client_secret}
                        onChange={(e) => setAuthConfig({...authConfig, client_secret: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="Votre client secret Reddit"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Reddit Username (optionnel) :</label>
                      <input
                        type="text"
                        value={authConfig.username}
                        onChange={(e) => setAuthConfig({...authConfig, username: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="votre_nom_utilisateur_reddit"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Reddit Password (optionnel) :</label>
                      <input
                        type="password"
                        value={authConfig.password}
                        onChange={(e) => setAuthConfig({...authConfig, password: e.target.value})}
                        className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="votre_mot_de_passe_reddit"
                      />
                    </div>
                  </>
                )}
              </div>

              {authConfig.platform && (
                <div className="mt-6">
                  <button
                    onClick={() => configureAuth(authConfig.platform)}
                    disabled={loading || !authConfig.platform}
                    className="btn-gradient px-6 py-3 hover:from-green-700 hover:to-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
                  >
                    {loading ? '⏳ Configuration...' : '💾 Enregistrer la Configuration'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        {searchMode === 'url' ? (
          /* URL Download Section */
          <div className="main-card rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">
                Entrez l'URL du média
              </h2>
              {selectedPlatform && (
                <div className="flex items-center space-x-2 px-3 py-1 glass-card rounded-full">
                  <span className="text-lg platform-icon">{getPlatformIcon(selectedPlatform)}</span>
                  <span className="text-sm font-medium text-gray-300">{getPlatformName(selectedPlatform)}</span>
                  <span className="text-lg">{getAuthStatusIcon(selectedPlatform)}</span>
                </div>
              )}
            </div>
            
            <div className="flex gap-4 mb-6">
              <input
                type="text"
                placeholder="https://... (YouTube, Instagram, Reddit, etc.)"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (e.target.value) {
                    setSelectedPlatform(detectPlatformFromUrl(e.target.value));
                  }
                }}
                className="flex-1 px-4 py-3 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-lg placeholder-gray-400"
                onKeyPress={(e) => e.key === 'Enter' && fetchMediaInfo()}
              />
              <button 
                onClick={fetchMediaInfo} 
                disabled={loading || !url}
                className="btn-gradient px-6 py-3 hover:from-purple-700 hover:to-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
              >
                {loading ? '⏳ Analyse...' : '🔍 Analyser'}
              </button>
            </div>

            {/* Supported Platforms */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Plateformes supportées :</h3>
              <div className="flex flex-wrap gap-2">
                {platforms.map((platform) => (
                  <span key={platform.key} className="inline-flex items-center px-3 py-1 glass-card text-gray-300 text-sm rounded-full">
                    <span className="platform-icon">{getPlatformIcon(platform.key)}</span> {platform.name} {getAuthStatusIcon(platform.key)}
                  </span>
                ))}
              </div>
            </div>

            {/* Media Information */}
            {mediaInfo && (
              <div className="border-t border-gray-600 pt-6">
                <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
                  <span className="platform-icon">{getPlatformIcon(mediaInfo.platform)}</span> Informations du média
                </h3>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-3 text-gray-300">
                    <div><strong>Titre:</strong> {mediaInfo.title}</div>
                    <div><strong>Plateforme:</strong> {getPlatformName(mediaInfo.platform)}</div>
                    {mediaInfo.uploader && <div><strong>Créateur:</strong> {mediaInfo.uploader}</div>}
                    {mediaInfo.duration && <div><strong>Durée:</strong> {formatDuration(mediaInfo.duration)}</div>}
                    {mediaInfo.view_count && <div><strong>Vues/Likes:</strong> {mediaInfo.view_count.toLocaleString()}</div>}
                    <div><strong>Type:</strong> {mediaInfo.media_type}</div>
                    {mediaInfo.media_count > 1 && <div><strong>Nombre d'éléments:</strong> {mediaInfo.media_count}</div>}
                  </div>

                  {/* Download Options */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-white">Options de téléchargement</h4>
                    
                    {(mediaInfo.platform === 'youtube' || mediaInfo.media_type === 'video') && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Qualité:</label>
                          <select
                            value={downloadOptions.quality}
                            onChange={(e) => setDownloadOptions({...downloadOptions, quality: e.target.value})}
                            className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="best">Meilleure qualité</option>
                            <option value="worst">Qualité minimale</option>
                            <option value="bestvideo[height<=720]+bestaudio/best[height<=720]">720p</option>
                            <option value="bestvideo[height<=480]+bestaudio/best[height<=480]">480p</option>
                          </select>
                        </div>

                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id="audio_only"
                            checked={downloadOptions.audio_only}
                            onChange={(e) => setDownloadOptions({...downloadOptions, audio_only: e.target.checked})}
                            className="mr-2 accent-purple-500"
                          />
                          <label htmlFor="audio_only" className="text-sm text-gray-300">
                            Audio uniquement (MP3)
                          </label>
                        </div>

                        {!downloadOptions.audio_only && (
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Format de sortie:</label>
                            <select
                              value={downloadOptions.output_format}
                              onChange={(e) => setDownloadOptions({...downloadOptions, output_format: e.target.value})}
                              className="w-full px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                            >
                              <option value="mp4">MP4</option>
                              <option value="avi">AVI</option>
                              <option value="mkv">MKV</option>
                              <option value="webm">WebM</option>
                            </select>
                          </div>
                        )}
                      </>
                    )}

                    <button 
                      onClick={startDownload} 
                      disabled={loading} 
                      className="w-full btn-gradient px-6 py-3 hover:from-red-700 hover:to-pink-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
                    >
                      {loading ? '⏳ Démarrage...' : '⬇️ Commencer le téléchargement'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Cosplay Search Section */
          <div className="main-card rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">
                👘 Recherche de Cosplay
              </h2>
              <div className="text-sm text-gray-300">
                Recherchez par nom de cosplayer ou personnage
              </div>
            </div>
            
            <div className="relative mb-6">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="Ex: Dva Overwatch, Harley Quinn, Chun Li..."
                    value={cosplayQuery}
                    onChange={(e) => {
                      setCosplayQuery(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    className="w-full px-4 py-3 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-lg placeholder-gray-400"
                    onKeyPress={(e) => e.key === 'Enter' && searchCosplay()}
                  />
                  
                  {/* Suggestions Dropdown */}
                  {showSuggestions && cosplaySuggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 glass-card border border-gray-600 rounded-lg z-50 max-h-60 overflow-y-auto">
                      {cosplaySuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          className="suggestion-item px-4 py-2 text-gray-300 cursor-pointer hover:text-white rounded"
                          onClick={() => {
                            setCosplayQuery(suggestion);
                            setShowSuggestions(false);
                          }}
                        >
                          {suggestion}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <button 
                  onClick={searchCosplay} 
                  disabled={loading || !cosplayQuery.trim()}
                  className="btn-gradient px-6 py-3 hover:from-purple-700 hover:to-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
                >
                  {loading ? '⏳ Recherche...' : '🔍 Rechercher'}
                </button>
              </div>
            </div>

            {/* Cosplay Results */}
            {cosplayResults.length > 0 && (
              <div className="border-t border-gray-600 pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">
                    Résultats de recherche ({cosplayResults.length})
                  </h3>
                  <div className="text-sm text-gray-300">
                    {selectedCosplays.length} sélectionné(s)
                  </div>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {cosplayResults.map((result) => (
                    <div
                      key={result.id}
                      className={`cosplay-result-card p-4 ${selectedCosplays.includes(result.id) ? 'selected' : ''}`}
                      onClick={() => toggleCosplaySelection(result.id)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1 truncate">
                            {result.name}
                          </h4>
                          <div className="flex items-center space-x-2 text-sm text-gray-400">
                            <span className="platform-icon">{getPlatformIcon(result.platform)}</span>
                            <span>{getPlatformName(result.platform)}</span>
                          </div>
                        </div>
                        <div className="text-2xl">
                          {selectedCosplays.includes(result.id) ? '✅' : '⭕'}
                        </div>
                      </div>
                      
                      {result.gallery_count && (
                        <div className="text-xs text-gray-400 mb-2">
                          📸 {result.gallery_count} images
                        </div>
                      )}
                      
                      {result.description && (
                        <div className="text-xs text-gray-500 truncate">
                          {result.description}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {selectedCosplays.length > 0 && (
                  <div className="flex items-center justify-between glass-card p-4 rounded-lg">
                    <div className="text-white">
                      <div className="font-medium">{selectedCosplays.length} galleries sélectionnées</div>
                      <div className="text-sm text-gray-400">Qualité: {downloadOptions.quality}</div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <select
                        value={downloadOptions.quality}
                        onChange={(e) => setDownloadOptions({...downloadOptions, quality: e.target.value})}
                        className="px-3 py-2 bg-black bg-opacity-20 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="best">Meilleure qualité</option>
                        <option value="worst">Qualité minimale</option>
                      </select>
                      <button
                        onClick={downloadSelectedCosplays}
                        disabled={loading}
                        className="btn-gradient px-6 py-3 hover:from-green-700 hover:to-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
                      >
                        {loading ? '⏳ Téléchargement...' : '⬇️ Télécharger Sélection'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Downloads List */}
        <div className="main-card rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              Mes téléchargements ({downloads.length})
            </h3>
            <button 
              onClick={fetchDownloads}
              className="px-4 py-2 glass-card hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            >
              🔄 Actualiser
            </button>
          </div>

          {downloads.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <div className="text-6xl mb-4">📥</div>
              <p>Aucun téléchargement pour le moment</p>
              <p className="text-sm mt-2">Commencez par analyser une URL ou rechercher un cosplay</p>
            </div>
          ) : (
            <div className="space-y-4">
              {downloads.map((download) => (
                <div key={download.id} className="download-card glass-card border border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-lg platform-icon">{getPlatformIcon(download.platform)}</span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(download.status)}`}>
                          {getStatusText(download.status)}
                        </span>
                        {download.progress > 0 && download.status === 'downloading' && (
                          <span className="text-sm text-gray-400">
                            {download.progress.toFixed(1)}%
                          </span>
                        )}
                        {download.file_size && (
                          <span className="text-sm text-gray-500">
                            {formatFileSize(download.file_size)}
                          </span>
                        )}
                        {download.cosplay_query && (
                          <span className="px-2 py-1 text-xs bg-purple-600 text-white rounded-full">
                            👘 Cosplay
                          </span>
                        )}
                      </div>
                      
                      <h4 className="font-medium text-white mb-1 truncate">
                        {download.title || 'Titre non disponible'}
                      </h4>
                      
                      <p className="text-sm text-gray-400 mb-1">
                        Plateforme: {getPlatformName(download.platform)} | Créateur: {download.uploader || 'Inconnu'}
                      </p>
                      
                      <p className="text-xs text-gray-500 truncate">
                        {download.url}
                      </p>
                      
                      {download.status === 'downloading' && download.progress > 0 && (
                        <div className="mt-3">
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div 
                              className="progress-bar-animated h-2 rounded-full transition-all duration-300" 
                              style={{width: `${download.progress}%`}}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {download.error_message && (
                        <div className="mt-2 text-sm text-red-300 bg-red-900 bg-opacity-30 p-2 rounded">
                          {download.error_message}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex space-x-2 ml-4">
                      {download.status === 'completed' && (
                        <button 
                          onClick={() => downloadFile(download.id, download.filename)}
                          className="px-3 py-1 btn-gradient hover:from-green-600 hover:to-green-700 text-white text-sm rounded transition-all duration-200 transform hover:scale-105"
                          title="Télécharger le fichier"
                        >
                          ⬇️
                        </button>
                      )}
                      <button 
                        onClick={() => deleteDownload(download.id)}
                        className="px-3 py-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white text-sm rounded transition-all duration-200 transform hover:scale-105"
                        title="Supprimer"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;