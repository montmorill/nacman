from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from math import isqrt

import streamlit as st
from pyncm.apis.cloudsearch import GetSearchResult

from models import AudioQuality, Track

st.set_page_config(page_title="Search", page_icon=":dvd:", layout="wide")


class DisplayOptions(StrEnum):
    COVER = "Cover"
    QUALITY = "Quality"
    DOWNLOAD = "Download"
    LYRICS = "Lyrics"
    TRACK_ID = "Track ID"
    DETAILS = "Details"


@dataclass
class Display:
    COVER: bool = False
    QUALITY: bool = False
    DOWNLOAD: bool = False
    LYRICS: bool = False
    TRACK_ID: bool = False
    DETAILS: bool = False


with st.sidebar:
    view = st.radio(
        label="View",
        options=["List", "Card"],
        key="view",
        horizontal=True
    )

    display_options = st.pills(
        label="Display",
        options=DisplayOptions,
        key="display",
        default=[DisplayOptions.COVER, DisplayOptions.DOWNLOAD],
        selection_mode="multi"
    )

    display = Display(**{
        option.name: option in display_options
        for option in DisplayOptions
    })

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


@st.fragment
def render_download_button(track: Track, quality: AudioQuality):
    detail = track.detail(quality)
    st.download_button(
        label="Download",
        key=f"download_{track.id}",
        data=detail["url"],
        file_name=f"{track.title}.{detail['type']}",
    )


@st.fragment
def render_lyrics(track: Track):
    availables = [(key, lyrics) for key, lyrics in track.lyrics if lyrics.text]
    if len(availables) > 1:
        tabs = st.tabs([key.capitalize() for (key, _) in availables])
        for index, (_, lyrics) in enumerate(availables):
            tabs[index].text(lyrics.text)
    else:
        st.text(availables[0][1].text)


@st.fragment
def render_track_card(track: Track, quality: AudioQuality):
    caption = track.title
    if display.TRACK_ID:
        caption += f" #{track.id}"
    if display.COVER:
        st.image(track.album.pic_url, caption=caption)
    else:
        st.text(caption)

    horizontal = display.DOWNLOAD and not display.QUALITY
    with st.container(horizontal=horizontal, horizontal_alignment="center"):

        placeholder = st.empty()

        if display.QUALITY:
            with st.container(horizontal=True, horizontal_alignment="center"):
                if display.DOWNLOAD:
                    left, right = st.columns([2, 1], vertical_alignment="center")
                    with right:
                        render_download_button(track, quality)
                else:
                    left = st
                quality = left.radio(
                    "quality", track.qualities.keys(),
                    key=f"quality_{track.id}",
                    horizontal=True, label_visibility="collapsed"
                )

        elif display.DOWNLOAD:
            render_download_button(track, quality)

        placeholder.audio(track.detail(quality)["url"])

    if display.LYRICS:
        render_lyrics(track)

    if display.DETAILS:
        st.json(track.model_dump_json())


@st.fragment
def render_track_list(track: Track, quality: AudioQuality):
    info, audio = st.columns(2)

    placeholder = info.empty()

    if display.QUALITY:
        quality = st.radio(
            "quality", track.qualities.keys(),
            key=f"quality_{track.id}",
            horizontal=True, label_visibility="collapsed"
        )

    with placeholder.container(horizontal=True, vertical_alignment="center"):

        if display.COVER:
            st.image(track.album.pic_url, width=48)

        subtext = " / ".join(artist.name for artist in track.artists)

        if display.TRACK_ID:
            subtext = f"#{track.id} {subtext}"

        st.html(f'''\
<div class="truncate">
    <div class="truncate">{track.name}</div>
    <div class="subtext">{subtext}</div>
</div>''')

        if display.DOWNLOAD:
            render_download_button(track, quality)

    with audio.container(height="stretch", vertical_alignment="center"):
        st.audio(track.detail(quality)["url"])

    if display.LYRICS:
        render_lyrics(track)

    if display.DETAILS:
        st.json(track.model_dump_json())


if view == "Card":
    column_count = min(isqrt(len(tracks)), 4)
    columns = st.columns(column_count)
    for index, track in enumerate(tracks):
        with columns[index % column_count].container(border=True):
            render_track_card(track, quality)

elif view == "List":
    st.html("""<style>
        .stHorizontalBlock:has(> .stElementContainer > .stHtml > .truncate) {
            flex-wrap: nowrap !important;
        }
        .truncate {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .subtext {
            font-size: 0.8em;
            color: #31333f;
        }
    </style>""")

    for track in tracks:
        with st.container(border=True):
            render_track_list(track, quality)
