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


@app.route('/api/check-language', methods=['POST'])
def check_language():
    path = request.json.get('path')
    file_path = Path(path)
    
    # PDF에서 텍스트 추출하여 언어 감지
    try:
        # PDF에서 처음 100KB만 읽어서 언어 감지
        with open(file_path, 'rb') as f:
            text = f.read(102400).decode('utf-8', errors='ignore')
        lang = detect(text) if text.strip() else "unknown"
    except Exception:
        lang = 'unknown'
    
    return jsonify({'name': file_path.name, 'path': path, 'lang': lang})


@app.route('/api/select-file', methods=['POST'])
def select_file():
    path = request.json.get('path')
    file_path = Path(path)
    
    try:
        # PDF를 마크다운으로 변환
        md_path = file_utils.convert_pdf_to_markdown(file_path)
        print(f"마크다운 변환 완료: {md_path}")
        
        # 마크다운 파일에서 내용을 읽어와서 언어 감지
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        try:
            lang = detect(text)
        except Exception:
            lang = 'unknown'
        
        return jsonify({
            'name': file_path.name, 
            'path': path, 
            'lang': lang,
            'markdown_path': md_path,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")
        return jsonify({
            'name': file_path.name, 
            'path': path, 
            'lang': 'unknown',
            'markdown_path': None,
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/view-pdf', methods=['POST'])
def view_pdf():
    path = request.json['path']
    page = int(request.json.get('page', 1))
    dpi = int(request.json.get('dpi', 200))  # 기본 DPI를 200으로 설정 (기본값은 100)
    
    try:
        # PDF에서 이미지 변환 시 DPI를 높여 선명도 향상
        info = pdfinfo_from_path(path)
        images = convert_from_path(
            path, 
            first_page=page, 
            last_page=page,
            dpi=dpi,  # DPI 증가
            thread_count=4,  # 멀티스레딩으로 성능 개선
            poppler_path=globals().get('POPPLER_PATH', None)
        )
        
        # 이미지 품질 향상을 위해 300%로 확대 (선택사항)
        if images:
            width, height = images[0].size
            # 이미지 크기를 2배로 확대 (필요에 따라 조정 가능)
            new_size = (int(width * 1.5), int(height * 1.5))
            resized_image = images[0].resize(new_size, Image.Resampling.LANCZOS)
            
            # 이미지를 더 선명하게 처리
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
    
    except Exception as e:
        print(f"PDF 뷰어 오류: {e}")
        return jsonify({'error': f'PDF를 로드하는 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/translate', methods=['POST'])
def translate():
    path = request.json['path']
    # 데몬 스레드로 설정하여 프로그램 종료 시 자동으로 종료되도록 함
    thread = threading.Thread(target=tasks.run_translation, args=(path,), daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'path': path})


@app.route('/api/translation-status')
def translation_status():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '경로가 지정되지 않았습니다.'}), 400
    
    # 번역 상태 확인
    status_data = tasks.progress_manager.get(path)
    if status_data is None:
        return jsonify({'status': 'not_found'})
    
    # 상태가 디셔너리인 경우 (새 형식)
    if isinstance(status_data, dict):
        response = {
            'status': status_data.get('status', 'unknown'),
        }
        
        # 번역 진행 상황 정보 추가
        if status_data.get('status') == 'running':
            # 총 청크 수와 완료된 청크 수
            total_chunks = status_data.get('total_chunks', 0)
            chunks_completed = status_data.get('chunks_completed', 0)
            
            # 진행률 계산 (0-100%)
            progress_percent = (chunks_completed / total_chunks * 100) if total_chunks > 0 else 0
            
            response.update({
                'total_chunks': total_chunks,
                'current_chunk': status_data.get('current_chunk', 0),
                'chunks_completed': chunks_completed,
                'progress_percent': progress_percent,
                'chunks_info': status_data.get('chunks_info', [])
            })
            
            # 부분 결과 추가 (선택적)
            include_partial = request.args.get('include_partial', 'false').lower() == 'true'
            if include_partial:
                partial_results = tasks.progress_manager.get_partial_results(path)
                response['partial_results'] = partial_results
        
        # 오류 정보 추가
        if status_data.get('status') == 'error' and 'error' in status_data:
            response['error'] = status_data['error']
            
        return jsonify(response)
    
    # 이전 형식의 상태 처리 (하위 호환성)
    elif status_data == 'running':
        return jsonify({'status': 'running'})
    elif status_data == 'done':
        return jsonify({'status': 'completed'})
    else:
        return jsonify({'status': status_data})


@app.route('/api/translation-result')
def translation_result():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '경로가 지정되지 않았습니다.'}), 400
    
    file_path = Path(path)
    translated_path = tasks.TRANSLATED_DIR / (file_path.stem + '.txt')
    
    if not translated_path.exists():
        return jsonify({'error': '번역 파일을 찾을 수 없습니다.'}), 404
    
    try:
        with open(translated_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': f'번역 파일을 읽는 중 오류가 발생했습니다: {str(e)}'}), 500


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
    from flask import send_file
    
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
    # 서버 종료 시 자원을 정리하도록 설정
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(port=5000, threaded=True, use_reloader=False)