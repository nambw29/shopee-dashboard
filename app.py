import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from datetime import timedelta

# 1. Cấu hình trang
st.set_page_config(page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29", layout="wide", page_icon="🧧")

# Cài đặt locale tiếng Việt cho date picker
try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Vietnamese_Vietnam.1258')
    except:
        pass  # Sử dụng locale mặc định nếu không set được

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
    
    /* Style cho bảng dataframe */
    .stDataFrame {
        font-size: 14px;
    }
    .stDataFrame th {
        background-color: #f0f2f6;
        font-weight: bold;
        text-align: center !important;
        padding: 12px 8px !important;
    }
    .stDataFrame td {
        text-align: left !important;
        padding: 10px 8px !important;
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
        # Thử đọc với encoding utf-8-sig để xử lý BOM
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            # Nếu lỗi, thử encoding khác
            file.seek(0)  # Reset file pointer
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
        
        # Kiểm tra nếu DataFrame rỗng hoặc không có cột
        if df.empty or len(df.columns) == 0:
            st.error("File CSV không có dữ liệu hoặc không có cột. Vui lòng kiểm tra lại file.")
            return None
            
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Thời gian Click'] = pd.to_datetime(df['Thời gian Click'], errors='coerce')
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Ngày Click'] = df['Thời gian Click'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
        cols_to_numeric = ['Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)', 
                           'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)', 
                           'Giá(₫)', 'Số lượng']
        for col in cols_to_numeric:
            if col in df.columns:
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '').str.replace('₫', '').replace('nan', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # PHÂN LOẠI NGUỒN ĐƠN - GỘP FACEBOOK/INSTAGRAM THÀNH SOCIAL
        def classify_source(row):
            kenh = str(row.get('Kênh', '')).strip()
            
            # Gộp các mạng xã hội thành Social
            if kenh in ['Facebook', 'Instagram', 'Zalo']:
                return 'Social'
            elif kenh == 'Others':
                return 'Others'
            elif kenh in ['Websites', 'EdgeBrowser']:
                return 'Others'
            elif kenh == '':
                return 'Không xác định'
            else:
                return 'Others'
        
        # PHÂN LOẠI VIDEO/LIVE SHOPEE - DỰA VÀO LOẠI SẢN PHẨM/HH
        def classify_content_type(row):
            # Kiểm tra các cột có thể chứa thông tin Video/Live của Shopee
            loai_sp = str(row.get('Loại sản phẩm', '')).lower()
            loai_hh = str(row.get('Loại Hoa hồng', '')).lower()
            
            # Shopee Video/Live thường có đánh dấu riêng trong Loại sản phẩm
            if 'video' in loai_sp or 'video' in loai_hh:
                return 'Shopee Video'
            elif 'live' in loai_sp or 'live' in loai_hh or 'livestream' in loai_sp:
                return 'Shopee Live'
            else:
                # Nếu không có video/live của Shopee, phân loại theo SubID
                sub_id3 = str(row.get('Sub_id3', '')).lower().strip()
                if 'video' in sub_id3:
                    return 'Video (SubID)'
                elif 'live' in sub_id3:
                    return 'Live (SubID)'
                else:
                    return 'Normal'
            
        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)
        df['Loại nội dung'] = df.apply(classify_content_type, axis=1)
        
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

# BỐ TRÍ UPLOAD FILE VÀ CHỌN THỜI GIAN TRÊN 1 DÒNG (BỎ ICON)
col_upload, col_date = st.columns([1, 1])

with col_upload:
    st.markdown("### Tải lên file dữ liệu")
    uploaded_file = st.file_uploader("", type=['csv'], label_visibility="collapsed")

with col_date:
    st.markdown("### Chọn khoảng thời gian")
    if uploaded_file is not None:
        df_temp = load_data(uploaded_file)
        if df_temp is not None:
            date_range = st.date_input(
                "Thời gian:", 
                [df_temp['Ngày'].min(), df_temp['Ngày'].max()], 
                format="DD/MM/YYYY",
                label_visibility="collapsed"
            )
    else:
        st.info("Vui lòng tải lên file CSV")
        date_range = None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        
        # Lọc theo thời gian
        if date_range and len(date_range) == 2:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # MỤC 1: THỐNG KÊ TỔNG QUAN - SẮP XẾP LẠI
        st.header("1. Thống kê tổng quan")
        
        # TÍNH TOÁN
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df_filtered['ID đơn hàng'].nunique()
        hh_shopee = df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()
        hh_xtra = df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()
        commission_rate = (total_comm/total_gmv*100 if total_gmv > 0 else 0)
        total_quantity_sold = int(df_filtered['Số lượng'].sum())
        avg_commission_per_order = (total_comm/total_orders if total_orders > 0 else 0)
        
        # Tính hoa hồng theo kênh (Social vs Others)
        comm_by_channel = df_filtered.groupby(['ID đơn hàng', 'Phân loại nguồn'])['Tổng hoa hồng đơn hàng(₫)'].first().reset_index()
        comm_social = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Social']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_others = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Others']['Tổng hoa hồng đơn hàng(₫)'].sum()

        # HÀNG 1: 5 cột
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💰 Tổng doanh thu", format_currency(total_gmv))
        col2.metric("💵 Tổng hoa hồng", format_currency(total_comm))
        col3.metric("📦 Tổng đơn hàng", f"{total_orders:,}".replace(',', '.'))
        col4.metric("💎 Hoa hồng Shopee", format_currency(hh_shopee))
        col5.metric("⭐ Hoa hồng Xtra", format_currency(hh_xtra))
        
        # HÀNG 2: 5 cột
        col6, col7, col8, col9, col10 = st.columns(5)
        col6.metric("📊 Tỷ lệ hoa hồng", f"{commission_rate:.2f}%")
        col7.metric("🛒 Số lượng bán", f"{total_quantity_sold:,}".replace(',', '.'))
        col8.metric("📈 Hoa hồng TB/Đơn", format_currency(avg_commission_per_order))
        col9.metric("👥 Hoa hồng Social", format_currency(comm_social))
        col10.metric("📋 Hoa hồng Others", format_currency(comm_others))

        st.markdown("---")

        # MỤC 2: THỐNG KÊ ĐƠN HÀNG
        st.header("2. Thống kê đơn hàng")
        
        # Đếm đơn hàng unique theo kênh (Social vs Others)
        orders_by_channel = df_filtered.groupby('Phân loại nguồn')['ID đơn hàng'].nunique()
        orders_social = orders_by_channel.get('Social', 0)
        orders_others = orders_by_channel.get('Others', 0)
        
        # Đếm đơn theo loại nội dung (Shopee Video/Live)
        orders_by_content = df_filtered.groupby('Loại nội dung')['ID đơn hàng'].nunique()
        orders_video = orders_by_content.get('Shopee Video', 0)
        orders_live = orders_by_content.get('Shopee Live', 0)
        
        # Đơn 0 đồng và đơn hủy
        orders_zero = df_filtered[df_filtered['Giá trị đơn hàng (₫)'] == 0]['ID đơn hàng'].nunique()
        orders_cancelled = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)]['ID đơn hàng'].nunique()
        
        # 1 HÀNG 6 CỘT
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("👥 Đơn Social", f"{orders_social:,}".replace(',', '.'))
        c2.metric("📋 Đơn Others", f"{orders_others:,}".replace(',', '.'))
        c3.metric("🎬 Đơn Video", f"{orders_video:,}".replace(',', '.'))
        c4.metric("📹 Đơn Live", f"{orders_live:,}".replace(',', '.'))
        c5.metric("🆓 Đơn 0 Đồng", f"{orders_zero:,}".replace(',', '.'))
        c6.metric("❌ Đơn Hủy", f"{orders_cancelled:,}".replace(',', '.'))

        st.markdown("---")

        # MỤC 3: BIỂU ĐỒ THỐNG KÊ
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
            
            # Biểu đồ tròn - Tỷ trọng đơn hàng theo kênh - SỬA HIỂN THỊ HOVER
            channel_stats = df_filtered.groupby('Phân loại nguồn').agg(
                Số_đơn=('ID đơn hàng', 'nunique'),
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            ).reset_index()
            channel_stats.columns = ['Kênh', 'Số đơn', 'Hoa hồng']
            channel_stats['Tỷ trọng'] = (channel_stats['Số đơn'] / channel_stats['Số đơn'].sum() * 100).round(2)
            channel_stats['Hoa_hồng_formatted'] = channel_stats['Hoa hồng'].apply(format_currency)
            channel_stats['Số_đơn_formatted'] = channel_stats['Số đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            fig2 = px.pie(
                channel_stats, 
                names='Kênh', 
                values='Số đơn',
                title="Tỷ trọng đơn hàng theo kênh"
            )
            
            # Tạo hover text riêng cho từng kênh
            hover_texts = []
            for idx, row in channel_stats.iterrows():
                hover_text = f"<b>{row['Kênh']}</b><br>"
                hover_text += f"Số đơn: {row['Số_đơn_formatted']}<br>"
                hover_text += f"Tỷ trọng: {row['Tỷ trọng']:.2f}%<br>"
                hover_text += f"Hoa hồng: {row['Hoa_hồng_formatted']}"
                hover_texts.append(hover_text)
            
            fig2.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='%{customdata}<extra></extra>',
                customdata=hover_texts
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
            
            cat_data.columns = ['Danh mục sản phẩm', 'Số_đơn', 'Hoa hồng (₫)']
            cat_data['Số_đơn_formatted'] = cat_data['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            cat_data['Hoa_hồng_formatted'] = cat_data['Hoa hồng (₫)'].apply(format_currency)
            
            fig4 = px.bar(cat_data, x='Hoa hồng (₫)', y='Danh mục sản phẩm', orientation='h', title="Top 10 Danh mục")
            fig4.update_traces(
                hovertemplate="<b>Số đơn:</b> %{customdata[0]}<br><b>Hoa hồng:</b> %{customdata[1]}<extra></extra>",
                customdata=cat_data[['Số_đơn_formatted', 'Hoa_hồng_formatted']]
            )
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("---")
        
        # MỤC 4: TOP 20 SUBID
        st.header("4. Top 20 SubID hiệu quả nhất")
        
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        
        # Tạo cột SubID kết hợp từ tất cả 5 cột
        df_filtered_sub = df_filtered.copy()
        df_filtered_sub['SubID_Merged'] = df_filtered_sub[sub_id_cols].fillna('').apply(
            lambda row: '-'.join([str(x).strip() for x in row if str(x).strip() != '']), axis=1
        )
        
        # Lọc những dòng có SubID
        df_filtered_sub = df_filtered_sub[df_filtered_sub['SubID_Merged'] != '']
        
        if len(df_filtered_sub) > 0:
            # Nhóm theo SubID kết hợp và tính toán
            sub_stats = df_filtered_sub.groupby('SubID_Merged').agg(
                Số_đơn=('ID đơn hàng', 'count'),
                Doanh_thu=('Giá trị đơn hàng (₫)', 'sum'),
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            ).reset_index().sort_values('Số_đơn', ascending=False).head(20)
            
            # Tạo bảng hiển thị đẹp
            display_df = pd.DataFrame({
                'Xếp Hạng': range(1, len(sub_stats) + 1),
                'SubID': sub_stats['SubID_Merged'].values,
                'Số Đơn': sub_stats['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.')).values,
                'Doanh Thu': sub_stats['Doanh_thu'].apply(format_currency).values,
                'Tổng Hoa Hồng': sub_stats['Hoa_hồng'].apply(format_currency).values,
                'HH Trung Bình/Đơn': sub_stats.apply(lambda row: format_currency(row['Hoa_hồng']/row['Số_đơn'] if row['Số_đơn'] > 0 else 0), axis=1).values
            })
            
            # Hiển thị bảng với style đẹp
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Xếp Hạng": st.column_config.NumberColumn(
                        "Xếp Hạng",
                        help="Xếp hạng theo số đơn",
                        width="small",
                    ),
                    "SubID": st.column_config.TextColumn(
                        "SubID",
                        help="Dãy SubID kết hợp (Sub_id1-Sub_id2-Sub_id3-Sub_id4-Sub_id5)",
                        width="large",
                    ),
                    "Số Đơn": st.column_config.TextColumn(
                        "Số Đơn",
                        help="Tổng số đơn hàng",
                        width="small",
                    ),
                    "Doanh Thu": st.column_config.TextColumn(
                        "Doanh Thu",
                        help="Tổng doanh thu",
                        width="medium",
                    ),
                    "Tổng Hoa Hồng": st.column_config.TextColumn(
                        "Tổng Hoa Hồng",
                        help="Tổng hoa hồng kiếm được",
                        width="medium",
                    ),
                    "HH Trung Bình/Đơn": st.column_config.TextColumn(
                        "HH TB/Đơn",
                        help="Hoa hồng trung bình mỗi đơn",
                        width="medium",
                    ),
                },
                height=600
            )

        st.markdown("---")
        
        # MỤC 5: TOP 10 SẢN PHẨM NHIỀU ĐƠN NHẤT
        st.header("5. Top 10 sản phẩm nhiều đơn nhất")
        
        # Group by both Tên Item, Shop id và Item id để lấy link
        product_stats = df_filtered.groupby(['Tên Item', 'Shop id', 'Item id']).agg(
            GMV=('Giá trị đơn hàng (₫)', 'sum'),
            Số_đơn=('ID đơn hàng', 'count'),
            Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
        ).reset_index()
        
        product_stats['Tỉ lệ hoa hồng'] = (product_stats['Hoa_hồng'] / product_stats['GMV'] * 100).round(2)
        product_stats = product_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)
        
        top_products = pd.DataFrame({
            'STT': range(1, len(product_stats) + 1),
            'Tên sản phẩm': product_stats.apply(
                lambda row: f"[{str(row['Tên Item']).replace('[', '\\[').replace(']', '\\]')}]"
                f"(https://shopee.vn/product/{row['Shop id']}/{row['Item id']})",
                axis=1
            ),
            'Tổng GMV': product_stats['GMV'].apply(format_currency),
            'Số đơn': product_stats['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.')),
            'Hoa hồng': product_stats['Hoa_hồng'].apply(format_currency),
            'Tỉ lệ hoa hồng': product_stats['Tỉ lệ hoa hồng'].apply(lambda x: f"{x:.2f}%")
        })

        st.table(top_products.set_index('STT'))

        st.markdown("---")
        
        # MỤC 6: TOP 10 SHOP CÓ NHIỀU ĐƠN NHẤT
        st.header("6. Top 10 shop có nhiều đơn nhất")
        
        # Group by both Tên Shop và Shop id để lấy link
        shop_stats = df_filtered.groupby(['Tên Shop', 'Shop id']).agg(
            GMV=('Giá trị đơn hàng (₫)', 'sum'),
            Số_đơn=('ID đơn hàng', 'nunique'),
            Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
        ).reset_index()
        
        shop_stats['Tỉ lệ hoa hồng'] = (shop_stats['Hoa_hồng'] / shop_stats['GMV'] * 100).round(2)
        shop_stats = shop_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)
        
        top_shops = pd.DataFrame({
            'STT': range(1, len(shop_stats) + 1),
            'Tên shop': shop_stats.apply(
                lambda row: f"[{str(row['Tên Shop']).replace('[', '\\[').replace(']', '\\]')}]"
                f"(https://shopee.vn/shop/{row['Shop id']})",
                axis=1
            ),
            'Tổng GMV': shop_stats['GMV'].apply(format_currency),
            'Số đơn': shop_stats['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.')),
            'Hoa hồng': shop_stats['Hoa_hồng'].apply(format_currency),
            'Tỉ lệ hoa hồng': shop_stats['Tỉ lệ hoa hồng'].apply(lambda x: f"{x:.2f}%")
        })

        st.table(top_shops.set_index('STT'))

        st.markdown("---")
        
        # MỤC 7: CHI TIẾT ĐƠN HÀNG
        st.header("7. Chi tiết đơn hàng")
        
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
                st.info("Không có đơn hàng đã hủy!")
