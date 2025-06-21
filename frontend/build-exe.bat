@echo off
echo 🚀 Construction de l'application Media Downloader...

REM Nettoyer les builds précédents
echo 🧹 Nettoyage des builds précédents...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Construire l'application React
echo ⚛️  Construction de l'interface React...
call npm run build

REM Vérifier si le build a réussi
if not exist build (
    echo ❌ Échec de la construction React
    pause
    exit /b 1
)

echo ✅ Build React terminé

REM Construire l'application Electron
echo 📦 Construction de l'application Electron...
call npm run dist

REM Vérifier si l'EXE a été créé
if exist "dist\Media Downloader Setup 1.0.0.exe" (
    echo 🎉 SUCCESS! Fichier EXE créé: dist\Media Downloader Setup 1.0.0.exe
    echo 📁 Taille du fichier:
    dir "dist\Media Downloader Setup 1.0.0.exe"
    
    echo.
    echo 🎯 INSTRUCTIONS D'INSTALLATION:
    echo 1. Allez dans le dossier dist\
    echo 2. Double-cliquez sur 'Media Downloader Setup 1.0.0.exe'
    echo 3. Suivez les instructions d'installation
    echo 4. L'application sera disponible dans le menu Démarrer
    echo.
    echo 📝 CARACTÉRISTIQUES DE L'APPLICATION:
    echo • Interface fluide violet/noir animée
    echo • Recherche de cosplay avec sélection multiple
    echo • Support 11+ plateformes (YouTube, Instagram, Reddit, etc.)
    echo • Téléchargements en arrière-plan avec progression
    echo • Organisation automatique des fichiers
    echo.
    
    REM Ouvrir le dossier dist
    explorer dist
) else (
    echo ❌ Échec de la création de l'EXE. Vérifiez les logs ci-dessus.
    pause
    exit /b 1
)

pause