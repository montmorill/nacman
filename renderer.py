from contextlib import contextmanager
from enum import StrEnum
from typing import Any, Callable, TypedDict
from urllib.parse import parse_qs, urlencode

from pydantic import BaseModel, Field
import streamlit as st
from streamlit.components.v2 import component

from models import (Album, AudioDetail, AudioQuality, BaseAlbum, BaseTrack,
                    Comment)


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
        st.error("No audio available due to either network or copyright issues.")
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
            caption = f"[{album.name}](/album?id={album.id}) - {caption}"
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


def render_comment(comment: Comment, hot=False,
                   many_emojis=False, zero_counts=False):
    st.image(comment.user.avatar_url, width=36)
    with st.container(gap=None):
        emoji = "🔥" if hot else "❤️"
        st.markdown(f"""
        **{comment.user.nickname}**
        {comment.time_str}
        {
            emoji * comment.liked_count
            if many_emojis else
            f"{emoji}{comment.liked_count}"
            if zero_counts or comment.liked_count else ""
        }
        """)
        st.text(comment.content)


class AlbumCommentStore(TypedDict):
    hot_comments: list[Comment]
    comments: list[Comment]
    page: int
    more: bool


@st.fragment
def render_album_comments(album: Album, **kwargs):
    store_key = f"comments_{album.info.id}"
    sentinel_key = f"comments_sentinel_{album.info.id}"

    # Initialize on first run
    if store_key not in st.session_state:
        first_page = album.comments(0)
        hot = list(first_page.hot_comments)
        more_hot, page = first_page.more_hot, 0
        while more_hot:
            page += 1
            data = album.comments(page)
            hot.extend(data.hot_comments)
            more_hot = data.more_hot
        st.session_state[store_key] = AlbumCommentStore(
            hot_comments=hot,
            comments=list(first_page.comments),
            page=0,
            more=first_page.more,
        )

    # Fetch next page when sentinel fires
    store: AlbumCommentStore = st.session_state[store_key]
    trigger = st.session_state.get(sentinel_key)
    if trigger and trigger.get("visible") and store["more"]:
        next_page = store["page"] + 1
        data = album.comments(next_page)
        store["comments"].extend(data.comments)
        store["page"] = next_page
        store["more"] = data.more

    # Hot comments
    for comment in store["hot_comments"]:
        with st.container(horizontal=True):
            render_comment(comment, hot=True, **kwargs)
    if store["hot_comments"]:
        st.divider()

    # Regular comments
    for comment in store["comments"]:
        with st.container(horizontal=True):
            render_comment(comment, **kwargs)

    if store["more"]:
        viewport_sentinel(key=sentinel_key)
        st.info("Loading more comments...", icon="⏳")
    else:
        st.divider()
        st.text("No more comments.", width="stretch", text_alignment="center")


class Location(BaseModel):
    search: dict[str, str] = Field(default_factory=dict)
    hash: str = ""


@contextmanager
def location(key: str):
    if key in st.session_state:
        yield (loc := Location.model_validate(st.session_state[key]))
        use_location(key=key, data=loc.model_dump())
    else:
        yield Location.model_validate(use_location())


use_location = component(
    "use_location",
    js="""//js
    export default function (component) {
    if (component.data !== null) {
        let url = window.location.pathname;
        const search = 'search' in component.data
                    ? new URLSearchParams(component.data.search).toString()
                    : window.location.search.slice(1);
        const hash = 'hash' in component.data
                    ? component.data.hash
                    : window.location.hash.slice(1);
        if (search) url += '?' + search.toString();
        if (hash) url += '#' + hash.toString();
        if (search !== window.location.search
            || hash !== window.location.hash) {
            history.pushState({}, '', url);
        }
    }

    function updateState() {
        component.setStateValue('hash', window.location.hash.slice(1));
        component.setStateValue('search', Object.fromEntries(new URLSearchParams(window.location.search)));
    }

    updateState();
    window.addEventListener('popstate', updateState);
    return () => window.removeEventListener('popstate', updateState);
    }
"""
)

viewport_sentinel = component(
    "viewport_sentinel",
    js="""//js
    export default function (component) {
        const rootMargin = component.data?.rootMargin || '0px';
        const sentinel = document.createElement('div');
        sentinel.style.height = '1px';
        component.parentElement.appendChild(sentinel);
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                component.setTriggerValue('visible', true);
            }
        }, { rootMargin });
        observer.observe(sentinel);
        return () => { observer.disconnect(); sentinel.remove(); };
    }
    """
)
