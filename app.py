import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import io
import zipfile
from PIL import Image

# ==========================================
# CẤU HÌNH GIAO DIỆN & BẢO MẬT
# ==========================================
st.set_page_config(page_title="Hệ Thống Tool ĐỨC", page_icon="🚀", layout="wide")

# DANH SÁCH TÀI KHOẢN (Bạn có thể thêm bớt tùy ý)
USERS = {
    "ducadmin": "matkhau123",  # Tài khoản: ducadmin | Mật khẩu: matkhau123
    "nhanvien1": "123456"      # Tài khoản: nhanvien1 | Mật khẩu: 123456
}

# ==========================================
# HỆ THỐNG ĐĂNG NHẬP
# ==========================================
def login_system():
    st.markdown("<h1 style='text-align: center; color: #1A237E;'>🔐 ĐĂNG NHẬP HỆ THỐNG</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Vui lòng nhập tài khoản do Admin cấp để sử dụng Tool</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("🚀 Đăng nhập", use_container_width=True)
            
            if submitted:
                if username in USERS and USERS[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_system()
    st.stop() # Dừng lại ở đây nếu chưa đăng nhập

# ==========================================
# KHU VỰC ĐÃ ĐĂNG NHẬP - THANH ĐIỀU HƯỚNG
# ==========================================
st.sidebar.markdown(f"### 👋 Xin chào, **{st.session_state['user'].upper()}**!")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "📌 CHỌN CÔNG CỤ",
    ["🏠 Trang chủ", "🔍 1. Quét Tên & ID Sản Phẩm", "🏪 2. Check Trạng Thái DMX", "📸 3. Lấy Thumb DMX", "✂️ 4. Resize Ảnh Hàng Loạt"]
)
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# ==========================================
# TOOL 0: TRANG CHỦ
# ==========================================
if menu == "🏠 Trang chủ":
    st.title("🌟 BẢNG ĐIỀU KHIỂN TRUNG TÂM")
    st.info("Chào mừng bạn đến với hệ thống Tool phiên bản Web bảo mật. Hãy chọn công cụ ở thanh bên trái để bắt đầu làm việc.")
    
    st.markdown("""
    **Các ưu điểm của phiên bản Web:**
    * 🔒 Bảo mật bằng mật khẩu, không sợ người lạ dùng chùa.
    * ☁️ Hoạt động trên mọi thiết bị (Máy tính, Điện thoại, Máy tính bảng).
    * 🚫 Không cần cài đặt bất kỳ phần mềm nào vào máy.
    * ⚡ Tốc độ xử lý cao trên máy chủ đám mây.
    """)

# ==========================================
# TOOL 1: QUÉT TÊN & ID SẢN PHẨM
# ==========================================
elif menu == "🔍 1. Quét Tên & ID Sản Phẩm":
    st.title("🔍 Tool Quét Tên & ID Sản Phẩm TGDD")
    raw_input = st.text_area("Dán danh sách Link (Mỗi link 1 dòng):", height=200)
    
    if st.button("🚀 Bắt đầu quét", type="primary"):
        if not raw_input.strip():
            st.warning("Vui lòng nhập Link!")
        else:
            links = [l.strip() for l in raw_input.splitlines() if l.strip()]
            results = []
            bar = st.progress(0)
            
            for i, link in enumerate(links):
                try:
                    html = requests.get(link, headers=HEADERS, timeout=10).text
                    soup = BeautifulSoup(html, "html.parser")
                    name = soup.select_one("div.product-name h1")
                    p_name = name.text.strip() if name else "Không tìm thấy"
                    
                    img = soup.select_one("img[src*='/Products/Images/']")
                    p_id = "Không tìm thấy"
                    if img:
                        match = re.search(r"Images/\d+/(\d+)/", img.get("src", ""))
                        if match: p_id = match.group(1)
                    
                    results.append({"Tên Sản Phẩm": p_name, "ID": p_id, "Link": link})
                except Exception as e:
                    results.append({"Tên Sản Phẩm": "Lỗi", "ID": "Lỗi", "Link": link})
                
                bar.progress((i + 1) / len(links))
            
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Tải file Excel", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="ID_SP.csv", mime='text/csv')

# ==========================================
# TOOL 2: CHECK TRẠNG THÁI DMX
# ==========================================
elif menu == "🏪 2. Check Trạng Thái DMX":
    st.title("🏪 Tool Check Trạng Thái Kinh Doanh DMX")
    raw_input = st.text_area("Dán danh sách ID (Mỗi ID 1 dòng):", height=200)
    
    if st.button("🚀 Kiểm tra Trạng Thái", type="primary"):
        if not raw_input.strip():
            st.warning("Vui lòng nhập ID!")
        else:
            ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
            results = []
            bar = st.progress(0)
            session = requests.Session()
            
            for i, pid in enumerate(ids):
                pid_num = re.search(r'(\d+)', pid).group(1) if re.search(r'(\d+)', pid) else pid
                url = f"https://www.dienmayxanh.com/sp-{pid_num}"
                try:
                    r = session.get(url, headers=HEADERS, timeout=10)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    name_tag = soup.find('h1')
                    p_name = name_tag.text.strip() if name_tag else "Không tìm thấy"
                    
                    status = "Không xác định"
                    status_tag = soup.find('strong', class_='productstatus orange')
                    if status_tag and "Hết hàng tạm thời" in status_tag.text:
                        status = "Hết hàng tạm thời"
                    elif soup.find('p', class_='box-price-present') or soup.find(lambda tag: tag.name == 'strong' and '₫' in tag.text):
                        status = "Đang kinh doanh"
                    
                    results.append({"ID": pid_num, "Tên Sản Phẩm": p_name, "Trạng Thái": status})
                except:
                    results.append({"ID": pid_num, "Tên Sản Phẩm": "Lỗi", "Trạng Thái": "Lỗi kết nối"})
                
                bar.progress((i + 1) / len(ids))
                time.sleep(0.2)
            
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Tải kết quả", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="Trang_Thai_DMX.csv", mime='text/csv')

# ==========================================
# TOOL 3: LẤY THUMB DMX
# ==========================================
elif menu == "📸 3. Lấy Thumb DMX":
    st.title("📸 Tool Quét Link Ảnh Thumbnail DMX")
    raw_input = st.text_area("Dán danh sách ID (Mỗi ID 1 dòng):", height=200)
    
    if st.button("🚀 Bắt đầu quét ảnh", type="primary"):
        if not raw_input.strip():
            st.warning("Vui lòng nhập ID!")
        else:
            ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
            results = []
            bar = st.progress(0)
            
            for i, pid in enumerate(ids):
                url = f"https://www.dienmayxanh.com/sp-{pid}"
                try:
                    r = requests.get(url, headers=HEADERS, timeout=10)
                    m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', r.text, re.I)
                    img_link = m.group(1) if m else "Không tìm thấy"
                    results.append({"ID": pid, "Link SP": url, "Link Ảnh": img_link})
                except:
                    results.append({"ID": pid, "Link SP": url, "Link Ảnh": "Lỗi"})
                bar.progress((i + 1) / len(ids))
                time.sleep(0.2)
            
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Tải Link Ảnh", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="Thumb_DMX.csv", mime='text/csv')

# ==========================================
# TOOL 4: RESIZE ẢNH HÀNG LOẠT (BẢN WEB)
# ==========================================
elif menu == "✂️ 4. Resize Ảnh Hàng Loạt":
    st.title("✂️ Cắt / Resize Ảnh Hàng Loạt Chuẩn Kích Thước")
    st.info("Vì là bản Web bảo mật, hệ thống không thể tự chui vào ổ đĩa (ổ C, D) máy tính của bạn. Vui lòng tải các ảnh cần Resize lên đây, web sẽ xử lý và đóng gói thành 1 file ZIP để bạn tải về máy nhanh chóng.")
    
    col1, col2 = st.columns(2)
    with col1:
        size_option = st.selectbox("Chọn kích thước mong muốn:", ["1020x680", "1020x570", "1200x1200"])
    
    uploaded_files = st.file_uploader("Kéo thả nhiều ảnh vào đây (JPG, PNG, WEBP)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png', 'webp'])
    
    if uploaded_files and st.button("🚀 Bắt đầu Resize", type="primary"):
        w, h = map(int, size_option.split("x"))
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                try:
                    img = Image.open(file)
                    if img.mode in ("RGBA", "LA", "P"):
                        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        bg.paste(img, (0, 0), img)
                        img = bg.convert("RGB")
                    else:
                        img = img.convert("RGB")

                    img_ratio = img.width / img.height
                    target_ratio = w / h

                    if img_ratio > target_ratio:
                        new_w = w
                        new_h = int(w / img_ratio)
                    else:
                        new_h = h
                        new_w = int(h * img_ratio)

                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    new_img = Image.new("RGB", (w, h), (255, 255, 255))
                    offset_x = (w - new_w) // 2
                    offset_y = (h - new_h) // 2
                    new_img.paste(resized, (offset_x, offset_y))

                    # Lưu ảnh vào RAM thay vì lưu ra ổ cứng
                    img_byte_arr = io.BytesIO()
                    new_img.save(img_byte_arr, format='JPEG', quality=95)
                    
                    # Đưa vào file ZIP
                    safe_name = file.name.rsplit('.', 1)[0] + ".jpg"
                    zip_file.writestr(safe_name, img_byte_arr.getvalue())
                except Exception as e:
                    st.error(f"Lỗi xử lý file {file.name}: {e}")
                
                bar.progress((i + 1) / len(uploaded_files))
                
        st.success("✅ Xử lý hoàn tất!")
        st.download_button(
            label="📦 Tải toàn bộ ảnh đã Resize (File ZIP)",
            data=zip_buffer.getvalue(),
            file_name="Anh_Da_Resize.zip",
            mime="application/zip",
            type="primary"
        )