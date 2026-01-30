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
        # 1. Xử lý thời gian
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
        # 2. Xử lý số liệu (Xóa dấu phẩy, chuyển về số)
        cols_to_numeric = ['Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
                           'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
                           'Giá(₫)', 'Số lượng']
        for col in cols_to_numeric:
            if col in df.columns:
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '').str.replace('₫', '').replace('nan', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. Phân loại nguồn đơn (Giữ nguyên logic chính xác)
        def classify_source(row):
            kenh = str(row.get('Kênh', '')).lower()
            sub_ids = f"{row['Sub_id1']} {row['Sub_id2']} {row['Sub_id3']} {row['Sub_id4']} {row['Sub_id5']}".lower()
            if 'video' in kenh: return 'Video'
            if 'live' in kenh or 'livestream' in kenh: return 'Live'
            if any(x in sub_ids for x in ['facebook', 'fb', 'group']): return 'Facebook'
            if 'zalo' in sub_ids: return 'Zalo'
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
        
        # --- BỘ LỌC THỜI GIAN (HIỂN THỊ TRỰC TIẾP) ---
        st.markdown("### 📅 Bộ lọc thời gian")
        col_date, _ = st.columns([4, 6])
        with col_date:
            date_range = st.date_input("Chọn khoảng ngày:", [df['Ngày'].min(), df['Ngày'].max()])
        
        if len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # --- 1 & 2. TỔNG QUAN & THỐNG KÊ ĐƠN ---
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

        # --- 3. BIỂU ĐỒ THỐNG KÊ ---
        st.header("3. Biểu Đồ Thống Kê")
        col_a, col_b = st.columns(2)
        with col_a:
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            st.plotly_chart(px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày"), use_container_width=True)
            fig_source = px.pie(df_filtered, names='Phân loại nguồn', title="Tỷ trọng đơn hàng theo Kênh")
            st.plotly_chart(fig_source, use_container_width=True)
        with col_b:
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            st.plotly_chart(px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ"), use_container_width=True)
            cat_comm = df_filtered.groupby('L1 Danh mục toàn cầu')['Tổng hoa hồng đơn hàng(₫)'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(cat_comm, x='Tổng hoa hồng đơn hàng(₫)', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục"), use_container_width=True)

        st.markdown("---")

        # --- 4 & 5. TOP SHOP & SẢN PHẨM ---
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("4. Top 5 Shop nhiều đơn nhất")
            top_shops = df_filtered.groupby('Tên Shop').agg({'ID đơn hàng':'count', 'Tổng hoa hồng đơn hàng(₫)':'sum'}).reset_index()
            top_shops.columns = ['Tên Shop', 'Số đơn', 'Hoa hồng']
            top_shops['Hoa hồng'] = top_shops['Hoa hồng'].apply(lambda x: f"{x:,.0f}".replace(',', '.') + " ₫")
            st.dataframe(top_shops.sort_values('Số đơn', ascending=False).head(5), hide_index=True, use_container_width=True)

        with col_t2:
            st.subheader("5. Top 5 Sản phẩm nổi bật")
            top_prods = df_filtered.groupby('Tên Item').agg({'Số lượng':'sum', 'Tổng hoa hồng đơn hàng(₫)':'sum'}).reset_index()
            top_prods.columns = ['Tên Sản Phẩm', 'Số lượng', 'Hoa hồng']
            top_prods['Hoa hồng'] = top_prods['Hoa hồng'].apply(lambda x: f"{x:,.0f}".replace(',', '.') + " ₫")
            st.dataframe(top_prods.sort_values('Số lượng', ascending=False).head(5), hide_index=True, use_container_width=True)

        st.markdown("---")

        # --- 6. TOP 20 SUBID HIỆU QUẢ NHẤT (SỬA THEO YÊU CẦU) ---
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
            
            # Thêm cột STT và ẩn Index mặc định
            all_subs.insert(0, 'STT', range(1, len(all_subs) + 1))
            
            # Định dạng hiển thị
            display_subs = all_subs.copy()
            display_subs['Hoa_hồng'] = display_subs['Hoa_hồng'].apply(lambda x: f"{int(round(x,0)):,}".replace(',', '.') + " ₫")
            display_subs['Số_đơn'] = display_subs['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            st.dataframe(display_subs, use_container_width=True, hide_index=True)
        else:
            st.info("Không có dữ liệu SubID.")

        st.markdown("---")

        # --- 7. CHI TIẾT ĐƠN HÀNG ---
        st.header("7. Chi Tiết Đơn Hàng")
        st.dataframe(df_filtered, use_container_width=True)
