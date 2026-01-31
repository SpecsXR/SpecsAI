
import sys
import os

# Mock QSurfaceFormat for headless check
try:
    from PySide6.QtGui import QSurfaceFormat, QGuiApplication
    app = QGuiApplication(sys.argv)
except:
    pass

try:
    import live2d.v3 as live2d_v3
    print("Live2D v3 imported successfully")
    
    live2d_v3.init()
    
    print("\nlive2d.v3 attributes:")
    print(dir(live2d_v3))
    
    print("\nLAppModel attributes:")
    model = live2d_v3.LAppModel()
    print(dir(model))
    
except ImportError:
    print("live2d.v3 not found")
except Exception as e:
    print(f"Error: {e}")
