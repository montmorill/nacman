from contextlib import contextmanager
from enum import StrEnum
from typing import Any, Callable, TypedDict
from urllib.parse import parse_qs, urlencode

import streamlit as st
from streamlit.components.v2 import component

from models import (AudioDetail, AudioQuality, BaseAlbum, BaseTrack, Comment,
                    Track)


class DisplayOption(StrEnum):
    COVER = "Cover"
    ALBUM = "Album"
    DOWNLOAD = "Download"
    QUALITY = "Quality"
    LYRICS = "Lyrics"
    TRACK_ID = "Track ID"
    DETAILS = "Details"


def render_audio(detail: AudioDetail | None):
    if detail is None:
        st.error("No audio available due to copyright issues.")
    else:
        st.audio(detail.url)


def render_download_button(track: BaseTrack, quality: AudioQuality, **kwargs):
    if detail := track.detail(quality):
        artists = "/".join(artist.name for artist in track.artists)
        st.download_button(
            label="Download",
            key=f"download_{track.id}",
            data=detail.url,
            file_name=f"{track.name} - {artists}.{detail.type}",
            **kwargs
        )


def render_lyrics(track: BaseTrack):
    availables = [(key, lyrics) for key, lyrics in track.lyrics if lyrics.text]
    if len(availables) > 1:
        tabs = st.tabs([key.capitalize() for (key, _) in availables])
        for index, (_, lyrics) in enumerate(availables):
            tabs[index].text(lyrics.text)
    else:
        st.text(availables[0][1].text)


def render_track_list_style():
    st.html("""<style>
    .stHorizontalBlock:has(> .stElementContainer > .stHtml > .nac-truncate) {
        flex-wrap: nowrap !important;
    }
    .nac-truncate {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .nac-subtitle {
        font-size: 0.8em;
        color: #31333f;
    }
    </style>""")


@st.fragment
def render_track_item(
    album: BaseAlbum,
    track: BaseTrack,
    displays: list[DisplayOption],
    quality: AudioQuality
):
    if DisplayOption.QUALITY in displays:
        quality = st.session_state.get(f"quality_{track.id}", quality)

    info, audio = st.columns([3, 2], vertical_alignment="center")

    with info.container(horizontal=True, vertical_alignment="center"):
        if DisplayOption.COVER in displays:
            st.image(album.pic_url, width=48)

        title = track.name
        if DisplayOption.ALBUM in displays:
            title = f"<a href='/album?id={album.id}'>{album.name}</a> - {title}"

        subtitle = " / ".join(artist.name for artist in track.artists)
        if DisplayOption.TRACK_ID in displays:
            subtitle = f"#{track.id} {subtitle}"

        st.html(f'''
        <div class="nac-truncate">
            <div class="nac-truncate">{title}</div>
            <div class="nac-subtitle">{subtitle}</div>
        </div>''')

        if DisplayOption.DOWNLOAD in displays:
            render_download_button(track, quality)

        if DisplayOption.QUALITY in displays:
            st.selectbox(
                "Quality", track.qualities.keys(),
                key=f"quality_{track.id}",
                label_visibility="collapsed",
                width=120,
            )

    with audio.container(horizontal=True, vertical_alignment="center"):
        render_audio(track.detail(quality))

    if DisplayOption.LYRICS in displays:
        render_lyrics(track)

    if DisplayOption.DETAILS in displays:
        st.json(track.model_dump())


@st.fragment
def render_track_card(
    album: BaseAlbum,
    track: BaseTrack,
    displays: list[DisplayOption],
    quality: AudioQuality
):
    if DisplayOption.QUALITY in displays:
        quality = st.session_state.get(f"quality_{track.id}", quality)

    with st.container(horizontal=True, horizontal_alignment="distribute"):
        caption = track.name

        if DisplayOption.ALBUM in displays:
            caption = f"{album.name} - {caption}"
        if DisplayOption.TRACK_ID in displays:
            caption = f"{caption} #{track.id}"

        if DisplayOption.COVER in displays:
            st.image(album.pic_url, width="stretch", caption=caption)
        else:
            st.text(caption)

        render_audio(track.detail(quality))

        if DisplayOption.QUALITY in displays:
            st.select_slider(
                "Quality", track.qualities.keys(),
                key=f"quality_{track.id}",
                label_visibility="collapsed"
            )

        if DisplayOption.DOWNLOAD in displays:
            render_download_button(track, quality, width="stretch")

    if DisplayOption.LYRICS in displays:
        render_lyrics(track)

    if DisplayOption.DETAILS in displays:
        st.json(track.model_dump())


def render_comment(comment: Comment):
    st.image(comment.user.avatar_url, width=32)
    with st.container(gap=None):
        st.markdown(f"**{comment.user.nickname}** {comment.time_str}")
        st.text(comment.content)


class Location(TypedDict):
    search: str
    hash: str


@contextmanager
def url_params(location_key: str = "location", **params: tuple[str, Callable[[str]]]):
    """Bidirectional sync between URL search params and session state.

    Usage::

        with url_params(id=("album_id", int)):
            album_id = st.number_input("Album ID", key="album_id", step=1)

    Args:
        **params: url_param=(session_state_key, converter)
    """
    synced_key = f"_{location_key}_synced"

    # Read: URL → session_state (first render only)
    location: Location | None = st.session_state.get(location_key)
    if location and synced_key not in st.session_state:
        search_params = parse_qs(location.get("search", ""))
        for url_param, (state_key, converter) in params.items():
            if values := search_params.get(url_param):
                st.session_state[state_key] = converter(values[0])
        st.session_state[synced_key] = True

    yield

    # Write: session_state → URL
    data = None
    if st.session_state.get(synced_key):
        encoded = {}
        for url_param, (state_key, converter) in params.items():
            if (value := st.session_state.get(state_key)) is not None:
                encoded[url_param] = converter(value)
        if encoded:
            data = {"search": urlencode(encoded)}
    use_location(key=location_key, data=data)


use_location = component(
    "use_location",
    js="""
    export default function (component) {
    if (component.data !== null) {
        let url = window.location.pathname;
        const search = 'search' in component.data
                    ? component.data.search
                    : window.location.search.slice(1);
        const hash = 'hash' in component.data
                    ? component.data.hash
                    : window.location.hash.slice(1);
        if (search) url += '?' + search;
        if (hash) url += '#' + hash;
        if (url !== window.location.pathname
                    + window.location.search
                    + window.location.hash) {
        history.pushState({}, '', url);
        }
    }

    function updateState() {
        component.setStateValue('hash', window.location.hash.slice(1));
        component.setStateValue('search', window.location.search.slice(1));
    }

    updateState();
    window.addEventListener('popstate', updateState);
    return () => window.removeEventListener('popstate', updateState);
    }
"""
)
