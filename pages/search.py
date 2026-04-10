from math import isqrt

import streamlit as st
from pyncm.apis.cloudsearch import GetSearchResult

from models import AudioQuality, Track
from renderer import (DisplayOption, location, render_track_card, render_track_item,
                      render_track_list_style)

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")

with st.sidebar:
    view = st.radio(
        label="View",
        options=["List", "Card"],
        key="view",
        horizontal=True
    )

    displays = st.pills(
        label="Display",
        options=DisplayOption,
        key="display",
        default=[
            DisplayOption.COVER,
            DisplayOption.ALBUM,
            DisplayOption.DOWNLOAD,
        ],
        selection_mode="multi"
    )

    limit = st.slider(
        label="Limit",
        key="limit",
        min_value=1,
        value=10,
        max_value=100
    )

    quality = st.radio(
        label="Quality",
        key="quality",
        options=list(AudioQuality),
        help="Will fallback to highest quality if not available."
    )


with location("location_search") as loc:
    keyword = st.text_input("Search for songs...", loc.search.get("keyword", ""))
    loc.search["keyword"] = keyword

if not keyword:
    st.stop()


@st.cache_data
def search(keyword: str, limit: int):
    response = GetSearchResult(keyword, limit=limit)
    try:
        return response["result"]  # type: ignore
    except KeyError:
        st.error(f"Search failed: {response['message']}")  # type: ignore
        st.json(response)
        st.stop()


result = search(keyword, limit)

if not (tracks := result.get("songs")):
    st.error("No tracks found.")
    st.stop()

tracks = [Track(**data) for data in tracks]

if view == "List":
    render_track_list_style()
    for track in tracks:
        with st.container(border=True):
            render_track_item(track.album, track, displays, quality)

elif view == "Card":
    column_count = min(isqrt(len(tracks)), 4)
    columns = st.columns(column_count)
    for index, track in enumerate(tracks):
        with columns[index % column_count].container(border=True):
            render_track_card(track.album, track, displays, quality)
