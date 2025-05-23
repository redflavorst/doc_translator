from threading import Lock
from typing import Dict, Any, List, Optional


class ProgressManager:
    def __init__(self):
        self._progress = {}
        self._lock = Lock()

    def start(self, path: str):
        with self._lock:
            self._progress[path] = {
                'status': 'running',
                'total_chunks': 0,
                'current_chunk': 0,
                'chunks_completed': 0,
                'chunks_info': [],
                'partial_results': []
            }

    def set_total_chunks(self, path: str, total: int, chunks_info: List[Dict[str, Any]]):
        """
        총 청크 수와 각 청크의 정보를 설정합니다.
        """
        with self._lock:
            if path in self._progress:
                self._progress[path]['total_chunks'] = total
                self._progress[path]['chunks_info'] = chunks_info
                # 부분 결과를 저장할 공간 초기화
                self._progress[path]['partial_results'] = [''] * total

    def update_chunk_progress(self, path: str, chunk_index: int, status: str = 'processing'):
        """
        현재 처리 중인 청크 정보를 업데이트합니다.
        """
        with self._lock:
            if path in self._progress:
                self._progress[path]['current_chunk'] = chunk_index
                self._progress[path]['chunks_info'][chunk_index]['status'] = status

    def add_chunk_result(self, path: str, chunk_index: int, result: str):
        """
        청크 번역 결과를 추가합니다.
        """
        with self._lock:
            if path in self._progress:
                self._progress[path]['chunks_completed'] += 1
                self._progress[path]['chunks_info'][chunk_index]['status'] = 'completed'
                self._progress[path]['partial_results'][chunk_index] = result

    def finish(self, path: str):
        with self._lock:
            if path in self._progress:
                self._progress[path]['status'] = 'done'

    def error(self, path: str, error_msg: str):
        with self._lock:
            if path in self._progress:
                self._progress[path]['status'] = 'error'
                self._progress[path]['error'] = error_msg
            else:
                self._progress[path] = {'status': 'error', 'error': error_msg}

    def get(self, path: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            progress_data = self._progress.get(path)
            if isinstance(progress_data, dict):
                return progress_data.copy()  # 복사본 반환
            elif progress_data == 'running':
                # 이전 형식의 데이터를 새 형식으로 변환
                return {'status': 'running'}
            elif progress_data == 'done':
                return {'status': 'done'}
            return None

    def get_partial_results(self, path: str) -> str:
        """
        현재까지 번역된 부분 결과를 반환합니다.
        """
        with self._lock:
            if path in self._progress and 'partial_results' in self._progress[path]:
                return '\n'.join(self._progress[path]['partial_results'])
            return ''

    def all(self):
        with self._lock:
            return {k: v.copy() if isinstance(v, dict) else v for k, v in self._progress.items()}

progress_manager = ProgressManager()
