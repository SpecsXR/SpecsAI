import json
import os

# Base directory for motions
motion_dir = r"c:\Users\abdur\Desktop\SpecsAI\assets\character\Spacia\shoujo_a\shoujo_a\motions"

def create_curve(target, id, segments):
    """
    Creates a curve dictionary.
    Segments format: [time, value, type, time, value, type, ...]
    But simpler for our generator: just points and we assume linear or bezier.
    Live2D Motion3 Curve Format:
    Target: "Parameter"
    Id: "ParamAngleX"
    Segments: [
       0, 0, 1, (start_time, start_val, segment_type)
       0.33, 10, 
       0.66, 10, 
       1.0, 0   (end_time, end_val)
    ]
    Segment Types: 0=Linear, 1=Bezier, 2=Stepped, 3=InverseStepped
    Standard Bezier segment: time, value, 1, control1_time, control1_val, control2_time, control2_val, end_time, end_val
    Standard Linear segment: time, value, 0, end_time, end_val
    """
    return {
        "Target": target,
        "Id": id,
        "Segments": segments
    }

def generate_motion_file(filename, duration, fps, curves, meta_name):
    data = {
        "Version": 3,
        "Meta": {
            "Duration": duration,
            "Fps": fps,
            "Loop": True,
            "AreBeziersRestricted": True,
            "CurveCount": len(curves),
            "TotalSegmentCount": 100, # Approximate
            "TotalPointCount": 100, # Approximate
            "UserDataCount": 0,
            "TotalUserDataSize": 0
        },
        "Curves": curves
    }
    
    filepath = os.path.join(motion_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Created {filename}")

# --- 1. IDLE MOTION (Subtle Breathing & Sway) ---
# Duration: 4.0s
idle_curves = [
    # Breath (Looping 0 -> 1 -> 0)
    create_curve("Parameter", "ParamBreath", [
        0, 0, 1, 
        1.0, 0.5, 2.0, 1.0, 2.0, 1.0, # Bezier to Peak
        1, 
        3.0, 0.5, 4.0, 0.0, 4.0, 0.0  # Bezier to Zero
    ]),
    # Subtle Head Sway (ParamAngleX) - Very slight left/right
    create_curve("Parameter", "ParamAngleX", [
        0, 0, 1,
        1.0, 2, 2.0, 0, 2.0, 0,
        1,
        3.0, -2, 4.0, 0, 4.0, 0
    ]),
     # Subtle Eye Blink (ParamEyeLOpen/R) - Blink at 3.5s
    create_curve("Parameter", "ParamEyeLOpen", [
        0, 1, 0, 3.4, 1, # Linear hold
        1, 3.5, 0, 3.6, 0, 3.6, 0, # Blink Close
        1, 3.7, 1, 3.8, 1, 4.0, 1 # Open
    ]),
    create_curve("Parameter", "ParamEyeROpen", [
        0, 1, 0, 3.4, 1,
        1, 3.5, 0, 3.6, 0, 3.6, 0,
        1, 3.7, 1, 3.8, 1, 4.0, 1
    ])
]
generate_motion_file("idle.motion3.json", 4.0, 30.0, idle_curves, "Idle")


# --- 2. NOD MOTION (Yes/Agree) ---
# Duration: 1.5s
# Head nods down twice
nod_curves = [
    create_curve("Parameter", "ParamAngleY", [
        0, 0, 1,
        0.2, -20, 0.4, -20, 0.4, -20, # Down
        1,
        0.5, 0, 0.6, 0, 0.6, 0,       # Up
        1,
        0.8, -20, 1.0, -20, 1.0, -20, # Down
        1,
        1.2, 0, 1.5, 0, 1.5, 0        # Up
    ]),
    # Eyes Close slightly during nod (Happy look)
    create_curve("Parameter", "ParamEyeLOpen", [0, 1, 1, 0.2, 0.8, 1.5, 1, 1.5, 1]),
    create_curve("Parameter", "ParamEyeROpen", [0, 1, 1, 0.2, 0.8, 1.5, 1, 1.5, 1])
]
generate_motion_file("nod.motion3.json", 1.5, 30.0, nod_curves, "Nod")


# --- 3. SHAKE MOTION (No/Deny) ---
# Duration: 1.5s
# Head shakes left/right twice
shake_curves = [
    create_curve("Parameter", "ParamAngleX", [
        0, 0, 1,
        0.2, 20, 0.3, 20, 0.3, 20, # Right
        1,
        0.5, -20, 0.7, -20, 0.7, -20, # Left
        1,
        0.9, 20, 1.1, 20, 1.1, 20, # Right
        1,
        1.3, 0, 1.5, 0, 1.5, 0 # Center
    ]),
    # Brow Frown (if supported) - ParamBrowLY
    create_curve("Parameter", "ParamBrowLY", [0, 0, 0, 1.5, -0.5]),
    create_curve("Parameter", "ParamBrowRY", [0, 0, 0, 1.5, -0.5])
]
generate_motion_file("shake.motion3.json", 1.5, 30.0, shake_curves, "Shake")


# --- 4. TAP/SURPRISE MOTION ---
# Duration: 1.0s
# Quick jump/shock
tap_curves = [
    # Body Jump (ParamBodyAngleY / ParamAngleZ shock)
    create_curve("Parameter", "ParamAngleY", [
        0, 0, 1, 0.1, 10, 0.2, 10, 0.2, 10, 1, 0.5, 0, 1.0, 0, 1.0, 0
    ]),
    # Eyes Wide Open
    create_curve("Parameter", "ParamEyeLOpen", [0, 1, 1, 0.1, 1.5, 0.5, 1.5, 1.0, 1]), # 1.5 might be clamped but shows intent
    create_curve("Parameter", "ParamEyeROpen", [0, 1, 1, 0.1, 1.5, 0.5, 1.5, 1.0, 1]),
    # Mouth Open
    create_curve("Parameter", "ParamMouthOpenY", [0, 0, 1, 0.1, 1, 0.3, 1, 1.0, 0])
]
generate_motion_file("tap.motion3.json", 1.0, 30.0, tap_curves, "Tap")


# --- 5. WAVE (FlickLeft) ---
# Assuming ParamBodyAngleZ for sway or ParamAngleZ
wave_curves = [
    create_curve("Parameter", "ParamAngleZ", [
        0, 0, 1, 
        0.25, 15, 0.5, 15, 0.5, 15, 
        1, 
        0.75, -15, 1.0, -15, 1.0, -15,
        1,
        1.25, 0, 1.5, 0, 1.5, 0
    ]),
    create_curve("Parameter", "ParamMouthOpenY", [0, 0, 0, 1.5, 0.3]) # Smile/Talk
]
generate_motion_file("wave.motion3.json", 1.5, 30.0, wave_curves, "Wave")

print("All motions created successfully!")
