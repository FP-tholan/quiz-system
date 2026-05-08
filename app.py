import streamlit as st
import pandas as pd
import os

# Cấu trúc gốc
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def admin_section():
    st.header("Quản lý Đề thi (Admin)")
    pwd = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    # Kiểm tra mật khẩu (thêm .get() để tránh lỗi nếu quên tạo file secrets.toml)
    if pwd == st.secrets.get("admin_password", "123"):
        # Dùng st.tabs để chia giao diện thành 2 phần: Upload và Xóa
        tab_upload, tab_delete = st.tabs(["Tải lên đề mới", "Xóa đề thi"])
        
        # --- TAB TẢI LÊN ---
        with tab_upload:
            st.subheader("Tải lên đề thi")
            existing_subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
            subject = st.text_input("Nhập tên môn học (hoặc tạo môn mới):").strip()
            
            if subject:
                subject_dir = os.path.join(DATA_DIR, subject)
                if not os.path.exists(subject_dir):
                    os.makedirs(subject_dir)
                    
                uploaded_file = st.file_uploader("Chọn file CSV", type=["csv"], key="upload_csv")
                if uploaded_file is not None:
                    file_path = os.path.join(subject_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"Đã lưu thành công đề '{uploaded_file.name}' vào môn '{subject}'")

        # --- TAB XÓA ---
        with tab_delete:
            st.subheader("Xóa đề thi")
            subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
            if not subjects:
                st.info("Chưa có môn học nào.")
            else:
                del_subject = st.selectbox("Chọn môn:", subjects, key="del_sub")
                if del_subject:
                    sub_dir = os.path.join(DATA_DIR, del_subject)
                    files = [f for f in os.listdir(sub_dir) if f.endswith('.csv')]
                    
                    if files:
                        del_file = st.selectbox("Chọn đề cần xóa:", files, key="del_file")
                        if st.button("Xóa đề này", type="primary"):
                            os.remove(os.path.join(sub_dir, del_file))
                            st.success(f"Đã xóa thành công file {del_file}!")
                            st.rerun() # Tải lại trang để cập nhật danh sách
                    else:
                        st.info("Không có đề thi nào trong môn này.")
    elif pwd != "":
        st.error("Sai mật khẩu!")

def take_quiz_section():
    st.header("Làm bài kiểm tra")
    
    subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    
    if not subjects:
        st.warning("Hiện chưa có dữ liệu môn học nào.")
        return

    selected_subject = st.selectbox("Chọn môn học:", subjects)
    
    if selected_subject:
        subject_dir = os.path.join(DATA_DIR, selected_subject)
        files = [f for f in os.listdir(subject_dir) if f.endswith('.csv')]
        
        if not files:
            st.warning("Môn này hiện chưa có đề thi nào.")
            return
            
        selected_file = st.selectbox("Chọn đề thi:", files)
        
        if selected_file:
            file_path = os.path.join(subject_dir, selected_file)
            df = pd.read_csv(file_path)
            
            st.write(f"### Đang làm bài: {selected_file} - Môn: {selected_subject}")
            
            # Chọn chế độ làm bài
            mode = st.radio("Chế độ làm bài:", ["Làm tất cả cùng lúc", "Làm từng câu một"], horizontal=True)
            
            if mode == "Làm tất cả cùng lúc":
                render_quiz_all(df)
            else:
                render_quiz_step_by_step(df, selected_file)

def render_quiz_all(df):
    st.write("---")
    with st.form(key="quiz_form"):
        user_answers = {}
        for index, row in df.iterrows():
            st.markdown(f"**Câu {index + 1}: {row['Câu hỏi']}**")
            
            options_display = {"A": f"A. {row['Đáp án A']}", "B": f"B. {row['Đáp án B']}", "C": f"C. {row['Đáp án C']}", "D": f"D. {row['Đáp án D']}"}
            
            user_choice = st.radio(
                label="Chọn đáp án:",
                options=["A", "B", "C", "D"],
                format_func=lambda x: options_display[x],
                key=f"q_all_{index}",
                index=None, # ĐÃ SỬA: Không chọn mặc định đáp án A
                label_visibility="collapsed"
            )
            user_answers[index] = user_choice
            st.write("") 
        
        submit_button = st.form_submit_button(label="Nộp bài")
        
    if submit_button:
        score = 0
        st.write("---")
        st.header("Kết quả")
        for index, row in df.iterrows():
            correct_answer = str(row['Đáp án đúng']).strip().upper()
            user_choice = user_answers[index]
            
            if user_choice is None:
                st.warning(f"Câu {index + 1}: Bạn chưa chọn đáp án. (Đáp án đúng là {correct_answer})")
            elif user_choice == correct_answer:
                score += 1
                st.success(f"Câu {index + 1}: Đúng! (Đáp án {correct_answer})")
            else:
                st.error(f"Câu {index + 1}: Sai. Bạn chọn {user_choice}, đáp án đúng là {correct_answer}")
                
        st.info(f"**Số câu đúng: {score}/{len(df)}**")
        st.metric(label="Điểm (Thang 10)", value=round((score / len(df)) * 10, 2))

def render_quiz_step_by_step(df, file_name):
    # Khởi tạo Session State nếu chuyển sang đề khác hoặc mới bắt đầu
    if "current_quiz" not in st.session_state or st.session_state.current_quiz != file_name:
        st.session_state.current_quiz = file_name
        st.session_state.current_q = 0    # Câu hỏi hiện tại
        st.session_state.score = 0        # Số điểm
        st.session_state.answered = False # Đã nộp câu trả lời cho câu hỏi này chưa?
        st.session_state.choice = None    # Đáp án người dùng chọn
        st.session_state.results = []     # Lưu kết quả tổng hợp

    # Kiểm tra nếu đã làm xong hết câu hỏi
    if st.session_state.current_q >= len(df):
        st.success("🎉 Bạn đã hoàn thành bài kiểm tra!")
        st.info(f"**Số câu đúng: {st.session_state.score}/{len(df)}**")
        st.metric(label="Điểm (Thang 10)", value=round((st.session_state.score / len(df)) * 10, 2))
        
        if st.button("Làm lại từ đầu"):
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.results = []
            st.rerun()
        return

    st.write("---")
    idx = st.session_state.current_q
    row = df.iloc[idx]
    
    # In câu hỏi
    st.markdown(f"**Câu {idx + 1}/{len(df)}: {row['Câu hỏi']}**")
    options_display = {"A": f"A. {row['Đáp án A']}", "B": f"B. {row['Đáp án B']}", "C": f"C. {row['Đáp án C']}", "D": f"D. {row['Đáp án D']}"}

    # Nếu chưa trả lời câu này -> Hiện form cho chọn
    if not st.session_state.answered:
        with st.form(key=f"step_form_{idx}"):
            choice = st.radio("Chọn đáp án:", ["A", "B", "C", "D"], format_func=lambda x: options_display[x], index=None, label_visibility="collapsed")
            submit = st.form_submit_button("Trả lời")
            
            if submit:
                if choice is None:
                    st.warning("Vui lòng chọn một đáp án trước khi nhấn Trả lời!")
                else:
                    st.session_state.choice = choice
                    st.session_state.answered = True
                    st.rerun()
    
    # Nếu đã trả lời -> Hiện kết quả của câu đó và nút Next
    else:
        st.radio("Bạn đã chọn:", ["A", "B", "C", "D"], format_func=lambda x: options_display[x], index=["A", "B", "C", "D"].index(st.session_state.choice), disabled=True, label_visibility="collapsed")
        
        correct_answer = str(row['Đáp án đúng']).strip().upper()
        if st.session_state.choice == correct_answer:
            st.success("✅ Chính xác!")
        else:
            st.error(f"❌ Sai rồi. Đáp án đúng là {correct_answer}")
            
        if st.button("Câu tiếp theo ➡️", type="primary"):
            # Cập nhật điểm trước khi sang câu mới
            if st.session_state.choice == correct_answer:
                st.session_state.score += 1
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.rerun()

# --- ĐIỀU HƯỚNG CHÍNH ---
st.title("Hệ thống Trắc nghiệm Tự do")

menu = ["Làm bài", "Quản lý (Admin)"]
choice = st.sidebar.selectbox("Chức năng", menu)

if choice == "Làm bài":
    take_quiz_section()
else:
    admin_section()