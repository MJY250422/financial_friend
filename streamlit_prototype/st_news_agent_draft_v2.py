"""
뉴스 에이전트 프로토타입 (Streamlit)
- 배치형: RSS 수집 → 중복 제거 → 요약 → DB 적재
- 온디맨드형: 실시간 질의 → 문서 검색 → LLM 응답
"""

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict, Tuple

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

DEFAULT_RSS_FEEDS = [
    "https://www.mk.co.kr/rss/30100041/",  # 매일경제 경제
    "https://www.hankyung.com/feed/economy",  # 한국경제
    "https://www.sedaily.com/RSS/S1N1.xml"  # 서울경제
]

KOREAN_CHAR_TO_TOKEN_RATIO = 2.0  # 한글 1,000자 ≈ 500 tokens
AVG_ARTICLE_LENGTH = 3000  # 평균 기사 길이 (자)
BATCH_INTERVAL_MINUTES = 30

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_simhash(text: str, bit_length: int = 64) -> int:
    """
    SimHash 알고리즘으로 텍스트 유사도 해시 생성
    중복 기사 탐지용
    """
    tokens = re.findall(r'\w+', text.lower())
    hash_vec = [0] * bit_length
    
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(bit_length):
            if h & (1 << i):
                hash_vec[i] += 1
            else:
                hash_vec[i] -= 1
    
    fingerprint = 0
    for i in range(bit_length):
        if hash_vec[i] > 0:
            fingerprint |= (1 << i)
    
    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """두 SimHash 간 해밍 거리 계산"""
    xor = hash1 ^ hash2
    distance = 0
    while xor:
        distance += 1
        xor &= xor - 1
    return distance


def estimate_tokens(text: str) -> int:
    """한국어 텍스트의 토큰 수 추정"""
    char_count = len(text)
    return int(char_count / KOREAN_CHAR_TO_TOKEN_RATIO)


def normalize_url(url: str) -> str:
    """URL 정규화 (파라미터 제거, 소문자화)"""
    url = url.lower().strip()
    url = re.sub(r'\?.*$', '', url)  # 쿼리 파라미터 제거
    url = re.sub(r'#.*$', '', url)  # 앵커 제거
    return url


# ============================================================================
# MOCK DATA GENERATORS (실제 환경에서는 RSS/DB/LLM 연동)
# ============================================================================

def fetch_rss_articles(feed_urls: List[str], limit_per_feed: int = 10) -> List[Dict]:
    """
    RSS 피드에서 기사 목록 수집
    실제 구현: feedparser.parse() 사용
    """
    mock_articles = []
    sources = ["매일경제", "한국경제", "서울경제"]
    
    for i, feed_url in enumerate(feed_urls[:3]):
        for j in range(limit_per_feed):
            article = {
                'source': sources[i],
                'url': f"https://example.com/article/{i}_{j}",
                'title': f"[{sources[i]}] {['금리 인상', '반도체 수출 급증', '부동산 시장 동향'][i]} 관련 기사 #{j+1}",
                'published_at': datetime.now() - timedelta(hours=i*2 + j),
                'raw_content': f"이 기사는 {sources[i]}에서 발행한 {'경제' if i==0 else '금융'} 관련 뉴스입니다. " * 50
            }
            mock_articles.append(article)
    
    return mock_articles


def extract_article_body(url: str) -> str:
    """
    URL에서 본문 추출
    실제 구현: readability-lxml 또는 newspaper3k 사용
    """
    # Mock implementation
    return f"본문 내용입니다. 이 기사는 경제 동향에 대해 설명합니다. " * 30


def summarize_with_llm(content: str, source: str) -> Tuple[str, str]:
    """
    LLM을 통한 기사 요약
    실제 구현: OpenAI API 또는 Anthropic Claude API
    
    Returns:
        (summary, top_facts) 튜플
    """
    # Mock LLM response
    summary = f"이 기사는 최근 경제 동향을 다루며, 주요 지표의 변화와 전망을 분석합니다. " \
              f"전문가들은 향후 3개월간 완만한 성장세를 예상하고 있습니다. " \
              f"[출처: {source}]"
    
    top_facts = "• GDP 성장률 2.3% 기록\n• 수출 전년 대비 15% 증가\n• 실업률 3.1%로 소폭 하락"
    
    return summary, top_facts


def upsert_articles_to_db(articles: List[Dict]) -> int:
    """
    기사 데이터를 DB에 UPSERT
    실제 구현: SQLite, PostgreSQL 등 사용
    
    Returns:
        삽입/업데이트된 레코드 수
    """
    # Mock DB operation
    if 'db_articles' not in st.session_state:
        st.session_state.db_articles = []
    
    inserted = 0
    for article in articles:
        # 중복 체크 (URL 기준)
        existing = next((a for a in st.session_state.db_articles 
                        if a['url'] == article['url']), None)
        if not existing:
            st.session_state.db_articles.append(article)
            inserted += 1
    
    return inserted


def log_batch_run(run_id: str, discovered: int, inserted: int, start_time: datetime):
    """배치 실행 로그 기록"""
    if 'fetch_logs' not in st.session_state:
        st.session_state.fetch_logs = []
    
    log_entry = {
        'run_id': run_id,
        'started_at': start_time,
        'finished_at': datetime.now(),
        'discovered_count': discovered,
        'inserted_count': inserted
    }
    st.session_state.fetch_logs.append(log_entry)


# ============================================================================
# CORE BUSINESS LOGIC
# ============================================================================

def batch_process_pipeline(feed_urls: List[str], limit_per_feed: int = 10) -> Dict:
    """
    배치형 파이프라인 전체 흐름
    1. RSS 수집
    2. 중복 제거 (SimHash)
    3. 본문 추출
    4. LLM 요약
    5. DB 적재
    """
    start_time = datetime.now()
    run_id = hashlib.md5(str(start_time).encode()).hexdigest()[:16]
    
    # Step 1: RSS 수집
    raw_articles = fetch_rss_articles(feed_urls, limit_per_feed)
    
    # Step 2: 정규화 및 중복 제거
    normalized_articles = []
    seen_hashes = set()
    
    for article in raw_articles:
        article['url'] = normalize_url(article['url'])
        article['simhash'] = calculate_simhash(article['title'] + article['raw_content'])
        
        # SimHash 기반 중복 체크 (해밍 거리 < 3이면 중복으로 간주)
        is_duplicate = False
        for seen_hash in seen_hashes:
            if hamming_distance(article['simhash'], seen_hash) < 3:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_hashes.add(article['simhash'])
            normalized_articles.append(article)
    
    # Step 3-4: 본문 추출 및 요약
    processed_articles = []
    total_tokens = 0
    
    for article in normalized_articles:
        full_content = extract_article_body(article['url'])
        summary, top_facts = summarize_with_llm(full_content, article['source'])
        
        article_record = {
            'article_id': hashlib.md5(article['url'].encode()).hexdigest(),
            'source': article['source'],
            'url': article['url'],
            'title': article['title'],
            'published_at': article['published_at'],
            'summary': summary,
            'top_facts': top_facts,
            'simhash': article['simhash'],
            'updated_at': datetime.now()
        }
        
        processed_articles.append(article_record)
        total_tokens += estimate_tokens(full_content) + estimate_tokens(summary)
    
    # Step 5: DB 적재
    inserted_count = upsert_articles_to_db(processed_articles)
    
    # 로그 기록
    log_batch_run(run_id, len(raw_articles), inserted_count, start_time)
    
    return {
        'run_id': run_id,
        'discovered': len(raw_articles),
        'deduplicated': len(normalized_articles),
        'inserted': inserted_count,
        'total_tokens': total_tokens,
        'elapsed_seconds': (datetime.now() - start_time).total_seconds()
    }


def on_demand_query(user_query: str, feed_urls: List[str]) -> Dict:
    """
    온디맨드 쿼리 처리
    1. 실시간 RSS 조회
    2. 최신 N건 본문 추출
    3. LLM에 컨텍스트와 함께 전달
    4. 응답 생성
    """
    # 최신 기사 수집
    recent_articles = fetch_rss_articles(feed_urls, limit_per_feed=5)
    
    # 문서 컨텍스트 구성
    context_docs = []
    for article in recent_articles[:5]:
        content = extract_article_body(article['url'])
        context_docs.append({
            'title': article['title'],
            'source': article['source'],
            'url': article['url'],
            'snippet': content[:500]  # 첫 500자
        })
    
    # LLM 프롬프트 구성 (실제로는 API 호출)
    prompt = f"""
사용자 질문: {user_query}

관련 최신 기사:
{chr(10).join([f"[{doc['source']}] {doc['title']}: {doc['snippet']}..." for doc in context_docs])}

위 내용을 바탕으로 사용자 질문에 답변해주세요.
"""
    
    # Mock LLM response
    response = f"'{user_query}'에 대한 답변입니다. 최근 뉴스를 분석한 결과, " \
               f"경제 지표가 전반적으로 긍정적인 흐름을 보이고 있습니다. " \
               f"특히 수출과 고용 지표가 개선되고 있습니다."
    
    citations = [
        f"[{doc['source']}] {doc['title']}\n{doc['url']}" 
        for doc in context_docs[:3]
    ]
    
    return {
        'query': user_query,
        'response': response,
        'citations': citations,
        'tokens_used': estimate_tokens(prompt) + estimate_tokens(response)
    }


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="뉴스 에이전트 프로토타입",
        page_icon="📰",
        layout="wide"
    )
    
    # Initialize session state
    if 'db_articles' not in st.session_state:
        st.session_state.db_articles = []
    if 'fetch_logs' not in st.session_state:
        st.session_state.fetch_logs = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Header
    st.title("📰 뉴스 에이전트 (프로토타입) — Streamlit 초안")
    st.markdown("**AI 기반 뉴스 수집·요약·검색 시스템**")
    st.divider()
    
    # ========================================================================
    # SIDEBAR: 설정
    # ========================================================================
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        
        st.subheader("RSS 피드 소스")
        rss_feeds = st.text_area(
            "RSS URL (줄바꿈으로 구분)",
            value="\n".join(DEFAULT_RSS_FEEDS),
            height=120
        )
        feed_list = [f.strip() for f in rss_feeds.split("\n") if f.strip()]
        
        st.subheader("배치 설정")
        batch_interval = st.slider(
            "배치 주기 (분)",
            min_value=10,
            max_value=120,
            value=BATCH_INTERVAL_MINUTES,
            step=10
        )
        
        articles_per_feed = st.number_input(
            "피드당 수집 기사 수",
            min_value=5,
            max_value=50,
            value=10
        )
        
        st.subheader("요약 옵션")
        include_keywords = st.checkbox("키워드 추출 포함", value=True)
        include_metrics = st.checkbox("핵심 지표 강조", value=True)
        
        st.divider()
        
        st.subheader("📊 토큰 산정기")
        sample_text = st.text_area(
            "샘플 텍스트 입력",
            placeholder="토큰 수를 계산할 텍스트를 입력하세요...",
            height=100
        )
        
        if sample_text:
            tokens = estimate_tokens(sample_text)
            st.metric("예상 토큰 수", f"{tokens:,}")
            st.caption(f"문자 수: {len(sample_text):,}자")
    
    # ========================================================================
    # MAIN AREA: 탭 구성
    # ========================================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 배치 실행", 
        "💬 온디맨드 쿼리", 
        "📊 대시보드", 
        "🗄️ 데이터베이스"
    ])
    
    # ------------------------------------------------------------------------
    # TAB 1: 배치형 플로우
    # ------------------------------------------------------------------------
    with tab1:
        st.header("A) 배치형 파이프라인")
        
        st.markdown("""
        **동작 흐름:**
        1. 📥 RSS 피드에서 최신 기사 수집
        2. 🔍 SimHash 기반 중복 제거
        3. 📄 본문 추출 (readability)
        4. 🤖 LLM 요약 생성 (3문장 + 핵심 지표)
        5. 💾 PostgreSQL DB 적재 (UPSERT)
        6. 📝 실행 로그 기록
        """)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("🚀 배치 실행", type="primary", use_container_width=True):
                with st.spinner("배치 작업 진행 중..."):
                    result = batch_process_pipeline(feed_list, articles_per_feed)
                    st.success("✅ 배치 완료!")
                    
                    st.metric("발견된 기사", f"{result['discovered']}건")
                    st.metric("중복 제거 후", f"{result['deduplicated']}건")
                    st.metric("DB 삽입", f"{result['inserted']}건")
                    st.metric("총 토큰 사용", f"{result['total_tokens']:,}")
                    st.caption(f"소요 시간: {result['elapsed_seconds']:.2f}초")
        
        with col2:
            st.info(f"""
            **현재 설정:**
            - RSS 소스: {len(feed_list)}개
            - 피드당 수집: {articles_per_feed}건
            - 배치 주기: {batch_interval}분
            - 예상 토큰/회: ~{articles_per_feed * len(feed_list) * 1500:,}
            """)
        
        st.divider()
        
        st.subheader("📋 최근 배치 로그")
        if st.session_state.fetch_logs:
            df_logs = pd.DataFrame(st.session_state.fetch_logs)
            df_logs['duration'] = (df_logs['finished_at'] - df_logs['started_at']).dt.total_seconds()
            st.dataframe(
                df_logs[['run_id', 'started_at', 'discovered_count', 'inserted_count', 'duration']],
                use_container_width=True
            )
        else:
            st.caption("아직 실행 내역이 없습니다.")
    
    # ------------------------------------------------------------------------
    # TAB 2: 온디맨드 쿼리
    # ------------------------------------------------------------------------
    with tab2:
        st.header("B) 온디맨드 쿼리 (챗봇)")
        
        st.markdown("""
        최신 뉴스를 실시간으로 검색하고 LLM이 답변을 생성합니다.
        """)
        
        # Chat interface
        user_query = st.text_input(
            "질문을 입력하세요",
            placeholder="예: 오늘 금융시장 동향은?"
        )
        
        if st.button("🔍 질의하기", type="primary"):
            if user_query:
                with st.spinner("뉴스 검색 및 분석 중..."):
                    result = on_demand_query(user_query, feed_list)
                    
                    st.session_state.chat_history.append({
                        'timestamp': datetime.now(),
                        'query': user_query,
                        'response': result['response'],
                        'citations': result['citations'],
                        'tokens': result['tokens_used']
                    })
        
        st.divider()
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("💬 대화 내역")
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                with st.expander(
                    f"🕐 {chat['timestamp'].strftime('%H:%M:%S')} - {chat['query'][:50]}...",
                    expanded=(i == 0)
                ):
                    st.markdown(f"**질문:** {chat['query']}")
                    st.markdown(f"**답변:** {chat['response']}")
                    
                    st.caption("**출처:**")
                    for citation in chat['citations']:
                        st.caption(citation)
                    
                    st.caption(f"토큰 사용: {chat['tokens']:,}")
        else:
            st.info("아직 대화 내역이 없습니다. 질문을 입력해보세요!")
    
    # ------------------------------------------------------------------------
    # TAB 3: 대시보드
    # ------------------------------------------------------------------------
    with tab3:
        st.header("📊 시스템 대시보드")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "총 기사 수",
                f"{len(st.session_state.db_articles):,}건"
            )
        
        with col2:
            recent_articles = [
                a for a in st.session_state.db_articles
                if (datetime.now() - a['published_at']).total_seconds() < 10800  # 3시간
            ]
            st.metric(
                "최근 3시간",
                f"{len(recent_articles)}건"
            )
        
        with col3:
            total_runs = len(st.session_state.fetch_logs)
            st.metric(
                "배치 실행 횟수",
                f"{total_runs}회"
            )
        
        with col4:
            total_queries = len(st.session_state.chat_history)
            st.metric(
                "총 쿼리 수",
                f"{total_queries}건"
            )
        
        st.divider()
        
        # Recent articles preview
        st.subheader("📰 최근 수집 기사 (최대 10건)")
        if st.session_state.db_articles:
            recent_df = pd.DataFrame(st.session_state.db_articles[-10:])
            
            for _, article in recent_df.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**[{article['source']}] {article['title']}**")
                        st.caption(article['summary'])
                    with col_b:
                        st.caption(f"🕐 {article['published_at'].strftime('%m/%d %H:%M')}")
                        st.caption(f"[링크]({article['url']})")
                    
                    if article.get('top_facts'):
                        with st.expander("📌 핵심 팩트"):
                            st.markdown(article['top_facts'])
                    
                    st.divider()
        else:
            st.info("아직 수집된 기사가 없습니다. 배치를 실행해보세요!")
    
    # ------------------------------------------------------------------------
    # TAB 4: 데이터베이스
    # ------------------------------------------------------------------------
    with tab4:
        st.header("🗄️ 데이터베이스 스키마 및 운영")
        
        st.subheader("📋 테이블 구조")
        
        with st.expander("**articles** 테이블", expanded=True):
            st.code("""
CREATE TABLE articles (
    article_id VARCHAR(64) PRIMARY KEY,
    source VARCHAR(100),
    url TEXT UNIQUE,
    title TEXT,
    published_at TIMESTAMP,
    summary TEXT,
    top_facts TEXT,
    simhash BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_published_at ON articles(published_at DESC);
CREATE INDEX idx_source ON articles(source);
CREATE INDEX idx_simhash ON articles(simhash);
            """, language="sql")
        
        with st.expander("**fetch_logs** 테이블"):
            st.code("""
CREATE TABLE fetch_logs (
    run_id VARCHAR(64) PRIMARY KEY,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    discovered_count INT,
    inserted_count INT,
    error_message TEXT
);
            """, language="sql")
        
        with st.expander("**model_runs** 테이블 (LLM 추적용)"):
            st.code("""
CREATE TABLE model_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    article_id VARCHAR(64) REFERENCES articles(article_id),
    model_name VARCHAR(100),
    prompt_tokens INT,
    completion_tokens INT,
    total_cost DECIMAL(10, 6),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
            """, language="sql")
        
        st.divider()
        
        st.subheader("🔧 운영 고려사항")
        st.markdown("""
        **1. 스케줄링**
        - Cron job 또는 APScheduler 사용
        - 배치 실행 시 중복 방지 (분산 락)
        
        **2. 에러 처리**
        - RSS 파싱 실패 시 로그 기록 및 재시도
        - LLM API 호출 실패 시 exponential backoff
        
        **3. 성능 최적화**
        - 본문 추출 병렬 처리 (asyncio, ThreadPoolExecutor)
        - LLM 배치 요청으로 비용 절감
        - Redis 캐시로 중복 URL 체크 가속화
        
        **4. 모니터링**
        - Prometheus + Grafana로 메트릭 추적
        - 토큰 사용량, 응답 시간, 에러율 모니터링
        
        **5. 데이터 보관 정책**
        - 90일 이상 된 기사 아카이빙
        - 로그 테이블 주기적 정리
        """)
        
        st.divider()
        
        st.subheader("📊 현재 DB 상태 미리보기")
        if st.session_state.db_articles:
            df_preview = pd.DataFrame(st.session_state.db_articles)
            st.dataframe(
                df_preview[['article_id', 'source', 'title', 'published_at']].head(20),
                use_container_width=True
            )
            
            # Download button
            csv = df_preview.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"news_articles_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.caption("데이터가 없습니다.")
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    st.divider()
    st.caption("""
    **프로덕션 배포 시 필요한 작업:**
    - `feedparser`, `readability-lxml` 실제 연동
    - OpenAI/Anthropic API 키 환경변수 설정
    - PostgreSQL 연결 (psycopg2 또는 SQLAlchemy)
    - Docker 컨테이너화 및 CI/CD 파이프라인
    - 보안: API 키 관리, Rate limiting, CORS 설정
    """)


if __name__ == "__main__":
    main()