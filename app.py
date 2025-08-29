import os
import re
import sqlite3
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Poppler path (Apne system ka sahi path dalna)
poppler_path = r"C:\poppler-24.08.0\Library\bin"

# ✅ Flask config
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ✅ Database setup
def init_db():
    conn = sqlite3.connect("resumes.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    career_vision TEXT
                )''')
    conn.commit()
    conn.close()

# Call at app startup
init_db()

# ✅ Extract text from image
def extract_text_from_image(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)

# ✅ Extract text from PDF
def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

# ✅ Parse details from text
def parse_resume(text):
    name = text.split("\n")[0].strip()
    phone_match = re.search(r'\+?\d[\d\s-]{8,}\d', text)
    phone = phone_match.group() if phone_match else None
    email_match = re.search(r'\S+@\S+', text)
    email = email_match.group() if email_match else None
    address_match = re.search(r'(Vasind.*\d{6})', text)
    address = address_match.group() if address_match else None
    career_match = re.search(r'Career Vision(.*)', text, re.IGNORECASE)
    career_vision = career_match.group(1).strip() if career_match else None
    return name, phone, email, address, career_vision

# ✅ Flask route
@app.route("/", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        file = request.files["resume"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # 📄 Detect PDF or Image
            if filename.lower().endswith(".pdf"):
                text = extract_text_from_pdf(file_path)
            else:
                text = extract_text_from_image(file_path)

            # 📌 Parse extracted text
            name, phone, email, address, career_vision = parse_resume(text)

            # 💾 Save to DB
            conn = sqlite3.connect("resumes.db")
            c = conn.cursor()
            c.execute("INSERT INTO resumes (name, phone, email, address, career_vision) VALUES (?, ?, ?, ?, ?)",
                      (name, phone, email, address, career_vision))
            conn.commit()
            conn.close()

            return f"✅ File uploaded & saved successfully!<br><br>📄 Extracted Text:<br><pre>{text}</pre>"

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
