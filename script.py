from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QAction, QLineEdit,
    QVBoxLayout, QWidget, QDialog, QComboBox, QCheckBox, QLabel, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QMessageBox, QSystemTrayIcon, QMenu
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import sys
import json
import os

# Charger les paramètres utilisateur depuis un fichier JSON
SETTINGS_FILE = "settings.json"
FAVORITES_FILE = "favorites.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {"theme": "light", "language": "English", "permissions": {"microphone": False}, "favorites_folder": ""}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):  # Vérifie que les favoris sont un dictionnaire
                return data
    return {}  # Retourne un dictionnaire vide si le fichier est manquant ou mal formaté

def save_favorites(favorites):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)

class BrowserTab(QWebEngineView):
    def __init__(self, url=None):
        super().__init__()

        self.titleChanged.connect(self.update_tab_title)
        self.iconChanged.connect(self.update_tab_icon)
        
        if url:
            self.setUrl(QUrl(url))
        else:
            self.setUrl(QUrl("https://www.google.com"))

        self.favicon = None  # Variable pour stocker le favicon
        self.tab_title = "Nouvel Onglet"  # Titre par défaut

    def update_tab_title(self, title):
        # Met à jour le titre de l'onglet avec le titre de la page
        self.tab_title = title
        window.tabs.setTabText(window.tabs.indexOf(self), title)

    def update_tab_icon(self, icon):
        # Met à jour l'icône de l'onglet avec le favicon de la page
        self.favicon = icon
        window.tabs.setTabIcon(window.tabs.indexOf(self), icon)

    def get_favicon(self):
        # Retourne l'icône du favicon, ou une icône par défaut si elle n'est pas définie
        return self.favicon if self.favicon else QIcon("default_favicon.png")

class FavoritesManager(QDialog):
    def __init__(self, favorites):
        super().__init__()
        self.setWindowTitle("Gestion des favoris")
        self.favorites = favorites

        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Favoris")
        layout.addWidget(self.tree)

        # Boutons pour gérer les favoris
        add_folder_btn = QPushButton("Ajouter un dossier")
        add_folder_btn.clicked.connect(self.add_folder)
        layout.addWidget(add_folder_btn)

        delete_favorite_btn = QPushButton("Supprimer")
        delete_favorite_btn.clicked.connect(self.delete_favorite)
        layout.addWidget(delete_favorite_btn)

        self.load_favorites_tree()
        
    def load_favorites_tree(self):
        # Charger la structure des favoris dans l'arborescence
        self.tree.clear()
        for folder_name, urls in self.favorites.items():
            folder_item = QTreeWidgetItem([folder_name])
            for url in urls:
                url_item = QTreeWidgetItem([url])
                folder_item.addChild(url_item)
            self.tree.addTopLevelItem(folder_item)

    def add_folder(self):
        # Créer un nouveau dossier de favoris
        folder_name, ok = QInputDialog.getText(self, "Ajouter un dossier", "Nom du dossier:")
        if ok and folder_name:
            if folder_name in self.favorites:
                QMessageBox.warning(self, "Erreur", "Ce dossier existe déjà.")
            else:
                self.favorites[folder_name] = []
                save_favorites(self.favorites)
                self.load_favorites_tree()

    def delete_favorite(self):
        # Supprimer un favori ou un dossier sélectionné
        selected_item = self.tree.currentItem()
        if selected_item:
            parent = selected_item.parent()
            if parent:
                # Si l'élément sélectionné est un favori
                folder_name = parent.text(0)
                url = selected_item.text(0)
                self.favorites[folder_name].remove(url)
                if not self.favorites[folder_name]:
                    del self.favorites[folder_name]
            else:
                # Si l'élément sélectionné est un dossier
                folder_name = selected_item.text(0)
                del self.favorites[folder_name]
            save_favorites(self.favorites)
            self.load_favorites_tree()

class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Paramètres")
        self.settings = settings

        layout = QVBoxLayout(self)

        # Paramètre de thème
        self.theme_label = QLabel("Thème:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Clair", "Sombre"])
        self.theme_combo.setCurrentText("Clair" if settings.get("theme") == "light" else "Sombre")
        layout.addWidget(self.theme_label)
        layout.addWidget(self.theme_combo)

        # Autorisations (microphone)
        self.microphone_label = QLabel("Microphone:")
        self.microphone_check = QCheckBox("Autoriser l'accès au microphone")
        self.microphone_check.setChecked(settings.get("permissions", {}).get("microphone", False))
        layout.addWidget(self.microphone_label)
        layout.addWidget(self.microphone_check)

        # Paramètre de langue
        self.language_label = QLabel("Langue:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Français"])
        self.language_combo.setCurrentText(settings.get("language", "English"))
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)

        # Dossier des favoris
        self.favorites_folder_label = QLabel("Dossier de favoris:")
        self.favorites_folder_btn = QPushButton("Choisir un dossier")
        self.favorites_folder_btn.clicked.connect(self.choose_favorites_folder)
        layout.addWidget(self.favorites_folder_label)
        layout.addWidget(self.favorites_folder_btn)

        # Boutons pour enregistrer ou annuler
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)

    def choose_favorites_folder(self):
        # Choisir un dossier pour enregistrer les favoris
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier de favoris")
        if folder:
            self.settings["favorites_folder"] = folder

    def save_settings(self):
        # Sauvegarde les paramètres sélectionnés
        self.settings["theme"] = "light" if self.theme_combo.currentText() == "Clair" else "dark"
        self.settings["permissions"]["microphone"] = self.microphone_check.isChecked()
        self.settings["language"] = self.language_combo.currentText()
        save_settings(self.settings)
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.favorites = load_favorites()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)

        self.setCentralWidget(self.tabs)

        # Barre d'outils de navigation
        nav_toolbar = QToolBar("Navigation")
        self.addToolBar(nav_toolbar)

        # Boutons avec icônes pour navigation et favoris
        back_btn = QAction(QIcon("back.png"), "Précédent", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        nav_toolbar.addAction(back_btn)

        forward_btn = QAction(QIcon("forward.png"), "Suivant", self)
        forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        nav_toolbar.addAction(forward_btn)

        reload_btn = QAction(QIcon("reload.png"), "Recharger", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        nav_toolbar.addAction(reload_btn)

        self.url_bar = QLineEdit(self)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.url_bar)

        add_fav_btn = QAction(QIcon("star.png"), "Ajouter aux favoris", self)
        add_fav_btn.triggered.connect(self.add_to_favorites)
        nav_toolbar.addAction(add_fav_btn)

        manage_fav_btn = QAction(QIcon("folder.png"), "Gérer les favoris", self)
        manage_fav_btn.triggered.connect(self.open_favorites_manager)
        nav_toolbar.addAction(manage_fav_btn)

        settings_btn = QAction(QIcon("settings.png"), "Paramètres", self)
        settings_btn.triggered.connect(self.open_settings)
        nav_toolbar.addAction(settings_btn)

        # Ajouter un bouton pour ouvrir un nouvel onglet
        new_tab_btn = QAction(QIcon("new_tab.png"), "Nouveau onglet", self)
        new_tab_btn.triggered.connect(self.add_new_tab)
        nav_toolbar.addAction(new_tab_btn)

        # Créer un nouvel onglet par défaut
        self.add_new_tab()

        self.setWindowTitle("PyNav")
        self.setWindowIcon(QIcon("logo.png"))
        self.resize(1024, 768)

        # Connecter le signal de changement d'URL
        self.tabs.currentChanged.connect(self.update_url_bar)

        # Ajouter l'icône à la barre des tâches
        self.tray_icon = QSystemTrayIcon(QIcon("logo.png"), self)
        self.tray_icon.setToolTip("PyNav Browser")
        
        tray_menu = QMenu(self)
        tray_menu.addAction("Ouvrir", self.show)
        tray_menu.addAction("Quitter", QApplication.instance().quit)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.show()

    def update_url_bar(self, index):
        # Mettre à jour la barre d'adresse avec l'URL de l'onglet sélectionné
        url = self.tabs.currentWidget().url().toString()
        self.url_bar.setText(url)

    def add_new_tab(self, qurl=None):
        if qurl is None:
            qurl = QUrl("https://www.google.com")
        browser_tab = BrowserTab(qurl)
        i = self.tabs.addTab(browser_tab, browser_tab.tab_title)
        self.tabs.setCurrentIndex(i)

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def navigate_to_url(self):
        qurl = QUrl(self.url_bar.text())
        self.tabs.currentWidget().setUrl(qurl)

    def add_to_favorites(self):
        current_url = self.tabs.currentWidget().url().toString()
        folder_name, ok = QInputDialog.getText(self, "Ajouter aux favoris", "Nom du dossier:")
        if ok and folder_name:
            if folder_name not in self.favorites:
                self.favorites[folder_name] = []
            self.favorites[folder_name].append(current_url)
            save_favorites(self.favorites)

    def open_favorites_manager(self):
        dialog = FavoritesManager(self.favorites)
        dialog.exec_()
        save_favorites(self.favorites)

    def open_settings(self):
        dialog = SettingsDialog(self.settings)
        if dialog.exec_():
            self.apply_settings()

    def apply_settings(self):
        if self.settings["theme"] == "dark":
            self.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")
        else:
            self.setStyleSheet("")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
