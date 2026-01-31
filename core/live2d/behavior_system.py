import random
import os
import re

class Live2DBehaviorSystem:
    """
    INTELLIGENT BEHAVIOR SYSTEM
    ---------------------------
    This system acts as the "Brain" for the Live2D character.
    It separates logic from rendering and manages:
    1. Intelligent Action Mapping (Tags -> Motions/Expressions)
    2. Context Awareness (Mood, Interaction History)
    3. Body Part Control (Parameter Overrides)
    """
    
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.current_mood = "normal"
        self.last_action_time = 0
        
        # Standardized Behavior Map (Can be expanded dynamically)
        self.behavior_map = {}
        
        # Fuzzy keyword map for natural language understanding
        self.keyword_map = {
            "happy": ["happy", "smile", "joy", "laugh", "excited"],
            "sad": ["sad", "cry", "depressed", "sorrow", "grief"],
            "angry": ["angry", "mad", "rage", "furious", "annoyed"],
            "surprised": ["surprised", "shock", "gasp", "wow"],
            "shy": ["shy", "blush", "embarrassed"],
            "love": ["love", "heart", "kiss", "romance"],
            "wave": ["wave", "hello", "hi", "bye", "greeting"],
            "nod": ["nod", "agree", "yes", "affirmative"],
            "shake": ["shake", "no", "deny", "disagree", "reject"],
            "tap_body": ["tap_body", "poke", "touch", "interact"],
            "tap_head": ["tap_head", "pat", "pet", "head"],
            "idle": ["idle", "wait", "stand"],
        }

        # Fallback map: If primary emotion isn't found, use these available motions
        self.fallback_map = {
            "happy": ["wave", "nod"],
            "smile": ["wave"],
            "excited": ["wave", "shake"], 
            "sad": ["idle"], 
            "angry": ["shake"], 
            "surprised": ["shake"],
            "love": ["wave"],
            "shy": ["idle"],
        }
        
    def scan_behaviors(self):
        """
        Scans available resources and maps them to intelligent behaviors.
        This makes the system adaptive to ANY model.
        """
        print("[BehaviorSystem] Scanning resources for intelligent mapping...")
        
        # Clear old map
        self.behavior_map = {}
        
        # 1. Map Motions
        for key, keywords in self.keyword_map.items():
            found_motions = []
            for kw in keywords:
                # Search in resource manager
                matches = self.resource_manager.find_motion(kw)
                if matches:
                    if isinstance(matches, list):
                        found_motions.extend(matches)
                    else:
                        found_motions.append(matches)
            
            if found_motions:
                # Deduplicate
                self.behavior_map[key] = list(set(found_motions))
                
        # 2. Map Expressions (as fallback or primary for emotions)
        for key, keywords in self.keyword_map.items():
            found_exprs = []
            for kw in keywords:
                match = self.resource_manager.find_expression(kw)
                if match:
                    found_exprs.append(match)
            
            if found_exprs:
                # Store expressions separately or mix them?
                # For now, let's store them in a specific 'expression' key
                self.behavior_map[f"expr_{key}"] = list(set(found_exprs))
                
        print(f"[BehaviorSystem] Mapped {len(self.behavior_map)} behavior categories.")

    def get_action_for_tag(self, tag):
        """
        Intelligently finds the best action (Motion or Expression) for a given tag.
        Returns: (type, content)
        type: "motion" or "expression" or "parameter"
        content: file path or parameter dict
        """
        tag = tag.lower().strip()
        print(f"[BehaviorSystem] Analyzing tag: '{tag}'")
        
        # 1. Direct Match in Behavior Map
        if tag in self.behavior_map:
            return "motion", random.choice(self.behavior_map[tag])
            
        # 2. Keyword Search (Fuzzy Matching)
        best_match_key = None
        for key, keywords in self.keyword_map.items():
            for kw in keywords:
                if kw in tag:
                    best_match_key = key
                    break
            if best_match_key: break
            
        if best_match_key and best_match_key in self.behavior_map:
            return "motion", random.choice(self.behavior_map[best_match_key])
            
        # 3. Direct Resource Search (Last Resort)
        # Maybe the tag IS the file name (e.g. "special_attack")
        direct_motion = self.resource_manager.find_motion(tag)
        if direct_motion:
            if isinstance(direct_motion, list):
                return "motion", random.choice(direct_motion)
            return "motion", direct_motion
            
        direct_expr = self.resource_manager.find_expression(tag)
        if direct_expr:
            return "expression", direct_expr
            
        print(f"[BehaviorSystem] No direct action found for '{tag}'.")
        
        # 4. Fallback Mapping
        # If we asked for "happy" but don't have it, check fallback map for substitutes like "wave"
        if best_match_key and best_match_key in self.fallback_map:
            potential_fallbacks = self.fallback_map[best_match_key]
            for fb_key in potential_fallbacks:
                if fb_key in self.behavior_map and self.behavior_map[fb_key]:
                    print(f"[BehaviorSystem] Using fallback '{fb_key}' for '{tag}'")
                    return "motion", random.choice(self.behavior_map[fb_key])

        return None, None

    def process_tap(self, x, y):
        """
        Decides what to do when tapped.
        x, y: Normalized coordinates (-1 to 1)
        """
        print(f"[BehaviorSystem] Processing Tap at ({x:.2f}, {y:.2f})")
        
        # Y is inverted in NativeLive2DWidget (Top = 1, Bottom = -1)
        action_key = "tap_body"
        if y > 0.4:
            action_key = "tap_head"
            print("[BehaviorSystem] Detected: Head Pat")
        else:
            print("[BehaviorSystem] Detected: Body Touch")
            
        # Check map
        if action_key in self.behavior_map:
            return "motion", random.choice(self.behavior_map[action_key])
            
        # Fallback to generic 'shake' or 'surprised' expression if no tap motion
        if "shake" in self.behavior_map:
            return "motion", random.choice(self.behavior_map["shake"])
            
        # Try to find a fallback expression
        fallback_expr = self.resource_manager.find_expression("surprised") or self.resource_manager.find_expression("shock")
        if fallback_expr:
            return "expression", fallback_expr
            
        print("[BehaviorSystem] No tap response found.")
        return None, None
