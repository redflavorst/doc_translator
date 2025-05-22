// 전역 변수
let currentFile = null;
let currentPage = 1;
let totalPages = 1;

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
      span.onclick = () => loadPDFView(file.path);
      
      li.appendChild(checkbox);
      li.appendChild(span);
      fileList.appendChild(li);
    });
  } catch (error) {
    console.error('폴더를 불러오는 중 오류 발생:', error);
  }
}

// 파일 선택 함수
async function selectFile(filePath) {
  try {
    const response = await fetch('/api/select-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    const file = await response.json();
    addFileItem(file);
  } catch (error) {
    console.error('파일을 불러오는 중 오류 발생:', error);
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
  span.onclick = () => loadPDFView(file.path);
  
  li.appendChild(checkbox);
  li.appendChild(span);
  fileList.appendChild(li);
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
          selectFile(filePath);
        }
      })
      .catch(error => {
        console.error('파일 선택 중 오류 발생:', error);
      });
  } else {
    console.error('pywebview API를 사용할 수 없습니다.');
  }
}

// 문서 로드 함수 (PDF, 텍스트, HTML 등 지원)
function loadPDFView(filePath, page = 1) {
  const viewer = document.getElementById('viewer-container');
  if (!viewer) return;

  // 파일 확장자에 따라 다른 처리
  const ext = filePath.split('.').pop().toLowerCase();
  
  // PDF 파일인 경우
  if (ext === 'pdf') {
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
  // 텍스트 파일인 경우
  else if (['txt', 'md', 'json', 'xml', 'csv'].includes(ext)) {
    fetch(`/api/read-file?path=${encodeURIComponent(filePath)}`)
      .then(res => res.json())
      .then(data => {
        if (data.content) {
          viewer.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace;">${escapeHtml(data.content)}</pre>`;
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

// 번역 시작 함수
function startTranslation(filePath) {
  fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  })
  .catch(error => {
    console.error('번역 중 오류 발생:', error);
  });
}

// 선택된 파일 번역
function translateSelected() {
  const checked = document.querySelectorAll('.file-checkbox:checked');
  if (checked.length === 0) {
    alert('번역할 파일을 선택해주세요.');
    return;
  }
  
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
      if (currentPage > 1) {
        loadPDFView(currentFile, currentPage - 1);
      }
    });
  }
  
  // 다음 페이지 버튼 이벤트 리스너
  const nextPageBtn = document.getElementById('next-page');
  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        loadPDFView(currentFile, currentPage + 1);
      }
    });
  }
  
  console.log('애플리케이션 초기화 완료');
});
