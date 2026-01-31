import random
import os
from .resource_manager import Live2DResourceManager
from .behavior_system import Live2DBehaviorSystem

class Live2DController:
    """
    Central Controller for Live2D logic.
    Decouples logic from the rendering widget.
    """
    def __init__(self, widget):
        self.widget = widget
        self.resource_manager = Live2DResourceManager()
        self.behavior_system = Live2DBehaviorSystem(self.resource_manager)
        self.current_model_dir = None
        self.is_processing_interaction = False

    def load_model(self, model_path):
        """Called when a new model is loaded."""
        self.current_model_dir = os.path.dirname(model_path)
        print(f"[Live2DController] Scanning resources in: {self.current_model_dir}")
        self.resource_manager.load_resources(self.current_model_dir)
        
        # Auto-configure behaviors based on what we found
        self.behavior_system.scan_behaviors()
        self.behavior_map = self.behavior_system.behavior_map # For backward compat if needed

    def get_diagnostics(self):
        """Returns a health report of the current model."""
        caps = self.resource_manager.capabilities
        status = "Healthy" if not caps["generated_json"] else "Auto-Generated (Basic)"
        return f"Status: {status} | Physics: {caps['physics']} | Motions: {len(self.resource_manager.motions)}"

    def process_action(self, action_tag):
        """
        Main entry point for "Intelligent" control from Chat/AI.
        action_tag: e.g. "looks happy", "waves", "surprised"
        """
        print(f"[Live2DController] Processing Action: {action_tag}")
        
        type, content = self.behavior_system.get_action_for_tag(action_tag)
        
        if type == "motion":
            self.trigger_motion_file(content)
        elif type == "expression":
            self.set_expression_file(content)
        else:
            print(f"[Live2DController] Action '{action_tag}' not handled.")

    def set_expression(self, emotion_name):
        """Legacy/Manual override for setting emotion."""
        path = self.resource_manager.find_expression(emotion_name)
        if path:
            self.set_expression_file(path)
        else:
            print(f"[Live2DController] Warning: Expression '{emotion_name}' not found.")

    def trigger_motion(self, motion_name):
        """Legacy/Manual override for triggering motion."""
        paths = self.resource_manager.find_motion(motion_name)
        if paths:
            if isinstance(paths, list):
                path = random.choice(paths)
            else:
                path = paths
            self.trigger_motion_file(path)
        else:
             print(f"[Live2DController] Warning: Motion '{motion_name}' not found.")

    def on_tap(self, x, y):
        """Handle tap interaction."""
        # x, y are -1 to 1
        
        type, content = self.behavior_system.process_tap(x, y)
        
        if type == "motion":
             self.trigger_motion_file(content)
        elif type == "expression":
             self.set_expression_file(content)

    # --- Internal Helpers to communicate with Widget ---
    def set_expression_file(self, path):
        # Path is relative to model dir, widget might need full path or name
        # The widget currently expects just the name if loaded via JSON,
        # but for our new system we might need to be careful.
        # Let's pass the full path if the widget supports loading from file.
        full_path = os.path.join(self.current_model_dir, path)
        # However, Live2D standard wrapper usually loads expressions defined in JSON by NAME.
        # If we want to support any file, we might need a custom loader in the widget.
        # For now, let's assume the widget can handle it or we pass the name.
        
        self.widget.set_expression_file(path)

    def trigger_motion_file(self, path):
        # Path is relative
        full_path = os.path.join(self.current_model_dir, path)
        
        # Try to find if this file belongs to a known Group
        group_info = self.resource_manager.find_motion_group(path)
        if group_info:
            group, index = group_info
            print(f"[Live2DController] Playing via Group: {group} [{index}]")
            self.widget.start_motion(group, index, 3)
        else:
            # Fallback: Try to play by file path directly (if supported) or just by name
            print(f"[Live2DController] File not in JSON groups: {path}. Attempting direct load.")
            self.widget.start_motion_file(path)
