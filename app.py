import streamlit as st

#main_page = st.Page("pages/0_welcome.py", title="Main Page", icon=None)
page_1 = st.Page("pages/1_doaj_quick_search.py", title="1. DOAJ Quick Search", icon=None)
page_2 = st.Page("pages/3_doaj_explore_scimago.py", title="2. SCImago Ranking Explorer", icon=None)

# Set up navigation
pg = st.navigation([page_1, page_2])

# Run the selected page
pg.run()