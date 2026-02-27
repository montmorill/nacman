from urllib.parse import parse_qs, urlencode

import streamlit as st
from pyncm.apis.album import GetAlbumInfo

from models import Album
from renderer import (AudioQuality, DisplayOption, render_track_item,
                      render_track_list_style, use_location)

st.set_page_config(page_title="Album", page_icon=":dvd:", layout="wide")

# Read URL params from previous render's location state
if (location := st.session_state.get("location"))\
        and "_url_synced" not in st.session_state:
    search_params = parse_qs(location.get("search", ""))
    if search_params.get("id"):
        st.session_state.album_id = int(search_params["id"][0])
    st.session_state._url_synced = True

album_id = st.number_input(
    label="Album ID",
    key="album_id",
    step=1,
)

# Sync album_id back to URL after initial URL read
data = {"search": urlencode({"id": int(album_id)})
        } if st.session_state.get("_url_synced") else None
use_location(key="location", data=data)


@st.cache_data
def get_album(album_id: str):
    return GetAlbumInfo(album_id)


album = get_album(str(album_id))
if album["code"] == 200:  # type: ignore
    album = Album(**album)  # type: ignore
else:
    st.error(f"Album not found.")
    st.json(album)
    st.stop()


with st.sidebar:
    displays = st.pills(
        label="Display",
        options=[
            option for option in DisplayOption
            if option != DisplayOption.ALBUM
        ],
        key="display",
        default=[
            DisplayOption.COVER,
            DisplayOption.DOWNLOAD,
        ],
        selection_mode="multi"
    )

    quality = st.radio(
        label="Quality",
        key="quality",
        options=AudioQuality,
    )

render_track_list_style()

for track in album.songs:
    with st.container(horizontal=True, vertical_alignment="center"):
        quality = AudioQuality.EXHIGH
        render_track_item(album.info, track, displays, quality)
