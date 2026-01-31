import pyttsx3
import threading
import queue
import time
import asyncio
import edge_tts
import os
import tempfile
from langdetect import detect
from dataclasses import dataclass
from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal
from core.config import Config
from core.services.character_presets import CharacterPresets
from core.settings.settings_manager import SettingsManager

@dataclass
class VoiceProfile:
    id: str
    name: str
    gender: str = "unknown" # male, female, unknown
    age: str = "adult" # child, adult, senior
    style: str = "neutral" # cute, mature, serious, etc.
    engine_id: str = "" # ID used by the TTS engine
    provider: str = "system" # system, edge-tts, edge-tts-preset
    language: str = "en" # en, bn, es, etc.
    pitch: str = "+0Hz"
    rate: str = "+0%"
    volume: str = "+0%"

class VoiceService(QObject):
    # Signals for Lip Sync and UI updates
    speaking_started = Signal()
    speaking_finished = Signal()
    audio_playback_requested = Signal(str, str, dict) # Request main thread to play audio (file_path, display_text, metadata)
    speech_metadata_ready = Signal(dict) # For System TTS to pass metadata

    # Mapping language codes to preferred Edge TTS voices
    # High quality defaults
    LANG_VOICE_MAP = {
        "bn": {"female": "bn-BD-NabanitaNeural", "male": "bn-BD-PradeepNeural"},
        "en": {"female": "en-US-AriaNeural", "male": "en-US-GuyNeural"},
        "hi": {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"},
        "es": {"female": "es-ES-ElviraNeural", "male": "es-ES-AlvaroNeural"},
        "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
        "ar": {"female": "ar-EG-SalmaNeural", "male": "ar-EG-ShakirNeural"},
        "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
        "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural"},
        "zh-cn": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural"},
        # Add more as needed
    }

    def __init__(self):
        super().__init__()
        
        # Cleanup old temp files
        self._cleanup_temp_files()

        # Temporary engine for discovery only
        temp_engine = pyttsx3.init()
        self.voices: Dict[str, VoiceProfile] = {}
        self._load_system_voices(temp_engine)
        del temp_engine # Cleanup
        
        # Load Character Presets (Synchronous)
        self._load_character_presets()
        
        # Load Online Voices (Edge TTS)
        # We run this in background to not block startup
        threading.Thread(target=self._load_edge_voices, daemon=True).start()

        self.current_voice_id = None
        if self.voices:
            self.current_voice_id = list(self.voices.keys())[0]

        # Check for saved voice preference
        self.strict_mode = False
        try:
             settings = SettingsManager().get_all()
             voice_settings = settings.get("voice", {})
             
             saved_voice = voice_settings.get("default_voice_id")
             self.strict_mode = voice_settings.get("strict_mode", False)
             
             if saved_voice and saved_voice in self.voices:
                 self.current_voice_id = saved_voice
                 print(f"VoiceService: Restored saved voice '{self.voices[saved_voice].name}'")
        except Exception as e:
            print(f"VoiceService: Error loading saved voice: {e}")

        # Queue system for non-blocking sequential speech
        self._speech_queue = queue.Queue()
        
        # Synchronization event for audio playback
        self._playback_finished_event = threading.Event()

        self._is_running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        
    def set_strict_mode(self, enabled: bool):
        """Enable/Disable strict voice mode (no auto-switching)"""
        self.strict_mode = enabled
        print(f"VoiceService: Strict Mode set to {enabled}")

    def stop_playback(self):
        """Stops current playback sequence and clears queue"""
        # Clear the queue
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        
        # Unblock current wait if any
        self.notify_playback_finished()
        print("VoiceService: Playback stopped and queue cleared.")

    def notify_playback_finished(self):
        """Called by main thread when audio playback is done"""
        self._playback_finished_event.set()

    def _cleanup_temp_files(self):
        """Removes old TTS files from temp directory"""
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), "specsai_tts")
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    fp = os.path.join(temp_dir, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                    except Exception as e:
                        print(f"Startup Cleanup Error: {e}")
        except: pass

    def _load_character_presets(self):
        """Loads the 100 character presets"""
        presets = CharacterPresets.get_presets()
        for p in presets:
            # Infer gender roughly from category or name if needed, 
            # but CharacterProfile doesn't strictly have gender. 
            # We can guess or assume based on category lists in presets file.
            # But presets.py separates them in code but returns flat list.
            # Simple heuristic:
            gender = "female" # Default
            name_lower = p.name.lower()
            if "boy" in name_lower or "man" in name_lower or "male" in name_lower or "guy" in name_lower or "butler" in name_lower or "prince" in name_lower or "lord" in name_lower or "hero" in name_lower or "ninja" in name_lower:
                 if "heroine" not in name_lower:
                     gender = "male"
            
            # Refine gender based on voice ID (Guy, Eric, Christopher -> Male)
            male_voices = ["Guy", "Eric", "Christopher", "Roger", "Ryan", "Thomas", "William", "Steffan", "Chilemba", "Sam", "Keita", "Killian", "Fabrice"]
            if any(mv in p.base_voice_id for mv in male_voices):
                gender = "male"

            profile = VoiceProfile(
                id=p.id,
                name=p.name,
                gender=gender,
                engine_id=p.base_voice_id,
                provider="edge-tts-preset",
                language="en", # Presets are mostly English focused
                pitch=p.pitch,
                rate=p.rate,
                volume=p.volume,
                style=p.category
            )
            self.voices[profile.id] = profile
        
        print(f"Loaded {len(presets)} Character Presets")

        
    def _load_system_voices(self, engine):
        """Loads available system voices via pyttsx3"""
        try:
            # Check if engine is valid
            if not engine: return
            try:
                system_voices = engine.getProperty('voices')
            except Exception as e:
                print(f"pyttsx3 getProperty error: {e}")
                return

            for v in system_voices:
                # Basic heuristics to determine gender/style
                name_lower = v.name.lower()
                gender = "female" if "zira" in name_lower or "female" in name_lower else "male"
                if "david" in name_lower: gender = "male"
                
                profile = VoiceProfile(
                    id=f"sys_{v.id}",
                    name=f"{v.name} (System)",
                    gender=gender,
                    engine_id=v.id,
                    provider="system",
                    language="en" # System voices are hard to detect reliably without parsing ID
                )
                self.voices[profile.id] = profile
                
            # Set a default if available
            if self.voices:
                self.current_voice_id = list(self.voices.keys())[0]
                
        except Exception as e:
            print(f"Error loading system voices: {e}")

    def _load_edge_voices(self):
        """Loads available Edge TTS voices"""
        try:
            # We need a loop to run async function
            async def get_voices():
                return await edge_tts.list_voices()
            
            voices = asyncio.run(get_voices())
            
            for v in voices:
                # Keep all voices now, not just English
                # if "English" not in v['FriendlyName']: continue
                    
                gender = "female" if "Female" in v['Gender'] else "male"
                short_name = v['ShortName']
                friendly_name = v['FriendlyName'] # e.g., "Microsoft Aria Online (Natural) - English (United States)"
                
                # Extract language code roughly from ShortName (e.g., "en-US-AriaNeural" -> "en")
                lang_code = short_name.split('-')[0].lower()
                
                profile = VoiceProfile(
                    id=f"edge_{short_name}",
                    name=f"{friendly_name} (Online)",
                    gender=gender,
                    engine_id=short_name,
                    provider="edge-tts",
                    language=lang_code
                )
                self.voices[profile.id] = profile
                
            print(f"Loaded {len(voices)} Edge TTS voices")
            
            # Switch to a better default if available (e.g., Aria or Guy)
            # Prefer Aria for female, Guy for male
            # Only if we don't have a good one yet (e.g. only system voices or random default)
            # If current voice is a Preset, keep it!
            current = self.voices.get(self.current_voice_id)
            if not current or current.provider == "system":
                for vid, v in self.voices.items():
                    if "Aria" in v.name and v.provider == "edge-tts":
                         self.current_voice_id = vid
                         break
                     
        except Exception as e:
            print(f"Error loading Edge voices: {e}")

    def get_available_voices(self, gender: str = None) -> List[VoiceProfile]:
        """Returns available voices, optionally filtered by gender ('male' or 'female')"""
        all_voices = list(self.voices.values())
        if gender:
            filtered = [v for v in all_voices if v.gender == gender]
            # If no voices match preference, return all to avoid silence
            return filtered if filtered else all_voices
        return all_voices

    def auto_select_voice_for_gender(self, gender: str):
        """Automatically switches to the first available voice of the specified gender"""
        # Prefer Edge TTS voices
        candidates = self.get_available_voices(gender)
        
        # Sort candidates to put edge-tts first
        candidates.sort(key=lambda x: x.provider == "system") # False (0) comes first? No, True is 1. 
        # We want edge-tts (0 if check is provider != edge). 
        # Let's simple filter
        edge_candidates = [v for v in candidates if v.provider == "edge-tts"]
        sys_candidates = [v for v in candidates if v.provider == "system"]
        
        final_list = edge_candidates + sys_candidates
        
        if final_list:
            self.set_voice(final_list[0].id)
            print(f"Auto-selected voice: {final_list[0].name} for gender: {gender}")

    def set_voice(self, voice_id: str):
        if voice_id in self.voices:
            self.current_voice_id = voice_id
            print(f"Voice selected: {self.voices[voice_id].name}")
            
            # Save to settings
            try:
                SettingsManager().set("voice", "default_voice_id", voice_id)
                SettingsManager().set("voice", "default_voice", self.voices[voice_id].name)
            except Exception as e:
                print(f"Failed to save voice setting: {e}")

    def speak(self, text: str, display_text: str = None, metadata: dict = None):
        """Add text to the speech queue"""
        # If text contains asterisks (actions), remove them for speech
        import re
        clean_text = re.sub(r'\*.*?\*', '', text) # Remove *actions*
        
        if not clean_text.strip():
            return
            
        self._speech_queue.put((clean_text, display_text or text, metadata or {}))

    def _detect_language(self, text: str) -> str:
        """Detects language code from text with heuristics for better stability"""
        # 1. Heuristic: Check for specific scripts
        # Bangla (U+0980 - U+09FF)
        if any('\u0980' <= char <= '\u09ff' for char in text):
            return "bn"
        # Hindi/Devanagari (U+0900 - U+097F)
        if any('\u0900' <= char <= '\u097f' for char in text):
            return "hi"
            
        # 2. Heuristic: Short Latin text is often misclassified (e.g. Banglish -> Kannada/Somali)
        # If text is purely Latin/ASCII and short, default to English (or stay on current)
        # unless it's clearly another major language.
        is_latin = all(ord(char) < 128 for char in text.replace(" ", "").replace("?", "").replace("!", "").replace(".", "").replace(",", ""))
        
        try:
            detected = detect(text)
            
            if is_latin:
                # Common misclassifications for Banglish/Short English: 'so', 'id', 'tl', 'cy', 'kn', 'sw'
                # If detected is NOT a major European language, fallback to 'en'
                major_latin_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl']
                if detected not in major_latin_langs:
                     # If confidence is low or it's a random guess, return 'en'
                     return "en"
            
            return detected
        except:
            return "en"

    def _get_voice_for_language(self, lang_code: str, gender: str = None) -> Optional[str]:
        """Returns the best voice ID for the given language and current character gender"""
        current_char = Config.get_current_character()
        # Prioritize passed gender, then character gender, then default to female
        if not gender:
            gender = current_char.gender if current_char else "female"
        
        # Check mapping
        if lang_code in self.LANG_VOICE_MAP:
            voice_name = self.LANG_VOICE_MAP[lang_code].get(gender)
            if voice_name:
                # Find the full profile ID
                # Edge voice IDs are usually "edge_{short_name}"
                target_id = f"edge_{voice_name}"
                if target_id in self.voices:
                    return target_id
                    
        # Fallback: Search all voices for this language
        for vid, v in self.voices.items():
            if v.provider == "edge-tts" and v.language == lang_code and v.gender == gender:
                return vid
                
        return None

    def _process_queue(self):
        """Worker thread to process speech queue sequentially"""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            print("Warning: pythoncom not found. Voice might not work in thread.")
        except Exception as e:
            print(f"COM Init Error: {e}")

        # Initialize engine for this thread
        try:
            # Force SAPI5 on Windows for better compatibility
            engine = pyttsx3.init('sapi5')
        except Exception as e:
            print(f"SAPI5 Init Error: {e}, falling back to default")
            try:
                engine = pyttsx3.init()
            except Exception as e:
                print(f"Engine Init Error: {e}")
                return
        
        # Ensure volume is up
        try:
            engine.setProperty('volume', 1.0)
        except: pass

        # Initialize Pygame Mixer for this thread if needed
        # REMOVED: Pygame mixer caused crashes. Using QMediaPlayer via signals instead.

        while self._is_running:
            try:
                queue_item = self._speech_queue.get(timeout=1)
                metadata = {}
                if isinstance(queue_item, tuple):
                    if len(queue_item) == 3:
                        text, display_text, metadata = queue_item
                    else:
                        text, display_text = queue_item
                else:
                    text, display_text = queue_item, queue_item
                
                print(f"Voice Service processing: {text[:20]}...") # Debug
                
                # Determine Voice
                target_voice_id = self.current_voice_id
                
                # Auto-Language Switching (Only if Strict Mode is OFF)
                if Config.LANGUAGE_MODE == "Auto" and not self.strict_mode:
                    detected_lang = self._detect_language(text)
                    print(f"Detected language: {detected_lang}")
                    
                    # If detected language is different from current voice's language, try to switch
                    current_profile = self.voices.get(self.current_voice_id)
                    if not current_profile or current_profile.language != detected_lang:
                        # Try to find a better voice
                        # Use current profile's gender to ensure consistency (Male/Female Automation)
                        target_gender = current_profile.gender if current_profile else None
                        
                        best_voice = self._get_voice_for_language(detected_lang, gender=target_gender)
                        if best_voice:
                            print(f"Auto-switching voice to {best_voice} for language {detected_lang}")
                            target_voice_id = best_voice
                
                # Get Voice Profile
                current_profile = self.voices.get(target_voice_id)
                
                # Check for Language Mismatch (Critical Fix for "No Audio")
                # If text contains Bangla but voice is English, EdgeTTS fails with "No Audio".
                # We must force-switch to Bangla voice for this specific sentence to ensure it speaks.
                has_bangla = any('\u0980' <= c <= '\u09ff' for c in text)
                current_voice_lang = self.voices.get(target_voice_id).language if self.voices.get(target_voice_id) else "en"
                
                if has_bangla and current_voice_lang != "bn":
                    # Force fallback to Bangla voice
                    # Try to keep gender consistent
                    current_gender = self.voices.get(target_voice_id).gender if self.voices.get(target_voice_id) else "female"
                    fallback_id = "edge_bn-BD-NabanitaNeural" if current_gender == "female" else "edge_bn-BD-PradeepNeural"
                    
                    if fallback_id in self.voices:
                        print(f"VoiceService: Detected Bangla text with English voice. Temporary switch to {fallback_id}")
                        target_voice_id = fallback_id
                        # Update profile reference
                        current_profile = self.voices.get(target_voice_id)

                # Removed early speaking_started.emit() to sync with audio
                
                try:
                    if current_profile and (current_profile.provider == "edge-tts" or current_profile.provider == "edge-tts-preset"):
                        # --- Edge TTS (Online) ---
                        print(f"Speaking via Edge TTS: {current_profile.name}")
                        try:
                            self._speak_edge(text, current_profile.engine_id, current_profile.pitch, current_profile.rate, current_profile.volume, display_text, metadata)
                        except Exception as edge_err:
                            # Log quietly, don't spam console if it's just a language mismatch (handled above, but just in case)
                            print(f"EdgeTTS warning: {str(edge_err)[:50]}... (Retrying)")
                            # Retry with reliable English voice (Aria) to avoid silence
                            # This handles cases where 'Kannada' voice fails on 'Latin' text
                            self._speak_edge(text, "en-US-AriaNeural", display_text=display_text, metadata=metadata)
                            
                    else:
                        # --- System TTS (Offline) ---
                        print(f"Speaking via System TTS: {current_profile.name if current_profile else 'Default'}")
                        if current_profile:
                             try:
                                engine.setProperty('voice', current_profile.engine_id)
                             except: pass
                        
                        # Emit signal for text display for system TTS
                        self.audio_playback_requested.emit("", display_text, metadata) # System TTS handles text display signal but audio is local
                        
                        # Signal metadata ready for UI to trigger emotions (Synchronous)
                        self.speech_metadata_ready.emit(metadata)
                        self.speaking_started.emit()
                        
                        engine.say(text)
                        engine.runAndWait()
                        
                except Exception as e:
                    print(f"TTS Error: {e}")
                    # Fallback to system if edge fails
                    if current_profile and (current_profile.provider == "edge-tts" or current_profile.provider == "edge-tts-preset"):
                         print("Falling back to system voice...")
                         try:
                             self.speech_metadata_ready.emit(metadata)
                             self.speaking_started.emit()
                             engine.say(text)
                             engine.runAndWait()
                         except: pass
                         
                finally:
                    self.speaking_finished.emit()
                    self._speech_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker Error: {e}")
        
        try:
            pythoncom.CoUninitialize()
        except: pass


    def _speak_edge(self, text, voice_name, pitch="+0Hz", rate="+0%", volume="+0%", display_text=None, metadata=None):
        """Helper to generate and play Edge TTS audio"""
        # Create a temporary file
        # We use a fixed temp directory to avoid permission issues
        temp_dir = os.path.join(tempfile.gettempdir(), "specsai_tts")
        os.makedirs(temp_dir, exist_ok=True)
        # Unique filename to avoid locking
        filename = f"speech_{int(time.time())}.mp3"
        output_file = os.path.join(temp_dir, filename)

        async def _generate_and_save():
            communicate = edge_tts.Communicate(text, voice_name, pitch=pitch, rate=rate, volume=volume)
            await communicate.save(output_file)

        try:
            # Run async generation
            asyncio.run(_generate_and_save())
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"EdgeTTS: Playing {output_file}")
                
                # Request playback on main thread
                self._playback_finished_event.clear()
                self.audio_playback_requested.emit(output_file, display_text or text, metadata or {})
                
                # Wait for playback to finish
                # We use a loop with timeout to check for app exit
                while self._is_running:
                     if self._playback_finished_event.wait(timeout=0.5):
                         break
            else:
                 print("EdgeTTS: Generated file is empty or missing.")
                 raise Exception("Empty audio file")

        except Exception as e:
            # print(f"EdgeTTS Error: {e}") # Suppress noisy error
            raise e # Trigger fallback
        finally:
            # Cleanup
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
            except: pass

    # Future: Integration with Coqui / ElevenLabs
    def add_custom_voice(self, profile: VoiceProfile):
        self.voices[profile.id] = profile
