
import os
import shutil

source = os.path.join("temp_live2d", "Samples", "Resources", "Hiyori")
destination_parent = os.path.join("assets", "character", "Specia")
destination = os.path.join(destination_parent, "Momose")

# Create parent dir
os.makedirs(destination_parent, exist_ok=True)

# Remove destination if exists
if os.path.exists(destination):
    print(f"Removing existing {destination}")
    shutil.rmtree(destination)

# Move
try:
    if os.path.exists(source):
        shutil.move(source, destination)
        print(f"Moved Hiyori to {destination}")
    else:
        print(f"Source not found: {source}")
except Exception as e:
    print(f"Error moving: {e}")

# Cleanup temp
try:
    if os.path.exists("temp_live2d"):
        # Helper to remove read-only files (git files often are)
        def on_rm_error(func, path, exc_info):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
            
        shutil.rmtree("temp_live2d", onerror=on_rm_error)
        print("Cleaned up temp_live2d")
except Exception as e:
    print(f"Error cleaning up: {e}")
