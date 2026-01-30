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
            # Kiểm tra chính xác cột Kênh từ file Shopee
            kenh = str(row.get('Kênh', '')).lower()
            sub_ids = f"{row['Sub_id1']} {row['Sub_id2']} {row['Sub_id3']} {row['Sub_id4']} {row['Sub_id5']}".lower()
            
            if 'video' in kenh: return 'Video'
            if 'live' in kenh or 'livestream' in kenh: return 'Live'
            if 'facebook' in sub_ids or 'fb' in sub_ids: return 'Facebook'
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
        
        # --- BỘ LỌC KHOẢNG THỜI GIAN NGAY TRÊN TRANG CHÍNH ---
        st.markdown("### 📅 Bộ lọc thời gian")
        col_date, _ = st.columns([4, 6])
        with col_date:
            date_range = st.date_input(
                "Chọn ngày bắt đầu và ngày kết thúc:",
                [df['Ngày'].min(), df['Ngày'].max()]
            )
        
        # Xử lý lọc dữ liệu
        if len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # --- 1 & 2. TỔNG QUAN & NGUỒN ĐƠN ---
        st.header("1 & 2. Thống Kê Tổng Quan")
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng Doanh Thu", f"{total_gmv:,.0f}".replace(',', '.') + " ₫")
        m2.metric("Tổng Hoa Hồng", f"{total_comm:,.0f}".replace(',', '.') + " ₫")
        m3.metric("Tổng đơn hàng", f"{len(df_filtered):,}".replace(',', '.'))
        m4.metric("Tỷ lệ HH TB", f"{(total_comm / total_gmv * 100) if total_gmv > 0 else 0:.2f}%")

        o_video = df_filtered[df_filtered['Phân loại nguồn'] == 'Video'].shape[0]
        o_live = df_filtered[df_filtered['Phân loại nguồn'] == 'Live'].shape[0]
        o_fb = df_filtered[df_filtered['Phân loại nguồn'] == 'Facebook'].shape[0]
        o_cancel = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)].shape[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Đơn từ Video", f"{o_video:,}".replace(',', '.'))
        c2.metric("Đơn từ Live", f"{o_live:,}".replace(',', '.'))
        c3.metric("Đơn từ Facebook", f"{o_fb:,}".replace(',', '.'))
        c4.metric("Đơn đã Hủy", f"{o_cancel:,}".replace(',', '.'))

        st.markdown("---")

        # --- 6. TOP 20 SUBID (STT, PHÂN TRANG, ĐỊNH DẠNG SỐ) ---
        st.header("6. Top 20 SubID hiệu quả nhất")
        
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        sub_list = []
        for col in sub_id_cols:
            if col in df_filtered.columns:
                temp = df_filtered[df_filtered[col].notna() & (df_filtered[col] != '')][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp.columns = ['SubID', 'HoaHồng']
                sub_list.append(temp)
        
        if sub_list:
            all_subs = pd.concat(sub_list).groupby('SubID').agg(
                Số_đơn=('SubID','count'), 
                Hoa_hồng=('HoaHồng','sum')
            ).reset_index().sort_values('Số_đơn', ascending=False).head(20)
            
            all_subs.insert(0, 'STT', range(1, len(all_subs) + 1))
            
            col_sel, _ = st.columns([3, 7])
            page = col_sel.radio("Chọn trang hiển thị:", ["Top 1-10", "Top 11-20"], horizontal=True)
            
            start_idx = 0 if "1-10" in page else 10
            display_df = all_subs.iloc[start_idx : start_idx + 10].copy()
            
            # Định dạng số tiền dấu chấm, làm tròn
            display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(lambda x: f"{int(round(x, 0)):,}".replace(',', '.') + " ₫")
            display_df['Số_đơn'] = display_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            st.table(display_df)
        else:
            st.info("Không tìm thấy dữ liệu mã SubID.")

        st.markdown("---")
        st.header("7. Chi Tiết Đơn Hàng")
        st.dataframe(df_filtered, use_container_width=True)
