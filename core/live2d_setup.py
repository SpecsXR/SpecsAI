"""
Live2D import, init, এবং OpenGL (QSurfaceFormat) setup.
এক জায়গায় রাখা যাতে বাকি কোড শুধু এখান থেকে use করে।
"""
import sys

from PySide6.QtGui import QSurfaceFormat

# Live2D import with error handling
try:
    import live2d.v2 as live2d_v2
    import live2d.v3 as live2d_v3
except ImportError as e:
    print(f"Error importing live2d: {e}")
    print("Please install: pip install live2d-py")
    sys.exit(1)


def ensure_live2d():
    """Live2D global init (QApplication create হওয়ার পর কল করতে হবে)।"""
    live2d_v2.init()
    live2d_v3.init()


def setup_opengl_format():
    """
    Live2D shader (GLSL 1.10/1.20) runs on Compatibility Profile.
    We use 3.3 Compatibility to support FBOs (needed for masking) and newer Qt features.
    """
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3) # Upgrade to 3.3 for FBO support
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setAlphaBufferSize(8)
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    # fmt.setSamples(4) # Optional: Anti-aliasing
    QSurfaceFormat.setDefaultFormat(fmt)
