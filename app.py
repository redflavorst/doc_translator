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
    # 개발자 도구를 여는 대신 브라우저에서 열기
    webbrowser.open('http://localhost:5000')
    return True

# 전역 API 클래스
class PyWebViewAPI:
    def open_file(self):
        """파일 선택 대화상자를 엽니다."""
        try:
            result = open_file_dialog()
            print(f"선택된 파일: {result}")
            return result
        except Exception as e:
            print(f"파일 선택 오류: {e}")
            return ""
    
    def open_folder(self):
        """폴더 선택 대화상자를 엽니다."""
        try:
            result = open_folder_dialog()
            print(f"선택된 폴더: {result}")
            return result
        except Exception as e:
            print(f"폴더 선택 오류: {e}")
            return ""
    
    def open_dev_tools(self):
        """개발자 도구를 엽니다."""
        try:
            return open_dev_tools()
        except Exception as e:
            print(f"개발자 도구 열기 오류: {e}")
            return False

def run_flask():
    from server import app
    app.run(port=5000, debug=False, use_reloader=False)

def create_window():
    # Flask 서버를 별도 스레드에서 실행
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Flask 서버가 시작될 때까지 잠시 대기
    time.sleep(2)
    
    # API 인스턴스 생성
    api = PyWebViewAPI()
    
    # 웹뷰 창 생성
    window = webview.create_window(
        '문서 번역기',
        'http://localhost:5000',
        js_api=api,  # API 객체를 직접 전달
        min_size=(1024, 768),
        width=1200,
        height=800
    )
    
    # 페이지 로드 완료 시 실행할 함수
    def on_loaded():
        print("페이지 로드 완료 - API 초기화 시작")
        
        # 초기화 스크립트
        init_script = """
        console.log('=== PyWebView API 초기화 시작 ===');
        
        // 현재 상태 확인
        console.log('window.pywebview:', window.pywebview);
        console.log('window.pywebview.api:', window.pywebview?.api);
        
        // API가 로드될 때까지 대기하는 함수
        function waitForAPI() {
            return new Promise((resolve) => {
                const checkAPI = () => {
                    if (window.pywebview && window.pywebview.api) {
                        console.log('API 발견됨:', Object.keys(window.pywebview.api));
                        resolve();
                    } else {
                        console.log('API 대기 중...');
                        setTimeout(checkAPI, 100);
                    }
                };
                checkAPI();
            });
        }
        
        // API 초기화
        waitForAPI().then(() => {
            console.log('=== API 초기화 완료 ===');
            console.log('사용 가능한 API 함수들:', Object.keys(window.pywebview.api));
            
            // API 테스트
            if (window.pywebview.api.open_folder) {
                console.log('open_folder API 사용 가능');
            } else {
                console.error('open_folder API 사용 불가');
            }
            
            if (window.pywebview.api.open_file) {
                console.log('open_file API 사용 가능');
            } else {
                console.error('open_file API 사용 불가');
            }
        });
        
        // 전역 함수로도 노출 (백업용) - selectFolder를 직접 호출하도록 수정
        window.triggerFolderSelect = function() {
            console.log('=== app.py triggerFolderSelect 호출됨 ===');
            
            if (window.pywebview && window.pywebview.api && window.pywebview.api.open_folder) {
                console.log('open_folder API 호출 시작');
                const result = window.pywebview.api.open_folder();
                console.log('open_folder API 호출 결과:', result);
                
                if (result && typeof result.then === 'function') {
                    return result.then(folderPath => {
                        console.log('폴더 선택 완료:', folderPath);
                        if (folderPath && folderPath.trim()) {
                            console.log('selectFolder 함수 호출 시도');
                            
                            // window.selectFolder 직접 호출
                            if (typeof window.selectFolder === 'function') {
                                console.log('window.selectFolder 함수 발견, 호출 중...');
                                window.selectFolder(folderPath);
                            } else {
                                console.error('window.selectFolder 함수를 찾을 수 없습니다.');
                                console.log('전역 함수 목록:', Object.keys(window).filter(k => typeof window[k] === 'function' && k.includes('select')));
                            }
                        }
                        return folderPath;
                    }).catch(error => {
                        console.error('폴더 선택 중 오류 발생:', error);
                        throw error;
                    });
                } else if (result) {
                    console.log('동기 결과:', result);
                    if (result.trim() && typeof window.selectFolder === 'function') {
                        window.selectFolder(result);
                    }
                    return result;
                }
            } else {
                console.error('API가 준비되지 않음');
                alert('API가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
                return Promise.resolve('');
            }
        };
        
        window.triggerFileSelect = function() {
            console.log('triggerFileSelect 호출됨');
            if (window.pywebview && window.pywebview.api && window.pywebview.api.open_file) {
                return window.pywebview.api.open_file();
            } else {
                console.error('API가 준비되지 않음');
                alert('API가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
                return Promise.resolve('');
            }
        };
        """
        
        # 초기화 스크립트 실행
        try:
            window.evaluate_js(init_script)
            print("초기화 스크립트 실행 완료")
        except Exception as e:
            print(f"초기화 스크립트 실행 오류: {e}")
    
    # 이벤트 핸들러 등록
    window.events.loaded += on_loaded
    
    print("웹뷰 창 생성 완료 - 시작 중...")
    
    # 웹뷰 실행
    webview.start(debug=True)

if __name__ == '__main__':
    create_window()