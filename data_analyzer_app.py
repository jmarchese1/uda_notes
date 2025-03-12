import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# Page Configuration & Custom Styling
# ----------------------------
st.set_page_config(page_title="Lead Analyzer", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    /* Global styling */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        background-color: #1C1C1C !important;
        color: #E0E0E0 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: 900 !important;
        color: #4FC3F7 !important;
        text-align: center;
    }
    .reportview-container, .main {
        background-color: #1C1C1C !important;
        padding: 2rem !important;
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #2A2A2A !important;
    }
    /* Explanation text for charts */
    .explanation {
        color: #B0BEC5 !important;
        font-size: 0.95rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    /* Tabs styling */
    .stTabs [role="tablist"] button {
        font-weight: bold;
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True
)

# ----------------------------
# Title & Introduction
# ----------------------------
st.title("Lead Analyzer")
st.markdown(
    """
    <p style="text-align: center; font-size:1.1rem;">
    Welcome to Lead Analyzer – your next‑level tool for dissecting and exploring lead data.
    Upload your CSV to unlock interactive visualizations, deep statistics, and real‑time filtering in a sleek, modern interface.
    </p>
    """, unsafe_allow_html=True
)

# ----------------------------
# Sidebar: Data Upload & Global Filters
# ----------------------------
st.sidebar.header("1. Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file is not None:
    # Read CSV into DataFrame
    df = pd.read_csv(uploaded_file)
    
    # Convert key columns to numeric where applicable
    for col in ['lead_score', 'reviews', 'rating']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    st.sidebar.header("2. Global Filters")
    
    # Social Media Filter using checkboxes
    social_media_cols = ["Instagram", "Facebook", "LinkedIn", "Twitter"]
    available_socials = [col for col in social_media_cols if col in df.columns]
    selected_socials = []
    st.sidebar.markdown("#### Social Media Platforms")
    for platform in available_socials:
        if st.sidebar.checkbox(platform, value=True):
            selected_socials.append(platform)
    
    # Apply social media filter: keep rows where at least one selected platform is non-empty
    if selected_socials:
        mask = df[selected_socials].applymap(lambda x: pd.notnull(x) and str(x).strip() != "")
        df = df[mask.any(axis=1)]
    
    # Lead Score Filter
    if 'lead_score' in df.columns:
        min_ls = float(df['lead_score'].min())
        max_ls = float(df['lead_score'].max())
        ls_range = st.sidebar.slider("Lead Score Range", min_value=min_ls, max_value=max_ls, value=(min_ls, max_ls))
        df = df[(df['lead_score'] >= ls_range[0]) & (df['lead_score'] <= ls_range[1])]
    
    # Chatbot Filter
    if "Has Chatbot" in df.columns:
        chatbot_filter = st.sidebar.radio("Chatbot Availability", options=["All", "Yes", "No"], index=0)
        if chatbot_filter != "All":
            df = df[df["Has Chatbot"] == chatbot_filter]
    
    # ----------------------------
    # Calculated Metrics
    # ----------------------------
    total_leads = len(df)
    avg_lead_score = df['lead_score'].mean() if 'lead_score' in df.columns else 0
    median_lead_score = df['lead_score'].median() if 'lead_score' in df.columns else 0
    min_lead_score = df['lead_score'].min() if 'lead_score' in df.columns else 0
    max_lead_score = df['lead_score'].max() if 'lead_score' in df.columns else 0
    avg_reviews = df['reviews'].mean() if 'reviews' in df.columns else 0
    
    if "Has Chatbot" in df.columns:
        chatbot_yes = df["Has Chatbot"].value_counts().get("Yes", 0)
    else:
        chatbot_yes = 0
    chatbot_pct = (chatbot_yes / total_leads * 100) if total_leads > 0 else 0
    
    def has_any_social(row):
        return any(pd.notnull(row.get(col)) and str(row.get(col)).strip() != "" for col in available_socials)
    total_social_media = df.apply(has_any_social, axis=1).sum()
    
    # ----------------------------
    # Main Tabs: Overview, Visualizations, Detailed Stats
    # ----------------------------
    tab1, tab2, tab3 = st.tabs(["Overview", "Visualizations", "Detailed Stats"])
    
    with tab1:
        st.header("Overview")
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Leads", total_leads)
        col2.metric("Avg Lead Score", f"{avg_lead_score:.2f}")
        col3.metric("Median Lead Score", f"{median_lead_score:.2f}")
        col4.metric("Min/Max Lead Score", f"{min_lead_score:.2f} / {max_lead_score:.2f}")
        col5, col6, col7 = st.columns(3)
        col5.metric("Avg Reviews", f"{avg_reviews:.2f}")
        col6.metric("Chatbot Adoption", f"{chatbot_yes} ({chatbot_pct:.1f}%)")
        col7.metric("Social Media Leads", total_social_media)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Data Preview")
        st.dataframe(df.head(10))
    
    with tab2:
        st.header("Visualizations")
        st.markdown("<hr>", unsafe_allow_html=True)
        # 1. Lead Score Distribution
        st.subheader("Lead Score Distribution")
        st.markdown("<p class='explanation'>This interactive histogram shows the distribution of lead scores. Zoom in or hover for details.</p>", unsafe_allow_html=True)
        fig_ls = px.histogram(df, x="lead_score", nbins=20, title="Lead Score Distribution", color_discrete_sequence=["#2980B9"])
        fig_ls.update_layout(plot_bgcolor="#F8F8F8", paper_bgcolor="#F8F8F8", font_color="#1C1C1C")
        st.plotly_chart(fig_ls, use_container_width=True)
        
        # 2. Chatbot Adoption Bar Chart
        st.subheader("Chatbot Adoption")
        st.markdown("<p class='explanation'>This bar chart displays the count of leads with and without a chatbot.</p>", unsafe_allow_html=True)
        if "Has Chatbot" in df.columns:
            chatbot_counts = df["Has Chatbot"].value_counts().reset_index()
            chatbot_counts.columns = ["Has Chatbot", "Count"]
            fig_chatbot = px.bar(chatbot_counts, x="Has Chatbot", y="Count", title="Chatbot Adoption",
                                 color="Has Chatbot", color_discrete_map={"Yes": "#27AE60", "No": "#C0392B"})
            fig_chatbot.update_layout(plot_bgcolor="#F8F8F8", paper_bgcolor="#F8F8F8", font_color="#1C1C1C")
            st.plotly_chart(fig_chatbot, use_container_width=True)
        else:
            st.info("No Chatbot data available.")
        
        # 3. Reviews Distribution Histogram
        if 'reviews' in df.columns:
            st.subheader("Reviews Distribution")
            st.markdown("<p class='explanation'>This histogram shows the distribution of reviews, reflecting customer engagement.</p>", unsafe_allow_html=True)
            fig_reviews = px.histogram(df, x="reviews", nbins=15, title="Reviews Distribution", color_discrete_sequence=["#66B2FF"])
            fig_reviews.update_layout(plot_bgcolor="#F8F8F8", paper_bgcolor="#F8F8F8", font_color="#1C1C1C")
            st.plotly_chart(fig_reviews, use_container_width=True)
        else:
            st.info("No Reviews data available.")
        
        # 4. Social Media Presence Bar Chart with custom colors
        st.subheader("Social Media Presence")
        st.markdown("<p class='explanation'>This chart visualizes the number of leads with social media profiles across platforms.</p>", unsafe_allow_html=True)
        if available_socials:
            social_counts = {platform: df[platform].apply(lambda x: pd.notnull(x) and str(x).strip() != "").sum() for platform in available_socials}
            social_df = pd.DataFrame({"Platform": list(social_counts.keys()), "Count": list(social_counts.values())})
            color_map = {
                "Instagram": "#FF00FF",   # Magenta
                "Facebook": "#87CEEB",    # Sky Blue
                "Twitter": "#000000",     # Black
                "LinkedIn": "#0e76a8"     # Deep Blue
            }
            fig_social = px.bar(social_df, x="Platform", y="Count", title="Social Media Presence",
                                color="Platform", color_discrete_map=color_map)
            fig_social.update_layout(plot_bgcolor="#F8F8F8", paper_bgcolor="#F8F8F8", font_color="#1C1C1C")
            st.plotly_chart(fig_social, use_container_width=True)
    
    with tab3:
        st.header("Detailed Statistics")
        st.markdown("<hr>", unsafe_allow_html=True)
        detail_cols = st.columns(4)
        with detail_cols[0]:
            st.markdown("<h4 style='text-align: center;'>Lead Score Stats</h4>", unsafe_allow_html=True)
            if 'lead_score' in df.columns:
                st.write(df['lead_score'].describe())
        with detail_cols[1]:
            st.markdown("<h4 style='text-align: center;'>Reviews Stats</h4>", unsafe_allow_html=True)
            if 'reviews' in df.columns:
                st.write(df['reviews'].describe())
        with detail_cols[2]:
            st.markdown("<h4 style='text-align: center;'>Chatbot Stats</h4>", unsafe_allow_html=True)
            if "Has Chatbot" in df.columns:
                st.write(df["Has Chatbot"].value_counts())
        with detail_cols[3]:
            st.markdown("<h4 style='text-align: center;'>Social Media Stats</h4>", unsafe_allow_html=True)
            if available_socials:
                for platform in available_socials:
                    st.markdown(f"<strong>{platform}</strong>")
                    st.write(df[platform].describe())
        
        st.markdown("<br><p style='text-align: center;'>Adjust the filters in the sidebar to dynamically update all statistics and visualizations.</p>", unsafe_allow_html=True)
    
else:
    st.info("Awaiting CSV file upload. Please use the sidebar to upload your leads CSV.")
