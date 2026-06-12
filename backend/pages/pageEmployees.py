import streamlit as st
import base64
import numpy as np
import pandas as pd

st.title("Employees")
col1, col2, col3, col4, col5 = st.columns(5)

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

icons = {
    "buttonPlus": "images/plus.png",
    "buttonMinus": "images/minus.png",
    "buttonSort": "images/sort.png",
    "buttonFilter": "images/filter.png",
    "buttonSearch": "images/search.png"
}
cols = [col1, col2, col3, col4, col5]

css = ""
for key, path in icons.items():
    b64 = img_to_base64(path)
    css += f"""
    div.st-key-{key} button {{
        background-image: url(data:image/png;base64,{b64});
        background-size: cover;
        width: 50px;
        height: 50px;
        border: none;
    }}
    """

st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

for col, key in zip(cols, icons.keys()):
    with col:
        with st.container(key=key):
            if key == "buttonPlus":
                if st.button("", key=f"button_{key}"):
                    st.write("Pressed plus")
            if key == "buttonMinus":
                if st.button("", key=f"button_{key}"):
                    st.write("Pressed minus")
            if key == "buttonFilter":
                if st.button("", key=f"button_{key}"):
                    st.write("Pressed filter")
            if key == "buttonSort":
                if st.button("", key=f"button_{key}"):
                    st.write("Pressed sort")
            if key == "buttonSearch":
                if st.button("", key=f"button_{key}"):
                    st.write("Pressed search")

    