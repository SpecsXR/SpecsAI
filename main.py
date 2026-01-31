import sys
import ctypes
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

from core.live2d_setup import setup_opengl_format, ensure_live2d
from ui import MainWindow
import traceback
import faulthandler

# Enable fault handler for hard crashes
faulthandler.enable(file=open("crash_log_native.txt", "w"), all_threads=True)

# Global Exception Handler
def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print("CRITICAL ERROR:", error_msg)
    with open("crash_log.txt", "w") as f:
        f.write(error_msg)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # Check for Admin Privileges
    if not is_admin():
        print("Requesting Admin Privileges...")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit() 
        except Exception as e:
            print(f"Failed to gain admin privileges: {e}")
    
    # --- GRAPHICS BACKEND SETUP ---
    # Fix for: "The top-level window is not using the expected graphics API for composition"
    
    # Force OpenGL for the entire application to satisfy both Live2D (OpenGL) and WebEngine (when using OpenGL)
    # This prevents Qt from defaulting to DirectX/Vulkan which causes the "not compatible" error.
    # QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    # Qt6 equivalent for forcing OpenGL RHI
    # QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGLRhi)
    
    # Fix for WebEngine transparency and File Access (for VRM loading)
    # UPDATED: Removed --disable-gpu-compositing to fix low FPS/Stuttering
    # Added --enable-gpu-rasterization --ignore-gpu-blacklist for smooth 3D
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-transparent-visuals --enable-gpu-rasterization --ignore-gpu-blacklist --allow-file-access-from-files --disable-web-security"

    setup_opengl_format() # Sets Compatibility Profile 3.3 (Disabled global default to prevent WebEngine conflicts)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ensure_live2d()
    
    # Scan for available characters
    from core.config import Config
    Config.scan_characters()
    
    print("\n=== Detected Characters ===")
    for char_id, char_config in Config.CHARACTERS.items():
        print(f" - {char_config.name} (ID: {char_id}) Path: {char_config.model_rel_path}")
    print(f"Default Character: {Config.CURRENT_CHARACTER_ID}")
    print("===========================\n")

    window = MainWindow()
    window.show()
    
    print("App running...")
    exit_code = app.exec()
    print(f"App closing with code: {exit_code}")
    sys.exit(exit_code)
