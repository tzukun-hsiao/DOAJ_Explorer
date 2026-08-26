import streamlit as st
import numpy as np
import pandas as pd
import requests
import io
from github import Github, Auth

st.set_page_config(layout="wide")

@st.cache_data
def load_data(file_name):
    auth = Auth.Token(st.secrets["GITHUB_TOKEN"])
    g = Github(auth=auth)
    repo = g.get_repo(st.secrets["DATA_REPO"])

    file = repo.get_contents(f'DOAJ_Explorer/{file_name}')

    response = requests.get(
        file.download_url,
        headers={"Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}"}
    )
    response.raise_for_status()

    return pd.read_csv(io.BytesIO(response.content), sep='\t')

df = load_data(file_name='doaj_journalcsv_20260726_scimago_ranking.tsv')
df = df.rename(columns={'Quartile': 'SJR quartile'})
#st.write(df.columns.tolist())
df = df.loc[~df['Top Category'].isna()]

md_txt = f"""
### DOAJ Journals in SCImago Ranking: Subject Area Explorer
This tool helps users explore DOAJ-indexed journals that are included in SCImago ranking.   
Use the dropdown menu below to browse journals by subject area and by SCImago quartile ranking.
- Last updated: August 26, 2026
- **Article processing charges (APCs) may change over time. Please check the journal’s website for the most up-to-date information.**
- If you find a journal that interests you and would like to check whether it is indexed in Web of Science, visit the [Web of Science Master Journal List](https://mjl.clarivate.com/home).
"""
st.markdown(md_txt)

#st.write(df.columns.tolist())

scimago = df.loc[~df['SJR quartile'].isna()]
scimago['SJR'] = scimago['SJR'].str.replace(',', '.')
scimago['SJR'] = scimago['SJR'].astype(float)
fields = scimago['Top Category'].unique().tolist()
fields.sort()
#st.write(scopus['Percentile'].unique().tolist())


option = st.selectbox(label=" ", placeholder='Select a Subject Area:', 
                      options=fields, index=None, key='selection1')
if option is not None:
    sub_fields = scimago.loc[scimago['Top Category']==option]['Category'].unique().tolist()
    sub_fields.sort()
    for isub, sub_field in enumerate(sub_fields):
        with st.expander(sub_field):
            df_display = scimago.loc[df['Category']==sub_field]
            quartiles = df_display['SJR quartile'].unique().tolist()
            quartiles.sort()
            for iq, quartile in enumerate(quartiles):
                with st.expander(f"SCImago quartile: {quartile}"):
                    #st.write(df_display)
                    no_apc = st.checkbox('Only show journals with no APCs', 
                                         key=f'no_apc_{isub}-{iq}')
                    df_display2 = df_display.loc[df_display['SJR quartile']==quartile]
                    df_display2 = df_display2.sort_values(by=['SJR', 'Publisher'], 
                                                          ascending=[False, True])

                    cols = ['Journal title', 'SJR quartile', 'Publisher', 'APC', 'APC amount', 
                            'Journal ISSN (print version)', 'Journal EISSN (online version)', 
                            'Journal URL', 'URL in DOAJ']
                    df_display2 = df_display2[cols]
                    df_display2 = df_display2.rename(columns={
                        'SJR quartile': 'Quartile',
                        'Journal ISSN (print version)': 'ISSN', 
                        'Journal EISSN (online version)': 'E-ISSN',
                        'URL in DOAJ': 'Journal DOAJ URL'})
                    
                    df_display2 = df_display2.set_index('Journal title')

                    if no_apc:
                        df_display2 = df_display2.loc[df_display2['APC']=='No']

                    if df_display2.shape[0] > 0:
                        st.dataframe(
                            df_display2, 
                            width='stretch',
                            column_config={
                                "Journal title": st.column_config.TextColumn("Journal title", width='large')
                                }
                            )
                    else:
                        st.write('No journals in this quartile and subject area are free of APCs.')