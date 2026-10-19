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

# df = load_data(file_name='doaj_journalcsv_20260726_scimago_ranking.tsv')
df = load_data(file_name='doaj_journalcsv_20260918_scimago_ranking.tsv')


md_txt = """
## DOAJ Journal Quick Search 
DOAJ Journal Quick Search helps you find open access journals and check available journal ranking information in one place.     
The tool searches journals indexed in the Directory of Open Access Journals (DOAJ) and provides basic information such as publisher, publication fees, average time from submission to publication, and links to the journal’s DOAJ page.
When available, it also provides quartile rankings from SCImago Journal Ranking.
### How to Search
Enter a journal title or ISSN in the search box, then click the search button.  
To limit your search to journals without article processing charges (APCs), select “Yes” for “Diamond OA only.”
### Viewing Results
If matching journals are found, the results will appear below the search box.
Click “View details” to expand the record and see more information.
### Want to explore journals by subject area?
Use the **SCImago Ranking Explorer** from the left sidebar to browse journals by subject area and ranking quartile.
### Important Notes
- Last updated: October 1, 2026
- **APCs may change over time. Please check the journal’s website for the most up-to-date information.**
- If you find a journal that interests you and would like to check whether it is indexed in Web of Science, visit the [Web of Science Master Journal List](https://mjl.clarivate.com/home).
"""

st.markdown(md_txt)

df = df.rename(columns={'Quartile': 'SJR quartile'})

df['SJR quartile'] = df['SJR quartile'].str.replace('Q', '')
df['SJR quartile'] = df['SJR quartile'].astype(float).astype('Int64')

#st.write(df)

with st.form("search_form"):
    col1, col2, col3, col4 = st.columns([4, 2, 2, 0.5], vertical_alignment="bottom")

    with col1:
        search_term = st.text_input(
            "Search",
            placeholder="Search a journal by title or ISSN",
            label_visibility="collapsed"
        )

    with col2:
        search_field = st.selectbox(
            "Search by",
            ["Journal Title", "ISSN"],
            #label_visibility="collapsed"
        )
    with col3:
        only_diamond = st.selectbox(
            "Diamond OA only",
            ["No", "Yes"],
            index=0
            #label_visibility="collapsed"
        )

    with col4:
        submitted = st.form_submit_button("🔍", use_container_width=True)

    if submitted:
        if only_diamond == 'Yes':
            #st.write(df['APC'].unique().tolist())
            df = df.loc[df['APC']=='No']
        if search_term.strip():
            #st.write(search_field)
            jrn_unique = df[['Journal title', 'URL in DOAJ']].drop_duplicates()
            jrn_unique = jrn_unique.dropna()
            if search_field == 'Journal Title':
                jrn_ti_split = search_term.lower().strip().split()
                found_doaj_ids = [['URL in DOAJ', 'n_word_matched']]
                for i, row in jrn_unique.iterrows():
                    doaj_ti = row['Journal title'].lower().strip().split()
                    doaj_id = row['URL in DOAJ']

                    overlap = set(jrn_ti_split) & set(doaj_ti)

                    if len(overlap) > 0:
                        found_doaj_ids.append([doaj_id, len(overlap)])
                
                found_doaj_ids = pd.DataFrame(found_doaj_ids[1:], columns=found_doaj_ids[0])
                if found_doaj_ids.shape[0] > 0:
                    max_n_words = found_doaj_ids['n_word_matched'].max()
                    found_doaj_ids = found_doaj_ids.loc[found_doaj_ids['n_word_matched']==max_n_words]
                    found_doaj_ids = found_doaj_ids['URL in DOAJ'].tolist()
                    df_found = df.loc[df['URL in DOAJ'].isin(found_doaj_ids)]
                    df_found = df_found.sort_values(by='SJR quartile', ascending=True)

                    df_found_urls = df_found['URL in DOAJ'].unique().tolist()
                    #df_found_g = df_found.groupby('URL in DOAJ')
                    #for i, dfg in df_found_g:
                    for df_found_url in df_found_urls:
                        dfg = df_found.loc[df_found['URL in DOAJ']==df_found_url]
                        
                        jrn_ti = dfg['Journal title'].tolist()[0]
                        jrn_url = dfg['Journal URL'].tolist()[0]
                        jrn_url_doaj = dfg['URL in DOAJ'].tolist()[0]
                        avg_time = dfg['Average number of weeks between article submission and publication'].tolist()[0]
                        publisher = dfg['Publisher'].tolist()[0]
                        has_apc = dfg['APC'].tolist()[0]
                        apc_amount = dfg['APC amount'].tolist()[0]
                        pissn = dfg['Journal ISSN (print version)'].tolist()[0]
                        eissn = dfg['Journal EISSN (online version)'].tolist()[0]

                        with st.expander(f'{jrn_ti} - *View details.*'):
                            #st.write(dfg)
                            if has_apc == 'Yes':
                                md_txt = f"""
                                - Publisher: {publisher}
                                - ISSN: {pissn}
                                - E-ISSN: {eissn}
                                - Average {avg_time} weeks from submission to publication.
                                - The journal charges an article processing charge (APC) of up to *{apc_amount}*.
                                - [Link to journal's DOAJ page]({jrn_url_doaj})
                                - [Link to journal's website]({jrn_url})
                                """                            
                            else:
                                md_txt = f"""
                                - Publisher: {publisher}
                                - ISSN: {pissn}
                                - E-ISSN: {eissn}
                                - Average {avg_time} weeks from submission to publication.
                                - There is no fee to publish in this journal.
                                - [Link to journal's DOAJ page]({jrn_url_doaj})
                                - [Link to journal's website]({jrn_url})
                                """ 
                            st.markdown(md_txt)
                            
                            with st.container(border=True):
                                st.markdown("SCImago Journal Rank 2025")
                                dfg_rank = dfg.sort_values(by='SJR quartile', ascending=True)
                                dfg_rank = dfg_rank.loc[~dfg_rank['SJR quartile'].isna()]
                                if dfg_rank.shape[0] > 0:
                                    st_cols = st.columns(dfg_rank.shape[0])

                                    for i, row in enumerate(dfg_rank[['Category', 'SJR quartile']].values.tolist()):
                                        st_col = st_cols[i]
                                        with st_col:
                                            st.metric(str(row[0]), f'Q{row[1]}')
                                else:
                                    st.write('This journal is not currently listed in the journal ranking.')
                
                else:
                    st.write('No results found.')
            
            if search_field == 'ISSN':
                issn = search_term.strip()
                issn = issn.replace('-', '')

                df['Journal ISSN (print version)'] = df['Journal ISSN (print version)'].astype(str)
                df['Journal EISSN (online version)'] = df['Journal EISSN (online version)'].astype(str)

                cond1 = df['Journal ISSN (print version)'] == str(issn)
                cond2 = df['Journal EISSN (online version)'] == str(issn)
                df_issn = df.loc[(cond1)|(cond2)]
                #st.write(df_issn)

                if df_issn.shape[0] > 0:
                    jrn_ti = df_issn['Journal title'].tolist()[0]
                    jrn_url = df_issn['Journal URL'].tolist()[0]
                    jrn_url_doaj = df_issn['URL in DOAJ'].tolist()[0]
                    avg_time = df_issn['Average number of weeks between article submission and publication'].tolist()[0]
                    publisher = df_issn['Publisher'].tolist()[0]
                    has_apc = df_issn['APC'].tolist()[0]
                    apc_amount = df_issn['APC amount'].tolist()[0]
                    pissn = df_issn['Journal ISSN (print version)'].tolist()[0]
                    eissn = df_issn['Journal EISSN (online version)'].tolist()[0]

                    with st.expander(f'{jrn_ti} - *View details.*'):
                        if has_apc == 'Yes':
                            md_txt = f"""
                            - Publisher: {publisher}
                            - ISSN: {pissn}
                            - E-ISSN: {eissn}
                            - Average {avg_time} weeks from submission to publication.
                            - The journal charges an article processing charge (APC) of up to *{apc_amount}*.
                            - [Link to journal's DOAJ page]({jrn_url_doaj})
                            - [Link to journal's website]({jrn_url})
                            """                            
                        else:
                            md_txt = f"""
                            - Publisher: {publisher}
                            - ISSN: {pissn}
                            - E-ISSN: {eissn}
                            - Average {avg_time} weeks from submission to publication.
                            - There is no fee to publish in this journal.
                            - [Link to journal's DOAJ page]({jrn_url_doaj})
                            - [Link to journal's website]({jrn_url})
                            """ 
                        st.markdown(md_txt)
                        
                        with st.container(border=True):
                            st.markdown("SCImago Journal Rank 2025")
                            dfg_rank = df_issn.sort_values(by='SJR quartile', ascending=True)
                            dfg_rank = dfg_rank.loc[~dfg_rank['SJR quartile'].isna()]
                            if dfg_rank.shape[0] > 0:
                                st_cols = st.columns(dfg_rank.shape[0])

                                for i, row in enumerate(dfg_rank[['Category', 'SJR quartile']].values.tolist()):
                                    st_col = st_cols[i]
                                    with st_col:
                                        st.metric(str(row[0]), f'Q{row[1]}')
                            else:
                                st.write('This journal is not currently listed in the journal ranking.')
                else:
                    st.write('No results found.')

md_txt = f"""
##### Data Sources
Directory of Open Access Journals. (n.d.). Journal CSV - DOAJ. Retrieved August 26, 2026, from https://doaj.org/docs/journal-csv     
SCImago. (n.d.). SJR-SCImago Journal Country & Rank [Portal]. Retrieved July 6, 2026, from https://www.scimagojr.com    
"""
st.markdown(md_txt)