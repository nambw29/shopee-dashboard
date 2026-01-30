import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Shopee Affiliate Dashboard", layout="wide")

# =========================
# HÀM FORMAT TIỀN VIỆT
# =========================
def format_vnd(x):
    if pd.isna(x):
        return "0 ₫"
    return f"{x:,.0f}".replace(",", ".") + " ₫"


# =========================
# LOAD DATA (VÍ DỤ)
# 👉 THAY BẰNG FILE CỦA BẠN
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")  
    df['Ngày'] = pd.to_datetime(df['Ngày'])
    return df


df = load_data()

# =========================
# FILTER
# =========================
st.title("📊 Shopee Affiliate Dashboard")

col_f1, col_f2 = st.columns(2)
with col_f1:
    date_range = st.date_input(
        "Chọn khoảng ngày",
        [df['Ngày'].min(), df['Ngày'].max()]
    )

with col_f2:
    source_filter = st.multiselect(
        "Nguồn đơn hàng",
        options=df['Phân loại nguồn'].unique(),
        default=df['Phân loại nguồn'].unique()
    )

df_filtered = df[
    (df['Ngày'] >= pd.to_datetime(date_range[0])) &
    (df['Ngày'] <= pd.to_datetime(date_range[1])) &
    (df['Phân loại nguồn'].isin(source_filter))
]

# =========================
# BIỂU ĐỒ
# =========================
st.header("📈 Biểu đồ thống kê")
col_a, col_b = st.columns(2)

# =========================
# CỘT TRÁI
# =========================
with col_a:
    # --- Hoa hồng theo ngày
    daily = (
        df_filtered
        .groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)']
        .sum()
        .reset_index()
    )

    daily['Ngày_str'] = daily['Ngày'].dt.strftime('%d/%m/%Y')
    daily['Tien_str'] = daily['Tổng hoa hồng đơn hàng(₫)'].apply(format_vnd)

    fig1 = px.line(
        daily,
        x='Ngày',
        y='Tổng hoa hồng đơn hàng(₫)',
        title="Hoa hồng theo ngày"
    )

    fig1.update_traces(
        hovertemplate=(
            "Ngày: %{customdata[0]}<br>"
            "Hoa hồng: %{customdata[1]}<extra></extra>"
        ),
        customdata=daily[['Ngày_str', 'Tien_str']]
    )

    st.plotly_chart(fig1, use_container_width=True)

    # --- Tỷ trọng theo kênh
    source_comm = (
        df_filtered
        .groupby('Phân loại nguồn')['Tổng hoa hồng đơn hàng(₫)']
        .sum()
        .reset_index()
    )
    source_comm['Tien_str'] = source_comm['Tổng hoa hồng đơn hàng(₫)'].apply(format_vnd)

    fig2 = px.pie(
        source_comm,
        names='Phân loại nguồn',
        values='Tổng hoa hồng đơn hàng(₫)',
        title="Tỷ trọng đơn hàng theo kênh"
    )

    fig2.update_traces(
        hovertemplate=(
            "Kênh: %{label}<br>"
            "Hoa hồng: %{customdata}<br>"
            "Tỷ trọng: %{percent}<extra></extra>"
        ),
        customdata=source_comm['Tien_str']
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================
# CỘT PHẢI
# =========================
with col_b:
    # --- Hoa hồng theo giờ
    hourly = (
        df_filtered
        .groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)']
        .sum()
        .reset_index()
    )

    hourly['Tien_str'] = hourly['Tổng hoa hồng đơn hàng(₫)'].apply(format_vnd)

    fig3 = px.bar(
        hourly,
        x='Giờ',
        y='Tổng hoa hồng đơn hàng(₫)',
        title="Hoa hồng theo khung giờ"
    )

    fig3.update_traces(
        hovertemplate=(
            "Giờ: %{x}h<br>"
            "Hoa hồng: %{customdata}<extra></extra>"
        ),
        customdata=hourly['Tien_str']
    )

    st.plotly_chart(fig3, use_container_width=True)

    # --- Top 10 danh mục
    cat_data = (
        df_filtered
        .groupby('L1 Danh mục toàn cầu')
        .agg(
            So_don=('ID đơn hàng', 'count'),
            Hoa_hong=('Tổng hoa hồng đơn hàng(₫)', 'sum')
        )
        .nlargest(10, 'Hoa_hong')
        .reset_index()
    )

    cat_data['Tien_str'] = cat_data['Hoa_hong'].apply(format_vnd)

    fig4 = px.bar(
        cat_data,
        x='Hoa_hong',
        y='L1 Danh mục toàn cầu',
        orientation='h',
        title="Top 10 danh mục"
    )

    fig4.update_traces(
        hovertemplate=(
            "Danh mục: %{y}<br>"
            "Số đơn: %{customdata[0]:,}<br>"
            "Hoa hồng: %{customdata[1]}<extra></extra>"
        ),
        customdata=cat_data[['So_don', 'Tien_str']]
    )

    st.plotly_chart(fig4, use_container_width=True)
