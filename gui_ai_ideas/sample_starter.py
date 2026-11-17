"""
[스타터 템플릿] CustomTkinter + 무료 API(Open-Meteo) + OpenRouter(Gemini 3.8 Flash)
실행 전 필요 라이브러리:
pip install customtkinter requests openai
"""

import os
import requests
import customtkinter as ctk
from openai import OpenAI

# ----------------------------------------------------
# 1. OpenRouter 클라이언트 설정
# ----------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ----------------------------------------------------
# 2. 키 없는 무료 API 함수 (Open-Meteo 서울 날씨 예시)
# ----------------------------------------------------
def get_seoul_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&current_weather=true"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        curr = data.get("current_weather", {})
        temp = curr.get("temperature", "N/A")
        wind = curr.get("windspeed", "N/A")
        return f"현재 서울 기온: {temp}℃, 풍속: {wind}km/h"
    except Exception as e:
        return f"날씨 정보 수신 실패: {e}"

# ----------------------------------------------------
# 3. GUI 애플리케이션 정의
# ----------------------------------------------------
class SmartLunchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🍱 스마트 오피스 런치 & 컨디션 AI 큐레이터")
        self.geometry("640x560")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # 타이틀
        self.lbl_title = ctk.CTkLabel(
            self, text="⚡ 날씨 실시간 연동 점심 메뉴 추천기", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_title.pack(pady=15)

        # 날씨 표시 영역
        self.weather_info = get_seoul_weather()
        self.lbl_weather = ctk.CTkLabel(
            self, text=f"🌤️ {self.weather_info}", font=ctk.CTkFont(size=14)
        )
        self.lbl_weather.pack(pady=5)

        # 사용자 입력 (기분/상황)
        self.entry_mood = ctk.CTkEntry(
            self, placeholder_text="오늘 팀원들의 기분이나 특별한 요구사항 (예: 어제 야근해서 매운 거 땡김)", width=480
        )
        self.entry_mood.pack(pady=10)

        # 추천 버튼
        self.btn_recommend = ctk.CTkButton(
            self, text="Gemini로 맞춤형 메뉴 & 사내 공지문 생성", command=self.on_recommend_click
        )
        self.btn_recommend.pack(pady=10)

        # 결과 텍스트 박스
        self.txt_result = ctk.CTkTextbox(self, width=540, height=280, font=ctk.CTkFont(size=13))
        self.txt_result.pack(pady=10)

    def on_recommend_click(self):
        user_mood = self.entry_mood.get() or "보통"
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", "Gemini 3.8 Flash에 문의 중입니다... 잠시만 기다려주세요.\n")
        self.update()

        prompt = f"""
당신은 사내에서 가장 센스 넘치는 직장인 AI 비서입니다.
현재 외부 날씨 데이터: {self.weather_info}
직원들의 오늘 컨디션/요구: {user_mood}

위 조건에 꼭 맞는 점심 메뉴 3가지를 추천하고, 사내 메신저(슬랙/카톡)에 바로 복사해서 붙여넣을 수 있는 위트 있고 센스 넘치는 점심 공지 문구를 작성해주세요.
"""

        try:
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free", # 또는 google/gemini-2.5-flash
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content
            self.txt_result.delete("0.0", "end")
            self.txt_result.insert("0.0", result)
        except Exception as e:
            self.txt_result.delete("0.0", "end")
            self.txt_result.insert("0.0", f"오류 발생 (API 키 확인 필요): {e}")

if __name__ == "__main__":
    app = SmartLunchApp()
    app.mainloop()
