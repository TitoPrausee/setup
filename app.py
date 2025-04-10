import sys
import os
import requests
from requests.auth import HTTPBasicAuth
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import matplotlib.dates as mdates
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDateEdit, QPushButton, QProgressBar, QDialog, QTreeWidget, QTreeWidgetItem, QMessageBox, QLineEdit, QTabWidget, QListWidget
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QDate, Qt
import mplcursors  

# Ausgabe der verfügbaren Matplotlib-Stile
print(plt.style.available)

# Worker-Klasse für die Verarbeitung von Hintergrundaufgaben, wie das Herunterladen von Daten
class Worker(QObject):
    finished = pyqtSignal(str)  # Signal, das gesendet wird, wenn die Aufgabe abgeschlossen ist
    error = pyqtSignal(str)     # Signal, das gesendet wird, wenn ein Fehler auftritt

    def __init__(self, username, password):
        super().__init__()
        self.username = username  # Benutzername für die Authentifizierung
        self.password = password  # Passwort für die Authentifizierung

    def run(self):
        try:
            # Daten herunterladen und den Dateipfad senden, wenn erfolgreich
            file_path = self.download_data(self.username, self.password)
            if file_path:
                self.finished.emit(file_path)  # Signal senden, dass der Download abgeschlossen ist
            else:
                self.error.emit('Fehler beim Herunterladen der Datei')  # Fehlerfall
        except Exception as e:
            self.error.emit(str(e))  # Fehlerbehandlung

    def download_data(self, username, password):
        # URL und Verzeichnis für den Download der Datei festlegen
        url = 'https://pgb-app-01.rz.uni-jena.de/data/18311100.txt'
        download_dir = os.path.join(os.path.dirname(__file__), 'data')  # Verzeichnis für die heruntergeladene Datei
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)  # Verzeichnis erstellen, falls es nicht existiert
        file_path = os.path.join(download_dir, '18311100.txt')  # Vollständiger Pfad zur Datei
        
        try:
            # HTTP-Anfrage mit Basis-Authentifizierung durchführen
            response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=10)
            response.raise_for_status()  # Überprüfen, ob die Anfrage erfolgreich war
            # Heruntergeladene Inhalte in einer Datei speichern
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path  # Rückgabe des Dateipfads
        except requests.RequestException as e:
            print(f'Fehler beim Herunterladen der Datei: {e}')  # Fehlerausgabe
            return None  # Rückgabe None im Fehlerfall

# Hauptanwendungsfenster
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Datenvisualisierung")  # Fenstertitel setzen
        self.setGeometry(100, 100, 1200, 800)       # Fenstergröße und -position festlegen
        self.initUI()  # Benutzeroberfläche initialisieren

    def initUI(self):
        # Hauptlayout und Widgets einrichten
        self.central_widget = QWidget()  # Zentrales Widget erstellen
        self.setCentralWidget(self.central_widget)  # Zentrales Widget setzen
        self.layout = QVBoxLayout(self.central_widget)  # Hauptvertikales Layout

        # QTabWidget für die Organisation von Tabs erstellen
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)  # Tab-Widget zum Layout hinzufügen

        # Platzhalter-Tab für die Visualisierung hinzufügen
        self.visualization_tab = QWidget()
        self.visualization_layout = QVBoxLayout(self.visualization_tab)  # Vertikales Layout für Graph und Liste
        self.tab_widget.addTab(self.visualization_tab, "Visualisierung")  # Tab hinzufügen

        # Platzhalter-Tab für die Datenübersicht hinzufügen
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)  # Vertikales Layout für die Datenübersicht
        self.tab_widget.addTab(self.data_tab, "Datenübersicht")  # Tab hinzufügen

        # Horizontales Layout für Fortschritt und Datumsbereichsauswahl hinzufügen
        self.controls_layout = QHBoxLayout()
        self .layout.addLayout(self.controls_layout)  # Layout für Steuerungselemente hinzufügen

        # Fortschrittslabel und Fortschrittsbalken hinzufügen
        self.progress_layout = QVBoxLayout()
        self.controls_layout.addLayout(self.progress_layout)

        self.progress_label = QLabel("Bereit")  # Label für den Fortschritt
        self.progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()  # Fortschrittsbalken erstellen
        self.progress_layout.addWidget(self.progress_bar)

        # Datumsbereichsauswahl hinzufügen
        self.date_range_layout = QVBoxLayout()
        self.controls_layout.addLayout(self.date_range_layout)

        self.start_date_label = QLabel("Startdatum:")  # Label für das Startdatum
        self.date_range_layout.addWidget(self.start_date_label)
        self.start_date_entry = QDateEdit()  # Eingabefeld für das Startdatum
        self.start_date_entry.setCalendarPopup(True)  # Kalender-Popup aktivieren
        self.start_date_entry.setDate(QDate.currentDate().addMonths(-1))  # Standard auf einen Monat zurück
        self.date_range_layout.addWidget(self.start_date_entry)

        self.end_date_label = QLabel("Enddatum:")  # Label für das Enddatum
        self.date_range_layout.addWidget(self.end_date_label)
        self.end_date_entry = QDateEdit()  # Eingabefeld für das Enddatum
        self.end_date_entry.setCalendarPopup(True)  # Kalender-Popup aktivieren
        self.end_date_entry.setDate(QDate.currentDate())  # Standard auf heute
        self.date_range_layout.addWidget(self.end_date_entry)

        # Button zum Starten der Visualisierung hinzufügen
        self.visualize_button = QPushButton("Visualisierung starten")  # Button erstellen
        self.visualize_button.clicked.connect(self.load_and_visualize)  # Verbindung zur Funktion herstellen
        self.date_range_layout.addWidget(self.visualize_button)

        # Horizontales Layout für den Visualisierungs-Tab hinzufügen
        self.visualization_split_layout = QHBoxLayout()
        self.visualization_layout.addLayout(self.visualization_split_layout)

        # QListWidget für das Scrollen durch Tage hinzufügen
        self.day_list = QListWidget()  # Liste erstellen
        self.day_list.setMaximumWidth(200)  # Breite der Liste begrenzen
        self.day_list.itemSelectionChanged.connect(self.update_highlighted_points)  # Verbindung zur Funktion herstellen
        self.visualization_split_layout.addWidget(self.day_list)

        # Platzhalter für den Graphen (wird dynamisch hinzugefügt)
        self.graph_placeholder = QLabel("Graph wird hier angezeigt")  # Platzhalter-Label erstellen
        self.graph_placeholder.setAlignment(Qt.AlignCenter)  # Zentrierte Ausrichtung
        self.visualization_split_layout.addWidget(self.graph_placeholder)

        # Legende oder Anweisungen am unteren linken Rand hinzufügen
        self.legend_label = QLabel(
            "Anleitung:\n"
            "- Wähle ein Start- und Enddatum aus.\n"
            "- Klicke auf 'Visualisierung starten', um den Graphen zu laden.\n"
            "- Wähle einen Tag aus der Liste, um Punkte hervorzuheben.\n"
            "- Hovere über Punkte, um Details anzuzeigen."
        )
        self.legend_label.setStyleSheet("font-size: 10px; color: gray;")  # Stil der Legende festlegen
        self.legend_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)  # Ausrichtung
        self.layout.addWidget(self.legend_label)  # Legende zum Layout hinzufügen

        # Benutzer nach Anmeldedaten fragen
        self.ask_credentials()

    def ask_credentials(self):
        # Dialog zur Eingabe von Benutzername und Passwort
        self.credentials_dialog = QDialog(self)  # Dialog erstellen
        self.credentials_dialog.setWindowTitle("Anmeldung")  # Titel des Dialogs setzen
        self.credentials_dialog.setGeometry(100, 100, 300, 200)  # Größe und Position festlegen
        self.credentials_layout = QVBoxLayout(self.credentials_dialog)  # Layout für den Dialog erstellen

        # Eingabefeld für den Benutzernamen
        self.username_label = QLabel("Benutzername:")  # Label für den Benutzernamen
        self.credentials_layout.addWidget(self.username_label)
        self.username_entry = QLineEdit()  # Eingabefeld für den Benutzernamen
        self.credentials_layout.addWidget(self.username_entry)

        # Eingabefeld für das Passwort
        self.password_label = QLabel("Passwort:")  # Label für das Passwort
        self.credentials_layout.addWidget(self.password_label)
        self.password_entry = QLineEdit()  # Eingabefeld für das Passwort
        self.password_entry.setEchoMode(QLineEdit.Password)  # Passwortfeld aktivieren
        self.credentials_layout.addWidget(self.password_entry)

        # Button zum Einreichen der Anmeldedaten
        self.submit_button = QPushButton("Einreichen")  # Button erstellen
        self.submit_button.clicked.connect(self.submit_credentials)  # Verbindung zur Funktion herstellen
        self.credentials_layout.addWidget(self.submit_button)

        self.credentials_dialog.exec_()  # Dialog anzeigen und auf Eingabe warten

    def submit_credentials(self):
        # Eingabewerte für Anmeldedaten abrufen
        self.username = self.username_entry.text()  # Benutzername speichern
        self.password = self.password_entry.text()  # Passwort speichern
        self.credentials_dialog.accept()  # Dialog schließen
        if self.username and self.password:
            # Download-Prozess starten
            self.progress_label.setText("Download läuft...")  # Fortschrittslabel aktualisieren
            self.progress_bar.setRange(0, 0)  # Fortschrittsbalken auf unbestimmt setzen
            self.worker = Worker(self.username, self.password)  # Worker-Instanz erstellen
            self.worker_thread = QThread()  # Neuen Thread für den Worker erstellen
            self.worker.moveToThread(self.worker_thread)  # Worker in den Thread verschieben
            self.worker.finished.connect(self.on_download_finished)  # Verbindung zur Funktion herstellen
            self.worker.error.connect(self.on_download_error)  # Verbindung zur Fehlerbehandlungsfunktion herstellen
            self.worker_thread.started.connect(self.worker.run)  # Start des Workers im Thread
            self.worker_thread.start()  # Thread starten

    def on_download_finished(self, file_path):
        # Erfolgreiches Herunterladen behandeln
        self.worker_thread.quit()  # Thread beenden
        self.worker_thread.wait()  # Auf das Ende des Threads warten
        self.progress_bar.setRange(0, 1)  # Fortschrittsbalken auf abgeschlossen setzen
        self.progress_label.setText(f'Download abgeschlossen: {file_path}')  # Erfolgreiche Meldung
        try:
            # Heruntergeladene Daten laden und verarbeiten
            df = pd.read_csv(file_path, sep='|')  # CSV-Datei einlesen
            df['time_from'] = pd.to_datetime(df['time_from'], errors='coerce')  # Zeitstempel konvertieren
            min_date = df['time_from'].min().strftime('%Y-%m-%d')  # Minimales Datum ermitteln
            max_date = df['time_from'].max().strftime('%Y-%m-%d')  # Maximales Datum ermitteln
            self.show_time_range_popup(min_date, max_date)  # Popup mit Zeitbereich anzeigen
        except Exception as e:
            self.progress_label.setText(f'Fehler beim Laden der Daten: {e}')  # Fehlerbehandlung
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Daten: {e}")  # Fehlermeldung anzeigen

    def on_download_error(self, error_message):
        # Fehler beim Herunterladen behandeln
        self.worker_thread.quit()  # Thread beenden
        self.worker_thread.wait()  # Auf das Ende des Threads warten
        self.progress_bar.setRange(0, 1)  # Fortschrittsbalken auf abgeschlossen setzen
        self.progress_label.setText(error_message)  # Fehlernachricht anzeigen
        QMessageBox.critical(self, "Fehler", error_message)  # Fehlermeldung anzeigen

    def show_time_range_popup(self, min_date, max_date):
        # Popup mit dem verfügbaren Zeitbereich anzeigen
        self.popup = QDialog(self)  # Popup-Dialog erstellen
        self.popup.setWindowTitle("Verfügbarer Zeitraum")  # Titel setzen
        self.popup.setGeometry(100, 100, 300, 100)  # Größe und Position festlegen
        self.popup_layout = QVBoxLayout(self.popup)  # Layout für den Popup-Dialog erstellen
        self.popup_label = QLabel(f"Verfügbarer Zeitraum: {min_date} bis {max_date}")  # Label mit Zeitbereich
        self.popup_layout.addWidget(self.popup_label)  # Label zum Layout hinzufügen
        self.ok_button = QPushButton("OK")  # Bestätigungsbutton erstellen
        self.ok_button.clicked.connect(self.popup.accept)  # Verbindung zur Schließfunktion herstellen
        self.popup_layout.addWidget(self.ok_button)  # Button zum Layout hinzufügen
        self.popup.exec_()  # Popup anzeigen

    def load_and_visualize(self):
        # Visualisierungsprozess starten
        start_date = self.start_date_entry.date().toString("yyyy-MM-dd")  # Startdatum abrufen
        end_date = self.end_date_entry.date().toString("yyyy-MM-dd")  # Enddatum abrufen
        self.progress_label.setText("Daten werden geladen und visualisiert")  # Fortschrittslabel aktual self.progress_bar.setRange(0, 0)  # Fortschrittsbalken auf unbestimmt setzen
        self.visualize_thread = QThread()  # Neuen Thread für die Visualisierung erstellen
        self.visualize_worker = VisualizeWorker(start_date, end_date)  # Worker für die Visualisierung erstellen
        self.visualize_worker.moveToThread(self.visualize_thread)  # Worker in den Thread verschieben
        self.visualize_worker.finished.connect(self.on_visualization_finished)  # Verbindung zur Funktion herstellen
        self.visualize_worker.error.connect(self.on_visualization_error)  # Verbindung zur Fehlerbehandlungsfunktion herstellen
        self.visualize_thread.started.connect(self.visualize_worker.run)  # Start des Workers im Thread
        self.visualize_thread.start()  # Thread starten

    def on_visualization_finished(self, df_filtered, start_date, end_date):
        # Erfolgreiche Visualisierung behandeln
        self.visualize_thread.quit()  # Thread beenden
        self.visualize_thread.wait()  # Auf das Ende des Threads warten
        self.progress_bar.setRange(0, 1)  # Fortschrittsbalken auf abgeschlossen setzen
        self.progress_label.setText("Visualisierung abgeschlossen")  # Erfolgreiche Meldung
        try:
            self.df_filtered = df_filtered  # Gefilterte Daten für spätere Verwendung speichern
            self.show_visualization(df_filtered, start_date, end_date)  # Visualisierung anzeigen
            self.show_data_window(df_filtered)  # Datenfenster anzeigen
        except Exception as e:
            self.progress_label.setText(f'Fehler bei der Visualisierung: {e}')  # Fehlerbehandlung
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Visualisierung: {e}")  # Fehlermeldung anzeigen

    def on_visualization_error(self, error_message):
        # Fehler bei der Visualisierung behandeln
        self.visualize_thread.quit()  # Thread beenden
        self.visualize_thread.wait()  # Auf das Ende des Threads warten
        self.progress_bar.setRange(0, 1)  # Fortschrittsbalken auf abgeschlossen setzen
        self.progress_label.setText(error_message)  # Fehlernachricht anzeigen
        QMessageBox.critical(self, "Fehler", error_message)  # Fehlermeldung anzeigen

    def show_visualization(self, df_filtered, start_date, end_date):
        # Vorherige Visualisierung entfernen
        if hasattr(self, 'canvas'):
            self.visualization_split_layout.removeWidget(self.canvas)  # Canvas entfernen
            self.canvas.deleteLater()  # Canvas löschen
            del self.canvas  # Referenz löschen

        # Platzhalter entfernen, falls vorhanden
        if hasattr(self, 'graph_placeholder'):
            self.visualization_split_layout.removeWidget(self.graph_placeholder)  # Platzhalter entfernen
            self.graph_placeholder.deleteLater()  # Platzhalter löschen
            del self.graph_placeholder  # Referenz löschen

        # Überprüfen, ob die Daten gültig sind
        if df_filtered.empty:
            QMessageBox.warning(self, "Warnung", "Keine Daten für den ausgewählten Zeitraum verfügbar.")  # Warnung anzeigen
            return

        if not pd.api.types.is_numeric_dtype(df_filtered['ac_measurements_active_percent']):
            QMessageBox.critical(self, "Fehler", "Die Spalte 'ac_measurements_active_percent' enthält ungültige Werte.")  # Fehler anzeigen
            return

        # Fortfahren mit der Visualisierung
        plt.style.use('ggplot')  # Stil für die Visualisierung festlegen
        self.fig, self.ax = plt.subplots(figsize=(14, 7))  # Figur und Achsen erstellen
        self.ax.plot(df_filtered['time_from'], df_filtered['ac_measurements_active_percent'], color='dodgerblue', linewidth=2, label='AC Measurements Active Percent')  # Daten plotten
        self.ax.fill_between(df_filtered['time_from'], df_filtered['ac_measurements_active_percent'], color='dodgerblue', alpha=0.2)  # Bereich unter dem Graphen füllen
        self.ax.set_xlabel(f'Time From ({start_date} to {end_date})', fontsize=12)  # X-Achsenbeschriftung
        self.ax.set_ylabel('Percent', fontsize=12)  # Y-Achsenbeschriftung
        self.ax.set_title('AC Measurements Active Percent Over Time', fontsize=16, fontweight='bold')  # Titel setzen
        self.ax.set_ylim(0, 100)  # Y-Achsenbereich festlegen
        self.ax.set_yticks(range(0, 101, 10))  # Y-Achsen-Ticks festlegen
        self.ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, alpha=0.7) # Dynamische Anpassung der X-Achsen-Ticks basierend auf der Anzahl der Einträge
        num_entries = len(df_filtered)
        if num_entries > 20:
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Automatische Datums-Ticks für viele Einträge
        else:
            self.ax.xaxis.set_major_locator(mdates.DayLocator())  # Tägliche Ticks für weniger Einträge
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Datumsformat für die X-Achse
        self.fig.autofmt_xdate(rotation=45)  # X-Achsen-Beschriftungen rotieren

        self.ax.legend(fontsize=12, loc='upper left', frameon=True, shadow=True, borderpad=1)  # Legende hinzufügen

        # Visualisierung zum Visualisierungs-Tab hinzufügen
        self.canvas = FigureCanvas(self.fig)  # Canvas für die Visualisierung erstellen
        self.visualization_split_layout.addWidget(self.canvas)  # Canvas zum Layout hinzufügen

        # Liste mit den Tagen füllen
        self.day_list.clear()  # Liste leeren
        for date in df_filtered['time_from'].dt.strftime('%Y-%m-%d').unique():
            self.day_list.addItem(date)  # Einträge zur Liste hinzufügen

    def show_data_window(self, df_filtered):
        # Daten im Daten-Tab anzeigen
        self.tree = QTreeWidget()  # Baum-Widget für die Daten erstellen
        self.tree.setColumnCount(2)  # Anzahl der Spalten festlegen
        self.tree.setHeaderLabels(["Datum", "AC Measurements Active Percent"])  # Spaltenüberschriften setzen
        for index, row in df_filtered.iterrows():
            item = QTreeWidgetItem([row['time_from'].strftime('%Y-%m-%d %H:%M:%S'), f"{row['ac_measurements_active_percent']}%"])  # Datenzeile erstellen
            item.setData(0, 1, row['time_from'])  # Zeitstempel speichern
            item.setData(1, 1, row['ac_measurements_active_percent'])  # Messwert speichern
            self.tree.addTopLevelItem(item)  # Zeile zum Baum hinzufügen
        self.tree.itemSelectionChanged.connect(lambda: self.highlight_selected_data(df_filtered))  # Verbindung zur Funktion herstellen
        self.data_layout.addWidget(self.tree)  # Baum zum Layout hinzufügen

        # Button zum Kopieren der Daten hinzufügen
        self.copy_button = QPushButton("Daten kopieren")  # Button erstellen
        self.copy_button.clicked.connect(lambda: self.copy_to_clipboard(df_filtered))  # Verbindung zur Kopierfunktion herstellen
        self.data_layout.addWidget(self.copy_button)  # Button zum Layout hinzufügen

    def highlight_selected_data(self, df_filtered):
        # Ausgewählte Datenpunkte im Graphen hervorheben
        selected_items = self.tree.selectedItems()  # Ausgewählte Elemente abrufen
        if not selected_items:
            return  # Keine Auswahl, nichts tun

        # Vorherige Hervorhebungen entfernen
        for collection in self.ax.collections[:]:
            collection.remove()  # Alle vorherigen Highlights entfernen

        # Entferne nur die Scatter-Highlights, nicht den Hauptgraphen
        if self.ax.lines and len(self.ax.lines) > 1:  # Sicherstellen, dass der Hauptgraph nicht entfernt wird
            self.ax.lines[-1].remove()  # Vorherige Scatter-Highlights entfernen

        # Ausgewählte Datenpunkte extrahieren
        selected_times = [item.data(0, 1) for item in selected_items]  # Zeitstempel der ausgewählten Elemente
        selected_values = [item.data(1, 1) for item in selected_items]  # Messwerte der ausgewählten Elemente

        # Sicherstellen, dass die ausgewählten Punkte mit den Graphdaten übereinstimmen
        selected_points = df_filtered[df_filtered['time_from'].isin(selected_times)]  # Gefilterte Datenpunkte

        # Ausgewählte Punkte hervorheben
        self.ax.scatter(
            selected_points['time_from'],
            selected_points['ac_measurements_active_percent'],
            color='red',
            s=50,
            label='Selected Points',
            zorder=5
        )
        self.ax.legend(fontsize=12, loc='upper left', frameon=True, shadow=True, borderpad=1)  # Legende aktualisieren
        self.canvas.draw()  # Canvas neu zeichnen

    def copy_to_clipboard(self, df_filtered):
        # Daten in die Zwischenablage kopieren
        data = ""  # Initialisierung der Daten
        for row in df_filtered.itertuples():
            data += f"{row.time_from.strftime('%Y-%m-%d %H:%M:%S')} : {row.ac_measurements_active_percent}%\n"  # Formatierte Datenzeile hinzufügen
        clipboard = QApplication.clipboard()  # Zwischenablage abrufen
        clipboard.setText(data)  # Daten in die Zwischenablage setzen
        QMessageBox.information(self, "Information", "Daten wurden in die Zwischenablage kopiert")  # Bestätigung anzeigen

    def update_highlighted_points(self):
        selected_items = self.day_list.selectedItems()  # Ausgewählte Tage abrufen
        if not selected_items:
            return  # Keine Auswahl, nichts tun

        # Ausgewählte Tage extrahieren
        selected_dates = [item.text() for item in selected_items]  # Text der ausgewählten Elemente

        # Daten basierend auf den ausgewählten Tagen filtern
        selected_points = self.df_filtered[self.df_filtered['time_from'].dt.strftime('%Y-%m-%d').isin(selected_dates)]

        # Vorherige Highlights entfernen
        for collection in self.ax.collections[:]:
            collection.remove()  # Alle vorherigen Highlights entfernen

        # Rote Punkte anzeigen
        scatter = self.ax.scatter(
            selected_points['time_from'],
            selected_points['ac_measurements_active_percent'],
            color='red',
            s=50,
            label='Selected Points',
            zorder=5
        )
        self.ax.legend(fontsize=12, loc='upper left', frameon=True, shadow=True, borderpad=1)  # Legende aktualisieren

        # Interaktive Tooltips hinzufügen
        cursor = mplcursors.cursor(scatter, hover=True)  # Cursor für interaktive Tooltips aktivieren
        @cursor.connect("add")
        def on_add(sel):
            # Zeit und Prozentwert in der Infoblase anzeigen
            index = sel.index
            time = selected_points.iloc[index]['time_from']
            percent = selected_points.iloc[index]['ac_measurements_active_percent']
            sel.annotation.set_text(f"Zeit: {time}\nWert: {percent}%")  # Tooltip-Text setzen
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)  # Hintergrund der Infoblase anpassen

        self.canvas.draw()  # Canvas neu zeichnen

# Worker-Klasse für das Filtern und Vorbereiten von Daten für die Visualisierung
class VisualizeWorker(QObject):
    finished = pyqtSignal(pd.DataFrame, str, str)  # Signal, das gesendet wird, wenn die Aufgabe abgeschlossen ist
    error = pyqtSignal(str)  # Signal, das gesendet wird, wenn ein Fehler auftritt

    def __init__(self, start_date, end_date):
        super().__init__()
        self.start_date = start_date  # Startdatum speichern
        self.end_date = end_date  # Enddatum speichern

    def run(self):
        try:
            # Daten basierend auf dem Datumsbereich laden und filtern
            file_path = os.path.join(os.path.dirname(__file__), 'data', '18311100.txt')  # Pfad zur Datei
            df = pd.read_csv(file_path, sep='|')  # CSV-Datei einlesen
            
            # 'time_from' in ein Datetime-Format konvertieren und ungültige Werte entfernen
            df['time_from'] = pd.to_datetime(df['time_from'], errors='coerce')  # Zeitstempel konvertieren
            df = df.dropna(subset=['time_from'])  # Zeilen mit ungültigen Datumswerten entfernen
            
            # 'ac_measurements_active_percent' bereinigen und konvertieren
            df['ac_measurements_active_percent'] = (
                df['ac_measurements_active_percent']
                .str.replace(',', '.', regex=False)  # Kommas durch Punkte ersetzen
                .astype(float)  # In Float konvertieren
            )
            df = df.dropna(subset=['ac_measurements_active_percent'])  # Ungültige Werte entfernen
            
            # Daten basierend auf dem Datum filtern
            df_filtered = df[(df['time_from'] >= self.start_date) & (df['time_from'] <= self.end_date)]
            
            self.finished.emit(df_filtered, self.start_date, self.end_date)  # Gefilterte Daten senden
        except Exception as e:
            self.error.emit(str(e))  # Fehler senden

# Beispiel-Worker zur Demonstration von Hintergrundaufgaben
class ExampleWorker(QObject):
    finished = pyqtSignal()  # Signal, das gesendet wird, wenn die Aufgabe abgeschlossen ist

    def run(self):
        import time
        time.sleep(3)  # Simuliere eine lang laufende Aufgabe
        self.finished.emit()  # Signal senden, dass die Aufgabe abgeschlossen ist

# Einstiegspunkt der Anwendung
if __name__ == "__main__":
    app = QApplication(sys.argv)  # QApplication erstellen
    main_window = MainWindow()  # Hauptfenster erstellen
    main_window.show()  # Hauptfenster anzeigen
    sys.exit(app.exec_())  # Anwendung ausführen und auf Beendigung warten