from flask import Flask, jsonify, request, send_from_directory, render_template
import threading
import base64
from io import BytesIO
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path
from langdetect import detect

import file_utils
import tasks

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    folder_path = request.json.get('path')
    files = file_utils.scan_foreign_docs(folder_path)
    return jsonify({'files': files})


@app.route('/api/select-file', methods=['POST'])
def select_file():
    path = request.json.get('path')
    file_path = Path(path)
    text = file_utils.extract_text_from_pdf(file_path)
    try:
        lang = detect(text)
    except Exception:
        lang = 'unknown'
    return jsonify({'name': file_path.name, 'path': path, 'lang': lang})


@app.route('/api/view-pdf', methods=['POST'])
def view_pdf():
    path = request.json['path']
    page = int(request.json.get('page', 1))
    info = pdfinfo_from_path(path)
    images = convert_from_path(path, first_page=page, last_page=page)
    buffered = BytesIO()
    images[0].save(buffered, format='PNG')
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return jsonify({'image': img_str, 'total_pages': info.get('Pages', 1)})


@app.route('/api/translate', methods=['POST'])
def translate():
    path = request.json['path']
    threading.Thread(target=tasks.run_translation, args=(path,)).start()
    return jsonify({'status': 'started'})


if __name__ == '__main__':
    app.run(port=5000)
