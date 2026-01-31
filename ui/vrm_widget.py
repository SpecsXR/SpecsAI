import os
import base64
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtCore import QUrl, Qt, Slot, QEvent, QPoint
from PySide6.QtGui import QColor

class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[JS Console] {message} (Line {lineNumber})")

class VRMWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Custom Page for Console Logging
        self.setPage(WebEnginePage(self))
        
        # Transparent Background Setup
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        try:
            self.page().setBackgroundColor(Qt.transparent)
        except Exception as e:
            print(f"[VRMWidget] Warning: Could not set transparent background: {e}")
        
        # Disable default context menu
        self.setContextMenuPolicy(Qt.NoContextMenu)
        
        # Install Event Filter for Native Window Dragging
        self.drag_start_pos = None
        self.installEventFilter(self)
        
        # Explicitly install on focusProxy if available (Qt WebEngine Input Handler)
        if self.focusProxy():
             self.focusProxy().installEventFilter(self)
        
        # Recursively install on all existing children
        self._install_filter_recursive(self)
        
        # Settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        
        # Load Viewer
        viewer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/vrm/viewer/index.html"))
        self.load(QUrl.fromLocalFile(viewer_path))
        
        self.is_loaded = False
        self._pending_model = None
        self.loadFinished.connect(self._on_load_finished)
        
    def _install_filter_recursive(self, widget):
        """Recursively installs event filter on a widget and its children"""
        if widget and widget != self: # Don't install on self twice (handled in init)
            widget.installEventFilter(self)
            
        for child in widget.children():
            self._install_filter_recursive(child)

    def eventFilter(self, source, event):
        """Handle child events (Only recursion) - Dragging handled by InputOverlay now"""
        
        # Dynamically install event filter on new children (critical for WebEngine)
        if event.type() == QEvent.ChildAdded:
            if hasattr(event, 'child'):
                child = event.child()
                if child:
                    self._install_filter_recursive(child)
                    if self.focusProxy() and child != self.focusProxy():
                        # Sometimes focus proxy is reset or recreated?
                        self.focusProxy().installEventFilter(self)

        # DEPRECATED: Dragging is now handled by InputOverlay
        # We return False to allow events to propagate if needed (though InputOverlay is on top)
        return super().eventFilter(source, event)
        
    def _on_load_finished(self, ok):
        if ok:
            print("[VRMWidget] Web Engine Loaded Successfully")
            self.is_loaded = True
            if self._pending_model:
                print(f"[VRMWidget] Loading pending model: {self._pending_model}")
                self.load_model(self._pending_model)
                self._pending_model = None
        else:
            print("[VRMWidget] Failed to load Web Engine")

    def load_model(self, model_path):
        """Loads a VRM model from local path safely using Base64"""
        # 1. Resolve Path
        abs_path = os.path.abspath(model_path)
        
        # Auto-fix path if not found (Search in assets/vrm/models)
        if not os.path.exists(abs_path):
            common_path = os.path.join(os.getcwd(), "assets", "vrm", "models", os.path.basename(model_path))
            if os.path.exists(common_path):
                print(f"[VRMWidget] Path corrected: {model_path} -> {common_path}")
                abs_path = common_path
        
        if not self.is_loaded:
            print("[VRMWidget] Engine not ready yet, queuing model...")
            self._pending_model = abs_path # Queue the resolved path
            return
            
        # Try loading via direct file URL first (Faster, requires --allow-file-access-from-files)
        try:
            file_url = QUrl.fromLocalFile(abs_path).toString()
            print(f"[VRMWidget] Loading model via URL: {file_url}")
            js = f"window.loadVRM('{file_url}');"
            self.page().runJavaScript(js)
        except Exception as e:
            print(f"[VRMWidget] Error loading via URL, trying Base64 fallback: {e}")
            try:
                with open(abs_path, "rb") as f:
                    data = f.read()
                    b64_data = base64.b64encode(data).decode('utf-8')
                js = f"window.loadVRMFromData('{b64_data}');"
                self.page().runJavaScript(js)
            except Exception as e2:
                print(f"[VRMWidget] Error reading model file: {e2}")


    def set_lip_sync(self, active):
        """Enables/Disables lip sync (Stub for VRM)"""
        # VRM handles lip sync via blend shapes, we might want to map audio volume to 'aa', 'ih', etc. later.
        # For now, just a stub to prevent crashes.
        self._lip_sync_active = active
        # if not active:
        #     self.set_expression("aa", 0)

    def set_click_through(self, enabled):
        """Sets click-through mode (Stub for VRM)"""
        # WebEngine handles this via window flags mostly
        pass


    def set_expression(self, name, value=1.0):
        """Sets an expression (neutral, happy, angry, etc.)"""
        if self.is_loaded:
            js = f"window.setExpression('{name}', {value});"
            self.page().runJavaScript(js)

    def set_emotion(self, emotion_name):
        """Alias for set_expression to match Live2D interface"""
        # Map common Live2D emotion names to VRM expressions if needed
        self.set_expression(emotion_name, 1.0)

            
    def load_animation(self, anim_path):
        """Loads and plays an animation file (.glb/.gltf)"""
        if not self.is_loaded: return
        
        abs_path = os.path.abspath(anim_path).replace("\\", "/")
        file_url = f"file:///{abs_path}"
        js = f"window.loadAnimation('{file_url}');"
        self.page().runJavaScript(js)

    def trigger_motion(self, motion_name):
        """Triggers a motion or expression"""
        print(f"[VRMWidget] Motion requested: {motion_name}")
        
        # 1. Check if it's an expression mapping
        expressions = ["happy", "angry", "sad", "relaxed", "surprised", "neutral", "blink", "joy", "fun"]
        
        # Map some common aliases
        aliases = {
            "smile": "happy",
            "wave": "wave.glb", 
            "dance": "dance.glb"
        }
        
        target = aliases.get(motion_name.lower(), motion_name.lower())
        
        if target in expressions:
            self.set_expression(target, 1.0)
            return

        # 2. Check for Procedural Animations (Built-in JS)
        procedural = ["nod", "shake", "jump", "yes", "no"]
        if target in procedural:
            # Map aliases
            if target == "yes": target = "nod"
            if target == "no": target = "shake"
            
            if self.is_loaded:
                js = f"window.triggerProcedural('{target}');"
                self.page().runJavaScript(js)
            return

        # 3. Check if it's an animation file
        motion_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/vrm/motions"))
        
        # Check specific file extensions
        extensions = [".glb", ".gltf"]
        for ext in extensions:
            # Try direct name
            candidate = os.path.join(motion_dir, f"{target}{ext}")
            if os.path.exists(candidate):
                self.load_animation(candidate)
                return
            
            # Try original name
            candidate = os.path.join(motion_dir, f"{motion_name}{ext}")
            if os.path.exists(candidate):
                self.load_animation(candidate)
                return
            
        print(f"[VRMWidget] Motion/Animation not found: {motion_name}")
        
    @property
    def is_speaking(self):
        return getattr(self, '_is_speaking', False)
        
    @is_speaking.setter
    def is_speaking(self, value):
        self._is_speaking = value
        # Trigger lip sync start/stop in JS if needed
        
    def set_look_at(self, x, y):
        """Sets look direction (-1 to 1)"""
        if self.is_loaded:
            js = f"window.setLookAt({x}, {y});"
            self.page().runJavaScript(js)

    def reset_camera(self):
        """Resets camera position"""
        if self.is_loaded:
            self.page().runJavaScript("window.resetCamera();")
