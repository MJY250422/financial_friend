import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(layout="wide", page_title="금융 뉴스 도우미")

# OpenAI 클라이언트 초기화 (MVP 단계: Mock 모드)
USE_OPENAI = False  # API 연결 시 True로 변경

@st.cache_resource
def get_openai_client():
    if USE_OPENAI:
        api_key = st.secrets.get("OPENAI_API_KEY", "your-api-key-here")
        return OpenAI(api_key=api_key)
    return None

client = get_openai_client()

# 세션 스테이트 초기화
if 'news_articles' not in st.session_state:
    st.session_state.news_articles = []
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'financial_terms' not in st.session_state:
    # RAG를 위한 금융 용어 사전 (예시)
    st.session_state.financial_terms = {
        "양적완화": {
            "정의": "중앙은행이 시중에 통화를 공급하기 위해 국채 등을 매입하는 정책",
            "설명": "경기 부양을 위해 중앙은행이 돈을 풀어 시장 유동성을 높이는 방법입니다.",
            "비유": "마른 땅에 물을 뿌려주는 것처럼, 경제에 돈이라는 물을 공급하는 것입니다."
        },
        "기준금리": {
            "정의": "중앙은행이 시중은행에 돈을 빌려줄 때 적용하는 기준이 되는 금리",
            "설명": "모든 금리의 기준이 되며, 기준금리가 오르면 대출이자도 함께 오릅니다.",
            "비유": "물가의 온도조절기와 같습니다. 경제가 과열되면 올리고, 침체되면 내립니다."
        },
        "배당": {
            "정의": "기업이 벌어들인 이익 중 일부를 주주들에게 나눠주는 것",
            "설명": "주식을 보유한 주주에게 기업의 이익을 분배하는 방식입니다.",
            "비유": "함께 식당을 운영하는 동업자들이 매출 중 일부를 나눠갖는 것과 같습니다."
        },
        "PER": {
            "정의": "주가수익비율. 주가를 주당순이익으로 나눈 값",
            "설명": "주식이 1년 치 이익의 몇 배에 거래되는지를 나타냅니다. 낮을수록 저평가된 것으로 볼 수 있습니다.",
            "비유": "1년에 100만원 버는 가게를 몇 년 치 수익을 주고 사는지를 나타냅니다."
        },
        "환율": {
            "정의": "서로 다른 두 나라 화폐의 교환 비율",
            "설명": "원화를 달러로, 달러를 원화로 바꿀 때 적용되는 비율입니다.",
            "비유": "해외 쇼핑몰에서 물건을 살 때 적용되는 환전 비율입니다."
        }
    }

# 뉴스 수집 Agent (시뮬레이션)
def collect_news():
    """실제로는 OpenAI API로 뉴스를 수집하지만, 여기서는 예시 데이터 사용"""
    sample_news = [
        {
            "id": 1,
            "title": "한국은행, 기준금리 동결 결정",
            "summary": "한국은행이 물가 안정을 위해 기준금리를 현 수준으로 유지하기로 했습니다.",
            "content": "한국은행 금융통화위원회는 21일 회의를 열고 기준금리를 연 3.50%로 동결했습니다. 이는 최근 물가 상승세가 진정되고 있으나 여전히 불확실성이 크다는 판단에 따른 것입니다. 시장에서는 양적완화 정책 전환 가능성도 제기되고 있습니다.",
            "date": "2025-10-21"
        },
        {
            "id": 2,
            "title": "삼성전자, 분기 배당 20% 증액 발표",
            "summary": "삼성전자가 주주환원 정책 강화 일환으로 배당금을 대폭 늘렸습니다.",
            "content": "삼성전자는 이번 분기 배당을 주당 500원으로 결정하며 전년 동기 대비 20% 증액했습니다. PER이 하락하며 주가가 저평가됐다는 시장 분석에 따라 주주환원을 강화하겠다는 의지를 보였습니다.",
            "date": "2025-10-20"
        },
        {
            "id": 3,
            "title": "원달러 환율, 1,300원 돌파",
            "summary": "미국 금리 인상 영향으로 원화 가치가 약세를 보이고 있습니다.",
            "content": "21일 서울 외환시장에서 원달러 환율이 1,300원을 넘어섰습니다. 미국의 기준금리 인상 기조가 지속되면서 달러 강세가 이어지고 있습니다. 수출 기업들에게는 호재이지만 수입 물가 상승 우려도 커지고 있습니다.",
            "date": "2025-10-21"
        }
    ]
    return sample_news

# 뉴스 요약 생성 (GPT-4o-mini 사용)
def generate_summary(articles):
    """여러 뉴스를 종합한 요약 생성"""
    if USE_OPENAI and client:
        try:
            news_texts = "\n\n".join([f"제목: {a['title']}\n내용: {a['content']}" for a in articles])
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 금융 뉴스를 간결하게 요약하는 전문가입니다."},
                    {"role": "user", "content": f"다음 금융 뉴스들을 3-4문장으로 종합 요약해주세요:\n\n{news_texts}"}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content
        except:
            pass
    
    # Mock 응답 (API 미연결 시)
    return "오늘 금융 시장은 한국은행의 기준금리 동결 결정과 삼성전자의 배당 증액 발표가 주목받았습니다. 원달러 환율이 1,300원을 돌파하며 외환시장의 변동성도 커지고 있습니다. 전문가들은 향후 통화정책 방향과 환율 추이를 주시할 필요가 있다고 조언합니다."

# 용어 하이라이트 처리
def highlight_terms(text, terms_dict):
    """텍스트에서 금융 용어를 하이라이트"""
    highlighted = text
    for term in terms_dict.keys():
        # HTML로 하이라이트 처리 - 클릭 가능하도록
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(
            f'<mark class="clickable-term" data-term="{term}" style="background-color: #FFEB3B; cursor: pointer; padding: 2px 4px; border-radius: 3px;">{term}</mark>',
            highlighted
        )
    return highlighted

# RAG 기반 용어 설명
def explain_term(term, chat_history):
    """RAG를 사용하여 용어 설명"""
    if term in st.session_state.financial_terms:
        term_info = st.session_state.financial_terms[term]
        context = f"""
        용어: {term}
        정의: {term_info['정의']}
        설명: {term_info['설명']}
        비유: {term_info['비유']}
        """
        
        if USE_OPENAI and client:
            try:
                messages = [
                    {"role": "system", "content": "당신은 금융 용어를 쉽게 설명하는 친절한 도우미입니다. 주어진 정보를 바탕으로 초보자도 이해할 수 있게 설명해주세요."}
                ]
                
                # 채팅 히스토리 추가
                for msg in chat_history[-4:]:  # 최근 4개만
                    messages.append(msg)
                
                messages.append({
                    "role": "user", 
                    "content": f"다음 금융 용어를 설명해주세요:\n{context}"
                })
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=300
                )
                return response.choices[0].message.content
            except:
                pass
        
        # Mock 응답 (API 미연결 시)
        return f"""**{term}** 에 대해 설명해드릴게요! 🎯

📖 **정의**
{term_info['정의']}

💡 **쉬운 설명**
{term_info['설명']}

🌟 **비유로 이해하기**
{term_info['비유']}

더 궁금한 점이 있으시면 언제든지 물어보세요!"""
    else:
        return f"'{term}'에 대한 정보가 금융 사전에 없습니다. 다른 용어를 선택해주세요."

# CSS 스타일
st.markdown("""
<style>
    .news-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .news-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: #1f77b4;
    }
    .summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .article-content {
        background: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        line-height: 1.8;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .user-message {
        background: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background: #f5f5f5;
    }
    .clickable-term {
        transition: all 0.2s;
    }
    .clickable-term:hover {
        background-color: #FDD835 !important;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# 메인 레이아웃
col1, col2 = st.columns([2, 1])

# 왼쪽: 컨텐츠 영역
with col1:
    st.title("📰 금융 뉴스 도우미")
    
    # 뉴스 수집
    if not st.session_state.news_articles:
        with st.spinner("최신 뉴스를 수집하는 중..."):
            st.session_state.news_articles = collect_news()
    
    # 선택된 기사가 없을 때: 요약 + 뉴스 리스트
    if st.session_state.selected_article is None:
        # 종합 요약
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.subheader("📊 오늘의 금융 뉴스 요약")
        summary = generate_summary(st.session_state.news_articles)
        st.write(summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 뉴스 목록
        st.subheader("📋 최신 뉴스")
        for article in st.session_state.news_articles:
            if st.button(
                f"**{article['title']}**\n{article['summary']}", 
                key=f"news_{article['id']}",
                use_container_width=True
            ):
                st.session_state.selected_article = article
                st.rerun()
    
    # 선택된 기사가 있을 때: 기사 내용 표시
    else:
        article = st.session_state.selected_article
        
        if st.button("← 뉴스 목록으로 돌아가기"):
            st.session_state.selected_article = None
            st.rerun()
        
        st.markdown("---")
        st.header(article['title'])
        st.caption(f"📅 {article['date']}")
        
        # 용어 하이라이트 처리된 본문
        st.markdown('<div class="article-content">', unsafe_allow_html=True)
        highlighted_content = highlight_terms(article['content'], st.session_state.financial_terms)
        st.markdown(highlighted_content, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info("💡 아래 버튼에서 용어를 선택하면 챗봇이 쉽게 설명해드립니다!")
        
        # 용어 선택 버튼 - 큰 버튼으로 개선
        st.subheader("🔍 용어 설명 요청")
        terms_in_article = [term for term in st.session_state.financial_terms.keys() if term in article['content']]
        
        # 한 줄에 3개씩 배치
        for i in range(0, len(terms_in_article), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(terms_in_article):
                    term = terms_in_article[i + j]
                    with col:
                        if st.button(
                            f"📌 {term}", 
                            key=f"term_btn_{term}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            # 채팅에 용어 설명 추가
                            user_msg = {"role": "user", "content": f"'{term}' 용어를 설명해주세요"}
                            st.session_state.chat_history.append(user_msg)
                            
                            explanation = explain_term(term, st.session_state.chat_history)
                            bot_msg = {"role": "assistant", "content": explanation}
                            st.session_state.chat_history.append(bot_msg)
                            st.rerun()
        
        # 하이라이트 클릭 감지 제거 (Streamlit 한계)
        st.caption("💡 Tip: 위 버튼을 클릭하면 오른쪽 챗봇에서 상세한 설명을 확인할 수 있습니다!")

# 오른쪽: 챗봇 영역
with col2:
    st.markdown("### 💬 금융 용어 도우미")
    st.markdown("---")
    
    # 채팅 히스토리 표시
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
    
    # 사용자 입력
    user_input = st.chat_input("궁금한 금융 용어를 입력하세요...")
    
    if user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 용어 추출 (간단한 키워드 매칭)
        found_term = None
        for term in st.session_state.financial_terms.keys():
            if term in user_input:
                found_term = term
                break
        
        if found_term:
            explanation = explain_term(found_term, st.session_state.chat_history)
        else:
            # 일반 대화
            if USE_OPENAI and client:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "당신은 금융 용어를 쉽게 설명하는 도우미입니다."}
                        ] + st.session_state.chat_history,
                        max_tokens=300
                    )
                    explanation = response.choices[0].message.content
                except:
                    explanation = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
            else:
                # Mock 응답
                explanation = f"'{user_input}'에 대해 궁금하시군요! MVP 개발 단계에서는 금융 사전에 등록된 용어({', '.join(st.session_state.financial_terms.keys())})만 설명이 가능합니다. 해당 용어를 입력하시거나 기사에서 하이라이트된 용어를 선택해주세요! 😊"
        
        st.session_state.chat_history.append({"role": "assistant", "content": explanation})
        st.rerun()
    
    # 채팅 초기화 버튼
    if st.button("🔄 대화 초기화"):
        st.session_state.chat_history = []
        st.rerun()

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    st.markdown("---")
    
    st.subheader("📚 금융 용어 사전")
    st.write(f"등록된 용어: {len(st.session_state.financial_terms)}개")
    
    with st.expander("용어 목록 보기"):
        for term in st.session_state.financial_terms.keys():
            st.write(f"• {term}")
    
    st.markdown("---")
    st.info("""
    **사용 방법:**
    1. 최신 뉴스 목록에서 관심있는 기사를 선택하세요
    2. 기사 내 노란색 용어를 클릭하거나 챗봇에 질문하세요
    3. RAG 기반으로 쉬운 설명을 받아보세요
    """)
    
    st.markdown("---")
    st.caption("💡 OpenAI GPT-4o-mini 사용")