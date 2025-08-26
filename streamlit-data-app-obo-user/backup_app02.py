"""
Banking RM Dashboard v2.0
Advanced Relationship Manager Dashboard with comprehensive banking features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import os
from databricks.sdk import WorkspaceClient
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="RM Dashboard v2.0",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css():
    css_file = "styles.css"
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file '{css_file}' not found. Using default styling.")

load_css()

# Initialize session state
def initialize_session_state():
    if 'current_rm' not in st.session_state:
        st.session_state.current_rm = {
            'name': 'Arjun Mehta',
            'employee_id': 'RM001234',
            'branch': 'Mumbai Central',
            'region': 'West Mumbai',
            'clients_assigned': 87,
            'aum_target': 25000000,
            'current_aum': 21500000
        }
    
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Summary"
        
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your RM Assistant. I can help you with client data, portfolio analysis, compliance queries, and task management. How can I assist you today?"}
        ]

# Sample data functions
def get_priority_actions():
    return [
        {"priority": "High", "action": "Follow up with Rajesh Sharma - FD maturity tomorrow", "due": "Today", "client": "Rajesh Sharma"},
        {"priority": "High", "action": "KYC renewal required for Priya Patel", "due": "2 days", "client": "Priya Patel"},
        {"priority": "Medium", "action": "Investment proposal review - Amit Singh", "due": "3 days", "client": "Amit Singh"},
        {"priority": "Medium", "action": "Credit card limit increase request", "due": "1 week", "client": "Neha Gupta"},
        {"priority": "Low", "action": "Annual portfolio review scheduling", "due": "2 weeks", "client": "Multiple"}
    ]

def get_alerts():
    return [
        {"type": "Compliance", "message": "3 KYC renewals pending", "severity": "High"},
        {"type": "Risk", "message": "2 clients exceeded transaction limits", "severity": "Medium"},
        {"type": "Opportunity", "message": "5 clients with idle cash > ₹5L", "severity": "Medium"},
        {"type": "Service", "message": "4 pending service requests", "severity": "Low"}
    ]

def get_portfolio_summary():
    return {
        "total_aum": 21500000,
        "target_aum": 25000000,
        "casa_balance": 8500000,
        "fd_balance": 6200000,
        "investment_balance": 4800000,
        "loan_portfolio": 2000000,
        "new_acquisitions": 1250000,
        "client_count": 87
    }

def get_client_portfolio_data():
    return pd.DataFrame([
        {"Client Name": "Rajesh Kumar Sharma", "Client ID": "CL001234", "AUM": 4500000, "CASA": 245000, "FD": 1500000, "Investments": 2200000, "Loans": 555000, "Risk Profile": "Moderate", "Last Activity": "2 days ago"},
        {"Client Name": "Priya Patel", "Client ID": "CL001235", "AUM": 3200000, "CASA": 180000, "FD": 1200000, "Investments": 1500000, "Loans": 320000, "Risk Profile": "Conservative", "Last Activity": "5 days ago"},
        {"Client Name": "Amit Singh", "Client ID": "CL001236", "AUM": 2800000, "CASA": 320000, "FD": 800000, "Investments": 1400000, "Loans": 280000, "Risk Profile": "Aggressive", "Last Activity": "1 day ago"},
        {"Client Name": "Neha Gupta", "Client ID": "CL001237", "AUM": 2100000, "CASA": 150000, "FD": 600000, "Investments": 1100000, "Loans": 250000, "Risk Profile": "Moderate", "Last Activity": "3 days ago"},
        {"Client Name": "Vikram Joshi", "Client ID": "CL001238", "AUM": 1900000, "CASA": 290000, "FD": 500000, "Investments": 900000, "Loans": 210000, "Risk Profile": "Conservative", "Last Activity": "1 week ago"}
    ])

def get_interaction_data():
    return pd.DataFrame([
        {"Date": "2024-03-15", "Client": "Rajesh Sharma", "Type": "Meeting", "Subject": "Portfolio Review", "Status": "Completed", "Next Action": "FD Renewal Proposal", "Due Date": "2024-03-20"},
        {"Date": "2024-03-14", "Client": "Priya Patel", "Type": "Call", "Subject": "KYC Renewal", "Status": "Pending", "Next Action": "Document Collection", "Due Date": "2024-03-16"},
        {"Date": "2024-03-13", "Client": "Amit Singh", "Type": "Email", "Subject": "Investment Opportunity", "Status": "Follow-up", "Next Action": "Proposal Presentation", "Due Date": "2024-03-18"},
        {"Date": "2024-03-12", "Client": "Neha Gupta", "Type": "WhatsApp", "Subject": "Credit Limit Increase", "Status": "In Progress", "Next Action": "Credit Assessment", "Due Date": "2024-03-22"}
    ])

def get_crosssell_opportunities():
    return pd.DataFrame([
        {"Client": "Rajesh Sharma", "Current Product": "Savings + FD", "Opportunity": "Mutual Fund SIP", "Potential Value": "₹25,000/month", "Probability": "High", "Reason": "Idle cash ₹3L+"},
        {"Client": "Priya Patel", "Current Product": "Savings", "Opportunity": "Fixed Deposit", "Potential Value": "₹8,00,000", "Probability": "Medium", "Reason": "FD inquiry last month"},
        {"Client": "Amit Singh", "Current Product": "Investment Portfolio", "Opportunity": "Insurance", "Potential Value": "₹50,000/year", "Probability": "High", "Reason": "New born child"},
        {"Client": "Neha Gupta", "Current Product": "CASA", "Opportunity": "Home Loan", "Potential Value": "₹45,00,000", "Probability": "Medium", "Reason": "Property search history"},
        {"Client": "Vikram Joshi", "Current Product": "FD", "Opportunity": "PMS", "Potential Value": "₹15,00,000", "Probability": "Low", "Reason": "HNI threshold reached"}
    ])

def get_service_requests():
    return pd.DataFrame([
        {"SR No": "SR001234", "Client": "Rajesh Sharma", "Type": "Cheque Book", "Priority": "Medium", "Status": "Pending", "Created": "2024-03-14", "SLA": "2 days"},
        {"SR No": "SR001235", "Client": "Priya Patel", "Type": "Address Change", "Priority": "High", "Status": "In Progress", "Created": "2024-03-13", "SLA": "1 day"},
        {"SR No": "SR001236", "Client": "Amit Singh", "Type": "Debit Card Block", "Priority": "Urgent", "Status": "Completed", "Created": "2024-03-15", "SLA": "4 hours"},
        {"SR No": "SR001237", "Client": "Neha Gupta", "Type": "Nominee Update", "Priority": "Low", "Status": "Pending", "Created": "2024-03-12", "SLA": "5 days"}
    ])

def get_compliance_data():
    return pd.DataFrame([
        {"Client": "Rajesh Sharma", "KYC Status": "Valid", "KYC Expiry": "2024-12-15", "AML Risk": "Low", "Last Review": "2024-01-15", "Action Required": "None"},
        {"Client": "Priya Patel", "KYC Status": "Expired", "KYC Expiry": "2024-03-10", "AML Risk": "Low", "Last Review": "2023-03-10", "Action Required": "KYC Renewal"},
        {"Client": "Amit Singh", "KYC Status": "Valid", "KYC Expiry": "2024-08-22", "AML Risk": "Medium", "Last Review": "2024-02-22", "Action Required": "Risk Review"},
        {"Client": "Neha Gupta", "KYC Status": "Valid", "KYC Expiry": "2024-06-18", "AML Risk": "Low", "Last Review": "2024-01-18", "Action Required": "None"},
        {"Client": "Vikram Joshi", "KYC Status": "Pending Update", "KYC Expiry": "2024-04-05", "AML Risk": "Low", "Last Review": "2023-10-05", "Action Required": "Document Update"}
    ])

def get_digital_engagement():
    return pd.DataFrame([
        {"Client": "Rajesh Sharma", "Mobile Banking": "High", "Internet Banking": "Medium", "Last Login": "Today", "Transactions/Month": 45, "Digital Adoption": "85%"},
        {"Client": "Priya Patel", "Mobile Banking": "Low", "Internet Banking": "High", "Last Login": "3 days", "Transactions/Month": 12, "Digital Adoption": "45%"},
        {"Client": "Amit Singh", "Mobile Banking": "High", "Internet Banking": "High", "Last Login": "Yesterday", "Transactions/Month": 38, "Digital Adoption": "90%"},
        {"Client": "Neha Gupta", "Mobile Banking": "Medium", "Internet Banking": "Low", "Last Login": "1 week", "Transactions/Month": 8, "Digital Adoption": "35%"},
        {"Client": "Vikram Joshi", "Mobile Banking": "Low", "Internet Banking": "Medium", "Last Login": "2 weeks", "Transactions/Month": 5, "Digital Adoption": "25%"}
    ])

# RM Assistant Chatbot
def get_rm_assistant_response(user_input):
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['portfolio', 'aum', 'client portfolio']):
        return """📊 **Portfolio Overview:**
        
Current AUM: ₹21.5 Cr (86% of target)
Top 5 Clients contribute: 65% of total AUM
Recent activities: 3 new FD bookings, 2 investment redemptions

Would you like detailed portfolio analysis for any specific client?"""
    
    elif any(word in user_input_lower for word in ['crosssell', 'opportunities', 'sales']):
        return """🎯 **Cross-sell Opportunities:**
        
• 5 clients with idle cash > ₹5L (FD/MF potential)
• 3 clients eligible for insurance (life events)
• 2 HNI clients for PMS upgrade
• 4 clients for digital banking adoption

High probability conversions this week: ₹75L+ potential"""
    
    elif any(word in user_input_lower for word in ['compliance', 'kyc', 'risk']):
        return """⚖️ **Compliance Status:**
        
• 2 KYC renewals overdue (immediate action)
• 1 client risk profile update pending
• All AML screenings clear
• Next compliance audit: April 15th

Priority: Complete Priya Patel's KYC renewal by EOD"""
    
    elif any(word in user_input_lower for word in ['tasks', 'meetings', 'schedule']):
        return """📅 **Today's Tasks:**
        
• 10:00 AM - Client meeting with Rajesh Sharma
• 2:00 PM - KYC renewal call with Priya Patel  
• 4:00 PM - Investment proposal review
• Pending: 4 follow-up calls, 2 service requests

Next urgent task: FD maturity follow-up tomorrow"""
    
    elif any(word in user_input_lower for word in ['performance', 'targets', 'achievement']):
        return """📈 **Performance Summary:**
        
AUM Achievement: 86% of target (₹21.5Cr/₹25Cr)
CASA Growth: 12% YTD
Investment Sales: 145% of target
Client Acquisition: 8 new clients this quarter

You're on track for quarterly bonus! Focus on AUM growth."""
    
    else:
        return """🤖 **RM Assistant Help:**
        
I can help you with:
• Client portfolio analysis and AUM tracking
• Cross-sell opportunities and sales pipeline
• Compliance status and KYC reminders
• Task management and meeting schedules
• Performance tracking against targets
• Digital engagement insights

Try asking: "Show me my top clients" or "What are my pending tasks?" """

# Main app function
def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <h1>🏦 RM Dashboard v2.0</h1>
            <div class="rm-info">
                <span>RM: {name} | Branch: {branch} | Clients: {clients}</span>
            </div>
        </div>
    </div>
    """.format(
        name=st.session_state.current_rm['name'],
        branch=st.session_state.current_rm['branch'],
        clients=st.session_state.current_rm['clients_assigned']
    ), unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown('<div class="sidebar-header">📋 Navigation</div>', unsafe_allow_html=True)
        
        tabs = [
            "Summary",
            "Customer Portfolio Review", 
            "Interaction & Task Management",
            "Sales & Cross-Sell Opportunities",
            "Customer Service Requests",
            "Risk & Compliance Checks", 
            "Reporting & Performance Tracking",
            "Client Engagement / Digital Insights",
            "RM Assistant"
        ]
        
        # Custom tab navigation
        selected_tab = st.radio("Select Tab:", tabs, key="tab_selector")
        st.session_state.selected_tab = selected_tab
        
        # RM Quick Stats
        st.markdown('<div class="quick-stats-header">📊 Quick Stats</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("AUM", "₹21.5Cr", "86%")
            st.metric("Clients", "87", "+8")
        with col2:
            st.metric("Revenue", "₹24.8L", "+18%")
            st.metric("Targets", "86%", "+12%")
    
    # Main content based on selected tab
    if selected_tab == "Summary":
        render_summary_page()
    elif selected_tab == "Customer Portfolio Review":
        render_portfolio_review()
    elif selected_tab == "Interaction & Task Management":
        render_interaction_management()
    elif selected_tab == "Sales & Cross-Sell Opportunities":
        render_sales_crosssell()
    elif selected_tab == "Customer Service Requests":
        render_service_requests()
    elif selected_tab == "Risk & Compliance Checks":
        render_risk_compliance()
    elif selected_tab == "Reporting & Performance Tracking":
        render_reporting_performance()
    elif selected_tab == "Client Engagement / Digital Insights":
        render_client_engagement()
    elif selected_tab == "RM Assistant":
        render_rm_assistant()

def render_summary_page():
    st.markdown('<div class="tab-header">📊 Dashboard Summary</div>', unsafe_allow_html=True)
    
    # Quick Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Quick Search", placeholder="Search clients, transactions, or requests...")
    with col2:
        st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
        if st.button("Search", key="quick_search"):
            if search_query:
                st.info(f"Searching for: {search_query}")
    
    # Priority Actions
    st.markdown('<div class="section-header">🚨 Priority Actions</div>', unsafe_allow_html=True)
    actions = get_priority_actions()
    
    for i, action in enumerate(actions):
        priority_class = f"priority-{action['priority'].lower()}"
        st.markdown(f"""
        <div class="action-card {priority_class}">
            <div class="action-priority">{action['priority']}</div>
            <div class="action-content">
                <div class="action-title">{action['action']}</div>
                <div class="action-details">Client: {action['client']} | Due: {action['due']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Alerts and Portfolio Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">🔔 Alerts</div>', unsafe_allow_html=True)
        alerts = get_alerts()
        
        for alert in alerts:
            severity_class = f"alert-{alert['severity'].lower()}"
            st.markdown(f"""
            <div class="alert-card {severity_class}">
                <div class="alert-type">{alert['type']}</div>
                <div class="alert-message">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">💼 Portfolio Summary</div>', unsafe_allow_html=True)
        portfolio = get_portfolio_summary()
        
        col2a, col2b = st.columns(2)
        with col2a:
            st.metric("Total AUM", f"₹{portfolio['total_aum']/10000000:.1f}Cr", f"{(portfolio['total_aum']/portfolio['target_aum']*100):.0f}%")
            st.metric("CASA Balance", f"₹{portfolio['casa_balance']/10000000:.1f}Cr")
            st.metric("FD Balance", f"₹{portfolio['fd_balance']/10000000:.1f}Cr")
        with col2b:
            st.metric("Investments", f"₹{portfolio['investment_balance']/10000000:.1f}Cr") 
            st.metric("Loan Portfolio", f"₹{portfolio['loan_portfolio']/10000000:.1f}Cr")
            st.metric("New Acquisitions", f"₹{portfolio['new_acquisitions']/10000000:.1f}Cr")

def render_portfolio_review():
    st.markdown('<div class="tab-header">💼 Customer Portfolio Review</div>', unsafe_allow_html=True)
    
    
    st.header("Embedded AI/BI Dashboard")

    iframe_source = "https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/01f07f8923f01ffa9c0b8386d9eef5d2?o=1444828305810485"
    
    st.components.v1.iframe(
    src=iframe_source,
    width=1000,
    height=1500,
    scrolling=True
    )
    # Filter options
    # col1, col2, col3, col4 = st.columns(4)
    # with col1:
    #     client_filter = st.selectbox("Filter by Client:", ["All", "Top 10", "High Value", "Recent Activity"])
    # with col2:
    #     product_filter = st.selectbox("Product Type:", ["All", "CASA", "FD", "Investments", "Loans"])
    # with col3:
    #     risk_filter = st.selectbox("Risk Profile:", ["All", "Conservative", "Moderate", "Aggressive"])
    # with col4:
    #     sort_by = st.selectbox("Sort by:", ["AUM", "Client Name", "Last Activity", "Risk Profile"])
    
    # Portfolio data table
    # portfolio_data = get_client_portfolio_data()
    
    # Format currency columns
    # currency_cols = ['AUM', 'CASA', 'FD', 'Investments', 'Loans']
    # for col in currency_cols:
    #     portfolio_data[f"{col}_formatted"] = portfolio_data[col].apply(lambda x: f"₹{x/100000:.1f}L")
    
    # Display formatted table
    # display_data = portfolio_data[['Client Name', 'Client ID', 'AUM_formatted', 'CASA_formatted', 'FD_formatted', 'Investments_formatted', 'Loans_formatted', 'Risk Profile', 'Last Activity']].copy()
    # display_data.columns = ['Client Name', 'Client ID', 'AUM', 'CASA', 'FD', 'Investments', 'Loans', 'Risk Profile', 'Last Activity']
    
    # st.dataframe(display_data, use_container_width=True, height=400)
    
    # Portfolio analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("AUM Distribution by Client")
        fig_pie = px.pie(
            values=portfolio_data['AUM'], 
            names=portfolio_data['Client Name'],
            title="AUM Distribution"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Product Mix Analysis")
        product_totals = {
            'CASA': portfolio_data['CASA'].sum(),
            'FD': portfolio_data['FD'].sum(), 
            'Investments': portfolio_data['Investments'].sum(),
            'Loans': portfolio_data['Loans'].sum()
        }
        
        fig_bar = px.bar(
            x=list(product_totals.keys()),
            y=list(product_totals.values()),
            title="Product Portfolio (₹)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def render_interaction_management():
    st.markdown('<div class="tab-header">💬 Interaction & Task Management</div>', unsafe_allow_html=True)
    
    # Today's Schedule
    st.subheader("📅 Today's Schedule")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="schedule-item">
            <div class="time">10:00 AM</div>
            <div class="event">Client Meeting - Rajesh Sharma (Portfolio Review)</div>
        </div>
        <div class="schedule-item">
            <div class="time">2:00 PM</div>
            <div class="event">KYC Renewal Call - Priya Patel</div>
        </div>
        <div class="schedule-item">
            <div class="time">4:00 PM</div>
            <div class="event">Investment Proposal Review - Amit Singh</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Interaction History
    st.subheader("📋 Recent Interactions")
    interaction_data = get_interaction_data()
    st.dataframe(interaction_data, use_container_width=True)
    
    # Add New Interaction
    st.subheader("➕ Log New Interaction")
    with st.form("new_interaction"):
        col1, col2, col3 = st.columns(3)
        with col1:
            client_name = st.selectbox("Client:", ["Rajesh Sharma", "Priya Patel", "Amit Singh", "Neha Gupta", "Vikram Joshi"])
            interaction_type = st.selectbox("Type:", ["Meeting", "Call", "Email", "WhatsApp", "Video Call"])
        with col2:
            subject = st.text_input("Subject:")
            status = st.selectbox("Status:", ["Completed", "Pending", "Follow-up", "In Progress"])
        with col3:
            due_date = st.date_input("Due Date:")
            priority = st.selectbox("Priority:", ["Low", "Medium", "High", "Urgent"])
        
        notes = st.text_area("Meeting Notes:")
        next_action = st.text_input("Next Action:")
        
        if st.form_submit_button("💾 Save Interaction"):
            st.success("Interaction logged successfully!")

def render_sales_crosssell():
    st.markdown('<div class="tab-header">🎯 Sales & Cross-Sell Opportunities</div>', unsafe_allow_html=True)
    
    # Opportunity Pipeline
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", "15", "+3")
    with col2:
        st.metric("High Probability", "8", "+2")
    with col3:
        st.metric("Pipeline Value", "₹2.5Cr", "+15%")
    with col4:
        st.metric("Conversion Rate", "68%", "+5%")
    
    # Cross-sell Opportunities Table
    st.subheader("💡 Cross-sell Recommendations")
    crosssell_data = get_crosssell_opportunities()
    
    # Add action buttons
    for idx, row in crosssell_data.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(f"**{row['Client']}**")
            st.write(f"Current: {row['Current Product']}")
        with col2:
            st.write(f"**{row['Opportunity']}**")
            st.write(f"Value: {row['Potential Value']}")
        with col3:
            probability_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
            st.write(f"{probability_color[row['Probability']]} {row['Probability']} Probability")
            st.write(f"Reason: {row['Reason']}")
        with col4:
            if st.button("Contact", key=f"contact_{idx}"):
                st.success(f"Contacting {row['Client']}...")
    
    # Sales Pipeline Chart
    st.subheader("📊 Sales Pipeline Progress")
    pipeline_data = {
        'Stage': ['Leads', 'Qualified', 'Proposals', 'Negotiation', 'Closed'],
        'Count': [25, 15, 10, 6, 4],
        'Value': [5000000, 3500000, 2800000, 2200000, 1500000]
    }
    
    fig = px.funnel(
        x=pipeline_data['Count'],
        y=pipeline_data['Stage'],
        title="Sales Pipeline Funnel"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_service_requests():
    st.markdown('<div class="tab-header">🎫 Customer Service Requests</div>', unsafe_allow_html=True)
    
    # Service Request Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Open Requests", "12", "+3")
    with col2:
        st.metric("Pending Approval", "4", "+1") 
    with col3:
        st.metric("Avg Response Time", "2.3h", "-15min")
    with col4:
        st.metric("SLA Compliance", "94%", "+2%")
    
    # Service Requests Table
    st.subheader("📋 Active Service Requests")
    sr_data = get_service_requests()
    
    # Add status styling
    def color_status(val):
        if val == "Completed":
            return "background-color: #d4edda"
        elif val == "Urgent":
            return "background-color: #f8d7da"
        elif val == "In Progress":
            return "background-color: #fff3cd"
        else:
            return "background-color: #f8f9fa"
    
    styled_sr = sr_data.style.applymap(color_status, subset=['Status', 'Priority'])
    st.dataframe(styled_sr, use_container_width=True)
    
    # Create New Service Request
    st.subheader("➕ Create New Service Request")
    with st.form("new_sr"):
        col1, col2 = st.columns(2)
        with col1:
            sr_client = st.selectbox("Client:", ["Rajesh Sharma", "Priya Patel", "Amit Singh", "Neha Gupta"])
            sr_type = st.selectbox("Request Type:", ["Cheque Book", "Debit Card", "Address Change", "Nominee Update", "Account Closure", "Limit Enhancement"])
        with col2:
            sr_priority = st.selectbox("Priority:", ["Low", "Medium", "High", "Urgent"])
            sr_category = st.selectbox("Category:", ["Account Services", "Card Services", "Digital Banking", "Loan Services"])
        
        sr_description = st.text_area("Description:")
        
        if st.form_submit_button("🎫 Create Service Request"):
            st.success("Service request created successfully! SR Number: SR" + str(int(time.time())))

def render_risk_compliance():
    st.markdown('<div class="tab-header">⚖️ Risk & Compliance Checks</div>', unsafe_allow_html=True)
    
    # Compliance Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("KYC Compliance", "94%", "+2%")
    with col2:
        st.metric("Pending Renewals", "3", "-1")
    with col3:
        st.metric("Risk Alerts", "2", "0")
    with col4:
        st.metric("AML Clear", "100%", "0%")
    
    # Compliance Data Table
    st.subheader("📊 Client Compliance Status")
    compliance_data = get_compliance_data()
    
    # Style compliance status
    def style_compliance(val):
        if val == "Expired":
            return "background-color: #f8d7da; color: #721c24"
        elif val == "Pending Update":
            return "background-color: #fff3cd; color: #856404"
        elif val == "Valid":
            return "background-color: #d4edda; color: #155724"
        else:
            return ""
    
    styled_compliance = compliance_data.style.applymap(style_compliance, subset=['KYC Status'])
    st.dataframe(styled_compliance, use_container_width=True)
    
    # Risk Distribution
    st.subheader("📈 Risk Profile Distribution")
    risk_counts = compliance_data['AML Risk'].value_counts()
    fig_risk = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title="AML Risk Distribution"
    )
    st.plotly_chart(fig_risk, use_container_width=True)

def render_reporting_performance():
    st.markdown('<div class="tab-header">📈 Reporting & Performance Tracking</div>', unsafe_allow_html=True)
    
    # Performance Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("AUM Growth", "+15.2%", "vs target +12%")
    with col2:
        st.metric("Revenue", "₹24.8L", "+18.2%")
    with col3:
        st.metric("New Clients", "8", "target: 10")
    with col4:
        st.metric("Cross-sell Rate", "68%", "+5%")
    
    # Performance Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Monthly AUM Trend")
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        aum_values = [18.5, 19.2, 20.1, 20.8, 21.2, 21.5]
        
        fig_aum = px.line(
            x=months, 
            y=aum_values,
            title="AUM Growth (₹ Cr)",
            markers=True
        )
        fig_aum.update_traces(line=dict(color='#1f4e79', width=3))
        st.plotly_chart(fig_aum, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Target Achievement")
        categories = ['AUM', 'CASA', 'Investment', 'Loans', 'Cross-sell']
        targets = [100, 100, 100, 100, 100]
        achieved = [86, 92, 145, 78, 68]
        
        fig_targets = go.Figure(data=[
            go.Bar(name='Target', x=categories, y=targets, marker_color='lightblue'),
            go.Bar(name='Achieved', x=categories, y=achieved, marker_color='#1f4e79')
        ])
        fig_targets.update_layout(barmode='group', title="Target vs Achievement (%)")
        st.plotly_chart(fig_targets, use_container_width=True)
    
    # Daily Sales Targets
    st.subheader("📅 Daily Sales Tracker")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Today's Target", "₹50L", "AUM")
        st.metric("Achieved", "₹35L", "70%")
    with col2:
        st.metric("FD Bookings", "₹15L", "target: ₹20L")
        st.metric("Investment", "₹12L", "target: ₹15L") 
    with col3:
        st.metric("CASA Growth", "₹8L", "target: ₹15L")
        st.metric("Cross-sell", "3 deals", "target: 5")

def render_client_engagement():
    st.markdown('<div class="tab-header">📱 Client Engagement / Digital Insights</div>', unsafe_allow_html=True)
    
    # Digital Adoption Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Digital Adoption", "68%", "+12%")
    with col2:
        st.metric("Mobile Banking", "78%", "+8%")
    with col3:
        st.metric("Internet Banking", "45%", "+5%")
    with col4:
        st.metric("Dormant Clients", "8", "-3")
    
    # Digital Engagement Table
    st.subheader("💻 Digital Engagement Analysis")
    digital_data = get_digital_engagement()
    st.dataframe(digital_data, use_container_width=True)
    
    # Engagement Visualization
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Digital Adoption by Client")
        fig_adoption = px.bar(
            digital_data,
            x='Client',
            y='Digital Adoption',
            title="Digital Adoption %",
            color='Digital Adoption',
            color_continuous_scale='Blues'
        )
        fig_adoption.update_xaxis(tickangle=45)
        st.plotly_chart(fig_adoption, use_container_width=True)
    
    with col2:
        st.subheader("📈 Transaction Frequency")
        fig_transactions = px.scatter(
            digital_data,
            x='Transactions/Month',
            y='Digital Adoption',
            size='Transactions/Month',
            hover_name='Client',
            title="Usage vs Adoption"
        )
        st.plotly_chart(fig_transactions, use_container_width=True)
    
    # Re-engagement Opportunities
    st.subheader("🔄 Re-engagement Opportunities")
    low_engagement = digital_data[digital_data['Digital Adoption'].str.rstrip('%').astype(int) < 50]
    
    if not low_engagement.empty:
        st.write("**Clients requiring digital engagement:**")
        for _, client in low_engagement.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{client['Client']}**")
                st.write(f"Last Login: {client['Last Login']}")
            with col2:
                st.write(f"Digital Adoption: {client['Digital Adoption']}")
                st.write(f"Monthly Transactions: {client['Transactions/Month']}")
            with col3:
                if st.button("Engage", key=f"engage_{client['Client']}"):
                    st.success(f"Engagement plan created for {client['Client']}")

def render_rm_assistant():
    st.markdown('<div class="tab-header">🤖 Ask Genie </div>', unsafe_allow_html=True)
    
    # Chat interface
    st.subheader("💬 Chat with RM Assistant")
    
###### GENIE ######
    #from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    genie_space_id = "01f07f96a2711ec2a3d678153974f002"  # GENIE SPACE ID

    def display_message(message):
        if "content" in message:
            st.markdown(message["content"])
        if "data" in message:
            st.dataframe(message["data"])
        if "code" in message:
            with st.expander("Show generated code"):
                st.code(message["code"], language="sql", wrap_lines=True)


    def get_query_result(statement_id):
        # For simplicity, let's say data fits in one chunk, query.manifest.total_chunk_count = 1

        result = w.statement_execution.get_statement(statement_id)
        return pd.DataFrame(
            result.result.data_array, columns=[i.name for i in result.manifest.schema.columns]
        )


    def process_genie_response(response):
        for i in response.attachments:
            if i.text:
                message = {"role": "assistant", "content": i.text.content}
                display_message(message)
            elif i.query:
                data = get_query_result(response.query_result.statement_id)
                message = {
                    "role": "assistant", "content": i.query.description, "data": data, "code": i.query.query
                }
                display_message(message)


    if prompt := st.chat_input("Ask your question..."):
        st.chat_message("user").markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.get("conversation_id"):
                conversation = w.genie.create_message_and_wait(
                    genie_space_id, st.session_state.conversation_id, prompt
                )
                process_genie_response(conversation)
            else:
                conversation = w.genie.start_conversation_and_wait(genie_space_id, prompt)
                process_genie_response(conversation)

###### GENIE ######

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    # if prompt := st.chat_input("Ask me anything about your clients, portfolio, or tasks..."):
    #     st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
    #     with st.chat_message("user"):
    #         st.write(prompt)
        
    #     # Get AI response
    #     response = get_rm_assistant_response(prompt)
    #     st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
    #     with st.chat_message("assistant"):
    #         st.write(response)
        
    #     st.rerun()
    
    # Quick Action Buttons
    # st.subheader("⚡ Quick Actions")
    # col1, col2, col3 = st.columns(3)
    
    # with col1:
    #     if st.button("📊 Show Portfolio Summary"):
    #         response = get_rm_assistant_response("portfolio summary")
    #         st.session_state.chat_messages.append({"role": "user", "content": "Show portfolio summary"})
    #         st.session_state.chat_messages.append({"role": "assistant", "content": response})
    #         st.rerun()
    
    # with col2:
    #     if st.button("🎯 Show Cross-sell Opportunities"):
    #         response = get_rm_assistant_response("crosssell opportunities")
    #         st.session_state.chat_messages.append({"role": "user", "content": "Show crosssell opportunities"})
    #         st.session_state.chat_messages.append({"role": "assistant", "content": response})
    #         st.rerun()
    
    # with col3:
    #     if st.button("📅 Show Today's Tasks"):
    #         response = get_rm_assistant_response("today's tasks")
    #         st.session_state.chat_messages.append({"role": "user", "content": "Show today's tasks"})
    #         st.session_state.chat_messages.append({"role": "assistant", "content": response})
    #         st.rerun()

if __name__ == "__main__":
    main()
