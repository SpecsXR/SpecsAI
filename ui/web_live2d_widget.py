
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Slot, Signal, Qt
import os

from PySide6.QtWebEngineCore import QWebEngineSettings

class WebLive2DWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Transparent background settings
        self.page().setBackgroundColor(Qt.transparent)
        self.setStyleSheet("background: transparent;")
        
        # Enable Local File Access for AJAX/Fetch
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        # Enable Dev Tools for debugging (Right click -> Inspect)
        # settings.setAttribute(QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled, True)
        
        # WebChannel setup
        self.channel = QWebChannel()
        self.bridge = PythonBridge()
        self.channel.registerObject("pyBridge", self.bridge)
        self.page().setWebChannel(self.channel)
        
        # Load the viewer
        current_dir = os.path.dirname(os.path.abspath(__file__))
        viewer_path = os.path.join(os.path.dirname(current_dir), "assets", "web_viewer", "index.html")
        self.load(QUrl.fromLocalFile(viewer_path))
        
        self.bridge.log_msg.connect(self.on_js_log)
        
        self.is_loaded = False
        self.pending_model = None
        self.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, ok):
        self.is_loaded = True
        if ok:
            print("Web Viewer Loaded Successfully")
            if self.pending_model:
                self.load_model(self.pending_model)
                self.pending_model = None
        else:
            print("Failed to load Web Viewer")

    def load_model(self, model_path):
        if not self.is_loaded:
            print(f"Page not loaded yet, queuing model: {model_path}")
            self.pending_model = model_path
            return

        # Convert local path to file URL or relative path that JS can access
        # Since we loaded index.html from local file, it can access local files relative to it
        # But model_path is absolute. We need to handle this.
        # Best way: pass absolute file URL
        file_url = QUrl.fromLocalFile(model_path).toString()
        print(f"Loading model from: {file_url}")
        self.page().runJavaScript(f"loadModel('{file_url}');")

    def look_at(self, x, y):
        self.page().runJavaScript(f"lookAt({x}, {y});")

    def set_state(self, state):
        # Compatibility with InteractiveWidget
        # In future, map 'talking', 'idle' to Live2D motions
        pass

    def set_click_through(self, enabled):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

    @Slot(str)
    def on_js_log(self, msg):
        print(f"[JS Log]: {msg}")

class PythonBridge(QObject):
    log_msg = Signal(str)

    @Slot(str)
    def log(self, msg):
        self.log_msg.emit(msg)
