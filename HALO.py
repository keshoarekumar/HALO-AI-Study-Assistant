

import gradio as gr
import markdown
from sentence_transformers import SentenceTransformer
import faiss
import groq
import re
import math
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
from deep_translator import GoogleTranslator

# ─────────────────────────────────────────────────────────────────────────────
# NOTE: Keep your existing Groq client line with your API key.
# For safety, we show a placeholder here. Replace with your current line.
# client = groq.Groq(api_key="YOUR_GROQ_KEY")
client = groq.Groq(api_key="your Groq API key here")  # Replace with your actual Groq API key
# ─────────────────────────────────────────────────────────────────────────────

# ------------------------------- Data & Embeddings ---------------------------
context_state = {
    "subject": None,
    "topics": [],
    "language": "english"  # default language
}

documents = [
    {"title": "Calculus Basics", "text": "Calculus is the mathematical study of continuous change..."},
    {"title": "Algebra Fundamentals", "text": "Algebra is about symbols and the rules for manipulating these symbols..."},
]

doc_texts = [doc['text'] for doc in documents]
# Use a standard Sentence Transformer model for embeddings
dense_model = SentenceTransformer('all-MiniLM-L6-v2')
doc_embeddings = dense_model.encode(doc_texts, convert_to_tensor=True)
index = faiss.IndexFlatIP(doc_embeddings.shape[1])
index.add(doc_embeddings.cpu().numpy())

# ------------------------------- Retrieval fns -------------------------------
def sparse_search(subject, syllabus):
    return ["Sparse snippet about " + subject]

def dense_search(query, top_k=3):
    # Use the Sentence Transformer model for embedding the query
    query_emb = dense_model.encode(query, convert_to_tensor=True)
    query_emb_np = query_emb.cpu().numpy().reshape(1, -1)
    D, I = index.search(query_emb_np, top_k)
    results = [documents[i]['text'] for i in I[0]]
    return results

# ----------------------------- Generation helpers ----------------------------
WORDS_PER_PAGE = 200
TOKENS_PER_PAGE = 300
# Define the Groq model to be used for generation
GROQ_GENERATION_MODEL = "llama-3.1-8b-instant"

def generate_notes(subject, syllabus, pages=3):
    max_words = pages * WORDS_PER_PAGE
    max_tokens = max(256, pages * TOKENS_PER_PAGE)
    sparse_results = sparse_search(subject, syllabus)
    dense_results = dense_search(f"{subject} {syllabus}")
    combined_context = "\n\n".join(sparse_results + dense_results)

    subject = subject or "General"
    syllabus = syllabus or "General topics"

    # --- Programming detection ---
    programming_keywords = [
        "python", "java", "c++", "javascript", "variables",
        "loops", "functions", "list", "dict", "array", "class", "object"
    ]
    combined_text = f"{subject} {syllabus}".lower()
    is_programming = any(kw in combined_text for kw in programming_keywords)

    # --- Fix ambiguous short phrases ---
    # If subject is 1-3 words and starts with a programming keyword, make it explicit
    if is_programming:
        words = subject.split()
        if len(words) <= 3:
            subject = " ".join(words[1:] + ["in", words[0]]) if len(words) == 2 else subject + " programming"

    context_hint = "Assume this is about programming and include code examples." if is_programming else ""

    prompt = (
        f"Generate detailed study notes for the subject '{subject}'. {context_hint} "
        f"Cover these topics: {syllabus}. "
        f"Reference materials:\n{combined_context}\n\n"
        f"Notes (approx {max_words} words):\n"
    )

    response = client.chat.completions.create(
        model=GROQ_GENERATION_MODEL, # Use the specified Groq model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.5,
    )
    return response.choices[0].message.content


def generate_schedule(subject, syllabus, days=14):
    # Slightly higher max_tokens so longer schedules fit
    max_tokens = max(300, 80 + days * 20)
    prompt = (
        f"Create a personalized, conflict-free study schedule for the subject '{subject}' covering these topics:\n"
        f"{syllabus}\n\n"
        f"Assume the user can study 2 hours daily and wants to finish in {days} days.\n"
        f"Provide a day-wise plan specifying which topics to study each day.\n"
        f"Format the schedule as a clear Markdown table."
    )
    response = client.chat.completions.create(
        model=GROQ_GENERATION_MODEL, # Use the specified Groq model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.5,
    )
    return response.choices[0].message.content

def extract_text_from_file(file_obj):
    file_name = file_obj.name.lower()

    if file_name.endswith(".pdf"):
        text = ""
        with fitz.open(file_obj.name if isinstance(file_obj.name, str) else file_obj) as pdf_doc:

            for page in pdf_doc:
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"
                else:
                    # OCR fallback
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text += pytesseract.image_to_string(img)
        return text

    elif file_name.endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(file_obj.name)
        return pytesseract.image_to_string(img)

    # Assuming docx requires python-docx library, which isn't installed
    # elif file_name.endswith(".docx"):
    #     doc = docx.Document(file_obj.name)
    #     return "\n".join([p.text for p in doc.paragraphs])

    else:
        return ""


def handle_file_upload(file_obj, chat_state, context_state):
    if file_obj is None:
        chat_state.append(("HALO", "Please upload a supported file (PDF, image)."))
        return render_chat(chat_state), list(chat_state), dict(context_state)

    extracted_text = extract_text_from_file(file_obj)
    subject, topics = extract_subject_and_topics(extracted_text)

    if not subject:
        subject = "General Study Material"
    if not topics:
        topics = "General topics from file"

    context_state["subject"] = subject
    context_state["syllabus"] = topics
    context_state.setdefault("pages", 3)
    context_state.setdefault("days", 14)
    context_state.pop("awaiting_new_subject", None)

    _respond_with_notes_and_schedule(chat_state, context_state)

    return render_chat(chat_state), list(chat_state), dict(context_state)
def detect_language_change(user_message):
    match = re.search(r"(?:change|switch|set)\s+language\s*(?:to)?\s*([a-zA-Z]+)", user_message, re.I)
    if match:
        return match.group(1).strip().lower()
    return None


# ---------------------------- Parsing & Intent fns ---------------------------
SUBJECT_CHANGE_KEYWORDS = [
    "new subject", "another subject", "change subject", "switch subject", "switch to", "next subject"
]
AFFIRMATIONS = {"yes", "yup", "yeah", "ok", "okay", "fine", "good", "looks good", "enough", "done", "next"}
NON_SUBJECT_WORDS = {"yes", "ok", "okay", "enough", "no", "stop", "continue", "thanks", "thank you"}


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def extract_subject_and_topics(text: str, allow_fallback: bool = True):
    """Extract subject and topic list from free text.
    If allow_fallback=False, we avoid 'guessing' the subject from first 3 words.
    """
    text_lower = text.lower()
    subject = None
    topics = ""

    # Explicit subject patterns
    patterns = [
        r"(?:new|another|change|switch|next)\s+subject[:\-\s]*([a-z0-9 &()\-]+)",
        r"(?:subject\s*[:\-]\s*)([a-z0-9 &()\-]+)",
        r"(?:study|learn)\s+([a-z0-9 &()\-]+)",
        r"notes\s+(?:on|for|about)\s+([a-z0-9 &()\-]+)",
        r"(?:about|on)\s+([a-z0-9 &()\-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            subject = _clean_text(m.group(1))
            break

    # Topics patterns
    topics_match = re.search(r"(topics\s*(?:are|include|:|\-)\s*)(.*)", text_lower)
    if topics_match:
        topics = _clean_text(topics_match.group(2))
    else:
        cover_match = re.search(r"(?:covering|syllabus|include|including)\s+([a-z0-9, \-&()]+)", text_lower)
        if cover_match:
            topics = _clean_text(cover_match.group(1))

    if subject is None and allow_fallback:
        # Conservative fallback: try to capture a short phrase before punctuation
        # but only if message is not an adjustment-only command
        if not re.search(r"\b(pages?|pgs?|p\b|words?|days?|weeks?|w\b|d\b)\b", text_lower):
            # Take up to first 3 words as a guess
            candidate = " ".join(text_lower.split()[:3]).strip()
            if 1 <= len(candidate) <= 40:
                subject = candidate

    # Title-case the subject nicely
    if subject:
        subject = re.sub(r"\s+", " ", subject).strip(" .,-:")
        subject = subject.title()

    return subject, topics


def parse_pages_days_words(text: str):
    """Parse pages, days, and words from text. Convert words→pages using WORDS_PER_PAGE.
    Accepts formats like '5 pages', '10pg', 'pgs', '2 days', '1 week', '500 words', etc.
    """
    pages = None
    days = None

    # words → pages
    words_match = re.search(r"(\d+)\s*words?\b", text, flags=re.I)
    if words_match:
        words = int(words_match.group(1))
        pages = max(1, math.ceil(words / WORDS_PER_PAGE))

    # pages
    pages_match = re.search(r"(\d+)\s*(?:pages?|pgs?|pg|p\b)\b", text, flags=re.I)
    if pages_match:
        pages = int(pages_match.group(1))

    # days/weeks
    days_match = re.search(r"(\d+)\s*(?:days?|d\b)\b", text, flags=re.I)
    weeks_match = re.search(r"(\d+)\s*(?:weeks?|w\b)\b", text, flags=re.I)
    if weeks_match:
        days = int(weeks_match.group(1)) * 7
    if days_match:
        days = int(days_match.group(1))

    return pages, days


def detect_subject_change(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in SUBJECT_CHANGE_KEYWORDS)


# ------------------------------ UI Rendering ---------------------------------

def render_chat(chat_state):
    html = ""
    for speaker, msg in chat_state:
        msg_html = markdown.markdown(msg, extensions=["tables"])  # allow Markdown tables
        # Force bold tags to white text
        msg_html = msg_html.replace("", "") \
                           .replace("", "")

        if speaker == "You":
            html += f"""
            
                
                    
                        {msg_html}
                    
                
            
            """
        else:
            html += f"""
            
                
                    
                        {msg_html}
                    
                
            
            """
    return html

# ------------------------------- Chatbot Logic --------------------------------

def _respond_with_notes_and_schedule(chat_state, ctx):
    subject = ctx["subject"]
    syllabus = ctx.get("syllabus", "General topics")
    pages = ctx.get("pages", 3)
    days = ctx.get("days", 14)
    lang = ctx.get("language", "english")

    notes = generate_notes(subject, syllabus, pages=pages)
    schedule = generate_schedule(subject, syllabus, days=days)

    # Translate outputs into selected language
    notes = translate_text(notes, lang)
    schedule = translate_text(schedule, lang)

    wrapper = translate_text(
        f"Here are the notes and schedule for **{subject}**.\n\n"
        f"**Notes:**\n{notes}\n\n"
        f"**Schedule:**\n{schedule}\n\n"
        "Is this enough? You can say things like: `5 pages`, `2 days`, `500 words`, "
        "or `new subject: Physics (topics include Kinematics, Optics)`—in any format.",
        lang
    )


    chat_state.append(("HALO", wrapper))


def translate_text(text, target_language):
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception as e:
        return text


def chatbot_response(user_message, chat_state, context_state):
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]

    if not user_message or user_message.strip() == "":
        return render_chat(chat_state), "", chat_state, context_state

    user_message_str = user_message.strip()
    user_message_lower = user_message_str.lower()
    chat_state.append(("You", user_message_str))

    # 1. Language change check first
    language_request = detect_language_change(user_message_str)
    if language_request:
        context_state["language"] = language_request
        reply = f"✅ Language changed to {language_request.title()}"

        # 🔹 translate before sending
        reply = translate_text(reply, context_state.get("language", "english")) # Use get for safety
        # 🔹 render markdown so **bold** works in all languages
        reply = markdown.markdown(reply)

        chat_state.append(("HALO", reply))  # Changed speaker to HALO
        return render_chat(chat_state), "", chat_state, context_state



    # 2. Greetings
    if user_message_lower in greetings:
        reply = "Hello! What subject would you like notes for?"
        # 🔹 translate before sending
        reply = translate_text(reply, context_state.get("language", "english")) # Use get for safety
        chat_state.append(("HALO", reply)) # Changed speaker to HALO
        return render_chat(chat_state), "", chat_state, context_state


    # If we don't have a subject yet OR user is asking to change to a new one
    if "subject" not in context_state or context_state["subject"] is None:
        subject, syllabus = extract_subject_and_topics(user_message_str, allow_fallback=True)
        if not subject:
            reply = "Tell me the subject (e.g., `Notes on Calculus`) and optional topics."
            reply = translate_text(reply, context_state.get("language", "english"))
            chat_state.append(("HALO", reply))
            return render_chat(chat_state), "", chat_state, context_state

        context_state["subject"] = subject
        context_state["syllabus"] = syllabus if syllabus else "General topics"
        context_state.setdefault("pages", 3)
        context_state.setdefault("days", 14)
        context_state.pop("awaiting_new_subject", None)

        _respond_with_notes_and_schedule(chat_state, context_state)
        return render_chat(chat_state), "", chat_state, context_state

    # From here, we already have a subject in context

    # If user says it's enough -> move to next subject
    if any(word in user_message_lower for word in AFFIRMATIONS):
        context_state["awaiting_new_subject"] = True
        reply = "Great! 🎉 Share the **next subject** (and optional topics/pages/days)."
        reply = translate_text(reply, context_state.get("language", "english"))
        chat_state.append(("HALO", reply))
        return render_chat(chat_state), "", chat_state, context_state

    # Detect explicit request for new/another subject in the message
    explicit_subject_switch = detect_subject_change(user_message_str)
    pages, days = parse_pages_days_words(user_message_str)

    # Case A: User asked for another subject and provided its name (optionally pages/days)
    maybe_new_subject, maybe_topics = extract_subject_and_topics(user_message_str, allow_fallback=False)
    if explicit_subject_switch and maybe_new_subject:
        context_state["subject"] = maybe_new_subject
        context_state["syllabus"] = maybe_topics if maybe_topics else "General topics"
        if pages: context_state["pages"] = pages
        if days: context_state["days"] = days
        context_state.pop("awaiting_new_subject", None)
        _respond_with_notes_and_schedule(chat_state, context_state)
        return render_chat(chat_state), "", chat_state, context_state

    # Case B: We are awaiting a new subject and the user provides one now
    if context_state.get("awaiting_new_subject"):
        subj2, topics2 = extract_subject_and_topics(user_message_str, allow_fallback=True)
        if subj2:
            context_state["subject"] = subj2
            context_state["syllabus"] = topics2 if topics2 else "General topics"
            if pages: context_state["pages"] = pages
            if days: context_state["days"] = days
            context_state.pop("awaiting_new_subject", None)
            _respond_with_notes_and_schedule(chat_state, context_state)
            return render_chat(chat_state), "", chat_state, context_state
        else:
            # They said 'another subject' but didn't specify which one
            if explicit_subject_switch:
                reply = "Sure — what's the **new subject**? You can also add topics/pages/days."
                reply = translate_text(reply, context_state.get("language", "english"))
                chat_state.append(("HALO", reply))
                return render_chat(chat_state), "", chat_state, context_state

    # Case C: Only adjust pages/days for the current subject
    if pages is not None or days is not None:
        if pages is not None:
            context_state["pages"] = pages
        if days is not None:
            context_state["days"] = days
        _respond_with_notes_and_schedule(chat_state, context_state)
        return render_chat(chat_state), "", chat_state, context_state

    # Case D: The user typed something that includes a new subject without explicit keywords
    maybe_new_subject, maybe_topics = extract_subject_and_topics(user_message_str, allow_fallback=True)
    if maybe_new_subject and maybe_new_subject != context_state.get("subject"):
        context_state["subject"] = maybe_new_subject
        context_state["syllabus"] = maybe_topics if maybe_topics else "General topics"
        if pages: context_state["pages"] = pages
        if days: context_state["days"] = days
        context_state.pop("awaiting_new_subject", None)
        _respond_with_notes_and_schedule(chat_state, context_state)
        return render_chat(chat_state), "", chat_state, context_state

    # Otherwise, clarify available actions without getting stuck
    reply = (
        "What would you like to change? You can say: \n"
        "• `5 pages` or `500 words` to change notes length\n"
        "• `2 days` or `1 week` to change schedule\n"
        "• `new subject: ` with optional topics\n"
        "• Or say `yes` if it's enough and we'll move to the next subject."
    )
    reply = translate_text(reply, context_state.get("language", "english"))
    chat_state.append(("HALO", reply))
    return render_chat(chat_state), "", chat_state, context_state


def is_probable_subject(text):
    text_clean = text.strip().lower()
    # If it's too short or is just a known non-subject word, reject
    if text_clean.isdigit():
        return False
    # Count words
    word_count = len(text_clean.split())
    # If short enough (1–4 words) and not mostly numbers, assume it's a subject
    return 1 <= word_count <= 4

def groq_translation(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",  # same model you use
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()


def parse_user_input(user_input):
    """
    Detects if the input is:
    - A subject change
    - A page request
    - A schedule duration change
    - Or just general conversation
    """
    user_input = user_input.strip()

    pages_match = re.search(r"(\d+)\s*pages?", user_input, re.IGNORECASE)
    words_match = re.search(r"(\d+)\s*words?", user_input, re.IGNORECASE)
    days_match = re.search(r"(\d+)\s*days?", user_input, re.IGNORECASE)

    pages = int(pages_match.group(1)) if pages_match else None
    words = int(words_match.group(1)) if words_match else None
    days = int(days_match.group(1)) if days_match else None

    subject = None
    if is_probable_subject(user_input) and not (pages or words or days):
        subject = user_input
    else:
        first_part = user_input.split(",")[0]
        if is_probable_subject(first_part):
            subject = first_part

    return {
        "subject": subject,
        "pages": pages,
        "words": words,
        "days": days
    }

# Your chatbot logic here
current_subject = None
notes_data = {}
schedule_data = {}
# ---------------------------------- CSS --------------------------------------
css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&display=swap');

.gradio-container {
  background: url('https://media.istockphoto.com/id/1354045696/photo/white-background-abstract.jpg?b=1&s=612x612&w=0&k=20&c=A8euRZKr_oVematye3PWaLnGKPou5VkVLvCCVH0xQOw=') center/cover no-repeat fixed !important;
 min-height: 100vh !important;
 animation: animatedBackground 60s linear infinite;
  }
@keyframes animatedBackground {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

#halo-title {
    text-align: center;
    margin: 5px 0; /* small top/bottom spacing */
}

.halo-deco {
    font-size: 28px; /* was 20px, now larger */
    color: #C1232C;
    text-shadow:
        0 0 5px #C1232C,
        0 0 10px #ff4d4d,

    margin: -3px 0; /* still keeps lines tight to title */
}

.halo-main {
    font-family: 'Cinzel Decorative', serif;
    font-size: 62px; /* slightly bigger title */
    font-weight: 900;
    letter-spacing: 4px;
    color: #C1232C;
    text-shadow:
        0 0 5px #C1232C,
        0 0 15px #ff4d4d,

    margin: 0;
}

.halo-main {
    font-family: 'Cinzel Decorative', serif;
    font-size: 60px;
    font-weight: 900;
    letter-spacing: 4px;
    color: #C1232C;

    margin: 0; /* no extra space */
}


#chat-box {
    background-color: transparent !important;
    padding: 15px;
    height: 60vh;
    overflow-y: auto;
    margin-bottom: 10px;
}

.gradio-textbox textarea {
    background-color: #C1232C !important;
    border: 1px solid #C1232C !important;
    border-radius: 15px !important;
    color: white !important;
    padding: 12px !important;
}

.gradio-textbox textarea::placeholder {
    color: rgba(255, 255, 255, 0.7) !important;
}

button {
    background-color: transparent !important;
    border: 1px solid rgba(193, 35, 44, 0.5) !important;
    color: #C1232C !important;
    border-radius: 15px !important;
    transition: all 0.3s ease;
}

button:hover {
    background-color: rgba(193, 35, 44, 0.1) !important;
}

#chat-history {
    background-color: transparent !important;
    border: 1px solid rgba(193, 35, 44, 0.2) !important;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
    color: white !important;
    max-height: 20vh;
    overflow-y: auto;
}

.chat-bubble {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    color: white !important;
}

.chat-bubble * {
    color: white !important;
}

#chat-box p,
#chat-box div,
#chat-box span {
    color: white !important;
}

.gradio-interface * {
    color: white !important;
}

::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: rgba(193, 35, 44, 0.5);
    border-radius: 3px;
}

/* Force input appearance */
textarea, input[type="text"] {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    color: white !important;
    font-weight: 500;
    border-radius: 8px !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Focus state — no white glow */
textarea:focus, input[type="text"]:focus {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    box-shadow: none !important; /* Removed glow */
    outline: none !important;
}


/* Search 🔍 button styling */
button:has(span:contains("🔍")) {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 20px;
    padding: 6px 12px;
    box-shadow: none !important;
}

button:has(span:contains("🔍")):hover {
    background-color: rgba(193, 35, 44, 0.8) !important;
    box-shadow: 0 0 8px #C1232C !important;
}

/* File upload / image upload button */
input[type="file"] {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 6px;
}

/* If it's rendered as a button with icon */
button.upload,
button[aria-label="Upload"],
button[title="Upload"],
button svg {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    border-radius: 8px !important;
    color: white !important;
    fill: white !important;
}

/* Hover effect */
button.upload:hover,
button[aria-label="Upload"]:hover {
    background-color: rgba(193, 35, 44, 0.8) !important;
}

/* Remove default Gradio wrapper background and set it to red */
.svelte-1ipelgc, .svelte-1ipelgc * {
    background-color: #C1232C !important;
    box-shadow: none !important;
}


/* Target the wrapper around textboxes */
.input-row > div, .input-row > div * {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

textarea, input[type="text"] {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    color: white !important;
    font-weight: 500;
    border-radius: 8px !important;
    box_shadow: none !important;
    outline: none !important;
}

/* Focus state — no white glow */
textarea:focus, input[type="text"]:focus {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    box-shadow: none !important; /* Removed glow */
    outline: none !important;
}


/* Force only the chat "Type your message..." box to be red */
.input-row textarea,
.input-row input[type="text"] {
    background-color: #C1232C !important;
    border: 2px solid #C1232C !important;
    color: white !important;
    border-radius: 8px !important;
}

/* Target wrapper of that chat input */
.input-row > div:has(> textarea),
.input-row > div:has(> input[type="text"]) {
    background-color: #C1323C !important;
    border-radius: 8px !important;
    border: 2px solid #C1232C !important;
    box-shadow: none !important;
}

/* Placeholder style */
.input-row textarea::placeholder,
.input-row input[type="text"]::placeholder {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Placeholder text color */
textarea::placeholder, input[type="text"]::placeholder {
    color: rgba(255, 255, 255, 0.7) !important;
}
/* Make the file upload button match search button style */
/* File upload button style */
/* File upload button style */
/* File upload button */
/* File upload button */

#file-upload-btn {
    background-color: transparent !important;
    border: 1px solid rgba(193, 35, 44, 0.5) !important;
    border-radius: 15px !important;
    height: 44px !important;
    width: 44px !important; /* make it square */
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important; /* no extra padding */
    cursor: pointer;
}

/* Icon inside button */
#file-upload-btn svg {
    width: 20px !important;
    height: 20px !important;
    stroke-width: 2.5 !important;
    color: #C1232C !important;
}

/* Remove watermark & placeholder */
#file-upload-btn .wrap,
#file-upload-btn .file-drop-label,
#file-upload-btn .file-preview {
    display: none !important;
}

/* Hide the default input field */
#file-upload-btn input[type=file] {
    display: none !important;
}

/* Hover effect */
#file-upload-btn:hover {
    background-color: rgba(193, 35, 44, 0.1) !important;
}

"""

# --------------------------------- App ---------------------------------------
chat_history = [("HALO", "Hello! 👋 I'm HALO, your study assistant. What subject would you like to study today?")]
context_state = {}

with gr.Blocks(css=css) as demo:
    with gr.Row():
        with gr.Column(scale=1):
            pass
        with gr.Column(scale=3):
            gr.Markdown("""
            
              ────୨ৎ────
              HALO
              . . . . . ╰──╮╭──╯ . . . . .
            """)
        with gr.Column(scale=1):
            pass

    chat_html = gr.HTML(value=render_chat(chat_history), elem_id="chat-box")


    with gr.Row(elem_classes="input-row"):
        msg = gr.Textbox(placeholder="Type your message...", show_label=False, scale=8)
        send_btn = gr.Button("🔍", scale=1)
        file_upload = gr.File(
    file_types=[".pdf", ".png", ".jpg", ".jpeg"],
    elem_id="file-upload-btn",
    label="⏏"
)





    state = gr.State(chat_history)
    context = gr.State(context_state)

    def on_send(text, chat_state, context_state):
        if text is None:
            return render_chat(chat_state), "", chat_state, context_state
        updated_html, cleared, updated_state, updated_context = chatbot_response(text, chat_state, context_state)
        return render_chat(updated_state), cleared, updated_state, updated_context

    send_btn.click(on_send, inputs=[msg, state, context], outputs=[chat_html, msg, state, context])
    msg.submit(on_send, inputs=[msg, state, context], outputs=[chat_html, msg, state, context])
    file_upload.change(
        handle_file_upload,
        inputs=[file_upload, state, context],
        outputs=[chat_html, state, context]
    )
if __name__ == "__main__":
    demo.launch()
     

!pip install markdown
!pip install sentence-transformers
!pip install faiss-cpu
!pip install groq
!pip install groq
!pip install sentence-transformers faiss-cpu requests markdown
!pip install PyMuPDF
!apt-get install -y tesseract-ocr
!pip install pytesseract pdf2image Pillow
!pip install deep-translator
     