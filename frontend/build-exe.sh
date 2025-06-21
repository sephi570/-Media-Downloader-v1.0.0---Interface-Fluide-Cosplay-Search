#!/bin/bash

echo "🚀 Construction de l'application Media Downloader..."

# Nettoyer les builds précédents
echo "🧹 Nettoyage des builds précédents..."
rm -rf build/
rm -rf dist/

# Construire l'application React
echo "⚛️  Construction de l'interface React..."
npm run build

# Vérifier si le build a réussi
if [ ! -d "build" ]; then
    echo "❌ Échec de la construction React"
    exit 1
fi

echo "✅ Build React terminé"

# Construire l'application Electron
echo "📦 Construction de l'application Electron..."
npm run dist

# Vérifier si l'EXE a été créé
if [ -f "dist/Media Downloader Setup 1.0.0.exe" ]; then
    echo "🎉 SUCCESS! Fichier EXE créé: dist/Media Downloader Setup 1.0.0.exe"
    echo "📁 Taille du fichier:"
    ls -lh "dist/Media Downloader Setup 1.0.0.exe"
    
    echo ""
    echo "🎯 INSTRUCTIONS D'INSTALLATION:"
    echo "1. Allez dans le dossier dist/"
    echo "2. Double-cliquez sur 'Media Downloader Setup 1.0.0.exe'"
    echo "3. Suivez les instructions d'installation"
    echo "4. L'application sera disponible dans le menu Démarrer"
    echo ""
    echo "📝 CARACTÉRISTIQUES DE L'APPLICATION:"
    echo "• Interface fluide violet/noir animée"
    echo "• Recherche de cosplay avec sélection multiple"
    echo "• Support 11+ plateformes (YouTube, Instagram, Reddit, etc.)"
    echo "• Téléchargements en arrière-plan avec progression"
    echo "• Organisation automatique des fichiers"
    echo ""
else
    echo "❌ Échec de la création de l'EXE. Vérifiez les logs ci-dessus."
    exit 1
fi