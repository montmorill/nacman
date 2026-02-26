from enum import StrEnum

import streamlit as st
from models import AudioQuality, Track


class Display(StrEnum):
    COVER = "Cover"
    ALBUM = "Album"
    DOWNLOAD = "Download"
    QUALITY = "Quality"
    LYRICS = "Lyrics"
    TRACK_ID = "Track ID"
    DETAILS = "Details"


def render_download_button(track: Track, quality: AudioQuality, **kwargs):
    detail = track.detail(quality)
    st.download_button(
        label="Download",
        key=f"download_{track.id}",
        data=detail["url"],
        file_name=f"{track.title}.{detail['type']}",
        **kwargs
    )


def render_lyrics(track: Track):
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
def render_track_item(track: Track, displays: list[Display], quality: AudioQuality):
    if Display.QUALITY in displays:
        quality = st.session_state.get(f"quality_{track.id}", quality)

    info, audio = st.columns([3, 2])

    with info.container(horizontal=True, vertical_alignment="center"):
        if Display.COVER in displays:
            st.image(track.album.pic_url, width=48)

        title = track.name
        if Display.ALBUM in displays:
            title = f"{track.album.name} - {title}"

        subtitle = " / ".join(artist.name for artist in track.artists)
        if Display.TRACK_ID in displays:
            subtitle = f"#{track.id} {subtitle}"

        st.html(f'''\
<div class="nac-truncate">
    <div class="nac-truncate">{title}</div>
    <div class="nac-subtitle">{subtitle}</div>
</div>''')

        if Display.DOWNLOAD in displays:
            render_download_button(track, quality)

        if Display.QUALITY in displays:
            st.selectbox(
                "Quality", track.qualities.keys(),
                key=f"quality_{track.id}",
                index=len(track.qualities.keys()) - 1,
                label_visibility="collapsed",
                width=120,
            )

    with audio.container(height="stretch", horizontal=True, vertical_alignment="center"):
        st.audio(track.detail(quality)["url"])

    if Display.LYRICS in displays:
        render_lyrics(track)

    if Display.DETAILS in displays:
        st.json(track.model_dump_json())


@st.fragment
def render_track_card(track: Track, displays: list[Display], quality: AudioQuality):
    if Display.QUALITY in displays:
        quality = st.session_state.get(f"quality_{track.id}", quality)

    with st.container(horizontal=True, horizontal_alignment="distribute"):
        caption = track.name

        if Display.ALBUM in displays:
            caption = f"{track.album.name} - {caption}"
        if Display.TRACK_ID in displays:
            caption = f"{caption} #{track.id}"

        if Display.COVER in displays:
            st.image(track.album.pic_url, width="stretch", caption=caption)
        else:
            st.text(caption)

        st.audio(track.detail(quality)["url"])

        if Display.QUALITY in displays:
            st.select_slider(
                "Quality", track.qualities.keys(),
                key=f"quality_{track.id}",
                value=track.highest_quality,
                label_visibility="collapsed"
            )

        if Display.DOWNLOAD in displays:
            render_download_button(track, quality, width="stretch")

    if Display.LYRICS in displays:
        render_lyrics(track)

    if Display.DETAILS in displays:
        st.json(track.model_dump_json())
