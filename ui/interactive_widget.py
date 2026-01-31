from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal, QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QMovie
import threading
import os
import sys

# Try imports, use dummy if failed
try:
    import cv2 # type: ignore
    import numpy as np # type: ignore
    import mediapipe as mp # type: ignore
    HAS_CV = True
except ImportError:
    HAS_CV = False
    cv2 = None
    np = None
    mp = None
    print("Warning: OpenCV/MediaPipe not found. Webcam tracking disabled.")

class InteractiveWidget(QWidget):
    """
    New Interactive Character Widget.
    - Uses static images/GIFs for motion (lighter than Live2D).
    - Uses MediaPipe for Webcam Gesture Tracking (if enabled).
    - Supports Screen Interactions (Click-through).
    """
    
    gesture_detected = Signal(str) # e.g., "wave", "thumbs_up"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window Flags: Frameless, Always on Top, Tool, Transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False) # Enable mouse initially
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Character Display (Label)
        self.char_label = QLabel()
        self.char_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.char_label)
        
        # State Management
        self.current_state = "idle" # idle, talking, thinking, happy
        self.assets_dir = os.path.join("assets", "character", "interactive")
        self.os_makedirs(self.assets_dir)
        
        # MediaPipe Setup (Hand Tracking)
        self.webcam_active = False
        self.cap = None
        
        if HAS_CV:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        
        # Tracking Timer
        self.track_timer = QTimer(self)
        self.track_timer.timeout.connect(self.update_tracking)
        # self.track_timer.start(50) # Enable for webcam tracking later
        
        # Default placeholder character
        self.set_placeholder_char()

    def set_webcam_tracking(self, enabled):
        self.webcam_active = enabled
        if enabled and HAS_CV:
            if not self.cap:
                self.cap = cv2.VideoCapture(0)
            self.track_timer.start(50)
        else:
            self.track_timer.stop()
            if self.cap:
                self.cap.release()
                self.cap = None

    def os_makedirs(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def set_placeholder_char(self):
        # First check if we have a default idle image
        idle_path = os.path.join(self.assets_dir, "idle.png")
        if os.path.exists(idle_path):
            self.set_state("idle")
            return

        # Create a simple colored circle as placeholder if no assets
        pixmap = QPixmap(300, 400)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(100, 200, 255, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(50, 50, 200, 300)
        
        # Eyes
        painter.setBrush(Qt.white)
        painter.drawEllipse(100, 120, 40, 40)
        painter.drawEllipse(160, 120, 40, 40)
        painter.setBrush(Qt.black)
        painter.drawEllipse(115, 130, 10, 10)
        painter.drawEllipse(175, 130, 10, 10)
        
        # Smile
        painter.setPen(QColor(0, 0, 0))
        painter.drawArc(100, 200, 100, 50, 0 * 16, -180 * 16)
        
        painter.end()
        self.char_label.setPixmap(pixmap)

    def update_tracking(self):
        """Captures webcam frame and detects gestures"""
        if not self.webcam_active: return
        
        # (Implementation for MediaPipe processing goes here)
        pass

    def set_state(self, state):
        self.current_state = state
        print(f"Character State: {state}")
        
        # Try to load GIF/Image from assets
        # Filename format: {state}.gif or {state}.png (e.g., idle.gif, talking.gif)
        extensions = [".gif", ".png"]
        found_file = None
        
        for ext in extensions:
            file_path = os.path.join(self.assets_dir, f"{state}{ext}")
            if os.path.exists(file_path):
                found_file = file_path
                break
        
        if found_file:
            if found_file.endswith(".gif"):
                movie = QMovie(found_file)
                self.char_label.setMovie(movie)
                movie.start()
            else:
                self.char_label.setPixmap(QPixmap(found_file))
        else:
            # Fallback for now if no assets
            if state == "idle":
                self.set_placeholder_char()
        
        # Simple animation effects (mimicking liveness)
        if state == "happy":
            # Bounce
            current_geo = self.geometry()
            self.setGeometry(current_geo.x(), current_geo.y() - 20, current_geo.width(), current_geo.height())
            QTimer.singleShot(200, lambda: self.setGeometry(current_geo))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            # Trigger 'Poke' reaction
            self.set_state("happy")
            QTimer.singleShot(2000, lambda: self.set_state("idle"))

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
