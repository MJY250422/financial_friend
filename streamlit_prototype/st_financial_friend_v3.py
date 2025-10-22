import streamlit as st
from datetime import datetime
import random
import urllib.parse

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="금융친구 | Financial Friend",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# Custom CSS
# -------------------------
st.markdown("""
<style>
/* Layout */
body { background-color: #FAF7F2; }

/* Header */
.main-header {
    background: #FFFFFF; padding: 1.2rem; border-bottom: 3px solid #D4AF37;
    border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(139,115,85,0.06);
}

/* Summary */
.summary-box {
    background: linear-gradient(135deg,#FFF9E6 0%,#FFE5B4 100%);
    padding: 1.6rem; border-radius: 12px; margin-bottom: 1.5rem;
    border-left: 5px solid #D4AF37;
}

/* News card (anchor wraps whole card) */
.news-card {
    background: white; padding: 1rem; border-radius: 12px; border: 1px solid #E8E4DF;
    margin-bottom: 1rem; transition: all .22s ease; color: inherit; text-decoration: none;
    display: block;
}
.news-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(139,115,85,0.12); border-color: #D4AF37; }

/* highlighted-term (underlined clickable term) */
.highlighted-term {
    text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 3px;
    text-decoration-color: #D4AF37; font-weight: 600; color: #5C4A3A; cursor: pointer;
}
.highlighted-term:hover { color: #D4AF37; }

/* tags */
.tag { background: #E8E4DF; padding: 4px 10px; border-radius: 14px; font-size: 12px; margin-right: 6px; color: #5C4A3A; }

/* article container */
.article-full { background: white; padding: 1.4rem; border-radius: 12px; border: 1px solid #E8E4DF; max-height: 80vh; overflow-y: auto; }

/* chat container with scroll */
.chat-container {
    height: 68vh; overflow-y: auto; padding: 1rem; background: white; border-radius: 12px; border: 1px solid #E8E4DF;
}
.chat-user { text-align: right; margin: 8px 0; }
.chat-user .bubble { display: inline-block; background: #E8E4DF; padding: 10px 12px; border-radius: 12px; color: #2b2b2b; max-width: 85%; }
.chat-assistant { text-align: left; margin: 8px 0; }
.chat-assistant .bubble { display: inline-block; background: #FFF9E6; padding: 10px 12px; border-radius: 12px; color: #5C4A3A; border: 1px solid #F1E6C9; max-width: 85%; }

/* hide streamlit menu/footer */
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
/* scrollbar */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #FAF7F2; }
::-webkit-scrollbar-thumb { background: #D4AF37; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Data (Glossary + News)
# -------------------------
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
        "analogy": "물건을 교환하는 비율과 같아요. 사과 2개와 귤 3개를 바꾸듯이, 1달러와 1,320원을 바꾸는 거죠.",
        "example": "원달러 환율이 1,300원에서 1,400원으로 오르면, 미국 여행이나 해외 직구가 더 비싸집니다.",
        "related_terms": ["외환시장", "달러", "수출입"]
    }
}

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

# -------------------------
# Helpers
# -------------------------
def get_term_definition(term):
    return GLOSSARY.get(term)

def generate_term_explanation(term):
    d = get_term_definition(term)
    if d:
        return f"**{term}**\n\n정의: {d['definition']}\n\n비유: {d['analogy']}\n\n사례: {d['example']}\n\n관련 용어: {', '.join(d['related_terms'])}"
    else:
        # 추천 유사어
        all_terms = list(GLOSSARY.keys())
        similar = random.sample(all_terms, min(2, len(all_terms)))
        s = "앗, 해당 단어는 아직 사전에 없습니다.\n\n대신 유사한 용어를 추천합니다:\n\n"
        for t in similar:
            s += f"- **{t}**: {GLOSSARY[t]['definition'][:80]}...\n"
        return s

def render_header():
    col1, col2, col3 = st.columns([2,6,1])
    with col1:
        st.markdown("<div class='main-header'><h3 style='margin:0'>🦉 금융친구</h3></div>", unsafe_allow_html=True)
    with col2:
        current_date = datetime.now().strftime("%Y년 %m월 %d일 %A")
        st.markdown(f"<p style='text-align:center; color:#8B7355; margin-top:8px'>{current_date}</p>", unsafe_allow_html=True)
    with col3:
        if st.button("⚙️"):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)

def render_summary():
    st.markdown(f"""
    <div class='summary-box'>
        <h4 style='color:#5C4A3A; margin:0'>📰 오늘의 핵심 뉴스 요약</h4>
        <p style='color:#5C4A3A; margin-top:8px'>
            • 한국은행 기준금리 3.50% 동결 결정<br>
            • 국내 주식시장 반등, 코스피 2,600 돌파<br>
            • 원달러 환율 1,320원대 안정화
        </p>
    </div>
    """, unsafe_allow_html=True)

def article_card_html(article):
    # 전체 카드를 anchor로 감싸서 클릭하면 ?article_id=ID 로 이동
    card = f"""
    <a class='news-card' href='?article_id={article['id']}' style='text-decoration:none; color:inherit;'>
        <p style='color:#8B7355; font-size:13px; margin:0 0 8px 0'>🏦 {article['source']} · {article['date']}</p>
        <h4 style='color:#5C4A3A; margin:6px 0'>{article['title']}</h4>
        <p style='color:#8B7355; margin:6px 0'>{article['preview']}</p>
        <div style='margin-top:8px'>""" + "".join([f"<span class='tag'>{t}</span>" for t in article['tags']]) + "</div></a>"
    return card

def render_news_list():
    st.markdown("### 📚 AI가 수집한 최신 금융 뉴스")
    st.markdown("")
    for article in NEWS_ARTICLES:
        st.markdown(article_card_html(article), unsafe_allow_html=True)

def render_article_view(article_id):
    article = next((a for a in NEWS_ARTICLES if a['id'] == article_id), None)
    if not article:
        st.warning("해당 기사를 찾을 수 없습니다.")
        return

    # Article header
    st.markdown(f"""
    <div class='article-full'>
        <p style='color:#8B7355; font-size:13px; margin:0 0 8px 0'>🏦 {article['source']} · {article['date']}</p>
        <h2 style='color:#5C4A3A; margin-top:6px'>{article['title']}</h2>
        <div style='margin-bottom:12px'>""" + "".join([f"<span class='tag'>{t}</span>" for t in article['tags']]) + "</div><hr style='border:none; border-top:1px solid #E8E4DF; margin:12px 0;'>", unsafe_allow_html=True)

    # Render paragraphs, replacing terms with underlined links that include term and article_id as query params
    paragraphs = article['content'].split('\n\n')
    for para in paragraphs:
        if not para.strip():
            continue
        para_html = st.markdown  # just to keep pattern
        enhanced = para
        for term in article['terms']:
            # replace plain term with link-encoded term
            encoded = urllib.parse.quote(term)
            enhanced = enhanced.replace(term, f"<a class='highlighted-term' href='?article_id={article_id}&term={encoded}' style='text-decoration:none'>{term}</a>")
        st.markdown(f"<p style='line-height:1.8; color:#5C4A3A; margin-bottom:12px'>{enhanced}</p>", unsafe_allow_html=True)

    # Back link
    st.markdown("<div style='margin-top:12px'><a href='?' style='text-decoration:none'>&larr; 뉴스 목록으로 돌아가기</a></div>", unsafe_allow_html=True)

# -------------------------
# Initialize session state
# -------------------------
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'chat_history' not in st.session_state:
    # start with a friendly assistant message
    st.session_state.chat_history = [
        {"role": "assistant", "content": "안녕하세요! 금융친구 AlBuOng이에요. 궁금한 용어를 클릭하거나 질문해보세요 😊"}
    ]
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

# -------------------------
# Query params handling (article click / term click)
# -------------------------
params = st.experimental_get_query_params()
# If article_id passed in URL, set session_state.selected_article
if 'article_id' in params and params['article_id']:
    try:
        aid = int(params['article_id'][0])
        st.session_state.selected_article = aid
    except:
        st.session_state.selected_article = None

# If term clicked via URL param, append explanation to chat_history
if 'term' in params and params['term']:
    term_raw = params['term'][0]
    # url-unquote
    try:
        term_clicked = urllib.parse.unquote(term_raw)
    except:
        term_clicked = term_raw
    explanation = generate_term_explanation(term_clicked)
    # add as user question + assistant answer to chat history for context
    st.session_state.chat_history.append({"role":"user", "content": f"'{term_clicked}' 설명해주세요"})
    st.session_state.chat_history.append({"role":"assistant", "content": explanation})
    # clear query params to avoid duplicate processing on rerun
    st.experimental_set_query_params()
    # ensure selected_article remains (if any)
    # no further action needed

# -------------------------
# Header + layout
# -------------------------
render_header()

# Layout: when no article selected => show list + chat; when selected => show article + chat
if st.session_state.selected_article is None:
    col_main, col_chat = st.columns([7, 3])
    with col_main:
        render_summary()
        render_news_list()
    with col_chat:
        # Chat column title
        st.markdown("### 💬 AlBuOng과 대화하기")
        # Chat history container (scrollable)
        chat_html = "<div class='chat-container'>"
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                chat_html += f"<div class='chat-user'><div class='bubble'>{msg['content']}</div></div>"
            else:
                chat_html += f"<div class='chat-assistant'><div class='bubble'>{msg['content']}</div></div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Chat input (use st.chat_input for consistent UX)
        user_input = st.chat_input("궁금한 점을 물어보세요... 💬")
        if user_input:
            st.session_state.chat_history.append({"role":"user","content": user_input})
            # generate simple response (rule-based as in original)
            resp = generate_term_explanation(user_input) if user_input in GLOSSARY else None
            if not resp:
                resp = None
                # fallback to previous generate_ai_response-like logic (simple rules)
                q = user_input.lower()
                if "금리" in q:
                    resp = """좋은 질문이에요! 💡

**금리 인상**은 주로 물가가 너무 빠르게 오를 때 일어나요. 

쉽게 말하면, 경제에 돈이 너무 많이 돌아다니면 물건 값이 계속 오르겠죠? 이걸 막기 위해 중앙은행이 "돈의 가격(금리)"을 올려서 사람들이 돈을 덜 쓰게 만드는 거예요.

### 금리가 오르면:
- 💳 대출 이자가 높아져요 → 사람들이 대출을 덜 받아요
- 💰 예금 이자가 높아져요 → 사람들이 저축을 더 해요
- 🛍️ 소비가 줄어들어요 → 물가 상승이 느려져요

**관련 용어**: 기준금리, 인플레이션, 통화정책"""
                elif "주식" in q:
                    resp = """주식에 대해 궁금하시군요! 📈

**주식**은 회사의 일부를 소유하는 거예요. 주식을 사면 그 회사의 주인 중 한 명이 되는 거죠!"""
                elif "뉴스" in q or "요약" in q:
                    resp = """오늘 주요 뉴스 요약입니다: 기준금리 동결 / 코스피 상승 / 환율 안정 등..."""
                else:
                    resp = f"'{user_input}'에 대해 궁금하시군요! 자세히 질문해 주세요."
            st.session_state.chat_history.append({"role":"assistant","content": resp})
            # rerun to show appended messages and maintain scroll
            st.experimental_rerun()
else:
    # Article is selected
    col_article, col_chat = st.columns([6,4])
    with col_article:
        render_article_view(st.session_state.selected_article)
    with col_chat:
        st.markdown("### 💬 AlBuOng과 대화하기")
        chat_html = "<div class='chat-container'>"
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                chat_html += f"<div class='chat-user'><div class='bubble'>{msg['content']}</div></div>"
            else:
                chat_html += f"<div class='chat-assistant'><div class='bubble'>{msg['content']}</div></div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("궁금한 점을 물어보세요... 💬")
        if user_input:
            st.session_state.chat_history.append({"role":"user","content": user_input})
            # generate AI-ish response (reuse generate_term_explanation when exact term)
            resp = None
            for term in GLOSSARY.keys():
                if term in user_input:
                    resp = generate_term_explanation(term)
                    break
            if not resp:
                q = user_input.lower()
                if "금리" in q:
                    resp = """좋은 질문이에요! 💡
금리가 오르면 대출이자 상승, 소비 감소 등..."""
                else:
                    resp = "좋은 질문이에요! 조금 더 구체적으로 말씀해주시면 더 잘 도와드릴게요."
            st.session_state.chat_history.append({"role":"assistant","content": resp})
            st.experimental_rerun()
