from flask import Flask, jsonify, request, send_from_directory, render_template
import threading
import base64
from io import BytesIO
from pdf2image import convert_from_path

import file_utils
import tasks

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    folder_path = request.json.get('path')
    files = file_utils.scan_pdfs(folder_path)
    return jsonify({'files': files})


@app.route('/api/view-pdf', methods=['POST'])
def view_pdf():
    path = request.json['path']
    images = convert_from_path(path, first_page=1, last_page=1)
    buffered = BytesIO()
    images[0].save(buffered, format='PNG')
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return jsonify({'image': img_str})


@app.route('/api/translate', methods=['POST'])
def translate():
    path = request.json['path']
    threading.Thread(target=tasks.run_translation, args=(path,)).start()
    return jsonify({'status': 'started'})


if __name__ == '__main__':
    app.run(port=5000)
