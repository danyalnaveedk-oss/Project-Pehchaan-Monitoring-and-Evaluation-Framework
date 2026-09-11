import sqlite3
from datetime import date
import pandas as pd
import streamlit as st
import os

# 1. UI Configuration & Apple Native CSS
st.set_page_config(page_title="Project Pehchaan", layout="wide")

st.markdown("""
    <style>
    /* System Font Enforcement */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    
    /* Hide the default sidebar completely */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    
    /* Clean typography */
    h1, h2, h3 { 
        font-weight: 600; 
        letter-spacing: -0.03em; 
        color: #0A2540;
    }
    
    /* Native iOS Card Styling */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E5EA;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
    }
    
    div[data-testid="stForm"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E5EA;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
    }
    
    /* Navy Blue Action Buttons */
    button[kind="primary"], button[kind="formSubmit"] {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        border: none !important;
        border-radius: 8px;
        transition: transform 0.2s ease, opacity 0.2s ease;
    }
    button[kind="primary"]:hover, button[kind="formSubmit"]:hover {
        opacity: 0.9;
        transform: scale(0.98);
    }
    
    /* Tab Styling */
    button[data-baseweb="tab"] {
        font-weight: 500;
        color: #8E8E93;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0A2540;
    }
    
    /* Minimalist inputs */
    input, select, .stSelectbox {
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Database Initialization
DB_FILE = "pehchaan_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS blocks 
                 (block_id TEXT PRIMARY KEY, location TEXT, status TEXT, init_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS coordinators 
                 (coord_id TEXT PRIMARY KEY, name TEXT, block_id TEXT, phone TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS lead_mothers 
                 (lm_id TEXT PRIMARY KEY, block_id TEXT, name TEXT, status TEXT, tapes INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS patients 
                 (patient_id TEXT PRIMARY KEY, block_id TEXT, lm_id TEXT, muac_zone TEXT, 
                  clinic TEXT, arrival TEXT, diagnosis TEXT, treatment TEXT, followup TEXT, outcome TEXT)""")
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect(DB_FILE)

# 3. Global Header with Logo Integration
col1, col2, col3 = st.columns([1, 4, 2])
with col1:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=80)
    elif os.path.exists("image_353947.jpg"):
        st.image("image_353947.jpg", width=80)
with col2:
    st.write("")
    st.title("Project Pehchaan")
with col3:
    st.write("")
    st.write("")
    role = st.selectbox("System Access Level", ["Block Coordinator", "Team Pehchaan"])

st.markdown("---")

# =====================================================================
# INTERFACE A: BLOCK COORDINATOR
# =====================================================================
if role == "Block Coordinator":
    
    conn = get_connection()
    active_blocks = pd.read_sql_query("SELECT block_id FROM blocks WHERE status = 'Active'", conn)
    conn.close()
    
    if active_blocks.empty:
        st.warning("No Active Blocks available. Contact Team Pehchaan for deployment.")
    else:
        current_block = st.selectbox("Assigned Operating Block", active_blocks["block_id"].tolist())
        st.write("")
        
        tab_child, tab_lm, tab_followup = st.tabs(["Child Referrals", "Lead Mothers", "Follow-up Tracker"])
        
        # --- TAB 1: CHILD STATUS ---
        with tab_child:
            colA, colB = st.columns(2)
            with colA:
                st.subheader("Log Detection")
                with st.form("new_case_form", clear_on_submit=True):
                    p_id = st.text_input("Patient ID")
                    lm_id = st.text_input("Lead Mother ID")
                    zone = st.radio("MUAC Zone", ["Red (<11.5cm)", "Yellow (11.5-12.5cm)"], horizontal=True)
                    clinic = st.selectbox("Referral Clinic", ["SINA", "ZMT", "MERF", "PPHI"])
                    if st.form_submit_button("Submit Record"):
                        if p_id and lm_id:
                            clean_zone = "Red" if "Red" in zone else "Yellow"
                            conn = get_connection()
                            try:
                                conn.execute("INSERT INTO patients (patient_id, block_id, lm_id, muac_zone, clinic, arrival, diagnosis, treatment, followup, outcome) VALUES (?, ?, ?, ?, ?, 'Pending', 'Pending', 'Pending', 'Pending', 'Active')", 
                                            (p_id, current_block, lm_id, clean_zone, clinic))
                                conn.commit()
                                st.success("Record submitted successfully.")
                            except sqlite3.IntegrityError:
                                st.error("Patient ID already exists.")
                            finally:
                                conn.close()
            with colB:
                st.subheader("Confirm Arrival")
                conn = get_connection()
                pending_arrivals = pd.read_sql_query(f"SELECT patient_id, clinic FROM patients WHERE block_id = '{current_block}' AND arrival = 'Pending'", conn)
                conn.close()
                if not pending_arrivals.empty:
                    with st.form("update_arrival_form"):
                        sel_p = st.selectbox("Pending Patients", pending_arrivals["patient_id"])
                        arr_status = st.radio("Status", ["Pending", "Confirmed"], horizontal=True)
                        if st.form_submit_button("Update"):
                            conn = get_connection()
                            conn.execute("UPDATE patients SET arrival = ? WHERE patient_id = ?", (arr_status, sel_p))
                            conn.commit()
                            conn.close()
                            st.success("Status updated.")
                else:
                    st.info("No pending arrivals at this time.")

        # --- TAB 2: LEAD MOTHER STATUS ---
        with tab_lm:
            st.subheader("Lead Mother Roster")
            conn = get_connection()
            lms = pd.read_sql_query(f"SELECT lm_id as 'ID', name as 'Name', status as 'Status', tapes as 'Tapes' FROM lead_mothers WHERE block_id = '{current_block}'", conn)
            conn.close()
            
            if not lms.empty:
                st.dataframe(lms, use_container_width=True, hide_index=True)
                with st.expander("Modify Status"):
                    with st.form("update_lm"):
                        sel_lm = st.selectbox("Select ID", lms["ID"])
                        new_status = st.selectbox("Status Update", ["Active", "Inactive", "Requires Refresher"])
                        if st.form_submit_button("Save Changes"):
                            conn = get_connection()
                            conn.execute("UPDATE lead_mothers SET status = ? WHERE lm_id = ?", (new_status, sel_lm))
                            conn.commit()
                            conn.close()
                            st.success("Record modified.")
            else:
                st.info("No data available for this block.")

        # --- TAB 3: FOLLOW-UP STATUS ---
        with tab_followup:
            st.subheader("Patient Follow-ups")
            conn = get_connection()
            active_patients = pd.read_sql_query(f"SELECT patient_id as 'Patient ID', muac_zone as 'Zone', clinic as 'Clinic', followup as 'Follow-up', outcome as 'Outcome' FROM patients WHERE block_id = '{current_block}'", conn)
            conn.close()
            
            if not active_patients.empty:
                st.dataframe(active_patients, use_container_width=True, hide_index=True)
                with st.form("update_followup"):
                    c_pat = st.selectbox("Target Patient ID", active_patients["Patient ID"])
                    c1, c2 = st.columns(2)
                    n_followup = c1.selectbox("Protocol Stage", ["Pending", "Scheduled", "14-Day Attended", "Defaulter"])
                    n_outcome = c2.selectbox("Clinical Outcome", ["Active Treatment", "Recovered", "Hospital Escalation"])
                    if st.form_submit_button("Update Record"):
                        conn = get_connection()
                        conn.execute("UPDATE patients SET followup = ?, outcome = ? WHERE patient_id = ?", (n_followup, n_outcome, c_pat))
                        conn.commit()
                        conn.close()
                        st.success("Record updated successfully.")
            else:
                st.info("No active patient follow-ups.")


# =====================================================================
# INTERFACE B: TEAM PEHCHAAN (ADMIN)
# =====================================================================
elif role == "Team Pehchaan":
    
    t_dash, t_blocks, t_coords, t_lms, t_clinical = st.tabs([
        "Overview", 
        "Network Blocks", 
        "Coordinators", 
        "Lead Mothers", 
        "Clinical Data"
    ])
    
    # --- TAB 1: DASHBOARD ---
    with t_dash:
        conn = get_connection()
        total_p = pd.read_sql_query("SELECT COUNT(*) as c FROM patients", conn).iloc[0]['c']
        arr_p = pd.read_sql_query("SELECT COUNT(*) as c FROM patients WHERE arrival = 'Confirmed'", conn).iloc[0]['c']
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Referrals", total_p)
        c2.metric("Confirmed Arrivals", arr_p)
        c3.metric("System Conversion", f"{round((arr_p/total_p)*100, 1) if total_p > 0 else 0}%")

    # --- TAB 2: LIVE BLOCKS ---
    with t_blocks:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Initialize Block")
            with st.form("new_block"):
                b_id = st.text_input("Identifier (e.g., BLK-01)")
                b_loc = st.text_input("Geographic Location")
                if st.form_submit_button("Deploy Block"):
                    conn = get_connection()
                    try:
                        conn.execute("INSERT INTO blocks VALUES (?, ?, 'Active', ?)", (b_id, b_loc, str(date.today())))
                        conn.commit()
                        st.success("Deployment successful.")
                    except sqlite3.IntegrityError:
                        st.error("Identifier already exists.")
                    finally:
                        conn.close()
        with col2:
            st.subheader("Network Status")
            conn = get_connection()
            blocks_df = pd.read_sql_query("SELECT block_id as 'Block', location as 'Location', status as 'Status', init_date as 'Deployed' FROM blocks", conn)
            if not blocks_df.empty:
                st.dataframe(blocks_df, use_container_width=True, hide_index=True)
                with st.expander("Modify Block Status"):
                    with st.form("edit_block"):
                        e_b = st.selectbox("Select Block", blocks_df["Block"])
                        e_stat = st.radio("System Status", ["Active", "Completed", "Suspended"], horizontal=True)
                        if st.form_submit_button("Save"):
                            conn.execute("UPDATE blocks SET status = ? WHERE block_id = ?", (e_stat, e_b))
                            conn.commit()
                            st.success("Configuration saved.")
            else:
                st.info("No active blocks in the network.")
            conn.close()

    # --- TAB 3: COORDINATORS ---
    with t_coords:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Onboard Personnel")
            conn = get_connection()
            avail_blocks = pd.read_sql_query("SELECT block_id FROM blocks WHERE status = 'Active'", conn)
            with st.form("new_coord"):
                c_id = st.text_input("ID")
                c_name = st.text_input("Full Name")
                c_phone = st.text_input("Contact Number")
                c_block = st.selectbox("Block Assignment", avail_blocks["block_id"] if not avail_blocks.empty else ["N/A"])
                if st.form_submit_button("Provision Access") and not avail_blocks.empty:
                    try:
                        conn.execute("INSERT INTO coordinators VALUES (?, ?, ?, ?, 'Active')", (c_id, c_name, c_block, c_phone))
                        conn.commit()
                        st.success("Personnel provisioned.")
                    except sqlite3.IntegrityError:
                        st.error("ID already exists.")
            conn.close()
        with col2:
            st.subheader("Active Roster")
            conn = get_connection()
            coords_df = pd.read_sql_query("SELECT coord_id as 'ID', name as 'Name', block_id as 'Block', phone as 'Contact', status as 'Status' FROM coordinators", conn)
            if not coords_df.empty:
                st.dataframe(coords_df, use_container_width=True, hide_index=True)
                with st.expander("Revoke Access"):
                    with st.form("del_coord"):
                        del_c = st.selectbox("Select ID", coords_df["ID"])
                        if st.form_submit_button("Remove"):
                            conn.execute("DELETE FROM coordinators WHERE coord_id = ?", (del_c,))
                            conn.commit()
                            st.success("Access revoked.")
            conn.close()

    # --- TAB 4: LEAD MOTHERS ---
    with t_lms:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Registration")
            conn = get_connection()
            avail_blocks = pd.read_sql_query("SELECT block_id FROM blocks WHERE status = 'Active'", conn)
            with st.form("new_lm"):
                l_id = st.text_input("ID")
                l_name = st.text_input("Full Name")
                l_block = st.selectbox("Block Assignment", avail_blocks["block_id"] if not avail_blocks.empty else ["N/A"])
                l_tapes = st.number_input("Issued Assets (MUAC)", min_value=1, value=10)
                if st.form_submit_button("Register Entity"):
                    try:
                        conn.execute("INSERT INTO lead_mothers VALUES (?, ?, ?, 'Active', ?)", (l_id, l_block, l_name, l_tapes))
                        conn.commit()
                        st.success("Entity registered.")
                    except sqlite3.IntegrityError:
                        st.error("ID already exists.")
            conn.close()
        with col2:
            st.subheader("Database")
            conn = get_connection()
            lms_df = pd.read_sql_query("SELECT lm_id as 'ID', block_id as 'Block', name as 'Name', status as 'Status', tapes as 'Assets' FROM lead_mothers", conn)
            st.dataframe(lms_df, use_container_width=True, hide_index=True)
            conn.close()

    # --- TAB 5: CLINICAL OVERRIDES ---
    with t_clinical:
        st.subheader("Medical Records")
        conn = get_connection()
        p_df = pd.read_sql_query("SELECT patient_id as 'Patient ID', block_id as 'Block', muac_zone as 'Zone', clinic as 'Clinic', arrival as 'Arrival', diagnosis as 'Diagnosis', treatment as 'Treatment', followup as 'Follow-up', outcome as 'Outcome' FROM patients", conn)
        st.dataframe(p_df, use_container_width=True, hide_index=True)
        
        if not p_df.empty:
            with st.expander("Override Clinical Data"):
                with st.form("clinical_override"):
                    colA, colB = st.columns(2)
                    sel_pat = colA.selectbox("Target Patient ID", p_df["Patient ID"])
                    new_diag = colB.selectbox("Diagnosis", ["Severe Wasting", "Moderate Wasting", "False Positive"])
                    
                    colC, colD = st.columns(2)
                    new_treat = colC.selectbox("Treatment", ["RUTF", "MNP", "Hospital Transfer", "None"])
                    new_out = colD.selectbox("Final Outcome", ["Active", "Recovered", "Defaulter"])
                    
                    if st.form_submit_button("Commit Changes"):
                        conn.execute("UPDATE patients SET diagnosis = ?, treatment = ?, outcome = ? WHERE patient_id = ?", 
                                     (new_diag, new_treat, new_out, sel_pat))
                        conn.commit()
                        st.success("Changes committed to database.")
        conn.close()
