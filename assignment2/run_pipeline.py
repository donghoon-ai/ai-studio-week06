import json
import csv
from mock_llm import mock_llm_call 

# 프롬프트 세팅
SYSTEM = """당신은 고객 리뷰 분류기입니다. 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 절대 포함하지 마세요.
{"category": "배송|품질|가격|서비스|기타", "sentiment": "긍정|부정|중립", "score": 1~5 사이의 정수}"""

error_stats = {
    "코드펜스_발생": 0,
    "코드펜스_복구": 0,
    "사족_발생": 0,
    "잘린JSON_발생": 0
}

def classify_review(review_text):

    global error_stats

    """리뷰 1건을 분류하여 딕셔너리로 반환. 실패 시 None."""
    result = mock_llm_call(SYSTEM, f"리뷰: {review_text}")
    raw = result["text"].strip() # 결과 텍스트의 앞뒤 불필요한 공백과 줄바꿈을 제거


    # 어떤 유형의 불량 응답이 발생했는지 텍스트 패턴으로 탐지 및 기록
    is_code_fence = raw.startswith("```")
    is_chatty = raw.startswith("물론입니다")
    # 정상 JSON은 '}'로 끝나야 함. '}'로 안 끝나고, 코드펜스(```)나 사족도 아니면 잘린 것.
    is_truncated = (not raw.endswith("}")) and (not is_code_fence) and (not is_chatty)

    if is_code_fence:
        error_stats["코드펜스_발생"] += 1
    elif is_chatty:
        error_stats["사족_발생"] += 1
    elif is_truncated:
        error_stats["잘린JSON_발생"] += 1

    # 방어 1: 마크다운 코드 블록 제거 (포맷 정규화): ```json ... ``` 코드 제거
    if is_code_fence:
        raw = raw.strip("`") # 문자열의 시작과 끝에 붙은 백틱(`)만 모두 제거
        raw = raw.replace("json", "", 1).strip() # "json"을 한번만(1회) 지우고 strip()
        
        # 백틱을 제거했으므로, 이 시점에서 코드펜스 유형은 복구된 것으로 간주
        error_stats["코드펜스_복구"] += 1

    # 방어 2: 파싱 실패는 언제든 일어날 수 있다 -> 예외 처리 필수
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # 방어 3: 필드 존재와 값의 유효성 검증
    if data.get("category") not in ["배송", "품질", "가격", "환불", "서비스", "기타"]:
        return None
        
    return data

def main():
    # 카운트 및 집계용 변수 초기화
    total_count = 0
    fail_count = 0
    stats = {}

    csv_file_path = "reviews_sample.csv" 

    print(f"데이터 처리를 시작합니다... ({csv_file_path})\n")
    
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # 리뷰 목록 자동 분류 및 집계
            for row in reader:
                total_count += 1
                
                r = row["review_text"]
                
                result = classify_review(r)
                
                if result is None:
                    # 실패 건은 건너뛰되 집계 카운트는 증가
                    fail_count += 1
                    continue
                
                # 성공 시 통계 딕셔너리에 누적
                cat = result["category"]
                stats[cat] = stats.get(cat, 0) + 1
                
    except FileNotFoundError:
        print(f"[오류] {csv_file_path} 파일을 찾을 수 없습니다. 같은 폴더에 있는지 확인해주세요.")
        return

    # 총 불량 응답 발생 건수 계산
    total_bad_generated = (
        error_stats["코드펜스_발생"] + 
        error_stats["사족_발생"] + 
        error_stats["잘린JSON_발생"]
    )


    #최종 실행 결과 분석 및 이유 설명 출력
    print("\n==================================================")
    print(f" 카테고리별 분류 통계: {stats}")
    print(f" 전체 처리: {total_count}건 /  최종 실패(M): {fail_count}건")
    print("--------------------------------------------------")
    print(f" 총 발생한 불량 응답 건수: {total_bad_generated}건")
    print(f"  - 코드펜스형: {error_stats['코드펜스_발생']}건 (이 중 {error_stats['코드펜스_복구']}건 복구 성공!)")
    print(f"  - 사족 포함형: {error_stats['사족_발생']}건 (복구 불가)")
    print(f"  - 잘린 JSON형: {error_stats['잘린JSON_발생']}건 (복구 불가)")
    print("--------------------------------------------------")
    print(f" [분석] 실패 {fail_count}건이 총 불량 응답 {total_bad_generated}건보다 적은 이유:")
    print(f"   => 불량 응답 중 '코드펜스형' {error_stats['코드펜스_복구']}건이 파이프라인의 '방어 1' 로직을 통해")
    print(f"      백틱(```)이 성공적으로 제거되고 정상적인 JSON으로 복구되었기 때문입니다.")
    print("==================================================")

if __name__ == "__main__":
    main()