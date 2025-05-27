// 전역 변수
let currentFile = null;
let currentPage = 1;
let totalPages = 1;

// 언어 코드를 국기 이모지로 변환하는 함수
function getLanguageFlag(languageCode) {
  const flagMap = {
    // 주요 언어들
    'en': '🇺🇸', // English - 미국 국기
    'ja': '🇯🇵', // Japanese - 일본 국기
    'zh': '🇨🇳', // Chinese - 중국 국기
    'zh-cn': '🇨🇳', // Chinese Simplified - 중국 국기
    'zh-tw': '🇹🇼', // Chinese Traditional - 대만 국기
    'es': '🇪🇸', // Spanish - 스페인 국기
    'fr': '🇫🇷', // French - 프랑스 국기
    'de': '🇩🇪', // German - 독일 국기
    'ru': '🇷🇺', // Russian - 러시아 국기
    'ar': '🇸🇦', // Arabic - 사우디아라비아 국기
    'pt': '🇵🇹', // Portuguese - 포르투갈 국기
    'it': '🇮🇹', // Italian - 이탈리아 국기
    'vi': '🇻🇳', // Vietnamese - 베트남 국기
    'th': '🇹🇭', // Thai - 태국 국기
    'id': '🇮🇩', // Indonesian - 인도네시아 국기
    'hi': '🇮🇳', // Hindi - 인도 국기
    'nl': '🇳🇱', // Dutch - 네덜란드 국기
    'pl': '🇵🇱', // Polish - 폴란드 국기
    'tr': '🇹🇷', // Turkish - 터키 국기
    'sv': '🇸🇪', // Swedish - 스웨덴 국기
    'da': '🇩🇰', // Danish - 덴마크 국기
    'no': '🇳🇴', // Norwegian - 노르웨이 국기
    'fi': '🇫🇮', // Finnish - 핀란드 국기
    'ms': '🇲🇾', // Malay - 말레이시아 국기
    'tl': '🇵🇭', // Filipino - 필리핀 국기
    'fil': '🇵🇭', // Filipino - 필리핀 국기
    
    // 기타 알 수 없는 언어
    'unknown': '🏳️', // 흰색 깃발
    'undefined': '🏳️'
  };
  
  // 언어 코드가 없거나 한국어인 경우 빈 문자열 반환
  if (!languageCode || languageCode === 'ko') {
    return '';
  }
  
  // 언어 코드를 소문자로 변환하고 매핑에서 찾기
  const normalizedCode = languageCode.toLowerCase();
  return flagMap[normalizedCode] || '🌐'; // 매핑에 없는 경우 지구본 이모지 사용
}

// 언어 신뢰도에 따라 국기 이모지 표시 여부 결정
function shouldShowFlag(confidence, isLanguageDetected = true) {
  // 언어가 감지되지 않았거나 신뢰도가 50% 미만인 경우 국기를 표시하지 않음
  return isLanguageDetected && confidence >= 50;
}

// 파일명에 국기 이모지 추가하는 함수
function addFlagToFileName(fileName, languageCode, confidence) {
  if (!shouldShowFlag(confidence, !!languageCode)) {
    return fileName;
  }
  
  const flag = getLanguageFlag(languageCode);
  if (!flag) {
    return fileName;
  }
  
  // 파일명 앞에 국기 이모지 추가
  return `${flag} ${fileName}`;
}

// 폴더 선택 함수 - 상세한 디버깅 포함 + 국기 이모지 추가
async function selectFolder(folderPath) {
  console.log('\n=== 폴더 선택 함수 시작 ===');
  console.log('폴더 경로:', folderPath);
  
  if (!folderPath) {
    console.error('폴더 경로가 없습니다.');
    return;
  }
  
  const fileList = document.getElementById('file-list');
  if (fileList) {
    fileList.innerHTML = '<div class="text-center py-4">폴더를 스캔하는 중...</div>';
  }
  
  try {
    console.log('서버에 요청 전송 중...');
    console.log('요청 URL: /api/select-folder');
    console.log('요청 데이터:', { path: folderPath });
    
    const response = await fetch('/api/select-folder', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ path: folderPath })
    });
    
    console.log('서버 응답 받음');
    console.log('응답 상태:', response.status, response.statusText);
    console.log('응답 헤더:', [...response.headers.entries()]);
    
    if (!response.ok) {
      console.error('서버 응답 오류');
      const errorText = await response.text();
      console.error('오류 내용:', errorText);
      throw new Error(`서버 오류 ${response.status}: ${errorText}`);
    }
    
    console.log('JSON 응답 파싱 중...');
    const data = await response.json();
    console.log('파싱된 응답 데이터:', data);
    
    if (fileList) {
      fileList.innerHTML = '';
      
      if (data.files && Array.isArray(data.files) && data.files.length > 0) {
        console.log(`${data.files.length}개 파일 발견`);
        console.log('파일 목록:', data.files);
        
        data.files.forEach((file, index) => {
          console.log(`파일 ${index + 1}:`, file);
          
          const li = document.createElement('li');
          li.className = 'flex items-center py-2 px-3 hover:bg-gray-100 rounded cursor-pointer';
          
          // 외국어 문서인 경우 특별한 스타일 추가
          if (file.is_foreign) {
            li.classList.add('foreign-doc');
          }
          
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.value = file.path || file;
          checkbox.className = 'mr-3';
          
          const fileName = document.createElement('span');
          // 국기 이모지가 포함된 파일명 사용
          const displayName = addFlagToFileName(
            file.name || (typeof file === 'string' ? file : '알 수 없는 파일'),
            file.language,
            file.confidence || 0
          );
          fileName.textContent = displayName;
          fileName.className = 'flex-1 emoji-font'; // 이모지 폰트 클래스 추가
          
          // 언어 정보 툴팁 추가
          if (file.language && file.language !== 'ko') {
            fileName.title = `언어: ${file.language_name || file.language} (신뢰도: ${file.confidence || 0}%)`;
          }
          
          li.appendChild(checkbox);
          li.appendChild(fileName);
          fileList.appendChild(li);
          
          // 파일 클릭 시 로드
          fileName.onclick = () => {
            const filePath = file.path || file;
            console.log('파일 클릭:', filePath);
            loadFile(filePath);
          };
        });
        
        console.log('파일 목록 UI 생성 완료');
        
        // 폴더 정보 표시
        if (data.message) {
          const statusDiv = document.createElement('div');
          statusDiv.className = 'folder-status mt-2 p-2 bg-blue-50 border-l-4 border-blue-400 text-blue-800 text-sm';
          statusDiv.textContent = data.message;
          fileList.parentElement.insertBefore(statusDiv, fileList);
        }
        
      } else {
        console.log('파일이 없거나 잘못된 응답 형식');
        console.log('data.files:', data.files);
        fileList.innerHTML = '<div class="text-center py-4 text-gray-500">파일이 없습니다.</div>';
      }
    }
    
    console.log('=== 폴더 선택 함수 완료 ===\n');
    
  } catch (error) {
    console.error('=== 폴더 스캔 오류 ===');
    console.error('오류 유형:', error.constructor.name);
    console.error('오류 메시지:', error.message);
    console.error('전체 오류:', error);
    
    if (fileList) {
      fileList.innerHTML = `
        <div class="text-center py-4 text-red-500">
          <p>오류: ${error.message}</p>
          <button onclick="selectFolder('${folderPath}')" class="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm">
            다시 시도
          </button>
        </div>
      `;
    }
  }
}

// 파일 로드 함수
function loadFile(filePath) {
  console.log('파일 로드:', filePath);
  const ext = filePath.split('.').pop().toLowerCase();
  
  if (ext === 'pdf') {
    loadPDFView(filePath, 1);
  } else {
    loadDocumentView(filePath);
  }
}

// PDF 로드
function loadPDFView(filePath, page = 1) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  fetch('/api/view-pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath, page: page })
  })
  .then(res => res.json())
  .then(data => {
    if (data.image) {
      viewer.innerHTML = `<img src="data:image/png;base64,${data.image}" style="max-width: 100%;">`;
      currentFile = filePath;
      currentPage = page;
      totalPages = data.total_pages || 1;
      
      updatePageControls();
    } else {
      viewer.innerHTML = '<p>PDF를 불러올 수 없습니다.</p>';
    }
  })
  .catch(error => {
    console.error('PDF 로드 오류:', error);
    viewer.innerHTML = `<p>오류: ${error.message}</p>`;
  });
}

// 문서 로드 (텍스트 파일 등)
function loadDocumentView(filePath) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  fetch(`/api/read-file?path=${encodeURIComponent(filePath)}`)
    .then(res => res.json())
    .then(data => {
      if (data.content) {
        viewer.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace; padding: 20px;">${data.content}</pre>`;
      } else {
        viewer.innerHTML = '<p>파일을 읽을 수 없습니다.</p>';
      }
    })
    .catch(error => {
      console.error('파일 로드 오류:', error);
      viewer.innerHTML = `<p>오류: ${error.message}</p>`;
    });
}

// 페이지 컨트롤 업데이트
function updatePageControls() {
  const pageInfo = document.getElementById('page-info');
  const controls = document.getElementById('page-controls');
  
  if (pageInfo) {
    pageInfo.textContent = `${currentPage} / ${totalPages}`;
  }
  
  if (controls) {
    controls.classList.toggle('hidden', totalPages <= 1);
  }
}

// 폴더 선택 트리거 - 강화된 디버깅 버전
function triggerFolderSelect() {
  console.log('=== frontend.js triggerFolderSelect 시작 ===');
  
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_folder) {
    console.log('API 호출 시작');
    
    try {
      const result = window.pywebview.api.open_folder();
      console.log('API 호출 결과:', result);
      
      if (result && typeof result.then === 'function') {
        console.log('Promise 처리 시작');
        result.then(folderPath => {
          console.log('Promise 완료, 선택된 폴더:', folderPath);
          
          if (folderPath && folderPath.trim()) {
            console.log('selectFolder 함수 호출 시작');
            console.log('selectFolder 함수 존재 여부:', typeof selectFolder);
            
            // selectFolder 직접 호출
            selectFolder(folderPath);
            console.log('selectFolder 함수 호출 완료');
          } else {
            console.log('폴더 선택 취소됨 또는 빈 경로');
          }
        }).catch(error => {
          console.error('Promise 오류:', error);
          alert('폴더 선택 중 오류가 발생했습니다: ' + error.message);
        });
      } else if (result) {
        console.log('동기 결과 처리:', result);
        selectFolder(result);
      } else {
        console.log('결과가 null 또는 undefined');
      }
    } catch (error) {
      console.error('API 호출 중 예외 발생:', error);
      alert('API 호출 중 오류가 발생했습니다: ' + error.message);
    }
  } else {
    console.error('API 상태 확인:');
    console.log('- window.pywebview:', !!window.pywebview);
    console.log('- window.pywebview.api:', !!window.pywebview?.api);
    console.log('- open_folder 함수:', !!window.pywebview?.api?.open_folder);
    alert('폴더 선택 기능이 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
  }
}

// 파일 선택 트리거
function triggerFileSelect() {
  console.log('파일 선택 트리거');
  
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_file) {
    const result = window.pywebview.api.open_file();
    
    if (result && typeof result.then === 'function') {
      result.then(filePath => {
        if (filePath) {
          loadFile(filePath);
        }
      }).catch(error => {
        console.error('파일 선택 오류:', error);
      });
    } else if (result) {
      loadFile(result);
    }
  } else {
    alert('파일 선택 기능이 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
  }
}

// 번역 기능
function translateSelected() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  
  if (checkboxes.length === 0) {
    alert('번역할 파일을 선택해주세요.');
    return;
  }
  
  checkboxes.forEach(checkbox => {
    const filePath = checkbox.value;
    startTranslation(filePath);
  });
}

function startTranslation(filePath) {
  const rightPanel = document.getElementById('right-panel');
  rightPanel.innerHTML = `
    <div class="p-4">
      <h3>번역 중...</h3>
      <p>${filePath.split(/[\\/]/).pop()}</p>
    </div>
  `;
  
  fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  })
  .then(res => res.json())
  .then(data => {
    console.log('번역 시작:', data);
    checkTranslationStatus(filePath);
  })
  .catch(error => {
    console.error('번역 오류:', error);
    rightPanel.innerHTML = `<div class="p-4 text-red-500">번역 오류: ${error.message}</div>`;
  });
}

function checkTranslationStatus(filePath) {
  fetch(`/api/translation-status?path=${encodeURIComponent(filePath)}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === 'completed') {
        showTranslationResult(filePath);
      } else if (data.status === 'error') {
        document.getElementById('right-panel').innerHTML = 
          `<div class="p-4 text-red-500">번역 오류: ${data.error}</div>`;
      } else {
        setTimeout(() => checkTranslationStatus(filePath), 2000);
      }
    })
    .catch(error => {
      console.error('상태 확인 오류:', error);
      setTimeout(() => checkTranslationStatus(filePath), 5000);
    });
}

function showTranslationResult(filePath) {
  fetch(`/api/translation-result?path=${encodeURIComponent(filePath)}`)
    .then(res => res.json())
    .then(data => {
      const rightPanel = document.getElementById('right-panel');
      if (data.content) {
        rightPanel.innerHTML = `
          <div class="p-4">
            <h3 class="text-lg font-semibold mb-4">번역 결과</h3>
            <div class="bg-white p-4 rounded border max-h-96 overflow-y-auto">
              <pre class="whitespace-pre-wrap text-sm">${data.content}</pre>
            </div>
          </div>
        `;
      } else {
        rightPanel.innerHTML = `<div class="p-4 text-red-500">번역 결과를 불러올 수 없습니다.</div>`;
      }
    })
    .catch(error => {
      console.error('번역 결과 로드 오류:', error);
    });
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
  console.log('페이지 로드 완료');
  
  // 커스텀 이벤트 리스너 (app.py에서 발생시키는 이벤트)
  window.addEventListener('folderSelected', (event) => {
    console.log('folderSelected 이벤트 수신:', event.detail);
    selectFolder(event.detail);
  });
  
  // 번역 버튼
  const translateBtn = document.getElementById('translate-btn');
  if (translateBtn) {
    translateBtn.addEventListener('click', translateSelected);
  }
  
  // 페이지 버튼들  
  const prevBtn = document.getElementById('prev-page');
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        loadPDFView(currentFile, currentPage - 1);
      }
    });
  }
  
  const nextBtn = document.getElementById('next-page');
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        loadPDFView(currentFile, currentPage + 1);
      }
    });
  }
  
  // API 준비 확인
  let attempts = 0;
  const checkAPI = setInterval(() => {
    attempts++;
    if (window.pywebview && window.pywebview.api) {
      console.log('API 준비 완료');
      clearInterval(checkAPI);
    } else if (attempts > 50) {
      console.warn('API 초기화 시간 초과');
      clearInterval(checkAPI);
    }
  }, 100);
});