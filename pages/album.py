import streamlit as st
from pyncm.apis.album import GetAlbumInfo

from models import Album
from renderer import (AudioQuality, DisplayOption, render_comment,
                      render_track_item, render_track_list_style, url_params)

st.set_page_config(page_title="Album", page_icon=":dvd:", layout="wide")


with url_params(id=("album_id", int)):
    album_id = st.number_input(label="Album ID", key="album_id", step=1)


@st.cache_data
def get_album(album_id: str):
    return GetAlbumInfo(album_id)


response = get_album(str(album_id))
if response["code"] == 200:  # type: ignore
    album = Album(**response)  # type: ignore
else:
    st.error(f"Album not found.")
    st.json(response)
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


with st.container(horizontal=True, vertical_alignment="center"):
    st.image(album.info.pic_url, width=96)
    st.title(album.info.name)
    with st.container(height="stretch", horizontal_alignment="right",
                      vertical_alignment="center", gap=None):
        artists = ', '.join(artist.name for artist in album.info.artists)
        date = album.info.publish_time.date().strftime("%Y-%m-%d")
        st.text(f"{artists} {date}")
        st.text(f"{album.info.type} / {album.info.sub_type}")
        st.text(f"{album.info.size} tracks")
        st.text(album.info.company)

tracks_tab, details_tab, comments_tab = st.tabs(
    ["Tracks", "Details", "Comments"])

with tracks_tab:
    for track in album.songs:
        with st.container(horizontal=True, vertical_alignment="center"):
            quality = AudioQuality.EXHIGH
            render_track_item(album.info, track, displays, quality)

with details_tab:
    if album.info.brief_desc:
        st.text(album.info.brief_desc)
    with st.expander("Description", expanded=True):
        st.text(album.info.description)
    st.json(album.info.model_dump())

with comments_tab:
    for comment in album.comments:
        with st.container(horizontal=True):
            render_comment(comment)
