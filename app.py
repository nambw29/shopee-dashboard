import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Shopee Affiliate Analytics - BLACKWHITE29", 
    layout="wide", 
    page_icon="🧧"
)

# --- 2. STYLE CSS (Tối ưu giao diện) ---
st.markdown("""
    <style>
    /* Ẩn text mặc định của uploader và thay bằng tiếng Việt */
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span { display: none; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "Kéo và thả tệp CSV vào đây";
        display: block; font-size: 1.1em; font-weight: bold;
    }
    /* Tối ưu các thẻ Metric */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #FF4B2B; }
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. UTILS (Hàm bổ trợ) ---
def format_currency(value):
    """Định dạng tiền tệ VNĐ: 1.234.567 ₫"""
    return f"{int(round(value, 0)):,}".replace(',', '.') + " ₫"

def format_number(value):
    """Định dạng số: 1.234"""
    return f"{int(value):,}".replace(',', '.')

# --- 4. LOGIC XỬ LÝ DỮ LIỆU (Đã tối ưu) ---
@st.cache_data
def process_data(file):
    try:
        # Đọc file với xử lý lỗi encoding
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            file.seek(0)
            df = pd.read_csv(file, encoding='latin1')

        if df.empty: return None

        # Chuyển đổi thời gian nhanh hơn
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
        # Xử lý số liệu (Vectơ hóa thay vì loop)
        cols_numeric = ['Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
                        'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
                        'Giá(₫)', 'Số lượng']
        
        for col in cols_numeric:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Phân loại nguồn & nội dung (Sử dụng .map hoặc vectorized logic)
        social_channels = ['Facebook', 'Instagram', 'Zalo']
        df['Phân loại nguồn'] = df['Kênh'].apply(lambda x: 'Social' if x in social_channels else 'Others')
        
        # Logic nội dung (Video/Live)
        df['Loại nội dung'] = 'Normal'
        mask_video = df['Loại sản phẩm'].str.contains('video', case=False, na=False) | \
                     df['Loại Hoa hồng'].str.contains('video', case=False, na=False) | \
                     df['Sub_id3'].str.contains('video', case=False, na=False)
        mask_live = df['Loại sản phẩm'].str.contains('live', case=False, na=False) | \
                    df['Loại Hoa hồng'].str.contains('live', case=False, na=False) | \
                    df['Sub_id3'].str.contains('live', case=False, na=False)
        
        df.loc[mask_video, 'Loại nội dung'] = 'Shopee Video'
        df.loc[mask_live, 'Loại nội dung'] = 'Shopee Live'
        
        return df
    except Exception as e:
        st.error(f"Lỗi xử lý dữ liệu: {e}")
        return None

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🧧 Shopee Affiliate Analytics")

col_up, col_dt = st.columns([2, 1])
with col_up:
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'], label_visibility="collapsed")

if uploaded_file:
    df = process_data(uploaded_file)
    
    if df is not None:
        with col_dt:
            date_range = st.date_input("Khoảng thời gian", [df['Ngày'].min(), df['Ngày'].max()])
        
        # Lọc dữ liệu
        if len(date_range) == 2:
            df_flt = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_flt = df

        # --- MỤC 1: TỔNG QUAN ---
        st.header("1. Thống kê tổng quan")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Doanh Thu", format_currency(df_flt['Giá trị đơn hàng (₫)'].sum()))
        m2.metric("💵 Hoa Hồng", format_currency(df_flt['Tổng hoa hồng đơn hàng(₫)'].sum()))
        m3.metric("📦 Đơn Hàng", format_number(df_flt['ID đơn hàng'].nunique()))
        m4.metric("📊 Tỷ Lệ HH", f"{(df_flt['Tổng hoa hồng đơn hàng(₫)'].sum()/df_flt['Giá trị đơn hàng (₫)'].sum()*100):.2f}%" if df_flt['Giá trị đơn hàng (₫)'].sum() > 0 else "0%")

        m5, m6, m7, m8 = st.columns(4)
        m5.metric("💎 HH Shopee", format_currency(df_flt['Hoa hồng Shopee trên sản phẩm(₫)'].sum()))
        m6.metric("⭐ HH Xtra", format_currency(df_flt['Hoa hồng Xtra trên sản phẩm(₫)'].sum()))
        m7.metric("🛒 SL Đã Bán", format_number(df_flt['Số lượng'].sum()))
        m8.metric("📈 HH TB/Đơn", format_currency(df_flt['Tổng hoa hồng đơn hàng(₫)'].sum() / df_flt['ID đơn hàng'].nunique() if df_flt['ID đơn hàng'].nunique() > 0 else 0))

        # --- MỤC 2: THỐNG KÊ ĐƠN HÀNG ---
        st.header("2. Thống kê đơn hàng")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        counts = df_flt.groupby('Phân loại nguồn')['ID đơn hàng'].nunique()
        content_counts = df_flt.groupby('Loại nội dung')['ID đơn hàng'].nunique()
        
        c1.metric("👥 Đơn Social", format_number(counts.get('Social', 0)))
        c2.metric("📋 Đơn Others", format_number(counts.get('Others', 0)))
        c3.metric("🎬 Đơn Video", format_number(content_counts.get('Shopee Video', 0)))
        c4.metric("📹 Đơn Live", format_number(content_counts.get('Shopee Live', 0)))
        c5.metric("🆓 Đơn 0đ", format_number(df_flt[df_flt['Giá trị đơn hàng (₫)'] == 0]['ID đơn hàng'].nunique()))
        c6.metric("❌ Đơn Hủy", format_number(df_flt[df_flt['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)]['ID đơn hàng'].nunique()))

        # --- MỤC 3: BIỂU ĐỒ ---
        st.header("3. Biểu đồ phân tích")
        g1, g2 = st.columns(2)
        
        with g1:
            # Line Chart: Hoa hồng theo ngày
            daily = df_flt.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig_line = px.line(daily, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Xu hướng hoa hồng", color_discrete_sequence=['#FF4B2B'])
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Pie Chart: Kênh
            fig_pie = px.pie(df_flt, names='Phân loại nguồn', values='Tổng hoa hồng đơn hàng(₫)', title="Tỷ trọng hoa hồng theo kênh", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with g2:
            # Bar Chart: Giờ cao điểm
            hourly = df_flt.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig_hour = px.bar(hourly, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
            st.plotly_chart(fig_hour, use_container_width=True)
            
            # Top Categories
            top_cat = df_flt.groupby('L1 Danh mục toàn cầu')['Tổng hoa hồng đơn hàng(₫)'].sum().nlargest(10).reset_index()
            fig_cat = px.bar(top_cat, x='Tổng hoa hồng đơn hàng(₫)', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục")
            st.plotly_chart(fig_cat, use_container_width=True)

        # --- MỤC 4, 5, 6: BẢNG TOP ---
        def display_top_table(header, data, columns_config):
            st.header(header)
            st.dataframe(data, use_container_width=True, hide_index=True, column_config=columns_config)

        # Top SubID
        sub_id_cols = [c for c in ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5'] if c in df_flt.columns]
        all_subs = pd.concat([df_flt[[c, 'Tổng hoa hồng đơn hàng(₫)']].rename(columns={c: 'SubID'}) for c in sub_id_cols])
        top_subs = all_subs.groupby('SubID').agg(Đơn=('SubID','count'), Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)','sum')).nlargest(20, 'Đơn').reset_index()
        
        display_top_table("4. Top 20 SubID hiệu quả", top_subs, {
            "Hoa_hồng": st.column_config.NumberColumn("Tổng Hoa Hồng", format="%.0f ₫"),
            "Đơn": st.column_config.NumberColumn("Số Đơn")
        })

        # Top Sản phẩm & Shop (Gộp logic hiển thị)
        p_stats = df_flt.groupby(['Tên Item', 'Shop id', 'Item id']).agg(Đơn=('ID đơn hàng','count'), HH=('Tổng hoa hồng đơn hàng(₫)','sum')).nlargest(10, 'Đơn').reset_index()
        p_stats['Link'] = p_stats.apply(lambda r: f"https://shopee.vn/product/{r['Shop id']}/{r['Item id']}", axis=1)
        
        display_top_table("5. Top 10 sản phẩm", p_stats[['Tên Item', 'Link', 'Đơn', 'HH']], {
            "Link": st.column_config.LinkColumn("Link Shopee"),
            "HH": st.column_config.NumberColumn("Hoa Hồng", format="%.0f ₫")
        })

        # --- MỤC 7: CHI TIẾT ---
        st.header("7. Chi tiết đơn hàng")
        tab_all, tab_pending, tab_cancel = st.tabs(["Tất cả", "Chờ xử lý", "Đã hủy"])
        
        with tab_all:
            st.dataframe(df_flt[['ID đơn hàng', 'Tên Shop', 'Tên Item', 'Giá(₫)', 'Trạng thái đặt hàng']], use_container_width=True)

else:
    st.info("👋 Chào mừng! Hãy tải file CSV từ Shopee Affiliate để bắt đầu phân tích.")
