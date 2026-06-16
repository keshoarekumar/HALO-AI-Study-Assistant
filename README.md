# HALO – AI Study Assistant

> **H**elp **A**nd **L**earn **O**rganizer — a conversational AI that generates personalised study notes and schedules from a subject name, syllabus text, or uploaded PDF/image.

![HALO UI](screenshot.png)

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Running Locally](#running-locally)
8. [VS Code Setup](#vs-code-setup)
9. [Usage Guide](#usage-guide)
10. [How It Works](#how-it-works)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)

---

## Features

| Feature | Description |
|---|---|
| **AI Study Notes** | Generates detailed notes for any subject using Groq's `llama-3.1-8b-instant` model |
| **Study Schedule** | Produces a day-wise Markdown table schedule (default: 14 days, 2 hrs/day) |
| **File Upload** | Extracts subject & topics from uploaded PDFs or images (PNG/JPG) via OCR |
| **Dynamic Adjustment** | Re-generate notes at a different length (`5 pages`, `500 words`) or schedule (`2 days`, `1 week`) |
| **Multi-Subject Flow** | Seamlessly move between subjects in the same session |
| **Language Switching** | Translate all output to any language (`change language to French`) |
| **Semantic Retrieval** | Hybrid sparse + dense (FAISS + Sentence Transformers) retrieval for context grounding |
| **Programming Detection** | Automatically includes code examples when a programming subject is detected |

---

## Tech Stack

| Layer | Library / Service |
|---|---|
| **UI** | [Gradio](https://gradio.app) 4.x |
| **LLM** | [Groq](https://console.groq.com) — `llama-3.1-8b-instant` |
| **Embeddings** | [Sentence Transformers](https://www.sbert.net) — `all-MiniLM-L6-v2` |
| **Vector Search** | [FAISS](https://faiss.ai) (CPU) |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io) (`fitz`) |
| **OCR** | [pytesseract](https://github.com/madmaze/pytesseract) + [Tesseract](https://github.com/tesseract-ocr/tesseract) |
| **Translation** | [deep-translator](https://github.com/nidhaloff/deep-translator) (Google Translate backend) |
| **Env Management** | [python-dotenv](https://github.com/theskumar/python-dotenv) |

---

## Project Structure

```
halo-study-assistant/
├── app.py               # Main application – all logic and Gradio UI
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Your secrets (git-ignored)
├── .gitignore
├── .vscode/
│   └── extensions.json  # Recommended VS Code extensions
├── screenshot.png       # UI screenshot (optional, used in README)
└── README.md
```

---

## Prerequisites

### Python

Python **3.9 or higher** is required.

```bash
python --version   # should print 3.9+
```

### Tesseract OCR (system package)

Tesseract must be installed at the **operating-system level** — `pip` cannot install it.

**macOS (Homebrew)**
```bash
brew install tesseract
```

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install -y tesseract-ocr
```

**Windows**

Download and run the installer from:  
https://github.com/UB-Mannheim/tesseract/wiki

After installation, add Tesseract to your `PATH`, or set the path explicitly in `app.py`:

```python
# Add near the top of app.py if on Windows:
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Poppler (required by pdf2image)

**macOS**
```bash
brew install poppler
```

**Ubuntu / Debian**
```bash
sudo apt install -y poppler-utils
```

**Windows**  
Download from https://github.com/oschwartz10612/poppler-windows/releases, unzip, and add the `bin/` folder to your `PATH`.

### Groq API Key

HALO uses the Groq API (free tier available) for LLM inference.

1. Sign up at https://console.groq.com
2. Create an API key under **API Keys**
3. Copy it — you will add it to `.env` below

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/halo-study-assistant.git
cd halo-study-assistant

# 2. Create and activate a virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements.txt
```

> **Note on PyTorch:** `requirements.txt` pulls in the default PyTorch build. If you have a CUDA GPU and want GPU acceleration for Sentence Transformers, replace `torch` with the appropriate CUDA wheel from https://pytorch.org/get-started/locally/

---

## Configuration

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` in any text editor and fill in your key:

```dotenv
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

`.env` is listed in `.gitignore` and will **never** be committed to version control.

---

## Running Locally

```bash
# Make sure your virtual environment is active, then:
python app.py
```

Open your browser at **http://localhost:7860**

To expose a public shareable link (useful for demos):

```python
# In app.py, change the last line to:
demo.launch(share=True)
```

---

## VS Code Setup

1. Open the project folder in VS Code: `code .`
2. VS Code will prompt you to install the recommended extensions — click **Install All**
3. Select the Python interpreter inside your `venv`:
   - `Ctrl+Shift+P` → **Python: Select Interpreter** → choose `./venv/bin/python`
4. Create a launch configuration for one-click runs:

   **`.vscode/launch.json`** (create this file):
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Run HALO",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/app.py",
         "envFile": "${workspaceFolder}/.env",
         "console": "integratedTerminal"
       }
     ]
   }
   ```
5. Press **F5** to launch HALO with the debugger attached.

---

## Usage Guide

### Basic Flow

| You type | HALO does |
|---|---|
| `Notes on Calculus` | Generates 3-page notes + 14-day schedule for Calculus |
| `5 pages` | Re-generates notes at 5-page length, same subject |
| `2 weeks` | Re-generates schedule for 14 days |
| `500 words` | Re-generates notes (~2-3 pages) |
| `yes` / `ok` / `enough` | Signals you're done — HALO asks for the next subject |
| `new subject: Physics topics include Kinematics, Optics` | Switches subject immediately |
| `change language to Tamil` | All subsequent output translated to Tamil |

### File Upload

Click the **⏏ upload button** (bottom right of the input row) to attach:

- **PDF** — text is extracted directly; scanned PDFs fall back to OCR automatically
- **PNG / JPG / JPEG** — full OCR via Tesseract

HALO parses the extracted text to detect the subject and topics, then generates notes and a schedule.

### Adjusting Output

You can mix adjustments in a single message:

```
new subject: Machine Learning topics include regression, neural nets 10 pages 3 weeks
```

---

## How It Works

```
User message
     │
     ▼
Intent detection (language change? greeting? subject? adjustment?)
     │
     ▼
Subject / topic extraction  ──►  parse_pages_days_words()
     │
     ▼
Hybrid Retrieval
  ├── sparse_search()  →  keyword snippet
  └── dense_search()   →  FAISS cosine similarity (Sentence Transformers)
     │
     ▼
generate_notes()  ──►  Groq LLM (llama-3.1-8b-instant)
generate_schedule()  ──►  Groq LLM (llama-3.1-8b-instant)
     │
     ▼
translate_text()  (Google Translate via deep-translator, if language ≠ English)
     │
     ▼
render_chat()  →  HTML bubble rendered in Gradio
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `EnvironmentError: GROQ_API_KEY is not set` | Create `.env` from `.env.example` and add your key |
| `TesseractNotFoundError` | Install Tesseract (see Prerequisites) and ensure it's on `PATH` |
| `pdf2image` / Poppler errors | Install Poppler (see Prerequisites) |
| `ModuleNotFoundError: No module named 'fitz'` | Run `pip install PyMuPDF` — the package is `PyMuPDF` but imports as `fitz` |
| Port 7860 already in use | Change `server_port=7861` in the `demo.launch()` call |
| Slow first run | Sentence Transformers downloads `all-MiniLM-L6-v2` (~90 MB) on first use — subsequent runs are fast |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Please keep API keys out of commits — the `.gitignore` helps, but double-check with `git diff --staged` before pushing.

---

## License

MIT — see [LICENSE](LICENSE) for details.
