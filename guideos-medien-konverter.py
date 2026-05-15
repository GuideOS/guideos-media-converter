#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GuideOS Media‑Konverter – GTK4 / Libadwaita
===========================================
Ein moderner, einsteigerfreundlicher Medien‑Konverter für Linux.

Unterstützt:
  • Video‑Konvertierung (MP4, AVI, MKV, MOV, WEBM)
  • Audio‑Konvertierung (MP3, FLAC, WAV, OGG)
  • Bild‑Konvertierung (JPG, PNG, WEBP, BMP)
  • Batch‑Konvertierung beliebig vieler Dateien
  • Fortschrittsanzeige mit ffmpeg‑Parsing
  • Drag‑&‑Drop, Thumbnails, System‑Benachrichtigungen

Technik:
  • GTK4 / Libadwaita Oberfläche
  • ffmpeg / ffprobe Backend
  • Persistente Einstellungen (Format, Qualität)
  • Saubere Thread‑Trennung für UI‑Responsivität

Autor   : Helga & evilware666
Version : 1.1
Lizenz  : MIT
"""

import subprocess
import os
import threading
import time
import configparser
import re
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Gdk, GLib, Adw, Notify, Pango

# Verfügbare Formate und ihre Optionen
VIDEO_FORMATS = {
    'mp4': {'codec': 'libx264', 'audio_codec': 'aac', 'ext': '.mp4'},
    'avi': {'codec': 'libx264', 'audio_codec': 'mp3', 'ext': '.avi'},
    'mkv': {'codec': 'libx264', 'audio_codec': 'aac', 'ext': '.mkv'},
    'mov': {'codec': 'libx264', 'audio_codec': 'aac', 'ext': '.mov'}
}

IMAGE_FORMATS = {
    'jpg': {'ext': '.jpg', 'quality_param': '-quality'},
    'png': {'ext': '.png', 'quality_param': '-quality'},
    'webp': {'ext': '.webp', 'quality_param': '-quality'},
    'bmp': {'ext': '.bmp', 'quality_param': None}
}

AUDIO_FORMATS = {
    'mp3': {'codec': 'libmp3lame', 'ext': '.mp3'},
    'flac': {'codec': 'flac', 'ext': '.flac'},
    'wav': {'codec': 'pcm_s16le', 'ext': '.wav'},
    'ogg': {'codec': 'libvorbis', 'ext': '.ogg'}
}

class Settings:
    """Einstellungen speichern/laden"""
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = os.path.expanduser("~/.config/guideos-mediaconverter.ini")
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
    
    def get_last_format(self, media_type):
        try:
            return self.config.get(media_type, 'last_format')
        except:
            return None
    
    def set_last_format(self, media_type, format):
        if not self.config.has_section(media_type):
            self.config.add_section(media_type)
        self.config.set(media_type, 'last_format', format)
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_last_quality(self, media_type):
        try:
            return self.config.get(media_type, 'last_quality')
        except:
            return None
    
    def set_last_quality(self, media_type, quality):
        if not self.config.has_section(media_type):
            self.config.add_section(media_type)
        self.config.set(media_type, 'last_quality', str(quality))
        with open(self.config_file, 'w') as f:
            self.config.write(f)

class MediaConverter(Adw.Application):
    """Hauptanwendung des Medienkonverters"""
    
    def __init__(self):
        super().__init__(application_id='com.guideos.mediaconverter')
        Notify.init("GuideOS Media Konverter")
        self.settings = Settings()
        
    def do_activate(self):
        """Wird aufgerufen, wenn die Anwendung gestartet wird"""
        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_title("GuideOS Media Konverter")
        self.window.set_default_size(500, 250)
        
        # Hauptinhalt
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)
        
        # Willkommenstext
        welcome_label = Gtk.Label()
        welcome_label.set_markup("<big><b>GuideOS Medienkonverter</b></big>\nWählen Sie einen Konvertierungstyp")
        welcome_label.set_justify(Gtk.Justification.CENTER)
        
        # Buttons für die drei Konvertierungstypen
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        button_box.set_homogeneous(True)
        
        # Video Button
        video_btn = Gtk.Button()
        video_icon = Gtk.Image.new_from_icon_name("video-x-generic")
        video_btn.set_child(video_icon)
        video_btn.set_size_request(80, 80)
        video_btn.connect("clicked", self.on_video_clicked)
        video_btn.set_tooltip_text("Video-Dateien konvertieren (MP4, AVI, MKV, MOV)")
        video_label = Gtk.Label(label="Video")
        
        video_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        video_box.append(video_btn)
        video_box.append(video_label)
        
        # Bild Button
        image_btn = Gtk.Button()
        image_icon = Gtk.Image.new_from_icon_name("image-x-generic")
        image_btn.set_child(image_icon)
        image_btn.set_size_request(80, 80)
        image_btn.connect("clicked", self.on_image_clicked)
        image_btn.set_tooltip_text("Bild-Dateien konvertieren (JPG, PNG, WEBP, BMP)")
        image_label = Gtk.Label(label="Bild")
        
        image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        image_box.append(image_btn)
        image_box.append(image_label)
        
        # Audio Button
        audio_btn = Gtk.Button()
        audio_icon = Gtk.Image.new_from_icon_name("audio-x-generic")
        audio_btn.set_child(audio_icon)
        audio_btn.set_size_request(80, 80)
        audio_btn.connect("clicked", self.on_audio_clicked)
        audio_btn.set_tooltip_text("Audio-Dateien konvertieren (MP3, FLAC, WAV, OGG)")
        audio_label = Gtk.Label(label="Audio")
        
        audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        audio_box.append(audio_btn)
        audio_box.append(audio_label)
        
        button_box.append(video_box)
        button_box.append(image_box)
        button_box.append(audio_box)
        
        # Beenden Button
        exit_btn = Gtk.Button(label="Beenden")
        exit_btn.add_css_class("destructive-action")
        exit_btn.connect("clicked", self.on_exit)
        exit_btn.set_tooltip_text("Programm beenden")
        
        main_box.append(welcome_label)
        main_box.append(button_box)
        main_box.append(exit_btn)
        
        self.window.set_content(main_box)
        self.window.present()
    
    def on_video_clicked(self, button):
        dialog = VideoConverterDialog(self.window, self.settings)
        dialog.present()
    
    def on_image_clicked(self, button):
        dialog = ImageConverterDialog(self.window, self.settings)
        dialog.present()
    
    def on_audio_clicked(self, button):
        dialog = AudioConverterDialog(self.window, self.settings)
        dialog.present()
    
    def on_exit(self, button):
        self.quit()

class BaseConverterDialog(Adw.Window):
    """Basisklasse für Konverter-Dialoge"""
    
    def __init__(self, parent, settings, title, file_filter, formats):
        super().__init__(transient_for=parent)
        self.set_title(title)
        self.set_default_size(500, 650)
        self.set_modal(True)
        self.parent = parent
        self.settings = settings
        self.file_filter = file_filter
        self.formats = formats
        self.media_type = title.lower().split()[0]
        self.input_files = []
        self.current_file_index = 0
        self.output_format = None
        self.conversion_thread = None
        self.stop_conversion = False
        self.current_process = None
        self.total_duration = 0
        self.current_time_ms = 0
        self.current_alert_dialog = None
        
        # Hauptinhalt
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_box.set_margin_top(15)
        self.main_box.set_margin_bottom(15)
        self.main_box.set_margin_start(15)
        self.main_box.set_margin_end(15)
        
        # Drag & Drop Bereich - mit korrekter Zentrierung
        drag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        drag_box.set_size_request(-1, 80)
        drag_box.add_css_class("card")
        drag_box.set_halign(Gtk.Align.FILL)
        
        # Zentrierter Container für den Text
        drag_center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        drag_center_box.set_halign(Gtk.Align.CENTER)
        drag_center_box.set_valign(Gtk.Align.CENTER)
        drag_center_box.set_hexpand(True)
        drag_center_box.set_vexpand(True)
        
        drag_label = Gtk.Label()
        drag_label.set_markup("<span foreground='gray' size='large'>📁 Dateien hierher ziehen</span>")
        drag_center_box.append(drag_label)
        drag_box.append(drag_center_box)
        
        # Drag & Drop einrichten
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_drag_drop)
        drag_box.add_controller(drop_target)
        
        self.main_box.append(drag_box)
        
        # Batch-Info Label
        self.batch_label = Gtk.Label()
        self.batch_label.set_visible(False)
        self.batch_label.add_css_class("dim-label")
        self.main_box.append(self.batch_label)
        
        # Dateiauswahl
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.file_label = Gtk.Label(label="Keine Datei ausgewählt")
        self.file_label.set_xalign(0)
        self.file_label.set_hexpand(True)
        self.file_label.set_ellipsize(Pango.EllipsizeMode.END)
        
        file_btn = Gtk.Button(label="Datei(en) auswählen")
        file_btn.set_tooltip_text("Eine oder mehrere Dateien zum Konvertieren auswählen")
        file_btn.connect("clicked", self.select_files)
        
        file_box.append(self.file_label)
        file_box.append(file_btn)
        
        self.main_box.append(file_box)
        
        # Info-Label für Dateigröße
        self.info_label = Gtk.Label()
        self.info_label.set_visible(False)
        self.info_label.add_css_class("dim-label")
        self.main_box.append(self.info_label)
        
        # Thumbnail Bereich - zentriert (für alle Medientypen)
        self.thumbnail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.thumbnail_box.set_visible(False)
        self.thumbnail_box.set_halign(Gtk.Align.CENTER)
        
        self.thumbnail_frame = Gtk.Frame()
        self.thumbnail_frame.set_size_request(400, -1)
        self.thumbnail_frame.add_css_class("card")
        
        self.thumbnail_image = Gtk.Picture.new()
        self.thumbnail_image.set_size_request(400, -1)
        self.thumbnail_frame.set_child(self.thumbnail_image)
        
        self.thumbnail_box.append(self.thumbnail_frame)
        self.main_box.append(self.thumbnail_box)
        
        # Formatauswahl
        format_label = Gtk.Label(label="Zielformat:", halign=Gtk.Align.START)
        self.format_combo = Gtk.DropDown.new_from_strings(list(formats.keys()))
        self.format_combo.set_tooltip_text("Wählen Sie das Ausgabeformat")
        
        self.main_box.append(format_label)
        self.main_box.append(self.format_combo)
        
        # Qualitätsauswahl
        self.add_quality_selector()
        
        # Button Box für Konvertieren, Abbrechen und Zurück
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_homogeneous(True)
        
        # Konvertierungsbutton
        self.convert_btn = Gtk.Button(label="Konvertieren")
        self.convert_btn.add_css_class("suggested-action")
        self.convert_btn.set_sensitive(False)
        self.convert_btn.set_tooltip_text("Konvertierung starten (Enter)")
        self.convert_btn.connect("clicked", self.start_conversion)
        
        # Abbrechen Button
        self.cancel_btn = Gtk.Button(label="Abbrechen")
        self.cancel_btn.add_css_class("destructive-action")
        self.cancel_btn.set_sensitive(False)
        self.cancel_btn.set_tooltip_text("Konvertierung abbrechen")
        self.cancel_btn.connect("clicked", self.cancel_conversion)
        
        # Zurück Button
        self.back_btn = Gtk.Button(label="Zurück")
        self.back_btn.set_tooltip_text("Zum Hauptmenü zurück (ESC)")
        self.back_btn.connect("clicked", self.go_back)
        
        button_box.append(self.convert_btn)
        button_box.append(self.cancel_btn)
        button_box.append(self.back_btn)
        self.main_box.append(button_box)
        
        # Fortschrittsbalken
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.set_size_request(-1, 25)
        self.main_box.append(self.progress_bar)
        
        # Prozent Label
        self.percent_label = Gtk.Label()
        self.percent_label.set_visible(False)
        self.percent_label.add_css_class("dim-label")
        self.main_box.append(self.percent_label)
        
        # Status Label
        self.status_label = Gtk.Label(label="")
        self.status_label.set_visible(False)
        self.main_box.append(self.status_label)
        
        # Tastenkürzel
        ctrl = Gtk.EventControllerKey.new()
        ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(ctrl)
        
        self.set_content(self.main_box)
        
        # Letzte Einstellungen laden
        self.load_last_settings()
    
    def on_drag_drop(self, drop_target, value, x, y, user_data=None):
        """Drag & Drop Handler"""
        files = value.get_files()
        if files:
            self.input_files = []
            for file in files:
                path = file.get_path()
                if path:
                    self.input_files.append(path)
            
            if self.input_files:
                self.update_file_list_display()
                self.convert_btn.set_sensitive(True)
                self.update_file_info(self.input_files[0])
                self.show_thumbnail(self.input_files[0])
        return True
    
    def update_file_list_display(self):
        """Aktualisiert die Anzeige der Dateiliste"""
        if len(self.input_files) == 1:
            short_name = os.path.basename(self.input_files[0])
            if len(short_name) > 40:
                short_name = short_name[:37] + "..."
            self.file_label.set_text(short_name)
            self.batch_label.set_visible(False)
        else:
            self.file_label.set_text(f"{len(self.input_files)} Dateien ausgewählt")
            self.batch_label.set_text(f"📦 Batch-Konvertierung: {len(self.input_files)} Dateien")
            self.batch_label.set_visible(True)
    
    def update_file_info(self, file_path):
        """Dateigröße und Info anzeigen"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            if self.media_type == "video":
                duration = self.get_video_duration(file_path)
                if duration > 0:
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    self.info_label.set_text(f"📁 {size_str}  ⏱️ {minutes}:{seconds:02d} min")
                else:
                    self.info_label.set_text(f"📁 {size_str}")
            else:
                self.info_label.set_text(f"📁 {size_str}")
            
            self.info_label.set_visible(True)
        except:
            self.info_label.set_visible(False)
    
    def get_video_duration(self, file_path):
        """Videodauer in Sekunden ermitteln"""
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                   '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return float(result.stdout.strip())
        except:
            return 0
    
    def show_thumbnail(self, file_path):
        """Thumbnail für alle Medientypen anzeigen"""
        thumbnail_path = f"/tmp/thumbnail_{self.media_type}_{os.getpid()}_{abs(hash(file_path))}.jpg"
        
        if self.media_type == "video":
            # Video Thumbnail
            cmd = ['ffmpeg', '-i', file_path, '-ss', '00:00:01', '-vframes', '1', 
                   '-vf', 'scale=400:-1', thumbnail_path, '-y']
        elif self.media_type == "image":
            # Bild Thumbnail
            cmd = ['convert', file_path, '-resize', '400x', thumbnail_path]
        else:  # audio
            # Für Audio: Erstelle ein einfaches Wellenform-Thumbnail
            # Verwende ffmpeg um ein Spektrum-Bild zu erstellen
            cmd = ['ffmpeg', '-i', file_path, '-filter_complex', 
                   'showwavespic=s=400x200', '-frames:v', '1', thumbnail_path, '-y']
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if os.path.exists(thumbnail_path) and os.path.getsize(thumbnail_path) > 0:
                self.thumbnail_image.set_filename(thumbnail_path)
                self.thumbnail_box.set_visible(True)
            else:
                # Fallback: Zeige Standard-Icon basierend auf Medientyp
                self.show_default_thumbnail()
        except Exception as e:
            print(f"Thumbnail Fehler: {e}")
            self.show_default_thumbnail()
    
    def show_default_thumbnail(self):
        """Zeigt ein Standard-Thumbnail basierend auf dem Medientyp"""
        # Erstelle ein einfaches Platzhalter-Bild
        placeholder_path = f"/tmp/placeholder_{self.media_type}.png"
        
        if self.media_type == "video":
            icon_name = "video-x-generic"
        elif self.media_type == "image":
            icon_name = "image-x-generic"
        else:
            icon_name = "audio-x-generic"
        
        # Versuche ein Theme-Icon zu laden
        theme = Gtk.IconTheme.get_for_display(self.get_display())
        try:
            icon = theme.lookup_icon(icon_name, None, 200, 1, 
                                    Gtk.TextDirection.NONE, 0)
            if icon:
                self.thumbnail_image.set_paintable(icon)
                self.thumbnail_box.set_visible(True)
                return
        except:
            pass
        
        self.thumbnail_box.set_visible(False)
    
    def select_files(self, button):
        """Mehrere Dateien auswählen"""
        dialog = Gtk.FileChooserNative(
            title="Datei(en) auswählen",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
            select_multiple=True
        )
        
        gtk_filter = Gtk.FileFilter()
        gtk_filter.set_name("Unterstützte Dateien")
        for pattern in self.file_filter:
            gtk_filter.add_pattern(pattern)
        dialog.add_filter(gtk_filter)
        
        def on_response(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                files = dialog.get_files()
                self.input_files = []
                for file in files:
                    path = file.get_path()
                    if path:
                        self.input_files.append(path)
                
                if self.input_files:
                    self.update_file_list_display()
                    self.convert_btn.set_sensitive(True)
                    self.update_file_info(self.input_files[0])
                    self.show_thumbnail(self.input_files[0])
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.show()
    
    def save_file_dialog(self, default_name, callback):
        """Speichern-Dialog"""
        dialog = Gtk.FileChooserNative(
            title="Speichern unter",
            transient_for=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.set_current_name(default_name)
        
        def on_response(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                file = dialog.get_file()
                if file:
                    callback(file.get_path())
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.show()
    
    def add_quality_selector(self):
        pass
    
    def load_last_settings(self):
        last_format = self.settings.get_last_format(self.media_type)
        if last_format and last_format in self.formats:
            format_list = list(self.formats.keys())
            if last_format in format_list:
                self.format_combo.set_selected(format_list.index(last_format))
    
    def save_settings(self):
        format_index = self.format_combo.get_selected()
        format_list = list(self.formats.keys())
        if format_index < len(format_list):
            self.settings.set_last_format(self.media_type, format_list[format_index])
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.go_back(None)
            return True
        elif keyval == Gdk.KEY_Return and self.convert_btn.get_sensitive():
            self.start_conversion(None)
            return True
        return False
    
    def go_back(self, button):
        if self.input_files and not self.stop_conversion:
            dialog = Adw.AlertDialog.new(
                "Wirklich zurück?",
                f"Möchten Sie wirklich zum Hauptmenü zurückkehren? Die ausgewählten Dateien ({len(self.input_files)}) werden nicht konvertiert."
            )
            dialog.add_response("cancel", "Abbrechen")
            dialog.add_response("back", "Zurück")
            dialog.set_response_appearance("back", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            
            def on_response(dialog, response):
                if response == "back":
                    self.close()
                dialog.hide()
            
            dialog.connect("response", on_response)
            dialog.present(self)
        else:
            self.close()
    
    def start_conversion(self, button):
        if not self.input_files:
            return
        
        self.save_settings()
        self.current_file_index = 0
        self.start_next_conversion()
    
    def start_next_conversion(self):
        if self.current_file_index >= len(self.input_files):
            self.show_message("Erfolg", f"✅ Alle {len(self.input_files)} Dateien erfolgreich konvertiert!", False)
            self.reset_ui()
            return
        
        input_file = self.input_files[self.current_file_index]
        self.status_label.set_text(f"📄 Datei {self.current_file_index + 1} von {len(self.input_files)}: {os.path.basename(input_file)}")
        
        format_index = self.format_combo.get_selected()
        format_list = list(self.formats.keys())
        self.output_format = format_list[format_index] if format_index < len(format_list) else format_list[0]
        
        base_name = Path(input_file).stem
        default_name = f"{base_name}_converted.{self.output_format}"
        
        self.save_file_dialog(default_name, self.start_conversion_thread)
    
    def start_conversion_thread(self, output_file):
        self.convert_btn.set_sensitive(False)
        self.cancel_btn.set_sensitive(True)
        self.back_btn.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.percent_label.set_visible(True)
        self.status_label.set_visible(True)
        self.progress_bar.set_fraction(0)
        self.percent_label.set_text("0%")
        
        input_file = self.input_files[self.current_file_index]
        
        if self.media_type == "video":
            self.total_duration = self.get_video_duration(input_file)
            print(f"Video-Dauer: {self.total_duration} Sekunden")
        
        self.conversion_thread = threading.Thread(target=self.convert_file_thread, 
                                                 args=(input_file, output_file))
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
        
        # Starte Timer für regelmäßige Fortschrittsaktualisierung
        self.start_progress_timer()
    
    def start_progress_timer(self):
        def update_timer():
            if self.current_process and self.current_process.poll() is None:
                if hasattr(self, 'current_time_ms') and self.total_duration > 0:
                    progress = min(self.current_time_ms / (self.total_duration * 1000000), 0.99)
                    percent = int(progress * 100)
                    GLib.idle_add(self.update_progress, progress, f"🎬 Konvertiere... {percent}%")
                    GLib.idle_add(self.percent_label.set_text, f"{percent}%")
                GLib.timeout_add(500, update_timer)
            else:
                self.progress_update_timer = None
        
        GLib.timeout_add(500, update_timer)
    
    def parse_ffmpeg_output(self, line):
        if 'out_time_ms' in line:
            try:
                time_str = line.split('=')[1].strip()
                self.current_time_ms = int(time_str)
                return True
            except:
                pass
        elif 'time=' in line:
            try:
                time_match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
                if time_match:
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    seconds = float(time_match.group(3))
                    self.current_time_ms = (hours * 3600 + minutes * 60 + seconds) * 1000000
                    return True
            except:
                pass
        return False
    
    def convert_file_thread(self, input_file, output_file):
        try:
            cmd = self.get_conversion_command(input_file, output_file)
            
            self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                                    text=True, bufsize=1, universal_newlines=True)
            
            self.current_time_ms = 0
            
            for line in self.current_process.stderr:
                if self.stop_conversion:
                    self.current_process.terminate()
                    break
                self.parse_ffmpeg_output(line)
            
            if self.media_type == "image":
                for i in range(10, 100, 10):
                    if self.stop_conversion:
                        break
                    progress = i / 100
                    GLib.idle_add(self.update_progress, progress, f"🖼️ Konvertiere... {i}%")
                    GLib.idle_add(self.percent_label.set_text, f"{i}%")
                    time.sleep(0.2)
            
            self.current_process.wait()
            return_code = self.current_process.returncode
            
            if not self.stop_conversion and return_code == 0:
                GLib.idle_add(self.update_progress, 1.0, "✅ Fertig!")
                GLib.idle_add(self.percent_label.set_text, "100%")
                time.sleep(0.5)
                self.current_file_index += 1
                GLib.idle_add(self.start_next_conversion)
            elif not self.stop_conversion:
                GLib.idle_add(self.show_message, "Fehler", 
                            f"❌ Konvertierung fehlgeschlagen: {os.path.basename(input_file)}", True)
                GLib.idle_add(self.reset_ui)
            else:
                GLib.idle_add(self.reset_ui)
                
        except Exception as e:
            if not self.stop_conversion:
                GLib.idle_add(self.show_message, "Fehler", f"❌ Fehler: {str(e)}", True)
                GLib.idle_add(self.reset_ui)
    
    def get_conversion_command(self, input_file, output_file):
        raise NotImplementedError
    
    def cancel_conversion(self, button):
        self.stop_conversion = True
        if self.current_process:
            self.current_process.terminate()
        self.status_label.set_text("⏹️ Konvertierung wird abgebrochen...")
        self.cancel_btn.set_sensitive(False)
    
    def send_notification(self, title, message, success=True):
        notification = Notify.Notification.new(title, message)
        if success:
            notification.set_urgency(Notify.Urgency.NORMAL)
        else:
            notification.set_urgency(Notify.Urgency.CRITICAL)
        notification.show()
    
    def show_message(self, title, message, is_error=False):
        dialog = Adw.AlertDialog.new(title, message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        
        if is_error:
            self.send_notification(title, message, success=False)
        else:
            self.send_notification(title, message, success=True)
        
        def on_response(dialog, response):
            dialog.hide()
        
        dialog.connect("response", on_response)
        dialog.present(self)
    
    def update_progress(self, value, status_text=""):
        self.progress_bar.set_fraction(value)
        if status_text:
            self.status_label.set_text(status_text)
    
    def reset_ui(self):
        self.convert_btn.set_sensitive(True)
        self.cancel_btn.set_sensitive(False)
        self.back_btn.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.percent_label.set_visible(False)
        self.status_label.set_visible(False)
        self.stop_conversion = False
        self.current_process = None
        self.current_file_index = 0
        self.total_duration = 0
        self.current_time_ms = 0
        self.close()

class VideoConverterDialog(BaseConverterDialog):
    def __init__(self, parent, settings):
        super().__init__(parent, settings, "Video konvertieren", 
                        ["*.mp4", "*.avi", "*.mkv", "*.mov", "*.webm"],
                        VIDEO_FORMATS)
        self.media_type = "video"
    
    def add_quality_selector(self):
        quality_label = Gtk.Label(label="Auflösung:", halign=Gtk.Align.START)
        self.quality_combo = Gtk.DropDown.new_from_strings([
            "Original", "4K (3840x2160)", "2K (2560x1440)", 
            "1080p (1920x1080)", "720p (1280x720)", "480p (854x480)"
        ])
        self.quality_combo.set_tooltip_text("Video-Auflösung auswählen")
        
        last_quality = self.settings.get_last_quality("video")
        if last_quality:
            try:
                self.quality_combo.set_selected(int(last_quality))
            except:
                pass
        
        self.main_box.append(quality_label)
        self.main_box.append(self.quality_combo)
    
    def save_settings(self):
        super().save_settings()
        self.settings.set_last_quality("video", self.quality_combo.get_selected())
    
    def get_conversion_command(self, input_file, output_file):
        quality_index = self.quality_combo.get_selected()
        qualities = ["", "3840x2160", "2560x1440", "1920x1080", "1280x720", "854x480"]
        resolution = qualities[quality_index]
        
        cmd = ['ffmpeg', '-i', input_file, '-y']
        if resolution:
            height = resolution.split("x")[1]
            cmd.extend(['-vf', f'scale=-2:{height}'])
        cmd.append(output_file)
        return cmd

class ImageConverterDialog(BaseConverterDialog):
    def __init__(self, parent, settings):
        super().__init__(parent, settings, "Bild konvertieren",
                        ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"],
                        IMAGE_FORMATS)
        self.media_type = "image"
    
    def add_quality_selector(self):
        quality_label = Gtk.Label(label="Qualität:", halign=Gtk.Align.START)
        self.quality_combo = Gtk.DropDown.new_from_strings([
            "Original", "Hohe Qualität (90%)", "Mittlere Qualität (75%)", 
            "Niedrige Qualität (50%)"
        ])
        self.quality_combo.set_tooltip_text("Bildqualität auswählen")
        
        last_quality = self.settings.get_last_quality("image")
        if last_quality:
            try:
                self.quality_combo.set_selected(int(last_quality))
            except:
                pass
        
        self.main_box.append(quality_label)
        self.main_box.append(self.quality_combo)
    
    def save_settings(self):
        super().save_settings()
        self.settings.set_last_quality("image", self.quality_combo.get_selected())
    
    def get_conversion_command(self, input_file, output_file):
        quality_index = self.quality_combo.get_selected()
        qualities = [100, 90, 75, 50]
        quality = qualities[quality_index]
        
        cmd = ['convert', input_file]
        if quality < 100 and self.output_format != 'png':
            cmd.extend(['-quality', str(quality)])
        cmd.append(output_file)
        return cmd

class AudioConverterDialog(BaseConverterDialog):
    def __init__(self, parent, settings):
        super().__init__(parent, settings, "Audio konvertieren",
                        ["*.mp3", "*.flac", "*.wav", "*.ogg", "*.m4a"],
                        AUDIO_FORMATS)
        self.media_type = "audio"
    
    def add_quality_selector(self):
        quality_label = Gtk.Label(label="Bitrate:", halign=Gtk.Align.START)
        self.quality_combo = Gtk.DropDown.new_from_strings([
            "320k (Hohe Qualität)", "256k (Gute Qualität)", 
            "192k (Mittlere Qualität)", "128k (Niedrige Qualität)"
        ])
        self.quality_combo.set_tooltip_text("Audio-Bitrate auswählen")
        
        last_quality = self.settings.get_last_quality("audio")
        if last_quality:
            try:
                self.quality_combo.set_selected(int(last_quality))
            except:
                pass
        
        self.main_box.append(quality_label)
        self.main_box.append(self.quality_combo)
    
    def save_settings(self):
        super().save_settings()
        self.settings.set_last_quality("audio", self.quality_combo.get_selected())
    
    def get_conversion_command(self, input_file, output_file):
        quality_index = self.quality_combo.get_selected()
        bitrates = ["320k", "256k", "192k", "128k"]
        bitrate = bitrates[quality_index]
        
        return ['ffmpeg', '-i', input_file, '-b:a', bitrate, '-y', output_file]

def main():
    app = MediaConverter()
    app.run()

if __name__ == "__main__":
    main()
