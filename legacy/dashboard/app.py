import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Airbnb Market Expert", page_icon="🏠", layout="wide")

st.title("🏠 Airbnb Market Expert Dashboard")
st.markdown("Data-driven insights for Airbnb hosts")

# Load clean data
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/clean_listings.csv")
    df["property_type"] = df["title"].str.split(" in ").str[0]
    
    # Must match exactly what model was trained on
    df["property_type"] = df["property_type"].replace({
        "Rooms": "Room",
        "Place to stay": "Apartment",
        "Hotel Julian": "Hotel",
        "Home": "Apartment"
    })
    return df


df = load_data()

if df is None or df.empty:
    st.error("Dataset not loaded or empty")
    st.stop()

required_cols = ["region", "price", "title"]

missing = [col for col in required_cols if col not in df.columns]

if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# ── Section 1: Key Metrics ──
st.header("📊 Market Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Listings", len(df))

with col2:
    st.metric("Average Price/Night", f"${df['price'].mean():.0f}")

with col3:
    st.metric("Cities Covered", df['region'].nunique())

# ── Section 2: Price by Region ──
st.header("💰 Average Price by Region")

avg_price = df.groupby("region")["price"].mean().reset_index()
fig1 = px.bar(avg_price, x="region", y="price",
              color="price", color_continuous_scale="Blues",
              title="Average Nightly Price by City")
st.plotly_chart(fig1, width="stretch")

# ── Section 3: Price Distribution ──
st.header("📈 Price Distribution")

fig2 = px.histogram(df, x="price", nbins=20,
                    title="Distribution of Listing Prices",
                    color_discrete_sequence=["#FF5A5F"])
st.plotly_chart(fig2, use_container_width=True)


# ── Section 4: Property Type Breakdown ──
st.header("🏘️ Listings by Property Type")

type_counts = df["property_type"].value_counts().reset_index()
type_counts.columns = ["property_type", "count"]
fig3 = px.pie(type_counts, values="count", names="property_type",
              title="Property Type Distribution",
              color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig3, use_container_width=True)

# ── Section 5: AI Price Predictor ──
st.header("🤖 AI Price Predictor")
st.markdown("Enter property details to get an instant price recommendation")

col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("Select Region", df["region"].unique())

with col2:
    property_type = st.selectbox("Select Property Type", df["property_type"].unique())

if st.button("Predict Price 🔮"):
    try:
        # Call your FastAPI
        url = f"http://api:8000/predict?region={region}&property_type={property_type}"
        response = requests.get(url)
        result = response.json()

        if "predicted_price_per_night" in result:
            price = result["predicted_price_per_night"]
            st.success(f"💰 Recommended Price: **${price} per night**")
            st.info(f"Region: {region} | Type: {property_type}")
        else:
            st.error(f"Error: {result}")
    except:
        st.error("FastAPI server is not running! Start it with: uvicorn api.main:app --reload")