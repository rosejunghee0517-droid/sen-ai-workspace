"""
사내 탕비실 성분 분석기 & 알레르기 안전 가디언 (Office Snack Guardian)
- 무료 No-Key API: OpenFoodFacts (제품 성분, 영양 정보, 알레르기 유발물질)
- AI 엔진: OpenRouter Gemini 3.8 Flash
- GUI: CustomTkinter (모던 다크 테마)
"""

import os
import threading
import requests
import customtkinter as ctk
from tkinter import messagebox
from openai import OpenAI

# ----------------------------------------------------
# 1. 한국 탕비실 대표 간식 프리셋 (실제 바코드 및 검색어 매핑)
# ----------------------------------------------------
POPULAR_SNACKS = [
    ("🍪 초코파이", "8801117111052", "오리온 초코파이 정"),
    ("🍜 신라면", "8801043014854", "농심 신라면"),
    ("⚡ 몬스터 에너지", "5060166692345", "몬스터 에너지"),
    ("☕ 맥심 모카골드", "8801037086881", "동서식품 맥심 모카골드 마일드"),
    ("🍫 롯데 빼빼로", "8801062635467", "롯데 아몬드 빼빼로"),
    ("🥤 코카콜라 제로", "5449000000996", "코카콜라"),
]

HEADERS = {
    "User-Agent": "OfficeSnackGuardian/1.0 (Windows; Python CustomTkinter; Educational Tool)"
}

# ----------------------------------------------------
# 2. OpenFoodFacts 무료 API 호출 함수 (No-Key)
# ----------------------------------------------------
def fetch_product_info(query: str):
    """바코드 또는 제품명으로 OpenFoodFacts 데이터 조회"""
    query = query.strip()
    if not query:
        raise ValueError("검색어 또는 바코드를 입력하세요.")

    # 1) 숫자로만 이루어진 경우 바코드 직접 조회
    if query.isdigit() and len(query) >= 8:
        url = f"https://world.openfoodfacts.org/api/v0/product/{query}.json"
        res = requests.get(url, headers=HEADERS, timeout=8)
        data = res.json()
        if data.get("status") == 1 and "product" in data:
            return parse_product_data(data["product"])

    # 2) 한국 로케일 및 글로벌 검색 시도
    search_urls = [
        f"https://kr.openfoodfacts.org/cgi/search.pl?search_terms={requests.utils.quote(query)}&search_simple=1&action=process&json=1&page_size=3",
        f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={requests.utils.quote(query)}&search_simple=1&action=process&json=1&page_size=5"
    ]

    for search_url in search_urls:
        try:
            res = requests.get(search_url, headers=HEADERS, timeout=6)
            data = res.json()
            products = data.get("products", [])
            if products:
                return parse_product_data(products[0])
        except Exception:
            continue

    # OpenFoodFacts에 없을 경우 기본 메타데이터 생성 (Gemini가 보완 추론)
    return {
        "name": query,
        "brand": "일반 시판 제품",
        "ingredients": "OpenFoodFacts DB에 등록되지 않았거나 미표기 상태 (Gemini 지식베이스 기반 분석 진행)",
        "allergens": "제품군 특성에 따른 일반 알레르기 점검 필요",
        "grade": "N/A",
        "kcal": "시판 평균 기준 추정",
        "sugars": "시판 평균 기준 추정",
        "sodium": "시판 평균 기준 추정",
        "fat": "시판 평균 기준 추정",
        "protein": "시판 평균 기준 추정",
    }


def parse_product_data(p: dict) -> dict:
    """필요한 영양 성분 추출 및 정돈"""
    name = (
        p.get("product_name_ko")
        or p.get("product_name")
        or p.get("generic_name_ko")
        or p.get("generic_name")
        or "이름 미상 제품"
    )
    brand = p.get("brands") or "제조사 미표기"
    ingredients = (
        p.get("ingredients_text_ko")
        or p.get("ingredients_text")
        or "원재료 상세 미표기"
    )
    allergens = p.get("allergens") or p.get("allergens_tags") or "명시된 알레르기 유발물질 없음"
    if isinstance(allergens, list):
        allergens = ", ".join([str(a).replace("en:", "").replace("ko:", "") for a in allergens]) or "없음"

    nutriments = p.get("nutriments", {})
    kcal = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal") or nutriments.get("energy-kcal_serving") or "N/A"
    sugars = nutriments.get("sugars_100g") or nutriments.get("sugars") or "N/A"
    sodium = nutriments.get("sodium_100g") or nutriments.get("sodium") or "N/A"
    fat = nutriments.get("fat_100g") or nutriments.get("fat") or "N/A"
    protein = nutriments.get("proteins_100g") or nutriments.get("proteins") or "N/A"
    grade = (p.get("nutriscore_grade") or "N/A").upper()

    return {
        "name": name,
        "brand": brand,
        "ingredients": str(ingredients)[:500],
        "allergens": str(allergens),
        "grade": grade,
        "kcal": kcal,
        "sugars": sugars,
        "sodium": sodium,
        "fat": fat,
        "protein": protein,
    }


# ----------------------------------------------------
# 3. OpenRouter Gemini 3.8 Flash 분석 프롬프트
# ----------------------------------------------------
def analyze_with_gemini(api_key: str, product_data: dict) -> str:
    """Gemini 3.8 Flash를 호출하여 직장인 맞춤형 분석 리포트 생성"""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = f"""
당신은 사내 탕비실의 건강과 생산성을 지키는 냉철하면서도 유쾌한 '사내 탕비실 AI 가디언'입니다.
직원들이 간식을 먹을 때 건강을 챙기고, 식곤증 없이 칼퇴할 수 있도록 전문적이면서도 아주 위트 넘치는 리포트를 작성해주세요.

[식품 데이터]
- 제품명: {product_data['name']} (브랜드: {product_data['brand']})
- 영양 등급: Nutri-Score {product_data['grade']}
- 열량: 약 {product_data['kcal']} kcal
- 당류: {product_data['sugars']} g | 지방: {product_data['fat']} g | 단백질: {product_data['protein']} g | 나트륨: {product_data['sodium']} g
- 원재료 요약: {product_data['ingredients']}
- 포함된 알레르기 정보: {product_data['allergens']}

반드시 아래 5가지 목차로 나누어 직원들이 보고 무릎을 탁 칠 정도로 생생하고 재미있게 작성해주세요:

### 1. 🚨 오후 3시 식곤증 & 혈당 스파이크 경보
- [위험도: 안전 / 주의 / 극도로 위험] 중 택1
- 당류와 탄수화물 흡수 속도를 감안할 때, 회의 전이나 나른한 오후에 섭취 시 찾아올 식곤증 수위와 뇌 정지(Brain Fog) 가능성 진단

### 2. 🏃 직장인 현실 칼로리 소모 처방전
- 이 간식을 완전히 태우기 위해 필요한 '회사 내 생존 운동량' (예: "비상계단 1층부터 18층까지 2회 왕복" 또는 "화장실 갈 때마다 런지 40회")

### 3. 🛡️ 알레르기 & 체질 안전 가이드
- 우유(유당불내증), 밀(글루텐), 견과류, 대두, 카페인 민감자 등 사내 동료들이 주의해야 할 알레르기 성분 콕 집어 설명

### 4. 💻 최적의 섭취 타이밍 & 추천 업무 시나리오
- "이럴 때 드시면 극효율입니다" (예: 기획서 마감 1시간 전 폭풍 타이핑, 단순 엑셀 복붙 노가다, 월요병 극복용 등)

### 5. 🏷️ 탕비실 포스트잇 한 줄 요약
- 탕비실 간식 바구니 위에 포스트잇으로 붙여두면 직원들이 키득거릴 만한 촌철살인 한 줄 경고문
"""

    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free",  # OpenRouter 무료 Gemini Flash
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ----------------------------------------------------
# 4. CustomTkinter GUI 클래스
# ----------------------------------------------------
class SnackGuardianApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛡️ 사내 탕비실 성분 분석기 & 알레르기 안전 가디언")
        self.geometry("1020x740")
        self.minsize(920, 640)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.current_analysis_text = ""
        self.build_ui()

    def build_ui(self):
        # 상단 헤더 프레임
        header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#111827")
        header_frame.pack(fill="x", padx=16, pady=(14, 8))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="🛡️ 사내 탕비실 성분 분석기 & 알레르기 가디언",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color="#10B981",
        )
        title_lbl.pack(anchor="w", padx=16, pady=(10, 2))

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="무료 OpenFoodFacts DB + Gemini 3.8 Flash가 직장인의 식곤증, 혈당 스파이크, 알레르기를 지켜드립니다.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF",
        )
        sub_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # API Key 입력 프레임
        key_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#1F2937")
        key_frame.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(key_frame, text="🔑 OpenRouter API Key:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(14, 8), pady=8
        )
        default_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="sk-or-v1-...",
            width=380,
            show="*"
        )
        if default_key:
            self.key_entry.insert(0, default_key)
        self.key_entry.pack(side="left", padx=5, pady=8)

        self.btn_toggle_key = ctk.CTkButton(
            key_frame, text="보기", width=50, height=28, command=self.toggle_key_visibility
        )
        self.btn_toggle_key.pack(side="left", padx=5, pady=8)

        # 탕비실 인기 간식 퀵 프리셋 버튼들
        preset_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#1F2937")
        preset_frame.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(preset_frame, text="⚡ 인기 간식 빠른 선택:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(14, 10), pady=6
        )

        for label, barcode, name in POPULAR_SNACKS:
            btn = ctk.CTkButton(
                preset_frame,
                text=label,
                width=90,
                height=28,
                fg_color="#374151",
                hover_color="#4B5563",
                command=lambda b=barcode, n=name: self.on_preset_click(b, n),
            )
            btn.pack(side="left", padx=3, pady=6)

        # 검색 및 분석 실행 프레임
        search_frame = ctk.CTkFrame(self, corner_radius=8)
        search_frame.pack(fill="x", padx=16, pady=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="간식 이름 (예: 초코파이, 신라면, 포카칩) 또는 바코드 번호 입력...",
            font=ctk.CTkFont(size=14),
            height=40,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(14, 10), pady=8)
        self.search_entry.bind("<Return>", lambda e: self.start_analysis())

        self.btn_search = ctk.CTkButton(
            search_frame,
            text="🚀 성분 분석 및 AI 가디언 호출",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_analysis,
        )
        self.btn_search.pack(side="left", padx=(0, 14), pady=8)

        # 메인 콘텐츠 (좌: OpenFoodFacts 영양 스펙 / 우: Gemini 3.8 Flash AI 리포트)
        content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # 좌측: 영양 스펙 카드
        left_frame = ctk.CTkFrame(content_frame, width=340, corner_radius=10)
        left_frame.pack(side="left", fill="both", padx=(0, 8), pady=0)
        left_frame.pack_propagate(False)

        ctk.CTkLabel(
            left_frame, text="📊 OpenFoodFacts 영양 스펙", font=ctk.CTkFont(size=15, weight="bold"), text_color="#60A5FA"
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.txt_nutri = ctk.CTkTextbox(left_frame, font=ctk.CTkFont(size=12), wrap="word")
        self.txt_nutri.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_nutri.insert("0.0", "상단의 '인기 간식 빠른 선택'을 누르거나\n검색창에 간식명/바코드를 입력하면\n영양 스펙과 알레르기 정보가 표시됩니다.")
        self.txt_nutri.configure(state="disabled")

        # 우측: Gemini 분석 결과
        right_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)

        right_top = ctk.CTkFrame(right_frame, fg_color="transparent")
        right_top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            right_top, text="🤖 Gemini 3.8 Flash 직장인 맞춤 처방전", font=ctk.CTkFont(size=15, weight="bold"), text_color="#34D399"
        ).pack(side="left")

        self.btn_copy = ctk.CTkButton(
            right_top, text="📋 결과 복사", width=80, height=26, command=self.copy_result
        )
        self.btn_copy.pack(side="right")

        self.txt_ai = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(size=13), wrap="word")
        self.txt_ai.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_ai.insert(
            "0.0",
            "🛡️ 탕비실 AI 가디언이 대기 중입니다.\n\n"
            "• 식곤증 & 혈당 스파이크 수위 진단\n"
            "• 사무실 내 생존 운동량 환산\n"
            "• 알레르기 및 유해 성분 점검\n"
            "• 업무 시나리오별 섭취 가이드 & 탕비실 포스트잇 라벨"
        )
        self.txt_ai.configure(state="disabled")

        # 하단 상태 바
        self.status_bar = ctk.CTkLabel(
            self, text="준비 완료 - 탕비실 간식을 선택하거나 검색하세요.", anchor="w", text_color="#9CA3AF"
        )
        self.status_bar.pack(fill="x", padx=20, pady=(0, 6))

    def toggle_key_visibility(self):
        if self.key_entry.cget("show") == "*":
            self.key_entry.configure(show="")
            self.btn_toggle_key.configure(text="숨김")
        else:
            self.key_entry.configure(show="*")
            self.btn_toggle_key.configure(text="보기")

    def on_preset_click(self, barcode: str, name: str):
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, barcode)
        self.start_analysis()

    def set_status(self, text: str, is_error: bool = False):
        color = "#EF4444" if is_error else "#9CA3AF"
        self.status_bar.configure(text=text, text_color=color)

    def copy_result(self):
        if not self.current_analysis_text:
            messagebox.showinfo("알림", "복사할 분석 결과가 없습니다.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_analysis_text)
        messagebox.showinfo("완료", "분석 리포트가 클립보드에 복사되었습니다!\n사내 메신저나 슬랙에 바로 공유해보세요.")

    def start_analysis(self):
        query = self.search_entry.get().strip()
        if not query:
            self.set_status("검색할 간식 이름이나 바코드를 입력해주세요.", is_error=True)
            return

        api_key = self.key_entry.get().strip()
        if not api_key:
            messagebox.showwarning(
                "API 키 필요",
                "OpenRouter API Key를 입력해주세요.\n(https://openrouter.ai 에서 무료/유료 키 발급 가능)"
            )
            return

        self.btn_search.configure(state="disabled")
        self.set_status(f"'{query}' 정보를 OpenFoodFacts 무료 DB에서 조회 중...")

        # 백그라운드 스레드로 비동기 처리
        threading.Thread(target=self._run_process, args=(query, api_key), daemon=True).start()

    def _run_process(self, query: str, api_key: str):
        try:
            # 1. OpenFoodFacts 데이터 수신
            product = fetch_product_info(query)

            nutri_text = (
                f"🏷️ 제품명: {product['name']}\n"
                f"🏢 제조사: {product['brand']}\n"
                f"🏅 영양 등급: Nutri-Score {product['grade']}\n"
                f"────────────────────────\n"
                f"🔥 열량: {product['kcal']} kcal\n"
                f"🍬 당류: {product['sugars']} g\n"
                f"🧈 지방: {product['fat']} g\n"
                f"🥩 단백질: {product['protein']} g\n"
                f"🧂 나트륨: {product['sodium']} g\n"
                f"────────────────────────\n"
                f"⚠️ 알레르기 유발 정보:\n{product['allergens']}\n\n"
                f"📜 원재료 요약:\n{product['ingredients']}"
            )
            self.after(0, self._update_nutri_card, nutri_text)
            self.after(0, self.set_status, f"'{product['name']}' 분석 중... Gemini 3.8 Flash 호출 중...")

            # 2. Gemini 3.8 Flash 분석
            analysis = analyze_with_gemini(api_key, product)
            self.current_analysis_text = f"[{product['name']} 사내 탕비실 가디언 리포트]\n\n" + analysis

            self.after(0, self._update_ai_report, analysis)
            self.after(0, self.set_status, f"✅ 분석 완료: '{product['name']}' 리포트가 준비되었습니다.")

        except Exception as e:
            err_msg = f"오류 발생: {str(e)}"
            self.after(0, self._handle_error, err_msg)
        finally:
            self.after(0, lambda: self.btn_search.configure(state="normal"))

    def _update_nutri_card(self, text: str):
        self.txt_nutri.configure(state="normal")
        self.txt_nutri.delete("0.0", "end")
        self.txt_nutri.insert("0.0", text)
        self.txt_nutri.configure(state="disabled")

    def _update_ai_report(self, text: str):
        self.txt_ai.configure(state="normal")
        self.txt_ai.delete("0.0", "end")
        self.txt_ai.insert("0.0", text)
        self.txt_ai.configure(state="disabled")

    def _handle_error(self, err: str):
        self.set_status(err, is_error=True)
        self.txt_ai.configure(state="normal")
        self.txt_ai.delete("0.0", "end")
        self.txt_ai.insert("0.0", f"❌ 분석 중 문제가 발생했습니다.\n\n{err}\n\n• OpenRouter API 키가 유효한지 확인하세요.\n• 네트워크 상태를 확인하세요.")
        self.txt_ai.configure(state="disabled")


if __name__ == "__main__":
    app = SnackGuardianApp()
    app.mainloop()
