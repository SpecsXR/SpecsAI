import re

class PostureMapper:
    """
    Maps natural language action descriptions to Live2D parameters and expressions.
    This acts as the translation layer between 'Roleplay' and 'Cubism SDK'.
    """

    # Standard Cubism Parameters
    PARAMS = {
        "AngleX": "ParamAngleX",
        "AngleY": "ParamAngleY",
        "AngleZ": "ParamAngleZ",
        "EyeLOpen": "ParamEyeLOpen",
        "EyeROpen": "ParamEyeROpen",
        "EyeBallX": "ParamEyeBallX",
        "EyeBallY": "ParamEyeBallY",
        "BrowLY": "ParamBrowLY",
        "BrowRY": "ParamBrowRY",
        "MouthForm": "ParamMouthForm",
        "BodyAngleX": "ParamBodyAngleX"
    }

    def __init__(self):
        # Define rules: (Regex Pattern, Result Dictionary)
        # Result Dictionary can contain:
        # - params: dict of Live2D parameter values
        # - expression: string name of expression to set
        # - motion: string name of motion group to trigger
        self.rules = [
            # --- Directional Looks ---
            (r"look.*?down", {
                "params": {self.PARAMS["AngleY"]: -30.0, self.PARAMS["EyeBallY"]: -0.8, self.PARAMS["BodyAngleX"]: -5.0},
                "priority": 10
            }),
            (r"look.*?up", {
                "params": {self.PARAMS["AngleY"]: 20.0, self.PARAMS["EyeBallY"]: 0.8, self.PARAMS["BodyAngleX"]: 5.0},
                "priority": 10
            }),
            (r"look.*?left", {
                "params": {self.PARAMS["AngleX"]: -25.0, self.PARAMS["EyeBallX"]: -0.8, self.PARAMS["BodyAngleX"]: -10.0},
                "priority": 10
            }),
            (r"look.*?right", {
                "params": {self.PARAMS["AngleX"]: 25.0, self.PARAMS["EyeBallX"]: 0.8, self.PARAMS["BodyAngleX"]: 10.0},
                "priority": 10
            }),
             (r"look.*?away", {
                "params": {self.PARAMS["AngleX"]: 30.0, self.PARAMS["AngleY"]: -10.0, self.PARAMS["EyeBallX"]: 0.8},
                "priority": 10
            }),

            # --- Emotions ---
            (r"sad|cry|tear|upset|sorry|apolog|trouble|difficult|fail|bad|hurt|pain|lonely|alone|miss", {
                "expression": "Sad",
                "params": {self.PARAMS["AngleZ"]: -5.0}, # Tilt head slightly
                "priority": 20
            }),
            (r"happy|smile|laugh|joy|glad|good|great|awesome|love|like|enjoy|fun|exciting|cool|wow", {
                "expression": "Happy",
                "params": {self.PARAMS["AngleZ"]: 2.0},
                "priority": 20
            }),
            (r"angry|mad|hate|furious|stupid|idiot|annoy|irritat", {
                "expression": "Angry",
                "priority": 20
            }),
            (r"surprise|shock|gasp|omg|wow|unexpected|sudden", {
                "expression": "Surprised", # Assuming mapping exists, otherwise generic
                "params": {self.PARAMS["EyeLOpen"]: 1.5, self.PARAMS["EyeROpen"]: 1.5},
                "priority": 20
            }),
            (r"think|ponder|wonder|hmm|idea|maybe|guess", {
                "expression": "Thinking", # Or neutral
                "params": {self.PARAMS["AngleZ"]: 8.0, self.PARAMS["EyeBallX"]: -0.4, self.PARAMS["EyeBallY"]: 0.4},
                "priority": 15
            }),
            (r"shy|blush|embarrass|cute|sweet|flatter|thank", {
                "expression": "Shy", # If available
                "params": {self.PARAMS["AngleY"]: -15.0, self.PARAMS["AngleX"]: -5.0},
                "priority": 15
            }),

            # --- Specific Actions ---
            (r"sigh", {
                "expression": "Sad",
                "params": {self.PARAMS["AngleY"]: -20.0, self.PARAMS["EyeLOpen"]: 0.8, self.PARAMS["EyeROpen"]: 0.8},
                "motion": "sigh", # Custom trigger if available
                "priority": 15
            }),
             (r"nod|agree|yes|okay|sure|fine|correct|right", {
                "motion": "tap", # Reusing tap motion as a nod/shake for now or we can procedural animate later
                "params": {self.PARAMS["AngleY"]: -10.0},
                "priority": 15
            }),
            (r"shake|deny|no|disagree|wrong|false|never|not", {
                "expression": "Sad", # Often associated with negative
                "params": {self.PARAMS["AngleZ"]: 0.0, self.PARAMS["AngleX"]: -10.0}, # Slight shake start
                "motion": "shake",
                "priority": 15
            }),
            (r"wave|hello|hi|greet|bye|hey", {
                "motion": "wave",
                "priority": 15
            }),
             (r"tilt|curious|confused|what|question|ask", {
                "expression": "Thinking",
                "params": {self.PARAMS["AngleZ"]: 15.0},
                "priority": 15
            }),
        ]

    def map_action(self, action_text):
        """
        Matches an action string against rules and returns the combined posture command.
        """
        action_text = action_text.lower()
        best_match = None
        highest_priority = 0

        for pattern, result in self.rules:
            if re.search(pattern, action_text):
                if result.get("priority", 0) > highest_priority:
                    best_match = result
                    highest_priority = result.get("priority", 0)
        
        # Add default duration if match found
        if best_match:
            # Copy to avoid mutating the rule definition
            result = best_match.copy()
            if "duration" not in result:
                result["duration"] = 3.0 # Default duration for any action
            return result
            
        return None

    def map_content(self, text):
        """
        Analyzes full text content for sentiment/posture if no explicit action tags exist.
        """
        return self.map_action(text) # Reuse logic for now
