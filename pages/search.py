from math import isqrt

import requests
import streamlit as st
from pyncm import apis

from models import AudioQuality, Track

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")

with st.sidebar:
    view = st.radio("View", ["List", "Card"], key="view", horizontal=True)
    options = ["Cover", "Lyrics", "Track ID", "Quality", "Download", "Details"]
    display = st.pills("Display", options=options, key="display",
                       default=["Cover"], selection_mode="multi")
    limit = st.slider("Limit", key="limit", min_value=1, value=12)
    quality = st.radio("Quality", AudioQuality, horizontal=True)

if not (keywords := st.text_input("Search for songs...")):
    st.stop()

result = apis.cloudsearch.GetSearchResult(
    keywords,
    limit=limit
)["result"]  # type: ignore

if not (tracks := result.get("songs")):
    st.error("No tracks found.")
    st.stop()

tracks = [Track(**data) for data in tracks]


def download_button(track: Track, quality: str):
    detail = track.detail(quality)
    stream = requests.get(detail["url"], stream=True)
    st.download_button(
        label="Download",
        data=stream.content,
        on_click=lambda: stream.close(),
        file_name=f"{track.title}.{detail['type']}",
        mime="audio/mpeg"
    )


if view == "Card":
    column_count = isqrt(len(tracks))
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
            horizontal = "Download" in display and "Quality" not in display
            with st.container(horizontal=horizontal, horizontal_alignment="center"):
                placeholder = st.empty()
                if "Quality" in display:
                    with st.container(horizontal=True, horizontal_alignment="center"):
                        quality = st.radio(
                            "quality", track.qualities.keys(),
                            key=f"quality_{track.id}",
                            horizontal=True, label_visibility="collapsed")
                        if "Download" in display:
                            download_button(track, quality)
                elif "Download" in display:
                    download_button(track, quality)
                placeholder.audio(track.detail(quality)["url"])
            if "Lyrics" in display:
                st.write(track.lyrics)
            if "Details" in display:
                st.json(track.model_dump_json())
    st.stop()

elif view == "List":
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
        with st.container(border=True, horizontal="Quality" not in display):
            with st.container(horizontal=True, vertical_alignment="center"):
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
                if "Quality" in display:
                    quality = st.radio(
                        "quality", track.qualities.keys(),
                        key=f"quality_{track.id}",
                        horizontal=True, label_visibility="collapsed")
                if "Download" in display:
                    download_button(track, quality)
            with st.container(height="stretch", vertical_alignment="center"):
                st.audio(track.detail(quality)["url"])
            if "Lyrics" in display:
                st.write(track.lyrics)
            if "Details" in display:
                st.json(track.model_dump_json())
