from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette, QFont, QPainter, QPainterPath

class TypingBubble(QFrame):
    """
    A Messenger-style typing indicator with bouncing dots.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.setFixedWidth(70)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(4)
        
        self.dots = []
        for i in range(3):
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet("background-color: #B0B3B8; border-radius: 4px;")
            self.layout.addWidget(dot)
            self.dots.append(dot)
            
        self.setStyleSheet("""
            QFrame {
                background-color: #3E4042;
                border-radius: 17px;
            }
        """)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(300)
        self.step = 0
        
    def animate(self):
        self.step = (self.step + 1) % 4
        colors = ["#FFFFFF", "#B0B3B8", "#B0B3B8"] # Highlight, Normal, Normal
        
        # Rotate the highlight
        for i in range(3):
            # 0 -> 0 highlight
            # 1 -> 1 highlight
            # 2 -> 2 highlight
            # 3 -> None highlight (pause)
            if self.step < 3 and i == self.step:
                 self.dots[i].setStyleSheet("background-color: #FFFFFF; border-radius: 4px;")
            else:
                 self.dots[i].setStyleSheet("background-color: #B0B3B8; border-radius: 4px;")

class MessageBubble(QFrame):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Message Label
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Segoe UI", 10))
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Styling
        if is_user:
            self.layout.addStretch()
            self.layout.addWidget(self.label)
            self.setStyleSheet("""
                QLabel {
                    background-color: #0084FF;
                    color: white;
                    border-radius: 15px;
                    padding: 10px 15px;
                    selection-background-color: #0056b3;
                }
            """)
        else:
            self.layout.addWidget(self.label)
            self.layout.addStretch()
            self.setStyleSheet("""
                QLabel {
                    background-color: #3E4042; 
                    color: white;
                    border-radius: 15px;
                    padding: 10px 15px;
                    selection-background-color: #5C5E60;
                }
            """)
            # Note: #3E4042 is Messenger Dark mode grey. #E4E6EB for light mode.
            # Using Dark mode style as base since app is generally dark/transparent.

        # Adjust size policy
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.label.setMaximumWidth(250) # Limit bubble width

class ChatWidget(QWidget):
    """
    A transparent, non-blocking chat widget for continuous conversation.
    Facebook Messenger style design.
    """
    message_sent = Signal(str)
    stop_clicked = Signal() # New Signal for Stop
    mic_clicked = Signal()
    vision_clicked = Signal() # New Signal for Vision

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window Flags: Frameless, Always on Top, Tool
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialize drag position
        self.old_pos = None
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # --- Header (Optional, for dragging) ---
        # self.header = QFrame()
        # self.header.setStyleSheet("background: rgba(0,0,0,0.1); border-radius: 10px;")
        # self.header_layout = QHBoxLayout(self.header)
        # self.layout.addWidget(self.header)

        # --- Chat History Area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(0,0,0,0.1);
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.2);
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        # Container for Bubbles
        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(5, 5, 5, 5)
        self.history_layout.setSpacing(10)
        self.history_layout.addStretch() # Push messages to bottom
        
        self.scroll_area.setWidget(self.history_container)
        self.layout.addWidget(self.scroll_area)

        # --- Input Area ---
        self.input_container = QFrame()
        self.input_container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 240); 
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
        """)
        self.input_layout = QHBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(10, 5, 5, 5)
        self.input_layout.setSpacing(5)

        # Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Message SpecsAI...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        self.input_layout.addWidget(self.input_field)

        # Vision Button (Eye/Camera)
        self.vision_btn = QPushButton("👁️")
        self.vision_btn.setCursor(Qt.PointingHandCursor)
        self.vision_btn.setToolTip("Specs Vision (Look at Screen)")
        self.vision_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00aaff;
                border-radius: 15px;
                width: 30px;
                height: 30px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(0, 170, 255, 0.2);
            }
        """)
        self.vision_btn.clicked.connect(self.on_vision_clicked)
        self.input_layout.addWidget(self.vision_btn)

        # Mic Button
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.setToolTip("Voice Input")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AAAAAA;
                border-radius: 15px;
                width: 30px;
                height: 30px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.mic_btn.clicked.connect(self.on_mic_clicked)
        self.input_layout.addWidget(self.mic_btn)

        # Clear Button
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setToolTip("Clear Chat UI (History Saved)")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AAAAAA;
                border-radius: 15px;
                width: 30px;
                height: 30px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                color: #FF4444;
                background-color: rgba(255, 68, 68, 0.1);
            }
        """)
        self.clear_btn.clicked.connect(self.clear_chat_ui)
        self.input_layout.addWidget(self.clear_btn)

        # Send Button
        self.send_btn = QPushButton("➤")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0084FF;
                border-radius: 15px;
                width: 30px;
                height: 30px;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(0, 132, 255, 0.1);
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_btn)

        # Stop Button (Initially Hidden)
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setVisible(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF4444;
                border-radius: 15px;
                width: 30px;
                height: 30px;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.1);
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.input_layout.addWidget(self.stop_btn)

        self.layout.addWidget(self.input_container)

        # Initial Size
        self.resize(380, 500)
        
        # Draggable logic
        self.old_pos = None
        
        # Typing Indicator
        self.typing_bubble = None

    def on_mic_clicked(self):
        self.mic_clicked.emit()

    def on_stop_clicked(self):
        self.stop_clicked.emit()

    def clear_chat_ui(self):
        """Clears the visual chat history without deleting actual history"""
        # Remove all items from history layout
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Re-add stretch to push future messages to bottom
        self.history_layout.addStretch()
        
        # Add a system note
        self.add_message("System", "Chat cleared (History preserved in memory)", is_user=False)

    def set_loading_state(self, is_loading):
        """Toggles between Send and Stop button"""
        if is_loading:
            self.send_btn.setVisible(False)
            self.stop_btn.setVisible(True)
        else:
            self.send_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.hide_typing()

    def on_vision_clicked(self):
        self.vision_clicked.emit()

    def show_typing(self):
        """Shows the typing indicator"""
        if self.typing_bubble:
            return # Already showing
            
        # Create a container for alignment (Left aligned)
        self.typing_container = QWidget()
        self.typing_container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(self.typing_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.typing_bubble = TypingBubble()
        container_layout.addWidget(self.typing_bubble)
        container_layout.addStretch() # Push to left
        
        # Insert before the stretch at the end
        # history_layout has messages + stretch. 
        # count() - 1 is the stretch.
        self.history_layout.insertWidget(self.history_layout.count() - 1, self.typing_container)
        
        # Scroll to bottom
        QTimer.singleShot(10, self._scroll_to_bottom)

    def hide_typing(self):
        """Removes the typing indicator"""
        if self.typing_bubble:
            self.typing_bubble.deleteLater()
            self.typing_bubble = None
        
        if hasattr(self, 'typing_container') and self.typing_container:
            self.typing_container.deleteLater()
            self.typing_container = None
            
    # set_mic_active is already defined below, avoiding duplicate

    def set_mic_active(self, active):
        if active:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF4444;
                    color: white;
                    border-radius: 15px;
                    width: 30px;
                    height: 30px;
                    font-size: 16px;
                    border: none;
                }
            """)
        else:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #AAAAAA;
                    border-radius: 15px;
                    width: 30px;
                    height: 30px;
                    font-size: 16px;
                    border: none;
                }
                QPushButton:hover {
                    color: white;
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Display User Message
        self.add_message("You", text, is_user=True)
        
        # Emit signal
        self.message_sent.emit(text)
        
        # Clear input
        self.input_field.clear()

    def add_message(self, sender, text, is_user=False):
        """Adds a bubble to the history"""
        bubble = MessageBubble(text, is_user)
        self.history_layout.addWidget(bubble)
        
        # Scroll to bottom
        # Need to wait for layout update or use a timer
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        super().mouseReleaseEvent(event)
        
    # Signals for MainWindow to handle
    model_changed_signal = Signal(str)
    online_toggled_signal = Signal(bool)

    def on_model_changed(self, index):
        provider_map = ["gemini", "groq", "claude", "ollama"]
        if index < len(provider_map):
            self.model_changed_signal.emit(provider_map[index])
            
    def on_online_toggled(self, checked):
        self.online_toggled_signal.emit(checked)
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
