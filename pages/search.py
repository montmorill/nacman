from math import isqrt

import requests
import streamlit as st
from pyncm import apis

from models import AudioQuality, Track

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")

with st.sidebar:
    view = st.radio("View", ["List", "Card"], key="view", horizontal=True)
    options = ["Cover", "Lyrics", "Track ID", "Download", "Detail"]
    display = st.pills("Display", options=options, key="display",
                       default=["Cover"], selection_mode="multi")
    limit = st.slider("Limit", key="limit", min_value=1, value=12)
    qualities = [quality.value for quality in AudioQuality]
    quality = st.radio("Quality", qualities, key="quality", horizontal=True)

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


def download_button(track: Track):
    stream = requests.get(track.url(quality), stream=True)
    st.download_button(
        label="Download",
        data=stream.content,
        on_click=lambda: stream.close(),
        file_name=f"{track.title}.mp3",
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
            with st.container(horizontal=True, vertical_alignment="center"):
                if "Download" in display:
                    download_button(track)
                st.audio(track.url(quality))
            if "Lyrics" in display:
                st.write(track.lyrics)
            if "Detail" in display:
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
                    download_button(track)
            with audio.container(height="stretch", vertical_alignment="center"):
                st.audio(track.detail(quality)["url"])
            if "Lyrics" in display:
                st.write(track.lyrics)
            if "Detail" in display:
                st.json(track.model_dump_json())
