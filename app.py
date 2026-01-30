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
        
        # 2. Xử lý số liệu (xóa dấu phẩy, chuyển sang số)
        cols_to_numeric = [
            'Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
            'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
            'Giá(₫)', 'Số lượng'
        ]
        
        for col in cols_to_numeric:
            if col in df.columns:
                # Xử lý nếu dữ liệu dạng chuỗi có dấu phẩy ngàn
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '').str.replace('₫', '').replace('nan', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. Tạo cột phân loại Đơn Video/Live dựa trên cột "Kênh" hoặc "Sub_id"
        # Lưu ý: Logic này phụ thuộc vào cách Shopee trả về trong file của bạn.
        # Ở đây tôi giả định tìm từ khóa trong cột "Kênh"
        def classify_source(channel):
            channel = str(channel).lower()
            if 'video' in channel: return 'Video'
            if 'live' in channel: return 'Live'
            if 'facebook' in channel or 'instagram' in channel or 'zalo' in channel: return 'Social'
            return 'Khác'
            
        df['Phân loại nguồn'] = df['Kênh'].apply(classify_source)
        
        return df
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Phân Tích Hiệu Suất Shopee Affiliate")
st.markdown("---")

# Upload File
uploaded_file = st.file_uploader("Tải lên file CSV báo cáo Shopee của bạn", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Sidebar bộ lọc
        st.sidebar.header("Bộ lọc dữ liệu")
        
        # Lọc theo ngày
        min_date = df['Thời Gian Đặt Hàng'].min()
        max_date = df['Thời Gian Đặt Hàng'].max()
        date_range = st.sidebar.date_input("Chọn khoảng thời gian", [min_date, max_date])
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df[(df['Thời Gian Đặt Hàng'].dt.date >= start_date) & (df['Thời Gian Đặt Hàng'].dt.date <= end_date)]
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

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Tổng Doanh Thu (GMV)", f"{total_gmv:,.0f} ₫")
        col2.metric("Tổng Hoa Hồng", f"{total_comm:,.0f} ₫")
        col3.metric("HH Shopee / Xtra", f"{comm_shopee:,.0f} / {comm_xtra:,.0f}")
        col4.metric("HH Trung bình/Đơn", f"{avg_comm:,.0f} ₫")
        col5.metric("Tỷ lệ Hoa hồng", f"{comm_rate:.2f}%")

        st.markdown("---")

        # --- 2. THỐNG KÊ ĐƠN HÀNG ---
        st.header("2. Thống Kê Đơn Hàng")
        
        # Phân loại đơn
        orders_video = df_filtered[df_filtered['Phân loại nguồn'] == 'Video'].shape[0]
        orders_live = df_filtered[df_filtered['Phân loại nguồn'] == 'Live'].shape[0]
        orders_social = df_filtered[df_filtered['Phân loại nguồn'] == 'Social'].shape[0]
        orders_cancelled = df_filtered[df_filtered['Trạng thái đặt hàng'] == 'Đã hủy'].shape[0]
        orders_zero_comm = df_filtered[df_filtered['Tổng hoa hồng đơn hàng(₫)'] == 0].shape[0]
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Tổng Số Đơn", total_orders)
        c2.metric("Đơn Video", orders_video)
        c3.metric("Đơn Live", orders_live)
        c4.metric("Đơn Social", orders_social)
        c5.metric("Đơn 0 đồng", orders_zero_comm, delta_color="inverse")
        c6.metric("Đơn Hủy", orders_cancelled, delta_color="inverse")

        st.markdown("---")

        # --- 3. BIỂU ĐỒ ---
        st.header("3. Biểu Đồ Phân Tích")
        
        tab1, tab2, tab3 = st.tabs(["Thời gian & Xu hướng", "Kênh & Danh mục", "Cơ cấu Hoa hồng"])
        
        with tab1:
            col_chart1, col_chart2 = st.columns(2)
            
            # Biểu đồ hoa hồng theo ngày
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig_daily = px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title='Xu hướng Hoa hồng theo Ngày', markers=True)
            col_chart1.plotly_chart(fig_daily, use_container_width=True)
            
            # Biểu đồ hoa hồng theo giờ
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig_hourly = px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title='Khung giờ ra nhiều Hoa hồng nhất')
            col_chart2.plotly_chart(fig_hourly, use_container_width=True)

        with tab2:
            col_chart3, col_chart4 = st.columns(2)
            
            # Biểu đồ theo kênh bán hàng (Dựa trên cột Kênh gốc)
            channel_counts = df_filtered['Kênh'].value_counts().reset_index()
            channel_counts.columns = ['Kênh', 'Số đơn']
            fig_channel = px.pie(channel_counts, names='Kênh', values='Số đơn', title='Tỷ trọng Đơn hàng theo Kênh (Source)', hole=0.4)
            col_chart3.plotly_chart(fig_channel, use_container_width=True)
            
            # Biểu đồ theo danh mục
            cat_comm = df_filtered.groupby('L1 Danh mục toàn cầu')['Tổng hoa hồng đơn hàng(₫)'].sum().nlargest(10).reset_index()
            fig_cat = px.bar(cat_comm, x='Tổng hoa hồng đơn hàng(₫)', y='L1 Danh mục toàn cầu', orientation='h', title='Top 10 Danh mục hái ra tiền')
            col_chart4.plotly_chart(fig_cat, use_container_width=True)

        with tab3:
             # Biểu đồ Hoa hồng Shopee vs Xtra
             comm_breakdown = pd.DataFrame({
                 'Loại': ['Shopee', 'Xtra'],
                 'Giá trị': [comm_shopee, comm_xtra]
             })
             fig_breakdown = px.pie(comm_breakdown, names='Loại', values='Giá trị', title='Tỷ lệ Hoa hồng Shopee vs Xtra')
             st.plotly_chart(fig_breakdown, use_container_width=True)

        st.markdown("---")

        # --- 4 & 5 & 6. TOP LIST ---
        st.header("Bảng Xếp Hạng Top")
        
        col_top1, col_top2 = st.columns(2)
        
        with col_top1:
            st.subheader("4. Top 5 Shop nhiều đơn nhất")
            top_shops = df_filtered.groupby('Tên Shop').agg({
                'Giá trị đơn hàng (₫)': 'sum',
                'Số lượng': 'count', # Đếm dòng coi như số đơn
                'Tổng hoa hồng đơn hàng(₫)': 'sum'
            }).reset_index()
            top_shops['Tỉ lệ HH'] = (top_shops['Tổng hoa hồng đơn hàng(₫)'] / top_shops['Giá trị đơn hàng (₫)'] * 100).round(2)
            top_shops.columns = ['Tên Shop', 'Tổng GMV', 'Số đơn', 'Hoa hồng', 'Tỉ lệ HH (%)']
            st.dataframe(top_shops.sort_values('Số đơn', ascending=False).head(5), hide_index=True)

        with col_top2:
            st.subheader("5. Top 5 Sản phẩm nổi bật (theo Hoa hồng)")
            top_items = df_filtered.groupby('Tên Item').agg({
                'Giá trị đơn hàng (₫)': 'sum',
                'Số lượng': 'sum',
                'Tổng hoa hồng đơn hàng(₫)': 'sum'
            }).reset_index()
            top_items['Tỉ lệ HH'] = (top_items['Tổng hoa hồng đơn hàng(₫)'] / top_items['Giá trị đơn hàng (₫)'] * 100).round(2)
            top_items.columns = ['Tên Sản Phẩm', 'Tổng GMV', 'Số lượng bán', 'Hoa hồng', 'Tỉ lệ HH (%)']
            st.dataframe(top_items.sort_values('Hoa hồng', ascending=False).head(5), hide_index=True)

        st.subheader("6. Top 10 SubID hiệu quả nhất")
        if 'Sub_id1' in df_filtered.columns:
            top_sub = df_filtered.groupby('Sub_id1').agg({
                'Số lượng': 'count',
                'Tổng hoa hồng đơn hàng(₫)': 'sum'
            }).reset_index()
            top_sub.columns = ['SubID', 'Số lượng đơn', 'Tổng hoa hồng']
            st.dataframe(top_sub.sort_values('Tổng hoa hồng', ascending=False).head(10), use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy cột Sub_id1 trong dữ liệu")

        st.markdown("---")

        # --- 7. CHI TIẾT ĐƠN HÀNG ---
        st.header("7. Chi Tiết Đơn Hàng")
        
        view_option = st.radio("Chọn loại đơn hàng muốn xem:", ["Tất cả đơn", "Đơn đang chờ xử lý", "Đơn đã hủy"], horizontal=True)
        
        columns_to_show = [
            'ID đơn hàng', 'Tên Shop', 'Tên Item', 'Giá(₫)', 'Số lượng', 
            'Tổng hoa hồng đơn hàng(₫)', 'Trạng thái đặt hàng', 'Kênh', 
            'Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5'
        ]
        # Đảm bảo chỉ lấy cột có trong file
        valid_cols = [c for c in columns_to_show if c in df_filtered.columns]

        if view_option == "Tất cả đơn":
            st.write(f"Tổng số: {len(df_filtered)} đơn")
            st.dataframe(df_filtered[valid_cols], use_container_width=True)
            
        elif view_option == "Đơn đang chờ xử lý":
            # Chú ý: Cần kiểm tra chính xác text trong CSV, thường là "Đang chờ xử lý" hoặc "Chờ xử lý"
            pending_orders = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('chờ', case=False, na=False)]
            st.write(f"Tổng số: {len(pending_orders)} đơn")
            st.dataframe(pending_orders[valid_cols], use_container_width=True)
            
        elif view_option == "Đơn đã hủy":
            cancelled_orders = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('hủy', case=False, na=False)]
            st.write(f"Tổng số: {len(cancelled_orders)} đơn")
            st.dataframe(cancelled_orders[valid_cols], use_container_width=True)

    else:
        st.info("Vui lòng tải lên file CSV để bắt đầu phân tích.")