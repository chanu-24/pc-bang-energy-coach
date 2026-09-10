import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

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
        inefficiency_weight = survey_answers.get(eq, 1.2)
        monthly_kwh = row["rated_power_kw"] * row["default_hours"] * 30 * inefficiency_weight
        monthly_cost = monthly_kwh * KRW_PER_KWH
        monthly_carbon = monthly_kwh * CARBON_FACTOR
        results.append({
            "equipment": eq, "name": row["name"],
            "monthly_kwh": round(monthly_kwh, 2),
            "monthly_cost": round(monthly_cost),
            "monthly_carbon": round(monthly_carbon, 2)
        })
    return pd.DataFrame(results)

def python_rule_engine(survey_answers):
    diagnoses = []
    if survey_answers.get("pc_standby_issue", False):
        diagnoses.append({
            "waste_code": "PC_STANDBY_POWER", "equipment": "PC_MONITOR", "risk_score": 85,
            "title": "퇴석 좌석 PC·모니터 전원 자동 차단 미설정",
            "description": "손님이 없는 좌석의 PC 본체·모니터·헤드셋 노하드 대기전력이 24시간 불필요하게 소비되고 있어요."
        })
    if survey_answers.get("hvac_over_use", False):
        diagnoses.append({
            "waste_code": "HVAC_OVER_USE", "equipment": "HVAC", "risk_score": 70,
            "title": "새벽/야간 시간대 매장 환기·냉난방 과다 가동",
            "description": "손님 이용률이 낮은 시간대에도 동일한 세팅으로 환기·냉난방 에어컨이 가동되고 있어요."
        })
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    col.add(ids=["doc_1"], documents=["PC방 야간 대기전력 저감 방안: 타임아웃 설정 또는 마스터 전원 차단 시스템으로 전력을 원천 차단해야 합니다."], metadatas=[{"equipment": "PC_MONITOR"}])
    col.add(ids=["doc_2"], documents=["냉난방기 효율화: 심야 시간대 중앙 제어 및 타이머를 연동하여 불필요한 전력 소모를 방지합니다."], metadatas=[{"equipment": "HVAC"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(equipment_type):
    results = rag_collection.query(query_texts=["에너지 절감 방법 가이드"], n_results=1, where={"equipment": equipment_type})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

if "step" not in st.session_state:
    st.session_state.step = 1

if st.session_state.step == 1:
    st.title("⚡ 1분 설문으로 실천 가능한 PC방 에너지 절감까지")
    with st.form("survey_form"):
        pc_issue = st.checkbox("손님이 나간 후에도 모니터만 끄거나 켜둔 채 방치되는 좌석이 많다.", value=True)
        hvac_issue = st.checkbox("손님이 적은 새벽 시간대에도 주간과 동일하게 냉난방·환기를 가동한다.", value=True)
        submitted = st.form_submit_button("AI 진단하기 🚀", use_container_width=True)
        if submitted:
            st.session_state.survey_answers = {"pc_standby_issue": pc_issue, "hvac_over_use": hvac_issue, "PC_MONITOR": 1.5 if pc_issue else 1.0, "HVAC": 1.4 if hvac_issue else 1.0}
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과")
    diagnoses = python_rule_engine(st.session_state.survey_answers)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="종합 에너지 효율 점수", value="52점", delta="-18점", delta_color="inverse")
    with col2:
        st.info("💡 전기요금을 크게 줄일 수 있는 낭비 요인을 발견했어요.")
    for diag in diagnoses:
        guide_text = search_rag_guides(diag["equipment"])
        st.markdown(f"""<div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;"><h4>{diag['title']}</h4><p>{diag['description']}</p><p style="color:#047857;"><b>RAG 근거:</b> {guide_text}</p></div>""", unsafe_allow_html=True)
    if st.button("📈 예상 절감 효과 보기 ➔", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    st.title("📈 예상 절감 효과 (100석 기준)")
    eq_df = load_pc_bang_data()
    impact_df = calculate_energy_impact(st.session_state.survey_answers, eq_df)
    total_kwh = impact_df["monthly_kwh"].sum() * 0.15
    total_cost = impact_df["monthly_cost"].sum() * 0.15
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("월 절감 전력량", f"{int(total_kwh)} kWh")
    with m2: st.metric("월 전기요금 절감", f"{int(total_cost):,} 원")
    st.dataframe(impact_df[["name", "monthly_kwh", "monthly_cost"]], use_container_width=True)
    if st.button("🔄 처음으로", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
