import streamlit as st

pg = st.navigation([
    st.Page("pages/profile.py", title="Profile", icon="👤"),
    st.Page("pages/search.py", title="Search", icon="🔍"),
    st.Page("pages/album.py", title="Album", icon="💿"),
])

pg.run()
