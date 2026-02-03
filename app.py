import streamlit as st
import pandas as pd
import plotly.express as px

# ================== CONFIG ==================
st.set_page_config(
    page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# ================== CSS ==================
st.markdown("""
<style>
[data-testid="stFileUploaderDropzoneInstructions"] > div > span { display:none; }
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content:"Kéo & thả tệp CSV vào đây";
    font-size:1.1em;
    font-weight:600;
}
.stFileUploader section button { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ================== UTILS ==================
def format_vnd(x):
    try:
        return f"{int(x):,}".replace(",", ".") + " ₫"
    except:
        return "0 ₫"

# ================== LOAD DATA ==================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'], errors='coerce')
    df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
    df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour

    numeric_cols = [
        'Giá trị đơn hàng (₫)',
        'Tổng hoa hồng đơn hàng(₫)',
        'Hoa hồng Shopee trên sản phẩm(₫)',
        'Hoa hồng Xtra trên sản phẩm(₫)',
        'Giá(₫)',
        'Số lượng'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '')
                .str.replace('₫', '')
                .replace('nan', '0')
                .astype(float)
            )

    def classify_source(row):
        kenh = str(row.get('Kênh', '')).lower()
        loai = str(row.get('Loại thuộc tính', '')).lower()

        if 'video' in kenh:
            return 'Shopee Video'
        if 'live' in kenh:
            return 'Shopee Live'
        if 'người giới thiệu' in loai or 'social' in loai:
            return 'Social'
        if 'không xác định' in loai or loai == '':
            return 'Không xác định'
        return 'Khác'

    df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
    return df

# ================== UI ==================
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")
uploaded_file = st.file_uploader("", type=['csv'])

if not uploaded_file:
    st.stop()

df = load_data(uploaded_file)

# ================== FILTER ==================
st.markdown("### Chọn khoảng thời gian")
date_range = st.date_input(
    "Thời gian:",
    [df['Ngày'].min(), df['Ngày'].max()],
    format="DD/MM/YYYY"
)

if len(date_range) == 2:
    df = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]

st.markdown("---")

# ================== 1. THỐNG KÊ TỔNG QUAN ==================
st.header("1. Thống kê tổng quan")

total_gmv = df['Giá trị đơn hàng (₫)'].sum()
total_comm = df['Tổng hoa hồng đơn hàng(₫)'].sum()
total_orders = len(df)

m1, m2, m3 = st.columns(3)
m1.metric("Tổng Doanh Thu", format_vnd(total_gmv))
m2.metric("Tổng Hoa Hồng", format_vnd(total_comm))
m3.metric("Tổng Đơn Hàng", f"{total_orders:,}".replace(",", "."))

st.markdown("---")

# ================== 2. THỐNG KÊ ĐƠN HÀNG ==================
st.header("2. Thống kê đơn hàng")

c1, c2, c3 = st.columns(3)
c1.metric("HH Shopee", format_vnd(df['Hoa hồng Shopee trên sản phẩm(₫)'].sum()))
c2.metric("HH Xtra", format_vnd(df['Hoa hồng Xtra trên sản phẩm(₫)'].sum()))
c3.metric("Đơn huỷ", f"{df[df['Trạng thái đặt hàng'].str.contains('Hủy', na=False)].shape[0]}")

st.markdown("---")

# ================== 3. BIỂU ĐỒ THỐNG KÊ ==================
st.header("3. Biểu đồ thống kê")
col_a, col_b = st.columns(2)

with col_a:
    daily = df.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
    daily['Ngày_str'] = daily['Ngày'].astype(str)

    fig1 = px.line(daily, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày")
    fig1.update_traces(
        hovertemplate="Ngày: %{customdata}<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>",
        customdata=daily['Ngày_str']
    )
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.pie(
        df,
        names='Phân loại nguồn',
        values='Tổng hoa hồng đơn hàng(₫)',
        title="Tỷ trọng hoa hồng theo kênh"
    )
    fig2.update_traces(
        hovertemplate="Nguồn: %{label}<br>Hoa hồng: %{value:,.0f} ₫<extra></extra>"
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    hourly = df.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
    fig3 = px.bar(hourly, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
    fig3.update_traces(
        hovertemplate="Giờ: %{x}h<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>"
    )
    st.plotly_chart(fig3, use_container_width=True)

    cat = (
        df.groupby('L1 Danh mục toàn cầu')
        .agg(Số_đơn=('ID đơn hàng', 'count'), Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum'))
        .nlargest(10, 'Hoa_hồng')
        .reset_index()
    )

    fig4 = px.bar(cat, x='Hoa_hồng', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục")
    fig4.update_traces(
        hovertemplate=(
            "Danh mục: %{y}<br>"
            "Số đơn: %{customdata[0]}<br>"
            "Hoa hồng: %{x:,.0f} ₫<extra></extra>"
        ),
        customdata=cat[['Số_đơn']]
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ================== 4. TOP SUBID ==================
st.header("4. Top SubID hiệu quả nhất")
sub_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
subs = []

for col in sub_cols:
    if col in df.columns:
        temp = df[df[col].notna() & (df[col] != '')][[col, 'Tổng hoa hồng đơn hàng(₫)']]
        temp.columns = ['SubID', 'Hoa_hồng']
        subs.append(temp)

if subs:
    sub_df = (
        pd.concat(subs)
        .groupby('SubID')
        .agg(Số_đơn=('SubID', 'count'), Hoa_hồng=('Hoa_hồng', 'sum'))
        .reset_index()
        .sort_values('Hoa_hồng', ascending=False)
        .head(20)
    )

    sub_df['Hoa_hồng'] = sub_df['Hoa_hồng'].apply(format_vnd)
    sub_df['Số_đơn'] = sub_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(",", "."))

    st.dataframe(sub_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ================== 5. CHI TIẾT ĐƠN HÀNG ==================
st.header("5. Chi tiết đơn hàng")
st.dataframe(df, use_container_width=True)
