from math import isqrt

import requests
import streamlit as st
from pyncm import apis

from models import Track

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")

with st.sidebar:
    limit = st.slider("Limit", min_value=1, max_value=100, value=9)
    view = st.radio("View", ["List", "Card"], horizontal=True)
    display = st.pills("Display", ["Cover", "Track ID", "Download", "Json"],
                       default=["Cover"], selection_mode="multi")

if search_query := st.text_input("Search for songs..."):
    result = apis.cloudsearch.GetSearchResult(search_query, limit=limit)
    tracks = [Track(**data) for data in result["result"]["songs"]]

    if track_count := len(tracks):
        if view == "Card":
            column_count = isqrt(track_count)
            columns = st.columns(column_count)
            for index, track in enumerate(tracks):
                with columns[index % column_count].container(border=True):
                    caption = track.title
                    if "Track ID" in display:
                        caption += f" #{track.id}"
                    if "Cover" in display:
                        st.image(track.album.pic_url, caption=caption)
                    else:
                        st.text(caption)
                    with st.container(horizontal=True, vertical_alignment="center"):
                        if "Download" in display:
                            st.download_button(
                                label="Download",
                                data=requests.get(
                                track.detail["url"], stream=True).content,
                                file_name=f"{track.title}.mp3",
                                mime="audio/mpeg"
                            )
                        st.audio(track.detail["url"])
                    if "Json" in display:
                        st.json(track.model_dump_json(), expanded=False)
            st.stop()
        st.html("""<style>
                .stHorizontalBlock:has(> .stElementContainer > .stHtml > .nac-nowrap) {
                    flex-wrap: nowrap !important;
                }
                .nac-nowrap {
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .subtext {
                    font-size: 0.8em;
                    color: rgb(49, 51, 63);
                }
            </style>""")
        for track in tracks:
            with st.container(border=True):
                info, audio = st.columns(2)
                with info.container(horizontal=True, vertical_alignment="center"):
                    if "Cover" in display:
                        st.image(track.album.pic_url, width=48)
                    artists = " / ".join(artist.name for artist in track.artists)
                    subtext = artists
                    if "Track ID" in display:
                        subtext = f"#{track.id} {subtext}"
                    st.html(f'''<div class="nac-nowrap">
                        <div>{track.name}</div>
                        <div class="subtext">{subtext}</div>
                    </div>''')
                    if "Download" in display:
                        st.download_button(
                            label="Download",
                            data=requests.get(
                                track.detail["url"], stream=True).content,
                            file_name=f"{track.title}.mp3",
                            mime="audio/mpeg"
                        )
                with audio.container(height="stretch", vertical_alignment="center"):
                    st.audio(track.detail["url"])
                if "Json" in display:
                    st.json(track.model_dump_json(), expanded=False)
    else:
        st.error("No tracks found.")
