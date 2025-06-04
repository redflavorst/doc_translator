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
            print(f"[PROGRESS] 시작 - {path}")

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
                print(f"[PROGRESS] 총 청크 설정 - {path}: {total}개")
            else:
                print(f"[PROGRESS] 경고: {path}가 progress에 없음 (set_total_chunks)")

    def update_chunk_progress(self, path: str, chunk_index: int, status: str = 'processing'):
        """
        현재 처리 중인 청크 정보를 업데이트합니다.
        """
        with self._lock:
            if path in self._progress:
                self._progress[path]['current_chunk'] = chunk_index
                if chunk_index < len(self._progress[path]['chunks_info']):
                    self._progress[path]['chunks_info'][chunk_index]['status'] = status
                #print(f"[PROGRESS] 청크 진행 업데이트 - {path}: 청크 {chunk_index} -> {status}")
            else:
                print(f"[PROGRESS] 경고: {path}가 progress에 없음 (update_chunk_progress)")

    def add_chunk_result(self, path: str, chunk_index: int, result: str):
        """
        청크 번역 결과를 추가합니다.
        """
        with self._lock:
            if path in self._progress:
                self._progress[path]['chunks_completed'] += 1
                if chunk_index < len(self._progress[path]['chunks_info']):
                    self._progress[path]['chunks_info'][chunk_index]['status'] = 'completed'
                if chunk_index < len(self._progress[path]['partial_results']):
                    self._progress[path]['partial_results'][chunk_index] = result
                
                completed = self._progress[path]['chunks_completed']
                total = self._progress[path]['total_chunks']
                print(f"[PROGRESS] 청크 완료 - {path}: {completed}/{total} (청크 {chunk_index})")
            else:
                print(f"[PROGRESS] 경고: {path}가 progress에 없음 (add_chunk_result)")

    def finish(self, path: str):
        with self._lock:
            if path in self._progress:
                self._progress[path]['status'] = 'done'
                print(f"[PROGRESS] 완료 - {path}")
            else:
                print(f"[PROGRESS] 경고: {path}가 progress에 없음 (finish)")

    def error(self, path: str, error_msg: str):
        with self._lock:
            if path in self._progress:
                self._progress[path]['status'] = 'error'
                self._progress[path]['error'] = error_msg
                print(f"[PROGRESS] 오류 - {path}: {error_msg}")
            else:
                self._progress[path] = {'status': 'error', 'error': error_msg}
                print(f"[PROGRESS] 새 오류 항목 생성 - {path}: {error_msg}")

    def get(self, path: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            progress_data = self._progress.get(path)
            if isinstance(progress_data, dict):
                #print(f"[PROGRESS] 상태 조회 - {path}: {progress_data.get('status', 'unknown')}")
                return progress_data.copy()  # 복사본 반환
            elif progress_data == 'running':
                # 이전 형식의 데이터를 새 형식으로 변환
                #print(f"[PROGRESS] 이전 형식 변환 - {path}: running")
                return {'status': 'running'}
            elif progress_data == 'done':
                #print(f"[PROGRESS] 이전 형식 변환 - {path}: done")
                return {'status': 'done'}
            
            print(f"[PROGRESS] 상태 없음 - {path}")
            return None

    def get_partial_results(self, path: str) -> str:
        """
        현재까지 번역된 부분 결과를 반환합니다.
        """
        with self._lock:
            if path in self._progress and 'partial_results' in self._progress[path]:
                # 빈 문자열이 아닌 결과만 합치기
                results = [r for r in self._progress[path]['partial_results'] if r.strip()]
                combined = '\n'.join(results)
                #print(f"[PROGRESS] 부분 결과 조회 - {path}: {len(combined)}자")
                return combined
            
            #print(f"[PROGRESS] 부분 결과 없음 - {path}")
            return ''

    def all(self):
        with self._lock:
            #print(f"[PROGRESS] 전체 상태 조회: {list(self._progress.keys())}")
            return {k: v.copy() if isinstance(v, dict) else v for k, v in self._progress.items()}

progress_manager = ProgressManager()