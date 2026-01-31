# SpecsAI Desktop Assistant - Roadmap

> **Project Goal:** An advanced, interactive desktop assistant featuring Live2D/VRM avatars, voice interaction, and a transparent overlay UI.

---

## ✅ Completed Features (Phase 1)
- [x] **Core UI System**
    - Transparent, click-through window (Overlay).
    - Smart Input Masking (Mouse events pass through transparent areas).
    - Messenger-style Chat Widget.
- [x] **Avatar Rendering**
    - **Live2D:** High-performance rendering with `glad` and `OpenGL`.
    - **VRM:** 3D Model support via `Three.js` in `QtWebEngine`.
    - **Interaction:** Head tracking (mouse follow), Lip-sync with speech.
- [x] **Voice & Logic**
    - Text-to-Speech (TTS) integration.
    - Speech-to-Text (STT) integration.
    - Basic Conversation capability.

---

## 🚧 In Progress / Refinement (Phase 2)
- [ ] **Interaction Polish**
    - [x] Fix Mouse Drag/Move issues for VRM.
    - [x] Fix "Box" blocking issues (DWM Transparency).
    - [ ] Smooth transition between models.
- [ ] **Performance Optimization**
    - Reduce CPU/GPU usage for background rendering.
    - Optimize memory usage for VRM loader.

---

## 📅 Future Plans (Phase 3)
- [ ] **Customization**
    - Easy Model importing (Drag & Drop).
    - Theme selection for Chat UI.
- [ ] **Advanced Assistant Features**
    - System Control (Volume, Brightness).
    - App Launching via Voice.
    - Calendar/Reminder integration.

---

*This roadmap tracks the development of the Desktop Assistant interface and core avatar interaction.*
