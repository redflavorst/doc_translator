function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('hidden');
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
