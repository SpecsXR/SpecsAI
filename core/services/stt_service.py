import speech_recognition as sr
import threading
from PySide6.QtCore import QObject, Signal
from core.config import Config

import concurrent.futures

class STTService(QObject):
    """
    Service for Speech-to-Text (Microphone Input)
    """
    listening_started = Signal()
    listening_ended = Signal()
    text_recognized = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.is_listening = False

    def listen_once(self):
        """Starts a background thread to listen for a single phrase"""
        if self.is_listening:
            return
        
        thread = threading.Thread(target=self._listen_thread)
        thread.daemon = True
        thread.start()

    def _recognize_worker(self, audio, lang):
        """Worker function for parallel recognition"""
        try:
            # show_all=True returns the raw JSON response which includes confidence
            result = self.recognizer.recognize_google(audio, language=lang, show_all=True)
            return (lang, result)
        except Exception:
            return (lang, None)

    def _listen_thread(self):
        self.is_listening = True
        self.listening_started.emit()
        
        try:
            with sr.Microphone() as source:
                # Fast adjustment for ambient noise
                # print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Optimized settings for speed
                self.recognizer.pause_threshold = 0.6 # Detect end of speech faster
                self.recognizer.non_speaking_duration = 0.4
                
                print("Listening...")
                try:
                    # phrase_time_limit=10 to prevent hanging too long
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    print("Listening timed out.")
                    return

            print("Processing Audio...")
            
            text = None
            
            # Smart Auto-Detect Mode (Multi-Language)
            if Config.LANGUAGE_MODE == "Auto":
                # Detect English, Bangla, and Hindi (Common in region)
                target_langs = ["en-US", "bn-BD", "hi-IN"]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {executor.submit(self._recognize_worker, audio, lang): lang for lang in target_langs}
                    
                    results = []
                    # Increased threshold to prevent premature selection of the wrong language
                    # If one language is > 96% confident, we take it. Otherwise we wait for all to compare.
                    high_confidence_threshold = 0.96 
                    
                    try:
                        for future in concurrent.futures.as_completed(futures):
                            lang, res = future.result()
                            if res and isinstance(res, dict) and 'alternative' in res:
                                best = res['alternative'][0]
                                confidence = best.get('confidence', 0.0)
                                transcript = best.get('transcript', "")
                                
                                print(f"Detected {lang}: {transcript} ({confidence})")
                                results.append((confidence, transcript, lang))
                                
                                # Fast Exit: Only if EXTREMELY confident
                                if confidence > high_confidence_threshold:
                                    print(f"Fast Match ({lang}): {confidence}")
                                    text = transcript
                                    executor.shutdown(wait=False) # Try to cancel others
                                    break
                    except Exception as e:
                        print(f"Parallel Recognition Error: {e}")
                    
                    if not text and results:
                        # Sort by confidence
                        results.sort(key=lambda x: x[0], reverse=True)
                        
                        # Preference logic for Mixed usage:
                        # If English is very close to the top result (within 5%), prefer English 
                        # because English commands are often more precise for system control.
                        # But if top result is significantly better, keep it.
                        best_match = results[0]
                        
                        # Check if English is in results but not first
                        english_result = next((r for r in results if r[2] == "en-US"), None)
                        if english_result and english_result != best_match:
                            # If English is within 0.1 (10%) of the winner, use English
                            # This helps with "Banglish" where English words might be detected as Bangla phonetically
                            if best_match[0] - english_result[0] < 0.1:
                                print(f"Preferring English (Confidence {english_result[0]}) over {best_match[2]} ({best_match[0]})")
                                best_match = english_result

                        print(f"Winner: {best_match[2]} ({best_match[0]}) - {best_match[1]}")
                        text = best_match[1]
                    elif not text and not results:
                        raise sr.UnknownValueError()
            
            else:
                # Specific Language Mode
                lang = "en-US"
                if Config.LANGUAGE_MODE == "Bangla":
                    lang = "bn-BD"
                elif Config.LANGUAGE_MODE == "Hindi":
                    lang = "hi-IN"
                
                text = self.recognizer.recognize_google(audio, language=lang)

            print(f"Recognized: {text}")
            
            if text:
                self.text_recognized.emit(text)
            
        except sr.UnknownValueError:
            print("Could not understand audio.")
            self.error_occurred.emit("Could not understand what you said.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            self.error_occurred.emit(f"Network error: {e}")
        except Exception as e:
            print(f"STT Error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.is_listening = False
            self.listening_ended.emit()
