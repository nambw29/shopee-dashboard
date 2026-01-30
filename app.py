import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình trang với tiêu đề mới và icon mới
st.set_page_config(page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29", layout="wide", page_icon="🧧")

# --- CSS để Việt hóa Browse Files ---
st.markdown("""
    <style>
    .stFileUploader section button {
        content: "Chọn tệp";
    }
    .stFileUploader section button::after {
        content: "Chọn tệp";
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
        content: "Kéo và thả tệp vào đây";
        display: block;
        font-size: 1em;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

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

        # PHÂN LOẠI NGUỒN ĐƠN (Sửa lỗi Other và Facebook)
        def classify_source(row):
            kenh = str(row.get('Kênh', '')).lower()
            sub_ids = f"{row['Sub_id1']} {row['Sub_id2']} {row['Sub_id3']} {row['Sub_id4']} {row['Sub_id5']}".lower()
            
            if 'video' in kenh or 'video' in sub_ids: return 'Video'
            if 'live' in kenh or 'livestream' in kenh or 'live' in sub_ids: return 'Live'
            if any(x in sub_ids for x in ['facebook', 'fb', 'group', 'social', 'ig', 'zalo']): return 'Social'
            return 'Others'
            
        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

uploaded_file = st.file_uploader("Chọn tệp báo cáo Shopee (.csv)", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        
        # 2. Bộ lọc thời gian dd/mm/yyyy
        st.markdown("### Chọn khoảng thời gian")
        date_range = st.date_input(
            "Thời gian:",
            [df['Ngày'].min(), df['Ngày'].max()],
            format="DD/MM/YYYY"
        )
        
        if len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # 3. MỤC 1: THỐNG KÊ TỔNG QUAN
        st.header("1. Thống kê tổng quan")
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = len(df_filtered)
        avg_comm = total_comm / total_orders if total_orders > 0 else 0
        
        comm_video = df_filtered[df_filtered['Phân loại nguồn'] == 'Video']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_live = df_filtered[df_filtered['Phân loại nguồn'] == 'Live']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_social = df_filtered[df_filtered['Phân loại nguồn'] == 'Social']['Tổng hoa hồng đơn hàng(₫)'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng Doanh Thu", f"{total_gmv:,.0f}".replace(',', '.') + " ₫")
        m2.metric("Tổng Hoa Hồng", f"{total_comm:,.0f}".replace(',', '.') + " ₫")
        m3.metric("Tổng Đơn Hàng", f"{total_orders:,}".replace(',', '.'))
        
        m4, m5, m6, m7 = st.columns(4)
        m4.metric("HH TB/Đơn", f"{avg_comm:,.0f}".replace(',', '.') + " ₫")
        m5.metric("HH Video", f"{comm_video:,.0f}".replace(',', '.') + " ₫")
        m6.metric("HH Live", f"{comm_live:,.0f}".replace(',', '.') + " ₫")
        m7.metric("HH Social", f"{comm_social:,.0f}".replace(',', '.') + " ₫")
        st.metric("Tỷ Lệ Hoa Hồng", f"{(total_comm/total_gmv*100):.2f}%")

        # MỤC 2: THỐNG KÊ ĐƠN HÀNG
        st.header("2. Thống kê đơn hàng")
        hh_shopee = df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()
        hh_xtra = df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()
        o_video = df_filtered[df_filtered['Phân loại nguồn'] == 'Video'].shape[0]
        o_live = df_filtered[df_filtered['Phân loại nguồn'] == 'Live'].shape[0]
        o_social = df_filtered[df_filtered['Phân loại nguồn'] == 'Social'].shape[0]
        o_cancel = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)].shape[0]

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("HH Shopee", f"{hh_shopee:,.0f}".replace(',', '.') + " ₫")
        c2.metric("HH Xtra", f"{hh_xtra:,.0f}".replace(',', '.') + " ₫")
        c3.metric("Đơn Video", f"{o_video:,}".replace(',', '.'))
        c4.metric("Đơn Live", f"{o_live:,}".replace(',', '.'))
        c5.metric("Đơn Social", f"{o_social:,}".replace(',', '.'))
        c6.metric("Đơn Hủy", f"{o_cancel:,}".replace(',', '.'))

        st.markdown("---")

        # 4 & 5. BIỂU ĐỒ (Hover ngắn gọn, định dạng tiền VNĐ)
        st.header("3. Biểu đồ thống kê")
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Hoa hồng theo ngày
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig1 = px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày")
            fig1.update_traces(hovertemplate="Ngày: %{x}<br>Hoa hồng: %{y:,.0f} VNĐ".replace(',', '.'))
            st.plotly_chart(fig1, use_container_width=True)
            
            # Tỷ trọng theo nguồn
            fig2 = px.pie(df_filtered, names='Phân loại nguồn', title="Tỷ trọng đơn hàng theo kênh")
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            # Hoa hồng theo giờ
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            fig3 = px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
            fig3.update_traces(hovertemplate="Giờ: %{x}h<br>Hoa hồng: %{y:,.0f} VNĐ".replace(',', '.'))
            st.plotly_chart(fig3, use_container_width=True)
            
            # Top 10 Danh mục (Hover: đơn + hoa hồng)
            cat_data = df_filtered.groupby('L1 Danh mục toàn cầu').agg(
                Số_đơn=('ID đơn hàng', 'count'),
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            ).nlargest(10, 'Hoa_hồng').reset_index()
            
            fig4 = px.bar(cat_data, x='Hoa_hồng', y='L1 Danh mục toàn cầu', orientation='h', title="Top 10 Danh mục")
            fig4.update_traces(hovertemplate="Danh mục: %{y}<br>Số đơn: %{customdata[0]}<br>Hoa hồng: %{x:,.0f} VNĐ".replace(',', '.'), 
                               customdata=cat_data[['Số_đơn']])
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("---")
        # 6. TOP 20 SUBID
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
            display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(lambda x: f"{int(round(x, 0)):,}".replace(',', '.') + " ₫")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.header("5. Chi Tiết Đơn Hàng")
        st.dataframe(df_filtered, use_container_width=True)
