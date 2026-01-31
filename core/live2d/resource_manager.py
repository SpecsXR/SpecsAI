import os
import json
import re

class Live2DResourceManager:
    """
    Intelligently manages Live2D assets (Motions, Expressions).
    Scans the model directory and maps natural language tags to specific files.
    """
    def __init__(self):
        self.model_dir = None
        self.model_json = None
        self.expressions = {} # Logical Name -> Filename
        self.motions = {}     # Logical Name -> Filename or List of Filenames
        self.groups = {}      # Group Name -> List of Motion Files

    def load_resources(self, model_dir):
        """Scans the model directory and builds the resource map."""
        self.model_dir = model_dir
        self.expressions = {}
        self.motions = {}
        self.groups = {}
        self.capabilities = {
            "physics": False,
            "lipsync": False,
            "eye_blink": False,
            "generated_json": False
        }

        if not os.path.exists(model_dir):
            print(f"[Live2DResourceManager] Error: Directory not found {model_dir}")
            return

        # 1. Try to find .model3.json
        model_file = None
        for f in os.listdir(model_dir):
            if f.endswith(".model3.json"):
                model_file = os.path.join(model_dir, f)
                break
        
        # AUTO-REPAIR: If no model3.json, try to generate one from raw files
        if not model_file:
            print("[Live2DResourceManager] No model3.json found. Attempting auto-generation...")
            model_file = self._auto_generate_model_json(model_dir)

        if model_file:
            self._parse_model_json(model_file)
        
        # 2. Deep Scan (Find unreferenced files and merge them)
        self._deep_scan_directory(model_dir)
        
        # 3. Check for unreferenced motions and UPDATE the JSON if needed
        # This fixes the "Tap doesn't work" issue by ensuring all motions are in groups
        # so StartMotion() can find them.
        registered_paths = set()
        for paths in self.groups.values():
            for p in paths:
                registered_paths.add(p.replace("\\", "/"))
        
        found_paths = set()
        for paths in self.motions.values():
            if isinstance(paths, list):
                for p in paths: found_paths.add(p.replace("\\", "/"))
            else:
                found_paths.add(paths.replace("\\", "/"))
                
        unregistered = found_paths - registered_paths
        if unregistered:
            print(f"[Live2DResourceManager] Found {len(unregistered)} unreferenced motions.")
            # DISABLED AUTO-UPDATE TO PREVENT CORRUPTION
            # print(f"[Live2DResourceManager] Found {len(unregistered)} unreferenced motions. Updating model3.json...")
            # if self._update_model_json(model_file, unregistered):
            #     # Reload groups to reflect changes immediately
            #     self.groups = {} 
            #     self._parse_model_json(model_file)
        
        # 4. Analyze Capabilities
        self._analyze_capabilities(model_dir)

        print(f"[Live2DResourceManager] Loaded {len(self.expressions)} expressions and {len(self.motions)} motions.")
        print(f"[Live2DResourceManager] Capabilities: {self.capabilities}")

    def _auto_generate_model_json(self, model_dir):
        """
        ADVANCED: Scans for .moc3, textures, and creates a valid model3.json in memory/disk.
        """
        try:
            # Find moc3
            moc3_file = None
            textures = []
            physics_file = None
            motions = {}
            expressions = []
            
            for root, _, files in os.walk(model_dir):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), model_dir).replace("\\", "/")
                    
                    if f.endswith(".moc3"):
                        moc3_file = rel_path
                    elif f.endswith(".png") and "texture" in root.lower():
                        textures.append(rel_path)
                    elif f.endswith("physics3.json"):
                        physics_file = rel_path
                    elif f.endswith(".motion3.json"):
                        # Use filename as group name (e.g. "tapBody" -> Group "tapBody")
                        group_name = f.replace(".motion3.json", "")
                        motions[group_name] = [{"File": rel_path}]
                    elif f.endswith(".exp3.json"):
                        name = f.replace(".exp3.json", "")
                        expressions.append({"Name": name, "File": rel_path})
            
            if not moc3_file:
                print("[Live2DResourceManager] Critical: No .moc3 file found. Cannot generate model.")
                return None

            # Sort textures naturally if possible
            textures.sort()

            # Create minimal JSON structure
            data = {
                "Version": 3,
                "FileReferences": {
                    "Moc": moc3_file,
                    "Textures": textures,
                    "Physics": physics_file,
                    "Motions": motions,
                    "Expressions": expressions
                }
            }
            
            # Save it
            generated_path = os.path.join(model_dir, "auto_generated.model3.json")
            with open(generated_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            self.capabilities["generated_json"] = True
            return generated_path

        except Exception as e:
            print(f"[Live2DResourceManager] Auto-generation failed: {e}")
            return None

    def _update_model_json(self, model_file, new_motion_paths):
        """Updates the model3.json to include new motions as groups."""
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_refs = data.get("FileReferences", {})
            motions = file_refs.get("Motions", {})
            
            changed = False
            for path in new_motion_paths:
                # Create a group name from the filename
                # e.g. "motions/tapBody.motion3.json" -> "tapBody"
                filename = os.path.basename(path)
                group_name = filename.replace(".motion3.json", "")
                
                if group_name not in motions:
                    motions[group_name] = [{"File": path}]
                    changed = True
                else:
                    # Group exists, check if file is in it
                    existing_files = [m.get("File") for m in motions[group_name]]
                    if path not in existing_files:
                        motions[group_name].append({"File": path})
                        changed = True
            
            if changed:
                file_refs["Motions"] = motions
                data["FileReferences"] = file_refs
                
                with open(model_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                print("[Live2DResourceManager] model3.json updated successfully.")
                return True
            return False
            
        except Exception as e:
            print(f"[Live2DResourceManager] Error updating model3.json: {e}")
            return False

    def _analyze_capabilities(self, model_dir):
        """Checks for Physics, LipSync parameters, etc."""
        # Physics Check
        for root, _, files in os.walk(model_dir):
            for f in files:
                if f.endswith("physics3.json"):
                    self.capabilities["physics"] = True
        
        # LipSync / Blink (Heuristic based on standard parameter names)
        # We can't easily parse moc3 without the library, but we can assume standard models have them.
        # If we had access to the loaded model instance, we could check parameters.
        # For now, we assume true if it's a standard format.
        self.capabilities["lipsync"] = True 
        self.capabilities["eye_blink"] = True

    def _parse_model_json(self, model_file):
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            file3 = data.get("FileReferences", {})
            
            # Expressions
            for exp in file3.get("Expressions", []):
                name = exp.get("Name")
                file_path = exp.get("File")
                if name and file_path:
                    self._register_expression(name, file_path)

            # Motions
            motions = file3.get("Motions", {})
            for group_name, motion_list in motions.items():
                self.groups[group_name] = []
                for motion in motion_list:
                    file_path = motion.get("File")
                    if file_path:
                        self.groups[group_name].append(file_path)
                        # Also register individual files
                        self._register_motion(group_name, file_path)

        except Exception as e:
            print(f"[Live2DResourceManager] Error parsing model3.json: {e}")

    def _deep_scan_directory(self, root_dir):
        """Recursively finds all .exp3.json and .motion3.json files."""
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.model_dir).replace("\\", "/")
                
                if file.endswith(".exp3.json"):
                    # Use filename as logical name (e.g. "Smile.exp3.json" -> "smile")
                    name = file.replace(".exp3.json", "")
                    self._register_expression(name, rel_path)
                    
                elif file.endswith(".motion3.json"):
                    name = file.replace(".motion3.json", "")
                    self._register_motion(name, rel_path)

    def _register_expression(self, name, path):
        # Normalize: lowercase
        key = name.lower()
        if key not in self.expressions:
            self.expressions[key] = path
            
            # Add fuzzy aliases
            if "smile" in key: self.expressions["happy"] = path
            if "sad" in key: self.expressions["cry"] = path
            if "angry" in key: self.expressions["mad"] = path

    def _register_motion(self, name, path):
        key = name.lower()
        # Remove trailing numbers (e.g. "tap_01" -> "tap")
        clean_key = re.sub(r'[_\-\s]*\d+$', '', key)
        
        if clean_key not in self.motions:
            self.motions[clean_key] = []
        
        if path not in self.motions[clean_key]:
            self.motions[clean_key].append(path)

    def find_expression(self, tag):
        """
        Finds the best matching expression for a given tag/action.
        Example: "looks happy" -> "smile"
        """
        tag = tag.lower()
        
        # Direct Match
        if tag in self.expressions:
            return self.expressions[tag]
        
        # Keyword Search
        keywords = {
            "happy": ["smile", "joy", "laugh", "happy"],
            "sad": ["cry", "tear", "sad", "depressed", "grief"],
            "angry": ["mad", "rage", "angry", "furious"],
            "surprised": ["shock", "wow", "surprise"],
            "shy": ["blush", "shy", "embarrassed"],
            "neutral": ["normal", "idle", "default"]
        }
        
        for exp_key, file_path in self.expressions.items():
            # Check if exp_key matches any keyword in the tag
            if exp_key in tag:
                return file_path
                
        # Reverse check: Check if tag contains any standard emotion keywords
        for emotion, aliases in keywords.items():
            for alias in aliases:
                if alias in tag:
                    # Try to find an expression that matches this emotion
                    # 1. Look for exact match of emotion name
                    if emotion in self.expressions: return self.expressions[emotion]
                    # 2. Look for expression containing alias
                    for k, v in self.expressions.items():
                        if alias in k: return v
                        
        return None

    def find_motion(self, tag):
        """
        Finds the best matching motion for a given tag/action.
        """
        tag = tag.lower()
        
        # Clean tag (remove "looks", "is", etc.)
        clean_tag = tag.replace("looks ", "").replace("is ", "").strip()
        
        # Direct Match
        if clean_tag in self.motions:
            return self.motions[clean_tag]
            
        # Group Match
        # e.g. "tap" -> group "Tap"
        for group in self.groups:
            if group.lower() == clean_tag:
                return self.groups[group]
                
        # Keyword Search
        if "wave" in tag or "hello" in tag: return self.motions.get("wave") or self.motions.get("flickleft")
        if "nod" in tag or "yes" in tag: return self.motions.get("nod") or self.motions.get("flickright")
        if "shake" in tag or "no" in tag: return self.motions.get("shake")
        
        # Partial Match in keys
        for key, paths in self.motions.items():
            if key in tag:
                return paths
                
        return None

    def find_motion_group(self, path):
        """
        Reverse lookup: Find which group and index a file belongs to.
        Returns (group_name, index) or None.
        """
        for group, files in self.groups.items():
            # Normalize paths for comparison
            norm_path = path.replace("\\", "/")
            norm_files = [f.replace("\\", "/") for f in files]
            
            if norm_path in norm_files:
                return group, norm_files.index(norm_path)
        return None
