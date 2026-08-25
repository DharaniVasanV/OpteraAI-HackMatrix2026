from flask import Flask, render_template, request, jsonify
from db import init_db, get_all_documents, search_documents, clear_documents, get_stats
from document_agent import process, search_index

app = Flask(__name__)

SAMPLE_INPUTS = {
    "hackathon": """Subject: Smart India Hackathon 2025 - Registration Open

Dear Participant,

Please find attached the Problem Statement PDF and Rulebook for Smart India Hackathon 2025.

Download Problem Statement: https://sih.gov.in/downloads/problem_statement_2025.pdf
Download Rulebook: https://sih.gov.in/downloads/rulebook_2025.pdf
Register here: https://sih.gov.in/register

Deadline: 30/07/2025
Prize Pool: INR 1,00,000
Organized by: Ministry of Education, Government of India
Contact: support@sih.gov.in""",

    "internship": """Subject: Internship Offer Letter - Amazon SDE Intern 2025

Congratulations! Please download your offer letter from the link below.
Offer Letter: https://amazon.jobs/downloads/offer_letter_2025.pdf
Joining Date: 15/08/2025
Stipend: INR 80,000/month
Contact HR: hr-intern@amazon.com
Accept Offer: https://amazon.jobs/accept?token=abc123
Deadline to accept: 10/07/2025""",

    "certificate": """Congratulations! Your certificate for completing the AWS Cloud Practitioner course is ready.

Download Certificate: https://aws.amazon.com/training/certificates/aws_cloud_practitioner_2025.pdf
Issued by: Amazon Web Services
Issue Date: 01/07/2025
Expiry Date: 01/07/2028
Credential ID: AWS-CP-2025-XYZ
Verify at: https://aws.amazon.com/verify/credential""",

    "invoice": """Invoice #INV-2025-0042

Please find your invoice attached.
Download: https://billing.example.com/invoices/INV-2025-0042.pdf
Amount Due: INR 12,500
Due Date: 15/07/2025
GST No: 29ABCDE1234F1Z5
Contact: billing@example.com""",

    "research": """New Research Paper Published

Title: Transformer Models for Document Classification
Download PDF: https://arxiv.org/pdf/2025.12345.pdf
Authors: Dr. John Smith, Dr. Jane Doe
Journal: IEEE Transactions on AI
Abstract: This paper presents a novel approach to document classification using transformer-based models.
Published: 25/06/2025"""
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def api_process():
    data = request.json
    text = data.get("text", "").strip()
    auto_download = data.get("auto_download", False)
    if not text:
        return jsonify({"error": "Input text is required"}), 400
    result = process(text, auto_download=auto_download)
    return jsonify(result)


@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    return jsonify(search_documents(query))


@app.route("/api/index", methods=["GET"])
def api_index():
    return jsonify(get_all_documents())


@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(get_stats())


@app.route("/api/samples", methods=["GET"])
def api_samples():
    return jsonify(SAMPLE_INPUTS)


@app.route("/api/clear_index", methods=["POST"])
def api_clear_index():
    clear_documents()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
