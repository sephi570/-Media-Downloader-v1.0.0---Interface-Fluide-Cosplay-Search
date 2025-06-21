import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [downloads, setDownloads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadOptions, setDownloadOptions] = useState({
    quality: 'best',
    audio_only: false,
    output_format: 'mp4'
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Fetch video information
  const fetchVideoInfo = async () => {
    if (!url || (!url.includes('youtube.com') && !url.includes('youtu.be'))) {
      alert('Veuillez entrer une URL YouTube valide');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/video/info`, { url });
      setVideoInfo(response.data);
    } catch (error) {
      alert('Échec de récupération des informations vidéo: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Start download
  const startDownload = async () => {
    if (!url) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/video/download`, {
        url,
        ...downloadOptions
      });
      
      alert('Téléchargement commencé! ID: ' + response.data.download_id);
      fetchDownloads();
      setUrl('');
      setVideoInfo(null);
    } catch (error) {
      alert('Échec du démarrage du téléchargement: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  // Fetch downloads list
  const fetchDownloads = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/video/downloads`);
      setDownloads(response.data);
    } catch (error) {
      console.error('Échec de récupération des téléchargements:', error);
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
      await axios.delete(`${BACKEND_URL}/api/video/download/${downloadId}`);
      fetchDownloads();
    } catch (error) {
      alert('Échec de suppression du téléchargement: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Download file
  const downloadFile = async (downloadId, filename) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/video/download/${downloadId}`, {
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
    const interval = setInterval(() => {
      fetchDownloads();
      fetchStats();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

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
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'downloading': return 'text-yellow-600 bg-yellow-100';
      case 'pending': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-gray-100">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🎥 Téléchargeur YouTube
              </h1>
              <p className="text-gray-600 mt-1">
                Téléchargez vos vidéos YouTube préférées en haute qualité
              </p>
            </div>
            
            {/* Stats */}
            {stats && (
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-blue-50 px-4 py-2 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{stats.total_downloads}</div>
                  <div className="text-xs text-blue-500">Total</div>
                </div>
                <div className="bg-green-50 px-4 py-2 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{stats.completed_downloads}</div>
                  <div className="text-xs text-green-500">Terminés</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* URL Input Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">
            Entrez l'URL de la vidéo YouTube
          </h2>
          
          <div className="flex gap-4 mb-6">
            <input
              type="text"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none text-lg"
              onKeyPress={(e) => e.key === 'Enter' && fetchVideoInfo()}
            />
            <button 
              onClick={fetchVideoInfo} 
              disabled={loading || !url}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? '⏳ Chargement...' : '🔍 Analyser'}
            </button>
          </div>

          {/* Video Information */}
          {videoInfo && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Informations de la vidéo</h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div><strong>Titre:</strong> {videoInfo.title}</div>
                  <div><strong>Créateur:</strong> {videoInfo.uploader}</div>
                  <div><strong>Durée:</strong> {formatDuration(videoInfo.duration)}</div>
                  <div><strong>Vues:</strong> {videoInfo.view_count?.toLocaleString()}</div>
                </div>

                {/* Download Options */}
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-800">Options de téléchargement</h4>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Qualité:</label>
                    <select
                      value={downloadOptions.quality}
                      onChange={(e) => setDownloadOptions({...downloadOptions, quality: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
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
                      className="mr-2"
                    />
                    <label htmlFor="audio_only" className="text-sm text-gray-700">
                      Audio uniquement (MP3)
                    </label>
                  </div>

                  {!downloadOptions.audio_only && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Format de sortie:</label>
                      <select
                        value={downloadOptions.output_format}
                        onChange={(e) => setDownloadOptions({...downloadOptions, output_format: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
                      >
                        <option value="mp4">MP4</option>
                        <option value="avi">AVI</option>
                        <option value="mkv">MKV</option>
                        <option value="webm">WebM</option>
                      </select>
                    </div>
                  )}

                  <button 
                    onClick={startDownload} 
                    disabled={loading} 
                    className="w-full px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
                  >
                    {loading ? '⏳ Démarrage...' : '⬇️ Commencer le téléchargement'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Downloads List */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-800">
              Mes téléchargements ({downloads.length})
            </h3>
            <button 
              onClick={fetchDownloads}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            >
              🔄 Actualiser
            </button>
          </div>

          {downloads.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-6xl mb-4">📥</div>
              <p>Aucun téléchargement pour le moment</p>
              <p className="text-sm mt-2">Commencez par analyser une URL YouTube ci-dessus</p>
            </div>
          ) : (
            <div className="space-y-4">
              {downloads.map((download) => (
                <div key={download.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(download.status)}`}>
                          {getStatusText(download.status)}
                        </span>
                        {download.progress > 0 && download.status === 'downloading' && (
                          <span className="text-sm text-gray-600">
                            {download.progress.toFixed(1)}%
                          </span>
                        )}
                        {download.file_size && (
                          <span className="text-sm text-gray-500">
                            {formatFileSize(download.file_size)}
                          </span>
                        )}
                      </div>
                      
                      <h4 className="font-medium text-gray-900 mb-1 truncate">
                        {download.title || 'Titre non disponible'}
                      </h4>
                      
                      <p className="text-sm text-gray-600 mb-1">
                        Créateur: {download.uploader || 'Inconnu'}
                      </p>
                      
                      <p className="text-xs text-gray-500 truncate">
                        {download.url}
                      </p>
                      
                      {download.status === 'downloading' && download.progress > 0 && (
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                              style={{width: `${download.progress}%`}}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {download.error_message && (
                        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                          {download.error_message}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex space-x-2 ml-4">
                      {download.status === 'completed' && (
                        <button 
                          onClick={() => downloadFile(download.id, download.filename)}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
                          title="Télécharger le fichier"
                        >
                          ⬇️
                        </button>
                      )}
                      <button 
                        onClick={() => deleteDownload(download.id)}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
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