import webbrowser
import os
import subprocess
import platform
import shutil
import re
import urllib.request
import urllib.parse
import uuid
from core.automation.automation_manager import AutomationManager

# Optional imports for advanced control
try:
    import pyautogui
except ImportError:
    pyautogui = None

class FeatureManager:
    """
    Implements Core Features from ROADMAP.md (Section 3).
    Handles system commands, media control, and productivity tasks.
    """
    def __init__(self):
        self.os_type = platform.system()
        self.automation = AutomationManager()

    def _get_youtube_video_id(self, query):
        """
        Scrapes YouTube search results to find the first video ID.
        Uses standard libraries to avoid heavy dependencies.
        """
        try:
            query_encoded = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={query_encoded}"
            
            # Request with headers to look like a browser
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            
            with urllib.request.urlopen(req) as response:
                html = response.read().decode()
                
            # Regex to find videoId
            # YouTube's initial data usually contains "videoId":"<ID>"
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            
            if video_ids:
                return video_ids[0]
            return None
        except Exception as e:
            print(f"YouTube Search Error: {e}")
            return None

    def search_file(self, query, operation='find'):
        """
        Searches for a file or folder in common user directories.
        Returns the path if found, else None.
        operation: 'find' (show in folder) or 'open' (launch/run)
        """
        # Prioritize likely locations for speed
        search_roots = [
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Pictures"),
            os.path.expanduser("~\\Music"),
            os.path.expanduser("~\\Videos"),
            "D:\\", "E:\\", "F:\\"
        ]
        
        # Directories to skip to avoid hanging/slowness
        skip_dirs = {
            "Windows", "Program Files", "Program Files (x86)", "ProgramData", 
            "AppData", "$RECYCLE.BIN", "System Volume Information"
        }
        
        print(f"Searching for '{query}' with operation '{operation}'...")
        
        for root_dir in search_roots:
            if not os.path.exists(root_dir): continue
            
            # Use os.walk with optimization
            for root, dirs, files in os.walk(root_dir):
                # Prune skip dirs in-place
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
                
                # Check directories (if user asked for a folder)
                for d in dirs:
                    if query.lower() in d.lower():
                        full_path = os.path.join(root, d)
                        # Only return if it's a "good" match (fuzzy logic could be better but strict substring is fast)
                        print(f"Found folder: {full_path}")
                        self.open_file_location(full_path, operation)
                        return f"Found folder: {full_path}"

                # Check files
                for f in files:
                    if query.lower() in f.lower():
                        full_path = os.path.join(root, f)
                        print(f"Found file: {full_path}")
                        self.open_file_location(full_path, operation)
                        return f"Found file: {full_path}"
                        
        return f"Could not find '{query}' in common locations."

    def open_file_location(self, path, operation='find'):
        """
        Opens the file or folder.
        operation='open': Launches the file (Double-click behavior) or opens folder.
        operation='find': Highlights the file in Explorer.
        """
        try:
            if operation == 'open':
                print(f"Launching: {path}")
                os.startfile(path)
            else:
                # Default 'find' behavior
                if os.path.isdir(path):
                    # Open the folder itself
                    os.startfile(path)
                else:
                    # Select the file in explorer
                    subprocess.Popen(f'explorer /select,"{path}"')
        except Exception as e:
            print(f"Error opening location: {e}")

    def execute_command(self, text):
        """
        Parses text and executes PC control features.
        Returns a response string if a command was executed, else None.
        """
        text = text.lower().strip()
        print(f"[FeatureManager] Processing: {text}")

        # --- 0. Fuzzy/LLM Command Parsing (Priority) ---
        # If the input is a direct command from [EXECUTE: ...] tag
        if text.startswith("open "):
            target = text.replace("open ", "").strip()
            
            # 1. Try Known Apps Map
            known_apps = {
                "chrome": "chrome",
                "google chrome": "chrome",
                "notepad": "notepad",
                "calculator": "calc",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "cmd": "cmd",
                "terminal": "wt",
                "explorer": "explorer",
                "settings": "ms-settings:",
                "vlc": "vlc",
                "spotify": "spotify"
            }
            
            # Check exact or partial match in known apps
            for key, cmd in known_apps.items():
                if key in target:
                    try:
                        os.startfile(cmd)
                        return f"Opening {key}..."
                    except:
                        pass # Continue to search

            # 2. Try generic start (if it works instantly)
            # This is tricky because 'start xyz' never fails in python Popen.
            # We skip this for random names to avoid error popups.
            
            # 3. Smart Search & Open (The "Chipay Chapay" Feature)
            # If it looks like a folder/file name, search for it.
            # ACTION: 'open' -> Launch it!
            search_result = self.search_file(target, operation='open')
            if "Found" in search_result:
                return search_result.replace("Found", "Launched")
            else:
                # Last Resort: Try to run it as a command
                try:
                    os.startfile(target)
                    return f"Attempting to launch {target}..."
                except:
                    return f"Could not find or open {target}."

        if text.startswith("search for ") or text.startswith("find "):
            query = text.replace("search for ", "").replace("find ", "").strip()
            # ACTION: 'find' -> Show in folder
            return self.search_file(query, operation='find')

        if "system info" in text:
            import platform
            return f"System: {platform.system()} {platform.release()}, Node: {platform.node()}"

        # Helper for multi-language keywords
        def match_any(keywords, text):
            return any(k in text for k in keywords)

        # Bangla/English Keywords
        # Open: open, khulo, chalu koro, start, launch, খুলুন, ওপেন
        kw_open = ["open", "start", "launch", "khulo", "chalu koro", "on koro", "khule dao", "open koro", "খুলুন", "চালু করুন", "ওপেন"]
        # Close: close, bondho koro, off koro, বন্ধ করুন
        kw_close = ["close", "exit", "quit", "bondho koro", "off koro", "bad dao", "close koro", "বন্ধ করুন"]
        # Play: play, bajao, chalao, শুনান, বাজান
        kw_play = ["play", "bajao", "chalao", "shunao", "start", "listen", "শুনান", "বাজান", "প্লে", "play koro"]
        # Stop: stop, thamao, pause, থামান
        kw_stop = ["stop", "pause", "thamao", "darao", "wait", "theme jao", "থামান", "দাঁড়ান", "stop koro"]
        # Next: next, porer, samne, skip, পরের
        kw_next = ["next", "skip", "porer", "samne", "porer ta", "next ta", "পরের"]
        # Prev: previous, back, ager, piche, আগের
        kw_prev = ["previous", "back", "ager", "piche", "ager ta", "previous ta", "আগের"]
        # Volume
        kw_vol_up = ["volume up", "increase volume", "sound barao", "awaj barao", "sound barie dao", "volume barie dao", "ভলিউম বাড়ান"]
        kw_vol_down = ["volume down", "decrease volume", "sound komao", "awaj komao", "sound komie dao", "volume komie dao", "ভলিউম কমান"]
        kw_mute = ["mute", "silent", "chup", "sound off", "awaj bondho", "mute koro", "মিউট"]


        # --- A. Multimedia & Entertainment ---
        
        # 1. Advanced YouTube Play (Direct Video)
        # Matches: "play [song] on youtube", "play [song]" (if context implies), "can you play [song]"
        # Bangla: "youtube e [song] bajao", "[song] chalao"
        
        yt_match = re.search(r'(?:play|start|listen to|bajao|chalao|shunao|বাজান|চালান)\s+(?:song\s+|video\s+|gan\s+)?(.+?)(?:\s+(?:on|in)\s+youtube)?$', text)
        
        if "youtube" in text and match_any(kw_open, text) and not yt_match:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube for you."
            
        if yt_match and ("youtube" in text or match_any(kw_play, text)):
            query = yt_match.group(1).strip()
            # If query is just "youtube", ignore (handled by open youtube)
            if query == "youtube": 
                webbrowser.open("https://www.youtube.com")
                return "Opening YouTube."
                
            # Try to find video ID for direct play
            video_id = self._get_youtube_video_id(query)
            
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
                return f"Playing {query} on YouTube."
            else:
                # Fallback to search
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return f"Searching for {query} on YouTube."

        # 2. Global Media Controls (Play/Pause/Next/Prev)
        if match_any(kw_stop, text) or "stop music" in text or "stop video" in text:
            if pyautogui:
                pyautogui.press("playpause")
                return "Paused media."
        
        if "resume" in text or (match_any(kw_play, text) and len(text) < 15): # e.g. just "play" or "bajao"
            if pyautogui:
                pyautogui.press("playpause")
                return "Resumed media."

        # --- B. System Automation & Productivity (High Tech) ---
        
        # 1. Open Applications
        if "excel" in text and match_any(kw_open, text):
            try:
                os.startfile("excel")
                return "Opening Microsoft Excel."
            except Exception as e:
                return f"Failed to open Excel: {e}"

        if "word" in text and match_any(kw_open, text):
            try:
                os.startfile("winword")
                return "Opening Microsoft Word."
            except:
                return "Could not open Word."
                
        if "notepad" in text and match_any(kw_open, text):
            try:
                os.startfile("notepad")
                return "Opening Notepad."
            except:
                return "Could not open Notepad."

        if "chrome" in text and match_any(kw_open, text):
            try:
                os.startfile("chrome")
                return "Opening Google Chrome."
            except:
                return "Could not open Chrome."

        # 2. Typing / Writing (Simple Automation)
        # Matches: "write [text]", "type [text]", "[text] likho"
        write_match = re.search(r'(?:write|type|likho|lekho|লিখুন|লেখো)\s+(.+)', text)
        if write_match and pyautogui:
            content = write_match.group(1).strip()
            return f"I would type '{content}' but I need to be sure where to type. Please click the field first."
            
        # Media Controls (Skipped previously)
        if match_any(kw_next, text) or "next song" in text:
            if pyautogui:
                pyautogui.press("nexttrack")
                return "Skipped to next track."

        if match_any(kw_prev, text) or "previous song" in text:
            if pyautogui:
                pyautogui.press("prevtrack")
                return "Playing previous track."

        # 3. Spotify
        if "spotify" in text and match_any(kw_open, text):
            if self.os_type == "Windows":
                try:
                    os.system("start spotify:")
                    return "Opening Spotify."
                except:
                    webbrowser.open("https://open.spotify.com")
                    return "Opening Spotify Web Player."
        
        # 4. WhatsApp
        if "whatsapp" in text and match_any(kw_open, text):
            if self.os_type == "Windows":
                try:
                    os.system("start whatsapp:")
                    return "Opening WhatsApp."
                except:
                    webbrowser.open("https://web.whatsapp.com")
                    return "Opening WhatsApp Web."
            else:
                 webbrowser.open("https://web.whatsapp.com")
                 return "Opening WhatsApp Web."

        # --- B. System & Desktop Control ---
        if "shutdown" in text or "turn off" in text or "bondho koro" in text or "off koro" in text:
            self.automation.shutdown_pc()
            return "Shutting down system in 5 seconds. Say 'cancel' to stop."
            
        if "restart" in text or "reboot" in text or "abar chalu" in text or "restart koro" in text:
            self.automation.restart_pc()
            return "Restarting system in 5 seconds. Say 'cancel' to stop."
            
        if "sleep" in text and ("pc" in text or "mode" in text or "ghum" in text):
            self.automation.sleep_pc()
            return "Going to sleep mode."

        if "lock" in text and ("pc" in text or "screen" in text or "tala" in text):
            self.automation.lock_screen()
            return "Locking screen."

        if "cancel" in text or "bad dao" in text:
            self.automation.cancel_shutdown()
            return "Cancelled system power action."
        
        if "screenshot" in text or "capture screen" in text or "chobi tolo" in text or "স্ক্রিনশট" in text:
            path = self.automation.screenshot()
            return f"Screenshot saved to {path}"

        # --- Universal Smart Storage (Infinite Data Types) ---
        # Handles ANY user data type: "save [category] [content]"
        # Examples: "save poem Roses are red", "save budget 500 dollars", "save recipe for cake..."
        
        # 1. Clipboard Variant: "save clipboard as [category]"
        if "clipboard" in text or "copied text" in text or "copy text" in text:
            # Extract category if possible
            category_match = re.search(r'(?:as|to|in)\s+(?:a\s+|an\s+)?([\w\s]+)', text, re.IGNORECASE)
            category = category_match.group(1).strip().title() if category_match else "Clipboard"
            
            try:
                content = subprocess.check_output(["powershell", "Get-Clipboard"], text=True).strip()
                if content:
                    serial = uuid.uuid4().hex[:12].upper()
                    filename = f"{category}_{serial}.txt"
                    path = self.automation.save_data(category, filename, content)
                    return f"Saved copied text to {path}"
                else:
                    return "Clipboard is empty."
            except:
                return "Could not access clipboard."

        # 3. Create Folder (Multi-language) - PRIORITY CHECK
        # English: "create folder named X", "create a folder named X"
        create_folder_match = re.search(r'(?:create|make|banao|toiri koro|তৈরি করুন)\s+(?:a\s+|an\s+|the\s+|ekta\s+)?(?:folder|directory|file)\s+(?:named|called|jar nam|nam|নাম)?\s+([\w\s]+)', text, re.IGNORECASE)
        
        # Bangla Suffix: "X namer folder banao"
        if not create_folder_match:
             create_folder_match = re.search(r'([\w\s]+)\s+(?:namer|named)\s+(?:folder|directory)\s+(?:create|banao|koro|khulo)', text, re.IGNORECASE)

        # Variation: "Folder create koro named X" (Banglish Mixed)
        if not create_folder_match:
            create_folder_match = re.search(r'(?:folder|directory)\s+(?:create|make|banao|koro|create koro|toiri koro)\s+(?:named|called|jar nam|nam)\s+([\w\s]+)', text, re.IGNORECASE)

        if create_folder_match:
            folder_name = create_folder_match.group(1).strip()
            path = self.automation.create_folder(folder_name)
            return f"Folder created at {path}"

        # 2. Universal Explicit Content (Multi-language)
        # Matches: "save [category] named [name] [content]" OR "save [category] [content]"
        smart_save_match = None
        
        # Priority 1: Named Content ("save python script named test.py with content print('hi')")
        # Bangla: "save koro [category] jar nam [name] jate thakbe [content]"
        smart_save_match = re.search(r'(?:save|create|write|store|rakho|songrokkhon)\s+(?:koro|korun)?\s*(?:a\s+|an\s+|ekta\s+)?(?P<category>[\w\s]+?)\s+(?:named|called|titled|jar nam|nam|namer)\s+(?P<name>[\w\s\.]+)\s+(?:with content|saying|:|->|jate thakbe|ja hobe)\s*(?P<content>.+)', text, re.IGNORECASE)
        
        # Priority 2: Simple Content ("save poem Roses are red")
        if not smart_save_match:
             # We assume the word after 'save' is the category
             smart_save_match = re.search(r'(?:save|create|write|store|rakho|songrokkhon)\s+(?:koro|korun)?\s*(?:a\s+|an\s+|ekta\s+)?(?P<category>[\w]+)\s+(?:with content|saying|:|->|jate thakbe|ja hobe)?\s*(?P<content>.+)', text, re.IGNORECASE)

        if smart_save_match:
            category = smart_save_match.group("category").strip().title()
            content = smart_save_match.group("content").strip()
            name = smart_save_match.group("name").strip() if "name" in smart_save_match.groupdict() and smart_save_match.group("name") else None
            
            # Filter out system commands
            if category.lower() in ["screenshot", "volume", "shutdown", "restart", "folder", "directory"]:
                pass # Let specific handlers take it
            else:
                # Generate Filename if not provided
                if not name:
                    serial = uuid.uuid4().hex[:12].upper()
                    ext = ".txt"
                    if category.lower() in ["python", "script", "code"]: ext = ".py"
                    if category.lower() in ["html", "webpage"]: ext = ".html"
                    if category.lower() in ["json", "data"]: ext = ".json"
                    name = f"{category}_{serial}{ext}"
                
                path = self.automation.save_data(category, name, content)
                return f"Saved {category} to {path}"

        # 4. Save Conversation
        if "save conversation" in text or "save chat" in text:
             from datetime import datetime
             # Use Date for Log, but filename can be serial if preferred. 
             # Logs usually need date. But user said "all data types".
             # Let's use serial for filename to be strict.
             serial = uuid.uuid4().hex[:12].upper()
             filename = f"chat_log_{serial}.txt"
             log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] User requested save.\n"
             path = self.automation.save_data("Conversations", filename, log_entry, mode="a")
             return f"Conversation log updated at {path}"

        if match_any(kw_vol_up, text):
            # Increase by 6 steps (3 calls)
            for _ in range(3):
                self.automation.volume_up()
            return "Increasing volume."
            
        if match_any(kw_vol_down, text):
            # Decrease by 6 steps
            for _ in range(3):
                self.automation.volume_down()
            return "Decreasing volume."
                
        if match_any(kw_mute, text):
            self.automation.mute_volume()
            return "Muted system volume."

        # --- C. Productivity ---
        if "notepad" in text and "open" in text:
            subprocess.Popen("notepad.exe")
            return "Opening Notepad."

        if "explorer" in text or "my computer" in text or "this pc" in text:
            if self.os_type == "Windows":
                os.system("explorer")
                return "Opening File Explorer."

        if "vs code" in text or "code" in text:
            try:
                if self.os_type == "Windows":
                    os.system("code")
                else:
                    subprocess.Popen(["code"])
                return "Opening Visual Studio Code."
            except:
                return "I couldn't find VS Code."

        if "time" in text or "date" in text:
            now = datetime.now()
            return f"It is currently {now.strftime('%I:%M %p on %A, %B %d')}."
        
        # --- D. General Search / Wikipedia ---
        if "search" in text or "google" in text:
            query = text.replace("search", "").replace("google", "").replace("for", "").strip()
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching Google for {query}."
                
        # Simple "Who is / What is" handler (simulated intelligence)
        if text.startswith("who is ") or text.startswith("what is "):
            query = text
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"I found some information about '{query}' for you."

        # --- E. Fuzzy Logic / LLM Fallback (Ulta Palta Command Handler) ---
        # If no regex matched, return None so the Main Window can send it to the LLM.
        # But if we want to catch "intent" here, we would need the LLM engine.
        # Since FeatureManager is standalone, we return None. 
        # The Main Window will then ask the LLM: "User said X, execute command if needed."
        
        return None
