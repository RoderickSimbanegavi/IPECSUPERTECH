# app.py - Complete restored and enhanced version
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64
from PIL import Image as PILImage
import os
import numpy as np

# Page configuration
st.set_page_config(
    page_title="IPEC Health Insurance Regulatory System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .benchmark-card {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin-bottom: 1rem;
    }
    .warning-card {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin-bottom: 1rem;
    }
    .info-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin-bottom: 1rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .compliance-good {
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        display: inline-block;
    }
    .compliance-warning {
        background-color: #ff9800;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        display: inline-block;
    }
    .compliance-poor {
        background-color: #f44336;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        display: inline-block;
    }
    .report-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .kpi-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1a237e;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_database():
    conn = sqlite3.connect('ipec_insurance.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id TEXT,
        claim_number TEXT,
        claim_line TEXT,
        code_type TEXT,
        procedure_code TEXT,
        procedure_description TEXT,
        treatment_date TEXT,
        practice_code TEXT,
        practice_name TEXT,
        discipline TEXT,
        pay_to TEXT,
        assessment_date TEXT,
        date_received TEXT,
        amount_claimed REAL,
        amount_paid REAL,
        shortfall REAL,
        province TEXT,
        facility_type TEXT,
        insurer_id TEXT,
        category TEXT,
        insurer_name TEXT,
        submission_date TEXT,
        quarter INTEGER,
        year INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS insurers (
        insurer_id TEXT PRIMARY KEY,
        insurer_name TEXT,
        registration_date TEXT,
        status TEXT,
        email TEXT,
        plan_types TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mrt_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        procedure_code TEXT,
        procedure_description TEXT,
        minimum_rate REAL,
        recommended_rate REAL,
        effective_date TEXT,
        category TEXT,
        benchmark_percentile INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS communications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        insurer_id TEXT,
        recipient_email TEXT,
        subject TEXT,
        message TEXT,
        sent_date TEXT,
        report_attachment TEXT,
        status TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type TEXT,
        report_period TEXT,
        generated_date TEXT,
        content TEXT
    )''')
    
    # Insert sample insurers
    c.execute("SELECT COUNT(*) FROM insurers")
    if c.fetchone()[0] == 0:
        sample_insurers = [
            ('INS001', 'First Mutual Health', '2020-01-15', 'Active', 'contact@firstmutual.co.zw', 'Essential, Standard, Premier'),
            ('INS002', 'Old Mutual Health', '2020-03-20', 'Active', 'info@oldmutual.co.zw', 'Basic, Plus, Executive'),
            ('INS003', 'Zimre Health', '2020-06-10', 'Active', 'contact@zimre.co.zw', 'Community, Standard, Corporate'),
            ('INS004', 'Nyaradzo Health', '2021-02-01', 'Active', 'info@nyaradzo.com', 'Bronze, Silver, Gold'),
            ('INS005', 'Alliance Health', '2021-08-15', 'Active', 'contact@alliance.co.zw', 'Starter, Family, Premium'),
            ('INS006', 'Digital Allianz', '2022-01-10', 'Active', 'digital@allianz.co.zw', 'Micro, Standard, Plus')
        ]
        c.executemany("INSERT INTO insurers VALUES (?,?,?,?,?,?)", sample_insurers)
    
    # Insert sample MRT rates
    c.execute("SELECT COUNT(*) FROM mrt_rates")
    if c.fetchone()[0] == 0:
        sample_mrt = [
            ('CS-001', 'Caesarean Section', 380.00, 450.00, '2025-01-01', 'Obstetrics', 50),
            ('AP-001', 'Appendectomy', 320.00, 380.00, '2025-01-01', 'Surgery', 50),
            ('ML-001', 'Malaria Treatment (Severe)', 45.00, 60.00, '2025-01-01', 'Infectious Diseases', 50),
            ('GP-001', 'General Consultation', 18.00, 25.00, '2025-01-01', 'General Practice', 50),
            ('SP-001', 'Specialist Consultation', 35.00, 50.00, '2025-01-01', 'Specialist', 50),
            ('XD-001', 'X-Ray (Chest)', 25.00, 35.00, '2025-01-01', 'Diagnostics', 50),
            ('LB-001', 'Full Blood Count', 8.00, 12.00, '2025-01-01', 'Laboratory', 50),
            ('MR-001', 'MRI Scan (Brain)', 180.00, 250.00, '2025-01-01', 'Radiology', 50),
            ('CT-001', 'CT Scan (Abdomen)', 150.00, 200.00, '2025-01-01', 'Radiology', 50),
            ('DENT-001', 'Tooth Extraction', 25.00, 35.00, '2025-01-01', 'Dental', 50)
        ]
        c.executemany("INSERT INTO mrt_rates (procedure_code, procedure_description, minimum_rate, recommended_rate, effective_date, category, benchmark_percentile) VALUES (?,?,?,?,?,?,?)", sample_mrt)
    
    conn.commit()
    conn.close()

# Helper functions
def check_credentials(username, password, user_type):
    if user_type == "insurer":
        return username == "Digital Allianz" and password == "IPECResearch"
    elif user_type == "ipec":
        return username == "Terrence Kamoto" and password == "NDS2"
    return False

def get_claims_data(insurer_id=None):
    conn = sqlite3.connect('ipec_insurance.db')
    if insurer_id:
        df = pd.read_sql_query("SELECT * FROM claims WHERE insurer_id = ?", conn, params=[insurer_id])
    else:
        df = pd.read_sql_query("SELECT * FROM claims", conn)
    conn.close()
    return df

def get_all_claims():
    conn = sqlite3.connect('ipec_insurance.db')
    df = pd.read_sql_query("SELECT * FROM claims", conn)
    conn.close()
    return df

def get_insurers():
    conn = sqlite3.connect('ipec_insurance.db')
    df = pd.read_sql_query("SELECT * FROM insurers", conn)
    conn.close()
    return df

def get_mrt_rates():
    conn = sqlite3.connect('ipec_insurance.db')
    df = pd.read_sql_query("SELECT * FROM mrt_rates", conn)
    conn.close()
    return df

def save_claims_to_db(df, insurer_name):
    conn = sqlite3.connect('ipec_insurance.db')
    cursor = conn.cursor()
    
    insurer_map = {
        'First Mutual Health': 'INS001',
        'Old Mutual Health': 'INS002',
        'Zimre Health': 'INS003',
        'Nyaradzo Health': 'INS004',
        'Alliance Health': 'INS005',
        'Digital Allianz': 'INS006'
    }
    insurer_id = insurer_map.get(insurer_name, 'INS006')
    
    for _, row in df.iterrows():
        treatment_date = pd.to_datetime(row.get('TREATMENT_DATE', datetime.now()))
        quarter = (treatment_date.month - 1) // 3 + 1
        year = treatment_date.year
        
        cursor.execute("""
            INSERT INTO claims (
                member_id, claim_number, claim_line, code_type, procedure_code,
                procedure_description, treatment_date, practice_code, practice_name,
                discipline, pay_to, assessment_date, date_received, amount_claimed,
                amount_paid, shortfall, province, facility_type, insurer_id, category,
                insurer_name, submission_date, quarter, year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get('MEMBER', '')),
            str(row.get('CLAIM', '')),
            str(row.get('CLAIM_LINE', '')),
            str(row.get('CODE_TYPE', '')),
            str(row.get('CODE', '')),
            str(row.get('CODE_DESCRIPTION', '')),
            str(row.get('TREATMENT_DATE', '')),
            str(row.get('PRACTICE', '')),
            str(row.get('PRACTICE_NAME', '')),
            str(row.get('DISCIPLINE', '')),
            str(row.get('PAY_TO', '')),
            str(row.get('ASSESSMENT_DATE', '')),
            str(row.get('DATE_RECEIVED', '')),
            float(row.get('AMOUNT_CLAIMED', 0)),
            float(row.get('AMOUNT_PAID', 0)),
            float(row.get('SHORTFALL', 0)),
            str(row.get('PROVINCE', '')),
            str(row.get('FACILITY_TYPE', '')),
            insurer_id,
            str(row.get('CATEGORY', '')),
            insurer_name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            quarter,
            year
        ))
    conn.commit()
    conn.close()

def calculate_insurer_metrics(df):
    if df.empty:
        return {
            'total_claims': 0,
            'total_amount_paid': 0,
            'total_amount_claimed': 0,
            'avg_payment_ratio': 0,
            'total_shortfall': 0,
            'unique_members': 0,
            'percent_at_benchmark': 0,
            'catastrophic_shortfalls': 0
        }
    
    total_claims = len(df)
    total_paid = df['amount_paid'].sum()
    total_claimed = df['amount_claimed'].sum()
    total_shortfall = df['shortfall'].sum()
    unique_members = df['member_id'].nunique()
    avg_payment_ratio = (total_paid / total_claimed * 100) if total_claimed > 0 else 0
    
    mrt_df = get_mrt_rates()
    benchmark_comparison = []
    for _, row in df.iterrows():
        mrt_row = mrt_df[mrt_df['procedure_code'] == row['procedure_code']]
        if not mrt_row.empty:
            benchmark = mrt_row['recommended_rate'].values[0]
            benchmark_comparison.append(row['amount_paid'] >= benchmark)
    percent_at_benchmark = (sum(benchmark_comparison) / len(benchmark_comparison) * 100) if benchmark_comparison else 0
    
    catastrophic = len(df[df['shortfall'] > df['amount_claimed'] * 0.5]) if not df.empty else 0
    
    return {
        'total_claims': total_claims,
        'total_amount_paid': total_paid,
        'total_amount_claimed': total_claimed,
        'avg_payment_ratio': avg_payment_ratio,
        'total_shortfall': total_shortfall,
        'unique_members': unique_members,
        'percent_at_benchmark': percent_at_benchmark,
        'catastrophic_shortfalls': catastrophic
    }

def calculate_reimbursement_distribution(df, procedure_code):
    """Calculate distribution of reimbursements for a procedure - as per document"""
    proc_df = df[df['procedure_code'] == procedure_code]
    if proc_df.empty:
        return None
    
    return {
        'count': len(proc_df),
        'min': proc_df['amount_paid'].min(),
        'q1': proc_df['amount_paid'].quantile(0.25),
        'median': proc_df['amount_paid'].median(),
        'q3': proc_df['amount_paid'].quantile(0.75),
        'max': proc_df['amount_paid'].max(),
        'mean': proc_df['amount_paid'].mean(),
        'std': proc_df['amount_paid'].std()
    }

def generate_quarterly_report(quarter, year):
    """Generate IPEC Quarterly Reimbursement Transparency Report"""
    conn = sqlite3.connect('ipec_insurance.db')
    df = pd.read_sql_query("SELECT * FROM claims WHERE quarter = ? AND year = ?", conn, params=[quarter, year])
    conn.close()
    
    if df.empty:
        return None
    
    mrt_df = get_mrt_rates()
    
    report = {
        'period': f"Q{quarter} {year}",
        'generated_date': datetime.now().strftime('%Y-%m-%d'),
        'market_statistics': {},
        'insurer_performance': [],
        'procedure_benchmarks': [],
        'provider_flags': []
    }
    
    # Market statistics
    report['market_statistics'] = {
        'total_claims': len(df),
        'total_reimbursed': df['amount_paid'].sum(),
        'total_charged': df['amount_claimed'].sum(),
        'total_shortfall': df['shortfall'].sum(),
        'avg_shortfall_per_claim': df['shortfall'].mean(),
        'catastrophic_shortfalls': len(df[df['shortfall'] > df['amount_claimed'] * 0.5])
    }
    
    # Insurer performance as per document sample output
    for insurer in df['insurer_name'].unique():
        insurer_df = df[df['insurer_name'] == insurer]
        metrics = calculate_insurer_metrics(insurer_df)
        
        # Calculate procedure compliance
        proc_compliance = []
        for proc in mrt_df['procedure_code'].unique():
            proc_df = insurer_df[insurer_df['procedure_code'] == proc]
            mrt_row = mrt_df[mrt_df['procedure_code'] == proc]
            if not proc_df.empty and not mrt_row.empty:
                benchmark = mrt_row['recommended_rate'].values[0]
                compliant = (proc_df['amount_paid'] >= benchmark).mean() * 100
                proc_compliance.append(compliant)
        
        avg_compliance = np.mean(proc_compliance) if proc_compliance else 0
        
        report['insurer_performance'].append({
            'insurer': insurer,
            'total_claims': metrics['total_claims'],
            'percent_at_benchmark': metrics['percent_at_benchmark'],
            'avg_shortfall': metrics['total_shortfall'] / metrics['total_claims'] if metrics['total_claims'] > 0 else 0,
            'catastrophic_shortfalls': metrics['catastrophic_shortfalls'],
            'payment_ratio': metrics['avg_payment_ratio'],
            'compliance_grade': 'A' if avg_compliance >= 80 else 'B' if avg_compliance >= 65 else 'C' if avg_compliance >= 50 else 'D'
        })
    
    # Procedure benchmarks stratified by province and facility type - as per document table
    for proc in mrt_df['procedure_code'].unique():
        proc_df = df[df['procedure_code'] == proc]
        if not proc_df.empty:
            mrt_row = mrt_df[mrt_df['procedure_code'] == proc]
            benchmark = mrt_row['recommended_rate'].values[0] if not mrt_row.empty else None
            
            strat_data = []
            for province in proc_df['province'].unique():
                for facility in proc_df['facility_type'].unique():
                    sub_df = proc_df[(proc_df['province'] == province) & (proc_df['facility_type'] == facility)]
                    if not sub_df.empty:
                        strat_data.append({
                            'Province': province,
                            'Facility Type': facility,
                            'Median Reimbursement': sub_df['amount_paid'].median(),
                            'Benchmark': benchmark,
                            'Shortfall Incidence': (sub_df['shortfall'] > 0).mean() * 100
                        })
            
            report['procedure_benchmarks'].append({
                'procedure_code': proc,
                'procedure_description': mrt_row['procedure_description'].values[0] if not mrt_row.empty else proc,
                'benchmark_rate': benchmark,
                'market_median': proc_df['amount_paid'].median(),
                'stratified_data': strat_data,
                'shortfall_incidence': (proc_df['shortfall'] > 0).mean() * 100
            })
    
    return report

def generate_annual_report(year):
    """Generate IPEC Annual Market Conduct Report"""
    conn = sqlite3.connect('ipec_insurance.db')
    df = pd.read_sql_query("SELECT * FROM claims WHERE year = ?", conn, params=[year])
    conn.close()
    
    if df.empty:
        return None
    
    mrt_df = get_mrt_rates()
    
    report = {
        'year': year,
        'generated_date': datetime.now().strftime('%Y-%m-%d'),
        'executive_summary': {},
        'insurer_rankings': [],
        'quarterly_trends': [],
        'enforcement_actions': [],
        'policy_recommendations': []
    }
    
    # Executive summary
    total_shortfall = df['shortfall'].sum()
    total_claims_value = df['amount_claimed'].sum()
    
    report['executive_summary'] = {
        'total_insurers': df['insurer_name'].nunique(),
        'total_members': df['member_id'].nunique(),
        'total_claims': len(df),
        'total_claims_value': total_claims_value,
        'total_shortfall': total_shortfall,
        'shortfall_percent': (total_shortfall / total_claims_value * 100) if total_claims_value > 0 else 0,
        'catastrophic_shortfalls': len(df[df['shortfall'] > df['amount_claimed'] * 0.5])
    }
    
    # Quarterly trends
    for q in range(1, 5):
        q_df = df[df['quarter'] == q]
        if not q_df.empty:
            compliant = 0
            total = 0
            for _, row in q_df.iterrows():
                mrt_row = mrt_df[mrt_df['procedure_code'] == row['procedure_code']]
                if not mrt_row.empty:
                    total += 1
                    if row['amount_paid'] >= mrt_row['recommended_rate'].values[0]:
                        compliant += 1
            compliance_rate = (compliant / total * 100) if total > 0 else 0
            report['quarterly_trends'].append({
                'quarter': f"Q{q}",
                'claims': len(q_df),
                'compliance_rate': compliance_rate,
                'avg_shortfall': q_df['shortfall'].mean()
            })
    
    # Insurer rankings
    for insurer in df['insurer_name'].unique():
        insurer_df = df[df['insurer_name'] == insurer]
        metrics = calculate_insurer_metrics(insurer_df)
        report['insurer_rankings'].append({
            'insurer': insurer,
            'compliance_rate': metrics['percent_at_benchmark'],
            'avg_shortfall': metrics['total_shortfall'] / metrics['total_claims'] if metrics['total_claims'] > 0 else 0,
            'payment_ratio': metrics['avg_payment_ratio'],
            'grade': 'A' if metrics['percent_at_benchmark'] >= 80 else 'B' if metrics['percent_at_benchmark'] >= 65 else 'C' if metrics['percent_at_benchmark'] >= 50 else 'D'
        })
    
    # Enforcement actions
    report['enforcement_actions'] = [
        {'insurer': 'Old Mutual Health', 'action': 'Formal Warning', 'reason': 'Below-benchmark reimbursement for 35% of claims', 'date': '2025-10-15'},
        {'insurer': 'Zimre Health', 'action': 'Corrective Action Required', 'reason': 'Persistent shortfalls on caesarean sections', 'date': '2025-11-01'}
    ]
    
    # Policy recommendations from document
    report['policy_recommendations'] = [
        "IPEC should adopt the National Reimbursement Benchmark (NRB) as a binding floor for reimbursement",
        "Establish a quarterly Reimbursement Transparency Report as a mandatory publication",
        "Implement automated SupTech monitoring for real-time compliance detection",
        "Create a consumer hotline for reporting catastrophic shortfalls"
    ]
    
    return report

def generate_public_report():
    """Generate public consumer report with out-of-pocket per procedure per insurer"""
    all_claims = get_all_claims()
    mrt_df = get_mrt_rates()
    
    if all_claims.empty:
        return None
    
    report = {
        'generated_date': datetime.now().strftime('%Y-%m-%d'),
        'insurer_rankings': [],
        'procedure_out_of_pocket': []
    }
    
    # Insurer star ratings
    for insurer in all_claims['insurer_name'].unique():
        insurer_df = all_claims[all_claims['insurer_name'] == insurer]
        metrics = calculate_insurer_metrics(insurer_df)
        star_rating = min(5, max(1, int(metrics['percent_at_benchmark'] / 20) + 1))
        
        report['insurer_rankings'].append({
            'Insurer': insurer,
            'Star Rating': star_rating,
            'Percent at Benchmark': f"{metrics['percent_at_benchmark']:.0f}%",
            'Avg Out-of-Pocket': f"${metrics['total_shortfall']/metrics['total_claims']:.2f}" if metrics['total_claims'] > 0 else "$0",
            'Payment Ratio': f"{metrics['avg_payment_ratio']:.0f}%"
        })
    
    # Out-of-pocket per procedure per insurer
    for proc in mrt_df['procedure_code'].unique():
        proc_desc = mrt_df[mrt_df['procedure_code'] == proc]['procedure_description'].values[0]
        for insurer in all_claims['insurer_name'].unique():
            proc_insurer_df = all_claims[(all_claims['procedure_code'] == proc) & (all_claims['insurer_name'] == insurer)]
            if not proc_insurer_df.empty:
                report['procedure_out_of_pocket'].append({
                    'Procedure': proc_desc,
                    'Insurer': insurer,
                    'Avg Out-of-Pocket': f"${proc_insurer_df['shortfall'].mean():.2f}",
                    'Avg Paid': f"${proc_insurer_df['amount_paid'].mean():.2f}",
                    'Claims': len(proc_insurer_df)
                })
    
    return report

def send_report_to_insurer(insurer_name, report_content, subject):
    conn = sqlite3.connect('ipec_insurance.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT insurer_id, email FROM insurers WHERE insurer_name = ?", [insurer_name])
    result = cursor.fetchone()
    
    if result:
        insurer_id, email = result
        cursor.execute("""
            INSERT INTO communications (insurer_id, recipient_email, subject, message, sent_date, report_attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            insurer_id, email, subject,
            f"IPEC Report for {insurer_name}",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            report_content, "Sent"
        ))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

# Login page
def login_page():
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    try:
        if os.path.exists("IPEC logo.png"):
            logo = PILImage.open("IPEC logo.png")
            st.image(logo, width=150)
        elif os.path.exists("IPEC_logo.png"):
            logo = PILImage.open("IPEC_logo.png")
            st.image(logo, width=150)
    except:
        pass
    
    st.markdown("<h1>Insurance and Pensions Commission of Zimbabwe</h1>", unsafe_allow_html=True)
    st.markdown("<h2>National Reimbursement Benchmark (NRB) SuperTech Framework</h2>", unsafe_allow_html=True)
    st.markdown("<p>Regulating Risk Without Controlling Price | Advancing NDS2 Through Insurance Reform</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.subheader("🔐 System Access")
        
        user_type = st.radio("Select User Type", ["🏢 Medical Aid Society Portal", "📋 IPEC Analyst Portal"], horizontal=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            if user_type == "🏢 Medical Aid Society Portal":
                if check_credentials(username, password, "insurer"):
                    st.session_state['logged_in'] = True
                    st.session_state['user_type'] = 'insurer'
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                if check_credentials(username, password, "ipec"):
                    st.session_state['logged_in'] = True
                    st.session_state['user_type'] = 'ipec'
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("---")
        st.caption("© 2026 Insurance and Pensions Commission of Zimbabwe")

# Insurer dashboard
def insurer_dashboard():
    st.markdown('<div class="main-header" style="background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);">', unsafe_allow_html=True)
    st.markdown("<h1>🏢 Medical Aid Society Portal</h1>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Digital Allianz Medical Aid")
        st.markdown(f"**Logged in:** {st.session_state.get('username', '')}")
        
        menu = st.radio("Navigation", ["📤 Submit Claims Data", "📊 My Performance", "💰 National Reimbursement Benchmark", "📨 Communications"])
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
    
    if menu == "📤 Submit Claims Data":
        st.subheader("📤 Submit Claims Data")
        
        st.info("""
        **Submission Guidelines:**
        - Upload CSV or Excel file with claims data
        - Required fields: MEMBER, CLAIM, CODE, CODE_DESCRIPTION, TREATMENT_DATE, PRACTICE_NAME, AMOUNT_CLAIMED, AMOUNT_PAID, SHORTFALL, PROVINCE, FACILITY_TYPE, CATEGORY
        """)
        
        uploaded_file = st.file_uploader("Choose file", type=['csv', 'xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ File loaded! {len(df)} claims found.")
                st.dataframe(df.head(10), use_container_width=True)
                
                if st.button("✅ Submit to IPEC", use_container_width=True):
                    save_claims_to_db(df, "Digital Allianz")
                    st.success("🎉 Claims data successfully submitted!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif menu == "📊 My Performance":
        st.subheader("📊 Performance Dashboard")
        
        df = get_claims_data('INS006')
        
        if df.empty:
            st.info("No claims data available. Please submit your claims data first.")
        else:
            metrics = calculate_insurer_metrics(df)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Claims", f"{metrics['total_claims']:,}")
            with col2:
                st.metric("Total Paid", f"${metrics['total_amount_paid']:,.2f}")
            with col3:
                st.metric("Payment Ratio", f"{metrics['avg_payment_ratio']:.1f}%")
            with col4:
                st.metric("At/Above Benchmark", f"{metrics['percent_at_benchmark']:.0f}%")
            
            st.subheader("Procedure-Level Performance")
            mrt_df = get_mrt_rates()
            
            proc_data = []
            for proc in mrt_df['procedure_code'].unique():
                proc_df = df[df['procedure_code'] == proc]
                mrt_row = mrt_df[mrt_df['procedure_code'] == proc]
                if not proc_df.empty and not mrt_row.empty:
                    benchmark = mrt_row['recommended_rate'].values[0]
                    compliant = (proc_df['amount_paid'] >= benchmark).mean() * 100
                    proc_data.append({
                        'Procedure': proc,
                        'Description': mrt_row['procedure_description'].values[0],
                        'Claims': len(proc_df),
                        'Avg Paid': f"${proc_df['amount_paid'].mean():.2f}",
                        'Benchmark': f"${benchmark:.2f}",
                        'Compliance': f"{compliant:.0f}%"
                    })
            
            st.dataframe(pd.DataFrame(proc_data), use_container_width=True)
    
    elif menu == "💰 National Reimbursement Benchmark":
        st.subheader("💰 National Reimbursement Benchmark (NRB)")
        mrt_df = get_mrt_rates()
        st.dataframe(mrt_df[['procedure_code', 'procedure_description', 'minimum_rate', 'recommended_rate']], use_container_width=True)
    
    elif menu == "📨 Communications":
        st.subheader("📨 Communications from IPEC")
        conn = sqlite3.connect('ipec_insurance.db')
        comms = pd.read_sql_query("SELECT * FROM communications WHERE insurer_id = 'INS006' ORDER BY sent_date DESC", conn)
        conn.close()
        
        if comms.empty:
            st.info("No communications yet.")
        else:
            for _, comm in comms.iterrows():
                with st.expander(f"📧 {comm['subject']} - {comm['sent_date'][:10]}"):
                    st.info(comm['message'])

# IPEC Analyst Dashboard
def ipec_dashboard():
    st.markdown('<div class="main-header" style="background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%);">', unsafe_allow_html=True)
    st.markdown("<h1>📋 IPEC Analyst Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p>SuperTech Regulatory Monitoring | NRB Management | Market Conduct Oversight</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        try:
            if os.path.exists("IPEC logo.png"):
                logo = PILImage.open("IPEC logo.png")
                st.image(logo, width=80)
        except:
            pass
        st.markdown("### IPEC Regulatory System")
        st.markdown(f"**Analyst:** Terrence Kamoto")
        
        menu = st.radio("Navigation", [
            "📊 Dashboard Overview",
            "📈 Insurer Performance Deep Dive",
            "💰 NRB Management",
            "🏥 Provider Overcharging Analysis",
            "📄 Generate Reports",
            "📨 Send Communications",
            "🗄️ Claims Database"
        ])
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
    
    all_claims = get_all_claims()
    insurers = get_insurers()
    mrt_df = get_mrt_rates()
    
    if menu == "📊 Dashboard Overview":
        st.subheader("📊 Regulatory Dashboard Overview")
        
        if all_claims.empty:
            st.warning("No claims data available in the system. Waiting for medical aid society submissions.")
        else:
            # Key metrics - KPI cards
            total_shortfall = all_claims['shortfall'].sum()
            total_claimed = all_claims['amount_claimed'].sum()
            shortfall_pct = (total_shortfall / total_claimed * 100) if total_claimed > 0 else 0
            catastrophic = len(all_claims[all_claims['shortfall'] > all_claims['amount_claimed'] * 0.5])
            
            st.markdown("### Key Performance Indicators")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">{len(all_claims):,}</div>
                    <div class="kpi-label">Total Claims</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">${all_claims['amount_paid'].sum():,.0f}</div>
                    <div class="kpi-label">Total Reimbursed</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">${total_shortfall:,.0f}</div>
                    <div class="kpi-label">Total Shortfall</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">{shortfall_pct:.1f}%</div>
                    <div class="kpi-label">Shortfall as % of Claims</div>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">{catastrophic:,}</div>
                    <div class="kpi-label">Catastrophic Shortfalls</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">{all_claims['insurer_name'].nunique()}</div>
                    <div class="kpi-label">Active Insurers</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-value">{all_claims['member_id'].nunique():,}</div>
                    <div class="kpi-label">Total Members Served</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Geographic Distribution - Bar Chart
            st.markdown("### 📍 Geographic Distribution of Claims")
            province_data = all_claims.groupby('province').agg({
                'amount_paid': 'sum',
                'amount_claimed': 'sum',
                'shortfall': 'sum'
            }).reset_index()
            province_data['payment_ratio'] = (province_data['amount_paid'] / province_data['amount_claimed'] * 100).fillna(0)
            
            fig = px.bar(province_data, x='province', y='amount_paid', 
                        title='Total Reimbursements by Province',
                        color='amount_paid', color_continuous_scale='Blues',
                        text=province_data['amount_paid'].apply(lambda x: f'${x:,.0f}'))
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Shortfall by Province
            fig2 = px.bar(province_data, x='province', y='shortfall',
                         title='Total Shortfall by Province',
                         color='shortfall', color_continuous_scale='Reds',
                         text=province_data['shortfall'].apply(lambda x: f'${x:,.0f}'))
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
            
            # Reimbursement Distribution Table - as per document
            st.markdown("### 📊 Reimbursement Distribution by Procedure (Stratified)")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_proc = st.selectbox("Select Procedure", mrt_df['procedure_code'].unique())
            
            dist = calculate_reimbursement_distribution(all_claims, selected_proc)
            
            if dist:
                # Distribution statistics table
                dist_df = pd.DataFrame([
                    {'Statistic': 'Number of Claims', 'Value': f"{dist['count']:,}"},
                    {'Statistic': 'Minimum Reimbursement', 'Value': f"${dist['min']:.2f}"},
                    {'Statistic': '25th Percentile', 'Value': f"${dist['q1']:.2f}"},
                    {'Statistic': 'Median (50th Percentile)', 'Value': f"${dist['median']:.2f}"},
                    {'Statistic': '75th Percentile', 'Value': f"${dist['q3']:.2f}"},
                    {'Statistic': 'Maximum Reimbursement', 'Value': f"${dist['max']:.2f}"},
                    {'Statistic': 'Mean Reimbursement', 'Value': f"${dist['mean']:.2f}"},
                    {'Statistic': 'Standard Deviation', 'Value': f"${dist['std']:.2f}"}
                ])
                st.dataframe(dist_df, use_container_width=True)
                
                # Stratified by Province and Facility Type - as per document sample output
                st.markdown(f"#### Stratified Analysis: {selected_proc}")
                proc_df = all_claims[all_claims['procedure_code'] == selected_proc]
                
                strat_data = []
                for province in proc_df['province'].unique():
                    for facility in proc_df['facility_type'].unique():
                        sub_df = proc_df[(proc_df['province'] == province) & (proc_df['facility_type'] == facility)]
                        if not sub_df.empty:
                            mrt_row = mrt_df[mrt_df['procedure_code'] == selected_proc]
                            benchmark = mrt_row['recommended_rate'].values[0] if not mrt_row.empty else None
                            strat_data.append({
                                'Province': province,
                                'Facility Type': facility,
                                'Median Reimbursement': f"${sub_df['amount_paid'].median():.2f}",
                                'Benchmark': f"${benchmark:.2f}" if benchmark else "N/A",
                                'Shortfall Incidence': f"{(sub_df['shortfall'] > 0).mean() * 100:.1f}%"
                            })
                
                if strat_data:
                    st.dataframe(pd.DataFrame(strat_data), use_container_width=True)
                    
                    # Distribution histogram
                    fig = px.histogram(proc_df, x='amount_paid', nbins=20,
                                      title=f'Distribution of Reimbursements - {selected_proc}',
                                      labels={'amount_paid': 'Reimbursement Amount (USD)'})
                    fig.add_vline(x=dist['median'], line_dash="dash", line_color="green", 
                                 annotation_text=f"Median: ${dist['median']:.2f}")
                    fig.add_vline(x=dist['q1'], line_dash="dot", line_color="orange", 
                                 annotation_text=f"Q1: ${dist['q1']:.2f}")
                    fig.add_vline(x=dist['q3'], line_dash="dot", line_color="orange", 
                                 annotation_text=f"Q3: ${dist['q3']:.2f}")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Insurer Performance Summary
            st.markdown("### 🏢 Insurer Performance Summary")
            insurer_summary = []
            for insurer in all_claims['insurer_name'].unique():
                insurer_df = all_claims[all_claims['insurer_name'] == insurer]
                metrics = calculate_insurer_metrics(insurer_df)
                insurer_summary.append({
                    'Insurer': insurer,
                    'Claims': metrics['total_claims'],
                    'Paid': f"${metrics['total_amount_paid']:,.0f}",
                    'Shortfall': f"${metrics['total_shortfall']:,.0f}",
                    'Payment Ratio': f"{metrics['avg_payment_ratio']:.0f}%",
                    'At Benchmark': f"{metrics['percent_at_benchmark']:.0f}%",
                    'Catastrophic': metrics['catastrophic_shortfalls']
                })
            
            st.dataframe(pd.DataFrame(insurer_summary), use_container_width=True)
    
    elif menu == "📈 Insurer Performance Deep Dive":
        st.subheader("📈 Insurer Performance Deep Dive Analysis")
        
        if all_claims.empty:
            st.warning("No claims data available.")
        else:
            # Filter controls
            st.markdown("### 🔍 Filter Controls")
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_insurer = st.selectbox("Select Insurer", ["All"] + list(all_claims['insurer_name'].unique()))
            with col2:
                selected_category = st.selectbox("Select Category", ["All"] + list(all_claims['category'].unique()))
            with col3:
                selected_procedure = st.selectbox("Select Procedure", ["All"] + list(mrt_df['procedure_code'].unique()))
            
            # Filter data
            filtered_df = all_claims.copy()
            if selected_insurer != "All":
                filtered_df = filtered_df[filtered_df['insurer_name'] == selected_insurer]
            if selected_category != "All":
                filtered_df = filtered_df[filtered_df['category'] == selected_category]
            if selected_procedure != "All":
                filtered_df = filtered_df[filtered_df['procedure_code'] == selected_procedure]
            
            if filtered_df.empty:
                st.warning("No data matches the selected filters.")
            else:
                # Summary metrics
                st.markdown("### 📊 Summary Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Claims", len(filtered_df))
                with col2:
                    st.metric("Total Paid", f"${filtered_df['amount_paid'].sum():,.2f}")
                with col3:
                    st.metric("Total Shortfall", f"${filtered_df['shortfall'].sum():,.2f}")
                with col4:
                    payment_ratio = (filtered_df['amount_paid'].sum() / filtered_df['amount_claimed'].sum() * 100) if filtered_df['amount_claimed'].sum() > 0 else 0
                    st.metric("Payment Ratio", f"{payment_ratio:.1f}%")
                
                # Shortfall Analysis by Category
                st.markdown("### 💰 Shortfall Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    shortfall_by_category = filtered_df.groupby('category')['shortfall'].sum().reset_index()
                    if not shortfall_by_category.empty:
                        fig = px.bar(shortfall_by_category, x='category', y='shortfall', 
                                    title='Shortfall by Category', color='shortfall',
                                    color_continuous_scale='Reds')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    shortfall_by_province = filtered_df.groupby('province')['shortfall'].sum().reset_index()
                    if not shortfall_by_province.empty:
                        fig = px.bar(shortfall_by_province, x='province', y='shortfall',
                                    title='Shortfall by Province', color='shortfall',
                                    color_continuous_scale='Reds')
                        st.plotly_chart(fig, use_container_width=True)
                
                # Detailed procedure analysis
                st.markdown("### 📋 Detailed Procedure Analysis")
                proc_details = []
                for proc in filtered_df['procedure_code'].unique():
                    proc_df = filtered_df[filtered_df['procedure_code'] == proc]
                    mrt_row = mrt_df[mrt_df['procedure_code'] == proc]
                    if not mrt_row.empty:
                        benchmark = mrt_row['recommended_rate'].values[0]
                        proc_details.append({
                            'Procedure': proc,
                            'Description': mrt_row['procedure_description'].values[0],
                            'Claims': len(proc_df),
                            'Avg Paid': f"${proc_df['amount_paid'].mean():.2f}",
                            'Benchmark': f"${benchmark:.2f}",
                            'Compliance': f"{(proc_df['amount_paid'] >= benchmark).mean() * 100:.0f}%",
                            'Avg Shortfall': f"${proc_df['shortfall'].mean():.2f}"
                        })
                
                st.dataframe(pd.DataFrame(proc_details), use_container_width=True)
                
                # Monthly trend
                st.markdown("### 📅 Monthly Trend Analysis")
                filtered_df['treatment_date'] = pd.to_datetime(filtered_df['treatment_date'])
                monthly = filtered_df.groupby(filtered_df['treatment_date'].dt.to_period('M')).agg({
                    'amount_paid': 'sum',
                    'shortfall': 'sum'
                }).reset_index()
                monthly['treatment_date'] = monthly['treatment_date'].astype(str)
                
                if not monthly.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=monthly['treatment_date'], y=monthly['amount_paid'], 
                                            name='Amount Paid', mode='lines+markers', line=dict(color='green')))
                    fig.add_trace(go.Scatter(x=monthly['treatment_date'], y=monthly['shortfall'], 
                                            name='Shortfall', mode='lines+markers', line=dict(color='red')))
                    fig.update_layout(title='Monthly Trend: Paid vs Shortfall', 
                                     xaxis_title='Month', yaxis_title='Amount (USD)')
                    st.plotly_chart(fig, use_container_width=True)
    
    elif menu == "💰 NRB Management":
        st.subheader("💰 National Reimbursement Benchmark (NRB) Management")
        
        st.markdown("""
        <div class="benchmark-card">
        <h4>📋 Data-Driven Benchmark Setting</h4>
        <p>The NRB is derived from actual claims data submitted by medical aid societies. 
        IPEC can review market distributions and set benchmarks based on observed data.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not all_claims.empty:
            # Data-driven recommendations
            st.subheader("📊 Data-Driven Benchmark Recommendations")
            st.markdown("Based on actual claims data submitted by insurers, here are the recommended benchmarks:")
            
            rec_data = []
            for proc in mrt_df['procedure_code'].unique():
                proc_df = all_claims[all_claims['procedure_code'] == proc]
                mrt_row = mrt_df[mrt_df['procedure_code'] == proc]
                if not proc_df.empty and not mrt_row.empty:
                    market_median = proc_df['amount_paid'].median()
                    market_q1 = proc_df['amount_paid'].quantile(0.25)
                    current_rec = mrt_row['recommended_rate'].values[0]
                    
                    rec_data.append({
                        'Procedure': proc,
                        'Description': mrt_row['procedure_description'].values[0],
                        'Market Median': f"${market_median:.2f}",
                        'Market Q1 (Floor)': f"${market_q1:.2f}",
                        'Current NRB': f"${current_rec:.2f}",
                        'Data-Recommended NRB': f"${market_median:.2f}",
                        'Sample Size': len(proc_df),
                        'Status': '🟢 Aligned' if abs(market_median - current_rec) < 10 else '🟡 Review Needed'
                    })
            
            st.dataframe(pd.DataFrame(rec_data), use_container_width=True)
            
            # Distribution visualization
            st.subheader("📈 Market Distribution Analysis")
            selected_proc = st.selectbox("Select Procedure to Analyze", mrt_df['procedure_code'].unique())
            
            if selected_proc:
                proc_df = all_claims[all_claims['procedure_code'] == selected_proc]
                mrt_row = mrt_df[mrt_df['procedure_code'] == selected_proc]
                
                if not proc_df.empty and not mrt_row.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sample Size", len(proc_df))
                    with col2:
                        st.metric("Market Median", f"${proc_df['amount_paid'].median():.2f}")
                    with col3:
                        st.metric("Current NRB", f"${mrt_row['recommended_rate'].values[0]:.2f}")
                    
                    fig = px.histogram(proc_df, x='amount_paid', nbins=20,
                                      title=f'Reimbursement Distribution - {selected_proc}',
                                      labels={'amount_paid': 'Amount Paid (USD)'})
                    fig.add_vline(x=proc_df['amount_paid'].median(), line_dash="dash", line_color="green",
                                 annotation_text=f"Median: ${proc_df['amount_paid'].median():.2f}")
                    fig.add_vline(x=mrt_row['recommended_rate'].values[0], line_dash="dot", line_color="blue",
                                 annotation_text=f"Current NRB: ${mrt_row['recommended_rate'].values[0]:.2f}")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Current MRT table
        st.subheader("Current NRB Schedule")
        
        cat_filter = st.selectbox("Filter by Category", ["All"] + list(mrt_df['category'].unique()))
        filtered_mrt = mrt_df if cat_filter == "All" else mrt_df[mrt_df['category'] == cat_filter]
        
        st.dataframe(filtered_mrt[['procedure_code', 'procedure_description', 'minimum_rate', 'recommended_rate', 'category']], use_container_width=True)
        
        if st.button("✏️ Edit NRB Rates", use_container_width=True):
            st.session_state['editing_mrt'] = True
        
        if st.session_state.get('editing_mrt', False):
            st.subheader("Edit NRB Rates")
            edited_mrt = st.data_editor(mrt_df[['procedure_code', 'procedure_description', 'minimum_rate', 'recommended_rate', 'category']], 
                                        use_container_width=True, num_rows="dynamic")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    conn = sqlite3.connect('ipec_insurance.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM mrt_rates")
                    for _, row in edited_mrt.iterrows():
                        cursor.execute("""
                            INSERT INTO mrt_rates (procedure_code, procedure_description, minimum_rate, recommended_rate, effective_date, category, benchmark_percentile)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (row['procedure_code'], row['procedure_description'], row['minimum_rate'], row['recommended_rate'], datetime.now().strftime('%Y-%m-%d'), row['category'], 50))
                    conn.commit()
                    conn.close()
                    st.success("✅ NRB rates updated!")
                    st.session_state['editing_mrt'] = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state['editing_mrt'] = False
                    st.rerun()
    
    elif menu == "🏥 Provider Overcharging Analysis":
        st.subheader("🏥 Provider Overcharging Analysis")
        
        st.markdown("""
        <div class="info-card">
        <h4>⚠️ Provider Overcharging Detection</h4>
        <p>This module identifies healthcare providers whose charges consistently exceed the National Reimbursement Benchmark.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if all_claims.empty:
            st.warning("No claims data available.")
        else:
            provider_analysis = []
            for provider in all_claims['practice_name'].unique():
                provider_df = all_claims[all_claims['practice_name'] == provider]
                avg_charge = provider_df['amount_claimed'].mean()
                avg_paid = provider_df['amount_paid'].mean()
                avg_shortfall = provider_df['shortfall'].mean()
                
                # Calculate overcharge rate
                overcharge_count = 0
                total_compared = 0
                for _, row in provider_df.iterrows():
                    mrt_row = mrt_df[mrt_df['procedure_code'] == row['procedure_code']]
                    if not mrt_row.empty:
                        total_compared += 1
                        if row['amount_claimed'] > mrt_row['recommended_rate'].values[0] * 1.3:
                            overcharge_count += 1
                
                overcharge_rate = (overcharge_count / total_compared * 100) if total_compared > 0 else 0
                
                if overcharge_rate > 30:
                    status = "🔴 High Overcharge"
                elif overcharge_rate > 15:
                    status = "🟡 Moderate Overcharge"
                else:
                    status = "🟢 Within Range"
                
                provider_type = provider_df['facility_type'].mode().values[0] if not provider_df.empty else 'Unknown'
                provider_province = provider_df['province'].mode().values[0] if not provider_df.empty else 'Unknown'
                
                provider_analysis.append({
                    'Provider': provider,
                    'Type': provider_type,
                    'Province': provider_province,
                    'Avg Charge': f"${avg_charge:.2f}",
                    'Avg Paid': f"${avg_paid:.2f}",
                    'Avg Shortfall': f"${avg_shortfall:.2f}",
                    'Overcharge Rate': f"{overcharge_rate:.0f}%",
                    'Status': status
                })
            
            provider_df_display = pd.DataFrame(provider_analysis)
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "🔴 High Overcharge", "🟡 Moderate Overcharge", "🟢 Within Range"])
            with col2:
                province_filter = st.selectbox("Filter by Province", ["All"] + list(all_claims['province'].unique()))
            
            filtered_providers = provider_df_display.copy()
            if status_filter != "All":
                filtered_providers = filtered_providers[filtered_providers['Status'] == status_filter]
            if province_filter != "All":
                filtered_providers = filtered_providers[filtered_providers['Province'] == province_filter]
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                high_count = len(provider_df_display[provider_df_display['Status'] == "🔴 High Overcharge"])
                st.metric("High Overcharge Providers", high_count)
            with col2:
                moderate_count = len(provider_df_display[provider_df_display['Status'] == "🟡 Moderate Overcharge"])
                st.metric("Moderate Overcharge Providers", moderate_count)
            with col3:
                compliant_count = len(provider_df_display[provider_df_display['Status'] == "🟢 Within Range"])
                st.metric("Compliant Providers", compliant_count)
            
            # Status distribution pie chart
            status_counts = provider_df_display['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(status_counts, values='Count', names='Status', title='Provider Overcharge Status Distribution',
                        color='Status', color_discrete_map={'🔴 High Overcharge': '#f44336', '🟡 Moderate Overcharge': '#ff9800', '🟢 Within Range': '#4caf50'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Provider details table
            st.subheader("Provider Details")
            st.dataframe(filtered_providers, use_container_width=True)
    
    elif menu == "📄 Generate Reports":
        st.subheader("📄 Generate IPEC Reports")
        
        st.markdown("""
        <div class="benchmark-card">
        <h4>📋 Report Generation Framework</h4>
        <p>As outlined in the research paper, IPEC shall publish:</p>
        <ul>
            <li><strong>Quarterly Reimbursement Transparency Report</strong> - Insurer-specific compliance data, procedure benchmarks, provider flags</li>
            <li><strong>Annual Market Conduct Report</strong> - Comprehensive market analysis, trends, enforcement actions, policy recommendations</li>
            <li><strong>Public Consumer Report</strong> - Easy-to-read format for informal sector and general public</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        report_type = st.selectbox("Report Type", [
            "Quarterly Reimbursement Transparency Report",
            "Annual Market Conduct Report",
            "Public Consumer Report"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            if "Quarterly" in report_type:
                year = st.selectbox("Year", [2025, 2026])
                quarter = st.selectbox("Quarter", [1, 2, 3, 4])
            elif "Annual" in report_type:
                year = st.selectbox("Year", [2025, 2026])
        
        if st.button("🚀 Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                if "Quarterly" in report_type:
                    report = generate_quarterly_report(quarter, year)
                    if report:
                        st.success(f"✅ Quarterly Report Generated - Q{quarter} {year}")
                        
                        st.markdown(f"## IPEC Quarterly Reimbursement Transparency Report")
                        st.markdown(f"**Period:** Q{quarter} {year}")
                        st.markdown(f"**Generated:** {report['generated_date']}")
                        st.markdown("---")
                        
                        # Market Statistics
                        st.markdown("### Market Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Claims", f"{report['market_statistics']['total_claims']:,}")
                        with col2:
                            st.metric("Total Shortfall", f"${report['market_statistics']['total_shortfall']:,.2f}")
                        with col3:
                            st.metric("Catastrophic Shortfalls", report['market_statistics']['catastrophic_shortfalls'])
                        with col4:
                            avg_shortfall = report['market_statistics']['avg_shortfall_per_claim']
                            st.metric("Avg Shortfall per Claim", f"${avg_shortfall:.2f}")
                        
                        # Insurer Performance Table - as per document sample
                        st.markdown("### Insurer Performance Summary")
                        st.dataframe(pd.DataFrame(report['insurer_performance']), use_container_width=True)
                        
                        # Procedure Benchmarks - as per document table
                        st.markdown("### Procedure Benchmarks (Stratified by Province & Facility Type)")
                        for proc in report['procedure_benchmarks'][:3]:
                            st.markdown(f"#### {proc['procedure_code']} - {proc['procedure_description']}")
                            st.markdown(f"**Benchmark Rate:** ${proc['benchmark_rate']:.2f} | **Market Median:** ${proc['market_median']:.2f} | **Shortfall Incidence:** {proc['shortfall_incidence']:.1f}%")
                            if proc['stratified_data']:
                                strat_df = pd.DataFrame(proc['stratified_data'])
                                st.dataframe(strat_df, use_container_width=True)
                        
                        # Export option
                        csv_data = pd.DataFrame(report['insurer_performance']).to_csv(index=False)
                        st.download_button("📥 Download Report as CSV", csv_data, f"IPEC_Quarterly_Q{quarter}_{year}.csv", "text/csv")
                    else:
                        st.warning("No data available for the selected period")
                
                elif "Annual" in report_type:
                    report = generate_annual_report(year)
                    if report:
                        st.success(f"✅ Annual Market Conduct Report Generated - {year}")
                        
                        st.markdown(f"## IPEC Annual Market Conduct Report")
                        st.markdown(f"**Year:** {year}")
                        st.markdown(f"**Generated:** {report['generated_date']}")
                        st.markdown("---")
                        
                        # Executive Summary
                        st.markdown("### Executive Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Insurers", report['executive_summary']['total_insurers'])
                            st.metric("Total Members", f"{report['executive_summary']['total_members']:,}")
                        with col2:
                            st.metric("Total Claims Value", f"${report['executive_summary']['total_claims_value']:,.2f}")
                            st.metric("Total Shortfall", f"${report['executive_summary']['total_shortfall']:,.2f}")
                        with col3:
                            st.metric("Shortfall %", f"{report['executive_summary']['shortfall_percent']:.1f}%")
                            st.metric("Catastrophic Claims", report['executive_summary']['catastrophic_shortfalls'])
                        
                        # Quarterly Trends
                        st.markdown("### Quarterly Trends")
                        trend_df = pd.DataFrame(report['quarterly_trends'])
                        fig = px.line(trend_df, x='quarter', y='compliance_rate', title='Quarterly Compliance Trend')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Insurer Rankings
                        st.markdown("### Insurer Rankings & Grades")
                        st.dataframe(pd.DataFrame(report['insurer_rankings']), use_container_width=True)
                        
                        # Enforcement Actions
                        st.markdown("### Enforcement Actions")
                        st.dataframe(pd.DataFrame(report['enforcement_actions']), use_container_width=True)
                        
                        # Policy Recommendations
                        st.markdown("### Policy Recommendations")
                        for rec in report['policy_recommendations']:
                            st.markdown(f"- {rec}")
                        
                        csv_data = pd.DataFrame(report['insurer_rankings']).to_csv(index=False)
                        st.download_button("📥 Download Report as CSV", csv_data, f"IPEC_Annual_{year}.csv", "text/csv")
                    else:
                        st.warning("No data available for the selected year")
                
                else:  # Public Consumer Report
                    report = generate_public_report()
                    if report:
                        st.success(f"✅ Public Consumer Report Generated")
                        
                        st.markdown(f"## Consumer Guide to Health Insurance")
                        st.markdown(f"**Published:** {report['generated_date']}")
                        st.markdown("---")
                        
                        # Insurer Star Ratings
                        st.markdown("### 🌟 Insurer Star Ratings")
                        for insurer in report['insurer_rankings']:
                            stars = "⭐" * insurer['Star Rating']
                            st.markdown(f"**{insurer['Insurer']}** {stars}")
                            st.markdown(f"- Pays at benchmark: {insurer['Percent at Benchmark']}")
                            st.markdown(f"- Average out-of-pocket: {insurer['Avg Out-of-Pocket']}")
                            st.markdown("---")
                        
                        # Out-of-pocket per procedure per insurer
                        st.markdown("### 💰 Expected Out-of-Pocket by Procedure and Insurer")
                        st.markdown("This table shows what you can expect to pay out-of-pocket for common procedures with each insurer:")
                        oop_df = pd.DataFrame(report['procedure_out_of_pocket'])
                        if not oop_df.empty:
                            st.dataframe(oop_df, use_container_width=True)
                        
                        # Export options
                        csv_data = pd.DataFrame(report['insurer_rankings']).to_csv(index=False)
                        st.download_button("📥 Download Insurer Rankings as CSV", csv_data, "IPEC_Public_Report_Insurers.csv", "text/csv")
                        
                        csv_oop = pd.DataFrame(report['procedure_out_of_pocket']).to_csv(index=False)
                        st.download_button("📥 Download Out-of-Pocket Data as CSV", csv_oop, "IPEC_Public_Report_OOP.csv", "text/csv")
                    else:
                        st.warning("No data available")
    
    elif menu == "📨 Send Communications":
        st.subheader("📨 Send Communications to Medical Aid Societies")
        
        insurers_list = get_insurers()
        
        if insurers_list.empty:
            st.warning("No insurers found in database")
        else:
            col1, col2 = st.columns(2)
            with col1:
                recipient = st.selectbox("Select Medical Aid Society", insurers_list['insurer_name'].tolist())
                subject = st.text_input("Subject", "IPEC Regulatory Notice")
            with col2:
                priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])
            
            message = st.text_area("Message Content", height=200)
            
            if st.button("📤 Send Communication", use_container_width=True):
                if send_report_to_insurer(recipient, message, subject):
                    st.success(f"✅ Communication sent to {recipient}")
                    st.balloons()
                else:
                    st.error("Failed to send communication")
    
    elif menu == "🗄️ Claims Database":
        st.subheader("🗄️ Claims Database - Regulatory Oversight")
        
        if all_claims.empty:
            st.warning("No claims data in database")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                insurer_filter = st.selectbox("Filter by Insurer", ["All"] + list(all_claims['insurer_name'].unique()))
            with col2:
                province_filter = st.selectbox("Filter by Province", ["All"] + list(all_claims['province'].unique()))
            with col3:
                category_filter = st.selectbox("Filter by Category", ["All"] + list(all_claims['category'].unique()))
            
            filtered_df = all_claims.copy()
            if insurer_filter != "All":
                filtered_df = filtered_df[filtered_df['insurer_name'] == insurer_filter]
            if province_filter != "All":
                filtered_df = filtered_df[filtered_df['province'] == province_filter]
            if category_filter != "All":
                filtered_df = filtered_df[filtered_df['category'] == category_filter]
            
            st.metric("Displaying Claims", len(filtered_df))
            st.dataframe(filtered_df, use_container_width=True, height=400)
            
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="ipec_claims_export.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)

def main():
    init_database()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['editing_mrt'] = False
    
    if not st.session_state['logged_in']:
        login_page()
    else:
        if st.session_state['user_type'] == 'insurer':
            insurer_dashboard()
        else:
            ipec_dashboard()

if __name__ == "__main__":
    main()