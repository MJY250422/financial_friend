import streamlit as st
import pandas as pd
import feedparser
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import sqlite3
from dataclasses import dataclass, asdict
import re
from collections import defaultdict

# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class Article:
    article_id: str
    source: str
    url: str
    title: str
    published_at: str
    content: str
    summary: str
    top_facts: str
    simhash: str
    tokens_used: int
    created_at: str

@dataclass
class FetchLog:
    log_id: str
    timestamp: str
    log_type: str
    status: str
    details: str
    source: Optional[str] = None

@dataclass
class ModelRun:
    run_id: str
    timestamp: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    article_id: Optional[str] = None
    query: Optional[str] = None

# ============================================================================
# 데이터베이스 초기화
# ============================================================================

def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect('news_agent.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # articles 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            article_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            published_at TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            top_facts TEXT,
            simhash TEXT,
            tokens_used INTEGER,
            created_at TEXT NOT NULL
        )
    ''')
    
    # fetch_logs 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fetch_logs (
            log_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            log_type TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            source TEXT
        )
    ''')
    
    # model_runs 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            article_id TEXT,
            query TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(article_id)
        )
    ''')
    
    # rag_eval 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rag_eval (
            eval_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            query TEXT,
            retrieved_count INTEGER,
            relevance_score REAL,
            response_quality TEXT
        )
    ''')
    
    conn.commit()
    return conn

# ============================================================================
# 유틸리티 함수
# ============================================================================

def generate_simhash(text: str) -> str:
    """텍스트의 simhash 생성 (중복 감지용)"""
    hash_obj = hashlib.md5(text.encode('utf-8'))
    return hash_obj.hexdigest()[:16]

def estimate_tokens(text: str) -> int:
    """한국어 텍스트의 토큰 수 추정 (1,000자 ≈ 500 tokens)"""
    return int(len(text) * 0.5)

def normalize_url(url: str) -> str:
    """URL 정규화"""
    url = url.strip()
    url = re.sub(r'[?#].*$', '', url)
    return url

def extract_text_from_html(html_content: str) -> str:
    """HTML에서 본문 추출 시뮬레이션"""
    # 실제 환경에서는 readability-lxml 또는 newspaper3k 사용
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ============================================================================
# RSS 및 기사 수집
# ============================================================================

RSS_SOURCES = [
    {
        'name': '매일경제',
        'url': 'https://www.mk.co.kr/rss/30300001/',
        'category': 'economy'
    },
    {
        'name': '한국경제',
        'url': 'https://www.hankyung.com/feed/economy',
        'category': 'economy'
    },
    {
        'name': 'KBS뉴스',
        'url': 'https://fs.kbs.co.kr/rss/news.xml',
        'category': 'general'
    }
]

def fetch_rss_articles(source: Dict, max_articles: int = 10) -> List[Dict]:
    """RSS 피드에서 기사 수집"""
    try:
        feed = feedparser.parse(source['url'])
        articles = []
        
        for entry in feed.entries[:max_articles]:
            article = {
                'source': source['name'],
                'url': normalize_url(entry.get('link', '')),
                'title': entry.get('title', '제목 없음'),
                'published_at': entry.get('published', datetime.now().isoformat()),
                'content': entry.get('summary', entry.get('description', ''))
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        st.error(f"RSS 수집 오류 ({source['name']}): {str(e)}")
        return []

def generate_llm_summary(content: str, source: str) -> tuple:
    """LLM을 사용한 요약 생성 시뮬레이션"""
    # 실제 환경에서는 OpenAI API 또는 다른 LLM 호출
    
    # 토큰 계산
    prompt_tokens = estimate_tokens(f"다음 기사를 3문장으로 요약하고 핵심 수치를 추출하세요:\n{content}")
    
    # 간단한 요약 생성 (실제로는 LLM 응답)
    sentences = content.split('.')[:3]
    summary = '. '.join(sentences).strip() + '.'
    
    # 핵심 사실 추출
    top_facts = f"""• 주요 변동: {hash(content) % 100}% 변화
• 분석 기간: 최근 {hash(content) % 12 + 1}개월
• 출처: {source}"""
    
    completion_tokens = estimate_tokens(summary + top_facts)
    
    return summary, top_facts, prompt_tokens, completion_tokens

def deduplicate_articles(articles: List[Dict], existing_hashes: set) -> List[Dict]:
    """simhash 기반 중복 제거"""
    unique_articles = []
    seen_hashes = existing_hashes.copy()
    
    for article in articles:
        article_hash = generate_simhash(article['title'] + article['url'])
        if article_hash not in seen_hashes:
            article['simhash'] = article_hash
            unique_articles.append(article)
            seen_hashes.add(article_hash)
    
    return unique_articles

# ============================================================================
# 배치 프로세스
# ============================================================================

def run_batch_process(conn: sqlite3.Connection, settings: Dict) -> Dict:
    """배치형 뉴스 수집 및 요약"""
    cursor = conn.cursor()
    start_time = time.time()
    
    # 로그 기록
    batch_log_id = f"batch_{int(time.time() * 1000)}"
    log_entry = FetchLog(
        log_id=batch_log_id,
        timestamp=datetime.now().isoformat(),
        log_type='batch',
        status='started',
        details=f"배치 프로세스 시작 - {len(RSS_SOURCES)}개 소스"
    )
    cursor.execute(
        'INSERT INTO fetch_logs VALUES (?, ?, ?, ?, ?, ?)',
        tuple(asdict(log_entry).values())
    )
    conn.commit()
    
    # 기존 simhash 가져오기
    cursor.execute('SELECT simhash FROM articles')
    existing_hashes = {row[0] for row in cursor.fetchall()}
    
    all_articles = []
    total_tokens = 0
    fetch_results = []
    
    # 각 RSS 소스에서 수집
    for source in RSS_SOURCES:
        try:
            raw_articles = fetch_rss_articles(source, settings['articles_per_source'])
            unique_articles = deduplicate_articles(raw_articles, existing_hashes)
            
            # 각 기사 처리
            for article in unique_articles:
                # 본문 추출 (실제로는 readability 사용)
                content = extract_text_from_html(article['content'])
                
                # LLM 요약
                summary, top_facts, prompt_tok, comp_tok = generate_llm_summary(
                    content, article['source']
                )
                
                # Article 객체 생성
                article_id = f"{article['source']}_{generate_simhash(article['url'])}"
                article_obj = Article(
                    article_id=article_id,
                    source=article['source'],
                    url=article['url'],
                    title=article['title'],
                    published_at=article['published_at'],
                    content=content[:5000],  # 최대 5000자
                    summary=summary,
                    top_facts=top_facts,
                    simhash=article['simhash'],
                    tokens_used=prompt_tok + comp_tok,
                    created_at=datetime.now().isoformat()
                )
                
                # DB 삽입 (UPSERT)
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(asdict(article_obj).values()))
                
                # Model run 기록
                run_id = f"run_{int(time.time() * 1000)}_{article_id}"
                model_run = ModelRun(
                    run_id=run_id,
                    timestamp=datetime.now().isoformat(),
                    model_name='gpt-4o-mini',  # 실제 모델명
                    prompt_tokens=prompt_tok,
                    completion_tokens=comp_tok,
                    total_tokens=prompt_tok + comp_tok,
                    article_id=article_id
                )
                cursor.execute(
                    'INSERT INTO model_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    tuple(asdict(model_run).values())
                )
                
                all_articles.append(article_obj)
                total_tokens += article_obj.tokens_used
                existing_hashes.add(article['simhash'])
            
            # 소스별 로그
            fetch_log = FetchLog(
                log_id=f"fetch_{source['name']}_{int(time.time() * 1000)}",
                timestamp=datetime.now().isoformat(),
                log_type='fetch',
                status='success',
                details=f"{len(unique_articles)}건 수집 (중복 {len(raw_articles) - len(unique_articles)}건 제거)",
                source=source['name']
            )
            cursor.execute(
                'INSERT INTO fetch_logs VALUES (?, ?, ?, ?, ?, ?)',
                tuple(asdict(fetch_log).values())
            )
            
            fetch_results.append({
                'source': source['name'],
                'collected': len(unique_articles),
                'duplicates': len(raw_articles) - len(unique_articles)
            })
            
        except Exception as e:
            error_log = FetchLog(
                log_id=f"error_{source['name']}_{int(time.time() * 1000)}",
                timestamp=datetime.now().isoformat(),
                log_type='fetch',
                status='error',
                details=f"오류 발생: {str(e)}",
                source=source['name']
            )
            cursor.execute(
                'INSERT INTO fetch_logs VALUES (?, ?, ?, ?, ?, ?)',
                tuple(asdict(error_log).values())
            )
    
    conn.commit()
    
    # 완료 로그
    elapsed_time = time.time() - start_time
    complete_log = FetchLog(
        log_id=f"batch_complete_{int(time.time() * 1000)}",
        timestamp=datetime.now().isoformat(),
        log_type='batch',
        status='completed',
        details=f"{len(all_articles)}건 처리, {total_tokens:,} 토큰 사용, {elapsed_time:.1f}초 소요"
    )
    cursor.execute(
        'INSERT INTO fetch_logs VALUES (?, ?, ?, ?, ?, ?)',
        tuple(asdict(complete_log).values())
    )
    conn.commit()
    
    return {
        'articles_count': len(all_articles),
        'total_tokens': total_tokens,
        'elapsed_time': elapsed_time,
        'fetch_results': fetch_results
    }

# ============================================================================
# 온디맨드 쿼리
# ============================================================================

def process_ondemand_query(conn: sqlite3.Connection, query: str, settings: Dict) -> Dict:
    """온디맨드 쿼리 처리"""
    cursor = conn.cursor()
    start_time = time.time()
    
    # 키워드 추출
    keywords = [word.lower() for word in query.split() if len(word) > 1]
    
    # DB에서 관련 기사 검색
    time_window = datetime.now() - timedelta(hours=settings['time_window'])
    
    cursor.execute('''
        SELECT * FROM articles 
        WHERE published_at >= ? 
        ORDER BY published_at DESC 
        LIMIT 20
    ''', (time_window.isoformat(),))
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    # 관련도 계산
    relevant_articles = []
    for row in rows:
        article = dict(zip(columns, row))
        relevance_score = sum(
            1 for kw in keywords 
            if kw in article['title'].lower() or kw in article['summary'].lower()
        )
        if relevance_score > 0 or len(relevant_articles) < 5:
            article['relevance_score'] = relevance_score
            relevant_articles.append(article)
    
    # 관련도 순 정렬
    relevant_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
    top_articles = relevant_articles[:5]
    
    # 없으면 실시간 수집
    if len(top_articles) == 0:
        st.warning("DB에 관련 기사가 없습니다. 실시간 수집을 시작합니다...")
        for source in RSS_SOURCES[:2]:
            raw_articles = fetch_rss_articles(source, 5)
            for article in raw_articles[:3]:
                content = extract_text_from_html(article['content'])
                summary, top_facts, _, _ = generate_llm_summary(content, article['source'])
                top_articles.append({
                    'source': article['source'],
                    'url': article['url'],
                    'title': article['title'],
                    'summary': summary,
                    'top_facts': top_facts,
                    'relevance_score': 0
                })
    
    # LLM 응답 생성
    context = "\n\n".join([
        f"[{i+1}] {a['title']}\n{a['summary']}\n출처: {a['source']}"
        for i, a in enumerate(top_articles)
    ])
    
    prompt = f"질문: {query}\n\n관련 기사:\n{context}"
    prompt_tokens = estimate_tokens(prompt)
    
    # 응답 생성 (실제로는 LLM 호출)
    response = f"""질문하신 '{query}'에 대한 분석 결과입니다.\n\n"""
    
    for i, article in enumerate(top_articles, 1):
        response += f"**{i}. {article['title']}**\n"
        response += f"{article['summary']}\n"
        response += f"[출처: {article['source']}]({article['url']})\n\n"
    
    response += f"---\n💡 **종합 분석**: {len(top_articles)}개 기사를 분석한 결과, "
    response += f"최근 {settings['time_window']}시간 동안의 주요 동향을 확인했습니다.\n\n"
    
    completion_tokens = estimate_tokens(response)
    total_tokens = prompt_tokens + completion_tokens
    
    # Model run 기록
    run_id = f"query_{int(time.time() * 1000)}"
    model_run = ModelRun(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        model_name='gpt-4o-mini',
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        query=query
    )
    cursor.execute(
        'INSERT INTO model_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        tuple(asdict(model_run).values())
    )
    
    # RAG 평가 기록
    eval_id = f"eval_{int(time.time() * 1000)}"
    cursor.execute('''
        INSERT INTO rag_eval VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        eval_id,
        datetime.now().isoformat(),
        query,
        len(top_articles),
        sum(a['relevance_score'] for a in top_articles) / max(len(top_articles), 1),
        'good'
    ))
    
    # 쿼리 로그
    query_log = FetchLog(
        log_id=f"query_{int(time.time() * 1000)}",
        timestamp=datetime.now().isoformat(),
        log_type='query',
        status='success',
        details=f"'{query}' - {len(top_articles)}건 참조, {total_tokens:,} 토큰 사용"
    )
    cursor.execute(
        'INSERT INTO fetch_logs VALUES (?, ?, ?, ?, ?, ?)',
        tuple(asdict(query_log).values())
    )
    
    conn.commit()
    
    return {
        'response': response,
        'articles': top_articles,
        'tokens': total_tokens,
        'elapsed_time': time.time() - start_time
    }

# ============================================================================
# Streamlit UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="뉴스 에이전트",
        page_icon="📰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # DB 초기화
    if 'conn' not in st.session_state:
        st.session_state.conn = init_database()
    
    conn = st.session_state.conn
    cursor = conn.cursor()
    
    # 사이드바 설정
    with st.sidebar:
        st.title("📰 뉴스 에이전트")
        st.markdown("**배치형 + 온디맨드형**")
        st.divider()
        
        st.subheader("⚙️ 설정")
        
        batch_interval = st.number_input(
            "배치 주기 (분)",
            min_value=5,
            max_value=1440,
            value=30,
            help="자동 배치 실행 간격"
        )
        
        articles_per_source = st.number_input(
            "소스당 기사 수",
            min_value=1,
            max_value=50,
            value=5,
            help="각 RSS 소스에서 가져올 기사 수"
        )
        
        time_window = st.number_input(
            "시간 윈도우 (시간)",
            min_value=1,
            max_value=48,
            value=3,
            help="표시할 기사의 시간 범위"
        )
        
        settings = {
            'batch_interval': batch_interval,
            'articles_per_source': articles_per_source,
            'time_window': time_window
        }
        
        st.divider()
        
        if st.button("🔄 배치 실행", use_container_width=True, type="primary"):
            with st.spinner("배치 프로세스 실행 중..."):
                result = run_batch_process(conn, settings)
                st.success(f"✅ {result['articles_count']}건 처리 완료!")
                st.info(f"토큰: {result['total_tokens']:,} | 시간: {result['elapsed_time']:.1f}초")
        
        st.divider()
        st.caption("💡 자동 배치는 백그라운드에서 실행됩니다")
    
    # 메인 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "💬 챗봇 요약", "📋 실행 로그", "📈 통계"])
    
    # 탭 1: 대시보드
    with tab1:
        st.header("최근 뉴스 대시보드")
        
        # 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(tokens_used) FROM articles')
        total_tokens = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(tokens_used) FROM articles')
        avg_tokens = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT MAX(created_at) FROM articles')
        last_batch = cursor.fetchone()[0]
        
        with col1:
            st.metric("총 기사 수", f"{total_articles:,}")
        with col2:
            st.metric("총 토큰", f"{total_tokens:,}")
        with col3:
            st.metric("평균 토큰/기사", f"{int(avg_tokens):,}")
        with col4:
            if last_batch:
                st.metric("마지막 배치", datetime.fromisoformat(last_batch).strftime("%H:%M"))
            else:
                st.metric("마지막 배치", "N/A")
        
        st.divider()
        
        # 기사 목록
        time_cutoff = datetime.now() - timedelta(hours=time_window)
        cursor.execute('''
            SELECT * FROM articles 
            WHERE published_at >= ? 
            ORDER BY published_at DESC
        ''', (time_cutoff.isoformat(),))
        
        articles = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        if len(articles) == 0:
            st.warning("표시할 기사가 없습니다. 배치를 실행해주세요.")
        else:
            st.subheader(f"최근 {time_window}시간 뉴스 ({len(articles)}건)")
            
            for row in articles:
                article = dict(zip(columns, row))
                
                with st.expander(f"**{article['title']}** - {article['source']}", expanded=False):
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"**📅 발행시각:** {datetime.fromisoformat(article['published_at']).strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(f"**📝 요약:**")
                        st.write(article['summary'])
                        
                        st.markdown("**📊 핵심 사실:**")
                        st.info(article['top_facts'])
                        
                        st.markdown(f"[원문 보기 →]({article['url']})")
                    
                    with col_b:
                        st.metric("토큰", f"{article['tokens_used']:,}")
                        st.caption(f"ID: {article['article_id'][:20]}...")
    
    # 탭 2: 챗봇
    with tab2:
        st.header("💬 온디맨드 뉴스 요약")
        st.caption("궁금한 뉴스 주제를 입력하면 실시간으로 요약해드립니다.")
        
        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # 채팅 입력
        user_query = st.chat_input("예: 오늘 금융뉴스 요약, 반도체 관련 최신 소식")
        
        if user_query:
            # 사용자 메시지 추가
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_query,
                'timestamp': datetime.now()
            })
            
            # 응답 생성
            with st.spinner("분석 중..."):
                result = process_ondemand_query(conn, user_query, settings)
            
            # 응답 추가
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': result['response'],
                'timestamp': datetime.now(),
                'tokens': result['tokens'],
                'elapsed': result['elapsed_time']
            })
        
        # 채팅 표시
        for msg in st.session_state.chat_history:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])
                if msg['role'] == 'assistant':
                    st.caption(f"⏱️ {msg['elapsed']:.1f}초 | 🎯 {msg['tokens']:,} tokens | 🕐 {msg['timestamp'].strftime('%H:%M:%S')}")
    
    # 탭 3: 로그
    with tab3:
        st.header("📋 실행 로그")
        
        log_type_filter = st.multiselect(
            "로그 타입 필터",
            ['batch', 'fetch', 'query', 'error'],
            default=['batch', 'fetch', 'query']
        )
        
        placeholders = ','.join(['?' for _ in log_type_filter])
        cursor.execute(f'''
            SELECT * FROM fetch_logs 
            WHERE log_type IN ({placeholders})
            ORDER BY timestamp DESC 
            LIMIT 100
        ''', tuple(log_type_filter))
        
        logs = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        if len(logs) == 0:
            st.info("로그가 없습니다.")
        else:
            for row in logs:
                log = dict(zip(columns, row))
                
                status_emoji = {
                    'started': '▶️',
                    'success': '✅',
                    'completed': '✅',
                    'error': '❌',
                    'running': '🔄'
                }.get(log['status'], '•')
                
                type_color = {
                    'batch': 'blue',
                    'fetch': 'green',
                    'query': 'orange',
                    'error': 'red'
                }.get(log['log_type'], 'gray')
                
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 5])
                    with col1:
                        st.markdown(f":{type_color}[**{log['log_type'].upper()}**]")
                    with col2:
                        st.caption(datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
                    with col3:
                        st.markdown(f"{status_emoji} {log['details']}")
                    st.divider()
    
    # 탭 4: 통계
    with tab4:
        st.header("📈 통계 및 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("소스별 기사 수")
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM articles 
                GROUP BY source 
                ORDER BY count DESC
            ''')
            source_stats = cursor.fetchall()
            if source_stats:
                df_sources = pd.DataFrame(source_stats, columns=['소스', '기사 수'])
                st.bar_chart(df_sources.set_index('소스'))
            else:
                st.info("데이터가 없습니다.")
        
        with col2:
            st.subheader("토큰 사용 추이")
            cursor.execute('''
                SELECT DATE(timestamp) as date, SUM(total_tokens) as tokens
                FROM model_runs
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 7
            ''')
            token_stats = cursor.fetchall()
            if token_stats:
                df_tokens = pd.DataFrame(token_stats, columns=['날짜', '토큰'])
                st.line_chart(df_tokens.set_index('날짜'))
            else:
                st.info("데이터가 없습니다.")
        
        st.divider()
        
        st.subheader("📊 전체 모델 실행 통계")
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                SUM(total_tokens) as total_tokens,
                AVG(total_tokens) as avg_tokens,
                SUM(prompt_tokens) as prompt_tokens,
                SUM(completion_tokens) as completion_tokens
            FROM model_runs
        ''')
        model_stats = cursor.fetchone()
        
        if model_stats and model_stats[0] > 0:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("총 실행 횟수", f"{model_stats[0]:,}")
            with col2:
                st.metric("총 토큰", f"{model_stats[1]:,}")
            with col3:
                st.metric("평균 토큰", f"{int(model_stats[2]):,}")
            with col4:
                st.metric("프롬프트 토큰", f"{model_stats[3]:,}")
            with col5:
                st.metric("완성 토큰", f"{model_stats[4]:,}")
        else:
            st.info("모델 실행 기록이 없습니다.")
        
        st.divider()
        
        # RAG 평가 통계
        st.subheader("🎯 RAG 평가 통계")
        cursor.execute('''
            SELECT 
                AVG(retrieved_count) as avg_retrieved,
                AVG(relevance_score) as avg_relevance,
                COUNT(*) as total_queries
            FROM rag_eval
        ''')
        rag_stats = cursor.fetchone()
        
        if rag_stats and rag_stats[2] > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 쿼리 수", f"{rag_stats[2]:,}")
            with col2:
                st.metric("평균 검색 문서 수", f"{rag_stats[0]:.1f}")
            with col3:
                st.metric("평균 관련도 점수", f"{rag_stats[1]:.2f}")
        else:
            st.info("RAG 평가 기록이 없습니다.")
        
        st.divider()
        
        # 최근 활동
        st.subheader("🕒 최근 활동")
        cursor.execute('''
            SELECT timestamp, model_name, total_tokens, query, article_id
            FROM model_runs
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        recent_runs = cursor.fetchall()
        
        if recent_runs:
            df_recent = pd.DataFrame(
                recent_runs,
                columns=['시각', '모델', '토큰', '쿼리', '기사ID']
            )
            df_recent['시각'] = pd.to_datetime(df_recent['시각']).dt.strftime('%Y-%m-%d %H:%M:%S')
            df_recent['쿼리'] = df_recent['쿼리'].fillna('-')
            df_recent['기사ID'] = df_recent['기사ID'].fillna('-').str[:20]
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("최근 활동이 없습니다.")

if __name__ == "__main__":
    main()