import asyncio
import edge_tts
import pygame
import os
import tempfile
import time

async def test_edge():
    print("Testing Edge TTS generation...")
    text = "Hello, this is a test of the online voice system."
    voice = "en-US-AriaNeural"
    
    temp_dir = os.path.join(tempfile.gettempdir(), "specsai_debug")
    os.makedirs(temp_dir, exist_ok=True)
    output_file = os.path.join(temp_dir, "test.mp3")
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        print(f"File saved to: {output_file}")
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"File size: {size} bytes")
            if size > 0:
                print("Playing with pygame...")
                pygame.mixer.init()
                pygame.mixer.music.load(output_file)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                print("Playback finished.")
                pygame.mixer.quit()
            else:
                print("Error: File is empty")
        else:
            print("Error: File not found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge())
