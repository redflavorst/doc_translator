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

  async function selectFolder(folderPath) {
    const response = await fetch('/api/select-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: folderPath })
    });
    const data = await response.json();
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    data.files.forEach(file => addFileItem(file));
  }

  async function selectFile(filePath) {
    const response = await fetch('/api/select-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    const file = await response.json();
    addFileItem(file);
  }

  function addFileItem(file) {
    const fileList = document.getElementById('file-list');
    const li = document.createElement('li');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    const span = document.createElement('span');
    span.className = 'file-name';
    span.textContent = file.name + ' (' + file.lang + ')';
    span.onclick = () => loadPDFView(file.path, 1);
    li.appendChild(checkbox);
    li.appendChild(span);
    fileList.appendChild(li);
  }

  function triggerFolderSelect() {
    window.pywebview.api.open_folder_dialog().then(folderPath => {
      if (folderPath) {
        selectFolder(folderPath);
      }
    });
  }

  function triggerFileSelect() {
    window.pywebview.api.open_file_dialog().then(filePath => {
      if (filePath) {
        selectFile(filePath);
      }
    });
  }

  let currentFile = null;
  let currentPage = 1;
  let totalPages = 1;

  function loadPDFView(filePath, page) {
    fetch('/api/view-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, page: page })
    })
    .then(res => res.json())
    .then(data => {
      const viewer = document.getElementById('viewer-container');
      viewer.innerHTML = '<img src="data:image/png;base64,' + data.image + '">';
      currentFile = filePath;
      currentPage = page;
      totalPages = data.total_pages;
      document.getElementById('page-info').textContent = page + ' / ' + totalPages;
      const controls = document.getElementById('page-controls');
      controls.classList.toggle('hidden', totalPages <= 1);
    });
  }

  document.getElementById('prev-page').onclick = () => {
    if (currentPage > 1) {
      loadPDFView(currentFile, currentPage - 1);
    }
  };

  document.getElementById('next-page').onclick = () => {
    if (currentPage < totalPages) {
      loadPDFView(currentFile, currentPage + 1);
    }
  };

function startTranslation(filePath) {
  fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  });
}
