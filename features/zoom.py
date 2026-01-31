"""
ফিচার: মাউস হুইল দিয়ে zoom in/out।
"""


def handle_wheel(widget, event):
    delta = event.angleDelta().y()
    if delta == 0:
        return
    step = 0.1 if delta > 0 else -0.1
    widget.set_scale(widget.get_scale() + step)
