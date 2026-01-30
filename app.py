import streamlit as st
import pandas as pd
import plotly.express as px

# =============================
# 1. CẤU HÌNH TRANG
# =============================
st.set_page_config(
    page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# =============================
# CSS VIỆT HÓA FILE UPLOADER
# =============================
st.markdown("""
<style>
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {display:none;}
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content:"Kéo và thả tệp vào đây";
    font-size:1.2em;
    font-weight:bold;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div::after {
    content:"Hỗ trợ tệp .CSV";
    font-size:0.8em;
}
.stFileUploader section button {display:none !important;}
</style>
""", unsafe_allow_html=True)

# =============================
# 2. LOAD & XỬ LÝ DỮ LIỆU
# =============================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
    df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
    df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour

    money_cols = [
        'Giá trị đơn hàng (₫)',
        'Tổng hoa hồng đơn hàng(₫)',
        'Hoa hồng Shopee trên sản phẩm(₫)',
        'Hoa hồng Xtra trên sản phẩm(₫)',
        'Giá(₫)',
        'Số lượng'
    ]

    for col in money_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(',', '')
                .str.replace('₫', '')
                .replace('nan', '0')
            )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    def classify_source(row):
        kenh = str(row.get('Kênh', '')).lower()
        loai = str(row.get('Loại thuộc tính', '')).lower()

        if 'video' in kenh:
            return 'Shopee Video'
        if 'live' in kenh:
            return 'Shopee Live'
        if 'người giới thiệu' in loai or 'social' in loai:
            return 'Social'
        if loai in ['', 'nan', 'không xác định']:
            return 'Không xác định'
        return 'Khác'

    df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
    return df

# =============================
# 3. GIAO DIỆN CHÍNH
# =============================
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

uploaded_file = st.file_uploader("", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)

    # -------------------------
    # BỘ LỌC NGÀY
    # -------------------------
    st.subheader("Chọn khoảng thời gian")
    date_range = st.date_input(
        "Thời gian:",
        [df['Ngày'].min(), df['Ngày'].max()],
        format="DD/MM/YYYY"
    )

    df_filtered = df[
        (df['Ngày'] >= date_range[0]) &
        (df['Ngày'] <= date_range[1])
    ]

    st.divider()

    # =============================
    # 4. THỐNG KÊ TỔNG QUAN
    # =============================
    total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
    total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
    total_orders = len(df_filtered)

    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng Doanh Thu", f"{total_gmv:,.0f}".replace(',', '.') + " ₫")
    m2.metric("Tổng Hoa Hồng", f"{total_comm:,.0f}".replace(',', '.') + " ₫")
    m3.metric("Tổng Đơn Hàng", f"{total_orders:,}".replace(',', '.'))

    st.divider()

    # =============================
    # 5. BIỂU ĐỒ THỐNG KÊ
    # =============================
    st.header("3. Biểu đồ thống kê")
    col_a, col_b = st.columns(2)

    # ---- CỘT TRÁI
    with col_a:
        daily = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
        daily['Ngày_str'] = daily['Ngày'].apply(lambda x: x.strftime('%d/%m/%Y'))

        fig1 = px.line(daily, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày")
        fig1.update_layout(locale="vi")
        fig1.update_traces(
            hovertemplate="Ngày: %{customdata}<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>",
            customdata=daily['Ngày_str']
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.pie(
            df_filtered,
            names='Phân loại nguồn',
            values='Tổng hoa hồng đơn hàng(₫)',
            title="Tỷ trọng đơn hàng theo kênh"
        )
        fig2.update_layout(locale="vi")
        fig2.update_traces(
            hovertemplate=(
                "Kênh: %{label}<br>"
                "Hoa hồng: %{value:,.0f} ₫<br>"
                "Tỷ trọng: %{percent}<extra></extra>"
            )
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ---- CỘT PHẢI
    with col_b:
        hourly = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()

        fig3 = px.bar(hourly, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
        fig3.update_layout(locale="vi")
        fig3.update_traces(
            hovertemplate="Giờ: %{x}h<br>Hoa hồng: %{y:,.0f} ₫<extra></extra>"
        )
        st.plotly_chart(fig3, use_container_width=True)

        cat = (
            df_filtered
            .groupby('L1 Danh mục toàn cầu')
            .agg(
                Số_đơn=('ID đơn hàng', 'count'),
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            )
            .nlargest(10, 'Hoa_hồng')
            .reset_index()
        )

        fig4 = px.bar(cat, x='Hoa_hồng', y='L1 Danh mục toàn cầu',
                      orientation='h', title="Top 10 Danh mục")
        fig4.update_layout(locale="vi")
        fig4.update_traces(
            hovertemplate=(
                "Danh mục: %{y}<br>"
                "Số đơn: %{customdata[0]:,}<br>"
                "Hoa hồng: %{x:,.0f} ₫<extra></extra>"
            ),
            customdata=cat[['Số_đơn']]
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.header("5. Chi tiết đơn hàng")
    st.dataframe(df_filtered, use_container_width=True)
