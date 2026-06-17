# HALO – AI Study Assistant

HALO is a conversational AI chatbot that generates personalized study notes and day-wise study schedules for any subject, using the Groq LLM API, semantic retrieval (FAISS + Sentence Transformers), and OCR-based file upload support.

## Web UI

![HALO Web UI](screenshot.png)

The interface is built with Gradio:
- **Title banner** – "HALO" displayed in a decorative red theme
- **Chat window** – conversation bubbles between you and HALO, supporting Markdown (including tables for schedules)
- **Message box** – type your subject, topics, or adjustment commands (e.g. `5 pages`, `2 days`)
- **🔍 button** – sends your message
- **⏏ upload button** – upload a PDF or image; HALO extracts the subject/topics via OCR and generates notes + schedule automatically

## Features

- Generates study notes for any subject via Groq (`llama-3.1-8b-instant`)
- Generates a day-wise study schedule as a Markdown table
- Upload PDFs or images (PNG/JPG) — text/subject/topics are extracted automatically (with OCR fallback for scanned PDFs)
- Adjust notes length anytime: `5 pages`, `500 words`
- Adjust schedule length anytime: `2 days`, `1 week`
- Switch to a new subject mid-conversation: `new subject: Physics topics include Kinematics, Optics`
- Change response language anytime: `change language to French`
- Hybrid retrieval (sparse keyword + dense FAISS vector search) used as grounding context for note generation

## Project Structure

```
halo-study-assistant/
├── app.py              # Main application (Gradio UI + chatbot logic)
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your Groq API key
├── .gitignore
├── screenshot.png       # Web UI screenshot
└── README.md
```

## Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/halo-study-assistant.git
cd halo-study-assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install system dependencies (required by OCR/PDF features)

**Tesseract OCR**
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH

**Poppler** (required by `pdf2image`)
- macOS: `brew install poppler`
- Ubuntu/Debian: `sudo apt install poppler-utils`
- Windows: download from https://github.com/oschwartz10612/poppler-windows/releases and add `bin/` to PATH

### 5. Configure your API key
```bash
cp .env.example .env
```
Open `.env` and paste your Groq API key (get one free at https://console.groq.com/keys):
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

### 6. Run the app
```bash
python app.py
```
Open the URL shown in the terminal (default: http://127.0.0.1:7860) in your browser.

## Notes on the API Key Change

The only change made to the original code is the Groq client initialization line, so the key is read securely from your `.env` file instead of being hardcoded:

```python
# Before
client = groq.Groq(api_key="your Groq API KEY")

# After
client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
```

All other logic, functions, and UI code are unchanged from the original.

## License

MIT
