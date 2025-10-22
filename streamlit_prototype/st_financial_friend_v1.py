import streamlit as st
from datetime import datetime
import random

# Page config
st.set_page_config(
    page_title="금융친구 | Financial Friend",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
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
    }
    
    .news-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 20px rgba(139, 115, 85, 0.15);
    }
    
    /* Highlighted term */
    .highlighted-term {
        background: linear-gradient(180deg, transparent 60%, #FFE5B4 60%);
        font-weight: 600;
        cursor: pointer;
        border-bottom: 2px dotted #D4AF37;
        padding: 2px 4px;
        transition: all 0.2s ease;
    }
    
    .highlighted-term:hover {
        background: #FFE5B4;
        border-bottom: 2px solid #D4AF37;
    }
    
    /* Glossary sidebar */
    .glossary-content {
        background: #FAF7F2;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #D4AF37;
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
    
    /* Chat welcome */
    .chat-welcome {
        background: #FFF9E6;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        border: 2px dashed #D4AF37;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    /* Term button */
    .term-button {
        background: #FFF9E6;
        border: 1px solid #D4AF37;
        color: #5C4A3A;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .term-button:hover {
        background: #D4AF37;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_term' not in st.session_state:
    st.session_state.selected_term = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

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
        "content": """한국은행 <span class="highlighted-term">금융통화위원회</span>가 21일 <span class="highlighted-term">기준금리</span>를 연 3.50%로 동결했다. 이는 시장 예상과 일치하는 결정이다.

금통위는 "최근 <span class="highlighted-term">인플레이션</span> 둔화 추세가 이어지고 있으나, 경기 회복 속도를 함께 고려해야 한다"며 동결 배경을 설명했다.

이창용 한국은행 총재는 "현재 금리 수준이 물가 안정과 성장을 모두 고려할 때 적절하다"고 밝혔다. 향후 통화정책 방향은 물가 흐름과 글로벌 경제 상황을 지켜보며 결정할 예정이다.""",
        "tags": ["금리", "통화정책", "한국은행"],
        "terms": ["금융통화위원회", "기준금리", "인플레이션"]
    },
    {
        "id": 2,
        "title": "코스피 2,600선 회복... 외국인 매수세에 상승",
        "source": "한국거래소",
        "date": "2025.10.21 15:30",
        "preview": "국내 증시가 외국인 투자자들의 매수세에 힘입어 상승했다...",
        "content": """21일 <span class="highlighted-term">코스피</span>가 2,600선을 회복하며 1.8% 상승 마감했다. 외국인 투자자들이 반도체와 자동차 업종을 중심으로 순매수에 나서면서 지수가 상승했다.

증권가에서는 "미국 연준의 금리 인하 기대감과 중국 경제 부양책이 긍정적으로 작용했다"고 분석했다.

개별 종목으로는 삼성전자(+2.3%)와 현대차(+3.1%)가 강세를 보였으며, 코스닥 지수도 1.5% 상승했다.""",
        "tags": ["주식", "증시", "코스피"],
        "terms": ["코스피"]
    },
    {
        "id": 3,
        "title": "원달러 환율 1,320원대 안정화... 수출 기업 숨통",
        "source": "외환시장",
        "date": "2025.10.21 11:00",
        "preview": "원달러 환율이 1,320원대에서 안정세를 보이고 있다...",
        "content": """21일 서울외환시장에서 원달러 <span class="highlighted-term">환율</span>이 전 거래일보다 5원 하락한 1,323원에 거래를 마쳤다.

외환 전문가들은 "미국 달러 약세와 국내 수출 호조가 맞물리면서 원화 가치가 안정되고 있다"고 설명했다.

환율 하락은 수입 물가를 낮춰 <span class="highlighted-term">인플레이션</span> 압력을 완화하는 효과가 있다. 반면 수출 기업들의 가격 경쟁력에는 부담이 될 수 있다.""",
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

def find_similar_terms(term):
    """유사 용어 찾기 (간단한 구현)"""
    all_terms = list(GLOSSARY.keys())
    # 실제로는 의미 기반 유사도를 사용하지만, 여기서는 랜덤으로 2개 선택
    similar = random.sample(all_terms, min(2, len(all_terms)))
    return [(t, GLOSSARY[t]['definition'][:50] + "...") for t in similar if t != term]

def generate_ai_response(user_query):
    """AI 응답 생성 (간단한 규칙 기반)"""
    query_lower = user_query.lower()
    
    # 특정 키워드에 대한 응답
    if "금리" in query_lower:
        return """좋은 질문이에요! 💡

**금리 인상**은 주로 물가가 너무 빠르게 오를 때 일어나요. 

쉽게 말하면, 경제에 돈이 너무 많이 돌아다니면 물건 값이 계속 오르겠죠? 이걸 막기 위해 중앙은행이 "돈의 가격(금리)"을 올려서 사람들이 돈을 덜 쓰게 만드는 거예요.

금리가 오르면:
- 대출 이자가 높아져요 → 사람들이 대출을 덜 받아요
- 예금 이자가 높아져요 → 사람들이 저축을 더 해요
- 소비가 줄어들어요 → 물가 상승이 느려져요

**관련 용어**: 기준금리, 인플레이션, 통화정책"""
    
    elif "주식" in query_lower:
        return """주식에 대해 궁금하시군요! 📈

**주식**은 회사의 일부를 소유하는 거예요. 주식을 사면 그 회사의 주인 중 한 명이 되는 거죠!

회사가 돈을 많이 벌면 → 주가가 올라가요 → 당신이 산 주식의 가치도 올라가요

반대로 회사가 어려워지면 주가가 내려가서 손해를 볼 수도 있어요.

**초보자 팁**: 처음에는 코스피 같은 지수형 상품부터 시작하는 게 좋아요. 한 번에 여러 회사에 분산 투자하는 효과가 있거든요!

**관련 용어**: 코스피, 증권시장, 배당"""
    
    elif "뉴스" in query_lower or "요약" in query_lower:
        return """오늘의 주요 뉴스를 요약해드릴게요! 📰

1. **한국은행 금리 동결** 
   - 기준금리 3.50% 유지
   - 물가와 성장 모두 고려한 결정

2. **코스피 2,600선 회복**
   - 외국인 매수세로 1.8% 상승
   - 반도체·자동차 업종 강세

3. **원화 환율 안정**
   - 1,320원대에서 안정
   - 수입 물가 하락 효과 기대

더 자세한 내용은 위의 뉴스 기사를 클릭해서 확인해보세요! 😊"""
    
    else:
        return f""""{user_query}"에 대해 궁금하시군요! 🦉

금융 용어는 처음엔 어렵게 느껴질 수 있어요. 하지만 하나씩 알아가다 보면 뉴스가 훨씬 쉽게 이해될 거예요!

위의 뉴스 기사에서 노란색으로 표시된 용어를 클릭해보세요. 쉬운 설명을 볼 수 있어요.

또는 이렇게 물어보세요:
- "금리가 오르면 어떻게 되나요?"
- "주식 투자 어떻게 시작하나요?"
- "오늘 뉴스 요약해줘"

무엇이든 물어보세요! 💬"""

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
            • 미국 연준 금리 0.25%p 인상 결정<br>
            • 국내 주식시장 반등, 코스피 2,600 돌파<br>
            • 원달러 환율 1,320원대 안정화
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_news_feed():
    """뉴스 피드 렌더링"""
    st.markdown("### 📚 AI가 수집한 최신 금융 뉴스")
    st.markdown("")
    
    for article in NEWS_ARTICLES:
        with st.expander(f"📄 {article['title']}", expanded=False):
            # 헤더 정보
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"🏦 {article['source']} · {article['date']}")
            
            # 태그
            tags_html = "".join([f"<span class='tag'>{tag}</span>" for tag in article['tags']])
            st.markdown(tags_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 기사 내용 (하이라이트 포함)
            st.markdown(article['content'], unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown("**💡 용어 설명 보기:**")
            
            # 용어 버튼들
            cols = st.columns(len(article['terms']))
            for idx, term in enumerate(article['terms']):
                with cols[idx]:
                    if st.button(f"📖 {term}", key=f"term_{article['id']}_{term}"):
                        st.session_state.selected_term = term
                        st.rerun()

def render_glossary_sidebar():
    """용어 사전 사이드바 렌더링"""
    if st.session_state.selected_term:
        with st.sidebar:
            st.markdown("## 🦉 AlBuOng이 설명해드려요")
            st.markdown("---")
            
            term = st.session_state.selected_term
            definition = get_term_definition(term)
            
            if definition:
                st.markdown(f"### 📖 {term}")
                st.markdown("")
                
                st.markdown("**▸ 정의**")
                st.info(definition['definition'])
                
                st.markdown("**▸ 쉬운 비유**")
                st.success(definition['analogy'])
                
                st.markdown("**▸ 실제 사례**")
                st.warning(definition['example'])
                
                st.markdown("---")
                st.markdown("**💡 관련 용어:**")
                
                for related in definition['related_terms']:
                    if st.button(f"• {related}", key=f"related_{related}"):
                        st.session_state.selected_term = related
                        st.rerun()
            else:
                st.markdown("### 😅 앗, 이 단어는 아직 사전에 없네요!")
                st.markdown("대신 비슷한 용어를 찾았어요:")
                st.markdown("")
                
                similar = find_similar_terms(term)
                for sim_term, sim_def in similar:
                    if st.button(f"**{sim_term}**\n\n{sim_def}", key=f"similar_{sim_term}"):
                        st.session_state.selected_term = sim_term
                        st.rerun()
                
                st.markdown("")
                if st.button("💬 AlBuOng에게 직접 물어보기", type="primary", use_container_width=True):
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": f"{term}에 대해 설명해주세요"
                    })
                    # AI 응답 생성
                    response = generate_ai_response(f"{term}에 대해 설명해주세요")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.session_state.selected_term = None
                    st.rerun()
            
            st.markdown("")
            if st.button("❌ 닫기", use_container_width=True):
                st.session_state.selected_term = None
                st.rerun()

def render_chatbot():
    """챗봇 렌더링"""
    st.markdown("### 💬 AlBuOng과 대화하기")
    
    # 채팅 히스토리
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
        for message in st.session_state.chat_history[-10:]:  # 최근 10개만 표시
            if message['role'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message['content'])
            else:
                with st.chat_message("assistant", avatar="🦉"):
                    st.markdown(message['content'])
    
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
    
    # 메인 레이아웃
    col_main, col_chat = st.columns([7, 3])
    
    with col_main:
        render_summary()
        render_news_feed()
    
    with col_chat:
        render_chatbot()
    
    # 용어 사전 사이드바
    render_glossary_sidebar()
    
    # 설정 모달 (선택사항)
    if st.session_state.show_settings:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### ⚙️ 설정")
            font_size = st.select_slider("글자 크기", options=["작게", "보통", "크게"], value="보통")
            theme = st.selectbox("테마", ["밝은 모드", "어두운 모드"])
            st.info("설정 기능은 프로토타입에서 곧 지원될 예정입니다.")

if __name__ == "__main__":
    main()