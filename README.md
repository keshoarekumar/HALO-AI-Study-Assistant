# HALO - AI-Powered Study Assistant

HALO (Helping Academic Learning Optimally) is an AI-powered study assistant designed to help students generate study notes, create personalized study schedules, analyze PDFs and images, and learn in multiple languages through an interactive chatbot interface.

Built using Python, Gradio, Groq LLM, FAISS, Sentence Transformers, OCR, and Translation APIs, HALO provides an intelligent learning experience for students preparing for exams and academic coursework.

---

## Features

### AI Notes Generation
- Generate detailed study notes for any subject.
- Supports custom topics and syllabus-based learning.
- Automatically detects programming-related subjects and includes code examples.

### Personalized Study Schedule
- Creates day-wise study plans.
- Generates structured schedules based on user-defined duration.
- Optimized for consistent daily study sessions.

### PDF Analysis
- Upload PDF files.
- Extracts text using PyMuPDF.
- OCR fallback for scanned PDFs.

### Image-to-Text OCR
- Upload PNG, JPG, and JPEG files.
- Extract text from images using Tesseract OCR.

### Multilingual Learning
- Change chatbot language dynamically.
- Supports automatic translation of notes and schedules.

### Intelligent Subject Detection
- Detects subjects and topics from natural language.
- Supports switching between multiple subjects seamlessly.

### Retrieval-Augmented Generation (RAG)
- Uses FAISS vector search.
- Uses Sentence Transformers for semantic retrieval.
- Retrieves relevant educational context before generating responses.

### Interactive Chat Interface
- Built using Gradio.
- Real-time chatbot interaction.
- Clean and responsive user experience.

---

## Tech Stack

### Frontend
- Gradio

### AI & LLM
- Groq API
- Llama 3.1 Models

### Retrieval System
- FAISS
- Sentence Transformers

### OCR & Document Processing
- PyMuPDF
- Tesseract OCR
- pdf2image
- Pillow

### Translation
- Deep Translator

### Programming Language
- Python

---

## Project Architecture

```text
User
  ↓
HALO Chat Interface (Gradio)
  ↓
Subject & Intent Detection
  ↓
Document Retrieval (FAISS)
  ↓
Sentence Transformer Embeddings
  ↓
Groq LLM
  ↓
Translation Layer
  ↓
Notes & Study Schedule Generation
  ↓
User Response
```

---

## User Interface

### Home Screen
The HALO chatbot welcomes users and accepts natural language study requests.

### Chat Interface
Users can:
- Ask for notes
- Generate schedules
- Change languages
- Switch subjects

### File Upload
Users can upload:
- PDF files
- Images

HALO automatically extracts text and generates study materials from uploaded content.

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/HALO-AI-Study-Assistant.git

cd HALO-AI-Study-Assistant
```

### Create Virtual Environment

Windows

```bash
python -m venv venv

venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## Run Application

```bash
python app.py
```

The application will launch locally in your browser using Gradio.

---

## Supported Commands

### Generate Notes

```text
Notes on Calculus
```

### Generate Notes with Topics

```text
Physics topics include Kinematics, Optics
```

### Change Notes Length

```text
5 pages
```

or

```text
1000 words
```

### Change Study Duration

```text
14 days
```

### Change Language

```text
change language to tamil
```

### Switch Subject

```text
new subject: Data Structures
```

---

## File Upload Support

Supported Formats:

```text
PDF
PNG
JPG
JPEG
```

HALO automatically:
- Extracts text
- Detects subject
- Identifies topics
- Generates notes
- Creates study schedules

---

## Future Improvements

- ChromaDB Integration
- Multi-PDF Knowledge Base
- User Authentication
- Voice Input Support
- Flashcard Generation
- Quiz Generation
- Export Notes to PDF
- Advanced RAG Pipeline
- Learning Analytics Dashboard

---

## Author

Keshoare

Engineering Student | AI Enthusiast | Software Developer

---

## License

This project is intended for educational and portfolio purposes.
