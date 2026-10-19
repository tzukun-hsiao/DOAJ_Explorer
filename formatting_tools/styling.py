import streamlit as st


def hide_toolbar(container_key: str):
    st.markdown(
        f"""
        <style>
        .st-key-{container_key} [data-testid="stElementToolbar"] {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )