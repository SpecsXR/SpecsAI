import pyttsx3
import sys

try:
    print("Initializing pyttsx3 with sapi5...")
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    print(f"Found {len(voices)} voices.")
    for v in voices:
        print(f" - {v.name}")
    
    print("Speaking test...")
    engine.say("Testing voice system.")
    engine.runAndWait()
    print("Done.")
except Exception as e:
    print(f"Error: {e}")
