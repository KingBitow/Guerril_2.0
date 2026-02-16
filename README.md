# Guerrilla Mail - Code & Link Extractor

A modern cyberpunk-themed GUI application for automatically extracting verification codes and links from temporary emails using Guerrilla Mail API.

![Interface Preview](screenshot.png)

## What It Does

1. **Generates** a temporary email address
2. **Monitors** incoming emails automatically
3. **Extracts** verification codes (4-6 digits)
4. **Finds** verification links (confirm/verify/activate URLs)
5. **Opens** links in your browser with one click

Perfect for signing up on websites without using your real email.

---

## Requirements

You need **Python 3.7 or higher** installed on your system.

### Install Python

| Operating System | Download Link |
|-----------------|---------------|
| **Windows** | https://python.org/downloads (Check "Add Python to PATH" during install) |
| **Mac** | https://python.org/downloads or `brew install python3` |
| **Linux** | Usually pre-installed. If not: `sudo apt install python3 python3-pip` |

---

## Installation

### Step 1: Download the Project
```bash
git clone https://github.com/KingBitow/Guerrilla.git
cd Guerrilla

Or download ZIP and extract it.
Step 2: Install Required Libraries
Open terminal/command prompt in the project folder and run:

## pip install requests pyperclip

Note: tkinter is included with Python by default.
How to Use
1. Start the Program
bash
Copy
python guerrilla.py

2. Generate Email
Click the RUN toggle switch
App generates a temporary email address
Email appears in the "EMAIL ADDRESS" box
3. Copy Email
Click the 📋 button to copy the email
Paste it into any website signup form
4. Wait for Verification
App checks for new emails every 5 seconds
When email arrives, it automatically extracts:
Verification codes → Shows in "VERIFICATION CODE" box
Verification links → Shows in "VERIFICATION LINKS" box
** 5. Verify
For codes: Copy and paste into the website
For links: Click LINK 1, LINK 2, etc. to open in browser
Or click OPEN ALL LINKS to open everything at once
** 6. Stop
Click STOP when done
Email will be deleted automatically

### Features

| Feature                | Description                               |
| ---------------------- | ----------------------------------------- |
| 🎨 **Cyberpunk UI**    | Neon cyan/purple theme with toggle switch |
| 📧 **Auto Email Gen**  | Creates @guerrillamailblock.com addresses |
| 🔢 **Code Extraction** | Finds 4-6 digit verification codes        |
| 🔗 **Link Extraction** | Finds verify/confirm/activate links       |
| 🖱️ **One-Click Open** | Opens links directly in your browser      |
| 📋 **Copy Buttons**    | Quick copy for email and codes            |
| 🌈 **Theme Switch**    | Toggle between cyan and purple            |


### Troubleshooting
Table
Copy
Problem	Solution
pip not found	Reinstall Python and check "Add to PATH"
No module named 'tkinter'	Install python3-tk: sudo apt install python3-tk (Linux)
Links not opening	Check your default browser settings
App won't start	Make sure you're using Python 3.7+


### How It Works (Simple)
plain
Copy
You Click RUN
    ↓
App connects to Guerrilla Mail API
    ↓
Creates temporary inbox
    ↓
Checks inbox every 5 seconds
    ↓
New email arrives
    ↓
Scans for: 6-digit codes + verification links
    ↓
Displays on dashboard
    ↓
You click link → Opens in your browser


Disclaimer
For educational purposes only. Use responsibly and in accordance with the Terms of Service of websites you interact with.
Made with 💚 by KingBitow
plain
Copy

This README is:
- **Simple** - No technical jargon
- **Clear** - Step-by-step instructions
- **Complete** - Covers all operating systems
- **Visual** - Uses tables and emojis for easy reading
- **Honest** - Explains exactly what the program does

Want me to adjust anything or add more details?









