# 🚀 Media Downloader - Application Multi-Plateformes

[![Download](https://img.shields.io/badge/Download-EXE-purple?style=for-the-badge&logo=windows)](../../releases/latest)
[![Version](https://img.shields.io/github/v/release/votre-username/media-downloader?style=for-the-badge)](../../releases)
[![Downloads](https://img.shields.io/github/downloads/votre-username/media-downloader/total?style=for-the-badge)](../../releases)

> **Téléchargeur universel de médias avec interface fluide violet/noir et recherche cosplay avancée**

![App Screenshot](docs/screenshot.png)

## ✨ Fonctionnalités

### 🌊 **Interface Stunning**
- **Fond fluide animé** violet/noir avec particules flottantes
- **Glass morphism** et effets de transparence
- **Animations fluides** et transitions buttery smooth
- **Thème sombre moderne** avec effets de lueur

### 👘 **Recherche Cosplay Intelligente**
- **Moteur de recherche** par nom de cosplayer/personnage
- **Suggestions automatiques** (Dva Overwatch, Harley Quinn, etc.)
- **Sélection multiple** avec confirmation visuelle
- **Téléchargement en masse** de galleries complètes

### 📱 **Support Multi-Plateformes (11+)**
- 🎥 **YouTube** - Vidéos HD, audio MP3, playlists
- 📷 **Instagram** - Posts, Stories, Reels
- 🔴 **Reddit** - Images, vidéos, GIFs
- 🔞 **Sites Adultes** - PornHub, RedTube
- 📚 **Galleries** - NHentai, Luscious, Nutaku, CosplayTele, ImHentai
- 🎵 **Spotify** - Previews (limité par DRM)

### ⚙️ **Fonctionnalités Avancées**
- **Authentification mémorisée** (Instagram, Reddit)
- **Organisation automatique** des fichiers
- **Téléchargements background** avec progression temps réel
- **Qualité personnalisable** (4K, 1080p, 720p, audio seul)
- **Historique complet** avec filtrage et statistiques

## 🚀 Installation Rapide

### 📥 **Téléchargement Direct**

**[⬇️ TÉLÉCHARGER L'APPLICATION (.EXE)](../../releases/latest/download/Media.Downloader.Setup.1.0.0.exe)**

> **Taille :** ~300MB (backend inclus) | **Compatible :** Windows 10/11 x64

### 📋 **Instructions**
1. **Téléchargez** le fichier EXE depuis les releases
2. **Exécutez** `Media Downloader Setup 1.0.0.exe`
3. **Suivez** l'assistant d'installation
4. **Lancez** depuis le menu Démarrer ou le raccourci bureau

## 🎮 Guide d'Utilisation

### **Mode URL (Classique)**
1. **Collez une URL** (YouTube, Instagram, Reddit, etc.)
2. **Cliquez "Analyser"** pour récupérer les infos
3. **Choisissez la qualité** et les options
4. **Lancez le téléchargement** et suivez la progression

### **Mode Cosplay (Exclusif)**
1. **Basculez vers "Cosplay"** dans l'en-tête
2. **Tapez un nom** (ex: "Dva Overwatch")
3. **Sélectionnez les galleries** qui vous intéressent
4. **Téléchargez en masse** toutes vos sélections

### **Configuration Authentification**
1. **Ouvrez les Paramètres** (⚙️)
2. **Configurez Instagram/Reddit** pour un accès complet
3. **Vos identifiants sont sauvegardés** localement

## 🗂️ Organisation des Fichiers

```
📁 Downloads/
├── 🎥 YouTube/
│   └── [Nom du Créateur]/
├── 📷 Instagram/
│   └── [Nom d'Utilisateur]/
├── 🔴 Reddit/
│   └── [u/username]/
├── 🔞 Pornhub/
│   └── [Créateur]/
└── 📚 Galleries/
    ├── NHentai/
    ├── Luscious/
    └── CosplayTele/
```

## 🛡️ Sécurité & Confidentialité

- ✅ **Aucune collecte de données** personnelles
- ✅ **Authentification locale** (stockage sécurisé)
- ✅ **Téléchargements directs** depuis les plateformes
- ✅ **Code source ouvert** et auditable
- ✅ **Antivirus compatible** (peut nécessiter autorisation initiale)

## 🔧 Développement

### **Prérequis**
- Node.js 16+
- Python 3.8+
- MongoDB

### **Installation Dev**
```bash
# Cloner le repo
git clone https://github.com/votre-username/media-downloader.git
cd media-downloader

# Backend
cd backend
pip install -r requirements.txt
python server.py

# Frontend
cd ../frontend
npm install
npm start

# Build EXE
npm run dist
```

### **Technologies**
- **Frontend :** React, TailwindCSS, Axios
- **Backend :** FastAPI, MongoDB, Motor
- **Téléchargement :** yt-dlp, instaloader, gallery-dl
- **Desktop :** Electron, Electron Builder

## 📝 Changelog

### **v1.0.0** (Dernière version)
- ✨ Interface fluide violet/noir avec animations
- ✨ Moteur de recherche cosplay avec sélection multiple
- ✨ Support 11+ plateformes
- ✨ Authentification Instagram/Reddit
- ✨ Application desktop standalone
- ✨ Organisation automatique des fichiers

## 🐛 Support & Bug Reports

- **🐞 Signaler un bug :** [Issues](../../issues)
- **💡 Demandes de fonctionnalités :** [Issues](../../issues/new?template=feature_request.md)
- **📚 Documentation :** [Wiki](../../wiki)

## 📜 Licence

MIT License - Libre d'utilisation pour usage personnel.

---

<div align="center">

**⭐ Si cette application vous plaît, n'hésitez pas à mettre une étoile !**

[![Stars](https://img.shields.io/github/stars/votre-username/media-downloader?style=social)](../../stargazers)
[![Forks](https://img.shields.io/github/forks/votre-username/media-downloader?style=social)](../../network/members)

</div>
