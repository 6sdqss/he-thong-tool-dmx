import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import io
import zipfile
import json
import os
from PIL import Image
from urllib.parse import urljoin, urlparse
from requests.utils import cookiejar_from_dict

# ==========================================
# CẤU HÌNH HEADER & THÔNG SỐ CHUNG
# ==========================================
st.set_page_config(page_title="Hệ Thống Tool ĐỨC", page_icon="🚀", layout="wide")
USERS = {"ducadmin": "matkhau123", "nhanvien1": "123456"}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}
KEYWORD_FILE = "keywords.json"
WEB_OPTIONS = ["Thế Giới Di Động", "Điện Máy Xanh", "TopZone"]

# ==========================================
# KHU VỰC 1: HỆ THỐNG ĐỌC COOKIE TỰ ĐỘNG
# ==========================================
def get_session():
    """Hàm nạp Cookie từ 2 file JSON riêng biệt để vượt tường lửa"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    all_cookies = {}
    
    # 1. Đọc Cookie của DMX
    if os.path.exists("cookies_dmx.json"):
        try:
            with open("cookies_dmx.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e:
            st.error(f"Lỗi đọc cookies_dmx.json: {e}")
            
    # 2. Đọc Cookie của TGDD
    if os.path.exists("cookies_tgdd.json"):
        try:
            with open("cookies_tgdd.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e:
            st.error(f"Lỗi đọc cookies_tgdd.json: {e}")
            
    # Nạp toàn bộ cookie vào hệ thống
    session.cookies = cookiejar_from_dict(all_cookies)
    return session

# ==========================================
# KHU VỰC 2: CÁC HÀM XỬ LÝ (BÊ NGUYÊN SI TỪ CODE GỐC)
# ==========================================

# --- TOOL 1: Hàm Chèn Link ---
def load_keywords():
    if os.path.exists(KEYWORD_FILE):
        try:
            with open(KEYWORD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {w: data.get(w, {}) for w in WEB_OPTIONS}
        except: pass
    return {w: {} for w in WEB_OPTIONS}

def save_keywords(data):
    with open(KEYWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- TOOL 2: Lấy ID SP ---
def scrape_tgdd_product(url):
    try:
        html = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        name = soup.select_one("div.product-name h1")
        product_name = name.text.strip() if name else "Không tìm thấy"
        img = soup.select_one("img[src*='/Products/Images/']")
        if img:
            match = re.search(r"Images/\d+/(\d+)/", img.get("src", ""))
            product_id = match.group(1) if match else "Không tìm thấy"
        else: product_id = "Không tìm thấy"
        return product_name, product_id
    except Exception as e: return "Lỗi", str(e)

# --- TOOL 3: Check Trạng Thái ---
def fetch_product_info(session, product_id):
    url = f"https://www.dienmayxanh.com/sp-{product_id}"
    try:
        r = session.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code != 200: return product_id, "Lỗi truy cập", f"HTTP {r.status_code}"
        soup = BeautifulSoup(r.text, 'html.parser')
        html_text = r.text
        h1_tag = soup.find('h1')
        product_name = h1_tag.text.strip() if h1_tag else "Không tìm thấy tên SP"
        
        status_tag = soup.find('strong', class_='productstatus orange')
        if status_tag and "Hết hàng tạm thời" in status_tag.text: return product_id, product_name, "Hết hàng tạm thời"
        if soup.find('p', class_='box-price-present'): return product_id, product_name, "Đang kinh doanh"
        if soup.find(lambda tag: tag.name == 'strong' and '₫' in tag.text): return product_id, product_name, "Đang kinh doanh"
        if "Online Giá Rẻ Quá" in html_text or "online giá rẻ quá" in html_text.lower(): return product_id, product_name, "Đang kinh doanh"
        if re.search(r'\d{1,3}(?:\.\d{3})+₫', html_text): return product_id, product_name, "Đang kinh doanh"
        return product_id, product_name, "Không xác định / Ngừng KD"
    except Exception as e: return product_id, "Lỗi kết nối", str(e)

# --- TOOL 4 & 5: Lấy Thumb API ---
def extract_simage_thumb(simage_str):
    if not simage_str: return None
    try:
        images = json.loads(simage_str)
        if not isinstance(images, list): return None
        thumb_image = None
        for img in images:
            if isinstance(img, dict) and img.get("PictureUrl"):
                if img.get("IsThumb") is True: return img["PictureUrl"]
                if thumb_image is None: thumb_image = img["PictureUrl"]
        return thumb_image
    except:
        if simage_str.startswith(("http", "//", "/")): return simage_str
        return None

def clean_image_url(url):
    if not url: return url
    cleaned = re.sub(r'-\d+x\d+(?=\.(?:jpg|jpeg|png))', '', url)
    if cleaned.startswith("//"): return "https:" + cleaned
    elif cleaned.startswith("/"): return "https://cdnv2.tgdd.vn" + cleaned
    return cleaned

def fetch_by_page(session, product_id, domain):
    short_url = f"https://www.{domain}/sp-{product_id}"
    try:
        r = session.get(short_url, headers=HEADERS, allow_redirects=True, timeout=12)
        if r.status_code != 200: return None, None, f"HTTP {r.status_code}"
        html = r.text
        m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if m: return r.url, m.group(1), "OK(Page-og)"
        m2 = re.search(r'(https?://[^"\']+(?:cdnv2.tgdd.vn|cdn.tgdd.vn|cdnv2.tgdd|tgdd.vn)[^"\']+\.(?:png|jpg|jpeg))', html, re.I)
        if m2: return r.url, m2.group(1), "OK(Page-find)"
        return r.url, None, "NoImageFound"
    except Exception as e: return None, None, f"Error: {e}"

def fetch_by_api(session, product_id, domain):
    api_url = f"https://www.{domain}/apiweb/productdetails?productId={product_id}"
    try:
        r = session.get(api_url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None, None, f"API HTTP {r.status_code}"
        data = r.json()
        seo = data.get("SeoUrl") or data.get("SeoUrlRaw")
        pic = data.get("PictureUrl") or data.get("ImagePath")
        simage = data.get("SIMAGE") or data.get("simage")
        
        if not seo and isinstance(data, dict):
            for k in ("data", "product", "productDetails"):
                if k in data and isinstance(data[k], dict):
                    dd = data[k]
                    seo = seo or dd.get("SeoUrl")
                    pic = pic or dd.get("PictureUrl")
                    simage = simage or dd.get("SIMAGE")
                    if seo: break
                    
        thumb_from_simage = extract_simage_thumb(simage) if simage else None
        if thumb_from_simage: pic = thumb_from_simage
            
        if seo:
            final_url = f"https://www.{domain}" + seo if seo.startswith("/") else seo
            status = "OK(API-SIMAGE)" if simage and pic == thumb_from_simage else "OK(API)"
            return final_url, pic or "", status
        return None, pic or "", "API_no_seo"
    except Exception as e: return None, None, f"API_error: {e}"

# --- TOOL 8: Tải Hình Gallery ---
def clean_name(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    return re.sub(r"\s+", " ", cleaned).strip()

def refine_product_name(name: str) -> str:
    name = re.sub(r"(,?\s*(giá tốt|thu cũ.*|trợ giá.*|góp 0%.*))", "", name, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", name).strip()

def get_item_name(main_url):
    try:
        response = requests.get(main_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        name_tag = soup.find("h1")
        if name_tag: name = name_tag.text.strip()
        else: return "Sản phẩm"
        return clean_name(refine_product_name(name))
    except: return "Sản phẩm không tên"

def get_color_links_and_names(main_url):
    try:
        response = requests.get(main_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        parsed = urlparse(main_url)
        color_data = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if parsed.path in href and "?code=" in href:
                color_name = a.get_text(strip=True)
                color_link = urljoin(main_url, href)
                if color_name and color_link not in [c["link"] for c in color_data]:
                    color_data.append({"name": color_name, "link": color_link})
        return color_data if color_data else [{"name": "Mặc định", "link": main_url}]
    except: return [{"name": "Mặc định", "link": main_url}]

# ==========================================
# KHU VỰC 3: HỆ THỐNG ĐĂNG NHẬP & SIDEBAR
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #1A237E;'>🔐 ĐĂNG NHẬP HỆ THỐNG</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("🚀 Đăng nhập", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else: st.error("❌ Sai thông tin!")
    st.stop()

st.sidebar.markdown(f"### 👋 Chào **{st.session_state['user'].upper()}**!")
st.sidebar.markdown("---")
menu = st.sidebar.radio("📌 CHỌN CÔNG CỤ", [
    "🏠 0. Trang chủ", "🔗 1. Công Cụ Chèn Link (JSON)", "🔍 2. Lấy ID & Tên Sản Phẩm",
    "🏪 3. Check Trạng Thái KD", "📸 4. Lấy Thumb DMX", "📸 5. Lấy Thumb TGDD",
    "📊 6. Lọc File (Google Sheet)", "✂️ 7. Resize Ảnh", "🖼️ 8. Tải Hình Gallery"
])
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

# ==========================================
# KHU VỰC 4: GIAO DIỆN CHÍNH CÁC TOOL
# ==========================================

# --- TOOL 0 ---
if "0. Trang chủ" in menu:
    st.title("🌟 BẢNG ĐIỀU KHIỂN")
    st.success("Hệ thống Web đã kích hoạt Thành Công. Hỗ trợ tự động phân loại Cookie DMX/TGDD, API quét ảnh chuyên sâu và lưu file JSON tự động.")

# --- TOOL 1: CHÈN LINK (CÓ JSON) ---
elif "1. Công Cụ Chèn Link" in menu:
    st.title("🔗 Quản Lý Từ Khóa & Chèn Link")
    kw_data = load_keywords()
    tab1, tab2 = st.tabs(["✍️ Chèn Link", "⚙️ JSON Từ Khóa"])
    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1: site_sel = st.selectbox("Trang", WEB_OPTIONS)
        with c2: new_kw = st.text_input("Từ khóa mới")
        with c3: new_link = st.text_input("Link chèn mới")
        if st.button("➕ Thêm vào Database"):
            if new_kw and new_link:
                kw_data[site_sel][new_kw] = new_link
                save_keywords(kw_data)
                st.success("Đã lưu vào keywords.json!")
                st.rerun()
        st.json(kw_data[site_sel])
    with tab1:
        site_use = st.selectbox("Dùng data của:", WEB_OPTIONS)
        raw_text = st.text_area("Dán bài viết vào đây:", height=200)
        if st.button("🚀 Chèn Link", type="primary") and raw_text:
            result_text = raw_text
            for kw, link in kw_data[site_use].items():
                pattern = re.compile(rf'(?i)\b({re.escape(kw)})\b')
                result_text = pattern.sub(f'<a href="{link}" target="_blank">\\1</a>', result_text)
            st.code(result_text, language="html")
            st.markdown("### Xem trước giao diện bài viết:")
            st.markdown(result_text, unsafe_allow_html=True)

# --- TOOL 2: LẤY ID SP ---
elif "2. Lấy ID" in menu:
    st.title("🔍 Lấy ID & Tên SP TGDD/DMX")
    raw_input = st.text_area("Dán Link:", height=150)
    if st.button("🚀 Quét dữ liệu"):
        links = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results, bar = [], st.progress(0)
        for i, link in enumerate(links):
            name, pid = scrape_tgdd_product(link)
            results.append({"Tên SP": name, "ID": pid, "Link": link})
            bar.progress((i + 1) / len(links))
        st.dataframe(pd.DataFrame(results), use_container_width=True)

# --- TOOL 3: CHECK TRẠNG THÁI ---
elif "3. Check Trạng Thái" in menu:
    st.title("🏪 Check Trạng Thái Kinh Doanh")
    raw_input = st.text_area("Dán ID SP:", height=150)
    if st.button("🚀 Kiểm tra"):
        ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results, bar = [], st.progress(0)
        session = get_session() # Lấy Session có Cookie tổng hợp
        for i, pid in enumerate(ids):
            pid_num = re.search(r'(\d+)', pid).group(1) if re.search(r'(\d+)', pid) else pid
            _id, name, status = fetch_product_info(session, pid_num)
            results.append({"ID": _id, "Tên SP": name, "Trạng Thái": status})
            bar.progress((i + 1) / len(ids))
            time.sleep(0.3)
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Excel", df.to_csv(index=False).encode('utf-8-sig'), "TrangThai.csv", "text/csv")

# --- TOOL 4 & 5: LẤY THUMB (CÓ API VÀ SIMAGE) ---
elif "Lấy Thumb" in menu:
    domain = "dienmayxanh.com" if "DMX" in menu else "thegioididong.com"
    st.title(f"📸 Lấy Link Ảnh Thumb ({domain})")
    raw_input = st.text_area("Dán ID:", height=150)
    if st.button("🚀 Quét Ảnh", type="primary"):
        ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results, bar = [], st.progress(0)
        session = get_session() # Lấy Session có Cookie tổng hợp
        for i, pid in enumerate(ids):
            mnum = re.search(r'(\d+)(?!.*\d)', pid)
            pid_num = mnum.group(1) if mnum else pid
            
            final_url, thumb, status = None, None, "Start"
            # Cào Page gốc
            f_url, t_img, s = fetch_by_page(session, pid_num, domain)
            if s.startswith("OK(Page-og"):
                final_url, thumb, status = f_url, t_img, s
            else:
                # Cào API SIMAGE (Nguyên bản 100%)
                a_url, a_img, a_s = fetch_by_api(session, pid_num, domain)
                final_url = final_url or a_url or f_url
                thumb = a_img or t_img
                status = f"{s}+{a_s}"
                
            thumb_clean = clean_image_url(thumb) if thumb else ""
            if not final_url: final_url = f"https://www.{domain}/sp-{pid_num}"
            out_status = "OK" if thumb_clean else status or "NoThumb"
            
            results.append({"ID": pid_num, "Link SP": final_url, "Link Ảnh": thumb_clean, "Status": out_status})
            bar.progress((i + 1) / len(ids))
            time.sleep(0.2)
            
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Link Ảnh", df.to_csv(index=False).encode('utf-8-sig'), f"Thumb_{domain}.csv", "text/csv")

# --- TOOL 6: LỌC FILE SHEET ---
elif "6. Lọc File" in menu:
    st.title("📊 Lọc & Quản Lý File (Từ Google Sheet)")
    SHEET_ID = "1wtIhG3O1_oDrJcUvgwxcjxeRnrWpqbWIN15c4a37kl0"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
    try:
        df = pd.read_csv(CSV_URL)
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        creator_col = df.columns[28] if len(df.columns) > 28 else df.columns[-1]
        c1, c2 = st.columns(2)
        with c1: creator_filter = st.selectbox("Lọc theo người làm:", ["Tất cả"] + df[creator_col].dropna().astype(str).unique().tolist())
        with c2: search_kw = st.text_input("Tìm Tên SP:")
        if creator_filter != "Tất cả": df = df[df[creator_col].astype(str) == creator_filter]
        if search_kw: df = df[df.iloc[:, 3].astype(str).str.lower().str.contains(search_kw.lower())]
        st.dataframe(df, use_container_width=True)
    except Exception as e: st.error(f"Lỗi tải Sheet: {e}. Vui lòng mở quyền công khai Google Sheet.")

# --- TOOL 7: RESIZE ẢNH THEO LOGIC CŨ ---
elif "7. Resize Ảnh" in menu:
    st.title("✂️ Resize Ảnh Chuẩn (Bù Nền Trắng)")
    size_option = st.selectbox("Chọn kích thước:", ["1020x680", "1020x570", "1200x1200"])
    uploaded_files = st.file_uploader("Kéo thả ảnh", accept_multiple_files=True, type=['jpg', 'jpeg', 'png', 'webp'])
    if uploaded_files and st.button("🚀 Bắt đầu Resize"):
        w, h = map(int, size_option.split("x"))
        zip_buffer = io.BytesIO() # Dùng ZIP vì Web không ghi vào ổ cứng được
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                try:
                    img = Image.open(file)
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGBA")
                        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        bg.paste(img, (0, 0), img)
                        img = bg.convert("RGB")
                    else: img = img.convert("RGB")
                    
                    # Logic Scale LANCZOS nguyên bản của bạn
                    img_ratio, target_ratio = img.width / img.height, w / h
                    if img_ratio > target_ratio:
                        new_w, new_h = w, int(w / img_ratio)
                    else:
                        new_h, new_w = h, int(h * img_ratio)
                        
                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    new_img = Image.new("RGB", (w, h), (255, 255, 255))
                    new_img.paste(resized, ((w - new_w) // 2, (h - new_h) // 2))
                    
                    img_byte_arr = io.BytesIO()
                    new_img.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(file.name.rsplit('.', 1)[0] + ".jpg", img_byte_arr.getvalue())
                except: pass
                bar.progress((i + 1) / len(uploaded_files))
        st.success("✅ Đã xử lý xong!")
        st.download_button("📦 Tải File ZIP chứa Ảnh", zip_buffer.getvalue(), "Anh_Da_Resize.zip", "application/zip")

# --- TOOL 8: TẢI HÌNH GALLERY ---
elif "8. Tải Hình Gallery" in menu:
    st.title("🖼️ Tải Hình Gallery (Xóa đuôi -750x500)")
    url_input = st.text_area("Dán link SP:", height=100)
    if "glr_links" not in st.session_state: st.session_state.glr_links = []
    
    if st.button("🔍 Quét Các Màu"):
        links = [l.strip() for l in url_input.splitlines() if l.strip()]
        st.session_state.glr_links = []
        for link in links:
            item_name = get_item_name(link)
            colors = get_color_links_and_names(link)
            st.session_state.glr_links.append({"item_name": item_name, "colors": colors})
        st.rerun()

    if st.session_state.glr_links:
        selected_to_download = []
        for p in st.session_state.glr_links:
            st.markdown(f"**📦 {p['item_name']}**")
            for c in p['colors']:
                if st.checkbox(c['name'], value=True, key=c['link']):
                    selected_to_download.append({"item_name": p['item_name'], "color_name": c['name'], "link": c['link']})
                    
        if st.button("📥 Bắt đầu Tải & Đóng Gói", type="primary"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                bar = st.progress(0)
                session = get_session()
                for i, info in enumerate(selected_to_download):
                    try:
                        resp = session.get(info['link'], timeout=10)
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for img in soup.find_all("img"):
                            src = img.get("data-src") or img.get("src")
                            if src and "750x500" in src:
                                img_url = urljoin(info['link'], src)
                                clean_url = re.sub(r"-750x500", "", img_url) # Logic cắt đuôi gốc
                                file_name = f"{clean_name(info['item_name'])}/{clean_name(info['color_name'])}/{os.path.basename(clean_url.split('?')[0])}"
                                zip_file.writestr(file_name, requests.get(clean_url, headers=HEADERS).content)
                    except: pass
                    bar.progress((i + 1) / len(selected_to_download))
            st.success("✅ Đã gom xong ảnh vào File ZIP!")
            st.download_button("📦 Bấm Tải Xuống File ZIP", zip_buffer.getvalue(), "Gallery_Images.zip", "application/zip")
