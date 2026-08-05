import streamlit as st


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# Main Dashboard
# --------------------------------------------------

st.title("📊 Nifty 100 Analytics")

st.markdown(
    """
    Welcome to the **Nifty 100 Analytics Dashboard**.

    Use the sidebar to navigate through the different analytics screens.
    """
)


# --------------------------------------------------
# Dashboard Information
# --------------------------------------------------

st.subheader("Dashboard Modules")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📈 Company Analytics
    - Home
    - Company Profile
    - Stock Screener
    - Peer Comparison
    """)

with col2:
    st.markdown("""
    ### 📊 Market Analytics
    - Trend Analysis
    - Sector Analysis
    - Capital Allocation
    - Annual Reports
    """)


st.divider()

st.caption("Nifty 100 Data Foundation | Streamlit Analytics Dashboard")