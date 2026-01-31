"""
ফিচার: মাউস অনুসরণ – মাথা ও চোখ মাউসের দিকে ঘোরে।
"""


def handle_mouse_move(widget, event):
    if not widget.model:
        return
    w, h = widget.width(), widget.height()
    if w <= 0 or h <= 0:
        return
    x = (event.position().x() / w - 0.5) * 2
    y = (event.position().y() / h - 0.5) * -2
    
    # Store targets instead of setting directly (to persist across updates)
    widget.target_head_x = x * 30
    widget.target_head_y = y * 30
    widget.target_eye_x = x
    widget.target_eye_y = y
    
    # Body Rotation (Leaning towards cursor for "Supportive" feel)
    # Scale down x slightly so body doesn't twist too much
    widget.target_body_x = x * 10 
    
    # Also set immediately for responsiveness (though next paintGL will overwrite then re-apply)
    # widget.model.SetParameterValue("PARAM_ANGLE_X", x * 30)
    # widget.model.SetParameterValue("PARAM_ANGLE_Y", y * 30)
    # widget.model.SetParameterValue("PARAM_EYE_BALL_X", x)
    # widget.model.SetParameterValue("PARAM_EYE_BALL_Y", y)
