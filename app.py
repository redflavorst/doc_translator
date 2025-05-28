import sys
import os
import threading
import webbrowser
from pathlib import Path
import webview
import time

def open_file_dialog():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("All supported", "*.pdf *.doc *.docx *.txt *.html"),
            ("PDF files", "*.pdf"),
            ("Word files", "*.doc *.docx"),
            ("Text files", "*.txt"),
            ("HTML files", "*.html"),
        ]
    )
    root.destroy()
    return file_path

def open_folder_dialog():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    root.destroy()
    return folder

def open_dev_tools():
    webbrowser.open('http://localhost:5000')
    return True

# 전역 API 클래스
class PyWebViewAPI:
    def open_file(self):
        try:
            result = open_file_dialog()
            print(f"선택된 파일: {result}")
            return result
        except Exception as e:
            print(f"파일 선택 오류: {e}")
            return ""
    
    def open_folder(self):
        try:
            result = open_folder_dialog()
            print(f"선택된 폴더: {result}")
            return result
        except Exception as e:
            print(f"폴더 선택 오류: {e}")
            return ""
    
    def open_dev_tools(self):
        try:
            return open_dev_tools()
        except Exception as e:
            print(f"개발자 도구 열기 오류: {e}")
            return False

def run_flask():
    from server import app
    app.run(host='localhost', port=5000, debug=False, use_reloader=False)

def create_window():
    # Flask 서버를 먼저 시작
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 서버가 시작될 때까지 잠깐 대기 (최소한)
    time.sleep(1)
    
    # API 인스턴스 생성
    api = PyWebViewAPI()
    
    # 웹뷰 창 생성
    window = webview.create_window(
        '문서 번역기',
        'http://localhost:5000',
        js_api=api,
        min_size=(1024, 768),
        width=1200,
        height=800
    )
    
    # 페이지 로드 완료 시 실행할 함수
    def on_loaded():
        print("페이지 로드 완료 - API 초기화")
        
        # 간단한 API 초기화
        init_script = """
        // API 준비되면 전역 함수 등록
        setTimeout(() => {
            if (window.pywebview && window.pywebview.api) {
                console.log('API 준비 완료');
                
                window.triggerFolderSelect = function() {
                    const result = window.pywebview.api.open_folder();
                    if (result && typeof result.then === 'function') {
                        return result.then(path => {
                            if (path && typeof window.selectFolder === 'function') {
                                window.selectFolder(path);
                            }
                            return path;
                        });
                    } else if (result && typeof window.selectFolder === 'function') {
                        window.selectFolder(result);
                    }
                    return result;
                };
                
                window.triggerFileSelect = function() {
                    return window.pywebview.api.open_file();
                };
            }
        }, 500);
        """
        
        try:
            window.evaluate_js(init_script)
            print("API 초기화 완료")
        except Exception as e:
            print(f"API 초기화 오류: {e}")
    
    # 이벤트 핸들러 등록
    window.events.loaded += on_loaded
    
    print("웹뷰 시작...")
    
    # 웹뷰 실행
    webview.start(debug=True)

if __name__ == '__main__':
    create_window()