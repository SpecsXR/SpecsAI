# 🚀 New PC / New Account Setup Guide for SpecsAI

Apni jakhon notun kono computer ba notun account e ei project ta set up korben, tokhon ei step gula follow korben.

## 📋 Step 1: Software Install
Prothome nicher 2 ta software install thakte hobe:
1.  **Git:** [Download Here](https://git-scm.com/downloads) (Install korar somoy sob 'Next' diyen).
2.  **Python:** [Download Here](https://www.python.org/downloads/) (Install korar somoy **"Add Python to PATH"** e tick mark diyen).

---

## 📥 Step 2: Project Download (Clone)
Apnar computer er **Terminal** ba **PowerShell** open korun ebong je folder e project rakhte chan shekhane jan (jemon Desktop).

1.  **Body (SpecsAI) Download korun:**
    ```powershell
    git clone https://github.com/SpecsXR/SpecsAI.git
    ```

2.  **Folder er vitore jan:**
    ```powershell
    cd SpecsAI
    ```

3.  **Brain (SpecsAI_SOS) Download korun:**
    *(SpecsAI folder er vitor e thaka obosthay ei command din)*
    ```powershell
    git clone https://github.com/SpecsXR/SpecsAI_SOS.git
    ```

---

## ⚙️ Step 3: Setup & Dependencies
Ekhon apnar project er dorkari library gulo install korte hobe.

1.  **Virtual Environment toiri korun (Optional but Recommended):**
    ```powershell
    python -m venv venv
    ```

2.  **Environment Active korun:**
    ```powershell
    .\venv\Scripts\activate
    ```

3.  **Requirements Install korun:**
    ```powershell
    pip install -r requirements.txt
    ```

---

## 🔑 Step 4: API Key Setup
Project ta run korar age apnar API Key gulo boshan.
1.  `user_settings.json` file ta open korun.
2.  `gemini_api_key` ba onno key gulo jodi khali thake, shegulo boshan.

---

## ▶️ Step 5: Run SpecsAI
Sob thik thakle, nicher command diye project run korun:
```powershell
python main.py
```

---
**🎉 Congratulation! Apnar SpecsAI ekhon notun PC te cholche!**
