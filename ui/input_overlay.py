from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QPoint, QEvent
from PySide6.QtGui import QCursor

class InputOverlay(QWidget):
    # Edge Constants (Integers to avoid Qt Enum TypeErrors)
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 4
    EDGE_BOTTOM = 8

    """
    A transparent overlay that handles all mouse interactions (Dragging, Clicking).
    This ensures that the underlying Renderer (Live2D/VRM) doesn't block input.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True) # Track mouse for cursor changes
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Window Dragging State
        self.drag_start_pos = None
        self.resize_margin = 10
        self.resizing = False
        self.resize_edge = 0
        self.moving = False
        
    def _check_edge(self, pos):
        """Determine if mouse is on a window edge for resizing"""
        rect = self.rect()
        edge = self.EDGE_NONE
        
        if pos.x() < self.resize_margin:
            edge |= self.EDGE_LEFT
        elif pos.x() > rect.width() - self.resize_margin:
            edge |= self.EDGE_RIGHT
            
        if pos.y() < self.resize_margin:
            edge |= self.EDGE_TOP
        elif pos.y() > rect.height() - self.resize_margin:
            edge |= self.EDGE_BOTTOM
            
        return edge

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            window = self.window()
            pos = event.pos()
            edge = self._check_edge(pos)
            
            # 1. Try System Resize (Best for Windows)
            if edge != 0:
                if window.windowHandle():
                    # Map internal edge flags to Qt.Edges
                    qt_edge = Qt.Edges()
                    if edge & self.EDGE_LEFT: qt_edge |= Qt.LeftEdge
                    if edge & self.EDGE_RIGHT: qt_edge |= Qt.RightEdge
                    if edge & self.EDGE_TOP: qt_edge |= Qt.TopEdge
                    if edge & self.EDGE_BOTTOM: qt_edge |= Qt.BottomEdge
                    
                    if window.windowHandle().startSystemResize(qt_edge):
                        return # Handled by system

                # Fallback to Manual Resize
                self.resizing = True
                self.resize_edge = edge
                self.drag_start_pos = event.globalPos()
                if hasattr(self.drag_start_pos, 'toPoint'):
                     self.drag_start_pos = self.drag_start_pos.toPoint()
                return

            # 2. Try System Drag (DISABLED: User reported "locking" / "snapping" issues)
            # System drag triggers Windows Snap/Aero features which might be causing the "fixed place" issue.
            # We will use Manual Drag exclusively for "Freedom".
            # if window.windowHandle():
            #    if window.windowHandle().startSystemMove():
            #        return # Handled by system
            
            # 3. Manual Drag (Primary)
            self.moving = True
            self.drag_start_pos = event.globalPos()
            if hasattr(self.drag_start_pos, 'toPoint'):
                 self.drag_start_pos = self.drag_start_pos.toPoint()
            
            event.accept() # CRITICAL: Consume event so it doesn't propagate to MainWindow/Children
            
    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.moving = False
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        window = self.window()
        
        # Handle Resizing (Manual)
        if self.resizing:
            global_pos = event.globalPos()
            if hasattr(global_pos, 'toPoint'):
                 global_pos = global_pos.toPoint()
                 
            diff = global_pos - self.drag_start_pos
            geo = window.geometry()
            new_geo = geo
            
            # Simple resize logic (can be expanded)
            # For now, just let user know resizing is active
            pass 
            
        # Handle Moving (Manual Fallback)
        if self.moving:
            global_pos = event.globalPos()
            if hasattr(global_pos, 'toPoint'):
                 global_pos = global_pos.toPoint()
            
            diff = global_pos - self.drag_start_pos
            new_pos = window.pos() + diff
            window.move(new_pos)
            self.drag_start_pos = global_pos
            return

        # Update Cursor for Edges
        edge = self._check_edge(pos)
        if edge == (self.EDGE_LEFT | self.EDGE_TOP) or edge == (self.EDGE_RIGHT | self.EDGE_BOTTOM):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == (self.EDGE_RIGHT | self.EDGE_TOP) or edge == (self.EDGE_LEFT | self.EDGE_BOTTOM):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edge & self.EDGE_LEFT or edge & self.EDGE_RIGHT:
            self.setCursor(Qt.SizeHorCursor)
        elif edge & self.EDGE_TOP or edge & self.EDGE_BOTTOM:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
    def mouseDoubleClickEvent(self, event):
        """Optional: Double click to toggle something?"""
        pass
