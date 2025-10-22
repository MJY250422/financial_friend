import streamlit as st
from datetime import datetime
import random

# Page config
st.set_page_config(
    page_title="금융친구 | Financial Friend",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Main styling */
    .main {
        background-color: #FAF7F2;
    }
    
    /* Header */
    .main-header {
        background: #FFFFFF;
        padding: 1.5rem;
        border-bottom: 3px solid #D4AF37;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(139, 115, 85, 0.08);
    }
    
    /* Summary box */
    .summary-box {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B4 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.15);
        margin-bottom: 2rem;
        border-left: 5px solid #D4AF37;
    }
    
    /* News card */
    .news-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E8E4DF;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .news-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 20px rgba(139, 115, 85, 0.15);
        border-color: #D4AF37;
    }
    
    /* Highlighted term - 클릭 가능하게 */
    .highlighted-term {
        background: linear-gradient(180deg, transparent 60%, #FFE5B4 60%);
        font-weight: 600;
        cursor: pointer;
        border-bottom: 2px dotted #D4AF37;
        padding: 2px 4px;
        transition: all 0.2s ease;
        display: inline;
    }
    
    .highlighted-term:hover {
        background: #FFE5B4;
        border-bottom: 2px solid #D4AF37;
    }
    
    /* Tags */
    .tag {
        background: #E8E4DF;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        margin-right: 8px;
        display: inline-block;
        color: #5C4A3A;
        font-weight: 500;
    }
    
    /* Chat container with scroll */
    .chat-container {
        height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: white;
        border-radius: 12px;
        border: 1px solid #E8E4DF;
        margin-bottom: 1rem;
    }
    
    /* Chat welcome */
    .chat-welcome {
        background: #FFF9E6;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        border: 2px dashed #D4AF37;
    }
    
    /* Article view */
    .article-full {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #E8E4DF;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #FAF7F2;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #D4AF37;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #C19B2E;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for term clicking
st.markdown("""
<script>
    function selectTerm(term) {
        // Streamlit의 session state를 업데이트하기 위한 트릭
        const input = window.parent.document.querySelector('input[aria-label="term_clicked"]');
        if (input) {
            input.value = term;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
</script>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False
if 'term_clicked' not in st.session_state:
    st.session_state.term_clicked = None

# ========================================
# DATA - 실제 금융 용어 사전
# ========================================
GLOSSARY = {
    "기준금리": {
        "definition": "한국은행이 금융기관에 돈을 빌려줄 때 적용하는 기본 금리입니다. 시중의 모든 금리에 영향을 주는 기준점이 됩니다.",
        "analogy": "집의 온도를 조절하는 중앙 온도 조절기와 같아요. 기준금리를 올리면 경제를 식히고, 내리면 경제를 데웁니다.",
        "example": "2023년 한국은행은 물가가 너무 빨리 오르자 기준금리를 3.50%까지 올렸습니다. 이로 인해 대출 이자가 높아져 사람들의 소비가 줄어들었어요.",
        "related_terms": ["금융통화위원회", "인플레이션", "통화정책"]
    },
    "금융통화위원회": {
        "definition": "한국은행의 금리 결정 기구로, 7명의 위원이 한 달에 한 번 모여 기준금리를 결정합니다.",
        "analogy": "경제의 체온을 재고 약을 처방하는 의사 회의와 같아요. 경제가 너무 뜨거우면 금리를 올리고, 너무 차가우면 금리를 내립니다.",
        "example": "금통위는 2024년 10월 회의에서 기준금리를 3.50%로 동결했습니다. 경기 회복세와 물가 안정을 동시에 고려한 결정이었어요.",
        "related_terms": ["기준금리", "통화정책", "한국은행"]
    },
    "인플레이션": {
        "definition": "물가가 지속적으로 오르는 현상을 말합니다. 같은 돈으로 살 수 있는 물건이 점점 줄어드는 것이죠.",
        "analogy": "풍선이 부풀어 오르는 것과 같아요. 돈의 가치는 그대로인데 물건의 가격이 점점 커지는 거예요.",
        "example": "2022년 한국의 인플레이션율은 5%를 넘었습니다. 작년에 1만원이던 치킨이 올해는 1만 5백원이 된 것처럼요.",
        "related_terms": ["물가", "기준금리", "소비자물가지수"]
    },
    "코스피": {
        "definition": "한국종합주가지수(KOSPI)는 우리나라 주식시장의 전체적인 흐름을 나타내는 지표입니다.",
        "analogy": "학급 전체의 평균 성적과 같아요. 개별 학생(기업)의 점수가 오르내리면 평균도 같이 변하죠.",
        "example": "2024년 10월 코스피는 2,600선을 돌파했습니다. 이는 대부분의 주요 기업 주가가 올랐다는 의미예요.",
        "related_terms": ["주식", "증권시장", "코스닥"]
    },
    "환율": {
        "definition": "두 나라 화폐의 교환 비율입니다. 원화와 달러를 교환할 때의 비율을 원달러 환율이라고 해요.",
        "analogy": "물건을 교환하는 비율과 같아요. 사과 2개와 귤 3개를 바꾸듯이, 1달러와 1,320원을 교환하는 거죠.",
        "example": "원달러 환율이 1,300원에서 1,400원으로 오르면, 미국 여행이나 해외 직구가 더 비싸집니다.",
        "related_terms": ["외환시장", "달러", "수출입"]
    }
}

# 샘플 뉴스 데이터
NEWS_ARTICLES = [
    {
        "id": 1,
        "title": "한국은행, 기준금리 3.50% 동결... 물가·성장 균형 고려",
        "source": "한국은행",
        "date": "2025.10.21 09:30",
        "preview": "한국은행 금융통화위원회가 기준금리를 연 3.50%로 동결했다...",
        "content": """한국은행 금융통화위원회가 21일 기준금리를 연 3.50%로 동결했다. 이는 시장 예상과 일치하는 결정이다.

금통위는 "최근 인플레이션 둔화 추세가 이어지고 있으나, 경기 회복 속도를 함께 고려해야 한다"며 동결 배경을 설명했다.

이창용 한국은행 총재는 "현재 금리 수준이 물가 안정과 성장을 모두 고려할 때 적절하다"고 밝혔다. 향후 통화정책 방향은 물가 흐름과 글로벌 경제 상황을 지켜보며 결정할 예정이다.

전문가들은 "금통위가 신중한 접근을 이어가고 있다"며 "당분간 기준금리 동결이 지속될 것"으로 전망했다.""",
        "tags": ["금리", "통화정책", "한국은행"],
        "terms": ["금융통화위원회", "기준금리", "인플레이션"]
    },
    {
        "id": 2,
        "title": "코스피 2,600선 회복... 외국인 매수세에 상승",
        "source": "한국거래소",
        "date": "2025.10.21 15:30",
        "preview": "국내 증시가 외국인 투자자들의 매수세에 힘입어 상승했다...",
        "content": """21일 코스피가 2,600선을 회복하며 1.8% 상승 마감했다. 외국인 투자자들이 반도체와 자동차 업종을 중심으로 순매수에 나서면서 지수가 상승했다.

증권가에서는 "미국 연준의 금리 인하 기대감과 중국 경제 부양책이 긍정적으로 작용했다"고 분석했다.

개별 종목으로는 삼성전자(+2.3%)와 현대차(+3.1%)가 강세를 보였으며, 코스닥 지수도 1.5% 상승했다.

애널리스트들은 "글로벌 경기 회복 기대감이 국내 증시에 긍정적"이라며 "다만 미중 무역 갈등 등 불확실성은 여전히 남아있다"고 조언했다.""",
        "tags": ["주식", "증시", "코스피"],
        "terms": ["코스피"]
    },
    {
        "id": 3,
        "title": "원달러 환율 1,320원대 안정화... 수출 기업 숨통",
        "source": "외환시장",
        "date": "2025.10.21 11:00",
        "preview": "원달러 환율이 1,320원대에서 안정세를 보이고 있다...",
        "content": """21일 서울외환시장에서 원달러 환율이 전 거래일보다 5원 하락한 1,323원에 거래를 마쳤다.

외환 전문가들은 "미국 달러 약세와 국내 수출 호조가 맞물리면서 원화 가치가 안정되고 있다"고 설명했다.

환율 하락은 수입 물가를 낮춰 인플레이션 압력을 완화하는 효과가 있다. 반면 수출 기업들의 가격 경쟁력에는 부담이 될 수 있다.

한국은행은 "환율 안정이 물가 관리에 도움이 된다"며 "다만 급격한 변동성은 경계하고 있다"고 밝혔다.""",
        "tags": ["환율", "외환", "무역"],
        "terms": ["환율", "인플레이션"]
    }
]

# ========================================
# HELPER FUNCTIONS
# ========================================
def get_term_definition(term):
    """용어 정의 가져오기"""
    return GLOSSARY.get(term)

def generate_term_explanation(term):
    """용어 설명 메시지 생성"""
    definition = get_term_definition(term)
    
    if definition:
        explanation = f"""## 📖 {term}

### ▸ 정의
{definition['definition']}

### ▸ 쉬운 비유
💡 {definition['analogy']}

### ▸ 실제 사례
📌 {definition['example']}

---

**💡 관련 용어**: {', '.join(definition['related_terms'])}

궁금한 관련 용어가 있다면 클릭하거나 질문해주세요!"""
        return explanation
    else:
        # 유사 용어 찾기
        all_terms = list(GLOSSARY.keys())
        similar = random.sample(all_terms, min(2, len(all_terms)))
        
        explanation = f"""## 😅 앗, '{term}'는 아직 사전에 없네요!

대신 비슷한 용어를 찾았어요:

"""
        for sim_term in similar:
            sim_def = GLOSSARY[sim_term]['definition'][:60] + "..."
            explanation += f"**• {sim_term}**: {sim_def}\n\n"
        
        explanation += f"\n'{term}'에 대해 더 알고 싶으시다면, 구체적으로 질문해주세요!"
        
        return explanation

def generate_ai_response(user_query):
    """AI 응답 생성"""
    query_lower = user_query.lower()
    
    # 용어 사전에 있는 단어인지 확인
    for term in GLOSSARY.keys():
        if term in user_query:
            return generate_term_explanation(term)
    
    # 특정 키워드에 대한 응답
    if "금리" in query_lower:
        return """좋은 질문이에요! 💡

**금리 인상**은 주로 물가가 너무 빠르게 오를 때 일어나요. 

쉽게 말하면, 경제에 돈이 너무 많이 돌아다니면 물건 값이 계속 오르겠죠? 이걸 막기 위해 중앙은행이 "돈의 가격(금리)"을 올려서 사람들이 돈을 덜 쓰게 만드는 거예요.

### 금리가 오르면:
- 💳 대출 이자가 높아져요 → 사람들이 대출을 덜 받아요
- 💰 예금 이자가 높아져요 → 사람들이 저축을 더 해요
- 🛍️ 소비가 줄어들어요 → 물가 상승이 느려져요

**관련 용어**: 기준금리, 인플레이션, 통화정책

더 자세히 알고 싶은 용어가 있으면 클릭해보세요!"""
    
    elif "주식" in query_lower:
        return """주식에 대해 궁금하시군요! 📈

**주식**은 회사의 일부를 소유하는 거예요. 주식을 사면 그 회사의 주인 중 한 명이 되는 거죠!

### 작동 원리
회사가 돈을 많이 벌면 → 주가가 올라가요 → 당신이 산 주식의 가치도 올라가요

반대로 회사가 어려워지면 주가가 내려가서 손해를 볼 수도 있어요.

### 초보자 팁
💡 처음에는 **코스피** 같은 지수형 상품부터 시작하는 게 좋아요. 한 번에 여러 회사에 분산 투자하는 효과가 있거든요!

**관련 용어**: 코스피, 증권시장, 배당

더 궁금한 점이 있으면 물어보세요!"""
    
    elif "뉴스" in query_lower or "요약" in query_lower:
        return """오늘의 주요 뉴스를 요약해드릴게요! 📰

### 1. 한국은행 금리 동결
- **기준금리** 3.50% 유지
- 물가와 성장 모두 고려한 결정

### 2. 코스피 2,600선 회복
- 외국인 매수세로 1.8% 상승
- 반도체·자동차 업종 강세

### 3. 원화 환율 안정
- 1,320원대에서 안정
- 수입 물가 하락 효과 기대

📌 더 자세한 내용은 위의 뉴스 기사를 클릭해서 확인해보세요!

궁금한 용어가 있다면 하이라이트된 단어를 클릭하거나 저에게 물어보세요! 😊"""
    
    else:
        return f""""{user_query}"에 대해 궁금하시군요! 🦉

금융 용어는 처음엔 어렵게 느껴질 수 있어요. 하지만 하나씩 알아가다 보면 뉴스가 훨씬 쉽게 이해될 거예요!

### 💡 이렇게 해보세요:
1. **뉴스 기사 읽기**: 위의 기사를 클릭해서 읽어보세요
2. **용어 클릭**: 노란색으로 표시된 용어를 클릭하면 설명이 나와요
3. **질문하기**: 저에게 자유롭게 질문해주세요

### 🎯 추천 질문:
- "금리가 오르면 어떻게 되나요?"
- "주식 투자 어떻게 시작하나요?"
- "인플레이션이 뭐예요?"

무엇이든 물어보세요! 💬"""

def highlight_terms_in_content(content, terms):
    """기사 내용에서 용어 하이라이트 (클릭 가능하게)"""
    highlighted = content
    for term in terms:
        if term in GLOSSARY:
            # 버튼 형태로 변경
            highlighted = highlighted.replace(
                term,
                f'<span class="highlighted-term" style="cursor:pointer;">{term}</span>'
            )
    return highlighted

# ========================================
# UI COMPONENTS
# ========================================
def render_header():
    """헤더 렌더링"""
    col1, col2, col3 = st.columns([2, 6, 1])
    
    with col1:
        st.markdown("### 🦉 금융친구")
    
    with col2:
        current_date = datetime.now().strftime("%Y년 %m월 %d일 %A")
        st.markdown(f"<p style='text-align:center; color: #8B7355; font-size: 16px; margin-top: 10px;'>{current_date}</p>", 
                    unsafe_allow_html=True)
    
    with col3:
        if st.button("⚙️", help="설정"):
            st.session_state.show_settings = not st.session_state.show_settings

def render_summary():
    """주요 뉴스 요약 렌더링"""
    st.markdown("""
    <div class='summary-box'>
        <h3 style='color: #5C4A3A; margin-bottom: 1rem;'>📰 오늘의 핵심 뉴스 요약</h3>
        <p style='font-size: 16px; line-height: 1.8; color: #5C4A3A;'>
            • 한국은행 기준금리 3.50% 동결 결정<br>
            • 국내 주식시장 반등, 코스피 2,600 돌파<br>
            • 원달러 환율 1,320원대 안정화
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_news_list():
    """뉴스 목록 렌더링 (카드 형태)"""
    st.markdown("### 📚 AI가 수집한 최신 금융 뉴스")
    st.markdown("")
    
    for article in NEWS_ARTICLES:
        # 뉴스 카드
        card_html = f"""
        <div class='news-card'>
            <p style='color: #8B7355; font-size: 14px; margin-bottom: 8px;'>
                🏦 {article['source']} · {article['date']}
            </p>
            <h4 style='color: #5C4A3A; margin-bottom: 8px;'>{article['title']}</h4>
            <p style='color: #8B7355; font-size: 14px;'>{article['preview']}</p>
            <div style='margin-top: 12px;'>
                {"".join([f"<span class='tag'>{tag}</span>" for tag in article['tags']])}
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        # 클릭 버튼 (카드 아래에 숨김)
        if st.button(f"기사 읽기 📖", key=f"read_{article['id']}", use_container_width=True):
            st.session_state.selected_article = article['id']
            # 챗봇 환영 메시지 추가
            if not st.session_state.chat_history:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"**'{article['title']}'** 기사를 선택하셨네요! 📰\n\n노란색으로 표시된 금융 용어를 클릭하면 자세한 설명을 볼 수 있어요. 궁금한 점이 있으면 언제든 물어보세요! 😊"
                })
            st.rerun()
        
        st.markdown("")

def render_article_view(article_id):
    """선택된 기사 상세 보기"""
    article = next((a for a in NEWS_ARTICLES if a['id'] == article_id), None)
    if not article:
        return
    
    st.markdown(f"""
    <div class='article-full'>
        <p style='color: #8B7355; font-size: 14px; margin-bottom: 8px;'>
            🏦 {article['source']} · {article['date']}
        </p>
        <h2 style='color: #5C4A3A; margin-bottom: 16px;'>{article['title']}</h2>
        <div style='margin-bottom: 16px;'>
            {"".join([f"<span class='tag'>{tag}</span>" for tag in article['tags']])}
        </div>
        <hr style='border: none; border-top: 1px solid #E8E4DF; margin: 16px 0;'>
    """, unsafe_allow_html=True)
    
    # 기사 내용을 문단별로 분리
    paragraphs = article['content'].split('\n\n')
    
    for para in paragraphs:
        if para.strip():
            # 각 문단에서 용어 찾기 및 버튼으로 만들기
            para_with_buttons = para
            for term in article['terms']:
                if term in para:
                    para_with_buttons = para_with_buttons.replace(
                        term,
                        f'<mark style="background: linear-gradient(180deg, transparent 60%, #FFE5B4 60%); font-weight: 600; padding: 2px 4px;">{term}</mark>'
                    )
            
            st.markdown(f"<p style='line-height: 1.8; color: #5C4A3A; margin-bottom: 16px;'>{para_with_buttons}</p>", unsafe_allow_html=True)
            
            # 문단에 포함된 용어에 대한 버튼 생성
            terms_in_para = [t for t in article['terms'] if t in para]
            if terms_in_para:
                cols = st.columns(len(terms_in_para))
                for idx, term in enumerate(terms_in_para):
                    with cols[idx]:
                        if st.button(f"📖 {term}", key=f"explain_{term}_{article['id']}_{para[:20]}"):
                            # 챗봇에 용어 설명 추가
                            explanation = generate_term_explanation(term)
                            st.session_state.chat_history.append({
                                "role": "user",
                                "content": f"'{term}' 설명해주세요"
                            })
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": explanation
                            })
                            st.rerun()
                st.markdown("")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 뒤로 가기 버튼
    if st.button("← 뉴스 목록으로 돌아가기", type="secondary"):
        st.session_state.selected_article = None
        st.session_state.chat_history = []
        st.rerun()

def render_chatbot():
    """챗봇 렌더링 (스크롤 기능 포함)"""
    st.markdown("### 💬 AlBuOng과 대화하기")
    
    # 채팅 컨테이너 (스크롤 가능)
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div class='chat-welcome'>
                <h3 style='color: #5C4A3A;'>🦉 안녕하세요!</h3>
                <p style='color: #8B7355; font-size: 16px;'>금융친구 AlBuOng이에요</p>
                <br>
                <p style='color: #5C4A3A;'><strong>💡 이렇게 물어보세요:</strong></p>
                <p style='color: #8B7355;'>• "금리가 오르면 어떻게 되나요?"</p>
                <p style='color: #8B7355;'>• "주식 용어 쉽게 설명해줘"</p>
                <p style='color: #8B7355;'>• "오늘 뉴스 요약해줘"</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 채팅 메시지 표시 (스크롤 가능한 영역)
            st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            for i, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant", avatar="🦉"):
                        st.markdown(message['content'])
            st.markdown("</div>", unsafe_allow_html=True)
    
    # 채팅 입력
    user_input = st.chat_input("궁금한 점을 물어보세요... 💬")
    
    if user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # AI 응답 생성
        response = generate_ai_response(user_input)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()

# ========================================
# MAIN APP
# ========================================
def main():
    render_header()
    
    # 기사가 선택되지 않았을 때: 뉴스 목록 + 챗봇
    if st.session_state.selected_article is None:
        col_main, col_chat = st.columns([7, 3])
        
        with col_main:
            render_summary()
            render_news_list()
        
        with col_chat:
            render_chatbot()
    
    # 기사가 선택되었을 때: 기사 본문 + 챗봇
    else:
        col_article, col_chat = st.columns([6, 4])
        
        with col_article:
            render_article_view(st.session_state.selected_article)
        
        with col_chat:
            render_chatbot()

if __name__ == "__main__":
    main()