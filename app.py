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

# CSS tùy chỉnh
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

# Hàm format tiền
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
            except Exception as e:
                st.error(f"Không thể đọc file với các encoding phổ biến: {e}")
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

        # Phân loại nguồn
        def classify_source(row):
            kenh = str(row.get('Kênh', '')).strip()
            if kenh in ['Facebook', 'Instagram', 'Zalo']:
                return 'Social'
            return 'Others'

        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)

        # Phân loại nội dung (đơn giản hóa một chút)
        def classify_content(row):
            loai = str(row.get('Loại sản phẩm', '')).lower()
            if 'video' in loai:
                return 'Shopee Video'
            if 'live' in loai or 'livestream' in loai:
                return 'Shopee Live'
            return 'Normal'

        df['Loại nội dung'] = df.apply(classify_content, axis=1)

        return df

    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu: {e}")
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
                "30 ngày qua": (today - datetime.timedelta(days=30), today),
                "Tháng này": (datetime.date(today.year, today.month, 1), today),
                "Từ trước đến nay": (min_date, max_date)
            }

            selected = st.selectbox("Chọn khoảng", list(time_options.keys()), index=0, label_visibility="collapsed")
            date_range = time_options[selected]
            st.info(f"📅 {date_range[0]:%d/%m/%Y} — {date_range[1]:%d/%m/%Y}")
        else:
            date_range = None
    else:
        st.info("Vui lòng tải file CSV lên trước")
        date_range = None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        if date_range:
            df = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]

        st.markdown("---")
        st.header("Tổng quan nhanh")

        total_gmv = df['Giá trị đơn hàng (₫)'].sum()
        total_comm = df['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df['ID đơn hàng'].nunique()

        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng GMV", format_currency(total_gmv))
        col2.metric("Tổng Hoa hồng", format_currency(total_comm))
        col3.metric("Tổng đơn hàng", f"{total_orders:,}".replace(",", "."))

        st.markdown("---")
        st.info("→ Phần còn lại của dashboard (biểu đồ, top sản phẩm, top shop, chi tiết đơn) bạn có thể thêm tiếp từ code cũ. Nếu cần mình viết tiếp phần nào cụ thể thì báo nhé!")

else:
    st.warning("Chưa có file dữ liệu. Vui lòng upload file CSV từ Shopee Affiliate.")
