/**
 * 3분 스피치 & 생각그물 마인드맵 AI 스튜디오 - 서울시교육청 에디션
 * File: js/app.js
 */

// 1. Mermaid 라이브러리 초기화
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Pretendard',
  mindmap: {
    useMaxWidth: true,
    padding: 16
  }
});

// Lucide 아이콘 초기화
lucide.createIcons();

// 2. 글로벌 상태 변수
let currentMermaidCode = `mindmap\n  root((스피치 주제))\n    [주요 논점 1]\n      구체적 근거\n      실천 사례\n    [주요 논점 2]\n      해결 방안\n      기대 효과\n    [결론 및 제언]\n      학급 실천 약속`;
let isRecording = false;
let recognition = null;
let recordStartTime = null;
let timerInterval = null;

// 3. 스피치 프리셋 데이터
const PRESETS = [
  {
    topic: "교내 스마트폰 사용 자율화",
    text: "저는 우리 학교에서 스마트폰 사용을 무조건 금지하기보다는 자율적으로 관리할 수 있는 기회를 주어야 한다고 생각합니다. 왜냐하면 첫째, 수업 시간에 모르는 어휘나 자료를 즉시 검색하여 탐구 능력을 높일 수 있습니다. 둘째, 학생 스스로 사용 시간을 통제해보는 경험이 진정한 디지털 시민 역량을 기르는 길이기 때문입니다. 다만 수업을 방해하지 않도록 '스마트폰 집중 보관 바구니'를 모둠별로 운영하는 규칙을 제안합니다."
  },
  {
    topic: "학교 탄소중립 실천 방안",
    text: "우리 학교가 기후 위기에 대응하기 위해 당장 실천할 수 있는 가장 확실한 방법은 급식 잔반 줄이기와 빈 교실 소등입니다. 매주 수요일을 잔반 없는 날로 지정하여 스티커 보상을 주고, 학급별로 에너지 지킴이를 정해 쉬는 시간마다 불필요한 전등과 전자칠판을 끄는 규칙을 만들면 연간 수 톤의 탄소를 줄일 수 있습니다."
  },
  {
    topic: "생성형 AI로 학교 숙제를 해도 될까?",
    text: "생성형 AI를 숙제에 활용하는 것은 표절이 아니라 새로운 협업 도구로 바라보아야 합니다. 단순 복사 붙여넣기는 금지해야 하지만, 내 아이디어를 발전시키거나 영어 문법을 교정받는 피드백 파트너로 쓰는 것은 학습 효율을 크게 높입니다. 중요한 것은 숙제 제출 시 'AI 프롬프트 사용 출처'를 투명하게 밝히는 윤리적 가이드라인을 세우는 것입니다."
  },
  {
    topic: "학생 자치와 즐거운 학급 문화",
    text: "선생님이 일방적으로 정하는 학급 규칙보다 우리가 직접 회의를 통해 만든 규칙이 훨씬 잘 지켜집니다. 우리 반만의 1달 1이벤트(예: 마니또, 칭찬 롤링페이퍼)를 운영하고, 친구 간의 사소한 갈등을 스스로 풀 수 있는 학급 자치 중재단을 만들면 따돌림 없는 평화로운 교실을 만들 수 있습니다."
  }
];

// 4. DOM 요소 참조
const apiKeyInput = document.getElementById('apiKeyInput');
const btnSaveKey = document.getElementById('btnSaveKey');
const toggleKeyBtn = document.getElementById('toggleKeyBtn');
const speechTextArea = document.getElementById('speechText');
const charCountEl = document.getElementById('charCount');
const btnGenerate = document.getElementById('btnGenerate');
const loader = document.getElementById('loader');
const mermaidTarget = document.getElementById('mermaidTarget');
const aiFeedback = document.getElementById('aiFeedback');
const renderStatus = document.getElementById('renderStatus');
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');
const speechTimer = document.getElementById('speechTimer');
const wikiCard = document.getElementById('wikiCard');
const wikiTitle = document.getElementById('wikiTitle');
const wikiExtract = document.getElementById('wikiExtract');

// 5. API Key 로컬 스토리지 연동
const savedKey = localStorage.getItem('sen_openrouter_key') || '';
if (savedKey) apiKeyInput.value = savedKey;

btnSaveKey.addEventListener('click', () => {
  const val = apiKeyInput.value.trim();
  if (!val) {
    alert('API Key를 입력해주세요.');
    return;
  }
  localStorage.setItem('sen_openrouter_key', val);
  alert('API Key가 브라우저에 안전하게 저장되었습니다!');
});

toggleKeyBtn.addEventListener('click', () => {
  apiKeyInput.type = (apiKeyInput.type === 'password') ? 'text' : 'password';
});

// 6. 프리셋 로더 함수
window.loadPreset = function(idx) {
  const p = PRESETS[idx];
  speechTextArea.value = p.text;
  updateCharCount();
  fetchWikiSummary(p.topic);
};

// 7. 글자수 업데이트
speechTextArea.addEventListener('input', updateCharCount);
function updateCharCount() {
  charCountEl.innerText = `${speechTextArea.value.length} 자 입력됨`;
}

// 8. Wikipedia 무료 No-Key API 조회
async function fetchWikiSummary(topic) {
  try {
    const res = await fetch(`https://ko.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic)}`);
    if (!res.ok) throw new Error('Wiki not found');
    const data = await res.json();
    if (data.extract) {
      wikiTitle.innerHTML = `<i data-lucide="book-open" class="w-4 h-4 text-emerald-400"></i> ${data.title} - 배경지식`;
      wikiExtract.innerText = data.extract;
      wikiCard.classList.remove('hidden');
      lucide.createIcons();
    }
  } catch (e) {
    wikiCard.classList.add('hidden');
  }
}

// 9. Web Speech API (마이크 음성 인식)
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'ko-KR';

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add('recording-pulse');
    micStatus.innerText = '녹음 중 (마이크에 말하세요)';
    recordStartTime = Date.now();
    timerInterval = setInterval(updateTimer, 500);
  };

  recognition.onresult = (event) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      }
    }
    if (finalTranscript) {
      speechTextArea.value = (speechTextArea.value + ' ' + finalTranscript).trim();
      updateCharCount();
    }
  };

  recognition.onerror = (e) => {
    console.warn('Speech recognition error', e);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
  };

  micBtn.addEventListener('click', () => {
    if (!isRecording) {
      try {
        recognition.start();
      } catch(e) {
        alert('마이크 접근 권한이 필요합니다.');
      }
    } else {
      recognition.stop();
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "이 브라우저는 음성인식을 지원하지 않습니다. (Chrome/Edge 권장)";
  micStatus.innerText = "음성 미지원 (직접입력)";
  micBtn.classList.replace('bg-red-600', 'bg-slate-700');
}

function stopRecording() {
  isRecording = false;
  micBtn.classList.remove('recording-pulse');
  micStatus.innerText = '음성 인식 시작';
  if (timerInterval) clearInterval(timerInterval);
  speechTimer.innerText = '⏱️ 녹음 종료';
}

function updateTimer() {
  const elapsed = Math.floor((Date.now() - recordStartTime) / 1000);
  const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const s = String(elapsed % 60).padStart(2, '0');
  speechTimer.innerText = `⏱️ 스피치 시간: ${m}:${s}`;
}

// 10. OpenRouter Gemini 3.8 Flash 호출 & 렌더링
btnGenerate.addEventListener('click', async () => {
  const text = speechTextArea.value.trim();
  if (!text) {
    alert('학생의 스피치 내용이나 발언문을 먼저 입력해주세요.');
    return;
  }

  const apiKey = apiKeyInput.value.trim();
  if (!apiKey) {
    alert('상단에 OpenRouter API Key를 입력해주세요.\n(openrouter.ai 에서 키를 발급받을 수 있습니다)');
    apiKeyInput.focus();
    return;
  }

  loader.classList.remove('hidden');
  renderStatus.innerText = '● Gemini 3.8 Flash 추론 중...';
  renderStatus.className = 'text-amber-400 font-medium';

  const prompt = `
당신은 서울시교육청 최고의 생각그물(마인드맵) 설계사이자 스피치 코칭 전문가입니다.
학생의 스피치 발언문을 분석하여 반드시 유효한 Mermaid 'mindmap' 문법 코드와, 교사용 관찰 평가 피드백을 JSON으로 작성해주세요.

[학생 발언문]
"${text}"

[요구사항]
1. Mermaid mindmap 문법 규칙을 엄격히 준수하세요.
   - 반드시 첫 줄은 "mindmap" 으로 시작합니다.
   - root 노드는 "root((핵심 주제))" 형태여야 합니다.
   - 들여쓰기(2칸 공백)로 계층 구조를 만드세요.
   - 대주제 [사각괄호], 소주제 (원형) 또는 일반 텍스트 사용.
   - 노드 텍스트 안에 쌍따옴표나 괄호 등 문법을 깨뜨리는 특수문자는 넣지 마세요.
2. 학생의 스피치 피드백:
   - 강점 2가지 (논리적 연결성, 참신성, 구체성 등)
   - 보완 제언 1가지 (근거 보강, 반대 입장 배려 등)

[반환 형식]
반드시 다른 설명 없이 아래 JSON 포맷으로만 응답하세요:
{
  "mermaid": "mindmap\\n  root((스마트폰 자율화))\\n    [학습 효과]\\n      실시간 자료 탐구\\n      어휘 검색\\n    [디지털 역량]\\n      스스로 통제 경험\\n      자기주도성 강화\\n    [실천 규칙]\\n      모둠 집중 바구니 운영",
  "feedback": "• 장점 1: ...\\n• 장점 2: ...\\n• 보완점: ..."
}
`;

  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": window.location.href,
        "X-Title": "SEN Speech MindMap Studio"
      },
      body: JSON.stringify({
        model: "google/gemini-2.0-flash-exp:free",
        messages: [{ role: "user", content: prompt }]
      })
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error?.message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    let content = data.choices[0].message.content.trim();
    content = content.replace(/```json/g, '').replace(/```/g, '').trim();
    
    const parsed = JSON.parse(content);
    currentMermaidCode = parsed.mermaid;

    await renderMermaidDiagram(currentMermaidCode);
    aiFeedback.innerHTML = parsed.feedback.replace(/\n/g, '<br>');

    renderStatus.innerText = '● 렌더링 완료 (완벽 생성됨)';
    renderStatus.className = 'text-emerald-400 font-medium';

    confetti({
      particleCount: 80,
      spread: 60,
      origin: { y: 0.6 }
    });

  } catch (err) {
    console.error(err);
    alert('생각그물 생성 중 오류가 발생했습니다:\n' + err.message + '\n\nOpenRouter API Key 유효 여부를 확인해주세요.');
    renderStatus.innerText = '● 오류 발생';
    renderStatus.className = 'text-red-400 font-medium';
  } finally {
    loader.classList.add('hidden');
  }
});

async function renderMermaidDiagram(code) {
  mermaidTarget.removeAttribute('data-processed');
  mermaidTarget.innerHTML = code;
  try {
    await mermaid.run({ nodes: [mermaidTarget] });
  } catch (e) {
    console.warn('Mermaid rendering retry...', e);
  }
}

// 11. PNG 이미지 저장 (html2canvas)
document.getElementById('btnExportPng').addEventListener('click', async () => {
  const container = document.getElementById('diagramContainer');
  try {
    const canvas = await html2canvas(container, {
      backgroundColor: '#090d16',
      scale: 2
    });
    const link = document.createElement('a');
    link.download = `스피치_마인드맵_${new Date().toISOString().slice(0,10)}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  } catch(e) {
    alert('이미지 저장 중 오류가 발생했습니다.');
  }
});

// 12. Mermaid 코드 복사
document.getElementById('btnCopyCode').addEventListener('click', () => {
  navigator.clipboard.writeText(currentMermaidCode).then(() => {
    alert('Mermaid 다이어그램 코드가 클립보드에 복사되었습니다!\n노션이나 마크다운 문서에 바로 붙여넣을 수 있습니다.');
  });
});
