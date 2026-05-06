from flask import Blueprint, request, jsonify, send_file
import io
import os
from werkzeug.utils import secure_filename
from crypto_helper import hash_file_data, generate_rsa_keys, sign_data, verify_signature
from pdf_helper import append_signature_page, get_original_hash_from_pdf

crypto_bp = Blueprint('crypto', __name__)


@crypto_bp.route('/generate-keys', methods=['GET'])
def generate_keys_route():
    priv_pem, pub_pem = generate_rsa_keys()
    return jsonify({
        "status": "success",
        "private_key": priv_pem,
        "public_key": pub_pem
    })


@crypto_bp.route('/sign', methods=['POST'])
def sign_pdf_route():
    if 'file' not in request.files or 'private_key' not in request.form:
        return jsonify({"error": "File PDF dan private_key wajib dikirim!"}), 400

    pdf_file = request.files['file']
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Format file ditolak! Hanya menerima dokumen PDF."}), 400

    try:
        raw_name = pdf_file.filename or "signed_document"
        original_filename = os.path.splitext(secure_filename(raw_name))[0] or "signed_document"
        download_filename = f"{original_filename}_signed.pdf"
    except Exception:
        download_filename = "signed_document.pdf"

    raw_private_key = request.form['private_key'].replace('\\n', '\n')
    private_key_pem = raw_private_key.encode('utf-8')

    pdf_data = pdf_file.read()
    file_hash = hash_file_data(pdf_data)
    original_hash_hex = file_hash.hex()

    try:
        signature_b64 = sign_data(file_hash, private_key_pem)
        print("\n" + "="*50)
        print("👉 COPY SIGNATURE INI UNTUK VERIFIKASI:")
        print(signature_b64)
        print(f"👉 ORIGINAL HASH HEX: {original_hash_hex}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"[ERROR SIGNING] Kunci salah atau rusak: {str(e)}")
        return jsonify({"error": "Private Key tidak valid atau format rusak!"}), 400

    output_pdf = append_signature_page(
        io.BytesIO(pdf_data),
        signature_b64,
        original_hash_hex=original_hash_hex
    )

    print(f"[DEBUG] download_filename: {download_filename}")
    response = send_file(output_pdf, mimetype='application/pdf', as_attachment=True, download_name=download_filename)
    response.headers['X-Signature'] = signature_b64
    return response


@crypto_bp.route('/verify', methods=['POST'])
def verify_pdf_route():
    if 'file' not in request.files or 'signature' not in request.form or 'public_key' not in request.form:
        return jsonify({"error": "Data tidak lengkap! Butuh file, signature, dan public_key."}), 400

    pdf_file = request.files['file']
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Hanya menerima dokumen PDF untuk dicek."}), 400

    raw_public_key = request.form['public_key'].replace('\\n', '\n')
    public_key_pem = raw_public_key.encode('utf-8')
    signature_b64 = request.form['signature'].strip()

    pdf_data = pdf_file.read()

    original_hash_hex = get_original_hash_from_pdf(pdf_data)
    if not original_hash_hex:
        return jsonify({
            "status": "invalid",
            "message": "PALSU! Metadata hash tidak ditemukan. Dokumen bukan hasil signing sistem ini."
        })

    try:
        original_hash_bytes = bytes.fromhex(original_hash_hex)
    except Exception:
        return jsonify({"status": "invalid", "message": "PALSU! Format hash di metadata rusak."})

    try:
        verify_signature(signature_b64, original_hash_bytes, public_key_pem)
        return jsonify({"status": "valid", "message": "Dokumen ASLI dan tidak ada perubahan."})
    except Exception as e:
        print(f"[ERROR VERIFY] Percobaan gagal: {str(e)}")
        return jsonify({"status": "invalid", "message": "PALSU! Dokumen telah diedit atau kunci salah."})
