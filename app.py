# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: 실제 설문 문항(15문항)과 1:1 매칭되는 5대 설비 스펙 및 계산 파이프라인
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "PC_MONITOR", "name": "💻 PC 및 모니터 (대기전력 관리)", "rated_power_kw": 0.25, "default_hours": 24},
        {"equipment": "HVAC", "name": "❄️ 에어컨 및 환기 설비 (냉방/공조)", "rated_power_kw": 3.5, "default_hours": 10},
        {"equipment": "KITCHEN", "name": "🍳 주방 조리기구 (라면조리기·튀김기)", "rated_power_kw": 2.0, "default_hours": 8},
        {"equipment": "LIGHTING", "name": "💡 매장 조명 설비 (간판/인테리어)", "rated_power_kw": 0.8, "default_hours": 12},
        {"equipment": "ETC", "name": "🔌 기타 부대 설비 (정수기·제빙기·서버)", "rated_power_kw": 0.5, "default_hours": 24}
    ])
    return equipment_df

def calculate_detailed_impact(answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    
    pc_count = answers.get("pc_count", 100)
    op_hours = answers.get("op_hours", 24)
    ac_count = answers.get("ac_count", 4)
    ac_hours = answers.get("ac_hours", 10)
    
    radio_keys = ["q3_idle", "q4_pc_manage", "q5_spec", "q7_monitor", "q9_temp", "q11_filter", "q12_door", "q13_lighting", "q14_light", "q15_kitchen"]
    unknown_count = sum(1 for k in radio_keys if answers.get(k) == "모름")
    unknown_penalty = 1.0 + (unknown_count * 0.1)
    
    before_results = []
    after_results = []
    
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        
        if eq == "PC_MONITOR":
            idle_map = {"0%": 1.0, "1~10%": 1.05, "11~30%": 1.15, "31~50%": 1.3, "51% 이상": 1.4, "모름": 1.4}
            idle_w = idle_map.get(answers.get("q3_idle", "1~10%"), 1.1)
            manage_map = {"자동 절전": 0.9, "자동 종료": 0.9, "직접 종료": 1.0, "모니터만 끔": 1.2, "둘 다 켜둠": 1.4, "모름": 1.4}
            manage_w = manage_map.get(answers.get("q4_pc_manage", "직접 종료"), 1.1)
            
            b_kwh = row["rated_power_kw"] * pc_count * op_hours * 30 * (idle_w * manage_w * unknown_penalty * 0.4)
            a_kwh = b_kwh * 0.75
            
        elif eq == "HVAC":
            temp_map = {"22℃ 이하": 1.3, "23~24℃": 1.1, "25℃": 1.0, "26℃ 이상": 0.9, "모름": 1.3, "미사용": 0.0}
            temp_w = temp_map.get(answers.get("q9_temp", "25℃"), 1.0)
            door_map = {"출입할 때만 열고 닫음": 0.9, "자주 열려있음": 1.2, "계속 열어둠": 1.4, "모름": 1.3, "미사용": 1.0}
            door_w = door_map.get(answers.get("q12_door", "출입할 때만 열고 닫음"), 1.0)
            
            b_kwh = row["rated_power_kw"] * ac_count * ac_hours * 30 * temp_w * door_w * unknown_penalty
            a_kwh = b_kwh * 0.80
            
        elif eq == "KITCHEN":
            kitchen_map = {"주문 시 즉시 가동": 0.9, "상시 고온 예열 유지": 1.3, "모름": 1.2}
            kitchen_w = kitchen_map.get(answers.get("q15_kitchen", "상시 고온 예열 유지"), 1.2)
            
            b_kwh = row["rated_power_kw"] * 2 * 8 * 30 * kitchen_w * unknown_penalty
            a_kwh = b_kwh * 0.80
            
        elif eq == "LIGHTING":
            light_map = {"LED": 0.8, "LED와 일반조명 혼합": 1.1, "형광등·일반조명 중심": 1.4, "모름": 1.3}
            light_w = light_map.get(answers.get("q14_light", "형광등·일반조명 중심"), 1.2)
            
            b_kwh = row["rated_power_kw"] * (pc_count / 25) * 12 * 30 * light_w * unknown_penalty
            a_kwh = b_kwh * 0.80
            
        else: # ETC (기타 부대 설비)
            b_kwh = row["rated_power_kw"] * 5 * 24 * 30 * unknown_penalty
            a_kwh = b_kwh * 0.90

        b_cost = b_kwh * KRW_PER_KWH
        a_cost = a_kwh * KRW_PER_KWH
        b_carbon = b_kwh * CARBON_FACTOR
        a_carbon = a_kwh * CARBON_FACTOR
        
        before_results.append({"equipment": eq, "name": row["name"], "kwh": round(b_kwh, 1), "cost": round(b_cost), "carbon": round(b_carbon, 1)})
        after_results.append({"equipment": eq, "name": row["name"], "kwh": round(a_kwh, 1), "cost": round(a_cost), "carbon": round(a_carbon, 1)})
        
    return pd.DataFrame(before_results), pd.DataFrame(after_results)

# 2. 백엔드: Python Rule Engine
def python_rule_engine(answers):
    diagnoses = []
    
    radio_keys = ["q3_idle", "q4_pc_manage", "q5_spec", "q7_monitor", "q9_temp", "q11_filter", "q12_door", "q13_lighting", "q14_light", "q15_kitchen"]
    unknown_count = sum(1 for k in radio_keys if answers.get(k) == "모름")
    
    if unknown_count > 0:
        diagnoses.append({
            "title": f"⚠️ 매장 전력 사용 실태 파악 심각한 부족 (모름 {unknown_count}개)",
            "description": f"주요 설비 운영 상태를 '모름'({unknown_count}개 항목)으로 응답하셨습니다. 매장의 에너지 낭비 요인을 통제하지 못하고 있어 요금 폭탄 위험이 큽니다!",
            "equipment": "PC_MONITOR", "risk_score": 95 + (unknown_count * 2)
        })

    if answers.get("q4_pc_manage") in ["모니터만 끔", "둘 다 켜둠"]:
        diagnoses.append({
            "title": "손님 없는 빈 좌석의 PC·모니터 전원 방치",
            "description": "빈 좌석에서 본체와 모니터 전원이 계속 켜져 있어 불필요한 대기전력이 소모되고 있습니다.",
            "equipment": "PC_MONITOR", "risk_score": 90
        })
    if answers.get("q9_temp") in ["22℃ 이하", "23~24℃"]:
        diagnoses.append({
            "title": "에어컨 설정 온도 과도 저온 유지",
            "description": "실내 적정 온도(26℃)보다 낮게 설정되어 냉방 전력이 과다하게 소모되고 있습니다.",
            "equipment": "HVAC", "risk_score": 85
        })
    if answers.get("q15_kitchen") == "상시 고온 예열 유지":
        diagnoses.append({
            "title": "주방 조리기구(라면조리기·튀김기) 상시 고온 예열",
            "description": "주문이 없는 시간대에도 조리기구 온도를 높게 유지하여 불필요한 전력 소모가 발생하고 있습니다.",
            "equipment": "KITCHEN", "risk_score": 80
        })
    if answers.get("q12_door") in ["자주 열려있음", "계속 열어둠"]:
        diagnoses.append({
            "title": "냉방 중 출입문 개방으로 인한 냉기 손실",
            "description": "출입문이 열려 있어 냉기가 지속 유실되며 냉방 에어컨 부하가 가중되고 있습니다.",
            "equipment": "HVAC", "risk_score": 75
        })
        
    if not diagnoses:
        diagnoses.append({
            "title": "전반적인 매장 설비 대기전력 점검",
            "description": "현재 양호한 상태이나 미세 전력 누수를 정기적으로 점검하는 것을 권장합니다.",
            "equipment": "PC_MONITOR", "risk_score": 40
        })
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    if col.count() == 0:
        col.add(ids=["doc_1"], documents=["[에너지공단] PC·모니터 절전: 빈 좌석 자동 타임아웃 및 마스터 차단기로 대기전력 원천 차단."], metadatas=[{"equipment": "PC_MONITOR"}])
        col.add(ids=["doc_2"], documents=["[에너지공단] 냉방 효율화: 에어컨 설정온도 26도 유지 및 문 닫고 냉방하기로 전력 손실 방지."], metadatas=[{"equipment": "HVAC"}])
        col.add(ids=["doc_3"], documents=["[에너지공단] 주방 조리기구: 주문 직전 가동 시작 및 브레이크 타임 전원 차단."], metadatas=[{"equipment": "KITCHEN"}])
        col.add(ids=["doc_4"], documents=["[에너지공단] 매장 조명 설비: 미사용 구역 소등 및 고효율 LED 조명 교체."], metadatas=[{"equipment": "LIGHTING"}])
        col.add(ids=["doc_5"], documents=["[에너지공단] 기타 부대 설비: 정수기 및 제빙기 절전 모드 활용."], metadatas=[{"equipment": "ETC"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(eq):
    results = rag_collection.query(query_texts=["에너지 절감 가이드"], n_results=1, where={"equipment": eq})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

# 4. 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {
        "pc_count": 100, "op_hours": 24, "ac_count": 4, "ac_hours": 10,
        "q3_idle": "모름", "q4_pc_manage": "모름", "q5_spec": "모름",
        "q6_power": "모름", "q7_monitor": "모름", "q9_temp": "모름",
        "q11_filter": "모름", "q12_door": "모름",
        "q13_lighting": "모름", "q14_light": "모름", "q15_kitchen": "모름"
    }

# [페이지 1] 15개 전체 설문 입력폼 (라면·튀김기 문항 명확히 포함)
if st.session_state.step == 1:
    st.title("⚡ PC방 에너지 진단 설문 (15개 문항)")
    st.write("매장 운영 상태를 입력하시면 맞춤형 전력 분석이 시작됩니다.")
    
    with st.form("survey_15_full_form"):
        st.subheader("1 매장 운영과 빈 좌석 관리")
        pc_count = st.number_input("1. PC방 좌석은 총 몇 석인가요?", min_value=10, max_value=500, value=st.session_state.answers.get("pc_count", 100), step=10)
        op_hours = st.slider("2. 하루에 몇 시간 영업하시나요?", min_value=1, max_value=24, value=st.session_state.answers.get("op_hours", 24))
        q3_idle = st.radio("3. 영업시간 전체를 평균으로 보면 빈 좌석은 어느 정도인가요?", ["0%", "1~10%", "11~30%", "31~50%", "51% 이상", "모름"])
        q4_pc_manage = st.radio("4. 손님이 없는 좌석의 PC와 모니터는 어떻게 관리하시나요?", ["자동 절전", "자동 종료", "직접 종료", "모니터만 끔", "둘 다 켜둠", "모름"])
        
        st.subheader("2 장비 정보와 냉방 관리")
        q5_spec = st.radio("5. PC 한 대의 주요 사양은 어떻게 되나요?", ["일반형", "중고사양", "고사양", "여러 사양 혼합", "모름"])
        q6_power = st.text_input("6. PC 1 대의 전력 표시값을 알고 계신가요?", value=st.session_state.answers.get("q6_power", "모름"))
        q7_monitor = st.radio("7. 사용 중인 모니터 크기는 어느 정도인가요?", ["24인치 이하", "24인치 초과~27 인치", "27인치 초과~32 인치", "32 인치 초과", "혼합", "모름"])
        ac_count = st.number_input("8. 매장에 설치된 에어컨은 총 몇 대인가요? (없으면 0)", min_value=0, max_value=30, value=st.session_state.answers.get("ac_count", 4))
        q9_temp = st.radio("9. 여름철 에어컨은 보통 몇 ℃로 설정하시나요?", ["22℃ 이하", "23~24℃", "25℃", "26℃ 이상", "모름", "미사용"])
        ac_hours = st.slider("10. 냉방하는 날에는 에어컨을 하루 평균 몇 시간 사용하시나요?", min_value=0, max_value=24, value=st.session_state.answers.get("ac_hours", 10))
        
        st.subheader("3 냉방 습관과 조명 및 주방 조리기구 관리")
        q11_filter = st.radio("11. 에어컨 필터는 얼마나 자주 청소하시나요?", ["2 주 이내", "2 주 초과~1 개월", "1 개월 초과~3 개월", "3 개월 초과", "거의 안 함", "모름"])
        q12_door = st.radio("12. 냉방 중 출입문은 어떻게 관리하시나요?", ["출입할 때만 열고 닫음", "자주 열려있음", "계속 열어둠", "모름", "미사용"])
        q13_lighting = st.radio("13. 손님이 없는 구역의 조명은 어떻게 관리하시나요?", ["구역별로 모두 끔", "일부만 끔", "계속 켜둠", "빈 구역 없음", "모름"])
        q14_light = st.radio("14. 매장 조명은 대부분 어떤 종류인가요?", ["LED", "LED와 일반조명 혼합", "형광등·일반조명 중심", "모름"])
        q15_kitchen = st.radio("15. 주방 조리기구(라면조리기·튀김기)는 평소 어떻게 관리하시나요?", ["주문 시 즉시 가동", "상시 고온 예열 유지", "모름"])

        submitted = st.form_submit_button("AI 정밀 진단하기 🚀", use_container_width=True)
        if submitted:
            st.session_state.answers = {
                "pc_count": pc_count, "op_hours": op_hours,
                "q3_idle": q3_idle, "q4_pc_manage": q4_pc_manage,
                "q5_spec": q5_spec, "q6_power": q6_power,
                "q7_monitor": q7_monitor, "ac_count": ac_count,
                "q9_temp": q9_temp, "ac_hours": ac_hours,
                "q11_filter": q11_filter, "q12_door": q12_door,
                "q13_lighting": q13_lighting, "q14_light": q14_light,
                "q15_kitchen": q15_kitchen
            }
            st.session_state.step = 2
            st.rerun()

# [페이지 2] AI 에너지 진단 결과
elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과")
    diagnoses = python_rule_engine(st.session_state.answers)
    
    radio_keys = ["q3_idle", "q4_pc_manage", "q5_spec", "q7_monitor", "q9_temp", "q11_filter", "q12_door", "q13_lighting", "q14_light", "q15_kitchen"]
    unknown_cnt = sum(1 for k in radio_keys if st.session_state.answers.get(k) == "모름")
    
    base_score = 95 - (unknown_cnt * 6)
    max_risk = max([d["risk_score"] for d in diagnoses]) if diagnoses else 50
    efficiency_score = max(30, int(base_score - (max_risk * 0.3)))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(
            label="종합 에너지 효율 점수", 
            value=f"{efficiency_score}점", 
            delta="🚨 심각한 관리 부실" if efficiency_score < 60 else "우수함",
            delta_color="inverse"
        )
    with col2:
        if unknown_cnt >= 2:
            st.error(f"⚠️ **관리 부실 경고**: '모름' 응답이 {unknown_cnt}개입니다. 전력 사용 현황을 파악하지 못하고 있어 요금 낭비 위험이 극심합니다!")
        else:
            st.info(f"💡 입력하신 **{st.session_state.answers.get('pc_count', 100)}석** 매장의 분석 결과입니다.")
        
    st.subheader("🚨 가장 먼저 확인해야 할 영역 (Rule Engine + RAG)")
    for diag in diagnoses:
        guide = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[위험점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 에너지공단 가이드:</b> {guide}</p>
        </div>
        """, unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 설문 수정하기", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("📈 상세 감액 분석 보기 ➔", use_container_width=True):
            st.session_state.step = 3; st.rerun()

# [페이지 3] 예상 전력절감 및 감액가능 상세 분석
elif st.session_state.step == 3:
    pc_count_val = st.session_state.answers.get("pc_count", 100)
    st.title(f"📈 예상 전력절감 및 감액가능 상세 분석 ({pc_count_val}석 기준)")
    st.write("진단 가이드를 실천할 경우 기대되는 월간 전력절감 및 감액가능 금액 비교입니다.")
    
    eq_df = load_pc_bang_data()
    b_df, a_df = calculate_detailed_impact(st.session_state.answers, eq_df)
    
    tot_b_kwh, tot_a_kwh = b_df["kwh"].sum(), a_df["kwh"].sum()
    tot_b_cost, tot_a_cost = b_df["cost"].sum(), a_df["cost"].sum()
    tot_b_carb, tot_a_carb = b_df["carbon"].sum(), a_df["carbon"].sum()
    
    saved_cost = int(tot_b_cost - tot_a_cost)
    saved_kwh = int(tot_b_kwh - tot_a_kwh)
    saved_carb = round(tot_b_carb - tot_a_carb, 1)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">전력절감 가능량</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_kwh:,} kWh</div>
            <div style="font-size:12px; color:#059669; background-color:#ecfdf5; padding:4px 8px; border-radius:6px; display:inline-block;">기존 {int(tot_b_kwh):,} ➔ {int(tot_a_kwh):,} (절감가능)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">전기요금 감액가능</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_cost:,} 원</div>
            <div style="font-size:12px; color:#059669; background-color:#ecfdf5; padding:4px 8px; border-radius:6px; display:inline-block;">기존 {int(tot_b_cost):,}원 ➔ {int(tot_a_cost):,}원 (감액가능)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">탄소 감축가능량</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_carb} kg</div>
            <div style="font-size:12px; color:#059669; background-color:#ecfdf5; padding:4px 8px; border-radius:6px; display:inline-block;">기존 {round(tot_b_carb, 1)} ➔ {round(tot_a_carb, 1)} (감축가능)</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("🔍 설비별 상세 전력절감 및 감액가능 내역")
    
    for i in range(len(b_df)):
        name = b_df.loc[i, "name"]
        b_kwh, a_kwh = b_df.loc[i, "kwh"], a_df.loc[i, "kwh"]
        b_cost, a_cost = b_df.loc[i, "cost"], a_df.loc[i, "cost"]
        diff_kwh = round(b_kwh - a_kwh, 1)
        diff_cost = int(b_cost - a_cost)
        
        st.markdown(f"""
        <div style="background-color:#f1f5f9; border-left:5px solid #3b82f6; padding:15px; border-radius:8px; margin-bottom:12px;">
            <h4 style="margin:0 0 8px 0; color:#1e293b;">{name}</h4>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>전력절감 가능:</b> <span style="color:#dc2626;">{b_kwh:,.1f} kWh</span> ➔ <span style="color:#16a34a;">{a_kwh:,.1f} kWh</span> (<b>총 {diff_kwh:,.1f} kWh 절감가능</b>)
            </p>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>요금 감액가능:</b> <span style="color:#dc2626;">{b_cost:,} 원</span> ➔ <span style="color:#16a34a;">{a_cost:,} 원</span> (<b>총 {diff_cost:,} 원 감액가능</b>)
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 설비별 비교 요약 테이블")
    comparison_df = pd.DataFrame({
        "설비 부문": b_df["name"],
        "기존 전력": b_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "절감 후 전력": a_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "기존 요금": b_df["cost"].apply(lambda x: f"{x:,} 원"),
        "개선 후 요금": a_df["cost"].apply(lambda x: f"{x:,} 원"),
        "월 감액가능 금액": (b_df["cost"] - b_df["cost"] + (b_df["cost"] - a_df["cost"])).apply(lambda x: f"{int(x):,} 원")
    })
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()