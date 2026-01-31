"""
MainWindow - Core of SpecsAI
"""
import os
import threading
import time
import pyautogui
from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QStyle, QInputDialog, QWidget, QStackedLayout
from PySide6.QtGui import QAction, QCursor, QRegion, QBitmap, QPainter, QTransform
from PySide6.QtCore import Qt, QUrl, QTimer, Signal, QEvent, QPoint, QRect
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .native_live2d_widget import NativeLive2DWidget
from .vrm_widget import VRMWidget
from .input_overlay import InputOverlay
from core.character.character_manager import CharacterManager
from core.automation.automation_manager import AutomationManager
from core.network.online_manager import OnlineManager
from core.features.feature_manager import FeatureManager
from core.services.voice_service import VoiceService
from core.services.ai_service import AIService
from core.services.stt_service import STTService
from core.services.history_service import HistoryService
from .chat_widget import ChatWidget
from core.config import Config
from core.settings.settings_manager import SettingsManager
from core.behavior.action_parser import ActionParser
from core.behavior.posture_mapper import PostureMapper
from core.services.neural_link import NeuralLinkService

import ctypes
from ctypes.wintypes import HWND, DWORD, LONG

class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", ctypes.c_int),
                ("cxRightWidth", ctypes.c_int),
                ("cyTopHeight", ctypes.c_int),
                ("cyBottomHeight", ctypes.c_int)]

class MainWindow(QMainWindow):
    # Signal to handle AI response on the main thread
    ai_response_received = Signal(str)

    def __init__(self):
        super().__init__()
        
        self.ai_response_received.connect(self.process_ai_response_ui)

        # Managers
        self.char_manager = CharacterManager()
        self.automation_manager = AutomationManager()
        self.online_manager = OnlineManager()
        self.feature_manager = FeatureManager()
        
        # Services
        self.voice_service = VoiceService()
        self.ai_service = AIService(online_manager=self.online_manager)
        self.stt_service = STTService()
        self.history_service = HistoryService()
        
        # Neural Link (Brain Connection)
        self.neural_link = NeuralLinkService()
        self.neural_link.request_speak.connect(self.handle_brain_speak)
        self.neural_link.request_expression.connect(self.handle_brain_expression)
        self.neural_link.request_move.connect(self.handle_brain_move)
        self.neural_link.start_listening()
        
        # Behavior
        self.action_parser = ActionParser()
        self.posture_mapper = PostureMapper()
        
        self.history_service.log_event("System", "SpecsAI Application Started")
        
        # STT Signals
        self.stt_service.listening_started.connect(self._on_listening_started)
        self.stt_service.listening_ended.connect(self._on_listening_ended)
        self.stt_service.text_recognized.connect(self._on_speech_recognized)
        self.stt_service.error_occurred.connect(self._on_stt_error)
        
        # Online Service
        threading.Thread(target=self._start_online_service, daemon=True).start()
        
        # Audio Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_media_error)
        
        self.voice_service.audio_playback_requested.connect(self._play_tts_audio)
        self.voice_service.speech_metadata_ready.connect(self._on_speech_metadata_ready)
        
        # Window Setup
        self.setWindowTitle("SpecsAI")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")
        
        self.enable_windows_transparency()
        
        # Layout Architecture
        self.central_container = QWidget()
        self.setCentralWidget(self.central_container)
        
        self.stack_layout = QStackedLayout(self.central_container)
        self.stack_layout.setStackingMode(QStackedLayout.StackAll)
        
        # 1. Renderer (Bottom)
        self.interactive_widget = NativeLive2DWidget(self)
        self.stack_layout.addWidget(self.interactive_widget)
        
        # 2. Input Overlay (Top)
        self.input_overlay = InputOverlay(self)
        self.stack_layout.addWidget(self.input_overlay)
        self.input_overlay.raise_()
        
        # Chat Widget
        self.chat_widget = ChatWidget(None) # Separate window
        self.chat_widget.user_input_received.connect(self.process_user_input)
        self.chat_widget.show()
        
        self.setup_tray_icon()
        
        # State
        self.stop_requested = False
        self.resize_margin = 10
        
        # Initial Size
        self.resize(400, 600)
        self.center_window()
        
        # Auto-Load
        QTimer.singleShot(1000, self.load_default_character)

    def enable_windows_transparency(self):
        """DWM Blur/Transparency for Windows"""
        try:
            hwnd = HWND(int(self.winId()))
            margins = MARGINS(-1, -1, -1, -1)
            dwm = ctypes.windll.dwmapi
            dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
        except Exception as e:
            print(f"DWM Transparency Error: {e}")

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width() - 50
        y = screen.height() - self.height() - 50
        self.move(x, y)

    def load_default_character(self):
        # Default logic
        self.switch_renderer("live2d") # Start with Live2D
        # In real implementation, check Config.CURRENT_CHARACTER_ID

    def switch_renderer(self, mode="live2d"):
        if mode == "vrm":
            if isinstance(self.interactive_widget, VRMWidget): return
            new_widget = VRMWidget(self)
            new_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        else:
            if isinstance(self.interactive_widget, NativeLive2DWidget): return
            new_widget = NativeLive2DWidget(self)
        
        # Replace in Stack
        self.stack_layout.removeWidget(self.interactive_widget)
        self.interactive_widget.deleteLater()
        self.interactive_widget = new_widget
        self.stack_layout.addWidget(self.interactive_widget)
        
        # Ensure Overlay is Top
        self.stack_layout.setCurrentWidget(self.input_overlay)
        self.input_overlay.raise_()

    # --- Event Handlers ---
    def _on_listening_started(self):
        self.chat_widget.set_recording_state(True)
    
    def _on_listening_ended(self):
        self.chat_widget.set_recording_state(False)
        
    def _on_speech_recognized(self, text):
        self.chat_widget.add_message("User", text, is_user=True)
        self.process_user_input(text)
        
    def _on_stt_error(self, error):
        print(f"STT Error: {error}")

    def process_user_input(self, text):
        if not text.strip(): return
        self.chat_widget.set_loading_state(True)
        
        # Stop previous speech
        self.voice_service.stop()
        self.player.stop()
        self.stop_requested = False
        
        threading.Thread(target=self.ai_service.generate_response, args=(text, self.on_ai_response), daemon=True).start()

    def on_ai_response(self, response_text):
        self.ai_response_received.emit(response_text)

    def process_ai_response_ui(self, response_text):
        self.chat_widget.set_loading_state(False)
        if self.stop_requested: return
        
        display_text = response_text
        tts_text = self.action_parser.remove_actions(response_text)
        
        self.history_service.log_chat("SpecsAI", display_text)
        self.voice_service.speak(tts_text, display_text=display_text)

    # --- Audio / Media ---
    def _play_tts_audio(self, file_path, display_text=None, metadata=None):
        if display_text:
            self.chat_widget.add_message("SpecsAI", display_text, is_user=False)
        
        if metadata:
            if metadata.get("expression") and hasattr(self.interactive_widget, 'set_emotion'):
                self.interactive_widget.set_emotion(metadata["expression"])
        
        if file_path:
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
            self._on_speaking_started()

    def _on_speaking_started(self):
        if hasattr(self.interactive_widget, 'set_lip_sync'):
            self.interactive_widget.set_lip_sync(True)

    def _on_speaking_finished(self):
        if hasattr(self.interactive_widget, 'set_lip_sync'):
            self.interactive_widget.set_lip_sync(False)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            QTimer.singleShot(500, self._finalize_playback)

    def _finalize_playback(self):
        self.voice_service.notify_playback_finished()
        self._on_speaking_finished()
    
    def _on_media_error(self, error):
        print(f"Media Error: {error}")
        self.voice_service.notify_playback_finished()

    # --- Tray Icon ---
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        menu = QMenu()
        menu.addAction("Show/Hide", self.on_tray_icon_activated)
        menu.addAction("Exit", QApplication.quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason=QSystemTrayIcon.Trigger):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible(): self.hide()
            else: self.show()

    def _start_online_service(self):
        # Placeholder for online service start
        pass

    # --- Neural Link Handlers (Brain Control) ---
    def handle_brain_speak(self, text):
        """Called when Brain (SOS) wants to speak"""
        print(f"[NeuralLink] Speaking: {text}")
        self.voice_service.speak(text, display_text=text)

    def handle_brain_expression(self, expression):
        """Called when Brain wants to change expression"""
        print(f"[NeuralLink] Expression: {expression}")
        if hasattr(self.interactive_widget, 'set_emotion'):
            self.interactive_widget.set_emotion(expression)

    def handle_brain_move(self, x, y):
        """Called when Brain wants to move the window"""
        print(f"[NeuralLink] Moving to: {x}, {y}")
        self.move(x, y)
