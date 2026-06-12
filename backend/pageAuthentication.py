import streamlit as st
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

col1, col2, col3 = st.columns([1, 4, 1])

if not st.session_state.authenticated:
    with col2:
        st.markdown("<h1 style='text-align: center;'>Authentication</h1>", unsafe_allow_html=True)
        login = st.text_input("Enter login:")
        password = st.text_input("Enter password:", type="password")

        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_b:
            login_button = st.button("Log in", use_container_width=True)

        if login_button:
            if password == st.secrets["admin_password"] and login == st.secrets["admin_login"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong login or password")
        st.stop()

employeesPage = st.Page("pages/pageEmployees.py", title="Employees")
logsPage = st.Page("pages/pageLogs.py", title="Logs")

pg = st.navigation([employeesPage, logsPage], position="sidebar")
pg.run()
with st.sidebar.container(key="sidebar_bottom"):
    if st.button("Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()