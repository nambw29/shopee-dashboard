import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Cấu hình trang
st.set_page_config(page_title="Shopee Affiliate Dashboard", layout="wide", page_icon="🛒")

# --- HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        
        # 1. Xử lý thời gian
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
        # 2. Xử lý số liệu
        cols_to_numeric = [
            'Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
            'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
            'Giá(₫)', 'Số lượng'
        ]
        
        for col in cols_to_numeric:
            if col in df.columns:
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '').str.replace('₫', '').replace('nan', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. Phân loại nguồn đơn
        def classify_source(row):
            # Kết hợp cả cột Kênh và các Sub_id để tìm nguồn
            search_str = f"{row['Kênh']} {row['Sub_id1']} {row['Sub_id2']} {row['Sub_id3']} {row['Sub_id4']} {row['Sub_id5']}".lower()
            if 'video' in search_str: return 'Video'
            if 'live' in search_str: return 'Live'
            if any(x in search_str for x in ['facebook', 'fb', 'group']): return 'Facebook'
            if 'zalo' in search_str: return 'Zalo'
            if 'instagram' in search_str or 'ig' in search_str: return 'Instagram'
            return 'Others'
            
        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
        
        return df
    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Shopee Affiliate Analytics Dashboard")
st.markdown("---")

uploaded_file = st.file_uploader("Tải lên file báo cáo Shopee (.csv)", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Sidebar Filter
        st.sidebar.header("Bộ lọc")
        date_range = st.sidebar.date_input("Chọn khoảng thời gian", [df['Ngày'].min(), df['Ngày'].max()])
        
        if len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        # --- 1. THỐNG KÊ TỔNG QUAN ---
        st.header("1. Thống Kê Tổng Quan")
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_shopee = df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()
        comm_xtra = df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()
        total_orders = len(df_filtered)
        avg_comm = total_comm / total_orders if total_orders > 0 else 0
        comm_rate = (total_comm / total_gmv * 100) if total_gmv > 0 else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Tổng Doanh Thu", f"{total_gmv:,.0f} ₫")
        m2.metric("Tổng Hoa Hồng", f"{total_comm:,.0f} ₫")
        m3.metric("HH Shopee / Xtra", f"{comm_shopee:,.0f} / {comm_xtra:,.0f}")
        m4.metric("HH Trung bình/Đơn", f"{avg_comm:,.0f} ₫")
        m5.metric("Tỷ lệ HH", f"{comm_rate:.2f}%")

        # --- 2. THỐNG KÊ ĐƠN HÀNG ---
        st.header("2. Thống Kê Đơn Hàng")
        orders_video = df_filtered[df_filtered['Phân loại nguồn'] == 'Video'].shape[0]
        orders_live = df_filtered[df_filtered['Phân loại nguồn'] == 'Live'].shape[0]
        orders_social = df_filtered[df_filtered['Phân loại nguồn'].isin(['Facebook', 'Zalo', 'Instagram'])].shape[0]
        orders_cancelled = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)].shape[0]
        orders_zero = df_filtered[df_filtered['Tổng hoa hồng đơn hàng(₫)'] == 0].shape[0]

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Tổng đơn", total_orders)
        c2.metric("Đơn Video", orders_video)
        c3.metric("Đơn Live", orders_live)
        c4.metric("Đơn Social", orders_social)
        c5.metric("Đơn 0đ", orders_zero)
        c6.metric("Đơn Hủy", orders_cancelled)

        st.markdown("---")

        # --- 3. BIỂU ĐỒ ---
        st.header("3. Biểu Đồ Thống Kê")
        col_a, col_b = st.columns(2)
        
        with col_a:
            # HH theo ngày
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            st.plotly_chart(px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày"), use_container_width=True)
            
            # Đơn hàng theo kênh
            fig_source = px.pie(df_filtered, names='Phân loại nguồn', title="Tỷ trọng đơn hàng theo Kênh bán")
            st.plotly_chart(fig_source, use_container_width=True)

        with col_b:
            # HH theo giờ
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            st.plotly_chart(px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ"), use_container_width=True)
            
            # HH theo danh mục
            cat_comm = df_filtered.groupby('L1 Danh mục toàn cầu')['Tổng hoa hồng đơn hàng(₫)'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(cat_comm, x='Tổng hoa hồng đơn hàng(₫)', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục"), use_container_width=True)

        st.markdown("---")

        # --- 4, 5, 6. TOP LISTS ---
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("4. Top 5 Shop nhiều đơn nhất")
            top_shops = df_filtered.groupby('Tên Shop').agg({'Giá trị đơn hàng (₫)':'sum', 'ID đơn hàng':'count', 'Tổng hoa hồng đơn hàng(₫)':'sum'}).reset_index()
            top_shops['Tỷ lệ HH'] = (top_shops['Tổng hoa hồng đơn hàng(₫)']/top_shops['Giá trị đơn hàng (₫)']*100).round(2)
            st.dataframe(top_shops.sort_values('ID đơn hàng', ascending=False).head(5), hide_index=True)

        with col_t2:
            st.subheader("5. Top 5 Sản phẩm nổi bật")
            top_prods = df_filtered.groupby('Tên Item').agg({'Giá trị đơn hàng (₫)':'sum', 'Số lượng':'sum', 'Tổng hoa hồng đơn hàng(₫)':'sum'}).reset_index()
            top_prods['Tỷ lệ HH'] = (top_prods['Tổng hoa hồng đơn hàng(₫)']/top_prods['Giá trị đơn hàng (₫)']*100).round(2)
            st.dataframe(top_prods.sort_values('Số lượng', ascending=False).head(5), hide_index=True)

        # MỤC 6 CẬP NHẬT: QUÉT CẢ 5 CỘT SUB_ID
        st.subheader("6. Top 10 SubID đóng góp đơn nhiều nhất")
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        sub_list = []
        for col in sub_id_cols:
            if col in df_filtered.columns:
                temp = df_filtered[df_filtered[col].notna()][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp.columns = ['SubID', 'HoaHồng']
                sub_list.append(temp)
        
        if sub_list:
            all_subs = pd.concat(sub_list).groupby('SubID').agg(Số_đơn=('SubID','count'), Hoa_hồng=('HoaHồng','sum')).reset_index()
            st.dataframe(all_subs.sort_values('Số_đơn', ascending=False).head(15), use_container_width=True, hide_index=True)

        st.markdown("---")

        # --- 7. CHI TIẾT ĐƠN HÀNG ---
        st.header("7. Chi Tiết Đơn Hàng")
        tab_all, tab_pending, tab_cancel = st.tabs(["Tất cả đơn", "Chờ xử lý", "Đã hủy"])
        
        show_cols = ['ID đơn hàng', 'Tên Shop', 'Tên Item', 'Giá(₫)', 'Số lượng', 'Tổng hoa hồng đơn hàng(₫)', 'Trạng thái đặt hàng', 'Kênh', 'Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        valid_show_cols = [c for c in show_cols if c in df_filtered.columns]

        with tab_all:
            st.dataframe(df_filtered[valid_show_cols])
        with tab_pending:
            st.dataframe(df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('chờ', case=False, na=False)][valid_show_cols])
        with tab_cancel:
            st.dataframe(df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('hủy', case=False, na=False)][valid_show_cols])
