"""
Banking RM Dashboard v3.0
Enhanced Relationship Manager Dashboard with intelligent assistants
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from databricks import sql
from databricks.sdk.core import Config
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient #for Genie
import logging
import os
from model_serving_utils import query_endpoint, is_endpoint_supported

# Page configuration
st.set_page_config(
    page_title="Bharat Bank - CustomerSphere",
    page_icon="",
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

##### Agent #####

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure environment variable is set correctly
SERVING_ENDPOINT = os.getenv('SERVING_ENDPOINT')
assert SERVING_ENDPOINT, \
    ("Unable to determine serving endpoint to use for chatbot app. If developing locally, "
     "set the SERVING_ENDPOINT environment variable to the name of your serving endpoint. If "
     "deploying to a Databricks app, include a serving endpoint resource named "
     "'serving_endpoint' with CAN_QUERY permissions, as described in "
     "https://docs.databricks.com/aws/en/generative-ai/agent-framework/chat-app#deploy-the-databricks-app")

# Check if the endpoint is supported
endpoint_supported = is_endpoint_supported(SERVING_ENDPOINT)


def get_user_info():
    headers = st.context.headers
    return dict(
        user_name=headers.get("X-Forwarded-Preferred-Username"),
        user_email=headers.get("X-Forwarded-Email"),
        user_id=headers.get("X-Forwarded-User"),
    )

user_info = get_user_info()

##### Agent #####

# Retrieve the user name from the environment variables
#user_name = os.getenv('DATABRICKS_USERNAME')

# Display the user name in your Databricks app
#print(f"User Name: {user_name}")

# Initialize session state
def initialize_session_state():
    if 'current_rm' not in st.session_state:
        st.session_state.current_rm = {
            'name': 'Shivani Mehta',
            'employee_id': 'RM001234',
            'branch': 'Mumbai Central',
            'region': 'West Mumbai',
            'clients_assigned': 87,
            'aum_target': 25000000,
            'current_aum': 23750000
        }
    
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Summary"
        
    if 'genie_messages' not in st.session_state:
        st.session_state.genie_messages = [
            {"role": "assistant", "content": "🧞‍♂️ Hello! I'm Ask Genie, your intelligent data assistant. I can help you analyze portfolios, predict trends, and answer complex queries about your clients and performance metrics."}
        ]
        
    if 'agent_messages' not in st.session_state:
        st.session_state.agent_messages = [
            {"role": "assistant", "content": "🤖 Hi! I'm Agent-isstant, your smart banking assistant. I specialize in compliance, regulations, product recommendations, and operational guidance for relationship managers."}
        ]
###########################################################################################

# Ensure environment variable is set correctly
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."

# Databricks config
cfg = Config()

# Query the SQL warehouse with Service Principal credentials
def sql_query_with_service_principal(query: str) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame."""
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{cfg.warehouse_id}",
        credentials_provider=lambda: cfg.authenticate  # Uses SP credentials from the environment variables
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()

# Query the SQL warehouse with the user credentials
def sql_query_with_user_token(query: str, user_token: str) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame."""
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{cfg.warehouse_id}",
        access_token=user_token  # Pass the user token into the SQL connect to query on behalf of user
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()

# Extract user access token from the request headers
user_token = st.context.headers.get('X-Forwarded-Access-Token')

# Query the SQL data with the user credentials
#data = sql_query_with_user_token("SELECT * FROM demo_soumyashree_patra.bharat_bank_rm.customer_product_value LIMIT 500", user_token=user_token)

# In order to query with Service Principal credentials, comment the above line and uncomment the below line
# data = sql_query_with_service_principal("SELECT * FROM samples.nyctaxi.trips LIMIT 5000")
# Query the SQL data with the user credentials
data = sql_query_with_service_principal("SELECT * FROM demo_soumyashree_patra.bharat_bank_rm.customer_product_value LIMIT 500")

#with col1:
#    st.scatter_chart(data=data, height=400, width=700, y="fare_amount", x="trip_distance")
#with col2:
#    st.subheader("Predict fare")
#    pickup = st.text_input("From (zipcode)", value="10003")
#    dropoff = st.text_input("To (zipcode)", value="11238")
 #   d = data[(data['pickup_zip'] == int(pickup)) & (data['dropoff_zip'] == int(dropoff))]
 #   st.write(f"# **${d['fare_amount'].mean() if len(d) > 0 else 99:.2f}**")
###########################################################################################

# Enhanced data functions
def get_enhanced_portfolio_data():
    return pd.DataFrame([
        {"Client Name": "Rajesh Kumar Sharma", "Client ID": "CL001234", "AUM": 4500000, "CASA": 245000, "FD": 1500000, "Investments": 2200000, "Insurance": 120000, "Loans": 555000, "Risk Profile": "Moderate", "Last Activity": "2 days ago", "Digital Score": 85},
        {"Client Name": "Priya Patel", "Client ID": "CL001235", "AUM": 3200000, "CASA": 180000, "FD": 1200000, "Investments": 1500000, "Insurance": 80000, "Loans": 320000, "Risk Profile": "Conservative", "Last Activity": "5 days ago", "Digital Score": 45},
        {"Client Name": "Amit Singh", "Client ID": "CL001236", "AUM": 2800000, "CASA": 320000, "FD": 800000, "Investments": 1400000, "Insurance": 95000, "Loans": 280000, "Risk Profile": "Aggressive", "Last Activity": "1 day ago", "Digital Score": 90},
        {"Client Name": "Neha Gupta", "Client ID": "CL001237", "AUM": 2100000, "CASA": 150000, "FD": 600000, "Investments": 1100000, "Insurance": 65000, "Loans": 250000, "Risk Profile": "Moderate", "Last Activity": "3 days ago", "Digital Score": 35},
        {"Client Name": "Vikram Joshi", "Client ID": "CL001238", "AUM": 1900000, "CASA": 290000, "FD": 500000, "Investments": 900000, "Insurance": 75000, "Loans": 210000, "Risk Profile": "Conservative", "Last Activity": "1 week ago", "Digital Score": 25},
        {"Client Name": "Sanya Verma", "Client ID": "CL001239", "AUM": 1750000, "CASA": 125000, "FD": 450000, "Investments": 980000, "Insurance": 55000, "Loans": 195000, "Risk Profile": "Moderate", "Last Activity": "4 days ago", "Digital Score": 60}
    ])
def get_lh_portfolio_data():
    return data

def get_scheduled_meetings():
    return pd.DataFrame([
        {"Time": "09:00 AM", "Client": "Rajesh Sharma", "Type": "Portfolio Review", "Duration": "45 min", "Location": "Branch", "Status": "Confirmed"},
        {"Time": "11:30 AM", "Client": "Priya Patel", "Type": "KYC Renewal", "Duration": "30 min", "Location": "Video Call", "Status": "Pending"},
        {"Time": "02:00 PM", "Client": "Amit Singh", "Type": "Investment Proposal", "Duration": "60 min", "Location": "Client Office", "Status": "Confirmed"},
        {"Time": "04:30 PM", "Client": "Neha Gupta", "Type": "Credit Discussion", "Duration": "30 min", "Location": "Phone Call", "Status": "Tentative"}
    ])

def get_pipeline_data():
    return pd.DataFrame([
        {"Client": "Rajesh Sharma", "Opportunity": "Mutual Fund SIP", "Stage": "Proposal", "Value": 2500000, "Probability": 85, "Expected Close": "2024-03-25"},
        {"Client": "Priya Patel", "Opportunity": "Fixed Deposit", "Stage": "Negotiation", "Value": 800000, "Probability": 70, "Expected Close": "2024-03-20"},
        {"Client": "Amit Singh", "Opportunity": "Insurance Plan", "Stage": "Qualified", "Value": 150000, "Probability": 90, "Expected Close": "2024-03-18"},
        {"Client": "Sanya Verma", "Opportunity": "Home Loan", "Stage": "Lead", "Value": 4500000, "Probability": 45, "Expected Close": "2024-04-15"},
        {"Client": "Vikram Joshi", "Opportunity": "PMS Portfolio", "Stage": "Proposal", "Value": 1500000, "Probability": 60, "Expected Close": "2024-03-30"}
    ])

def get_service_requests_enhanced():
    return pd.DataFrame([
        {"SR No": "SR001234", "Client": "Rajesh Sharma", "Type": "Cheque Book", "Priority": "Medium", "Status": "In Progress", "Created": "2024-03-14", "SLA": "2 days", "Assigned To": "Operations"},
        {"SR No": "SR001235", "Client": "Priya Patel", "Type": "Address Change", "Priority": "High", "Status": "Pending Approval", "Created": "2024-03-13", "SLA": "1 day", "Assigned To": "KYC Team"},
        {"SR No": "SR001236", "Client": "Amit Singh", "Type": "Debit Card Block", "Priority": "Urgent", "Status": "Completed", "Created": "2024-03-15", "SLA": "4 hours", "Assigned To": "Card Ops"},
        {"SR No": "SR001237", "Client": "Neha Gupta", "Type": "Nominee Update", "Priority": "Low", "Status": "Pending", "Created": "2024-03-12", "SLA": "5 days", "Assigned To": "Account Ops"},
        {"SR No": "SR001238", "Client": "Sanya Verma", "Type": "Grievance", "Priority": "High", "Status": "Under Review", "Created": "2024-03-11", "SLA": "3 days", "Assigned To": "Customer Care"}
    ])

def get_compliance_alerts():
    return pd.DataFrame([
        {"Client": "Priya Patel", "Alert Type": "KYC Expiry", "Severity": "High", "Due Date": "2024-03-18", "Action": "Document Renewal"},
        {"Client": "Vikram Joshi", "Alert Type": "Risk Review", "Severity": "Medium", "Due Date": "2024-03-25", "Action": "Profile Update"},
        {"Client": "Sanya Verma", "Alert Type": "AML Check", "Severity": "Low", "Due Date": "2024-04-01", "Action": "Screening"},
        {"Client": "Amit Singh", "Alert Type": "Transaction Monitoring", "Severity": "Medium", "Due Date": "2024-03-20", "Action": "Review Pattern"}
    ])

def get_performance_metrics():
    return {
        "daily_targets": {
            "aum_target": 500000,
            "aum_achieved": 375000,
            "casa_target": 200000,
            "casa_achieved": 180000,
            "fd_target": 300000,
            "fd_achieved": 250000,
            "investment_target": 150000,
            "investment_achieved": 195000
        },
        "monthly_performance": {
            "target_achievement": 88,
            "revenue_generated": 2480000,
            "client_acquisition": 8,
            "cross_sell_rate": 72
        }
    }

# Intelligent Assistant Functions
def get_genie_response(user_input):
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['predict', 'forecast', 'trend']):
        return """🔮 **Predictive Analysis:**
        
Based on current trends and ML models:
• Your AUM is likely to grow 8-12% next quarter
• Rajesh Sharma shows 95% probability of MF investment
• Priya Patel risk: 15% chance of account dormancy
• Market volatility may affect aggressive portfolios by 5-7%

**Recommendations:**
- Focus on Rajesh for immediate conversions
- Re-engage Priya with digital banking features
- Hedge aggressive portfolios with balanced funds"""
    
    elif any(word in user_input_lower for word in ['analyze', 'analysis', 'insights']):
        return """📊 **Advanced Analytics:**
        
**Portfolio Insights:**
• Top 3 clients contribute 58% of total AUM
• Digital adoption correlates with portfolio growth (+23%)
• Conservative clients show highest retention (94%)

**Behavioral Patterns:**
- High-value clients prefer personal meetings (78%)
- Digital-native clients execute 3x more transactions
- Cross-sell success rate peaks on Tuesdays (84%)"""
    
    elif any(word in user_input_lower for word in ['optimize', 'improve', 'strategy']):
        return """⚡ **Optimization Strategy:**
        
**Time Management:**
• Batch similar client calls for efficiency
• Tuesday-Thursday optimal for sales calls
• Friday best for documentation review

**Revenue Optimization:**
- Target idle cash > ₹5L for immediate FD conversion
- Insurance cross-sell during life events (90% success)
- PMS upgrade for clients with ₹20L+ investment portfolio

**Resource Allocation:**
Focus 60% time on top 20% clients for maximum ROI"""
    
    else:
        return """🧞‍♂️ **Ask Genie Capabilities:**
        
I can help you with:
• **Predictive Analytics** - Forecast trends and client behavior
• **Portfolio Optimization** - Strategic recommendations
• **Performance Analysis** - Deep dive into metrics
• **Risk Assessment** - Advanced risk profiling
• **Market Intelligence** - Industry insights and benchmarks

Try asking: "Predict my next quarter performance" or "Analyze my top clients"""

def get_agent_response(user_input):
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['compliance', 'regulation', 'kyc', 'aml']):
        return """⚖️ **Compliance Guidance:**
        
**Current Alerts:**
• 2 KYC renewals due within 5 days (High Priority)
• 1 AML screening pending review
• 3 risk profile updates overdue

**Regulatory Updates:**
- New SEBI guidelines for mutual fund investments
- RBI circular on digital KYC acceptance
- Enhanced due diligence for NRI accounts

**Action Items:**
1. Complete Priya Patel's KYC by EOD
2. Submit quarterly compliance report
3. Update risk assessment matrices"""
    
    elif any(word in user_input_lower for word in ['product', 'recommend', 'suggest']):
        return """💡 **Product Recommendations:**
        
**Based on Client Profiles:**

**Rajesh Sharma** - Idle cash ₹3L+
→ Systematic Investment Plan (SIP) - ₹25K/month
→ Term Insurance - ₹1Cr coverage

**Priya Patel** - Conservative investor
→ Tax-saving Fixed Deposit
→ Senior Citizen Savings Scheme

**Amit Singh** - Aggressive profile
→ Equity Mutual Funds
→ Portfolio Management Services (PMS)

**Cross-sell Success Tips:**
- Insurance during life events (95% success)
- FDs near tax season (80% conversion)
- MFs for salaried professionals (75% uptake)"""
    
    elif any(word in user_input_lower for word in ['process', 'procedure', 'how to']):
        return """📋 **Process Guidance:**
        
**Account Opening Process:**
1. KYC document collection
2. Risk profiling questionnaire
3. Initial product recommendation
4. Account activation within 24 hours

**Loan Processing:**
1. Credit assessment and CIBIL check
2. Income verification documents
3. Collateral evaluation (if applicable)
4. Approval workflow through system

**Service Request Handling:**
- Urgent: 4 hours SLA
- High: 24 hours SLA
- Medium: 48 hours SLA
- Low: 120 hours SLA

**Escalation Matrix:**
Branch Manager → Regional Head → Circle Head"""
    
    else:
        return """🤖 **Agent-isstant Expertise:**
        
I specialize in:
• **Regulatory Compliance** - KYC, AML, risk management
• **Product Knowledge** - Features, eligibility, pricing
• **Process Guidance** - SOPs, workflows, approvals
• **Policy Updates** - Latest regulatory changes
• **Best Practices** - Industry standards and benchmarks

Try asking: "What are the KYC requirements?" or "Recommend products for high-net-worth clients"""

# Main app function
def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <h2>Bharat Bank - CustomerSphere </h2>
            <div class="rm-info">
                <span>RM: {name} | Branch: {branch} | Clients: {clients} | AUM: ₹{aum:.1f}Cr</span>
            </div>
        </div>
    </div>
    """.format(
        name=st.session_state.current_rm['name'],
        branch=st.session_state.current_rm['branch'],
        clients=st.session_state.current_rm['clients_assigned'],
        aum=st.session_state.current_rm['current_aum']/10000000
    ), unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown('<div class="sidebar-header">📋 Navigation</div>', unsafe_allow_html=True)
        
        tabs = [
            "📊 Summary",
            "💼 Customer Portfolio Review", 
            "📅 Interaction & Task Management",
            "🎯 Sales & Cross-Sell Opportunities",
            "🎫 Customer Service Requests",
            "⚖️ Risk & Compliance Checks", 
            "📈 Reporting & Performance Tracking",
            "📱 Client Engagement / Digital Insights",
            "🧞‍♂️ Ask Genie",
            "🤖 Agent-isstant"
        ]
        
        selected_tab = st.radio("", tabs, key="tab_selector")
        st.session_state.selected_tab = selected_tab
        

    
    # Main content based on selected tab
    tab_content = {
        "📊 Summary": render_summary_page,
        "💼 Customer Portfolio Review": render_portfolio_review,
        "📅 Interaction & Task Management": render_interaction_management,
        "🎯 Sales & Cross-Sell Opportunities": render_sales_crosssell,
        "🎫 Customer Service Requests": render_service_requests,
        "⚖️ Risk & Compliance Checks": render_risk_compliance,
        "📈 Reporting & Performance Tracking": render_reporting_performance,
        "📱 Client Engagement / Digital Insights": render_client_engagement,
        "🧞‍♂️ Ask Genie": render_ask_genie,
        "🤖 Agent-isstant": render_agent_assistant
    }
    
    if selected_tab in tab_content:
        tab_content[selected_tab]()

def render_summary_page():
    st.markdown(
    "<div class='tab-header' style='font-size:16px; color:#888;'>Relationship Management Portal with Intelligent Assistants</div>",
    unsafe_allow_html=True
    )
    
    # Quick Search
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("🔍 Quick Search", placeholder="Search clients, transactions, accounts, or requests...")
    with col2:
        st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
        if st.button("🔍 Search", key="quick_search"):
            if search_query:
                st.info(f"🔍 Searching for: '{search_query}' across all data sources...")

 
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        #st.metric("Total AUM", "₹23.8Cr", "95% of target")
        total_aum = data['AUM'].sum()
        st.metric("Total AUM", f"₹{total_aum/1e7:.1f}Cr")
    with col2:
        #st.metric("Active Clients", "87", "+8 this quarter")
        unique_customer_count = data['CustomerID'].nunique()  # Count of unique customer IDs
        st.metric("Active Clients", unique_customer_count)
    with col3:
        st.metric("Revenue MTD", "₹24.8L", "+18.2%")
    with col4:
        st.metric("Pipeline Value", "₹8.2Cr", "+25%")
    
    # Priority Actions and Alerts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">🚨 Priority Actions</div>', unsafe_allow_html=True)
        priority_actions = [
            {"priority": "High", "action": "KYC renewal - Priya Patel (Due: Today)", "client": "Priya Patel"},
            {"priority": "High", "action": "FD maturity follow-up - Rajesh Sharma", "client": "Rajesh Sharma"},
            {"priority": "Medium", "action": "Investment proposal - Amit Singh", "client": "Amit Singh"},
            {"priority": "Medium", "action": "Credit assessment - Sanya Verma", "client": "Sanya Verma"}
        ]
        
        for action in priority_actions:
            priority_class = f"priority-{action['priority'].lower()}"
            st.markdown(f"""
            <div class="action-card {priority_class}">
                <div class="action-priority">{action['priority']}</div>
                <div class="action-title">{action['action']}</div>
                <div class="action-details">Client: {action['client']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">🔔 System Alerts</div>', unsafe_allow_html=True)
        alerts = [
            {"type": "Compliance", "message": "2 KYC renewals pending", "severity": "High"},
            {"type": "Risk", "message": "1 client exceeded transaction limit", "severity": "Medium"},
            {"type": "Opportunity", "message": "3 clients with idle cash > ₹5L", "severity": "Medium"},
            {"type": "Service", "message": "5 pending service requests", "severity": "Low"}
        ]
        
        for alert in alerts:
            severity_class = f"alert-{alert['severity'].lower()}"
            st.markdown(f"""
            <div class="alert-card {severity_class}">
                <div class="alert-type">{alert['type']}</div>
                <div class="alert-message">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Portfolio Summary
    st.markdown('<div class="section-header">💼 Portfolio Summary</div>', unsafe_allow_html=True)
    
    #portfolio_data = get_enhanced_portfolio_data()
    #st.dataframe(data=data, height=300, use_container_width=True)
    #portfolio_data = get_lh_portfolio_data()
    
    import streamlit.components.v1 as components
    
    st.markdown(
    "<h4 style='color:#888888; font-weight:normal;'>[Embedded AI/BI Dashboard]</h4>",
    unsafe_allow_html=True
    )

    iframe_source = "https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/01f07f8923f01ffa9c0b8386d9eef5d2?o=1444828305810485"
    
    st.components.v1.iframe(
    src=iframe_source,
    height=1500,
    scrolling=True
    )

def render_portfolio_review():
    st.markdown('<div class="tab-header">💼 Customer Portfolio Review</div>', unsafe_allow_html=True)
    
    # Enhanced filters
    # col1, col2, col3, col4, col5 = st.columns(5)
    # with col1:
    #     client_filter = st.selectbox("Client Filter:", ["All Clients", "Top 10 by AUM", "High Value (>₹2Cr)", "New Clients", "At Risk"])
    # with col2:
    #     product_filter = st.selectbox("Product Focus:", ["All Products", "CASA", "Fixed Deposits", "Investments", "Insurance", "Loans"])
    # with col3:
    #     risk_filter = st.selectbox("Risk Profile:", ["All Profiles", "Conservative", "Moderate", "Aggressive"])
    # with col4:
    #     activity_filter = st.selectbox("Activity:", ["All", "Active (7 days)", "Recent (30 days)", "Dormant (90+ days)"])
    # with col5:
    #     sort_by = st.selectbox("Sort by:", ["AUM Descending", "Client Name", "Last Activity", "Digital Score"])
    
    # Portfolio data with enhanced columns
    portfolio_data = get_lh_portfolio_data()
    st.dataframe(data=data, height=800, use_container_width=True)
    
    # Summary metrics
    # col1, col2, col3, col4 = st.columns(4)
    # with col1:
    #     st.metric("Total Clients", len(portfolio_data))
    # with col2:
    #     total_aum = portfolio_data['AUM'].sum()
    #     st.metric("Total AUM", f"₹{total_aum/10000000:.1f}Cr")
    # with col3:
    #     avg_aum = portfolio_data['AUM'].mean()
    #     st.metric("Average AUM", f"₹{avg_aum/100000:.1f}L")
    # with col4:
    #     high_value_clients = len(portfolio_data[portfolio_data['AUM'] > 2000000])
    #     st.metric("High Value Clients", f"{high_value_clients}")
    
    # Detailed portfolio table
    st.subheader("📋 Client Portfolio Details")
    
    # Format currency columns
    display_data = portfolio_data.copy()
    currency_cols = ['CustomerID', 'Name', 'ProductType']
    #for col in currency_cols:
    #    display_data[f"{col}_formatted"] = display_data[col].apply(lambda x: f"₹{x/100000:.1f}L")
    
    # Create display dataframe
    final_display = display_data[['CustomerID', 'Name', 'ProductType']].copy() 
                                #'Loans_formatted', 'Risk Profile', 'Digital Score', 'Last Activity']].copy()
    #final_display.columns = ['Client Name', 'Client ID', 'AUM', 'CASA', 'FD', 'Investments', 'Insurance', 'Loans', 'Risk Profile', 'Digital Score', 'Last Activity']
    final_display.columns = ['CustomerID', 'Name', 'ProductType']
    
    st.dataframe(final_display, use_container_width=True, height=400)
    
    # Portfolio analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 AUM Distribution")
        fig_pie = px.pie(
            values=portfolio_data['AUM'], 
            names=portfolio_data['Client Name'],
            title="Assets Under Management by Client"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📈 Product Mix Analysis")
        product_totals = {
            'CASA': portfolio_data['CASA'].sum(),
            'FD': portfolio_data['FD'].sum(), 
            'Investments': portfolio_data['Investments'].sum(),
            'Insurance': portfolio_data['Insurance'].sum(),
            'Loans': portfolio_data['Loans'].sum()
        }
        
        fig_bar = px.bar(
            x=list(product_totals.keys()),
            y=list(product_totals.values()),
            title="Product Portfolio Distribution (₹)",
            color=list(product_totals.keys()),
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def render_interaction_management():
    st.markdown('<div class="tab-header">📅 Interaction & Task Management</div>', unsafe_allow_html=True)
    
    # Today's schedule
    st.subheader("📅 Today's Schedule")
    meetings_data = get_scheduled_meetings()
    
    for _, meeting in meetings_data.iterrows():
        status_color = {"Confirmed": "🟢", "Pending": "🟡", "Tentative": "🔶"}
        st.markdown(f"""
        <div class="schedule-item">
            <div class="time">{meeting['Time']}</div>
            <div class="event">{status_color.get(meeting['Status'], '⚪')} {meeting['Client']} - {meeting['Type']}</div>
            <div class="details">{meeting['Duration']} | {meeting['Location']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("📞 Schedule Call"):
            st.success("Call scheduling interface opened!")
        if st.button("📧 Send Email"):
            st.success("Email composer opened!")
        if st.button("💬 Log WhatsApp Interaction"):
            st.success("WhatsApp interaction logged!")
        if st.button("⏰ Set Reminder"):
            st.success("Reminder set successfully!")
    
    with col2:
        # Interaction metrics
        st.subheader("📊 Interaction Metrics")
        col2a, col2b = st.columns(2)
        with col2a:
            st.metric("Today's Meetings", "4")
            st.metric("Pending Calls", "7")
        with col2b:
            st.metric("This Week", "23")
            st.metric("Follow-ups Due", "12")
    
    # Recent interactions log
    st.subheader("📋 Recent Interactions")
    interaction_data = pd.DataFrame([
        {"Date": "2024-03-15", "Client": "Rajesh Sharma", "Type": "Meeting", "Subject": "Portfolio Review", "Status": "Completed", "Next Action": "FD Renewal", "Due": "2024-03-20"},
        {"Date": "2024-03-14", "Client": "Priya Patel", "Type": "Call", "Subject": "KYC Renewal", "Status": "Pending", "Next Action": "Document Collection", "Due": "2024-03-16"},
        {"Date": "2024-03-13", "Client": "Amit Singh", "Type": "Email", "Subject": "Investment Proposal", "Status": "Follow-up", "Next Action": "Presentation", "Due": "2024-03-18"},
        {"Date": "2024-03-12", "Client": "Sanya Verma", "Type": "WhatsApp", "Subject": "Loan Inquiry", "Status": "In Progress", "Next Action": "Credit Check", "Due": "2024-03-19"}
    ])
    
    st.dataframe(interaction_data, use_container_width=True)
    
    # Log new interaction
    st.subheader("➕ Log New Interaction")
    with st.form("new_interaction"):
        col1, col2, col3 = st.columns(3)
        with col1:
            client = st.selectbox("Client:", ["Rajesh Sharma", "Priya Patel", "Amit Singh", "Neha Gupta", "Sanya Verma"])
            interaction_type = st.selectbox("Type:", ["Meeting", "Call", "Email", "WhatsApp", "Video Call", "SMS"])
        with col2:
            subject = st.text_input("Subject:")
            status = st.selectbox("Status:", ["Completed", "Pending", "Follow-up", "In Progress", "Cancelled"])
        with col3:
            due_date = st.date_input("Next Action Due:")
            priority = st.selectbox("Priority:", ["Low", "Medium", "High", "Urgent"])
        
        notes = st.text_area("Detailed Notes:")
        next_action = st.text_input("Next Action Required:")
        
        if st.form_submit_button("💾 Save Interaction"):
            st.success("✅ Interaction logged successfully!")

def render_sales_crosssell():
    st.markdown('<div class="tab-header">🎯 Sales & Cross-Sell Opportunities</div>', unsafe_allow_html=True)
    
    # Pipeline metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pipeline", "₹8.2Cr", "+25%")
    with col2:
        st.metric("High Probability", "₹5.1Cr", "85%+")
    with col3:
        st.metric("Expected This Month", "₹3.4Cr", "+15%")
    with col4:
        st.metric("Conversion Rate", "72%", "+8%")
    
    # Pipeline data
    pipeline_data = get_pipeline_data()
    
    # Sales funnel
    st.subheader("📊 Sales Pipeline Funnel")
    col1, col2 = st.columns(2)
    
    with col1:
        # Pipeline by stage
        stage_counts = pipeline_data['Stage'].value_counts()
        fig_funnel = px.funnel(
            x=stage_counts.values,
            y=stage_counts.index,
            title="Opportunities by Stage"
        )
        st.plotly_chart(fig_funnel, use_container_width=True)
    
    with col2:
        # Value by probability
        fig_scatter = px.scatter(
            pipeline_data,
            x='Probability',
            y='Value',
            size='Value',
            color='Stage',
            hover_name='Client',
            title="Opportunity Value vs Probability"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Detailed pipeline table
    st.subheader("💼 Active Opportunities")
    
    # Format value column
    pipeline_display = pipeline_data.copy()
    pipeline_display['Value_formatted'] = pipeline_display['Value'].apply(lambda x: f"₹{x/100000:.1f}L")
    pipeline_display['Probability_formatted'] = pipeline_display['Probability'].apply(lambda x: f"{x}%")
    
    display_pipeline = pipeline_display[['Client', 'Opportunity', 'Stage', 'Value_formatted', 'Probability_formatted', 'Expected Close']].copy()
    display_pipeline.columns = ['Client', 'Opportunity', 'Stage', 'Value', 'Probability', 'Expected Close']
    
    st.dataframe(display_pipeline, use_container_width=True)
    
    # Cross-sell recommendations
    st.subheader("💡 AI-Powered Cross-sell Recommendations")
    
    recommendations = [
        {"Client": "Rajesh Sharma", "Product": "Mutual Fund SIP", "Reason": "Idle cash ₹3L+ detected", "Confidence": "95%", "Revenue": "₹2.5L"},
        {"Client": "Priya Patel", "Product": "Tax Saver FD", "Reason": "Tax season approaching", "Confidence": "80%", "Revenue": "₹8L"},
        {"Client": "Sanya Verma", "Product": "Home Loan", "Reason": "Property search activity", "Confidence": "75%", "Revenue": "₹45L"},
        {"Client": "Amit Singh", "Product": "Child Education Plan", "Reason": "New child in family", "Confidence": "90%", "Revenue": "₹1.5L"}
    ]
    
    for rec in recommendations:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(f"**{rec['Client']}**")
            st.write(f"Product: {rec['Product']}")
        with col2:
            st.write(f"**Reason:** {rec['Reason']}")
            st.write(f"Confidence: {rec['Confidence']}")
        with col3:
            st.write(f"**Potential Revenue:** {rec['Revenue']}")
        with col4:
            if st.button("Contact", key=f"contact_{rec['Client']}"):
                st.success(f"📞 Contacting {rec['Client']}...")

def render_service_requests():
    st.markdown('<div class="tab-header">🎫 Customer Service Requests</div>', unsafe_allow_html=True)
    
    # SR metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Open Requests", "15", "+3")
    with col2:
        st.metric("Pending Approval", "6", "+2")
    with col3:
        st.metric("Avg Response Time", "1.8h", "-20min")
    with col4:
        st.metric("SLA Compliance", "96%", "+3%")
    
    # Service requests data
    sr_data = get_service_requests_enhanced()
    
    # Status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Request Status Distribution")
        status_counts = sr_data['Status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Service Requests by Status"
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ SLA Performance")
        priority_counts = sr_data['Priority'].value_counts()
        fig_priority = px.bar(
            x=priority_counts.index,
            y=priority_counts.values,
            title="Requests by Priority",
            color=priority_counts.index,
            color_discrete_map={
                'Urgent': '#ff4444',
                'High': '#ff8800',
                'Medium': '#ffcc00',
                'Low': '#44ff44'
            }
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    # Active service requests
    st.subheader("📋 Active Service Requests")
    st.dataframe(sr_data, use_container_width=True)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("✅ Approve Pending"):
            st.success("Pending requests approved!")
    with col2:
        if st.button("📤 Forward to Ops"):
            st.success("Requests forwarded to operations!")
    with col3:
        if st.button("📧 Send Update"):
            st.success("Status updates sent to clients!")
    with col4:
        if st.button("📊 Generate Report"):
            st.success("SR performance report generated!")
    
    # Create new SR
    st.subheader("➕ Create New Service Request")
    with st.form("new_sr"):
        col1, col2 = st.columns(2)
        with col1:
            client = st.selectbox("Client:", ["Rajesh Sharma", "Priya Patel", "Amit Singh", "Neha Gupta", "Sanya Verma"])
            sr_type = st.selectbox("Request Type:", [
                "Cheque Book Request", "Debit Card Services", "Address Change", 
                "Nominee Update", "Account Closure", "Limit Enhancement", 
                "Grievance Resolution", "Statement Request"
            ])
        with col2:
            priority = st.selectbox("Priority:", ["Low", "Medium", "High", "Urgent"])
            category = st.selectbox("Category:", [
                "Account Services", "Card Services", "Digital Banking", 
                "Loan Services", "Investment Services", "Customer Care"
            ])
        
        description = st.text_area("Detailed Description:")
        
        if st.form_submit_button("🎫 Create Service Request"):
            sr_number = f"SR{int(time.time())}"
            st.success(f"✅ Service request created successfully! SR Number: {sr_number}")

def render_risk_compliance():
    st.markdown('<div class="tab-header">⚖️ Risk & Compliance Checks</div>', unsafe_allow_html=True)
    
    # Compliance metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("KYC Compliance", "96%", "+2%")
    with col2:
        st.metric("Pending Reviews", "4", "-2")
    with col3:
        st.metric("Risk Alerts", "3", "+1")
    with col4:
        st.metric("AML Screening", "100%", "✅")
    
    # Compliance alerts
    st.subheader("🚨 Compliance Alerts")
    compliance_alerts = get_compliance_alerts()
    
    for _, alert in compliance_alerts.iterrows():
        severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        st.markdown(f"""
        <div class="alert-card alert-{alert['Severity'].lower()}">
            <div class="alert-type">{severity_color[alert['Severity']]} {alert['Alert Type']}</div>
            <div class="alert-message">Client: {alert['Client']} | Due: {alert['Due Date']} | Action: {alert['Action']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Risk Profile Distribution")
    
        #portfolio_data = get_enhanced_portfolio_data()
        portfolio_data = get_lh_portfolio_data()
        risk_counts = portfolio_data['Risk Profile'].value_counts()
        fig_risk = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="Client Risk Profiles",
            color_discrete_sequence=['#ff9999', '#66b3ff', '#99ff99']
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        st.subheader("📈 Compliance Trends")
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        compliance_scores = [94, 95, 92, 96, 97, 96]
        
        fig_trend = px.line(
            x=months,
            y=compliance_scores,
            title="Monthly Compliance Score",
            markers=True
        )
        fig_trend.update_traces(line=dict(color='#2E86AB', width=3))
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Detailed compliance table
    st.subheader("📋 Client Compliance Status")
    compliance_data = pd.DataFrame([
        {"Client": "Rajesh Sharma", "KYC Status": "Valid", "KYC Expiry": "2024-12-15", "Risk Level": "Low", "Last Review": "2024-01-15"},
        {"Client": "Priya Patel", "KYC Status": "Expired", "KYC Expiry": "2024-03-10", "Risk Level": "Low", "Last Review": "2023-03-10"},
        {"Client": "Amit Singh", "KYC Status": "Valid", "KYC Expiry": "2024-08-22", "Risk Level": "Medium", "Last Review": "2024-02-22"},
        {"Client": "Neha Gupta", "KYC Status": "Valid", "KYC Expiry": "2024-06-18", "Risk Level": "Low", "Last Review": "2024-01-18"},
        {"Client": "Sanya Verma", "KYC Status": "Pending", "KYC Expiry": "2024-04-05", "Risk Level": "Medium", "Last Review": "2023-10-05"}
    ])
    
    st.dataframe(compliance_data, use_container_width=True)
    
    # Quick actions
    st.subheader("⚡ Compliance Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📋 Generate KYC Report"):
            st.success("KYC compliance report generated!")
    with col2:
        if st.button("🔍 Run AML Screening"):
            st.success("AML screening initiated for all clients!")
    with col3:
        if st.button("⚠️ Send Renewal Alerts"):
            st.success("KYC renewal alerts sent to clients!")
    with col4:
        if st.button("📊 Risk Assessment"):
            st.success("Risk profile assessment completed!")

def render_reporting_performance():
    st.markdown('<div class="tab-header">📈 Reporting & Performance Tracking</div>', unsafe_allow_html=True)
    
    performance_data = get_performance_metrics()
    
    # Daily targets
    st.subheader("🎯 Daily Sales Targets")
    daily = performance_data['daily_targets']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        aum_pct = (daily['aum_achieved'] / daily['aum_target']) * 100
        st.metric("AUM Target", f"₹{daily['aum_achieved']/100000:.1f}L", f"{aum_pct:.0f}%")
    with col2:
        casa_pct = (daily['casa_achieved'] / daily['casa_target']) * 100
        st.metric("CASA Target", f"₹{daily['casa_achieved']/100000:.1f}L", f"{casa_pct:.0f}%")
    with col3:
        fd_pct = (daily['fd_achieved'] / daily['fd_target']) * 100
        st.metric("FD Target", f"₹{daily['fd_achieved']/100000:.1f}L", f"{fd_pct:.0f}%")
    with col4:
        inv_pct = (daily['investment_achieved'] / daily['investment_target']) * 100
        st.metric("Investment Target", f"₹{daily['investment_achieved']/100000:.1f}L", f"{inv_pct:.0f}%")
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Monthly Performance Trend")
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        aum_values = [18.5, 19.2, 20.1, 21.8, 22.5, 23.8]
        revenue_values = [180, 195, 210, 225, 235, 248]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=months, y=aum_values, name="AUM (₹Cr)", line=dict(color='blue')),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=months, y=revenue_values, name="Revenue (₹L)", line=dict(color='green')),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="AUM (₹Cr)", secondary_y=False)
        fig.update_yaxes(title_text="Revenue (₹L)", secondary_y=True)
        fig.update_layout(title_text="AUM vs Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Target Achievement")
        categories = ['AUM', 'CASA', 'FD', 'Investment', 'Cross-sell']
        targets = [100, 100, 100, 100, 100]
        achieved = [95, 90, 83, 130, 72]
        
        fig_targets = go.Figure(data=[
            go.Bar(name='Target', x=categories, y=targets, marker_color='lightblue'),
            go.Bar(name='Achieved', x=categories, y=achieved, marker_color='darkblue')
        ])
        fig_targets.update_layout(barmode='group', title="Target vs Achievement (%)")
        st.plotly_chart(fig_targets, use_container_width=True)
    
    # Monthly performance summary
    st.subheader("📋 Monthly Performance Summary")
    monthly = performance_data['monthly_performance']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Target Achievement", f"{monthly['target_achievement']}%", "+3%")
    with col2:
        st.metric("Revenue Generated", f"₹{monthly['revenue_generated']/100000:.1f}L", "+18%")
    with col3:
        st.metric("New Clients", monthly['client_acquisition'], "+2")
    with col4:
        st.metric("Cross-sell Rate", f"{monthly['cross_sell_rate']}%", "+8%")

def render_client_engagement():
    st.markdown('<div class="tab-header">📱 Client Engagement / Digital Insights</div>', unsafe_allow_html=True)
    
    # Digital adoption metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Digital Adoption", "68%", "+12%")
    with col2:
        st.metric("Mobile Banking", "78%", "+8%")
    with col3:
        st.metric("Internet Banking", "45%", "+5%")
    with col4:
        st.metric("At Risk Clients", "6", "-3")
    
    # Digital engagement data
    portfolio_data = get_enhanced_portfolio_data()
    #portfolio_data = get_lh_portfolio_data
    
    # Engagement analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Digital Adoption by Client")
        fig_digital = px.bar(
            portfolio_data,
            x='Client Name',
            y='Digital Score',
            title="Digital Adoption Score",
            color='Digital Score',
            color_continuous_scale='RdYlGn'
        )
        fig_digital.update_xaxis(tickangle=45)
        st.plotly_chart(fig_digital, use_container_width=True)
    
    with col2:
        st.subheader("💰 Digital Score vs AUM")
        fig_correlation = px.scatter(
            portfolio_data,
            x='Digital Score',
            y='AUM',
            size='AUM',
            hover_name='Client Name',
            title="Digital Adoption vs Portfolio Size"
        )
        st.plotly_chart(fig_correlation, use_container_width=True)
    
    # Transaction patterns
    st.subheader("📈 Transaction Pattern Analysis")
    transaction_data = pd.DataFrame([
        {"Client": "Rajesh Sharma", "Weekly Txns": 15, "Mobile %": 85, "Digital Channels": 90, "Branch Visits": 1},
        {"Client": "Priya Patel", "Weekly Txns": 4, "Mobile %": 30, "Digital Channels": 45, "Branch Visits": 3},
        {"Client": "Amit Singh", "Weekly Txns": 18, "Mobile %": 95, "Digital Channels": 90, "Branch Visits": 0},
        {"Client": "Neha Gupta", "Weekly Txns": 6, "Mobile %": 40, "Digital Channels": 35, "Branch Visits": 2},
        {"Client": "Sanya Verma", "Weekly Txns": 8, "Mobile %": 60, "Digital Channels": 60, "Branch Visits": 1}
    ])
    
    st.dataframe(transaction_data, use_container_width=True)
    
    # Re-engagement opportunities
    st.subheader("🔄 Re-engagement Opportunities")
    low_digital = portfolio_data[portfolio_data['Digital Score'] < 50]
    
    if not low_digital.empty:
        for _, client in low_digital.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{client['Client Name']}**")
                st.write(f"AUM: ₹{client['AUM']/100000:.1f}L")
            with col2:
                st.write(f"Digital Score: {client['Digital Score']}%")
                st.write(f"Last Activity: {client['Last Activity']}")
            with col3:
                if st.button("📱 Engage", key=f"engage_{client['Client Name']}"):
                    st.success(f"Digital engagement plan created for {client['Client Name']}")

def render_ask_genie():
    st.markdown('<div class="tab-header">🧞‍♂️ Ask Genie - AI Assistant</div>', unsafe_allow_html=True)
    
    # Genie capabilities
    
    # Chat interface
    
    # Display chat messages
    for message in st.session_state.genie_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
     
    w = WorkspaceClient()

    genie_space_id = "01f07f96a2711ec2a3d678153974f002" #GENIE SPACE ID


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


    if prompt := st.chat_input("Hi, I am Genie. How can I help you today?"):
        # Refer to actual app code for chat history persistence on rerun

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

        #st.rerun()

def render_agent_assistant():
    st.markdown('<div class="tab-header">🤖 Agent-isstant - Your Banking Expert</div>', unsafe_allow_html=True)

    # Check if endpoint is supported and show appropriate UI
    #if not endpoint_supported:
    if endpoint_supported:
        st.error("⚠️ Unsupported Endpoint Type")
        st.markdown(
            f"The endpoint `{SERVING_ENDPOINT}` of type `{endpoint_supported}` is not compatible with this basic chatbot template.\n\n"
            "This template only supports chat completions-compatible endpoints.\n\n"
            "👉 **For a richer chatbot template** that supports all conversational endpoints on Databricks, "
            "please see the [Databricks documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/chat-app)."
        )
    else:
        st.markdown(
            "ℹ️ This is a simple example. See "
            "[Databricks docs](https://docs.databricks.com/aws/en/generative-ai/agent-framework/chat-app) "
            "for a more comprehensive example with streaming output and more."
        )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Hi, I am your Agentic Assistant. How can I help you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # Query the Databricks serving endpoint
            assistant_response = query_endpoint(
                endpoint_name=SERVING_ENDPOINT,
                messages=st.session_state.messages,
                max_tokens=400,
            )["content"]
            st.markdown(assistant_response)


        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    # Display chat messages
    # for message in st.session_state.agent_messages:
    #     with st.chat_message(message["role"]):
    #         st.write(message["content"])
    
    # Chat input
    # if prompt := st.chat_input("Ask me about compliance, products, processes, or regulations..."):
    #     st.session_state.agent_messages.append({"role": "user", "content": prompt})
        
    #     with st.chat_message("user"):
    #         st.write(prompt)
        
    #     # Get Agent response
    #     response = get_agent_response(prompt)
    #     st.session_state.agent_messages.append({"role": "assistant", "content": response})
        
    #     with st.chat_message("assistant"):
    #         st.write(response)
        
    #     st.rerun()
    
    # Quick action buttons
    st.subheader("⚡ Expert Guidance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⚖️ Compliance Check"):
            response = get_agent_response("compliance status and requirements")
            st.session_state.agent_messages.append({"role": "user", "content": "Check compliance status"})
            st.session_state.agent_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("💡 Product Recommendations"):
            response = get_agent_response("recommend products for clients")
            st.session_state.agent_messages.append({"role": "user", "content": "Recommend products for my clients"})
            st.session_state.agent_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("📋 Process Guidance"):
            response = get_agent_response("process guidance for account opening")
            st.session_state.agent_messages.append({"role": "user", "content": "Guide me through processes"})
            st.session_state.agent_messages.append({"role": "assistant", "content": response})
            st.rerun()

if __name__ == "__main__":
    main()
