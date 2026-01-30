import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình trang
st.set_page_config(page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29", layout="wide", page_icon="🧧")

# --- CSS để Việt hóa và tùy chỉnh vùng tải tệp ---
st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {
        display: none;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "Kéo và thả tệp vào đây";
        display: block;
        font-size: 1.2em;
        font-weight: bold;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "Hỗ trợ tệp .CSV";
        display: block;
        font-size: 0.8em;
    }
    .stFileUploader section button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HÀM FORMAT SỐ TIỀN ---
def format_currency(value):
    """Định dạng số tiền theo kiểu: 868.368.902 ₫"""
    return f"{int(round(value, 0)):,}".replace(',', '.') + " ₫"

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

        # PHÂN LOẠI NGUỒN ĐƠN THEO KÊNH THỰC TẾ
        def classify_source(row):
            kenh = str(row.get('Kênh', '')).strip()
            
            # Giữ nguyên tên kênh từ dữ liệu gốc
            if kenh in ['Facebook', 'Instagram', 'Zalo', 'Websites', 'Others']:
                return kenh
            elif kenh == '':
                return 'Không xác định'
            else:
                return kenh  # Giữ nguyên các kênh khác như EdgeBrowser, etc.
            
        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

uploaded_file = st.file_uploader("", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        
        # 2. Bộ lọc thời gian
        st.markdown("### Chọn khoảng thời gian")
        date_range = st.date_input("Thời gian:", [df['Ngày'].min(), df['Ngày'].max()], format="DD/MM/YYYY")
        
        if len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # 3. MỤC 1: THỐNG KÊ TỔNG QUAN
        st.header("1. Thống kê tổng quan")
        
        # TÍNH TOÁN THEO ĐƠN HÀNG (ID đơn hàng unique)
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df_filtered['ID đơn hàng'].nunique()  # ĐẾM UNIQUE ORDER ID
        total_clicks = df_filtered['Thời gian Click'].nunique()  # SỐ CLICK UNIQUE
        total_quantity_sold = int(df_filtered['Số lượng'].sum())  # TỔNG SỐ LƯỢNG ĐÃ BÁN
        
        # Tính hoa hồng theo kênh (group by order ID để tránh tính trùng)
        comm_by_channel = df_filtered.groupby(['ID đơn hàng', 'Phân loại nguồn'])['Tổng hoa hồng đơn hàng(₫)'].first().reset_index()
        comm_facebook = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Facebook']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_instagram = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Instagram']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_others = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Others']['Tổng hoa hồng đơn hàng(₫)'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng Doanh Thu", format_currency(total_gmv))
        m2.metric("Tổng Hoa Hồng", format_currency(total_comm))
        m3.metric("Tổng Đơn Hàng", f"{total_orders:,}".replace(',', '.'))
        
        m4, m5, m6, m7 = st.columns(4)
        m4.metric("HH TB/Đơn", format_currency(total_comm/total_orders if total_orders > 0 else 0))
        m5.metric("HH Facebook", format_currency(comm_facebook))
        m6.metric("HH Instagram", format_currency(comm_instagram))
        m7.metric("HH Others", format_currency(comm_others))
        
        m8, m9, m10 = st.columns(3)
        m8.metric("Tỷ Lệ Hoa Hồng", f"{(total_comm/total_gmv*100 if total_gmv > 0 else 0):.2f}%")
        m9.metric("Số Lượng Click", f"{total_clicks:,}".replace(',', '.'))
        m10.metric("Số Lượng Đã Bán", f"{total_quantity_sold:,}".replace(',', '.'))

        # MỤC 2: THỐNG KÊ ĐƠN HÀNG
        st.header("2. Thống kê đơn hàng")
        
        # Đếm đơn hàng unique theo kênh
        orders_by_channel = df_filtered.groupby('Phân loại nguồn')['ID đơn hàng'].nunique()
        orders_facebook = orders_by_channel.get('Facebook', 0)
        orders_instagram = orders_by_channel.get('Instagram', 0)
        orders_others = orders_by_channel.get('Others', 0)
        orders_cancelled = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)]['ID đơn hàng'].nunique()
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("HH Shopee", format_currency(df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()))
        c2.metric("HH Xtra", format_currency(df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()))
        c3.metric("Đơn Facebook", f"{orders_facebook:,}".replace(',', '.'))
        c4.metric("Đơn Instagram", f"{orders_instagram:,}".replace(',', '.'))
        c5.metric("Đơn Others", f"{orders_others:,}".replace(',', '.'))
        c6.metric("Đơn Hủy", f"{orders_cancelled:,}".replace(',', '.'))

        st.markdown("---")

        # 4 & 5 & 6. BIỂU ĐỒ (Hover chuẩn 868.368.902 ₫)
        st.header("3. Biểu đồ thống kê")
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Biểu đồ Hoa hồng theo ngày
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            daily_comm['Ngày_str'] = daily_comm['Ngày'].apply(lambda x: x.strftime('%d/%m/%Y'))
            daily_comm['Hoa_hồng_formatted'] = daily_comm['Tổng hoa hồng đơn hàng(₫)'].apply(format_currency)
            
            fig1 = px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày")
            fig1.update_traces(
                hovertemplate="<b>Ngày:</b> %{customdata[0]}<br><b>Hoa hồng:</b> %{customdata[1]}<extra></extra>",
                customdata=daily_comm[['Ngày_str', 'Hoa_hồng_formatted']]
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Biểu đồ tròn - Tỷ trọng đơn hàng theo kênh (ĐẾM UNIQUE ORDER)
            channel_orders = df_filtered.groupby('Phân loại nguồn')['ID đơn hàng'].nunique().reset_index()
            channel_orders.columns = ['Kênh', 'Số đơn']
            channel_orders['Tỷ trọng'] = (channel_orders['Số đơn'] / channel_orders['Số đơn'].sum() * 100).round(2)
            
            fig2 = px.pie(
                channel_orders, 
                names='Kênh', 
                values='Số đơn',
                title="Tỷ trọng đơn hàng theo kênh",
                hover_data=['Tỷ trọng']
            )
            fig2.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Số đơn: %{value:,}<br>Tỷ trọng: %{customdata[0]:.2f}%<extra></extra>"
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            # Biểu đồ Hoa hồng theo khung giờ
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            hourly_comm['Hoa_hồng_formatted'] = hourly_comm['Tổng hoa hồng đơn hàng(₫)'].apply(format_currency)
            
            fig3 = px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
            fig3.update_traces(
                hovertemplate="<b>Giờ:</b> %{x}h<br><b>Hoa hồng:</b> %{customdata}<extra></extra>",
                customdata=hourly_comm['Hoa_hồng_formatted']
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Top 10 Danh mục
            cat_data = df_filtered.groupby('L1 Danh mục toàn cầu').agg(
                Số_đơn=('ID đơn hàng', 'count'), 
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            ).nlargest(10, 'Hoa_hồng').reset_index()
            
            cat_data['Số_đơn_formatted'] = cat_data['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            cat_data['Hoa_hồng_formatted'] = cat_data['Hoa_hồng'].apply(format_currency)
            
            fig4 = px.bar(cat_data, x='Hoa_hồng', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục")
            fig4.update_traces(
                hovertemplate="<b>Số đơn:</b> %{customdata[0]}<br><b>Hoa hồng:</b> %{customdata[1]}<extra></extra>",
                customdata=cat_data[['Số_đơn_formatted', 'Hoa_hồng_formatted']]
            )
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("---")
        # TOP 20 SUBID
        st.header("4. Top 20 SubID hiệu quả nhất")
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        sub_list = []
        for col in sub_id_cols:
            if col in df_filtered.columns:
                temp = df_filtered[df_filtered[col].notna() & (df_filtered[col] != '')][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp.columns = ['SubID', 'HoaHồng']
                sub_list.append(temp)
        
        if sub_list:
            all_subs = pd.concat(sub_list).groupby('SubID').agg(Số_đơn=('SubID','count'), Hoa_hồng=('HoaHồng','sum')).reset_index().sort_values('Số_đơn', ascending=False).head(20)
            all_subs.insert(0, 'STT', range(1, len(all_subs) + 1))
            display_df = all_subs.copy()
            display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(format_currency)
            display_df['Số_đơn'] = display_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # MỤC 5: CHI TIẾT ĐƠN HÀNG
        st.header("5. Chi Tiết Đơn Hàng")
        
        # Chuẩn bị dữ liệu chi tiết
        detail_cols = ['ID đơn hàng', 'Tên Shop', 'Tên Item', 'Giá(₫)', 'Số lượng', 
                       'Tổng hoa hồng đơn hàng(₫)', 'Trạng thái đặt hàng', 'Kênh', 
                       'Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        
        df_detail = df_filtered[detail_cols].copy()
        
        # Format lại cột Giá và Tổng hoa hồng
        df_detail['Giá(₫)'] = df_detail['Giá(₫)'].apply(lambda x: format_currency(x))
        df_detail['Tổng hoa hồng đơn hàng(₫)'] = df_detail['Tổng hoa hồng đơn hàng(₫)'].apply(lambda x: format_currency(x))
        df_detail['Số lượng'] = df_detail['Số lượng'].apply(lambda x: int(x))
        
        # Đổi tên cột cho dễ đọc
        df_detail.columns = ['ID Đơn Hàng', 'Tên Shop', 'Tên Sản Phẩm', 'Giá', 'Số Lượng', 
                            'Tổng Hoa Hồng', 'Trạng Thái', 'Kênh', 
                            'SubID 1', 'SubID 2', 'SubID 3', 'SubID 4', 'SubID 5']
        
        # Tạo tabs cho các loại đơn hàng
        tab1, tab2, tab3 = st.tabs([
            f"📦 Tất cả đơn ({len(df_detail):,} dòng)".replace(',', '.'),
            f"⏳ Đơn đang chờ xử lý ({df_detail[df_detail['Trạng Thái'].str.contains('chờ xử lý', case=False, na=False)].shape[0]:,} dòng)".replace(',', '.'),
            f"❌ Đơn đã hủy ({df_detail[df_detail['Trạng Thái'].str.contains('Hủy', case=False, na=False)].shape[0]:,} dòng)".replace(',', '.')
        ])
        
        with tab1:
            st.markdown(f"**Tổng số dòng:** {len(df_detail):,}".replace(',', '.'))
            st.dataframe(df_detail, use_container_width=True, hide_index=True, height=500)
        
        with tab2:
            df_pending = df_detail[df_detail['Trạng Thái'].str.contains('chờ xử lý', case=False, na=False)]
            st.markdown(f"**Tổng số dòng:** {len(df_pending):,}".replace(',', '.'))
            if len(df_pending) > 0:
                st.dataframe(df_pending, use_container_width=True, hide_index=True, height=500)
            else:
                st.info("Không có đơn hàng đang chờ xử lý")
        
        with tab3:
            df_cancelled = df_detail[df_detail['Trạng Thái'].str.contains('Hủy', case=False, na=False)]
            st.markdown(f"**Tổng số dòng:** {len(df_cancelled):,}".replace(',', '.'))
            if len(df_cancelled) > 0:
                st.dataframe(df_cancelled, use_container_width=True, hide_index=True, height=500)
            else:
                st.info("Không có đơn hàng đã hủy")
