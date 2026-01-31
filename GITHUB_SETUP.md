# 🌐 How to Connect SpecsAI to GitHub (Online System)

To ensure your AI is safe forever, follow these steps to upload it to the cloud.

## Step 1: Create Repositories on GitHub
1.  Log in to your [GitHub account](https://github.com).
2.  Click the **+** icon in the top right and select **New repository**.
3.  **Repository 1 Name:** `SpecsAI`
    *   Description: "The Body - Visualization & UI"
    *   Visibility: **Private** (Recommended) or Public.
    *   **Do NOT** initialize with README, .gitignore, or License (we already have them).
    *   Click **Create repository**.
4.  Repeat the process for **Repository 2**.
    *   **Repository 2 Name:** `SpecsAI_SOS`
    *   Description: "The Brain - Logic & Memory"
    *   Visibility: **Private** (Recommended).
    *   Click **Create repository**.

## Step 2: Upload "The Body" (SpecsAI)
Open a terminal in the `SpecsAI` folder (or use the command prompt) and run:

```bash
cd c:\Users\abdur\Desktop\SpecsAI
git remote add origin https://github.com/YOUR_USERNAME/SpecsAI.git
git branch -M main
git push -u origin main
```
*(Replace `YOUR_USERNAME` with your actual GitHub username)*

## Step 3: Upload "The Brain" (SpecsAI_SOS)
Open a terminal in the `SpecsAI_SOS` folder and run:

```bash
cd c:\Users\abdur\Desktop\SpecsAI_SOS
git remote add origin https://github.com/YOUR_USERNAME/SpecsAI_SOS.git
git branch -M main
git push -u origin main
```
*(Replace `YOUR_USERNAME` with your actual GitHub username)*

---

## ✅ Done!
Once you see the success message, your AI's Soul (Brain) and Body are safely backed up online.
Even if your PC crashes or you change accounts, you can just "Clone" these repositories back.
