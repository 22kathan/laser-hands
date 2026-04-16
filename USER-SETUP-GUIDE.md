# 🎯 Laser Hands - Standalone Setup Guide for Users

This guide helps users on **any Windows computer** set up and run **Laser Hands** with just one batch file!

---

## **Quick Start (3 Steps)**

### **Step 1: Download the Setup File**
Download `Setup-and-Launch-Laser-Hands.bat` from:
- **GitHub Releases:** https://github.com/22kathan/laser-hands/releases
- **Portfolio Website:** https://22kathan.github.io/portfolio

### **Step 2: Run the Batch File**
1. **Right-click** the `Setup-and-Launch-Laser-Hands.bat` file
2. Select **"Run as Administrator"** ⚠️ (Important for Python installation)
3. Click **"Yes"** when prompted by Windows

### **Step 3: Follow On-Screen Instructions**
The batch file will automatically:
✅ Check if Python 3.11 is installed  
✅ Download Python from python.org (with active timer and progress bar)  
✅ Install Python silently  
✅ Download Laser Hands project files  
✅ Install Python dependencies  
✅ Launch the application  

**Total time: 5-15 minutes** (depending on internet speed)

---

## **What This Batch File Does**

```
Setup-and-Launch-Laser-Hands.bat
    ↓
[Check Python]
    ↓ (if not installed)
[Download Python 3.11 with 3 fallback methods]
    ↓
[Install Python automatically]
    ↓
[Download Laser Hands from GitHub]
    ↓
[Install Python dependencies (pyautogui, websockets)]
    ↓
[Launch Laser Hands application]
```

---

## **System Requirements**

| Requirement | Details |
|---|---|
| **OS** | Windows 10 or later (64-bit) |
| **Internet** | Required for initial setup |
| **Disk Space** | ~300MB free |
| **Webcam** | Required for hand tracking |

---

## **Troubleshooting**

### **❌ "Python Download Failed"**
**Solution:**
1. Try running as Administrator
2. Check your internet connection
3. Check if python.org is accessible (firewall/proxy)
4. Install Python manually from https://www.python.org/downloads/release/python-3119/

### **❌ "Git not found"**
**Solution:**
1. Install Git from https://git-scm.com/download/win
2. Run the batch file again

### **❌ "Module not found (pyautogui, websockets)"**
**Solution:**
```bash
python -m pip install -r requirements.txt
```

### **❌ "Access Denied"**
**Solution:**
1. Right-click the batch file
2. Select "Run as Administrator"

---

## **Installation Locations**

After setup, files are installed at:
```
C:\Users\[YourUsername]\Documents\Laser Hands\
    ├── index.html                          (Web interface)
    ├── os_controller.py                    (Python backend)
    ├── Launch Laser Hands.bat              (Regular launcher)
    ├── requirements.txt                    (Dependencies)
    └── ...other files
```

To run again later, use: **Launch Laser Hands.bat** (in Documents/Laser Hands/)

---

## **How to Use Laser Hands**

1. **Start**: Run the batch file → Browser opens → Allow camera access
2. **Gestures**:
   - ✋ **Move**: Point with open hand
   - 👆 **Left Click**: Pinch thumb + index
   - 🔄 **Drag & Drop**: Move while pinching
   - ⏸️ **Right Click**: Hover for 1.5 seconds
   - 🔄 **Scroll**: Rotate hand (twist)
   - ✊ **Zoom In**: Close hand
   - ✋ **Zoom Out**: Open hand wide

---

## **Support & Issues**

- **Documentation**: https://github.com/22kathan/laser-hands
- **Report Issues**: https://github.com/22kathan/laser-hands/issues
- **Portfolio**: https://22kathan.github.io/portfolio

---

## **File Descriptions**

| File | Purpose |
|---|---|
| `Setup-and-Launch-Laser-Hands.bat` | **One-click setup** for new users (this file) |
| `Launch Laser Hands.bat` | **Regular launcher** for returning users |
| `os_controller.py` | Hand tracking → OS control backend |
| `index.html` | Web interface with hand tracking |
| `requirements.txt` | Python dependencies |

---

**👍 First time? Use `Setup-and-Launch-Laser-Hands.bat`**  
**🔄 Next time? Use `Launch Laser Hands.bat` (in Documents/Laser Hands/)**

Enjoy! 🎮✨
