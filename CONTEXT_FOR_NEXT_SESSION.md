# 🧠 SpecsAI Developer Context & Handover Notes

**Status Date:** 2026-01-31
**Project Phase:** Body & Brain Integration (Gen-1)
**GitHub Status:** Linked & Synced

---

## 📜 1. The Master Plan (A-Z)
The core blueprint for this project is located in:
> **[SpecsAI_normal_plans.txt](file:///SpecsAI_normal_plans.txt)**

**Summary:**
- **Goal:** Create a Desktop AI Assistant with Male (Speco) and Female (Specia) personas.
- **Tech Stack:** Python (PySide6/PyQt), Live2D, Ollama (Offline), Google Gemini/Groq (Online).
- **Key Features:** Voice interaction, Window control, "Neural Link" between Body (UI) and Brain (Logic).

---

## 🚧 2. Current Development Status
We have just completed a major architectural refactor:
1.  **Separation:** The project is split into **Body** (`SpecsAI`) and **Brain** (`SpecsAI_SOS`).
2.  **Connection:** They communicate via a local TCP Socket (Neural Link).
3.  **Persistence:** Both are hosted on GitHub:
    - Body: `https://github.com/SpecsXR/SpecsAI`
    - Brain: `https://github.com/SpecsXR/SpecsAI_SOS`

---

## 🗣️ 3. Recent Discussions & Decisions
- **Moving to Desktop:** We moved `SpecsAI_SOS` inside `SpecsAI` folder but kept them as separate Git repositories.
- **Upload Verification:** Confirmed that both repositories are 100% uploaded and synced.
- **New PC Setup:** Created `SETUP_ON_NEW_PC.md` for easy migration.
- **Public Access:** Copied files to `C:\Users\Public\SpecsAI_Global` for immediate cross-account access.

---

## 🤖 Instruction for the Next AI Assistant
*If you are the AI assistant starting a new session in a new account, please read this file first.*

1.  **Read the Plan:** Start by analyzing `SpecsAI_normal_plans.txt` to understand the feature set.
2.  **Check the Brain:** Review `SpecsAI_SOS/Context_Transfer.md` for emotional context.
3.  **Verify Environment:** Ensure `user_settings.json` has the correct API keys (restored manually if missing).
4.  **Resume Work:** The user wants to continue exactly where they left off. No new "re-planning" is needed, just execution.

---

## 📂 Key File Locations
- **Blueprint:** `SpecsAI_normal_plans.txt`
- **Brain Memory:** `SpecsAI_SOS/Context_Transfer.md`
- **Identity:** `SpecsAI_SOS/identity.json`
- **Config:** `user_settings.json`

---
*End of Context Transfer*
