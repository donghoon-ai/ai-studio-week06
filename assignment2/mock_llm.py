# mock_llm.py — 6~12주차용 모의 LLM 모듈
import random

def mock_llm_call(system, user_message, temperature=0.2, max_tokens=500):
    """실제 API와 동일한 인터페이스를 갖는 모의 함수.
    13주차에 이 함수의 내부만 실제 Anthropic 호출로 교체한다."""
    reviews_keywords = {
        "배송": '{"category": "배송", "sentiment": "긍정", "score": 4}',
        "환불": '{"category": "환불", "sentiment": "부정", "score": 2}',
        "품질": '{"category": "품질", "sentiment": "긍정", "score": 5}',
    }
    
    # 1) 어떤 응답을 줄지 먼저 결정합니다 (기본값: 기타)
    canned_response = '{"category": "기타", "sentiment": "중립", "score": 3}'
    for keyword, canned in reviews_keywords.items():
        if keyword in user_message:
            canned_response = canned
            break  # 키워드를 찾았으므로 루프를 종료합니다.

    # 2) 20% 확률로 불량 응답을 생성합니다.
    if random.random() < 0.2:
        # 3가지 불량 유형 중 하나를 무작위로 고릅니다.
        bad_type = random.choice(["code_fence", "chatty", "truncated"])
        
        if bad_type == "code_fence":
            # 마크다운 코드블록(백틱 3개)으로 감싼 형태
            canned_response = f"```json\n{canned_response}\n```"
            
        elif bad_type == "chatty":
            # 앞에 쓸데없는 텍스트(사족)가 붙은 형태
            canned_response = f"물론입니다! 분석 결과는 다음과 같습니다.\n{canned_response}"
            
        elif bad_type == "truncated":
            # 응답이 중간에 끊긴 형태 (문자열을 절반쯤에서 자름)
            # 과제 예시의 '{"category": "배송", "sentim' 처럼 만들기 위해 문자열 슬라이싱 사용
            cut_index = len(canned_response) // 2 + 2 
            canned_response = canned_response[:cut_index]
            
        # 이 프린트문이 있으면 나중에 왜 '실패 수'와 '불량 응답 수'가 다른지 파악하기 아주 좋습니다.
        print(f"\n[Mock] ⚠️ 불량 응답 발생 ({bad_type})")

    # 3) 최종 완성된 문자열(정상 or 불량)을 기존과 동일한 형태의 딕셔너리로 반환합니다.
    return {
        "text": canned_response, 
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 120, "output_tokens": 35}
    }