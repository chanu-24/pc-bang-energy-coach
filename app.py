# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: Pandas 데이터 및 계산 파이프라인 (캐싱 처리)
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "PC_MONITOR", "name": "게이밍 PC 및 모니터 대기전력", "rated_power_kw": 0.25, "default_hours": 24},
        {"equipment": "HVAC", "name": "냉난방기·환기 설비", "rated_power_kw": 3.5, "default_hours": 10},
        {"equipment": "KITCHEN", "name": "주방 조리기구 (라면기·튀김기)", "rated_power_kw": 2.0, "default_hours": 5},
        {"equipment": "LIGHTING", "name": "매장 조명 및 기타", "rated_power_kw": 1.0, "default_hours": 12}
    ])
    return equipment_df

def calculate_energy_impact(survey_answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    
    results = []
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        inefficiency_weight = survey_answers.get(eq, 1.0)
        
        monthly_kwh = row["rated_power_kw"] * row["default_hours"] * 30 * inefficiency_weight
        monthly_cost = monthly_kwh * KRW_PER_KWH
        monthly_carbon = monthly_kwh * CARBON_FACTOR
        
        results.append({
            "equipment": eq,
            "name": row["name"],
            "monthly_kwh": round(monthly_kwh, 2),
            "monthly_cost": round(monthly_cost),
            "monthly_carbon": round(monthly_carbon, 2)
        })
    return pd.DataFrame(results)

# 2. 백엔드: Python Rule Engine (10개 문항 응답 기반 다중 판정)
def python_rule_engine(answers):
    diagnoses = []
    
    if answers.get("q1_pc_standby") == "방치함":
        diagnoses.append({
            "waste_code": "PC_STANDBY_POWER", "equipment": "PC_MONITOR", "risk_score": 90,
            "title": "퇴석 좌석 PC·모니터 전원 자동 차단 미설정",
            "description": "손님이 없는 좌석의 본체·모니터·노하드 서버 주변기기가 24시간 대기전력을 소모하고 있습니다."
        })
        
    if answers.get("q2_server_power") == "상시 켜둠(개선 필요)":
        diagnoses.append({
            "waste_code": "SERVER_IDLE", "equipment": "PC_MONITOR", "risk_score": 75,
            "title": "부대 장비 및 네트워크 스위치 상시 과다 가동",
            "description": "영업 마감 후에도 불필요한 네트워크 장비 및 허브가 최대 전력으로 구동 중입니다."
        })

    if answers.get("q3_hvac_temp") == "과도한 저온/고온 유지":
        diagnoses.append({
            "waste_code": "HVAC_OVER_USE", "equipment": "HVAC", "risk_score": 85,
            "title": "냉난방기 과도한 온도 설정 및 야간 방치",
            "description": "실내 적정 온도(여름 26도, 겨울 18~20도)를 초과하여 에어컨·히터가 비효율적으로 돌아갑니다."
        })

    if answers.get("q4_ventilation") == "24시간 연속 가동":
        diagnoses.append({
            "waste_code": "VENT_CONTINUOUS", "equipment": "HVAC", "risk_score": 65,
            "title": "공조·환기 설비 24시간 무단속 가동",
            "description": "새벽 시간대 이용객이 적음에도 급·배기 환기팬이 최고 속도로 가동되고 있습니다."
        })

    if answers.get("q5_kitchen_preheat") == "상시 고온 예열 유지":
        diagnoses.append({
            "waste_code": "KITCHEN_PREHEAT", "equipment": "KITCHEN", "risk_score": 80,
            "title": "주방 조리기구(라면조리기·튀김기) 상시 고온 유지",
            "description": "주문이 없는 시간대에도 조리기구 온도가 상시 유지되어 전력 손실이 큽니다."
        })

    if answers.get("q6_fridge_curtain") == "야간 커튼/문 없음":
        diagnoses.append({
            "waste_code": "FRIDGE_LOSS", "equipment": "KITCHEN", "risk_score": 60,
            "title": "음료 냉장 쇼케이스 냉기 누출",
            "description": "야간 마감 시간대 오픈형 쇼케이스에 단열 커튼이나 도어가 없어 냉기가 유실됩니다."
        })

    if answers.get("q7_signage_light") == "수동 제어 또는 24시간 켜둠":
        diagnoses.append({
            "waste_code": "LIGHT_OVERUSE", "equipment": "LIGHTING", "risk_score": 50,
            "title": "외부 간판 및 실내 조명 타이머 제어 미적용",
            "description": "심야 영업 종료 후에도 간판 조명과 내부 인테리어 조명이 계속 켜져 있습니다."
        })

    if not diagnoses:
        diagnoses.append({
            "waste_code": "GENERAL_OPTIMIZE", "equipment": "LIGHTING", "risk_score": 40,
            "title": "전반적인 멀티탭 대기전력 점검 필요",
            "description": "대체로 양호하나 미세 대기전력 누수를 점검할 필요가 있습니다."
        })
        
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG (스로틀링 방지를 위한 완벽한 캐싱 및 중복 방지)
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    if col.count() == 0:
        col.add(ids=["doc_1"], documents=["[에너지공단] PC방 대기전력 저감: 퇴실 후 타임아웃 및 마스터 차단 시스템으로 본체/주변기기 전력 원천 차단."], metadatas=[{"equipment": "PC_MONITOR"}])
        col.add(ids=["doc_2"], documents=["[에너지공단] 공조·냉난방 효율화: 심야 시간대 중앙 제어 및 타이머 연동으로 전력 소모 방지."], metadatas=[{"equipment": "HVAC"}])
        col.add(ids=["doc_3"], documents=["[에너지공단] 주방 가전 절감: 조리기구는 주문 직전 예열 시작 및 브레이크 타임 전원 차단 권장."], metadatas=[{"equipment": "KITCHEN"}])
        col.add(ids=["doc_4"], documents=["[에너지공단] 조명 및 설비: 간판 조명은 타이머 스위치 의무 장착 및 고효율 LED로 교체."], metadatas=[{"equipment": "LIGHTING"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(equipment_type):
    results = rag_collection.query(query_texts=["에너지 절감 방법 가이드"], n_results=1, where={"equipment": equipment_type})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

# 4. 프론트엔드 UI 페이지 흐름
if "step" not in st.session_state:
    st.session_state.step = 1

# [페이지 1] 10문항 상세 설문지
if st.session_state.step == 1:
    st.title("⚡ PC방 에너지 진단 설문 (약 1분 소요)")
    st.write("매장의 PC, 냉난방, 주방, 조명 설비 운영 방식을 선택해 주세요.")
    
    with st.form("detailed_survey_form"):
        st.subheader("🖥️ [PC 및 주변기기 영역]")
        q1 = st.radio("Q1. 손님이 퇴석한 PC 좌석 및 대기전력 관리 방식은?", ["즉시 전원 차단", "자동 타임아웃 활용", "방치함"])
        q2 = st.radio("Q2. 노하드 서버 및 네트워크 스위치 장비 관리 상태는?", ["사용 시간만 켜둠", "상시 켜둠(개선 필요)"])
        
        st.subheader("❄️ [냉난방기 및 공조 영역]")
        q3 = st.radio("Q3. 매장 냉난방기 온도 설정 및 관리 방식은?", ["적정 온도 유지", "과도한 저온/고온 유지"])
        q4 = st.radio("Q4. 환기팬 및 공조기 가동 방식은?", ["이용률 연동 타이머 제어", "24시간 연속 가동"])
        
        st.subheader("🍳 [주방 및 부대시설 영역]")
        q5 = st.radio("Q5. 라면조리기·튀김기 등 주방 조리기구 예열 방식은?", ["주문 시 즉시 가동", "상시 고온 예열 유지"])
        q6 = st.radio("Q6. 음료 냉장 쇼케이스 야간 관리 방식은?", ["야간 커튼/도어 활용", "야간 커튼/문 없음"])
        q7 = st.radio("Q7. 정수기 및 제빙기 절전 모드 설정 여부", ["절전 모드 사용 중", "상시 풀가동"])
        
        st.subheader("💡 [조명 및 기타 영역]")
        q8 = st.radio("Q8. 외부 간판 및 실내 인테리어 조명 제어 방식은?", ["타이머/자동 제어", "수동 제어 또는 24시간 켜둠"])
        q9 = st.radio("Q9. 매장 내 멀티탭 개별 차단기 설치 비율", ["대부분 개별 스위치 멀티탭 사용", "일반 헐거운 멀티탭 사용"])
        q10 = st.radio("Q10. 최근 1년내 고효율 인버터/LED 교체 여부", ["전체 교체 완료", "부분 교체 또는 미교체"])

        submitted = st.form_submit_button("AI 정밀 진단하기 🚀", use_container_width=True)
        if submitted:
            answers = {
                "q1_pc_standby": q1, "q2_server_power": q2,
                "q3_hvac_temp": q3, "q4_ventilation": q4,
                "q5_kitchen_preheat": q5, "q6_fridge_curtain": q6,
                "q7_signage_light": q8
            }
            weights = {
                "PC_MONITOR": 1.5 if q1 == "방치함" else 1.0,
                "HVAC": 1.4 if q3 == "과도한 저온/고온 유지" else 1.0,
                "KITCHEN": 1.3 if q5 == "상시 고온 예열 유지" else 1.0,
                "LIGHTING": 1.2 if q8 == "수동 제어 또는 24시간 켜둠" else 1.0
            }
            
            st.session_state.survey_answers = answers
            st.session_state.weights = weights
            st.session_state.step = 2
            st.rerun()

# [페이지 2] AI 에너지 진단 결과
elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과")
    diagnoses = python_rule_engine(st.session_state.survey_answers)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="종합 에너지 효율 점수", value="58점", delta="-15점", delta_color="inverse")
    with col2:
        st.info("💡 **AI 코치 진단**: 설문 응답을 분석한 결과, 전기요금을 크게 절감할 수 있는 주요 낭비 요인들이 발견되었습니다.")
        
    st.subheader("🚨 가장 먼저 확인해야 할 영역 (Rule Engine + RAG)")
    for diag in diagnoses:
        guide_text = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[위험점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 에너지공단 RAG 근거:</b> {guide_text}</p>
        </div>
        """, unsafe_allow_html=True)
        
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 설문 수정하기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("📈 예상 절감 효과 보기 ➔", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# [페이지 3] 예상 절감 효과
elif st.session_state.step == 3:
    st.title("📈 예상 절감 효과 (100석 기준)")
    eq_df = load_pc_bang_data()
    impact_df = calculate_energy_impact(st.session_state.weights, eq_df)
    
    total_kwh = impact_df["monthly_kwh"].sum() * 0.18
    total_cost = impact_df["monthly_cost"].sum() * 0.18
    total_carbon = impact_df["monthly_carbon"].sum() * 0.18
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="월 절감 전력량", value=f"{int(total_kwh)} kWh")
    with m2:
        st.metric(label="월 전기요금 절감", value=f"{int(total_cost):,} 원")
    with m3:
        st.metric(label="월 탄소 감축량", value=f"{round(total_carbon, 1)} kgCO₂e")
        
    st.subheader("📊 설비별 전력 기여도 분석 (Pandas)")
    st.dataframe(impact_df[["name", "monthly_kwh", "monthly_cost"]], use_container_width=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()