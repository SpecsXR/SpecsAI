# 🌐 Step-by-Step Online System Guide

Apnar "Online System" ready. Ekhon 2 ta kaj korte hobe:
1.  **GitHub Backup:** Jate system kokhono hariye na jay.
2.  **Wireless Brain:** Jate Brain onno computer thekeo Body ke control korte pare.

---

## Part 1: GitHub Backup (Persistence)
*Eita korle apnar AI safe thakbe.*

### Step 1: GitHub e Account Khulun
Jodi na thake, [github.com](https://github.com) e giye signup korun.

### Step 2: Repository Create Korun
1.  Log in korun.
2.  Top-right corner e `+` button e click kore **"New repository"** select korun.
3.  Name din: `SpecsAI`
    *   **Private** select korun (Safety r jonno).
    *   Kisu check korar dorkar nai (README, .gitignore baad din).
    *   **Create repository** click korun.
4.  Abar same vabe arekta banan, Name: `SpecsAI_SOS` (Brain er jonno).

### Step 3: Body (SpecsAI) Upload Korun
Terminal e ei command gula ekta ekta kore copy-paste korun:

```powershell
cd c:\Users\abdur\Desktop\SpecsAI
git remote add origin https://github.com/APNAR_USERNAME/SpecsAI.git
git branch -M main
git push -u origin main
```
*(Note: `APNAR_USERNAME` er jaygay apnar ashol GitHub username ta likhben)*

### Step 4: Brain (SpecsAI_SOS) Upload Korun

```powershell
cd c:\Users\abdur\Desktop\SpecsAI_SOS
git remote add origin https://github.com/APNAR_USERNAME/SpecsAI_SOS.git
git branch -M main
git push -u origin main
```

---

## Part 2: Wireless Brain Connection (Real "Online" Mode)
*Ami system ta update kore diyechi. Ekhon Brain r Body "wire" chara Internet/Network diye kotha bolte pare.*

### Kibhabe Kaj Kore?
- **Body (`SpecsAI`)** ekhon ekta Server (`Port 6000`) on kore rakhe.
- **Brain (`SpecsAI_SOS`)** sei Port e connect kore command pathay.
- Er mane, future e apni **Brain ta Cloud Server e (Online)** rakhte paren, r **Body ta apnar PC te**. Tao kaj korbe!

### Test Korar Niyom:
1.  Prothome **SpecsAI (Body)** run korun (`main.py`).
2.  Tarpor **SpecsAI_SOS (Brain)** folder theke `brain_transmitter.py` run korun.
3.  Dekhben Brain command dicche r Body kotha bolche!

---
*Safe & Connected. Mission Successful.* 🚀
