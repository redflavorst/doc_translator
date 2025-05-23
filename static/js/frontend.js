// 전역 변수
let currentFile = null;
let currentPage = 1;
let totalPages = 1;
let currentMarkdownPath = null;
let currentViewMode = 'pdf'; // 'pdf' 또는 'md'

// 사이드바 토글 함수
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  sidebar.classList.toggle('hidden');
  
  // 토글 버튼 위치 조정 (사이드바가 열려있으면 오른쪽으로, 닫혀있으면 왼쪽으로)
  if (sidebar.classList.contains('hidden')) {
    toggleBtn.style.left = '0';
  } else {
    toggleBtn.style.left = '250px'; // 사이드바 너비와 동일하게 조정
  }
}

// 뷰 모드 전환 함수
function switchViewMode(mode) {
  if (!currentFile) return;
  
  currentViewMode = mode;
  
  // 탭 활성화 상태 업데이트
  document.querySelectorAll('.view-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.getElementById(`${mode}-tab`).classList.add('active');
  
  // 해당 모드로 뷰어 업데이트
  if (mode === 'pdf') {
    loadPDFView(currentFile, currentPage);
  } else if (mode === 'md' && currentMarkdownPath) {
    loadMarkdownView(currentMarkdownPath);
  }
  
  // 페이지 컨트롤은 PDF 모드에서만 표시
  const pageControls = document.getElementById('page-controls');
  if (pageControls) {
    pageControls.classList.toggle('hidden', mode !== 'pdf' || totalPages <= 1);
  }
}

// 마크다운 뷰어 함수
function loadMarkdownView(markdownPath) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  fetch(`/api/read-file?path=${encodeURIComponent(markdownPath)}`)
    .then(res => res.json())
    .then(data => {
      if (data.content) {
        // 마크다운을 HTML로 렌더링 (간단한 변환)
        const htmlContent = convertMarkdownToHtml(data.content);
        viewer.innerHTML = `
          <div class="markdown-content" style="padding: 20px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;">
            ${htmlContent}
          </div>`;
      } else {
        viewer.innerHTML = '<p>마크다운 파일을 불러올 수 없습니다.</p>';
      }
    })
    .catch(error => {
      console.error('마크다운 파일을 읽는 중 오류 발생:', error);
      viewer.innerHTML = `<p>마크다운 파일을 로드하는 중 오류가 발생했습니다: ${error.message}</p>`;
    });
}

// 간단한 마크다운 to HTML 변환기
function convertMarkdownToHtml(markdown) {
  return markdown
    // 제목 변환
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    // 볼드 변환
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // 이탤릭 변환
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // 코드 블록 변환
    .replace(/```([\s\S]*?)```/g, '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;"><code>$1</code></pre>')
    // 인라인 코드 변환
    .replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">$1</code>')
    // 링크 변환
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color: #0066cc;">$1</a>')
    // 줄바꿈 변환
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    // 문단 래핑
    .replace(/^(.+)/, '<p>$1')
    .replace(/(.+)$/, '$1</p>');
}

// 탭 컨트롤 생성 함수
function createViewTabs() {
  const leftPanel = document.getElementById('left-panel');
  if (!leftPanel) return;

  // 기존 탭이 있으면 제거
  const existingTabs = leftPanel.querySelector('.view-tabs');
  if (existingTabs) {
    existingTabs.remove();
  }

  // 탭 컨테이너 생성
  const tabContainer = document.createElement('div');
  tabContainer.className = 'view-tabs';
  tabContainer.style.cssText = `
    display: flex;
    border-bottom: 1px solid #e5e5e5;
    background: #f8f9fa;
    margin-bottom: 10px;
  `;

  // PDF 탭
  const pdfTab = document.createElement('button');
  pdfTab.id = 'pdf-tab';
  pdfTab.className = 'view-tab active';
  pdfTab.textContent = 'PDF';
  pdfTab.onclick = () => switchViewMode('pdf');
  pdfTab.style.cssText = `
    padding: 8px 16px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  `;

  // 마크다운 탭
  const mdTab = document.createElement('button');
  mdTab.id = 'md-tab';
  mdTab.className = 'view-tab';
  mdTab.textContent = 'Markdown';
  mdTab.onclick = () => switchViewMode('md');
  mdTab.style.cssText = `
    padding: 8px 16px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  `;

  tabContainer.appendChild(pdfTab);
  tabContainer.appendChild(mdTab);

  // 뷰어 컨테이너 앞에 삽입
  const viewerContainer = leftPanel.querySelector('#viewer-container');
  leftPanel.insertBefore(tabContainer, viewerContainer);

  // CSS 스타일 추가
  if (!document.querySelector('#tab-styles')) {
    const style = document.createElement('style');
    style.id = 'tab-styles';
    style.textContent = `
      .view-tab:hover {
        background: #e9ecef !important;
      }
      .view-tab.active {
        background: white !important;
        border-bottom-color: #007bff !important;
        font-weight: 500;
      }
    `;
    document.head.appendChild(style);
  }
}

// 탭 제거 함수
function removeViewTabs() {
  const tabs = document.querySelector('.view-tabs');
  if (tabs) {
    tabs.remove();
  }
}

// 폴더 선택 함수
async function selectFolder(folderPath) {
  try {
    const response = await fetch('/api/select-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: folderPath })
    });
    const data = await response.json();
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    
    data.files.forEach(file => {
      const li = document.createElement('li');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = file.path;
      checkbox.classList.add('file-checkbox');
      
      const span = document.createElement('span');
      span.textContent = file.name + (file.lang ? ` (${file.lang})` : '');
      span.onclick = () => loadFileWithTabs(file.path);
      
      li.appendChild(checkbox);
      li.appendChild(span);
      fileList.appendChild(li);
    });
  } catch (error) {
    console.error('폴더를 불러오는 중 오류 발생:', error);
  }
}

// 파일 선택 함수 - 외국어 문서 여부만 파악하고 변환은 하지 않음
function selectFile(filePath) {
  // 파일 확장자 확인
  const ext = filePath.split('.').pop().toLowerCase();
  
  if (ext === 'pdf') {
    // PDF 파일인 경우 언어 감지만 수행
    fetch('/api/check-language', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    })
    .then(res => res.json())
    .then(data => {
      // 파일 정보를 사이드바 목록에 추가
      addFileItem({
        name: data.name,
        path: data.path,
        lang: data.lang
      });
      
      // 파일 로드 및 탭 생성 (변환 없이)
      loadPDFView(filePath, 1);
    })
    .catch(error => {
      console.error('파일 언어 감지 중 오류 발생:', error);
    });
  } else {
    // PDF가 아닌 파일은 그냥 로드
    addFileItem({
      name: filePath.split(/[\\/]/).pop(),
      path: filePath,
      lang: 'unknown'
    });
    
    loadDocumentView(filePath);
  }
}

// 파일 아이템 추가 함수
function addFileItem(file) {
  const fileList = document.getElementById('file-list');
  const li = document.createElement('li');
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.value = file.path;
  checkbox.classList.add('file-checkbox');
  
  const span = document.createElement('span');
  span.textContent = file.name + (file.lang ? ` (${file.lang})` : '');
  span.onclick = () => loadFileWithTabs(file.path);
  
  li.appendChild(checkbox);
  li.appendChild(span);
  fileList.appendChild(li);
}

// 탭과 함께 파일 로드하는 함수
async function loadFileWithTabs(filePath) {
  const ext = filePath.split('.').pop().toLowerCase();
  
  if (ext === 'pdf') {
    // PDF 파일인 경우 마크다운 변환 후 탭 생성
    try {
      // 마크다운 변환을 위해 select-file API 호출
      const response = await fetch('/api/select-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: filePath })
      });
      
      if (response.ok) {
        // 마크다운 경로 추정 (변환된 파일 경로)
        const fileName = filePath.split(/[\\/]/).pop().replace('.pdf', '.md');
        currentMarkdownPath = filePath.replace(/[^/\\]+\.pdf$/, fileName);
        
        // 탭 생성
        createViewTabs();
        
        // 기본으로 PDF 뷰 로드
        currentFile = filePath;
        currentViewMode = 'pdf';
        loadPDFView(filePath, 1);
      } else {
        // 변환 실패 시 기존 방식으로 PDF만 로드
        removeViewTabs();
        loadPDFView(filePath, 1);
      }
    } catch (error) {
      console.error('파일 변환 중 오류 발생:', error);
      removeViewTabs();
      loadPDFView(filePath, 1);
    }
  } else {
    // PDF가 아닌 파일은 탭 없이 기존 방식으로 로드
    removeViewTabs();
    loadDocumentView(filePath);
  }
}

// 폴더 선택 트리거
function triggerFolderSelect() {
  console.log('폴더 선택 대화상자 열기 시도');
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_folder_dialog()
      .then(folderPath => {
        console.log('선택된 폴더:', folderPath);
        if (folderPath) {
          selectFolder(folderPath);
        }
      })
      .catch(error => {
        console.error('폴더 선택 중 오류 발생:', error);
      });
  } else {
    console.error('pywebview API를 사용할 수 없습니다.');
  }
}

// 파일 선택 트리거
function triggerFileSelect() {
  console.log('파일 선택 대화상자 열기 시도');
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_file_dialog()
      .then(filePath => {
        console.log('선택된 파일:', filePath);
        if (filePath) {
          // 파일 정보를 서버에 전송하고 사이드바에 추가
          selectFile(filePath);
          // loadFileWithTabs는 selectFile 내부에서 호출됨
        }
      })
      .catch(error => {
        console.error('파일 선택 중 오류 발생:', error);
      });
  } else {
    console.error('pywebview API를 사용할 수 없습니다.');  
  }
}

// 문서 로드 함수 (PDF, 텍스트, HTML 등 지원) - 기존 함수명 변경
function loadDocumentView(filePath, page = 1) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  // 파일 확장자에 따라 다른 처리
  const ext = filePath.split('.').pop().toLowerCase();
  
  // 텍스트 파일인 경우
  if (['txt', 'md', 'json', 'xml', 'csv'].includes(ext)) {
    fetch(`/api/read-file?path=${encodeURIComponent(filePath)}`)
      .then(res => res.json())
      .then(data => {
        if (data.content) {
          if (ext === 'md') {
            const htmlContent = convertMarkdownToHtml(data.content);
            viewer.innerHTML = `
              <div class="markdown-content" style="padding: 20px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;">
                ${htmlContent}
              </div>`;
          } else {
            viewer.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace;">${escapeHtml(data.content)}</pre>`;
          }
        } else {
          viewer.innerHTML = '<p>빈 파일입니다.</p>';
        }
      })
      .catch(error => {
        console.error('텍스트 파일을 읽는 중 오류 발생:', error);
        viewer.innerHTML = `<p>파일을 읽는 중 오류가 발생했습니다: ${error.message}</p>`;
      });
  }
  // HTML 파일인 경우
  else if (ext === 'html' || ext === 'htm') {
    fetch(`/api/read-file?path=${encodeURIComponent(filePath)}`)
      .then(res => res.json())
      .then(data => {
        if (data.content) {
          // 보안을 위해 iframe에 로드
          viewer.innerHTML = `
            <iframe 
              srcdoc="${data.content.replace(/"/g, '&quot;')}" 
              style="width: 100%; height: 100%; border: none;">
            </iframe>`;
        } else {
          viewer.innerHTML = '<p>빈 HTML 파일입니다.</p>';
        }
      })
      .catch(error => {
        console.error('HTML 파일을 읽는 중 오류 발생:', error);
        viewer.innerHTML = `<p>HTML 파일을 로드하는 중 오류가 발생했습니다: ${error.message}</p>`;
      });
  }
  // 기타 파일 형식
  else {
    viewer.innerHTML = `
      <div style="text-align: center; padding: 20px;">
        <p>이 파일 형식은 미리보기를 지원하지 않습니다.</p>
        <p>파일 경로: ${filePath}</p>
        <button onclick="downloadFile('${filePath}')">파일 다운로드</button>
      </div>`;
  }
  
  // 페이지 제목 업데이트
  document.title = `문서 뷰어 - ${filePath.split(/[\\/]/).pop()}`;
}

// PDF 문서 로드 함수 (기존 loadPDFView 함수)
function loadPDFView(filePath, page = 1) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  // 화면 크기에 맞게 DPI 조정 (기본 200, 고해상도 디스플레이를 위해 300으로 설정)
  const dpi = window.devicePixelRatio > 1 ? 300 : 200;
  
  fetch('/api/view-pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      path: filePath, 
      page: page,
      dpi: dpi  // DPI 파라미터 추가
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.image) {
      viewer.innerHTML = `<img src="data:image/png;base64,${data.image}" style="max-width: 100%;">`;
      currentFile = filePath;
      currentPage = page;
      totalPages = data.total_pages || 1;
      
      // 페이지 컨트롤 업데이트
      const pageInfo = document.getElementById('page-info');
      if (pageInfo) {
        pageInfo.textContent = `${page} / ${totalPages}`;
      }
      
      // 페이지 컨트롤 표시/숨기기
      const controls = document.getElementById('page-controls');
      if (controls) {
        controls.classList.toggle('hidden', totalPages <= 1);
      }
    } else {
      viewer.innerHTML = '<p>문서를 불러올 수 없습니다.</p>';
    }
  })
  .catch(error => {
    console.error('문서를 불러오는 중 오류 발생:', error);
    viewer.innerHTML = `<p>문서를 불러오는 중 오류가 발생했습니다: ${error.message}</p>`;
  });
}

// HTML 이스케이프 유틸리티 함수
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 파일 다운로드 함수
function downloadFile(filePath) {
  const a = document.createElement('a');
  a.href = `/api/download?path=${encodeURIComponent(filePath)}`;
  a.download = filePath.split(/[\\/]/).pop();
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// 번역 시작 함수 (번역 요청 및 상태 확인)
function startTranslation(filePath) {
  // 우측 패널에 번역 중 표시
  const rightPanel = document.getElementById('right-panel');
  rightPanel.innerHTML = `
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <h3>번역 중...</h3>
      <p>문서: ${filePath.split(/[\\/]/).pop()}</p>
      <div id="translation-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: 0%"></div>
        </div>
        <p id="progress-text">0%</p>
      </div>
      <div id="chunk-status"></div>
      <div id="partial-result" style="margin-top: 20px; text-align: left; max-height: 300px; overflow-y: auto;"></div>
    </div>
  `;
  
  // 번역 요청 보내기
  fetch('/api/translate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ path: filePath }),
  })
  .then(response => response.json())
  .then(data => {
    console.log('Translation started:', data);
    
    // 2초마다 번역 상태 확인
    checkTranslationStatus(filePath);
  })
  .catch(error => {
    console.error('Error starting translation:', error);
    rightPanel.innerHTML = `<div class="error-message">번역 시작 중 오류가 발생했습니다: ${error.message}</div>`;
  });
}

function checkTranslationStatus(filePath) {
  // 부분 결과를 포함하도록 요청
  const includePartial = true;
  const url = `/api/translation-status?path=${encodeURIComponent(filePath)}&include_partial=${includePartial}`;
  
  fetch(url)
  .then(response => response.json())
  .then(data => {
    console.log('Translation status:', data);
    
    if (data.status === 'completed') {
      // 번역이 완료되면 결과 표시
      showTranslationResult(filePath);
    } else if (data.status === 'error') {
      // 오류 발생 시 오류 메시지 표시
      const rightPanel = document.getElementById('right-panel');
      rightPanel.innerHTML = `<div class="error-message">번역 중 오류가 발생했습니다: ${data.error || '알 수 없는 오류'}</div>`;
    } else if (data.status === 'running') {
      // 진행 상황 표시 업데이트
      updateProgressUI(data);
      
      // 2초 후 다시 확인
      setTimeout(() => checkTranslationStatus(filePath), 2000);
    } else {
      // 기타 상태인 경우 2초 후 다시 확인
      setTimeout(() => checkTranslationStatus(filePath), 2000);
    }
  })
  .catch(error => {
    console.error('번역 상태 확인 중 오류:', error);
    // 오류 발생 시 5초 후 다시 시도
    setTimeout(() => checkTranslationStatus(filePath), 5000);
  });
}

// 번역 진행 상황 UI 업데이트 함수
function updateProgressUI(data) {
  // 진행률 계산
  const progressPercent = data.progress_percent || 0;
  const completedChunks = data.chunks_completed || 0;
  const totalChunks = data.total_chunks || 1;
  
  const rightPanel = document.getElementById('right-panel');
  if (!rightPanel) return;
  
  // 처음 업데이트하는 경우 UI 요소 생성
  if (!document.getElementById('progress-bar')) {
    const fileName = currentFile.split(/[\/]/).pop();
    rightPanel.innerHTML = `
      <div class="p-4">
        <h3 class="text-lg font-semibold mb-4">번역 진행 중...</h3>
        <p class="mb-2">${fileName} 파일을 번역하고 있습니다.</p>
        
        <div class="mt-4">
          <div id="progress-container" class="w-full bg-gray-200 rounded-full h-4 mb-2">
            <div id="progress-bar" class="bg-blue-500 h-4 rounded-full" style="width: ${progressPercent}%"></div>
          </div>
          <p id="progress-text" class="text-sm text-gray-600">${progressPercent.toFixed(1)}% (${completedChunks}/${totalChunks} 청크)</p>
        </div>
        
        <div id="chunk-status" class="mt-4">
          <h4 class="font-medium mb-2">청크 상태</h4>
          <div class="flex flex-wrap gap-1" id="chunk-indicators"></div>
        </div>
        
        <div id="partial-result" class="mt-4">
          <h4 class="font-medium mb-2">번역 진행 결과</h4>
          <div class="bg-white p-3 rounded border border-gray-200 max-h-[300px] overflow-y-auto">
            <pre class="whitespace-pre-wrap text-sm" id="partial-content"></pre>
          </div>
        </div>
      </div>
    `;
  }
  
  // 프로그레스 바 업데이트
  const progressBar = document.getElementById('progress-bar');
  if (progressBar) {
    progressBar.style.width = `${progressPercent}%`;
  }
  
  // 텍스트 업데이트
  const progressText = document.getElementById('progress-text');
  if (progressText) {
    progressText.textContent = `${progressPercent.toFixed(1)}% (${completedChunks}/${totalChunks} 청크)`;
  }
  
  // 청크 상태 표시기 업데이트
  const chunkIndicators = document.getElementById('chunk-indicators');
  if (chunkIndicators && data.chunks_info) {
    chunkIndicators.innerHTML = '';
    
    data.chunks_info.forEach((chunk, index) => {
      const indicator = document.createElement('div');
      indicator.className = 'w-6 h-6 flex items-center justify-center text-xs rounded';
      indicator.textContent = index + 1;
      
      // 상태에 따른 스타일 적용
      if (chunk.status === 'completed') {
        indicator.classList.add('bg-green-500', 'text-white');
      } else if (chunk.status === 'processing') {
        indicator.classList.add('bg-blue-500', 'text-white', 'animate-pulse');
      } else {
        indicator.classList.add('bg-gray-200', 'text-gray-700');
      }
      
      // 툴팁 추가
      indicator.title = `청크 ${index + 1}: ${chunk.status}`;
      
      chunkIndicators.appendChild(indicator);
    });
  }
  
  // 부분 결과 표시
  if (data.partial_results) {
    const partialContent = document.getElementById('partial-content');
    if (partialContent) {
      partialContent.textContent = data.partial_results;
      // 자동 스크롤
      const container = document.getElementById('partial-result');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }
}

// 번역 결과 불러오기
function loadTranslationResult(filePath) {
  fetch(`/api/translation-result?path=${encodeURIComponent(filePath)}`)
    .then(res => res.json())
    .then(data => {
      if (data.content) {
        const rightPanel = document.getElementById('right-panel');
        if (rightPanel) {
          rightPanel.innerHTML = `
            <div class="p-4">
              <h3 class="text-lg font-semibold mb-4">번역 결과</h3>
              <div class="bg-white p-4 rounded border border-neutral-200 max-h-[70vh] overflow-y-auto">
                <pre class="whitespace-pre-wrap font-sans text-sm">${data.content}</pre>
              </div>
            </div>
          `;
        }
      } else if (data.error) {
        const rightPanel = document.getElementById('right-panel');
        if (rightPanel) {
          rightPanel.innerHTML = `
            <div class="p-4">
              <h3 class="text-lg font-semibold mb-4 text-red-500">번역 결과 로드 오류</h3>
              <p class="text-neutral-700">${data.error}</p>
            </div>
          `;
        }
      }
    })
    .catch(error => {
      console.error('번역 결과 로드 중 오류:', error);
      const rightPanel = document.getElementById('right-panel');
      if (rightPanel) {
        rightPanel.innerHTML = `
          <div class="p-4">
            <h3 class="text-lg font-semibold mb-4 text-red-500">번역 결과 로드 오류</h3>
            <p class="text-neutral-700">번역 결과를 불러오는 중 오류가 발생했습니다.</p>
            <p class="mt-2 text-neutral-500">${error.message || '알 수 없는 오류'}</p>
          </div>
        `;
      }
    });
}

// 선택된 파일 번역
function translateSelected() {
  const checked = document.querySelectorAll('.file-checkbox:checked');
  if (checked.length === 0) {
    alert('번역할 파일을 선택해주세요.');
    return;
  }
  
  // 사용자에게 번역 시작 알림
  alert(`${checked.length}개의 파일 번역을 시작합니다. 번역은 마크다운 변환 후 진행됩니다.`);
  
  checked.forEach(cb => {
    startTranslation(cb.value);
  });
}

// 페이지 로드 시 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', () => {
  // 번역 버튼 이벤트 리스너
  const translateBtn = document.getElementById('translate-btn');
  if (translateBtn) {
    translateBtn.addEventListener('click', translateSelected);
  }
  
  // 이전 페이지 버튼 이벤트 리스너
  const prevPageBtn = document.getElementById('prev-page');
  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (currentPage > 1 && currentViewMode === 'pdf') {
        loadPDFView(currentFile, currentPage - 1);
      }
    });
  }
  
  // 다음 페이지 버튼 이벤트 리스너
  const nextPageBtn = document.getElementById('next-page');
  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      if (currentPage < totalPages && currentViewMode === 'pdf') {
        loadPDFView(currentFile, currentPage + 1);
      }
    });
  }
  
  console.log('애플리케이션 초기화 완료');
});