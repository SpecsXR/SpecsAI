import os
import time
import random
import math
import re
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QSurfaceFormat, QBitmap, QCursor
from core.live2d.live2d_controller import Live2DController

# Import Live2D (v3 for Cubism 4/5)
try:
    import live2d.v3 as live2d
except ImportError:
    live2d = None
    print("[Error] live2d-py not installed. Please install it.")

class NativeLive2DWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Controller Initialization ---
        self.controller = Live2DController(self)
        # ---------------------------------
        
        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

        
        # Set Surface Format for Alpha Channel
        fmt = QSurfaceFormat()
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        fmt.setVersion(3, 3) # Upgrade to 3.3 Compatibility for FBO support
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        fmt.setAlphaBufferSize(8)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        self.setFormat(fmt)
        
        self.model = None
        self.is_initialized = False
        self.current_model_path = None
        self.is_speaking = False
        self.lip_sync_value = 0.0
        self.lip_target = 0.0
        self.lip_next_change = 0
        self.current_emotion = "normal"
        
        # --- HIGH TECH UPGRADES ---
        # Mouse Tracking
        self.setMouseTracking(True) # Enable mouse tracking without button press
        self.tracking_enabled = True # Active state
        self.user_tracking_pref = True # User preference (Menu Toggle)
        self.target_look_x = 0.0
        self.target_look_y = 0.0
        self.current_look_x = 0.0
        self.current_look_y = 0.0
        
        # Physics / Wind Simulation
        self.wind_strength = 0.0
        self.wind_timer = 0.0
        
        # Human-like Idle Behavior
        self.last_interaction_time = time.time()
        self.idle_timeout = 5.0 # Seconds before starting idle motions
        self.auto_blink_timer = 0
        self.breath_timer = 0.0 # Breathing Cycle
        
        # Posture Control (Procedural Animation Override)
        self.posture_override = {} # Dict of param_name -> value
        self.posture_end_time = 0.0 # Timestamp until which override is active
        
        # Timer for 60 FPS rendering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
    def initializeGL(self):
        if not live2d:
            return
            
        print("[NativeLive2D] Initializing OpenGL...")
        self.makeCurrent() # Ensure context is current before external init
        live2d.init()
        live2d.glInit() # Initialize internal GL resources
        live2d.enableLog(True)
        self.is_initialized = True
        
        # Start animation loop
        self.timer.start(16) # ~60 FPS
        
        # Load pending model if any
        if self.current_model_path:
            self.load_model(self.current_model_path)

    def paintGL(self):
        if not self.is_initialized or not live2d:
            return
            
        # Clear buffer with transparent color
        # DEBUG: If you see a RED/GREEN box, it means transparency is failing.
        # live2d.clearBuffer(0.0, 1.0, 0.0, 0.5) # Debug Green
        live2d.clearBuffer(0.0, 0.0, 0.0, 0.0) # Transparent
        
        if self.model:
            # Update and Draw
            # Time delta is handled internally or we can pass it if needed
            self.model.Update()
            self.model.Draw()

    def resizeGL(self, w, h):
        if self.model:
            self.model.Resize(w, h)
            
    def closeEvent(self, event):
        """Cleanup resources before destruction"""
        print("[NativeLive2D] Closing widget...")
        if self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse movement for head tracking"""
        # Calculate normalized coordinates (-1.0 to 1.0)
        w = self.width()
        h = self.height()
        
        # --- IMPROVED HEAD TRACKING ---
        # User Feedback: "Keeps looking up" (Shei oporei takaye thaktese)
        # Reason: Previous logic assumed Center (h/2) was neutral.
        # But character head is likely higher or lower depending on layout.
        # If widget is full screen, and character is at bottom, Mouse is almost always "Above".
        
        # New Approach: 
        # Define a "Head Level" in screen coordinates.
        # If Mouse < Head Level -> Look Up
        # If Mouse > Head Level -> Look Down
        
        # Let's assume Head Level is at 30% from the top (0.3 * h)
        head_level_y = h * 0.3
        
        # Calculate Y relative to Head Level
        rel_y = event.y() - head_level_y
        
        # Scale factor (Sensitivity)
        # If mouse is at 0 (Top), rel_y = -0.3h. We want Look Up (+1.0 max)
        # If mouse is at h (Bottom), rel_y = 0.7h. We want Look Down (-1.0 max)
        
        # Note: Screen Y increases DOWN. Live2D ParamAngleY increases UP (+).
        # So Negative rel_y (Above) should map to Positive ParamAngleY.
        
        scale_y = h * 0.5 # Sensitivity divisor
        y = -(rel_y / scale_y)
        
        x = (event.x() / w) * 2.0 - 1.0 
        
        # Clamp to reasonable range (-1.0 to 1.0)
        self.target_look_x = max(-1.0, min(1.0, x))
        self.target_look_y = max(-1.0, min(1.0, y))
        
        # Call parent
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        """Propagate wheel events to parent (MainWindow) for resizing"""
        event.ignore()


    def leaveEvent(self, event):
        """Reset look target when mouse leaves window"""
        # Disable reset to prevent head snapping when mouse leaves (or context menu opens)
        # self.target_look_x = 0.0
        # self.target_look_y = 0.0
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle Taps/Clicks via Controller"""
        # User requested to REMOVE body tap feature for now.
        # Keeping the structure for future use, but disabling the call.
        if event.button() == Qt.LeftButton:
            pass
            # Calculate normalized coordinates (-1 to 1)
            # h = self.height()
            # w = self.width()
            # x = (event.x() / w) * 2 - 1
            # # Invert Y to match Live2D coordinate system (Top=1, Bottom=-1)
            # y = -((event.y() / h) * 2 - 1)
            
            # # Controller handles the logic
            # if self.controller:
            #     self.controller.on_tap(x, y)
                
        super().mousePressEvent(event)

    def set_emotion(self, emotion_name):
        """Wrapper for Controller to set emotion/expression"""
        if self.controller:
            self.controller.set_expression(emotion_name)

    def trigger_motion(self, motion_name):
        """Wrapper for Controller to trigger motion"""
        if self.controller:
            self.controller.trigger_motion(motion_name)

    def update_animation(self):
        # Handle Lip Sync (Smoothed)
        if self.model and self.is_speaking:
            
            # Target mouth openness (0.0 to 1.0)
            # We change the target occasionally to simulate speech rhythm
            if not hasattr(self, 'lip_target'):
                self.lip_target = 0.0
                self.lip_next_change = 0
            
            current_time = time.time()
            if current_time > self.lip_next_change:
                # New target: 
                # 20% chance of closing (pause), 80% chance of active speech
                if random.random() < 0.2:
                    self.lip_target = 0.0
                else:
                    # OPEN FREELY: Range 0.3 to 1.0 (Max open)
                    self.lip_target = random.uniform(0.3, 1.0)
                
                # Next change in 0.05s to 0.15s (Faster, more responsive)
                self.lip_next_change = current_time + random.uniform(0.05, 0.15)

            # Smoothly interpolate towards target
            # 0.4 factor gives a snappier effect (less laggy)
            self.lip_sync_value = self.lip_sync_value * 0.6 + self.lip_target * 0.4
            
            # Try both standard and CAPS parameter names (Model dependent)
            self.model.SetParameterValue("PARAM_MOUTH_OPEN_Y", self.lip_sync_value, 1.0)
            self.model.SetParameterValue("ParamMouthOpenY", self.lip_sync_value, 1.0)
            self.last_interaction_time = time.time() # Reset idle timer
        elif self.model:
             # Close mouth smoothly when not speaking
             self.lip_sync_value = self.lip_sync_value * 0.8 # Decay
             if self.lip_sync_value < 0.01: self.lip_sync_value = 0.0
             
             # Force mouth closed with MAX weight (1.0) to override any idle motion mouth movement
             self.model.SetParameterValue("PARAM_MOUTH_OPEN_Y", self.lip_sync_value, 1.0)
             self.model.SetParameterValue("ParamMouthOpenY", self.lip_sync_value, 1.0)

        # Handle Human-like Idle Behavior
        if self.model:
            current_time = time.time()
            
            # --- Check Posture Override ---
            is_posture_active = False
            if current_time < self.posture_end_time and self.posture_override:
                is_posture_active = True
                # Apply overridden parameters
                for param, value in self.posture_override.items():
                    # Apply to Standard (CamelCase)
                    self.model.SetParameterValue(param, value, 1.0)
                    
                    # Apply to UPPERCASE (PARAMANGLE) - Rare but possible
                    self.model.SetParameterValue(param.upper(), value, 1.0)
                    
                    # Apply to SNAKE_CASE_UPPER (PARAM_ANGLE_X) - Common in older models/Izumi
                    # ParamAngleX -> PARAM_ANGLE_X
                    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', param).upper()
                    self.model.SetParameterValue(snake_case, value, 1.0)
            else:
                # Posture expired, re-enable tracking if it was disabled by posture
                if self.posture_override: # It was active but just timed out
                     self.posture_override = {}
                     # Only re-enable tracking if USER PREFERENCE allows it
                     self.tracking_enabled = self.user_tracking_pref 

            # --- 1. Breathing (Standard ParamBreath) ---
            # Cycle ~20 seconds (Very Slow) - 0.3 rad/s
            # Fixed speed to avoid frequency acceleration bugs
            breath_speed = 0.3 
            breath = (math.sin(current_time * breath_speed) + 1.0) * 0.2 # Reduced amplitude to 0.2 (Very subtle)
            self.model.SetParameterValue("ParamBreath", breath, 1.0)
            self.model.SetParameterValue("PARAM_BREATH", breath, 1.0)

            # --- 2. Advanced Head Tracking (Look At Mouse - GLOBAL) ---
            # ONLY if Posture is NOT active
            if not is_posture_active:
                if self.tracking_enabled:
                    # --- GLOBAL TRACKING LOGIC ---
                    try:
                        cursor_pos = QCursor.pos()
                        # Widget position in global coordinates
                        # We use a try-except because mapToGlobal might fail during initialization
                        if self.isVisible():
                            widget_pos = self.mapToGlobal(self.rect().topLeft())
                            
                            # Head Center (approximate)
                            # Assuming head is horizontally centered and at ~30% from top of widget
                            head_cx = widget_pos.x() + self.width() * 0.5
                            head_cy = widget_pos.y() + self.height() * 0.3 
                            
                            # Deltas (Cursor relative to Head)
                            dx = cursor_pos.x() - head_cx
                            dy = cursor_pos.y() - head_cy
                            
                            # Screen Reference for Normalization
                            # Use primary screen or current screen
                            screen = self.screen()
                            if not screen:
                                screen = self.window().windowHandle().screen() if self.window().windowHandle() else None
                            
                            if screen:
                                screen_rect = screen.geometry()
                                max_dx = screen_rect.width() * 0.5
                                max_dy = screen_rect.height() * 0.5
                            else:
                                max_dx = 1920 * 0.5
                                max_dy = 1080 * 0.5
                            
                            # Normalize (-1.0 to 1.0)
                            raw_x = max(-1.0, min(1.0, dx / max_dx))
                            # Invert Y: Up on screen (negative dy) -> Positive ParamAngleY (Look Up)
                            raw_y = max(-1.0, min(1.0, -(dy / max_dy)))
                            
                            # Apply Sensitivity
                            self.target_look_x = max(-1.0, min(1.0, raw_x * 1.5))
                            self.target_look_y = max(-1.0, min(1.0, raw_y * 1.5))
                    except Exception as e:
                        pass # Ignore tracking errors during init

                    # Smooth Interpolation
                    smoothing = 0.1 # Responsive
                    self.current_look_x += (self.target_look_x - self.current_look_x) * smoothing
                    self.current_look_y += (self.target_look_y - self.current_look_y) * smoothing
                else:
                    # Return to center
                    self.current_look_x += (0.0 - self.current_look_x) * 0.05
                    self.current_look_y += (0.0 - self.current_look_y) * 0.05
                
                # Apply to Head
                self.model.SetParameterValue("ParamAngleX", self.current_look_x * 30, 1.0)
                self.model.SetParameterValue("ParamAngleY", self.current_look_y * 30, 1.0)
                self.model.SetParameterValue("PARAM_ANGLE_X", self.current_look_x * 30, 1.0)
                self.model.SetParameterValue("PARAM_ANGLE_Y", self.current_look_y * 30, 1.0)
                
                # Apply to Eyes
                self.model.SetParameterValue("ParamEyeBallX", self.current_look_x, 1.0)
                self.model.SetParameterValue("ParamEyeBallY", self.current_look_y, 1.0)
                self.model.SetParameterValue("PARAM_EYE_BALL_X", self.current_look_x, 1.0)
                self.model.SetParameterValue("PARAM_EYE_BALL_Y", self.current_look_y, 1.0)
                
                # Debug Eye Tracking (Throttled) - DISABLED for Production
                # if not hasattr(self, 'last_eye_debug'): self.last_eye_debug = 0
                # if time.time() - self.last_eye_debug > 2.0:
                #     print(f"[NativeLive2D] Eyes: {self.current_look_x:.2f}, {self.current_look_y:.2f} (Target: {self.target_look_x:.2f}, {self.target_look_y:.2f})")
                #     self.last_eye_debug = time.time()
                
                # Apply to Body
                self.model.SetParameterValue("ParamBodyAngleX", self.current_look_x * 10, 1.0)
                self.model.SetParameterValue("PARAM_BODY_ANGLE_X", self.current_look_x * 10, 1.0)

            # --- 3. Simulated Wind / Physics (Hair Sway) ---
            # Only apply wind if tracking is enabled (happy/normal state) AND Posture not active
            if self.tracking_enabled and not is_posture_active:
                # Perlin-like noise using sins - SLOWED DOWN significantly
                self.wind_timer += 0.02 # Was 0.05. Slower update = less jitter.
                wind_noise = math.sin(self.wind_timer) * 0.5 + math.sin(self.wind_timer * 0.5) * 0.3
                
                # Apply to Hair Physics parameters
                if abs(self.target_look_x) < 0.2:
                    tilt_z = wind_noise * 1.0 # Was 2.0. Reduced sway.
                    self.model.SetParameterValue("ParamAngleZ", tilt_z, 0.5) 
                    self.model.SetParameterValue("PARAM_ANGLE_Z", tilt_z, 0.5)

            # --- Fix: Force Mouth Closed if Not Speaking ---
            # Prevents random lip movement from idle motions or noise
            if not self.is_speaking:
                self.model.SetParameterValue("ParamMouthOpenY", 0.0, 1.0)
                self.model.SetParameterValue("PARAM_MOUTH_OPEN_Y", 0.0, 1.0)

            # --- 4. Breathing (Continuous) ---
            # self.breath_timer += 0.05
            # breath_val = (math.sin(self.breath_timer) + 1.0) * 0.5
            # self.model.SetParameterValue("ParamBreath", breath_val, 1.0)
            # self.model.SetParameterValue("PARAM_BREATH", breath_val, 1.0)

            # --- 5. Auto Blink (Physics/Timer) ---
            # Disable blink for emotions that usually have closed eyes (happy/smile)
            # or if we want to preserve specific eye shapes of expressions (sad/angry often have specific eye openings)
            should_blink = True
            if self.current_emotion in ["happy", "smile", "sleeping"]:
                should_blink = False
            
            if should_blink:
                if self.auto_blink_timer <= 0:
                     # Blink every 2-5 seconds randomly (more frequent = more alive)
                     if random.random() < 0.01: 
                         self.auto_blink_timer = 0.25 # Blink duration
                else:
                     self.auto_blink_timer -= 0.016 # Sub 16ms
                     # Bell curve for blink (0 -> 1 -> 0)
                     t = max(0, self.auto_blink_timer)
                     eye_val = 1.0 - math.sin((t / 0.25) * math.pi) # 1 (Open) -> 0 (Closed) -> 1 (Open)
                     
                     # Clamp
                     if eye_val < 0: eye_val = 0
                     if eye_val > 1: eye_val = 1
                     
                     self.model.SetParameterValue("ParamEyeLOpen", eye_val, 1.0)
                     self.model.SetParameterValue("ParamEyeROpen", eye_val, 1.0)
                     self.model.SetParameterValue("PARAM_EYE_L_OPEN", eye_val, 1.0)
                     self.model.SetParameterValue("PARAM_EYE_R_OPEN", eye_val, 1.0)
            
        # 5. Trigger Idle Motion Loop (Subtle) - ENABLED as per "High Tech" request
        # We want 'Idle' to be subtle, not big movements.
        # Only trigger if user hasn't interacted for a while and we are not speaking
        if not self.is_speaking:
            # Check strategy
            should_play_motion = True
            if hasattr(self, 'idle_strategy') and self.idle_strategy == "eyes_only":
                should_play_motion = False
            
            # Start Idle motion continuously (Loop) if allowed
            # We don't want to spam it, so check interval or let Live2D handle it.
            # Usually StartRandomMotion("Idle") starts it if not playing.
            # FIX: Only play idle if NO other motion is playing (check priority or isFinished if possible)
            # For now, we reduce frequency to avoid "Head Up" locking from bad idle motions.
            if should_play_motion and random.random() < 0.01: # Reduced from 0.05 (less frequent)
                 self.start_random_motion("Idle", 1) 
            
        self.update() # Schedule a repaint
                
        self.update() # Schedule a repaint

    def set_posture(self, posture_data):
        """
        Sets a procedural posture based on the provided data.
        posture_data format:
        {
            "params": {"ParamAngleY": -30, ...},
            "expression": "Sad",
            "motion": "sigh",
            "duration": 2.0
        }
        """
        if not self.model or not posture_data:
            return

        print(f"[NativeLive2D] Setting Posture: {posture_data}")

        # 1. Set Expression
        if "expression" in posture_data and posture_data["expression"]:
            self.set_emotion(posture_data["expression"])

        # 2. Trigger Motion
        if "motion" in posture_data and posture_data["motion"]:
            self.trigger_motion(posture_data["motion"])

        # 3. Apply Parameter Overrides
        if "params" in posture_data and posture_data["params"]:
            self.posture_override = posture_data["params"]
            duration = posture_data.get("duration", 2.0)
            self.posture_end_time = time.time() + duration
            
            # Disable mouse tracking during posture override to prevent conflict
            self.tracking_enabled = False

    def start_random_motion(self, group="Idle", priority=2):
        """Starts a random motion from the specified group"""
        if not self.model: return
        try:
            if hasattr(self.model, "StartRandomMotion"):
                self.model.StartRandomMotion(group, priority)
            else:
                self.model.StartMotion(group, 0, priority)
        except Exception as e:
            print(f"[NativeLive2D] Error starting random motion: {e}")

    def set_lip_sync(self, active):
        """Enable or disable lip sync animation"""
        self.is_speaking = active
        if not active and self.model:
            self.model.SetParameterValue("PARAM_MOUTH_OPEN_Y", 0.0, 1.0)

    def start_motion(self, group, no, priority):
        """Start a specific motion (Group + Index)"""
        if self.model:
            print(f"[NativeLive2D] Starting Motion: Group={group}, No={no}, Priority={priority}")
            try:
                self.model.StartMotion(group, no, priority)
            except Exception as e:
                print(f"[NativeLive2D] Error starting motion: {e}")
    
    def start_motion_file(self, motion_path):
        """Start a motion by file path (Fallback)"""
        if self.model:
            print(f"[NativeLive2D] Starting Motion File: {motion_path}")
            try:
                # Fallback: Just try treating path as group name
                self.model.StartMotion(motion_path, 0, 3)
            except Exception as e:
                print(f"[NativeLive2D] Error starting motion file: {e}")

    def set_expression_file(self, expression_path):
        """Set an expression by file path"""
        if self.model:
            # Extract name from path (e.g. "Smile.exp3.json" -> "Smile")
            name = os.path.basename(expression_path).split(".")[0]
            print(f"[NativeLive2D] Setting Expression: {name} ({expression_path})")
            try:
                self.model.SetExpression(name)
            except Exception as e:
                print(f"[NativeLive2D] Error setting expression: {e}")

    def get_render_mask(self, scale=0.5):
        """
        Returns a QBitmap mask based on the current render content (Alpha channel).
        Args:
            scale (float): Scale factor for mask generation (default 0.5).
                          Lower values (e.g. 0.25) are faster but less precise.
        Returns:
            QBitmap: The generated mask (at scaled size).
        """
        if not self.is_initialized:
            return None
        
        try:
            # Grab content (GPU -> CPU readback)
            image = self.grabFramebuffer()
            if image.isNull():
                return None
            
            # Optimization: Downscale image for faster mask generation
            # This significantly reduces the cost of createAlphaMask() and subsequent Region operations
            if scale < 1.0:
                new_w = int(image.width() * scale)
                new_h = int(image.height() * scale)
                if new_w > 0 and new_h > 0:
                    image = image.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.FastTransformation)
            
            # Create Alpha Mask (1 for non-transparent pixels, 0 for transparent)
            # This creates a tight contour around the visible pixels
            raw_mask = QBitmap.fromImage(image.createAlphaMask())
            return raw_mask
        except Exception as e:
            print(f"[NativeLive2D] Error creating mask: {e}")
            return None

    def load_model(self, model_path):
        """Loads a Live2D model from the given absolute path."""
        # Normalize path separators to forward slashes (helps with some C++ bindings)
        model_path = model_path.replace("\\", "/")
        self.current_model_path = model_path
        
        # Notify Controller
        if self.controller:
            self.controller.load_model(model_path)

        if not self.is_initialized:
            print(f"[NativeLive2D] Queuing model load: {model_path}")
            return
            
        if not os.path.exists(model_path):
            print(f"[NativeLive2D] Error: Model file not found: {model_path}")
            return

        print(f"[NativeLive2D] Loading model: {model_path}")
        
        try:
            # Clean up old model
            if self.model:
                # self.model.Delete() # If such method exists, otherwise assume GC handles it or reuse
                self.model = None
            
            # Create new model
            self.model = live2d.LAppModel()
            
            # Load Model
            # Note: live2d-py expects the JSON path. 
            # It handles texture paths relative to the JSON.
            self.model.LoadModelJson(model_path)
            
            # Initial Resize
            self.model.Resize(self.width(), self.height())
            
            # --- DEBUG: Print Texture Info ---
            # Try to verify if textures are loaded
            # Note: Python binding might not expose GetTexture, but let's try or just log.
            print(f"[NativeLive2D] Model Resized to: {self.width()}x{self.height()}")
            # ---------------------------------
            
            # Enable LipSync and other features if available
            # self.model.StartMotion(...) 
            
            # Special Config for Specific Models
            if "izumi" in model_path.lower():
                self.idle_strategy = "eyes_only"
                print("[NativeLive2D] Config: Izumi detected. Setting Idle Strategy to 'eyes_only'.")
            else:
                self.idle_strategy = "full" # default
            
            print("[NativeLive2D] Model loaded successfully.")

            # Debug: Dump Parameters to identify correct Eye/Mouth IDs
            self.debug_dump_parameters()
            
        except Exception as e:
            print(f"[NativeLive2D] Exception loading model: {e}")
            import traceback
            traceback.print_exc()

    def debug_dump_parameters(self):
        """Dumps all available parameters in the loaded model for debugging"""
        if not self.model: return
        try:
            pass
            # print("--- Model Parameter Dump ---")
            
            # # Print available methods to debug API
            # # print(f"Model Methods: {dir(self.model)}")
            
            # if hasattr(self.model, "GetParameterCount"):
            #     count = self.model.GetParameterCount()
            #     print(f"Parameter Count: {count}")
                
            #     # Try to get IDs by index
            #     for i in range(min(count, 323)): # Scan all
            #         try:
            #             pid = self.model.GetParameterId(i)
            #             if "Eye" in pid or "Ball" in pid or "Mouth" in pid:
            #                  print(f"Param [{i}]: {pid}")
            #         except:
            #             pass
            # print("----------------------------")
        except Exception as e:
            print(f"Could not dump parameters: {e}")

    def set_click_through(self, enabled):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

    def look_at(self, x, y):
        # Programmatic look at
        if self.model:
             self.model.Drag(x, y)

    def set_state(self, state):
        # Placeholder for state management (e.g. idle, talking)
        # In future, trigger motions based on state
        pass
