import os
from databricks import sql
from databricks.sdk.core import Config
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from databricks.sdk import WorkspaceClient #for Genie

# Page configuration
st.set_page_config(
    page_title="[Demo] Relationship Management",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to load CSS
def load_css(file_name):
    """Load CSS from external file"""
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please ensure it's in the same directory as this app.")
    except Exception as e:
        st.error(f"Error loading CSS file: {str(e)}")

# Load custom CSS for banking theme
load_css("styles.css")

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

###########################################################################################

#st.image("/Volumes/demo_soumyashree_patra/bharat_bank_bi/bi-files/bb-logo.png", width=120)
#st.header("RM Dashboard Data !!! :)")
st.header("Bharat Bank - CustomerSphere 360 - Relationship Management Portal")
col1, col2 = st.columns([3, 1])
# Extract user access token from the request headers
user_token = st.context.headers.get('X-Forwarded-Access-Token')
# Query the SQL data with the user credentials
data = sql_query_with_user_token("SELECT * FROM demo_soumyashree_patra.bharat_bank_bi.rm_master LIMIT 5", user_token=user_token)
# In order to query with Service Principal credentials, comment the above line and uncomment the below line
# data = sql_query_with_service_principal("SELECT * FROM samples.nyctaxi.trips LIMIT 5000")
#with col1:
#    st.scatter_chart(data=data, height=400, width=700, y="fare_amount", x="trip_distance")
#with col2:
#    st.subheader("Predict fare")
#    pickup = st.text_input("From (zipcode)", value="10003")
#    dropoff = st.text_input("To (zipcode)", value="11238")
 #   d = data[(data['pickup_zip'] == int(pickup)) & (data['dropoff_zip'] == int(dropoff))]
 #   st.write(f"# **${d['fare_amount'].mean() if len(d) > 0 else 99:.2f}**")

tabs = st.tabs(["MAIN", "RM Dashboard","Genie"])
tab_main = tabs[0]
tab_rm_dashboard = tabs[1]
tab_rm_genie = tabs[2]

with tab_main:
    st.header("MAIN")
    # Add your main page content here
    st.dataframe(data=data, height=300, use_container_width=True)

### TAB: RM Dashboard #########################################################
with tab_rm_dashboard:
    import streamlit.components.v1 as components
    st.header("Embedded AI/BI Dashboard")

    iframe_source = "https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/01f07f8923f01ffa9c0b8386d9eef5d2?o=1444828305810485"
    
    st.components.v1.iframe(
    src=iframe_source,
    width=2000,
    height=1500,
    scrolling=True
    )
    
    # components.v1.iframe(
    #     src="https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/01f07f8923f01ffa9c0b8386d9eef5d2?o=1444828305810485",  # Replace with your dashboard's embed URL
    #     height=800,
    #     width=1200
    # )
    

### TAB: RM Genie #########################################################
# Genie space integration with Databricks Apps
with tab_rm_genie:
    st.header("---")
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


    if prompt := st.chat_input("Hi, I am Genie. How can I help you today??"):
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

####################################################################################

# Chatbot session state
if 'chatbot_visible' not in st.session_state:
    st.session_state.chatbot_visible = False

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "bot", "content": "👋 Hello! I'm RM Assist. I can help you with customer information, portfolio queries, compliance questions, and more. How can I assist you today?"}
    ]


def get_chatbot_response(user_message):
    """Generate contextual responses for the RM chatbot"""
    user_message_lower = user_message.lower()
    
    # Customer-specific responses
    if any(word in user_message_lower for word in ['customer', 'profile', 'rajesh', 'sharma']):
        return """📋 **Current Customer**: Rajesh Kumar Sharma (CUS123456789)
        
**Key Details:**
• Premium Banking Customer since 2016
• Portfolio Value: ₹45.2L
• Risk Score: 6.2/10 (Medium)
• Satisfaction Score: 4.7/5

Would you like specific details about portfolio, transactions, or compliance status?"""
    
    # Portfolio queries
    elif any(word in user_message_lower for word in ['portfolio', 'investment', 'balance', 'holdings']):
        return """💼 **Portfolio Overview:**
        
• **Total Value**: ₹45.2L
• **Products**: 5 active products
• **Top Holdings**: Home Loan (₹35.5L), Mutual Funds (₹3.25L)
• **Monthly SIP**: ₹25,000
• **Risk Profile**: Conservative-Moderate

Need details on any specific product or investment recommendations?"""
    
    # Transaction queries
    elif any(word in user_message_lower for word in ['transaction', 'payment', 'transfer', 'emi']):
        return """💸 **Recent Activity:**
        
• **Last Transaction**: Salary Credit ₹1.5L (3 days ago)
• **Pending EMI**: Home Loan ₹45.5K (due 5th)
• **SIP Deduction**: ₹25K monthly
• **Credit Card**: 42% utilization

Any specific transaction you'd like me to check?"""
    
    # Compliance and KYC
    elif any(word in user_message_lower for word in ['kyc', 'compliance', 'aml', 'document']):
        return """⚖️ **Compliance Status:**
        
• **KYC Status**: ✅ Complete (valid till Jan 2025)
• **AML Screening**: ✅ Clear
• **Risk Assessment**: ⚠️ Due in 5 days
• **PEP Status**: Not applicable

Shall I schedule the upcoming risk assessment review?"""
    
    # Interactions and communication
    elif any(word in user_message_lower for word in ['interaction', 'call', 'meeting', 'contact']):
        return """📞 **Recent Interactions:**
        
• **Last Contact**: Phone call 3 days ago
• **Subject**: Investment advisory discussion
• **Follow-up**: Pending (ELSS options)
• **Next Scheduled**: Risk assessment review

Would you like me to schedule a follow-up call?"""
    
    # Analytics and performance
    elif any(word in user_message_lower for word in ['analytics', 'performance', 'metrics', 'kpi']):
        return """📊 **Performance Metrics:**
        
• **Cross-sell Score**: 8.5/10 (High potential)
• **Digital Engagement**: 9.2/10 (Very active)
• **Response Time**: 2.3 hours average
• **Satisfaction**: 4.7/5 stars

Need specific analytics for portfolio performance or customer behavior?"""
    
    # General banking services
    elif any(word in user_message_lower for word in ['loan', 'credit', 'deposit', 'savings']):
        return """🏦 **Banking Services:**
        
• **Home Loan**: Active (₹35.5L outstanding)
• **Credit Card**: Platinum (₹2.5L limit, 42% used)
• **Savings**: Premium account (₹2.45L balance)
• **Fixed Deposit**: Maturing in 3 days (₹1.5L)

Which service would you like to explore or need assistance with?"""
    
    # Alerts and notifications
    elif any(word in user_message_lower for word in ['alert', 'notification', 'due', 'reminder']):
        return """🚨 **Current Alerts:**
        
• **High Priority**: Credit card payment overdue (5 days)
• **Medium**: FD maturity in 3 days (₹1.5L)
• **Low**: KYC document update required
• **Reminder**: Risk assessment due in 5 days

Would you like me to help resolve any of these alerts?"""
    
    # Help and general queries
    elif any(word in user_message_lower for word in ['help', 'assist', 'support', 'how']):
        return """🆘 **I can help you with:**
        
• Customer profile and account details
• Portfolio analysis and investment advice
• Transaction history and payment status
• Compliance and KYC requirements
• Scheduling calls and follow-ups
• Performance analytics and reports
• Banking services and product information

What specific area would you like assistance with?"""
    
    # Greetings
    elif any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return """👋 Hello! I'm here to assist you with all your relationship management needs.
        
I can help you with customer information, portfolio analysis, compliance status, scheduling, and much more. What would you like to know about today?"""
    
    # Default response
    else:
        return """🤔 I understand you're looking for information about that topic. 
        
I specialize in:
• Customer account management
• Portfolio and investment queries  
• Compliance and KYC assistance
• Transaction and payment support
• Analytics and reporting

Could you be more specific about what you'd like to know? For example, you could ask about "Rajesh's portfolio" or "pending compliance tasks"."""

def render_chatbot():
    """Render the RM Assist chatbot"""
    # Floating chatbot toggle button
    chatbot_col1, chatbot_col2 = st.columns([10, 1])
    
    with chatbot_col2:
        if not st.session_state.chatbot_visible:
            if st.button("🤖", key="show_chatbot", help="RM Assist - Ask me anything!"):
                st.session_state.chatbot_visible = True
                st.rerun()
    
    # Chatbot interface
    if st.session_state.chatbot_visible:
        with st.expander("🤖 RM Assist - Ask me anything!", expanded=True):
            # Minimize button
            if st.button("Minimize Chat", key="hide_chatbot"):
                st.session_state.chatbot_visible = False
                st.rerun()
            
            # Display messages
            chat_container = st.container()
            with chat_container:
                for i, message in enumerate(st.session_state.chat_messages):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style="text-align: right; margin: 8px 0;">
                            <div style="background: linear-gradient(135deg, #2a5298, #1e3c72); color: white; 
                                        padding: 8px 12px; border-radius: 15px 15px 4px 15px; display: inline-block; 
                                        max-width: 70%; font-size: 14px; line-height: 1.4;">
                                {message["content"]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="text-align: left; margin: 8px 0;">
                            <div style="background: #f1f3f4; color: #333; padding: 8px 12px; 
                                        border-radius: 15px 15px 15px 4px; display: inline-block; 
                                        max-width: 70%; font-size: 14px; line-height: 1.4;
                                        border: 1px solid #e0e0e0;">
                                {message["content"]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Input form
            with st.form("chatbot_input_form", clear_on_submit=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    user_message = st.text_input(
                        "Type your message:", 
                        placeholder="Ask me about customer info, portfolio, compliance...",
                        label_visibility="collapsed"
                    )
                with col2:
                    send_button = st.form_submit_button("Send", use_container_width=True)
                
                if send_button and user_message.strip():
                    # Add user message
                    st.session_state.chat_messages.append({
                        "role": "user", 
                        "content": user_message
                    })
                    
                    # Generate bot response
                    bot_response = get_chatbot_response(user_message)
                    st.session_state.chat_messages.append({
                        "role": "bot", 
                        "content": bot_response
                    })
                    
                    st.rerun()
            
            # Quick action buttons
            st.markdown("**Quick Actions:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Portfolio", key="quick_portfolio"):
                    st.session_state.chat_messages.append({
                        "role": "user", 
                        "content": "Show me portfolio overview"
                    })
                    bot_response = get_chatbot_response("portfolio")
                    st.session_state.chat_messages.append({
                        "role": "bot", 
                        "content": bot_response
                    })
                    st.rerun()
            
            with col2:
                if st.button("⚖️ Compliance", key="quick_compliance"):
                    st.session_state.chat_messages.append({
                        "role": "user", 
                        "content": "Check compliance status"
                    })
                    bot_response = get_chatbot_response("compliance")
                    st.session_state.chat_messages.append({
                        "role": "bot", 
                        "content": bot_response
                    })
                    st.rerun()
            
            with col3:
                if st.button("🚨 Alerts", key="quick_alerts"):
                    st.session_state.chat_messages.append({
                        "role": "user", 
                        "content": "Show current alerts"
                    })
                    bot_response = get_chatbot_response("alerts")
                    st.session_state.chat_messages.append({
                        "role": "bot", 
                        "content": bot_response
                    })
                    st.rerun()
    
    # Style the floating chatbot button
    # Style the floating chatbot button and window to the right
if not st.session_state.chatbot_visible:
    st.markdown("""
    <style>
    .stButton > button[title="RM Assist - Ask me anything!"] {
        position: fixed !important;
        top: 30px !important;
        right: 30px !important;
        z-index: 999 !important;
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #2a5298, #1e3c72) !important;
        border: none !important;
        color: white !important;
        font-size: 24px !important;
        box-shadow: 0 4px 20px rgba(42, 82, 152, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[title="RM Assist - Ask me anything!"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 25px rgba(42, 82, 152, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.chatbot_visible:
    st.markdown("""
    <style>
    /* Chatbot expander to the right */
    .streamlit-expander {
        position: fixed !important;
        top: 100px !important;
        right: 30px !important;
        width: 400px !important;
        z-index: 1000 !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Render chatbot on all pages
render_chatbot()

# Footer
st.markdown("---")
st.markdown("**Powered by Databricks** | Secure Banking Solutions | Last Updated: " + datetime.now().strftime('%d-%b-%Y %I:%M %p'))
