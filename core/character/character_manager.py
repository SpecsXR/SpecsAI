import os
from PySide6.QtGui import QPixmap, QMovie

class CharacterManager:
    """
    Manages character assets and states.
    Separates logic from UI.
    """
    def __init__(self, assets_root="assets/character/interactive"):
        self.assets_root = assets_root
        self.current_char = "default"
        self.states = {} # Cache for loaded assets
        
    def load_character(self, char_name):
        self.current_char = char_name
        char_path = os.path.join(self.assets_root, char_name)
        
        # Load states (idle.png, talking.gif, etc.)
        # This is a placeholder for asset loading logic
        pass

    def get_asset(self, state):
        # Return path or QPixmap/QMovie for the state
        return None
