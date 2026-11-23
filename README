## Project Structure

```text
DB_University/
├── README.md                       # Project structure and environment setup guide
├── .gitignore
└── server/
    ├── app.py                      # Flask entry point and URL routing
    ├── .venv/                      # Python virtual environment
    ├── installation/
    │   ├── requirements.txt        # Pinned Python dependencies
    │   ├── setup.sh                # macOS / Linux
    │   ├── setup.bat               # Windows
    │   ├── requirements.sh         # macOS / Linux
    │   └── requirements.bat        # Windows
    ├── api/
    │   └── auth.py                 # Access control
    ├── db/                         # Private DB config & credentials (gitignored)
    └── static/
        ├── style.css               # Shared stylesheet
        ├── index.html              # Landing page
        ├── login.html
        ├── signup.html
        ├── admin/
        │   └── admin.html          # Admin dashboard
        ├── instructor/
        │   └── instructor.html     # Instructor dashboard
        └── student/
            └── student.html        # Student dashboard
```


**Notes (`installation/`):**
```text
- setup                # Create/sync .venv with requirements.txt
- requirements         # Export installed .venv packages to requirements.txt
```

---



# Environment Setup & Run

## 1.
### Windows (PowerShell)

```powershell
# Check if Python 3.11 or higher is installed
python --version

# Move to the server directory
cd server

# Create .venv (if missing) or sync packages inside .venv with installation\requirements.txt
.\installation\setup.bat

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Export packages currently installed inside .venv to installation\requirements.txt
.\installation\requirements.bat
```


### macOS / Linux

```bash
# Check if Python 3.11 or higher is installed
python3 --version

# Move to the server directory
cd server

# Create .venv (if missing) or sync packages inside .venv with installation/requirements.txt
# Run with 'bash' (not 'source') so any error exits the script without closing your terminal
bash installation/setup.sh

# Activate virtual environment
source .venv/bin/activate

# Export packages currently installed inside .venv to installation/requirements.txt
bash installation/requirements.sh
```

---

## 2. Run Flask server in debug mode
```
python app.py
```