import pyautogui
import os
import platform
import subprocess
import uuid

class AutomationManager:
    """
    Handles OS-level automation tasks.
    """
    def __init__(self):
        # Safety: Fail-safe corner (Top-Left)
        pyautogui.FAILSAFE = True
        # Ensure external storage directory exists on startup
        self.base_path = self._get_storage_directory()

    def get_storage_path(self):
        """Returns the active storage directory path."""
        return self.base_path
        
    def _get_storage_directory(self):
        """
        Determines the external storage directory (C:/SpecsAI Data or D:/SpecsAI Data).
        Creates it if it doesn't exist.
        """
        drives = ["C:\\", "D:\\"]
        target_dir = None

        for drive in drives:
            if os.path.exists(drive):
                try:
                    path = os.path.join(drive, "SpecsAI Data")
                    if not os.path.exists(path):
                        os.makedirs(path)
                    
                    # Test write permission to ensure we can actually use this drive
                    test_file = os.path.join(path, ".test")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    
                    target_dir = path
                    break
                except Exception as e:
                    print(f"Could not use {drive}: {e}")
                    continue
        
        # Fallback to user home if system drives are restricted
        if not target_dir:
            target_dir = os.path.join(os.path.expanduser("~"), "SpecsAI Data")
        
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except OSError:
                # Fallback to Desktop
                target_dir = os.path.join(os.path.expanduser("~\\Desktop"), "SpecsAI Data")
                if not os.path.exists(target_dir):
                     os.makedirs(target_dir, exist_ok=True)
                     
        return target_dir

    def screenshot(self):
        base_dir = self._get_storage_directory()
        screenshot_dir = os.path.join(base_dir, "screenshots")
        
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Use random unique serial number instead of timestamp
        serial = uuid.uuid4().hex[:12].upper()
        filename = f"screenshot_{serial}.png"
        save_path = os.path.join(screenshot_dir, filename)
        
        pyautogui.screenshot(save_path)
        return save_path

    def save_data(self, content: str, filename: str, category: str = "General", mode: str = "w"):
        """
        Saves data to the appropriate category folder in SpecsAI Data.
        """
        base_dir = self._get_storage_directory()
        target_dir = os.path.join(base_dir, category)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        file_path = os.path.join(target_dir, filename)
        
        try:
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
            return file_path
        except Exception as e:
            print(f"Error saving file: {e}")
            return None

    def create_folder(self, folder_name):
        """Creates a custom folder in SpecsAI Data"""
        base_dir = self._get_storage_directory()
        target_dir = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            return target_dir
        return target_dir

    def open_app(self, app_name):
        """Opens an application based on name"""
        system = platform.system()
        
        if system == "Windows":
            # Simple common apps mapping
            apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "chrome": "chrome.exe",
                "explorer": "explorer.exe",
                "cmd": "cmd.exe"
            }
            
            target = apps.get(app_name.lower())
            if target:
                subprocess.Popen(target)
                return True
            else:
                # Try generic start
                try:
                    os.startfile(app_name)
                    return True
                except:
                    return False
        return False

    def type_text(self, text):
        """Types text at current cursor location"""
        pyautogui.write(text, interval=0.05)

    def press_key(self, key):
        """Presses a specific key"""
        pyautogui.press(key)
        
    def minimize_all(self):
        pyautogui.hotkey('win', 'd')

    def volume_up(self):
        pyautogui.press('volumeup')
        pyautogui.press('volumeup') # Do it twice for noticeable change

    def volume_down(self):
        pyautogui.press('volumedown')
        pyautogui.press('volumedown')

    def mute_volume(self):
        pyautogui.press('volumemute')

    def lock_screen(self):
        os.system("rundll32.exe user32.dll,LockWorkStation")

    def sleep_pc(self):
        # Hibernation off usually required for pure sleep, but this works generally
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def shutdown_pc(self):
        # /s = shutdown, /t 5 = 5 seconds delay (to allow cancellation if needed)
        os.system("shutdown /s /t 5")

    def restart_pc(self):
        os.system("shutdown /r /t 5")
        
    def cancel_shutdown(self):
        os.system("shutdown /a")

    # --- File Management & Downloads ---
    def download_file(self, url, dest_path):
        """Downloads a file from a URL to the destination path."""
        import requests
        try:
            print(f"Downloading {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download complete.")
            return True
        except Exception as e:
            print(f"Download Error: {e}")
            return False

    def import_character_package(self, source_path, dest_name=None):
        """
        Imports a character folder or zip to the assets directory.
        Returns the new character directory path.
        """
        import shutil
        import zipfile
        
        # Determine assets path
        # Assuming we are in core/automation/..., assets is ../../assets
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        char_dir = os.path.join(root_dir, "assets", "character", "User")
        
        if not os.path.exists(char_dir):
            os.makedirs(char_dir)
            
        if not dest_name:
            dest_name = os.path.splitext(os.path.basename(source_path))[0]
            
        final_path = os.path.join(char_dir, dest_name)
        
        try:
            if os.path.isdir(source_path):
                # Copy Directory
                if os.path.exists(final_path):
                    shutil.rmtree(final_path)
                shutil.copytree(source_path, final_path)
            elif zipfile.is_zipfile(source_path):
                # Extract Zip
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(final_path)
            
            return final_path
        except Exception as e:
            print(f"Import Error: {e}")
            return None
