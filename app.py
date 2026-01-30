import streamlit as st
import pandas as pd
import plotly.express as px

# Cấu hình trang
st.set_page_config(page_title="Shopee Affiliate Dashboard", layout="wide", page_icon="🛒")

# --- HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
        cols_to_numeric = ['Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
                           'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
                           'Giá(₫)', 'Số lượng']
        for col in cols_to_numeric:
            if col in df.columns:
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '').str.replace('₫', '').replace('nan', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        def classify_source(row):
            search_str = f"{row['Kênh']} {row['Sub_id1']} {row['Sub_id2']} {row['Sub_id3']} {row['Sub_id4']} {row['Sub_id5']}".lower()
            if 'video' in search_str: return 'Video'
            if 'live' in search_str: return 'Live'
            if any(x in search_str for x in ['facebook', 'fb', 'group']): return 'Facebook'
            if 'zalo' in search_str: return 'Zalo'
            return 'Others'
            
        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Shopee Affiliate Analytics Dashboard")

uploaded_file = st.file_uploader("Tải lên file báo cáo Shopee (.csv)", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        # Filter Sidebar
        st.sidebar.header("Bộ lọc")
        date_range = st.sidebar.date_input("Khoảng thời gian", [df['Ngày'].min(), df['Ngày'].max()])
        df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])] if len(date_range) == 2 else df

        # --- 1 & 2. TỔNG QUAN ---
        st.header("1 & 2. Tổng Quan & Đơn Hàng")
        m1, m2, m3, m4, m5 = st.columns(5)
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        m1.metric("Tổng Hoa Hồng", f"{total_comm:,.0f} ₫".replace(',', '.'))
        m2.metric("Tổng đơn", f"{len(df_filtered):,}".replace(',', '.'))
        m3.metric("Đơn Hủy", f"{df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)].shape[0]:,}".replace(',', '.'))
        m4.metric("Đơn Video/Live", f"{df_filtered[df_filtered['Phân loại nguồn'].isin(['Video', 'Live'])].shape[0]:,}".replace(',', '.'))
        m5.metric("Tỷ lệ HH", f"{(total_comm/df_filtered['Giá trị đơn hàng (₫)'].sum()*100):.2f}%")

        st.markdown("---")

        # --- 6. LIỆT KÊ TOP 20 SUBID (PHÂN TRANG & ĐỊNH DẠNG) ---
        st.header("6. Top 20 SubID đóng góp đơn nhiều nhất")
        
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        sub_list = []
        for col in sub_id_cols:
            if col in df_filtered.columns:
                temp = df_filtered[df_filtered[col].notna()][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp.columns = ['SubID', 'HoaHồng']
                sub_list.append(temp)
        
        if sub_list:
            # Gộp và tính toán Top 20
            all_subs = pd.concat(sub_list).groupby('SubID').agg(
                Số_đơn=('SubID','count'), 
                Hoa_hồng=('HoaHồng','sum')
            ).reset_index().sort_values('Số_đơn', ascending=False).head(20)
            
            # Thêm cột STT (Số thứ tự)
            all_subs.insert(0, 'STT', range(1, len(all_subs) + 1))
            
            # Logic Phân trang
            col_page, _ = st.columns([2, 3])
            page_choice = col_page.radio("Chọn trang hiển thị:", ["Trang 1 (STT 1-10)", "Trang 2 (STT 11-20)"], horizontal=True)
            
            if "Trang 1" in page_choice:
                display_df = all_subs.iloc[0:10].copy()
            else:
                display_df = all_subs.iloc[10:20].copy()
            
            # Định dạng hiển thị số tiền và số đơn cho dễ nhìn
            display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(lambda x: f"{int(round(x, 0)):,}".replace(',', '.') + " ₫")
            display_df['Số_đơn'] = display_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            # Hiển thị bảng tĩnh (st.table) để đẹp hơn cho dữ liệu ít dòng
            st.table(display_df)
            
            if st.checkbox("Xem toàn bộ danh sách (Top 20)"):
                 st.dataframe(all_subs, use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy dữ liệu SubID.")

        st.markdown("---")
        # --- 7. CHI TIẾT ĐƠN HÀNG ---
        st.header("7. Chi Tiết Đơn Hàng")
        st.dataframe(df_filtered, use_container_width=True)
