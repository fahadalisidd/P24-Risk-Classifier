# 📘 Complete Step-by-Step Setup & Execution Guide
## P24: Risk Rubric and Classifier

This guide provides complete, beginner-friendly instructions to install all prerequisites and run the project from scratch on **Windows**, **macOS**, or **Linux**.

---

## 🛠️ PART 1: Installing Prerequisites

### 1. Install Python (Version 3.10, 3.11, or 3.12)

#### 🪟 On Windows:
1. Go to the official Python download page: **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Download the latest Python installer (e.g. Python 3.12).
3. **⚠️ CRUCIAL STEP**: When the installer window opens, make sure to check the box at the bottom:
   - ☑️ **"Add python.exe to PATH"** *(or "Add Python to environment variables")*
4. Click **"Install Now"** and finish the installation.
5. Close and reopen your terminal / PowerShell.

#### 🍏 On macOS:
1. Open Terminal and install Python using Homebrew (if installed):
   ```bash
   brew install python
   ```
   *Or download the installer directly from [python.org/downloads/macos](https://www.python.org/downloads/macos/).*

#### 🐧 On Linux (Ubuntu / Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

---

### 2. Verify Python & Pip Installation
Open your terminal (PowerShell, Command Prompt, or Terminal) and run:

```bash
python --version
# (On Mac/Linux, if python points to Python 2, use: python3 --version)

pip --version
# (Or: pip3 --version)
```

You should see something like `Python 3.12.x` and `pip 24.x.x`.

---

## 📂 PART 2: Extracting the Project

1. Locate **`p24-risk-classifier.zip`**.
2. **Right-click** the zip file and click **"Extract All..."** (or use your favorite unzip tool).
3. You will get a folder called **`p24-risk-classifier`**.

---

## 💻 PART 3: Step-by-Step Execution

### Step 1: Open Terminal in the Project Directory

* **Windows Easy Method**:
  1. Open the unzipped `p24-risk-classifier` folder in File Explorer.
  2. Click on the folder's address bar at the very top (where the path is shown).
  3. Type `powershell` or `cmd` and hit **Enter**.
  4. A black or blue terminal window will open right inside that folder.

* **Mac / Linux Method**:
  Open Terminal and change directory (`cd`) to the project folder:
  ```bash
  cd /path/to/p24-risk-classifier
  ```

---

### Step 2: Create and Activate a Virtual Environment (Recommended)

* **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
  *(Note: If PowerShell shows an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run `.\venv\Scripts\activate` again).*

* **Windows (Command Prompt / CMD)**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

* **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

*(Once activated, you will see `(venv)` appear at the beginning of your terminal prompt).*

---

### Step 3: Install Required Dependencies

Run:
```bash
pip install -r requirements.txt
```
*(This installs FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, and Pytest).*

---

### Step 4: Run Database Migrations

Run:
```bash
python -m alembic upgrade head
```
*(This creates the database tables and initializes the schema).*

---

### Step 5: Start the Application Server

Run:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You will see:
```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
✅ **The backend service is now live and running!**

---

## 🌐 PART 4: Using the Interactive API (Swagger UI)

Keep the terminal running, open your web browser, and go to:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Test 1: Evaluate Risk and Obligation Detection
1. Scroll to **`POST /api/v1/risk/evaluate`** and click on it.
2. Click the **"Try it out"** button on the right.
3. Replace the text in the **Request body** box with:
   ```json
   {
     "operationId": "op-prod-1",
     "operationType": "DELETE",
     "scope": "GLOBAL",
     "reversibility": "IRREVERSIBLE",
     "persistence": "PERMANENT",
     "payload": {
       "environment": "PRODUCTION",
       "approval": "CAB-2026-99",
       "justification": "Purge deprecated production DB",
       "rollbackPlan": "Restore from snapshot snap-2026-08-31"
     }
   }
   ```
4. Click the blue **"Execute"** button.
5. You will see response `200 OK` with `finalCategory: 4`, `riskScore: 64`, and `obligationsSatisfied: true`.

---

### Test 2: Check Overdue Policy Pins Report
1. Click **`GET /api/v1/policies/pins/review-report`** $\rightarrow$ **"Try it out"**.
2. Click **"Execute"**.
3. View all temporary policy pins that require periodic review.

---

### Test 3: Two-Engineer Peer Review
1. Click **`POST /api/v1/reviews`** $\rightarrow$ **"Try it out"**.
2. Submit Engineer 1's score (`category: 3`).
3. Submit Engineer 2's score (`category: 4`) for the same `operationId`.
4. The system automatically detects the conflict and records a `DISAGREEMENT` note while preserving both original scores!

---

## 🧪 PART 5: Running the 40 Automated Tests

Open a **second** terminal window inside the `p24-risk-classifier` folder and run:

```bash
python -m pytest -v
```

You will see:
```text
======================== 40 passed in 1.53s ========================
```
This tests all components, including **every single route to Category 4 (Static, Dynamic, Override, and Pin)**.

---

## 🐳 PART 6: (Alternative) Running with Docker Compose

If you have Docker Desktop installed, you don't even need Python installed:

```bash
docker-compose up --build
```
This automatically boots PostgreSQL and the FastAPI application on `http://localhost:8000/docs`.

---

## 🛑 How to Stop the Server
In the terminal where the server is running, press **`CTRL + C`**.
