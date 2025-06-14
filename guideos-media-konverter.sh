#!/bin/bash


# ==============================================
# GuideOS-Media-Konverter
# ==============================================
# Entwickler: evilware666
# Beschreibung:
# Dieses Skript bietet eine einfache grafische Benutzeroberfläche, 
# um verschiedene Medienformate wie Video, Bild und Audio zu konvertieren.
# Es verwendet Zenity für die Benutzerinteraktion und ermöglicht die Auswahl
# von verschiedenen Zielformaten und Qualitätsoptionen.
# 
# Unterstützte Formate:
# - Video: MP4, AVI, MKV, MOV
# - Bild: JPG, PNG, WEBP, BMP
# - Audio: MP3, FLAC, WAV, OGG
#
# Das Skript bietet Fortschrittsbalken und Fehlerbehandlung für die 
# Konvertierungsprozesse und kann mit einem Klick aufgerufen werden.
# ==============================================

# Zenity-Fenstergröße und Schrift anpassen
ZENITY_OPTIONS="--width=600 --height=400"

# ==============================================
# VIDEO-KONVERTIERUNG MIT QUALITÄTSAUSWAHL
# ==============================================
convert_video() {
    input_file=$(zenity --file-selection --title="Wählen Sie ein Video aus" $ZENITY_OPTIONS)
    [ -z "$input_file" ] && { zenity --error --text="Keine Datei ausgewählt!" $ZENITY_OPTIONS; return; }

    output_format=$(zenity --list --title="Zielformat" --column="Format" mp4 avi mkv mov $ZENITY_OPTIONS)
    [ -z "$output_format" ] && { zenity --error --text="Kein Format ausgewählt!" $ZENITY_OPTIONS; return; }

    # Videoqualität auswählen
    output_quality=$(zenity --list --title="Videoqualität" \
        --column="Qualität" --column="Auflösung" \
        "4K" "3840x2160" \
        "2K" "2560x1440" \
        "1080p" "1920x1080" \
        "720p" "1280x720" \
        $ZENITY_OPTIONS)
    [ -z "$output_quality" ] && { zenity --error --text="Keine Qualität ausgewählt!" $ZENITY_OPTIONS; return; }

    # Skalierungsparameter setzen
    case $output_quality in
        "4K") height=2160 ;;
        "2K") height=1440 ;;
        "1080p") height=1080 ;;
        "720p") height=720 ;;
        *) height=480 ;;
    esac

    output_file=$(zenity --file-selection --save --confirm-overwrite \
        --filename="${input_file%.*}_${output_quality}.$output_format" \
        --title="Speichern unter" $ZENITY_OPTIONS)
    [ -z "$output_file" ] && { zenity --error --text="Kein Speicherort ausgewählt!" $ZENITY_OPTIONS; return; }

    # Konvertierung mit Fortschrittsbalken
    total_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_file" | cut -d. -f1)
    [ -z "$total_duration" ] && total_duration=1  # Fallback

    (
        ffmpeg -i "$input_file" -vf "scale=-2:$height" -progress - -v error -y "$output_file" 2>/dev/null |&
        while IFS= read -r line; do
            if [[ $line =~ out_time_ms=([0-9]+) ]]; then
                current_ms=${BASH_REMATCH[1]}
                percent=$(( (current_ms * 100) / (total_duration * 1000000) ))
                echo "$percent"
            fi
        done
        echo "100"
    ) | zenity --progress --title="Video wird konvertiert..." --auto-close

    [ -f "$output_file" ] && zenity --info --text="Video erfolgreich konvertiert:\n$output_file" $ZENITY_OPTIONS ||
    zenity --error --text="Fehler bei der Konvertierung!" $ZENITY_OPTIONS
}

# ==============================================
# BILD-KONVERTIERUNG MIT QUALITÄTSAUSWAHL
# ==============================================
convert_image() {
    input_file=$(zenity --file-selection --title="Wählen Sie ein Bild aus" $ZENITY_OPTIONS)
    [ -z "$input_file" ] && { zenity --error --text="Keine Datei ausgewählt!" $ZENITY_OPTIONS; return; }

    output_format=$(zenity --list --title="Zielformat" --column="Format" jpg png webp bmp $ZENITY_OPTIONS)
    [ -z "$output_format" ] && { zenity --error --text="Kein Format ausgewählt!" $ZENITY_OPTIONS; return; }

    # Bildqualität auswählen
    img_quality=$(zenity --list --title="Bildqualität" \
        --column="Einstellung" --column="Beschreibung" \
        "Original" "Keine Änderung" \
        "HQ" "Hohe Qualität (90%)" \
        "MQ" "Mittlere Qualität (75%)" \
        "LQ" "Niedrige Qualität (50%)" \
        $ZENITY_OPTIONS)
    
    # Qualitätsparameter setzen
    case $img_quality in
        "HQ") quality=90 ;;
        "MQ") quality=75 ;;
        "LQ") quality=50 ;;
        *) quality=100 ;;
    esac

    output_file=$(zenity --file-selection --save --confirm-overwrite \
        --filename="${input_file%.*}_${img_quality}.$output_format" \
        --title="Speichern unter" $ZENITY_OPTIONS)
    [ -z "$output_file" ] && { zenity --error --text="Kein Speicherort ausgewählt!" $ZENITY_OPTIONS; return; }

    # Konvertierung mit Fortschritt
    (
        echo "25"; convert "$input_file" -quality $quality "$output_file"
        echo "50"; sleep 1  # Simulierter Fortschritt für bessere Visualisierung
        echo "75"; sleep 1
        echo "100"
    ) | zenity --progress --title="Bild wird konvertiert..." --auto-close

    [ -f "$output_file" ] && zenity --info --text="Bild erfolgreich konvertiert:\n$output_file" $ZENITY_OPTIONS ||
    zenity --error --text="Fehler bei der Konvertierung!" $ZENITY_OPTIONS
}

# ==============================================
# AUDIO-KONVERTIERUNG MIT QUALITÄTSAUSWAHL
# ==============================================
convert_audio() {
    input_file=$(zenity --file-selection --title="Wählen Sie eine Audiodatei aus" $ZENITY_OPTIONS)
    [ -z "$input_file" ] && { zenity --error --text="Keine Datei ausgewählt!" $ZENITY_OPTIONS; return; }

    output_format=$(zenity --list --title="Zielformat" --column="Format" mp3 flac wav ogg $ZENITY_OPTIONS)
    [ -z "$output_format" ] && { zenity --error --text="Kein Format ausgewählt!" $ZENITY_OPTIONS; return; }

    # Audioqualität auswählen
    audio_quality=$(zenity --list --title="Audioqualität" \
        --column="Bitrate" --column="Qualität" \
        "320k" "Hohe Qualität (320 kbps)" \
        "256k" "Gute Qualität (256 kbps)" \
        "192k" "Mittlere Qualität (192 kbps)" \
        "128k" "Niedrige Qualität (128 kbps)" \
        $ZENITY_OPTIONS)
    [ -z "$audio_quality" ] && audio_quality="256k"  # Default-Wert

    output_file=$(zenity --file-selection --save --confirm-overwrite \
        --filename="${input_file%.*}_${audio_quality}.$output_format" \
        --title="Speichern unter" $ZENITY_OPTIONS)
    [ -z "$output_file" ] && { zenity --error --text="Kein Speicherort ausgewählt!" $ZENITY_OPTIONS; return; }

    # Konvertierung mit Fortschritt
    (
        echo "33"; ffmpeg -i "$input_file" -b:a $audio_quality -y "$output_file" 2>/dev/null
        echo "66"; sleep 1  # Simulierter Fortschritt
        echo "100"
    ) | zenity --progress --title="Audio wird konvertiert..." --auto-close

    [ -f "$output_file" ] && zenity --info --text="Audio erfolgreich konvertiert:\n$output_file" $ZENITY_OPTIONS ||
    zenity --error --text="Fehler bei der Konvertierung!" $ZENITY_OPTIONS
}

# ==============================================
# HAUPTPROGRAMM
# ==============================================
while true; do
    choice=$(zenity --list --title="GuideOS-Media-Konverter" \
        --text="Was möchten Sie konvertieren?" \
        --column="Typ" --column="Beschreibung" \
        "Video" "MP4, AVI, MKV-Dateien" \
        "Bild" "JPG, PNG, WEBP-Dateien" \
        "Audio" "MP3, FLAC, WAV-Dateien" \
        --cancel-label="Beenden" $ZENITY_OPTIONS)

    case $choice in
        "Video") convert_video ;;
        "Bild") convert_image ;;
        "Audio") convert_audio ;;
        *) exit 0 ;;
    esac
done
