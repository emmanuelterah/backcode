import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS
import openai
from PyPDF2 import PdfFileReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set the secret key for session management (ensure it's properly set in production)
app.secret_key = os.urandom(24)

# CORS configuration to handle cross-origin requests
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://your-production-site.com"])

# Database configuration using SQLite for now (you can replace this with another DB if needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ztea.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and migration engine
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Set your OpenAI API key securely from the environment
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Flask-RESTful API
api = Api(app)

# Model to store PDF text content
class PDFContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    def __init__(self, text):  # Corrected method name to __init__
        self.text = text



def create_tables():
    db.create_all()

# Endpoint for uploading PDF and extracting text
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File is not a PDF'}), 400

    # Open the PDF file with PyPDF2 and extract the text
    try:
        pdf_reader = PdfFileReader(file)
        pdf_text = ""

        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        # Store the PDF text in the database
        pdf_content = PDFContent(text=pdf_text)
        db.session.add(pdf_content)
        db.session.commit()

        return jsonify({'message': 'PDF content indexed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint for querying the indexed PDFs
@app.route('/query_pdf', methods=['POST'])
def query_pdf():
    query = request.json.get('query')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Get all the stored PDF text from the database
    pdf_texts = [pdf.text for pdf in PDFContent.query.all()]

    if not pdf_texts:
        return jsonify({'error': 'No PDF content found in the database'}), 404

    combined_pdf_text = "\n".join(pdf_texts)

    # Combine the PDF text and the query in a prompt for OpenAI
    prompt = f"The following is extracted text from a PDF:\n{combined_pdf_text}\n\nAnswer the following query: {query}"

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1000
        )
        return jsonify({'response': response.choices[0].text.strip()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
