# Quick Start Guide - دليل البدء السريع

## English Version

### Installation Steps:

1. **Open Command Prompt or Terminal in this folder**

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   ⏳ This may take 5-10 minutes for CAMeL Tools to download language models.

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open browser:**
   Go to: http://localhost:5000

### Test Example:
Copy and paste this text to test:
```
الطالب المجتهد ينجح في الامتحان. المعلم يشرح الدرس بوضوح.
```

---

## النسخة العربية

### خطوات التثبيت:

1. **افتح موجه الأوامر في هذا المجلد**

2. **أنشئ بيئة افتراضية:**
   ```bash
   python -m venv venv
   ```

3. **فعّل البيئة الافتراضية:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **ثبّت المكتبات المطلوبة:**
   ```bash
   pip install -r requirements.txt
   ```
   ⏳ قد يستغرق هذا 5-10 دقائق لتحميل نماذج اللغة العربية.

5. **شغّل التطبيق:**
   ```bash
   python app.py
   ```

6. **افتح المتصفح:**
   اذهب إلى: http://localhost:5000

### مثال للتجربة:
انسخ والصق هذا النص للتجربة:
```
الطالب المجتهد ينجح في الامتحان. المعلم يشرح الدرس بوضوح.
```

---

## Need Help?

### Common Issues:

**❌ Python not found?**
- Install Python 3.8+ from: https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

**❌ pip not found?**
- Windows: `python -m pip install --upgrade pip`
- macOS/Linux: `python3 -m pip install --upgrade pip`

**❌ CAMeL Tools installation error?**
- Make sure you have Python 3.8 or higher
- Try: `pip install --upgrade pip setuptools wheel`
- Then retry: `pip install -r requirements.txt`

**❌ Port 5000 already in use?**
- Edit app.py and change the port:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)
  ```

### To Stop the Server:
Press `Ctrl + C` in the terminal

### To Deactivate Virtual Environment:
```bash
deactivate
```

---

## Project Files Overview:

- `app.py` - Main Python application (Flask backend)
- `requirements.txt` - List of required Python packages
- `templates/index.html` - Website HTML page
- `static/style.css` - Website styling
- `static/script.js` - Website functionality
- `README.md` - Full documentation
- `QUICKSTART.md` - This file (quick guide)

---

**Ready to go! 🚀**
