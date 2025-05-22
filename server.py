from flask import Flask, jsonify, request, send_from_directory, render_template
import threading
import base64
from io import BytesIO
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path
from langdetect import detect
from PIL import Image, ImageEnhance

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


@app.route('/api/select-file', methods=['POST'])
def select_file():
    path = request.json.get('path')
    file_path = Path(path)
    md_path = file_utils.convert_pdf_to_markdown(file_path)
    # 필요하다면, 마크다운 파일에서 내용을 읽어올 수도 있습니다.
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        lang = detect(text)
    except Exception:
        lang = 'unknown'
    return jsonify({'name': file_path.name, 'path': path, 'lang': lang})


@app.route('/api/view-pdf', methods=['POST'])
def view_pdf():
    path = request.json['path']
    page = int(request.json.get('page', 1))
    dpi = int(request.json.get('dpi', 200))  # 기본 DPI를 200으로 설정 (기본값은 100)
    
    # PDF에서 이미지 변환 시 DPI를 높여 선명도 향상
    info = pdfinfo_from_path(path)
    images = convert_from_path(
        path, 
        first_page=page, 
        last_page=page,
        dpi=dpi,  # DPI 증가
        thread_count=4,  # 멀티스레딩으로 성능 개선
        poppler_path=POPPLER_PATH if 'POPPLER_PATH' in globals() else None
    )
    
    # 이미지 품질 향상을 위해 300%로 확대 (선택사항)
    if images:
        width, height = images[0].size
        # 이미지 크기를 2배로 확대 (필요에 따라 조정 가능)
        new_size = (int(width * 1.5), int(height * 1.5))
        resized_image = images[0].resize(new_size, Image.Resampling.LANCZOS)
        
        # 이미지를 더 선명하게 처리
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(resized_image)
        enhanced_image = enhancer.enhance(1.5)  # 선명도 50% 증가
        
        buffered = BytesIO()
        enhanced_image.save(buffered, format='PNG', quality=95, dpi=(dpi, dpi))
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'image': img_str, 
            'total_pages': info.get('Pages', 1),
            'dpi': dpi,
            'original_size': f"{width}x{height}",
            'display_size': f"{new_size[0]}x{new_size[1]}"
        })
    
    return jsonify({'error': '이미지를 로드할 수 없습니다.'}), 500


@app.route('/api/translate', methods=['POST'])
def translate():
    path = request.json['path']
    threading.Thread(target=tasks.run_translation, args=(path,)).start()
    return jsonify({'status': 'started'})


@app.route('/api/read-file')
def read_file():
    import os
    from pathlib import Path
    
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except UnicodeDecodeError:
        try:
            # UTF-8 실패 시 다른 인코딩 시도
            with open(file_path, 'r', encoding='cp949') as f:
                content = f.read()
            return jsonify({'content': content})
        except Exception as e:
            return jsonify({'error': f'파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/download')
def download_file():
    import os
    from flask import send_file, safe_join
    
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return jsonify({'error': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(port=5000)
