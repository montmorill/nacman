from functools import cache
from math import isqrt

import streamlit as st
from pyncm.apis.cloudsearch import GetSearchResult

from models import AudioQuality, Track
from renderer import Display, render_track_card, render_track_item, render_track_list_style

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
        options=Display,
        key="display",
        default=[Display.COVER, Display.DOWNLOAD],
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
        horizontal=True,
        options=list(AudioQuality),
        help="Will fallback to highest quality if not available."
    )


if not (keyword := st.text_input("Search for songs...")):
    st.stop()


@cache
def search(keyword: str, limit: int):
    response = GetSearchResult(keyword, limit=limit)
    return response["result"]  # type: ignore


result = search(keyword, limit)

if not (tracks := result.get("songs")):
    st.error("No tracks found.")
    st.stop()

tracks = [Track(**data) for data in tracks]

if view == "List":
    render_track_list_style()
    for track in tracks:
        with st.container(border=True):
            render_track_item(track, displays, quality)

elif view == "Card":
    column_count = min(isqrt(len(tracks)), 4)
    columns = st.columns(column_count)
    for index, track in enumerate(tracks):
        with columns[index % column_count].container(border=True):
            render_track_card(track, displays, quality)
