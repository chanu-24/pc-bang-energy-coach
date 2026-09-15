# app.py
import streamlit as st
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

st.set_page_config(
    page_title="아까운 전기요금, 인건비로 환산하기",
    page_icon="💸",
    layout="centered"
)

# 1. [RAG & ChromaDB] 한국에너지공단 공식 가이드 및 지식 베이스 초기화
@st.cache_resource
def init_rag_system():
    client = chromadb.Client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="korea_energy_guide_kb",
        embedding_function=ef
    )
    
    # 한국에너지공단 공식 에너지 절감 가이드 문서 Chunk 데이터
    documents = [
        "모니터 영역: 손님이 없는 빈 좌석의 모니터 대기전력 방치 및 고주사율 상시 유지는 전력 손실의 주원인입니다. 대기전력 자동 차단 및 절전 모드 활성화로 대기 전력을 대폭 감축할 수 있습니다.",
        "설비 및 본체 영역: PC 게임 최대 프레임 수 제한과 야간 업데이트 대기 시간의 불필요한 본체 가동을 막고 원격(WoL) 제어를 도입하면 GPU 과열 방지 및 전력 낭비를 차단합니다.",
        "주방 및 판매설비 영역: 온수기, 제빙기, 쇼케이스 등 주방 가전의 24시간 상시 가동을 지양하고 심야 시간 타이머 및 스마트 멀티탭을 적용하여 전력 누수를 방지합니다.",
        "조명 및 냉난방 영역: 이용객이 적은 심야 시간대 매장 전체 조명을 켜지 않고 특정 구역(존)으로 유도하며 독립 제어 시스템을 운영하여 고정비를 절감합니다."
    ]
    metadatas = [{"area": "monitor"}, {"area": "hardware"}, {"area": "kitchen"}, {"area": "lighting"}]
    ids = ["doc_m", "doc_h", "doc_k", "doc_l"]
    
    if collection.count() == 0:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        
    return collection

rag_collection = init_rag_system()

# PC방 전용 프리미엄 다크/카드 스타일 UI/UX (모바일 앱 감성)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    .pc-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .highlight-banner {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
    }
    .metric-badge {
        background-color: #0f172a;
        border: 1px solid #475569;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {"pc_count": 50}

# ==========================================
# [설문 페이지 영역별 구성 (1분 내 완료형)]
# ==========================================

# 1. 모니터 영역 설문 (질문 3개)
if st.session_state.step == 1:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("Step 1/4 : 모니터 영역 정밀 진단")
    
    st.markdown("### 🖥️ 모니터 및 주변기기 관리 상태")
    pc_count = st.number_input("매장 총 PC 및 모니터 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
    
    m1 = st.selectbox("1. 손님이 없는 빈 좌석의 모니터 전원 및 대기 상태가 그대로 방치되나요?", ["전혀 관리 안 함 (상시 대기)", "부분 관리", "자동 절전 시스템 완비"])
    m2 = st.selectbox("2. 모니터 응답 속도 및 주사율(Hz)을 고정하여 불필요한 전력 소모를 막고 계신가요?", ["기본 설정 그대로", "일부 타협", "최적화 설정 적용"])
    m3 = st.selectbox("3. 모니터 주변 기기(스탠드 조명, USB 허브 등) 전력 차단 멀티탭을 사용하시나요?", ["상시 켜둠", "수동 소등", "자동 차단 멀티탭 사용"])
    
    if st.button("다음: 설비/본체 영역으로 ➔", use_container_width=True):
        st.session_state.answers["pc_count"] = pc_count
        st.session_state.answers["monitor"] = [m1, m2, m3]
        st.session_state.step = 2
        st.rerun()

# 2. 설비/본체 영역 설문 (질문 3개)
elif st.session_state.step == 2:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("Step 2/4 : 설비 및 본체 영역 정밀 진단")
    
    st.markdown("### 💻 하드웨어 및 업데이트 관리 상태")
    h1 = st.selectbox("1. 게임 최대 프레임 수 제한(백그라운드/메뉴 포함)을 설정하여 GPU 과열을 막고 계신가요?", ["제한 없음", "일부 게임만 제한", "매장 전체 공통 제한"])
    h2 = st.selectbox("2. 야간 게임 업데이트 대기 시 빈 PC를 미리 켜두고 대기전력을 낭비하시나요?", ["업데이트 몇 시간 전부터 켜둠", "시작 전 잠시 켜둠", "Wake-on-LAN 원격 제어 활용"])
    h3 = st.selectbox("3. 업데이트가 완료된 빈 좌석 PC를 곧바로 자동 절전/종료 처리하시나요?", ["다음 손님 올 때까지 방치", "직원이 뒤늦게 수동 종료", "완료 즉시 자동 절전"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("다음: 주방 영역으로 ➔", use_container_width=True):
            st.session_state.answers["hardware"] = [h1, h2, h3]
            st.session_state.step = 3
            st.rerun()

# 3. 주방 영역 설문 (질문 3개)
elif st.session_state.step == 3:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("Step 3/4 : 주방 영역 정밀 진단")
    
    st.markdown("### 🍳 주방 및 판매설비 관리 상태")
    k1 = st.selectbox("1. 온수기, 제빙기, 전자레인지 등 주방 가전의 대기전력 및 상시 가동을 관리하시나요?", ["24시간 상시 켜둠", "부분 절전", "시간대별 타이머/스마트 멀티탭 제어"])
    k2 = st.selectbox("2. 손님이 적은 심야 시간에 주방 조리대 및 보조 가전 전원을 분리 소등하시나요?", ["전체 켜둠", "일부만 소등", "구역별 완벽 분리 소등"])
    k3 = st.selectbox("3. 냉장/냉동 쇼케이스 문 개폐 및 온도 설정을 에너지 절약형으로 운영하시나요?", ["기본 설정", "수시 점검", "최적 온도 및 효율 관리"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("다음: 조명/냉난방 영역으로 ➔", use_container_width=True):
            st.session_state.answers["kitchen"] = [k1, k2, k3]
            st.session_state.step = 4
            st.rerun()

# 4. 조명 및 냉난방 영역 설문 (질문 3개)
elif st.session_state.step == 4:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("Step 4/4 : 조명 및 냉난방 영역 정밀 진단")
    
    st.markdown("### 💡❄️ 조명 및 공조 시스템 관리 상태")
    l1 = st.selectbox("1. 손님이 적은 시간대에 매장 전체를 밝히지 않고 특정 구역(존)으로만 안내하시나요?", ["매장 전체 자유 이용", "일부 구역 제한 운영", "저이용 구역 소등 및 집중 안내"])
    l2 = st.selectbox("2. 키보드·마우스·헤드셋 거치대 등 게이밍 주변기기 조명 대기전력을 관리하시나요?", ["상시 점등", "일부 소등", "미사용 시 자동 소등/밝기 조절"])
    l3 = st.selectbox("3. 냉난방기와 홀 조명을 구역별로 독립 제어하여 낭비를 줄이고 계신가요?", ["통합 제어/상시 가동", "수동 조절", "구역별 스마트 독립 제어"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("🚀 AI 정밀 진단 및 인건비 환산 결과 보기", use_container_width=True):
            st.session_state.answers["lighting"] = [l1, l2, l3]
            st.session_state.step = 5
            st.rerun()

# ==========================================
# [마지막 페이지: AI 진단 결과, 행동추천, 효과 및 환산]
# ==========================================
elif st.session_state.step == 5:
    st.title("📊 AI 에너지 진단 & 인건비 환산 리포트")
    st.caption("한국에너지공단 공식 가이드 및 한전 단가 기반 정량 계산 결과")
    
    pc_count = st.session_state.answers.get("pc_count", 50)
    
    # [Python 정량 계산 엔진 로직]
    # 한전 일반용 전력 단가: 약 130원/kWh, 탄소 배출계수: 0.4781 kgCO2e/kWh
    # 최저시급(인건비 환산 기준): 10,030원
    KRW_PER_KWH = 130
    CARBON_FACTOR = 0.4781
    HOURLY_WAGE = 10030
    
    base_kwh = pc_count * 190  # 기존 월 소비량 기준
    min_saved_kwh = int(base_kwh * 0.30)  # Min 절감량 (30%)
    max_saved_kwh = int(base_kwh * 0.45)  # Max 절감량 (45%)
    
    min_saved_cost = min_saved_kwh * KRW_PER_KWH
    max_saved_cost = max_saved_kwh * KRW_PER_KWH
    
    min_hours = int(min_saved_cost / HOURLY_WAGE)
    max_hours = int(max_saved_cost / HOURLY_WAGE)
    
    base_cost = base_kwh * KRW_PER_KWH
    min_cost_after = base_cost - max_saved_cost
    max_cost_after = base_cost - min_saved_kwh * KRW_PER_KWH
    
    base_carbon = base_kwh * CARBON_FACTOR
    min_carbon_saved = min_saved_kwh * CARBON_FACTOR
    max_carbon_saved = max_saved_kwh * CARBON_FACTOR
    
    # RAG 검색 결과 연동
    rag_res = rag_collection.query(query_texts=["모니터 및 본체 대기전력 낭비 개선 우선순위"], n_results=1)
    top_rag_text = rag_res['documents'][0][0] if rag_res['documents'] else "공식 절감 가이드를 불러왔습니다."

    # 1. 인건비 환산 강조 배너
    st.markdown(f"""
    <div class="highlight-banner">
        <h2>💡 전기요금을 아껴서 알바생 인건비로 채운다!</h2>
        <p style="font-size:17px; margin-top:8px;">
            매장 전력 체질을 개선하면 월 <b>{min_saved_cost:,}원 ~ {max_saved_cost:,}원</b>의 전기요금이 절감됩니다.<br>
            이는 알바생 인건비 <b>약 {min_hours}시간 ~ {max_hours}시간분</b>에 달하는 놀라운 절약 효과입니다!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 중간: AI 에너지 진단 결과 (가장 먼저 확인할 영역)
    st.subheader("🎯 이번주 가장 먼저 확인할 영역 (Top Priority)")
    st.markdown(f"""
    <div class="pc-card" style="border-left: 6px solid #38bdf8;">
        <h4 style="margin:0; color:#38bdf8;">🔥 AI 룰 엔진 및 RAG 분석 우선 개선점</h4>
        <p style="margin:8px 0 0 0; color:#cbd5e1; font-size:15px; line-height:1.5;">
            {top_rag_text}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 중간: PC방 낭비요인 및 영역별 행동추천
    st.subheader("🛠️ 영역별 낭비요인 분석 및 실천 행동요령")
    
    areas_data = [
        {"name": "🖥️ 모니터 영역", "share": 0.30, "tip": "빈 좌석 모니터 강제 절전 및 고주사율 타협 설정 적용", "rag": "대기전력 자동 차단 멀티탭 및 슬립 모드 활용"},
        {"name": "💻 설비/본체 영역", "share": 0.30, "tip": "게임 최대 프레임 제한 및 야간 업데이트 자동 종료 연동", "rag": "GPU 부하 감소 및 원격(WoL) 전원 제어 구축"},
        {"name": "🍳 주방 영역", "share": 0.20, "tip": "온수기·제빙기 심야 시간 타이머 제어 및 보조 가전 분리 소등", "rag": "상시 가동 가전 타이머 설치로 전력 누수 원천 차단"},
        {"name": "💡 조명/냉난방 영역", "share": 0.20, "tip": "손님 적은 시간대 구역(존) 집중 안내 및 주변기기 조명 소등", "rag": "냉난방 및 홀 조명 독립 제어로 불필요한 공조 차단"}
    ]
    
    for item in areas_data:
        area_kwh = int(max_saved_kwh * item["share"])
        area_cost = int(max_saved_cost * item["share"])
        area_hours = int(area_cost / HOURLY_WAGE)
        
        st.markdown(f"""
        <div class="pc-card">
            <h4 style="margin:0 0 6px 0; color:#f8fafc;">{item['name']}</h4>
            <p style="margin:2px 0; font-size:14px; color:#94a3b8;"><b>💡 행동요령:</b> {item['tip']}</p>
            <p style="margin:2px 0; font-size:13px; color:#38bdf8;"><b>📋 공단 가이드 근거:</b> {item['rag']}</p>
            <hr style="border-color:#334155; margin:8px 0;">
            <p style="margin:0; font-size:14px; color:#34d399;">
               • 예상 전력 감소: <b>↓ 약 {area_kwh:,} kWh</b><br>
               • 요금 감액 및 인건비 효과: <b>↓ 약 {area_cost:,}원 절약</b> (인건비 <b>{area_hours}시간</b> 확보)
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 4. 마지막: 전력, 비용, 탄소 절감 효과 및 세부 비교
    st.markdown("---")
    st.subheader("📈 종합 에너지 및 비용 절감 효과 (Min ~ Max 범위)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("월 총 전력 사용량", f"{base_kwh:,} kWh", f"↓ {min_saved_kwh:,} ~ {max_saved_kwh:,} kWh 감소", delta_color="inverse")
    with col2:
        st.metric("월 총 전기요금", f"{base_cost:,}원", f"↓ {min_saved_cost:,} ~ {max_saved_cost:,}원 절감", delta_color="inverse")
    with col3:
        st.metric("월 탄소 배출량", f"{int(base_carbon):,} kg", f"↓ {int(min_carbon_saved):,} ~ {int(max_carbon_saved):,} kg 감축", delta_color="inverse")
        
    st.markdown("---")
    st.subheader("❓ 어디에서 가장 많이 줄일 수 있나요?")
    st.info("""
    📊 **정량 계산 엔진 분석 결과**:
    * **모니터 영역(30%)**과 **설비/본체 영역(30%)**에서 전체 절감액의 60폭 이상을 차지합니다. 
    * 따라서 매장 내 **모니터 대기전력 자동 차단**과 **게임 프레임 제한 및 업데이트 자동 종료 시스템**을 가장 먼저 도입하는 것이 투자 대비 가장 큰 감액 효과를 냅니다.
    """)
    
    if st.button("🔄 처음부터 다시 진단하기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()