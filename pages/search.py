from math import isqrt

import streamlit as st
from pyncm import apis

from models import Track

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")


with st.sidebar:
    search_query = st.text_input('Search for songs...')
    limit = st.sidebar.slider('Limit', min_value=1, max_value=30, value=10)


if search_query:
    result = apis.cloudsearch.GetSearchResult(search_query, limit=limit)
    tracks = [Track(**data) for data in result['result']['songs']]

    if track_count := len(tracks):
        column_count = isqrt(track_count)
        columns = st.columns(column_count)
        for index, track in enumerate(tracks):
            track.bind(columns[index % column_count])
    else:
        st.error('No tracks found.')
