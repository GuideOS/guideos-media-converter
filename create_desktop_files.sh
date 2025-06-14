#!/bin/bash

# Sicherstellen, dass die Verzeichnisse existieren
mkdir -p debian/guideos-media-converter/usr/share/applications
#mkdir -p debian/guideos-ticket-tool/etc/xdg/autostart

# Erstellen der ersten .desktop-Datei
cat > debian/guideos-media-converter/usr/share/applications/guideos-media-converter.desktop <<EOL
[Desktop Entry]
Version=1.0
Name=GuideOS Media Converter
Comment=Media conversion tool for GuideOS
Name[de]=GuideOS Medienkonverter
Comment[de]=Medienkonvertierungstool für GuideOS
Exec=guideos-media-converter
Icon=guideos-media-converter
Terminal=false
Type=Application
Categories=GuideOS;
StartupNotify=true
EOL