"""
ফিচার: উইন্ডো ড্র্যাগ – মাউস ধরে চেপে রাখলে চরিত্রটাকে মনি্টরের যেকোনো জায়গায় টেনে নিতে পারবে।
"""
from PySide6.QtCore import Qt


def handle_mouse_press(widget, event):
    if event.button() == Qt.MouseButton.LeftButton:
        widget._dragging = True
        widget._drag_start = event.globalPosition().toPoint()


def handle_mouse_release(widget, event):
    if event.button() == Qt.MouseButton.LeftButton:
        widget._dragging = False


def handle_mouse_move_drag(widget, event):
    """ড্র্যাগ করলে True, না হলে False (তখন mouse_follow চালবে)।"""
    if not getattr(widget, "_dragging", False):
        return False
    now = event.globalPosition().toPoint()
    dx = now.x() - widget._drag_start.x()
    dy = now.y() - widget._drag_start.y()
    widget._drag_start = now
    
    # If the widget supports moving the model internally (Full Screen Mode), use that.
    if hasattr(widget, "move_model"):
        widget.move_model(dx, dy)
    else:
        # Otherwise move the window itself
        win = widget.window()
        win.move(win.x() + dx, win.y() + dy)
        
    return True
