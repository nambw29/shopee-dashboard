import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import datetime

# 1. Cấu hình trang
st.set_page_config(
    page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# Cài đặt locale tiếng Việt cho date picker
try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Vietnamese_Vietnam.1258')
    except:
        pass

# --- CSS tùy chỉnh ---
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
    return f"{int(round(value, 0)):,}".replace(',', '.') + " ₫"

# --- HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_data(file):
    try:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            file.seek(0)
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
        
        if df.empty or len(df.columns) == 0:
            st.error("File CSV không có dữ liệu hoặc không có cột.")
            return None
            
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Thời gian Click'] = pd.to_datetime(df['Thời gian Click'], errors='coerce')
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Ngày Click'] = df['Thời gian Click'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour
        
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

        def classify_source(row):
            kenh = str(row.get('Kênh', '')).strip()
            if kenh in ['Facebook', 'Instagram', 'Zalo']:
                return 'Social'
            elif kenh in ['Others', 'Websites', 'EdgeBrowser']:
                return 'Others'
            elif kenh == '':
                return 'Không xác định'
            else:
                return 'Others'
        
        def classify_content_type(row):
            loai_sp = str(row.get('Loại sản phẩm', '')).lower()
            loai_hh = str(row.get('Loại Hoa hồng', '')).lower()
            if 'video' in loai_sp or 'video' in loai_hh:
                return 'Shopee Video'
            elif 'live' in loai_sp or 'live' in loai_hh or 'livestream' in loai_sp:
                return 'Shopee Live'
            else:
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
        st.error(f"Lỗi khi đọc file: {e}")
        return None

# === GIAO DIỆN CHÍNH ===
st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

col_upload, col_date = st.columns([1, 1])

with col_upload:
    st.markdown("### Tải lên file dữ liệu")
    uploaded_file = st.file_uploader("", type=['csv'], label_visibility="collapsed")

with col_date:
    st.markdown("### Chọn khoảng thời gian")
    if uploaded_file is not None:
        df_temp = load_data(uploaded_file)
        if df_temp is not None:
            min_date = df_temp['Ngày'].min()
            max_date = df_temp['Ngày'].max()
            today = datetime.date.today()

            time_range_options = {
                "Ngày cập nhật lần cuối": (max_date, max_date),
                "7 ngày qua": (today - datetime.timedelta(days=7), today),
                "15 ngày qua": (today - datetime.timedelta(days=15), today),
                "30 ngày qua": (today - datetime.timedelta(days=30), today),
                "Tháng này": (datetime.date(today.year, today.month, 1), today),
                "Tháng trước": (
                    datetime.date(today.year, today.month - 1 if today.month > 1 else 12, 1) 
                    if today.month > 1 else datetime.date(today.year - 1, 12, 1),
                    (datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1))
                ),
                "Từ trước đến nay": (min_date, max_date)
            }
            
            selected_range = st.selectbox(
                "Lựa chọn:",
                options=list(time_range_options.keys()),
                index=0,
                label_visibility="collapsed"
            )
            
            date_range = time_range_options[selected_range]
            st.info(f"📅 {date_range[0].strftime('%d/%m/%Y')} - {date_range[1].strftime('%d/%m/%Y')}")
    else:
        st.info("Vui lòng tải lên file CSV")
        date_range = None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        
        if date_range:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # 1. THỐNG KÊ TỔNG QUAN
        st.header("1. Thống kê tổng quan")
        
        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df_filtered['ID đơn hàng'].nunique()
        hh_shopee = df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()
        hh_xtra = df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()
        commission_rate = (total_comm / total_gmv * 100 if total_gmv > 0 else 0)
        total_quantity_sold = int(df_filtered['Số lượng'].sum())
        avg_commission_per_order = (total_comm / total_orders if total_orders > 0 else 0)
        
        comm_by_channel = df_filtered.groupby(['ID đơn hàng', 'Phân loại nguồn'])['Tổng hoa hồng đơn hàng(₫)'].first().reset_index()
        comm_social = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Social']['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_others = comm_by_channel[comm_by_channel['Phân loại nguồn'] == 'Others']['Tổng hoa hồng đơn hàng(₫)'].sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💰 Tổng Doanh Thu", format_currency(total_gmv))
        col2.metric("💵 Tổng Hoa Hồng", format_currency(total_comm))
        col3.metric("📦 Tổng Đơn Hàng", f"{total_orders:,}".replace(',', '.'))
        col4.metric("💎 Hoa Hồng Shopee", format_currency(hh_shopee))
        col5.metric("⭐ Hoa Hồng Xtra", format_currency(hh_xtra))
        
        col6, col7, col8, col9, col10 = st.columns(5)
        col6.metric("📊 Tỷ Lệ Hoa Hồng", f"{commission_rate:.2f}%")
        col7.metric("🛒 Số Lượng Đã Bán", f"{total_quantity_sold:,}".replace(',', '.'))
        col8.metric("📈 Hoa Hồng TB/Đơn", format_currency(avg_commission_per_order))
        col9.metric("👥 Hoa Hồng Social", format_currency(comm_social))
        col10.metric("📋 Hoa Hồng Others", format_currency(comm_others))

        st.markdown("---")

        # 2. THỐNG KÊ ĐƠN HÀNG
        st.header("2. Thống kê đơn hàng")
        
        orders_by_channel = df_filtered.groupby('Phân loại nguồn')['ID đơn hàng'].nunique()
        orders_social = orders_by_channel.get('Social', 0)
        orders_others = orders_by_channel.get('Others', 0)
        
        orders_by_content = df_filtered.groupby('Loại nội dung')['ID đơn hàng'].nunique()
        orders_video = orders_by_content.get('Shopee Video', 0)
        orders_live = orders_by_content.get('Shopee Live', 0)
        
        orders_zero = df_filtered[df_filtered['Giá trị đơn hàng (₫)'] == 0]['ID đơn hàng'].nunique()
        orders_cancelled = df_filtered[df_filtered['Trạng thái đặt hàng'].str.contains('Hủy', case=False, na=False)]['ID đơn hàng'].nunique()
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("👥 Đơn Social", f"{orders_social:,}".replace(',', '.'))
        c2.metric("📋 Đơn Others", f"{orders_others:,}".replace(',', '.'))
        c3.metric("🎬 Đơn Video", f"{orders_video:,}".replace(',', '.'))
        c4.metric("📹 Đơn Live", f"{orders_live:,}".replace(',', '.'))
        c5.metric("🆓 Đơn 0 Đồng", f"{orders_zero:,}".replace(',', '.'))
        c6.metric("❌ Đơn Hủy", f"{orders_cancelled:,}".replace(',', '.'))

        st.markdown("---")

        # 3. BIỂU ĐỒ
        st.header("3. Biểu đồ thống kê")
        col_a, col_b = st.columns(2)
        
        with col_a:
            daily_comm = df_filtered.groupby('Ngày')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            daily_comm['Ngày_str'] = daily_comm['Ngày'].apply(lambda x: x.strftime('%d/%m/%Y'))
            daily_comm['Hoa_hồng_formatted'] = daily_comm['Tổng hoa hồng đơn hàng(₫)'].apply(format_currency)
            
            fig1 = px.line(daily_comm, x='Ngày', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo ngày")
            fig1.update_traces(
                hovertemplate="<b>Ngày:</b> %{customdata[0]}<br><b>Hoa hồng:</b> %{customdata[1]}<extra></extra>",
                customdata=daily_comm[['Ngày_str', 'Hoa_hồng_formatted']]
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            channel_stats = df_filtered.groupby('Phân loại nguồn').agg(
                Số_đơn=('ID đơn hàng', 'nunique'),
                Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
            ).reset_index()
            channel_stats.columns = ['Kênh', 'Số đơn', 'Hoa hồng']
            channel_stats['Tỷ trọng'] = (channel_stats['Số đơn'] / channel_stats['Số đơn'].sum() * 100).round(2)
            channel_stats['Hoa_hồng_formatted'] = channel_stats['Hoa hồng'].apply(format_currency)
            channel_stats['Số_đơn_formatted'] = channel_stats['Số đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            fig2 = px.pie(channel_stats, names='Kênh', values='Số đơn', title="Tỷ trọng đơn hàng theo kênh")
            hover_texts = [f"<b>{row['Kênh']}</b><br>Số đơn: {row['Số_đơn_formatted']}<br>Tỷ trọng: {row['Tỷ trọng']:.2f}%<br>Hoa hồng: {row['Hoa_hồng_formatted']}" 
                           for _, row in channel_stats.iterrows()]
            
            fig2.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='%{customdata}<extra></extra>',
                customdata=hover_texts
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            hourly_comm = df_filtered.groupby('Giờ')['Tổng hoa hồng đơn hàng(₫)'].sum().reset_index()
            hourly_comm['Hoa_hồng_formatted'] = hourly_comm['Tổng hoa hồng đơn hàng(₫)'].apply(format_currency)
            
            fig3 = px.bar(hourly_comm, x='Giờ', y='Tổng hoa hồng đơn hàng(₫)', title="Hoa hồng theo khung giờ")
            fig3.update_traces(
                hovertemplate="<b>Giờ:</b> %{x}h<br><b>Hoa hồng:</b> %{customdata}<extra></extra>",
                customdata=hourly_comm['Hoa_hồng_formatted']
            )
            st.plotly_chart(fig3, use_container_width=True)
            
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
        
        # 4. TOP 20 SUBID
        st.header("4. Top 20 SubID hiệu quả nhất")
        
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        sub_list = []
        for col in sub_id_cols:
            if col in df_filtered.columns:
                temp = df_filtered[df_filtered[col].notna() & (df_filtered[col] != '')][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp.columns = ['SubID', 'HoaHồng']
                sub_list.append(temp)
        
        if sub_list:
            all_subs = pd.concat(sub_list).groupby('SubID').agg(
                Số_đơn=('SubID', 'count'), 
                Hoa_hồng=('HoaHồng', 'sum')
            ).reset_index().sort_values('Số_đơn', ascending=False).head(20)
            
            display_df = pd.DataFrame({
                'Xếp Hạng': range(1, len(all_subs) + 1),
                'SubID': all_subs['SubID'],
                'Số Đơn': all_subs['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.')),
                'Tổng Hoa Hồng': all_subs['Hoa_hồng'].apply(format_currency),
                'HH Trung Bình/Đơn': all_subs.apply(
                    lambda row: format_currency(row['Hoa_hồng'] / row['Số_đơn'] if row['Số_đơn'] > 0 else 0), axis=1
                )
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Xếp Hạng": st.column_config.NumberColumn("Xếp Hạng", width="small"),
                    "SubID": st.column_config.TextColumn("SubID", width="medium"),
                    "Số Đơn": st.column_config.TextColumn("Số Đơn", width="small"),
                    "Tổng Hoa Hồng": st.column_config.TextColumn("Tổng Hoa Hồng", width="medium"),
                    "HH Trung Bình/Đơn": st.column_config.TextColumn("HH TB/Đơn", width="medium"),
                },
                height=600
            )

        st.markdown("---")
        
        # 5. TOP 10 SẢN PHẨM NHIỀU ĐƠN NHẤT - LINK TRỰC TIẾP VÀO TÊN SẢN PHẨM
        st.header("5. Top 10 sản phẩm nhiều đơn nhất")
        
        product_stats = df_filtered.groupby(['Tên Item', 'Shop id', 'Item id']).agg(
            GMV=('Giá trị đơn hàng (₫)', 'sum'),
            Số_đơn=('ID đơn hàng', 'count'),
            Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
        ).reset_index()
        
        product_stats['Tỉ lệ hoa hồng'] = (product_stats['Hoa_hồng'] / product_stats['GMV'] * 100).round(2)
        product_stats = product_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)
        
        if not product_stats.empty:
            # Tạo cột link sản phẩm
            product_stats['Link sản phẩm'] = product_stats.apply(
                lambda row: f"https://shopee.vn/product/{row['Shop id']}/{row['Item id']}", axis=1
            )
            
            # Chuẩn bị dataframe hiển thị
            display_cols = {
                'Tên Item': 'Tên sản phẩm',
                'Link sản phẩm': 'Link sản phẩm (ẩn)',
                'GMV': 'Tổng GMV',
                'Số_đơn': 'Số đơn',
                'Hoa_hồng': 'Hoa hồng',
                'Tỉ lệ hoa hồng': 'Tỉ lệ HH (%)'
            }
            
            display_df = product_stats.rename(columns=display_cols)[['Tên sản phẩm', 'Tổng GMV', 'Số đơn', 'Hoa hồng', 'Tỉ lệ HH (%)']]
            
            display_df['Tổng GMV'] = display_df['Tổng GMV'].apply(format_currency)
            display_df['Hoa hồng'] = display_df['Hoa hồng'].apply(format_currency)
            display_df['Số đơn'] = display_df['Số đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tên sản phẩm": st.column_config.LinkColumn(
                        "Tên sản phẩm",
                        display_text="Tên sản phẩm",
                        help="Nhấn vào tên để mở trang sản phẩm trên Shopee",
                        width="large"
                    ),
                    "Tổng GMV": st.column_config.TextColumn("Tổng GMV", width="small"),
                    "Số đơn": st.column_config.TextColumn("Số đơn", width="small"),
                    "Hoa hồng": st.column_config.TextColumn("Hoa hồng", width="small"),
                    "Tỉ lệ HH (%)": st.column_config.NumberColumn("Tỉ lệ HH (%)", format="%.2f", width="small"),
                },
                height=500
            )
        else:
            st.info("Không có dữ liệu sản phẩm trong khoảng thời gian đã chọn.")

        st.markdown("---")
        
        # 6. TOP 10 SHOP CÓ NHIỀU ĐƠN NHẤT
        st.header("6. Top 10 shop có nhiều đơn nhất")
        
        shop_stats = df_filtered.groupby(['Tên Shop', 'Shop id']).agg(
            GMV=('Giá trị đơn hàng (₫)', 'sum'),
            Số_đơn=('ID đơn hàng', 'nunique'),
            Hoa_hồng=('Tổng hoa hồng đơn hàng(₫)', 'sum')
        ).reset_index()
        
        shop_stats['Tỉ lệ hoa hồng'] = (shop_stats['Hoa_hồng'] / shop_stats['GMV'] * 100).round(2)
        shop_stats = shop_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)
        
        if not shop_stats.empty:
            shop_stats['Link shop'] = shop_stats['Shop id'].apply(lambda x: f"https://shopee.vn/shop/{x}")
            
            display_cols_shop = {
                'Tên Shop': 'Tên shop',
                'Link shop': 'Link',
                'GMV': 'Tổng GMV',
                'Số_đơn': 'Số đơn',
                'Hoa_hồng': 'Hoa hồng',
                'Tỉ lệ hoa hồng': 'Tỉ lệ HH (%)'
            }
            
            display_df_shop = shop_stats.rename(columns=display_cols_shop)[list(display_cols_shop.values())]
            
            display_df_shop['Tổng GMV'] = display_df_shop['Tổng GMV'].apply(format_currency)
            display_df_shop['Hoa hồng'] = display_df_shop['Hoa hồng'].apply(format_currency)
            display_df_shop['Số đơn'] = display_df_shop['Số đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))
            
            st.dataframe(
                display_df_shop,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tên shop": st.column_config.TextColumn("Tên shop", width="large"),
                    "Link": st.column_config.LinkColumn(
                        "Link",
                        display_text="Mở shop",
                        help="Nhấn để xem trang shop trên Shopee",
                        width="medium"
                    ),
                    "Tổng GMV": st.column_config.TextColumn("Tổng GMV", width="small"),
                    "Số đơn": st.column_config.TextColumn("Số đơn", width="small"),
                    "Hoa hồng": st.column_config.TextColumn("Hoa hồng", width="small"),
                    "Tỉ lệ HH (%)": st.column_config.NumberColumn("Tỉ lệ HH (%)", format="%.2f", width="small"),
                },
                height=500
            )
        else:
            st.info("Không có dữ liệu shop trong khoảng thời gian đã chọn.")

        st.markdown("---")
        
        # 7. CHI TIẾT ĐƠN HÀNG
        st.header("7. Chi tiết đơn hàng")
        
        detail_cols = [
            'ID đơn hàng', 'Tên Shop', 'Tên Item', 'Giá(₫)', 'Số lượng', 
            'Tổng hoa hồng đơn hàng(₫)', 'Trạng thái đặt hàng', 'Kênh', 
            'Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5'
        ]
        
        df_detail = df_filtered[detail_cols].copy()
        
        df_detail['Giá(₫)'] = df_detail['Giá(₫)'].apply(format_currency)
        df_detail['Tổng hoa hồng đơn hàng(₫)'] = df_detail['Tổng hoa hồng đơn hàng(₫)'].apply(format_currency)
        df_detail['Số lượng'] = df_detail['Số lượng'].astype(int)
        
        df_detail.columns = [
            'ID Đơn Hàng', 'Tên Shop', 'Tên Sản Phẩm', 'Giá', 'Số Lượng', 
            'Tổng Hoa Hồng', 'Trạng Thái', 'Kênh', 
            'SubID 1', 'SubID 2', 'SubID 3', 'SubID 4', 'SubID 5'
        ]
        
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
            if not df_pending.empty:
                st.dataframe(df_pending, use_container_width=True, hide_index=True, height=500)
            else:
                st.info("Không có đơn hàng đang chờ xử lý")
        
        with tab3:
            df_cancelled = df_detail[df_detail['Trạng Thái'].str.contains('Hủy', case=False, na=False)]
            st.markdown(f"**Tổng số dòng:** {len(df_cancelled):,}".replace(',', '.'))
            if not df_cancelled.empty:
                st.dataframe(df_cancelled, use_container_width=True, hide_index=True, height=500)
            else:
                st.info("Không có đơn hàng đã hủy")
