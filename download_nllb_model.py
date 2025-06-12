# download_nllb_model.py
# NLLB 모델을 수동으로 다운로드하는 스크립트

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path
import os
from tqdm import tqdm

def download_nllb_model():
    """NLLB 모델을 로컬에 다운로드"""
    
    # 모델 정보
    model_name = "facebook/nllb-200-distilled-600M"
    local_dir = "./models/nllb-200-distilled-600M"
    
    print(f"🚀 NLLB 모델 다운로드 시작: {model_name}")
    print(f"📁 저장 위치: {local_dir}")
    print(f"📊 예상 크기: 약 2.4GB")
    print("-" * 50)
    
    # 디렉토리 생성
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. 토크나이저 다운로드
        print("1️⃣ 토크나이저 다운로드 중...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=local_dir,
            local_files_only=False,
            force_download=False  # 이미 있으면 다시 다운로드하지 않음
        )
        print("✅ 토크나이저 다운로드 완료!")
        
        # 2. 모델 다운로드
        print("2️⃣ 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=local_dir,
            local_files_only=False,
            force_download=False,
            torch_dtype='auto'
        )
        print("✅ 모델 다운로드 완료!")
        
        # 3. 로컬에 저장
        print("3️⃣ 로컬에 저장 중...")
        tokenizer.save_pretrained(local_dir)
        model.save_pretrained(local_dir)
        print("✅ 로컬 저장 완료!")
        
        # 4. 다운로드 확인
        print("4️⃣ 다운로드 파일 확인...")
        files_to_check = [
            "config.json",
            "tokenizer.json", 
            "tokenizer_config.json",
            "special_tokens_map.json"
        ]
        
        for filename in files_to_check:
            filepath = Path(local_dir) / filename
            if filepath.exists():
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ {filename} (누락)")
        
        # 모델 파일 확인 (pytorch_model.bin 또는 model.safetensors)
        model_files = list(Path(local_dir).glob("pytorch_model*.bin")) + \
                     list(Path(local_dir).glob("model*.safetensors"))
        
        if model_files:
            for model_file in model_files:
                size_mb = model_file.stat().st_size / (1024 * 1024)
                print(f"   ✅ {model_file.name} ({size_mb:.1f}MB)")
        else:
            print("   ❌ 모델 파일이 없습니다!")
            
        print("-" * 50)
        print("🎉 다운로드 완료!")
        print(f"📁 모델 위치: {os.path.abspath(local_dir)}")
        
        return local_dir
        
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return None

def test_model(model_path):
    """다운로드된 모델 테스트"""
    print("\n🧪 모델 테스트 중...")
    
    try:
        from transformers import pipeline
        
        # 파이프라인 생성
        translator = pipeline(
            "translation",
            model=model_path,
            tokenizer=model_path,
            device=-1  # CPU 사용
        )
        
        # 간단한 테스트
        test_text = "Hello, how are you?"
        result = translator(
            test_text, 
            src_lang="eng_Latn", 
            tgt_lang="kor_Hang",
            max_length=100
        )
        
        print(f"✅ 테스트 성공!")
        print(f"   입력: {test_text}")
        print(f"   출력: {result[0]['translation_text']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 NLLB 모델 다운로더")
    print("=" * 60)
    
    # 다운로드 실행
    model_path = download_nllb_model()
    
    if model_path:
        # 테스트 실행
        test_success = test_model(model_path)
        
        if test_success:
            print("\n🎯 다음 단계:")
            print("1. translator.py에서 다음과 같이 설정하세요:")
            print(f'   model_path = r"{os.path.abspath(model_path)}"')
            print("2. 프로그램을 다시 실행하세요.")
        else:
            print("\n⚠️ 모델 테스트에 실패했습니다. HuggingFace 자동 다운로드를 사용하세요.")
    else:
        print("\n❌ 다운로드에 실패했습니다.")
        print("💡 대안: 인터넷 연결을 확인하고 다시 시도하세요.")
    
    print("\n" + "=" * 60)
    input("계속하려면 Enter를 누르세요...")