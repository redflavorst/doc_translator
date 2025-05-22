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

function addFileToList(filePath) {
  const fileList = document.getElementById('file-list');
  const li = document.createElement('li');
  const name = filePath.split(/[/\\]/).pop();
  li.textContent = name;
  if (name.toLowerCase().endsWith('.pdf')) {
    li.onclick = () => loadPDFView(filePath);
  }
  fileList.appendChild(li);
}

function triggerFileSelect() {
  window.pywebview.api.open_file_dialog().then(filePath => {
    if (filePath) {
      addFileToList(filePath);
    }
  });
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
  data.files.forEach(file => {
    const li = document.createElement('li');
    li.textContent = file.name + ' (' + file.lang + ')';
    li.onclick = () => loadPDFView(file.path);
    fileList.appendChild(li);
  });
}

function triggerFolderSelect() {
  window.pywebview.api.open_folder_dialog().then(folderPath => {
    if (folderPath) {
      selectFolder(folderPath);
    }
  });
}

function loadPDFView(filePath) {
  fetch('/api/view-pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  })
  .then(res => res.json())
  .then(data => {
    const left = document.getElementById('left-panel');
    left.innerHTML = '<img src="data:image/png;base64,' + data.image + '">';
  });
}

function startTranslation(filePath) {
  fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: filePath })
  });
}
