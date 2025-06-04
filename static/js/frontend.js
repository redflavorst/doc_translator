// 전역 변수
let currentFile = null;

// 새로운 공통 함수: 마크다운을 가져와 파싱합니다.
async function fetchAndParseMarkdown(filePath, apiEndpoint) {
  if (!filePath) {
    return Promise.reject(new Error('파일 경로가 없습니다.'));
  }

  try {
    // API 엔드포인트에 이미 쿼리 문자열 시작인 '?'가 포함되어 있을 수 있으므로, 
    // 경로 파라미터만 추가하도록 수정합니다.
    const apiUrl = `${apiEndpoint}?path=${encodeURIComponent(filePath)}`;
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `서버 오류: ${response.status}`);
    }

    if (data.content !== undefined) {
      if (typeof marked === 'undefined') {
        throw new Error('Markdown 라이브러리(marked.js)를 로드할 수 없습니다.');
      }
      return marked.parse(data.content);
    } else {
      throw new Error('마크다운 내용을 찾을 수 없습니다 (잘못된 서버 응답).');
    }
  } catch (error) {
    console.error(`Error loading/parsing markdown from ${apiEndpoint} for ${filePath}:`, error);
    throw error; // 호출자가 오류를 처리하도록 다시 throw
  }
}

let currentPage = 1;
let totalPages = 1;
let translationStatusInterval = null;  // 번역 상태 체크를 위한 인터벌 ID
let currentOriginalMarkdownPath = null; // 원본 마크다운 파일 경로
let leftPanelViewMode = 'pdf'; // 좌측 패널 보기 모드: 'pdf' 또는 'md'

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
          fileName.onclick = async () => {
            const filePath = file.path || file;
            console.log('파일 클릭:', filePath, '원본 MD 경로:', file.original_md_path);
            const fileType = file.type || 'pdf'; // 기본값은 PDF
            const originalMdPath = file.original_md_path || null;
            loadFile(filePath, fileType, originalMdPath);
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
async function loadFile(filePath, fileType, originalMdPath) {
  console.log('파일 로드:', filePath, '타입:', fileType);
  // Reset markdown path and disable button first
  currentOriginalMarkdownPath = null;
  const viewMdBtn = document.getElementById('view-md-btn');
  if (viewMdBtn) {
    viewMdBtn.disabled = true;
    viewMdBtn.classList.remove('bg-blue-500', 'text-white');
    viewMdBtn.classList.add('bg-neutral-200', 'text-neutral-700');
  }
  document.getElementById('view-pdf-btn').classList.add('bg-blue-500', 'text-white');
  document.getElementById('view-pdf-btn').classList.remove('bg-neutral-200', 'text-neutral-700');
  leftPanelViewMode = 'pdf'; // Reset to PDF view by default
  currentOriginalMarkdownPath = originalMdPath; // 전달받은 원본 MD 경로 설정

  if (viewMdBtn) {
      viewMdBtn.disabled = !currentOriginalMarkdownPath;
      if (currentOriginalMarkdownPath) {
        viewMdBtn.classList.remove('bg-neutral-200', 'text-neutral-700');
        // viewMdBtn.classList.add('bg-blue-500', 'text-white'); // 활성화 시 스타일은 토글 함수에서 관리
      } else {
        viewMdBtn.classList.remove('bg-blue-500', 'text-white');
        viewMdBtn.classList.add('bg-neutral-200', 'text-neutral-700');
      }
  }

  if (fileType === 'pdf' || filePath.toLowerCase().endsWith('.pdf')) {
    loadPDFView(filePath, 1);
  } else {
    loadDocumentView(filePath);
  }

  // Update right panel with translation or placeholder
  displayTranslatedContentOrPlaceholder(filePath);
}

// PDF 로드 및 좌측 패널 보기 모드 관리
async function loadPDFView(filePath, page = 1) {
  console.log(`[VIEWER] PDF 로드 요청: ${filePath}, 페이지: ${page}`);
  currentFile = filePath;
  currentPage = page;
  leftPanelViewMode = 'pdf';

  const viewerContainer = document.getElementById('viewer-container');
  const pageControls = document.getElementById('page-controls');
  const pageInfo = document.getElementById('page-info');
  const viewPdfBtn = document.getElementById('view-pdf-btn');
  const viewMdBtn = document.getElementById('view-md-btn');

  viewerContainer.innerHTML = '<div class="flex items-center justify-center h-full text-neutral-400"><p>PDF 로딩 중...</p></div>';
  pageControls.classList.remove('hidden');
  pageInfo.textContent = '';

  // Update button styles
  if (viewPdfBtn && viewMdBtn) {
    viewPdfBtn.classList.add('bg-blue-500', 'text-white');
    viewPdfBtn.classList.remove('bg-neutral-200', 'text-neutral-700');
    viewMdBtn.classList.remove('bg-blue-500', 'text-white');
    viewMdBtn.classList.add('bg-neutral-200', 'text-neutral-700');
  }

  // Clear right panel when loading a new PDF
  const rightPanel = document.getElementById('right-panel');
  if (rightPanel) {
      rightPanel.innerHTML = '<div class="text-neutral-500 text-center py-8">번역된 내용이 여기에 표시됩니다.</div>';
  }

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

// 문서 로드 (텍스트 파일 등) - 현재는 PDF/MD 외 다른 문서 타입은 이 함수를 직접 호출하지 않음
async function loadDocumentView(filePath) {
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
  console.log('[FRONTEND] translateSelected 함수 호출됨');
  
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  console.log('[FRONTEND] 선택된 체크박스 수:', checkboxes.length);
  
  if (checkboxes.length === 0) {
    console.log('[FRONTEND] 선택된 파일이 없음');
    alert('번역할 파일을 선택해주세요.');
    return;
  }
  
  // 여러 파일 번역은 첫 번째 파일만 처리 (단순화)
  const firstFile = checkboxes[0].value;
  console.log('[FRONTEND] 첫 번째 선택된 파일:', firstFile);
  
  startTranslation(firstFile);
}

function startTranslation(filePath) {
  console.log('[FRONTEND] === startTranslation 시작 ===');
  console.log('[FRONTEND] 파일 경로:', filePath);
  
  // 기존 번역 상태 체크 중지
  if (translationStatusInterval) {
    console.log('[FRONTEND] 기존 인터벌 정리');
    clearInterval(translationStatusInterval);
    translationStatusInterval = null;
  }
  
  const rightPanel = document.getElementById('right-panel');
  console.log('[FRONTEND] right-panel 요소:', rightPanel);
  
  if (!rightPanel) {
    console.error('[FRONTEND] right-panel 요소를 찾을 수 없습니다!');
    alert('UI 오류: right-panel을 찾을 수 없습니다.');
    return;
  }
  
  const fileName = filePath.split(/[\\/]/).pop();
  console.log('[FRONTEND] 파일명:', fileName);
  
  console.log('[FRONTEND] 번역 UI 생성 중...');
  
  // 번역 진행률 UI 표시
  const progressUI = createTranslationProgressUI(fileName);
  console.log('[FRONTEND] 생성된 UI HTML 길이:', progressUI.length);
  
  rightPanel.innerHTML = progressUI;
  console.log('[FRONTEND] UI HTML 삽입 완료');
  
  // UI가 제대로 생성되었는지 확인
  setTimeout(() => {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    const chunksInfo = document.getElementById('chunks-info');
    
    console.log('[FRONTEND] UI 생성 확인:', {
      progressBar: !!progressBar,
      progressText: !!progressText,
      progressPercent: !!progressPercent,
      chunksInfo: !!chunksInfo
    });
    
    if (!progressBar || !progressText || !progressPercent) {
      console.error('[FRONTEND] 필수 UI 요소가 생성되지 않았습니다!');
      console.log('[FRONTEND] 현재 right-panel 내용:', rightPanel.innerHTML.substring(0, 200) + '...');
    } else {
      console.log('[FRONTEND] UI 요소들이 성공적으로 생성되었습니다');
    }
  }, 100);
  
  // 번역 시작 API 호출
  console.log('[FRONTEND] 번역 시작 API 호출...');
  fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  })
  .then(res => {
    console.log('[FRONTEND] 번역 시작 응답 상태:', res.status);
    return res.json();
  })
  .then(data => {
    console.log('[FRONTEND] 번역 시작 응답 데이터:', data);
    if (data.status === 'started') {
      // 번역 상태 모니터링 시작
      console.log('[FRONTEND] 번역 상태 모니터링 시작');
      startTranslationStatusCheck(filePath);
    } else {
      throw new Error(data.error || '번역 시작 실패');
    }
  })
  .catch(error => {
    console.error('[FRONTEND] 번역 시작 오류:', error);
    rightPanel.innerHTML = `
      <div class="p-4 text-red-500">
        <h3 class="font-semibold mb-2">번역 오류</h3>
        <p>${error.message}</p>
        <button onclick="startTranslation('${filePath}')" class="mt-3 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
          다시 시도
        </button>
      </div>
    `;
  });
  
  console.log('[FRONTEND] === startTranslation 완료 ===');
}

// 번역 진행률 UI 생성
function createTranslationProgressUI(fileName) {
  console.log('[FRONTEND] createTranslationProgressUI 호출:', fileName);
  
  // 더 간단한 HTML로 테스트
  const htmlContent = `
    <div style="padding: 20px; background-color: white; border: 1px solid #ccc;">
      <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div style="width: 20px; height: 20px; border: 2px solid #3b82f6; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>
        <h3 style="margin: 0; font-size: 18px; font-weight: bold;">번역 진행 중</h3>
      </div>
      
      <div style="margin-bottom: 20px;">
        <p style="margin: 0 0 10px 0; font-size: 14px;">파일: <strong>${fileName}</strong></p>
        <div style="background-color: #e5e7eb; border-radius: 10px; height: 12px; margin-bottom: 10px;">
          <div id="progress-bar" style="background-color: #3b82f6; height: 12px; border-radius: 10px; width: 0%; transition: width 0.3s;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #6b7280;">
          <span id="progress-text">준비 중...</span>
          <span id="progress-percent">0%</span>
        </div>
      </div>
      
      <div style="background-color: #f9fafb; border-radius: 8px; padding: 15px;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">진행 상황</h4>
        <div id="chunks-info" style="max-height: 160px; overflow-y: auto;">
          <div style="font-size: 12px; color: #6b7280;">청크 분석 중...</div>
        </div>
      </div>
      
      <div id="partial-preview" style="margin-top: 15px; display: none;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">번역 결과 미리보기</h4>
        <div style="background-color: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 12px; max-height: 120px; overflow-y: auto; font-size: 12px;">
          <div id="partial-content"></div>
        </div>
      </div>
    </div>
    
    <style>
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    </style>
  `;
  
  console.log('[FRONTEND] UI HTML 생성 완료, 길이:', htmlContent.length);
  return htmlContent;
}

// 번역 상태 체크 시작
function startTranslationStatusCheck(filePath) {
  console.log('[FRONTEND] startTranslationStatusCheck 시작:', filePath);
  
  // 기존 인터벌 정리
  if (translationStatusInterval) {
    clearInterval(translationStatusInterval);
  }
  
  // 즉시 한 번 실행
  checkTranslationStatus(filePath);
  
  // 2초마다 상태 확인
  translationStatusInterval = setInterval(() => {
    checkTranslationStatus(filePath);
  }, 2000);
}

// 번역 상태 확인
function checkTranslationStatus(filePath) {
  console.log('[FRONTEND] 번역 상태 확인:', filePath);
  
  fetch(`/api/translation-status?path=${encodeURIComponent(filePath)}&include_partial=true`)
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP 오류 ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      console.log('[FRONTEND] 상태 응답:', data);
      
      // 'done' 또는 'completed' 상태 모두 처리
      if (data.status === 'completed' || data.status === 'done') {
        // 번역 완료
        console.log('[FRONTEND] 번역 완료');
        clearInterval(translationStatusInterval);
        showTranslationResult(filePath);
      } else if (data.status === 'error') {
        // 오류 발생
        console.error('[FRONTEND] 번역 오류:', data.error);
        clearInterval(translationStatusInterval);
        showTranslationError(filePath, data.error);
      } else if (data.status === 'running') {
        // 진행 중인 경우 진행률 업데이트
        updateTranslationProgress(data);
      } else {
        console.log('[FRONTEND] 알 수 없는 상태:', data.status);
      }
    })
    .catch(error => {
      console.error('[FRONTEND] 상태 확인 실패:', error);
      // 상태 확인 실패 시 5초 후 재시도
      setTimeout(() => checkTranslationStatus(filePath), 5000);
    });
}

// 번역 진행률 업데이트
function updateTranslationProgress(data) {
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  const progressPercent = document.getElementById('progress-percent');
  const chunksInfo = document.getElementById('chunks-info');
  
  if (progressBar && progressPercent) {
    const percent = Math.round(data.progress_percent || 0);
    progressBar.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;
  }
  
  if (progressText) {
    progressText.textContent = `처리 중: ${data.chunks_completed || 0}/${data.total_chunks || 0} 청크`;
  }
  
  // 청크 정보 업데이트
  if (chunksInfo && data.chunks_info && Array.isArray(data.chunks_info)) {
    chunksInfo.innerHTML = data.chunks_info.map((chunk, index) => {
      let status = '⏳';
      if (chunk.status === 'completed') status = '✅';
      else if (chunk.status === 'error') status = '❌';
      
      return `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 12px;">
          <span>${status} 청크 ${index + 1}: ${chunk.header || '제목 없음'}</span>
          <span>${chunk.size || 0}자</span>
        </div>
      `;
    }).join('');
  }
}

// 번역 오류 표시
function showTranslationError(filePath, error) {
  const rightPanel = document.getElementById('right-panel');
  if (!rightPanel) return;
  
  rightPanel.innerHTML = `
    <div class="p-4">
      <div class="bg-red-50 border-l-4 border-red-500 p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">번역 중 오류가 발생했습니다</h3>
            <div class="mt-2 text-sm text-red-700">
              <p>${error || '알 수 없는 오류가 발생했습니다.'}</p>
            </div>
            <div class="mt-4">
              <button onclick="startTranslation('${filePath}')" class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                다시 시도
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// 번역 결과 또는 플레이스홀더 표시
function displayTranslatedContentOrPlaceholder(filePath) {
  const rightPanel = document.getElementById('right-panel');
  if (!rightPanel) {
    console.error('[FRONTEND] right-panel 요소를 찾을 수 없습니다!');
    return;
  }

  rightPanel.innerHTML = '<div class="p-4 text-gray-500">번역된 내용을 불러오는 중...</div>';

  fetch(`/api/translation-result?path=${encodeURIComponent(filePath)}`)
    .then(res => {
      if (res.status === 404) { // Translated file not found
        return { notFound: true };
      }
      if (!res.ok) {
        return res.json().then(errData => {
          throw new Error(errData.error || `HTTP 오류 ${res.status}`);
        }).catch(() => { 
          throw new Error(`HTTP 오류 ${res.status}`);
        });
      }
      return res.json(); // Translated content exists
    })
    .then(data => {
      if (data.notFound) {
        rightPanel.innerHTML = `
          <div class="p-4">
            <h3 class="text-lg font-semibold mb-2">번역</h3>
            <div class="bg-white p-4 rounded border text-gray-600">
              번역된 내용이 여기에 표시됩니다.
            </div>
          </div>
        `;
      } else if (data.content) {
        const downloadPath = data.translated_path || filePath; 
        const fileName = downloadPath.split(/[\\/]/).pop();
        rightPanel.innerHTML = `
          <div class="p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">번역 결과</h3>
              <a href="/api/download?path=${encodeURIComponent(downloadPath)}"
                 class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                 download="${fileName}">
                다운로드
              </a>
            </div>
            <div class="bg-white p-4 rounded border max-h-[500px] overflow-y-auto">
              <pre class="whitespace-pre-wrap text-sm">${data.content}</pre>
            </div>
          </div>
        `;
      } else {
        throw new Error('번역된 내용이 없거나 형식이 잘못되었습니다.');
      }
    })
    .catch(error => {
      console.error('[FRONTEND] 번역 결과 또는 플레이스홀더 표시 오류:', error);
      rightPanel.innerHTML = `
        <div class="p-4 text-red-500">
          <h3 class="font-semibold mb-2">오류</h3>
          <p>번역된 내용을 가져오는 중 오류가 발생했습니다: ${error.message}</p>
          <button onclick="displayTranslatedContentOrPlaceholder('${filePath}')" class="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            다시 시도
          </button>
        </div>
      `;
    });
}

// 번역 결과 표시
function showTranslationResult(filePath) {
  console.log('[FRONTEND] 번역 결과 표시 요청:', filePath);
  
  const rightPanel = document.getElementById('right-panel');
    // 초기 로딩 UI 설정
    rightPanel.innerHTML = `
      <div class="p-4 flex flex-col h-full">
        <div class="flex items-center justify-between mb-4 flex-shrink-0">
          <h3 class="text-lg font-semibold">번역 결과</h3>
          <span class="text-sm text-neutral-500">로딩 중...</span>
        </div>
        <div class="prose-placeholder flex-grow flex items-center justify-center text-neutral-400">
          <p>번역 내용 로딩 중...</p>
        </div>
        <div class="mt-4 text-sm text-gray-500 flex-shrink-0">
          <p>잠시만 기다려 주세요.</p>
        </div>
      </div>
    `;

    fetchAndParseMarkdown(filePath, '/api/translation-result')
      .then(translatedHtmlContent => {
        rightPanel.innerHTML = `
          <div class="p-4 flex flex-col h-full">
            <div class="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 class="text-lg font-semibold">번역 결과</h3>
              <a href="/api/download?path=${encodeURIComponent(filePath)}" 
                 class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">
                다운로드
              </a>
            </div>
            <div class="prose max-w-none h-full overflow-y-auto bg-white p-4 rounded border flex-grow">
              ${translatedHtmlContent}
            </div>
            <div class="mt-4 text-sm text-gray-500 flex-shrink-0">
              <p>번역이 완료되었습니다. 위의 다운로드 버튼을 클릭하여 파일을 저장하세요.</p>
            </div>
          </div>
        `;
      })
      .catch(error => {
        console.error('[FRONTEND] 번역 결과 로드 또는 처리 중 오류 (refactored):', error);
        rightPanel.innerHTML = `
          <div class="p-4 text-red-500">
            <h3 class="font-semibold mb-2">번역 결과 로드 실패</h3>
            <p>${error.message}</p>
            <button onclick="showTranslationResult('${filePath}')" class="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              다시 시도
            </button>
          </div>
        `;
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

  // 좌측 패널 보기 모드 전환 버튼 이벤트 리스너
  const viewPdfBtn = document.getElementById('view-pdf-btn');
  if (viewPdfBtn) {
    viewPdfBtn.addEventListener('click', () => {
      if (currentFile) toggleLeftPanelView('pdf');
    });
  }

  const viewMdBtn = document.getElementById('view-md-btn');
  if (viewMdBtn) {
    viewMdBtn.addEventListener('click', () => {
      if (currentFile && currentOriginalMarkdownPath) toggleLeftPanelView('md');
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

// 좌측 패널 보기 모드 전환 함수
async function toggleLeftPanelView(mode) {
  if (!currentFile) return;
  leftPanelViewMode = mode;

  const viewerContainer = document.getElementById('viewer-container');
  const pageControls = document.getElementById('page-controls');
  const viewPdfBtn = document.getElementById('view-pdf-btn');
  const viewMdBtn = document.getElementById('view-md-btn');

  if (mode === 'pdf') {
    console.log('[VIEWER] PDF 보기 모드로 전환');
    pageControls.classList.remove('hidden');
    if (viewPdfBtn && viewMdBtn) {
      viewPdfBtn.classList.add('bg-blue-500', 'text-white');
      viewPdfBtn.classList.remove('bg-neutral-200', 'text-neutral-700');
      viewMdBtn.classList.remove('bg-blue-500', 'text-white');
      viewMdBtn.classList.add('bg-neutral-200', 'text-neutral-700');
    }
    // loadPDFView를 직접 호출하기보다, 현재 페이지로 다시 로드하는 것이 안전할 수 있음
    // 여기서는 이미 loadPDFView가 currentFile, currentPage를 사용하므로, 해당 상태로 다시 그림
    loadPDFView(currentFile, currentPage);
  } else if (mode === 'md') {
    console.log('[VIEWER] 원본 MD 보기 모드로 전환');
    if (!currentOriginalMarkdownPath) {
      viewerContainer.innerHTML = '<div class="flex items-center justify-center h-full text-red-500"><p>원본 마크다운 파일 경로가 없습니다.</p></div>';
      pageControls.classList.add('hidden');
      return;
    }
    pageControls.classList.add('hidden');
    if (viewPdfBtn && viewMdBtn) {
      viewMdBtn.classList.add('bg-blue-500', 'text-white');
      viewMdBtn.classList.remove('bg-neutral-200', 'text-neutral-700');
      viewPdfBtn.classList.remove('bg-blue-500', 'text-white');
      viewPdfBtn.classList.add('bg-neutral-200', 'text-neutral-700');
    }
    viewerContainer.innerHTML = '<div class="flex items-center justify-center h-full text-neutral-400"><p>마크다운 로딩 중...</p></div>';

    fetchAndParseMarkdown(currentOriginalMarkdownPath, '/api/read-file')
      .then(htmlContent => {
        viewerContainer.innerHTML = `<div class="prose max-w-none p-4 overflow-y-auto h-full">${htmlContent}</div>`;
      })
      .catch(error => {
        viewerContainer.innerHTML = `<div class="flex items-center justify-center h-full text-red-500"><p>마크다운 표시 오류: ${error.message}</p></div>`;
      });
  }
}