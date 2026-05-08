# Hệ Thống Trắc Nghiệm Tự Do (Streamlit)

Hệ thống cho phép người dùng làm bài kiểm tra trắc nghiệm dựa trên dữ liệu từ file CSV.

## Cấu trúc file CSV đầu vào
File đề thi phải có đuôi `.csv` và bắt buộc chứa 6 cột với tiêu đề (Header) chính xác như sau:
`"Câu hỏi","Đáp án A","Đáp án B","Đáp án C","Đáp án D","Đáp án đúng"`

## Cài đặt và Chạy cục bộ (Local)
1. Tạo môi trường ảo: `python -m venv venv`
2. Kích hoạt môi trường:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
3. Cài đặt thư viện: `pip install -r requirements.txt`
4. Tạo mật khẩu admin bằng cách tạo file `.streamlit/secrets.toml` chứa `admin_password = "mat_khau_cua_ban"`
5. Chạy ứng dụng: `streamlit run app.py`