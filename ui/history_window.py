from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QComboBox, QLabel, QHeaderView,
    QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from core.services.history_service import HistoryService

class HistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activity & Chat History")
        self.resize(700, 500)
        self.history_service = HistoryService()
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3b3b3b;
                color: #ffffff;
                gridline-color: #555;
                border: none;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0063b1;
            }
            QComboBox {
                background-color: #3b3b3b;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        
        # Top Bar
        top_layout = QHBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Events", "Chat Only", "System Events"])
        self.filter_combo.currentIndexChanged.connect(self.load_history)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_history)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("background-color: #d93025;")
        clear_btn.clicked.connect(self.clear_history)
        
        top_layout.addWidget(QLabel("Filter:"))
        top_layout.addWidget(self.filter_combo)
        top_layout.addStretch()
        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(clear_btn)
        
        self.layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Time", "Type/Sender", "Details/Message"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.layout.addWidget(self.table)
        
        self.load_history()

    def load_history(self):
        filter_idx = self.filter_combo.currentIndex()
        filter_type = None
        if filter_idx == 1:
            filter_type = "chat"
        elif filter_idx == 2:
            filter_type = "event"
            
        data = self.history_service.get_history(limit=200, filter_type=filter_type)
        
        self.table.setRowCount(0)
        
        for entry in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Time
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("timestamp", "")))
            
            # Type/Sender
            if entry.get("type") == "chat":
                sender = entry.get("sender", "Unknown")
                item = QTableWidgetItem(f"💬 {sender}")
                if sender == "You":
                    item.setForeground(QColor("#0084FF"))
                else:
                    item.setForeground(QColor("#00d775")) # Greenish for AI
                self.table.setItem(row, 1, item)
                
                # Message
                self.table.setItem(row, 2, QTableWidgetItem(entry.get("message", "")))
                
            else:
                # Event
                cat = entry.get("category", "Info")
                source = entry.get("source", "System")
                item = QTableWidgetItem(f"⚙️ {cat}")
                item.setForeground(QColor("#aaaaaa"))
                self.table.setItem(row, 1, item)
                
                # Detail
                detail = f"[{source}] {entry.get('detail', '')}"
                self.table.setItem(row, 2, QTableWidgetItem(detail))

    def clear_history(self):
        self.history_service.clear_history()
        self.load_history()
