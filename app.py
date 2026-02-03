import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import datetime

# Cấu hình trang
st.set_page_config(
    page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# CSS tùy chỉnh vùng upload
st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {display: none;}
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
    .stFileUploader section button {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Hàm định dạng tiền Việt Nam
def format_currency(value):
    return f"{int(round(value, 0)):,}".replace(',', '.') + " ₫"

# Hàm load và xử lý dữ liệu
@st.cache_data
def load_data(file):
    df = None
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        file.seek(0)
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            try:
                df = pd.read_csv(file, encoding='latin1')
            except Exception as read_err:
                st.error(f"Không đọc được file với các encoding phổ biến: {read_err}")
                return None
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        return None

    if df is None or df.empty:
        st.error("File CSV rỗng hoặc không có dữ liệu.")
        return None

    try:
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'])
        df['Thời gian Click'] = pd.to_datetime(df['Thời gian Click'], errors='coerce')
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date
        df['Giờ'] = df['Thời Gian Đặt Hàng'].dt.hour

        numeric_cols = [
            'Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)',
            'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)',
            'Giá(₫)', 'Số lượng'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '').str.replace('₫', ''),
                    errors='coerce'
                ).fillna(0)

        # Phân loại nguồn đơn
        def classify_source(row):
            k = str(row.get('Kênh', '')).strip()
            if k in ['Facebook', 'Instagram', 'Zalo']:
                return 'Social'
            elif k in ['Others', 'Websites', 'EdgeBrowser']:
                return 'Others'
            elif k == '':
                return 'Không xác định'
            else:
                return 'Others'

        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)

        # Phân loại nội dung (Video/Live)
        def classify_content_type(row):
            sp = str(row.get('Loại sản phẩm', '')).lower()
            hh = str(row.get('Loại Hoa hồng', '')).lower()
            if 'video' in sp or 'video' in hh:
                return 'Shopee Video'
            elif 'live' in sp or 'live' in hh or 'livestream' in sp:
                return 'Shopee Live'
            sub3 = str(row.get('Sub_id3', '')).lower()
            if 'video' in sub3:
                return 'Video (SubID)'
            elif 'live' in sub3:
                return 'Live (SubID)'
            else:
                return 'Normal'

        df['Loại nội dung'] = df.apply(classify_content_type, axis=1)

        return df

    except Exception as proc_err:
        st.error(f"Lỗi khi xử lý dữ liệu sau khi đọc file: {proc_err}")
        return None

# =============================================
# GIAO DIỆN CHÍNH
# =============================================

st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

col_upload, col_date = st.columns([1, 1])

with col_upload:
    st.markdown("### Tải lên file dữ liệu")
    uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed")

with col_date:
    st.markdown("### Chọn khoảng thời gian")
    if uploaded_file is not None:
        df_temp = load_data(uploaded_file)
        if df_temp is not None:
            min_date = df_temp['Ngày'].min()
            max_date = df_temp['Ngày'].max()
            today = datetime.date.today()

            time_options = {
                "Ngày cập nhật lần cuối": (max_date, max_date),
                "7 ngày qua": (today - datetime.timedelta(days=7), today),
                "15 ngày qua": (today - datetime.timedelta(days=15), today),
                "30 ngày qua": (today - datetime.timedelta(days=30), today),
                "Tháng này": (datetime.date(today.year, today.month, 1), today),
                "Tháng trước": (
                    datetime.date(today.year, today.month - 1 if today.month > 1 else today.year - 1, 12 if today.month == 1 else today.month - 1, 1),
                    datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)
                ),
                "Từ trước đến nay": (min_date, max_date)
            }

            selected = st.selectbox("Lựa chọn:", list(time_options.keys()), index=0, label_visibility="collapsed")
            date_range = time_options[selected]
            st.info(f"📅 {date_range[0]:%d/%m/%Y} – {date_range[1]:%d/%m/%Y}")
        else:
            date_range = None
    else:
        st.info("Vui lòng tải lên file CSV trước")
        date_range = None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        if date_range is not None:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # 1. Thống kê tổng quan
        st.header("1. Thống kê tổng quan")

        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df_filtered['ID đơn hàng'].nunique()
        hh_shopee = df_filtered['Hoa hồng Shopee trên sản phẩm(₫)'].sum()
        hh_xtra = df_filtered['Hoa hồng Xtra trên sản phẩm(₫)'].sum()
        rate = total_comm / total_gmv * 100 if total_gmv > 0 else 0
        qty = int(df_filtered['Số lượng'].sum())
        avg_comm = total_comm / total_orders if total_orders > 0 else 0

        comm_social = df_filtered.groupby(['ID đơn hàng', 'Phân loại nguồn'])['Tổng hoa hồng đơn hàng(₫)'].first()\
                      .reset_index().query("`Phân loại nguồn` == 'Social'")['Tổng hoa hồng đơn hàng(₫)'].sum()
        comm_others = total_comm - comm_social

        cols1 = st.columns(5)
        cols1[0].metric("💰 Tổng GMV", format_currency(total_gmv))
        cols1[1].metric("💵 Tổng Hoa Hồng", format_currency(total_comm))
        cols1[2].metric("📦 Tổng Đơn", f"{total_orders:,}".replace(",", "."))
        cols1[3].metric("💎 HH Shopee", format_currency(hh_shopee))
        cols1[4].metric("⭐ HH Xtra", format_currency(hh_xtra))

        cols2 = st.columns(5)
        cols2[0].metric("📊 Tỷ lệ HH", f"{rate:.2f}%")
        cols2[1].metric("🛒 Số lượng bán", f"{qty:,}".replace(",", "."))
        cols2[2].metric("📈 HH TB/Đơn", format_currency(avg_comm))
        cols2[3].metric("👥 HH Social", format_currency(comm_social))
        cols2[4].metric("📋 HH Others", format_currency(comm_others))

        st.markdown("---")

        # 5. Top 10 sản phẩm (tên là link)
        st.header("5. Top 10 sản phẩm nhiều đơn nhất")

        product_stats = df_filtered.groupby(['Tên Item', 'Shop id', 'Item id']).agg({
            'Giá trị đơn hàng (₫)': 'sum',
            'ID đơn hàng': 'count',
            'Tổng hoa hồng đơn hàng(₫)': 'sum'
        }).rename(columns={
            'Giá trị đơn hàng (₫)': 'GMV',
            'ID đơn hàng': 'Số_đơn',
            'Tổng hoa hồng đơn hàng(₫)': 'Hoa_hồng'
        }).reset_index()

        product_stats['Tỉ lệ HH (%)'] = (product_stats['Hoa_hồng'] / product_stats['GMV'] * 100).round(2)
        product_stats = product_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)

        if not product_stats.empty:
            product_stats['Link sản phẩm'] = product_stats.apply(
                lambda row: f"https://shopee.vn/product/{row['Shop id']}/{row['Item id']}", axis=1
            )

            display_df = product_stats[['Tên Item', 'GMV', 'Số_đơn', 'Hoa_hồng', 'Tỉ lệ HH (%)']].copy()
            display_df.rename(columns={'Tên Item': 'Tên sản phẩm'}, inplace=True)
            display_df['GMV'] = display_df['GMV'].apply(format_currency)
            display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(format_currency)
            display_df['Số_đơn'] = display_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tên sản phẩm": st.column_config.LinkColumn(
                        "Tên sản phẩm",
                        help="Nhấn để mở sản phẩm trên Shopee",
                        width="large"
                    ),
                    "GMV": st.column_config.TextColumn("Tổng GMV"),
                    "Số_đơn": st.column_config.TextColumn("Số đơn"),
                    "Hoa_hồng": st.column_config.TextColumn("Hoa hồng"),
                    "Tỉ lệ HH (%)": st.column_config.NumberColumn("Tỉ lệ HH (%)", format="%.2f")
                },
                height=520
            )
        else:
            st.info("Không có dữ liệu sản phẩm trong khoảng thời gian chọn.")

        st.markdown("---")

        # 6. Top 10 shop (tên shop là link)
        st.header("6. Top 10 shop có nhiều đơn nhất")

        shop_stats = df_filtered.groupby(['Tên Shop', 'Shop id']).agg({
            'Giá trị đơn hàng (₫)': 'sum',
            'ID đơn hàng': 'nunique',
            'Tổng hoa hồng đơn hàng(₫)': 'sum'
        }).rename(columns={
            'Giá trị đơn hàng (₫)': 'GMV',
            'ID đơn hàng': 'Số_đơn',
            'Tổng hoa hồng đơn hàng(₫)': 'Hoa_hồng'
        }).reset_index()

        shop_stats['Tỉ lệ HH (%)'] = (shop_stats['Hoa_hồng'] / shop_stats['GMV'] * 100).round(2)
        shop_stats = shop_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)

        if not shop_stats.empty:
            shop_stats['Link shop'] = shop_stats['Shop id'].apply(lambda x: f"https://shopee.vn/shop/{x}")

            display_shop = shop_stats[['Tên Shop', 'GMV', 'Số_đơn', 'Hoa_hồng', 'Tỉ lệ HH (%)']].copy()
            display_shop['GMV'] = display_shop['GMV'].apply(format_currency)
            display_shop['Hoa_hồng'] = display_shop['Hoa_hồng'].apply(format_currency)
            display_shop['Số_đơn'] = display_shop['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))

            st.dataframe(
                display_shop,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tên Shop": st.column_config.LinkColumn(
                        "Tên Shop",
                        help="Nhấn để mở shop trên Shopee",
                        width="large"
                    ),
                    "GMV": st.column_config.TextColumn("Tổng GMV"),
                    "Số_đơn": st.column_config.TextColumn("Số đơn"),
                    "Hoa_hồng": st.column_config.TextColumn("Hoa hồng"),
                    "Tỉ lệ HH (%)": st.column_config.NumberColumn("Tỉ lệ HH (%)", format="%.2f")
                },
                height=520
            )

            st.caption("🔗 Nhấn trực tiếp vào tên shop để xem trang Shopee")
        else:
            st.info("Không có dữ liệu shop trong khoảng thời gian chọn.")

        st.markdown("---")

        # Phần 7 - Chi tiết đơn hàng (bạn có thể paste phần cũ vào đây)
        st.header("7. Chi tiết đơn hàng")
        st.info("Phần chi tiết đơn hàng – bạn có thể copy từ file cũ vào đây")

        st.success("Dashboard đã chạy ổn – chúc Nam kiếm thật nhiều hoa hồng nhé! ❤️")

    else:
        st.error("Không thể tải dữ liệu từ file. Vui lòng kiểm tra định dạng CSV.")
