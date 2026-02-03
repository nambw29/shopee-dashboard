import streamlit as st
import pandas as pd
import plotly.express as px

# ================== CONFIG ==================
st.set_page_config(
    page_title="Shopee Affiliate Analytics - BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# ================== CSS ==================
st.markdown("""
<style>
[data-testid="stFileUploaderDropzoneInstructions"] > div > span { display:none; }
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content:"Kéo & thả file CSV vào đây";
    font-size:1.1em;
    font-weight:600;
}
.stFileUploader section button { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ================== UTILS ==================
def vnd(x):
    return f"{int(x):,}".replace(",", ".") + " ₫"

# ================== LOAD DATA ==================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'], errors='coerce')
    df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
    df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour

    num_cols = [
        'Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)',
        'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)',
        'Giá(₫)', 'Số lượng'
    ]

    for col in num_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "")
                .str.replace("₫", "")
                .replace("nan", "0")
                .astype(float)
            )

    def classify(row):
        kenh = str(row.get('Kênh', '')).lower()
        loai = str(row.get('Loại thuộc tính', '')).lower()

        if 'video' in kenh: return 'Shopee Video'
        if 'live' in kenh: return 'Shopee Live'
        if 'người giới thiệu' in loai or 'social' in loai: return 'Social'
        if 'không xác định' in loai or loai == '': return 'Không xác định'
        return 'Khác'

    df['Phân loại nguồn'] = df.apply(classify, axis=1)
    return df

# ================== UI ==================
st.title("🧧 Shopee Affiliate Analytics Dashboard - BLACKWHITE29")
file = st.file_uploader("", type="csv")

if not file:
    st.stop()

df = load_data(file)

# ================== FILTER ==================
date_range = st.date_input(
    "📅 Khoảng thời gian",
    [df['Ngày'].min(), df['Ngày'].max()],
    format="DD/MM/YYYY"
)

df = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]

# ================== OVERVIEW ==================
st.header("1️⃣ Tổng quan")

gmv = df['Giá trị đơn hàng (₫)'].sum()
comm = df['Tổng hoa hồng đơn hàng(₫)'].sum()
orders = len(df)

c1, c2, c3 = st.columns(3)
c1.metric("Tổng GMV", vnd(gmv))
c2.metric("Tổng Hoa Hồng", vnd(comm))
c3.metric("Tổng Đơn", f"{orders:,}".replace(",", "."))

# ================== CHARTS ==================
st.header("2️⃣ Biểu đồ phân tích")
col1, col2 = st.columns(2)

# ---- Hoa hồng theo ngày ----
with col1:
    daily = df.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
    daily['Ngày_str'] = daily['Ngày'].astype(str)

    fig1 = px.line(daily, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)')
    fig1.update_traces(
        hovertemplate="Ngày: %{customdata}<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>",
        customdata=daily['Ngày_str']
    )
    st.plotly_chart(fig1, use_container_width=True)

# ---- Tỷ trọng nguồn ----
with col1:
    fig2 = px.pie(
        df,
        names='Phân loại nguồn',
        values='Tổng hoa hồng đơn hàng(₫)'
    )
    fig2.update_traces(
        hovertemplate="Nguồn: %{label}<br>Hoa hồng: %{value:,.0f} ₫<extra></extra>"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---- Hoa hồng theo giờ ----
with col2:
    hourly = df.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
    fig3 = px.bar(hourly, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)')
    fig3.update_traces(
        hovertemplate="Giờ: %{x}h<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>"
    )
    st.plotly_chart(fig3, use_container_width=True)

# ---- Top danh mục ----
with col2:
    cat = (
        df.groupby('L1 Danh mục toàn cầu')
        .agg(Số_đơn=('ID đơn hàng', 'count'), Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum'))
        .nlargest(10, 'Hoa_hồng')
        .reset_index()
    )

    fig4 = px.bar(cat, x='Hoa_hồng', y='L1 Danh mục toàn cầu', orientation='h')
    fig4.update_traces(
        hovertemplate=(
            "Danh mục: %{y}<br>"
            "Số đơn: %{customdata[0]}<br>"
            "Hoa hồng: %{x:,.0f} ₫<extra></extra>"
        ),
        customdata=cat[['Số_đơn']]
    )
    st.plotly_chart(fig4, use_container_width=True)

# ================== TABLE ==================
st.header("3️⃣ Chi tiết đơn hàng")
st.dataframe(df, use_container_width=True)
