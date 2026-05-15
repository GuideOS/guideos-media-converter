
# GuideOS Media-Converter  
Ein moderner, einsteigerfreundlicher Medien‑Konverter für Linux – entwickelt mit **GTK4** und **libadwaita**.

## Entwickler: 
evilware666 & Helga

## Version 
1.1

## ✨ Funktionen
- **Video‑, Audio‑ und Bild‑Konvertierung**  
  Unterstützt MP4, AVI, MKV, MOV, WEBM, JPG, PNG, WEBP, BMP, MP3, FLAC, WAV, OGG u.v.m.
- **Batch‑Konvertierung**  
  Mehrere Dateien gleichzeitig konvertieren – inkl. Fortschrittsanzeige pro Datei.
- **Drag & Drop Unterstützung**  
  Dateien einfach in das Fenster ziehen.
- **Automatische Thumbnails**  
  • Video: Frame‑Vorschau  
  • Bild: verkleinertes Vorschaubild  
  • Audio: Wellenform‑Bild  
- **Fortschrittsanzeige mit Prozenten**  
  ffmpeg‑Parsing (`out_time_ms` / `time=`) für echte Fortschrittswerte.
- **Qualitäts‑ und Auflösungswahl**  
  • Video: 4K, 2K, 1080p, 720p, 480p  
  • Bild: Qualitätsstufen (100–50%)  
  • Audio: Bitraten (320k–128k)
- **Speicherung der letzten Einstellungen**  
  Merkt sich Format & Qualität pro Medien‑Typ (`~/.config/guideos-mediaconverter.ini`).
- **System‑Benachrichtigungen**  
  Erfolg/Fehler über libnotify.
- **Abbrechen‑Funktion**  
  Konvertierung jederzeit stoppen.
- **Saubere GTK4‑UI**  
  libadwaita‑Design, responsive Layouts, moderne Dialoge.

---

## 📦 Abhängigkeiten
- `ffmpeg`
- `ffprobe`
- `imagemagick` (für Bild‑Konvertierung & Thumbnails)
- `python3-gi`
- GTK4 + libadwaita
- `python3-notify2` / GI Notify

---

## ▶️ Starten
```bash
python3 mediakonverter.py
```

---

## 🖼️ Bedienung
1. **Medientyp wählen** (Video / Bild / Audio)  
2. Dateien per **Drag & Drop** oder **Dateiauswahl** hinzufügen  
3. **Zielformat** und **Qualität** wählen  
4. **Konvertieren** klicken  
5. Fortschritt & Status werden live angezeigt  
6. Nach Abschluss erscheint eine System‑Benachrichtigung

---

## 🆕 Neuerungen in dieser Version
- ✔ **Batch‑Konvertierung** mit Dateizähler  
- ✔ **Drag & Drop** für mehrere Dateien  
- ✔ **Thumbnails für alle Medientypen**  
- ✔ **Echte ffmpeg‑Fortschrittsanzeige** (Parsing von `out_time_ms` & `time=`)  
- ✔ **Speicherung der letzten Einstellungen** (Format & Qualität)  
- ✔ **Verbesserte Fehlerdialoge**  
- ✔ **Audio‑Wellenform‑Thumbnail**  
- ✔ **Zentrierte Thumbnail‑Box & Info‑Labels**  
- ✔ **ESC = Zurück**, **Enter = Konvertieren**  
- ✔ **Verbesserte Status‑ und Prozentanzeige**  
- ✔ **Stabilere ffmpeg‑Aufrufe & Timeout‑Handling**

---

## 📄 Lizenz
MIT‑Lizenz  


