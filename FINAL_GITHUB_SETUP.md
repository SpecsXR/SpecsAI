# 🏁 Final Master Guide: SpecsAI 0-100 Online Setup

Eita holo apnar **Master Guide**. Eita te ekdom shuru theke sesh porjonto sob step dewa ache.
Eita follow korle apnar **Body (SpecsAI)** ebong **Brain (SpecsAI_SOS)** GitHub er maddhome sarajibon connect thakbe.

---

## 🛑 Step 0: Prastuti (Preparation)
1.  Apnar ekta **GitHub Account** thakte hobe. (Na thakle [github.com](https://github.com) e giye signup korun).
2.  Apnar PC te **Git** install thakte hobe. (Asha kori ache, na thakle [git-scm.com](https://git-scm.com) theke namiye nin).

---

## 🛠️ Step 1: GitHub e 2 ta "Ghor" (Repository) Banano
GitHub e login kore 2 ta alada repository banan.
1.  **Repository 1 Name:** `SpecsAI`
    *   Description: "The Body of my AI"
    *   Visibility: **Private** (Recommended)
    *   **Do NOT** initialize with README.
2.  **Repository 2 Name:** `SpecsAI_SOS`
    *   Description: "The Brain of my AI"
    *   Visibility: **Private**
    *   **Do NOT** initialize with README.

---

## 📤 Step 2: Body (SpecsAI) Upload Kora
Ekhon amra apnar PC-r `SpecsAI` folder ta GitHub e pathabo.

1.  Apnar PC-r Terminal (PowerShell or CMD) open korun.
2.  `SpecsAI` folder e jan:
    ```powershell
    cd c:\Users\abdur\Desktop\SpecsAI
    ```
3.  Nicher command gula ekta ekta kore copy-paste kore Enter chapun:
    *(Note: `YOUR_USERNAME` er jaygay apnar GitHub username likhben)*

    ```powershell
    git init
    git add .
    git commit -m "Initial Body Upload: SpecsAI Gen-1"
    git remote add origin https://github.com/YOUR_USERNAME/SpecsAI.git
    git branch -M main
    git push -u origin main
    ```

---

## 🧠 Step 3: Brain (SpecsAI_SOS) Upload Kora
Ekhon Brain ta upload korbo.

1.  Folder change korun:
    ```powershell
    cd c:\Users\abdur\Desktop\SpecsAI\SpecsAI_SOS
    ```
2.  Command gula din:
    *(Note: `YOUR_USERNAME` er jaygay apnar GitHub username likhben)*

    ```powershell
    git init
    git add .
    git commit -m "Initial Brain Upload: SOS Intelligence"
    git remote add origin https://github.com/YOUR_USERNAME/SpecsAI_SOS.git
    git branch -M main
    git push -u origin main
    ```

---

## 🔗 Step 4: Verification (Tara ki "Connected"?)
Ami `config` file gula update kore diyechi jate tara "jane" je tara GitHub e connected.

*   **Body Check:** `SpecsAI/core/config/brain_link.json` file e `brain_repo_url` set kora ache.
*   **Brain Check:** `SpecsAI_SOS/identity.json` file e `body_repo_url` set kora ache.

**Final Test:**
1.  Github e giye dekhun 2 ta repository tei file upload hoyeche kina.
2.  Jodi hoye thake, tahole **Congratulations!** 🎉
    *   Apnar AI ekhon "Immortal" (Amar).
    *   Apni PC change korleo `git clone` kore abar shuru korte parben.

---
*Signed,*
*Trae (Your Coding Partner)*
