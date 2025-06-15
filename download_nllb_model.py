# download_nllb_model.py
# NLLB 모델을 수동으로 다운로드하는 스크립트 (개선된 버전)

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path
import os
import sys
from tqdm import tqdm
import torch
import shutil

# 사용 가능한 NLLB 모델 목록
AVAILABLE_MODELS = {
    "600M": {
        "name": "facebook/nllb-200-distilled-600M",
        "size": "2.4GB",
        "description": "경량화된 모델 (빠름, 품질 보통)",
        "local_dir": "./models/nllb-200-distilled-600M"
    },
    "1.3B": {
        "name": "facebook/nllb-200-1.3B", 
        "size": "5.2GB",
        "description": "중간 크기 모델 (균형잡힌 성능)",
        "local_dir": "./models/nllb-200-1.3B"
    },
    "3.3B": {
        "name": "facebook/nllb-200-3.3B",
        "size": "13GB", 
        "description": "대용량 모델 (느림, 최고 품질)",
        "local_dir": "./models/nllb-200-3.3B"
    }
}

def show_model_menu():
    """모델 선택 메뉴 표시"""
    print("📚 사용 가능한 NLLB 모델:")
    print("-" * 80)
    
    for key, info in AVAILABLE_MODELS.items():
        print(f"{key:>4} | {info['size']:>6} | {info['description']}")
        print(f"     | 모델명: {info['name']}")
        print(f"     | 저장위치: {info['local_dir']}")
        print("-" * 80)
    
    print("\n💡 권장사항:")
    print("   - 번역 품질 우선: 1.3B 선택")
    print("   - 속도 우선: 600M 선택") 
    print("   - 최고 품질 (GPU 필요): 3.3B 선택")
    print()

def get_user_choice():
    """사용자 선택 받기"""
    while True:
        choice = input("어떤 모델을 다운로드하시겠습니까? (600M/1.3B/3.3B): ").strip().upper()
        if choice in AVAILABLE_MODELS:
            return choice
        else:
            print("❌ 올바른 선택이 아닙니다. 600M, 1.3B, 3.3B 중 하나를 입력하세요.")

def check_disk_space(required_gb):
    """디스크 공간 확인"""
    try:
        current_dir = Path.cwd()
        free_space = shutil.disk_usage(current_dir).free
        free_gb = free_space / (1024**3)
        
        print(f"💾 디스크 여유 공간: {free_gb:.1f}GB")
        print(f"📦 필요한 공간: ~{required_gb}GB")
        
        if free_gb < required_gb * 1.2:  # 20% 여유 공간 고려
            print(f"⚠️  디스크 공간이 부족할 수 있습니다!")
            choice = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
            return choice in ['y', 'yes']
        else:
            print("✅ 디스크 공간 충분")
            return True
            
    except Exception as e:
        print(f"⚠️  디스크 공간 확인 실패: {e}")
        return True  # 확인 실패 시에도 진행

def download_nllb_model(model_key):
    """선택된 NLLB 모델을 로컬에 다운로드"""
    
    model_info = AVAILABLE_MODELS[model_key]
    model_name = model_info["name"]
    local_dir = model_info["local_dir"]
    size_str = model_info["size"]
    
    print(f"🚀 NLLB 모델 다운로드 시작: {model_name}")
    print(f"📁 저장 위치: {local_dir}")
    print(f"📊 예상 크기: {size_str}")
    print(f"🔧 설명: {model_info['description']}")
    print("-" * 70)
    
    # 디스크 공간 확인
    required_gb = float(size_str.replace('GB', ''))
    if not check_disk_space(required_gb):
        print("❌ 다운로드 중단됨")
        return None
    
    # 디렉토리 생성
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. 토크나이저 다운로드
        print("1️⃣ 토크나이저 다운로드 중...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=None,  # 캐시 사용하지 않음
            local_files_only=False,
            force_download=False,
            resume_download=True  # 중단된 다운로드 재개
        )
        print("✅ 토크나이저 다운로드 완료!")
        
        # 2. 모델 다운로드 (진행률 표시)
        print("2️⃣ 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)")
        print("   💡 팁: 인터넷 연결이 중단되면 다시 실행하세요. 이어서 다운로드됩니다.")
        
        # 메모리 효율적인 다운로드
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=None,
            local_files_only=False,
            force_download=False,
            resume_download=True,
            torch_dtype=torch.float32,  # 호환성을 위해 float32 사용
            low_cpu_mem_usage=True  # 메모리 사용량 최적화
        )
        print("✅ 모델 다운로드 완료!")
        
        # 3. 로컬에 저장
        print("3️⃣ 로컬에 저장 중...")
        tokenizer.save_pretrained(local_dir)
        model.save_pretrained(local_dir)
        print("✅ 로컬 저장 완료!")
        
        # 4. 다운로드 확인
        print("4️⃣ 다운로드 파일 확인...")
        verify_download(local_dir)
        
        print("-" * 70)
        print("🎉 다운로드 완료!")
        print(f"📁 모델 위치: {os.path.abspath(local_dir)}")
        
        return local_dir
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단됨")
        print("💡 다음에 다시 실행하면 이어서 다운로드됩니다.")
        return None
        
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        print("\n🔧 문제 해결 방법:")
        print("1. 인터넷 연결 확인")
        print("2. 디스크 공간 확인") 
        print("3. Python 패키지 업데이트: pip install --upgrade transformers torch")
        print("4. 프록시 설정 확인")
        return None

def verify_download(model_path):
    """다운로드된 파일 확인"""
    model_dir = Path(model_path)
    
    # 필수 파일 확인
    required_files = [
        "config.json",
        "tokenizer.json", 
        "tokenizer_config.json",
        "special_tokens_map.json"
    ]
    
    missing_files = []
    for filename in required_files:
        filepath = model_dir / filename
        if filepath.exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} (누락)")
            missing_files.append(filename)
    
    # 모델 파일 확인
    model_files = list(model_dir.glob("pytorch_model*.bin")) + \
                 list(model_dir.glob("model*.safetensors"))
    
    total_size_mb = 0
    if model_files:
        for model_file in model_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            total_size_mb += size_mb
            print(f"   ✅ {model_file.name} ({size_mb:.1f}MB)")
    else:
        print("   ❌ 모델 파일이 없습니다!")
        missing_files.append("model files")
    
    if total_size_mb > 0:
        print(f"   📊 총 모델 크기: {total_size_mb:.1f}MB")
    
    if missing_files:
        print(f"   ⚠️  누락된 파일: {', '.join(missing_files)}")
        return False
    else:
        print("   ✅ 모든 파일 확인됨")
        return True

def test_model(model_path):
    """다운로드된 모델 테스트"""
    print("\n🧪 모델 테스트 중...")
    
    try:
        from transformers import pipeline
        
        # 파이프라인 생성
        print("   📝 파이프라인 생성 중...")
        translator = pipeline(
            "translation",
            model=model_path,
            tokenizer=model_path,
            device=-1,  # CPU 사용
            torch_dtype=torch.float32
        )
        
        # 간단한 테스트
        test_cases = [
            ("Hello, how are you?", "eng_Latn", "kor_Hang"),
            ("This is a test.", "eng_Latn", "kor_Hang")
        ]
        
        print("   🔄 번역 테스트 중...")
        for i, (text, src, tgt) in enumerate(test_cases, 1):
            result = translator(
                text, 
                src_lang=src, 
                tgt_lang=tgt,
                max_length=200,
                num_beams=2
            )
            
            print(f"   테스트 {i}:")
            print(f"     입력: {text}")
            print(f"     출력: {result[0]['translation_text']}")
        
        print("✅ 모델 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        print("💡 하지만 모델 파일은 정상적으로 다운로드되었을 수 있습니다.")
        return False

def update_translator_config(model_path, model_key):
    """translator.py 설정 업데이트 안내"""
    print("\n📝 설정 가이드:")
    print("=" * 60)
    print("translator.py에서 다음과 같이 수정하세요:")
    print()
    print("🔧 방법 1: 직접 경로 설정")
    print("   def _find_best_model(self) -> str:")
    print(f'       return r"{os.path.abspath(model_path)}"')
    print()
    print("🔧 방법 2: 환경 변수 설정")
    print(f'   export NLLB_MODEL_PATH="{os.path.abspath(model_path)}"')
    print()
    print("🔧 방법 3: 모델 경로 리스트에 추가")
    print("   preferred_models = [")
    print(f'       "{os.path.abspath(model_path)}",')
    print("       # 다른 경로들...")
    print("   ]")
    print("=" * 60)
    
    # 성능 최적화 팁
    if model_key in ["1.3B", "3.3B"]:
        print("\n⚡ 성능 최적화 팁:")
        print("1. GPU 사용 권장 (device='cuda')")
        print("2. float16 사용 (torch_dtype=torch.float16)")
        print("3. 배치 크기 조정")

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🤖 개선된 NLLB 모델 다운로더")
    print("=" * 70)
    
    # 의존성 확인
    try:
        import torch
        import transformers
        print(f"✅ PyTorch 버전: {torch.__version__}")
        print(f"✅ Transformers 버전: {transformers.__version__}")
    except ImportError as e:
        print(f"❌ 의존성 오류: {e}")
        print("💡 다음 명령어로 설치하세요:")
        print("   pip install torch transformers tqdm")
        return
    
    print()
    
    # 모델 선택
    show_model_menu()
    model_choice = get_user_choice()
    
    print(f"\n✅ 선택된 모델: {model_choice}")
    print(f"📦 {AVAILABLE_MODELS[model_choice]['description']}")
    
    # 확인
    confirm = input(f"\n{AVAILABLE_MODELS[model_choice]['size']} 다운로드를 시작하시겠습니까? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 다운로드 취소됨")
        return
    
    # 다운로드 실행
    print("\n" + "=" * 70)
    model_path = download_nllb_model(model_choice)
    
    if model_path:
        # 테스트 실행
        test_success = test_model(model_path)
        
        # 설정 가이드 표시
        update_translator_config(model_path, model_choice)
        
        if test_success:
            print("\n🎯 다음 단계:")
            print("1. 위의 설정 가이드를 따라 translator.py를 수정하세요.")
            print("2. 번역 프로그램을 다시 실행하세요.")
            print("3. 번역 품질 향상을 확인하세요!")
        else:
            print("\n⚠️ 모델은 다운로드되었지만 테스트에 실패했습니다.")
            print("💡 translator.py에서 직접 사용해보세요.")
    else:
        print("\n❌ 다운로드에 실패했습니다.")
        print("💡 인터넷 연결을 확인하고 다시 시도하세요.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        print("🐛 버그 리포트를 위해 위의 오류 메시지를 보고해주세요.")
    finally:
        input("\n계속하려면 Enter를 누르세요...")