import streamlit as st
import pandas as pd
import os
from github import Github

# Cấu trúc gốc
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Khởi tạo kết nối GitHub
def get_github_repo():
    try:
        g = Github(st.secrets["github_token"])
        repo = g.get_repo(st.secrets["github_repo"])
        return repo
    except Exception as e:
        st.error(f"Lỗi kết nối GitHub. Hãy kiểm tra lại secrets. Chi tiết lỗi: {e}")
        return None

def admin_section():
    st.header("Quản lý Đề thi (Admin)")
    pwd = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if pwd == st.secrets.get("admin_password", "123"):
        tab_upload, tab_delete, tab_download = st.tabs(["Tải lên đề mới", "Xóa đề thi", "Tải xuống đề thi"])
        repo = get_github_repo()
        
        # --- TAB TẢI LÊN ---
        with tab_upload:
            st.subheader("Tải lên đề thi")
            
            st.info('''**Lưu ý định dạng file .csv hợp lệ:**
"Câu hỏi","Đáp án A","Đáp án B","Đáp án C","Đáp án D","Đáp án đúng"
"Trước năm 26 tuổi, Issac Newton chứng minh được điều nào dưới đây ?","Định luật vạn vật hấp dẫn","Bản chất của ánh sáng","Ba định luật chuyển động","Tất cả đều đúng","D"''')
            
            existing_subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
            options = ["-- Chọn môn --"] + existing_subjects + ["+ Thêm môn học mới"]
            subject_choice = st.selectbox("Môn học:", options)
            
            subject = ""
            if subject_choice == "+ Thêm môn học mới":
                subject = st.text_input("Nhập tên môn học mới:").strip()
            elif subject_choice != "-- Chọn môn --":
                subject = subject_choice
                
            if subject:
                subject_dir = os.path.join(DATA_DIR, subject)
                if not os.path.exists(subject_dir):
                    os.makedirs(subject_dir)
                    
                uploaded_file = st.file_uploader("Chọn file CSV", type=["csv"], key="upload_csv")
                if uploaded_file is not None and repo is not None:
                    file_path = os.path.join(subject_dir, uploaded_file.name)
                    github_path = f"{DATA_DIR}/{subject}/{uploaded_file.name}"
                    
                    with st.spinner("Đang đẩy file lên hệ thống GitHub..."):
                        try:
                            # 1. Đẩy file lên GitHub
                            content = uploaded_file.getvalue()
                            repo.create_file(github_path, f"Upload {uploaded_file.name} via web", content)
                            
                            # 2. Lưu file ở local (container) để hệ thống đọc được ngay
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                            st.success(f"Đã lưu thành công đề '{uploaded_file.name}' vào môn '{subject}' và đồng bộ lên GitHub!")
                        except Exception as e:
                            st.error(f"Có lỗi khi đẩy lên GitHub (Có thể file đã tồn tại). Lỗi: {e}")

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
                        if st.button("Xóa đề này", type="primary") and repo is not None:
                            github_path = f"{DATA_DIR}/{del_subject}/{del_file}"
                            local_path = os.path.join(sub_dir, del_file)
                            
                            with st.spinner("Đang xóa file trên hệ thống GitHub..."):
                                try:
                                    # 1. Xóa trên GitHub
                                    contents = repo.get_contents(github_path)
                                    repo.delete_file(contents.path, f"Delete {del_file} via web", contents.sha)
                                    
                                    # 2. Xóa ở local
                                    if os.path.exists(local_path):
                                        os.remove(local_path)
                                        
                                    st.success(f"Đã xóa vĩnh viễn file {del_file}!")
                                    st.rerun() 
                                except Exception as e:
                                    st.error(f"Có lỗi khi xóa trên GitHub. Lỗi: {e}")
                    else:
                        st.info("Không có đề thi nào trong môn này.")
                        
        # --- TAB TẢI XUỐNG ---
        with tab_download:
            st.subheader("Tải xuống đề thi")
            subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
            if not subjects:
                st.info("Chưa có môn học nào.")
            else:
                dl_subject = st.selectbox("Chọn môn:", subjects, key="dl_sub")
                if dl_subject:
                    sub_dir = os.path.join(DATA_DIR, dl_subject)
                    files = [f for f in os.listdir(sub_dir) if f.endswith('.csv')]
                    
                    if files:
                        dl_file = st.selectbox("Chọn đề cần tải:", files, key="dl_file")
                        file_path = os.path.join(sub_dir, dl_file)
                        
                        with open(file_path, "rb") as file:
                            st.download_button(
                                label=f"⬇️ Tải xuống file {dl_file}",
                                data=file,
                                file_name=dl_file,
                                mime="text/csv"
                            )
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
            df.columns = df.columns.str.strip() 
            
            st.write(f"### Đang làm bài: {selected_file} - Môn: {selected_subject}")
            
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
                index=None,
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
    if "current_quiz" not in st.session_state or st.session_state.current_quiz != file_name:
        st.session_state.current_quiz = file_name
        st.session_state.current_q = 0    
        st.session_state.score = 0        
        st.session_state.answered = False 
        st.session_state.choice = None    
        st.session_state.results = []     

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
    
    st.markdown(f"**Câu {idx + 1}/{len(df)}: {row['Câu hỏi']}**")
    options_display = {"A": f"A. {row['Đáp án A']}", "B": f"B. {row['Đáp án B']}", "C": f"C. {row['Đáp án C']}", "D": f"D. {row['Đáp án D']}"}

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
    
    else:
        st.radio("Bạn đã chọn:", ["A", "B", "C", "D"], format_func=lambda x: options_display[x], index=["A", "B", "C", "D"].index(st.session_state.choice), disabled=True, label_visibility="collapsed")
        correct_answer = str(row['Đáp án đúng']).strip().upper()
        
        if st.session_state.choice == correct_answer:
            st.success("✅ Chính xác!")
        else:
            st.error(f"❌ Sai rồi. Đáp án đúng là {correct_answer}")
            
        if st.button("Câu tiếp theo ➡️", type="primary"):
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