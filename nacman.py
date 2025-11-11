import re
from datetime import date, datetime

import streamlit as st
from pyncm import SetCurrentSession, CreateNewSession
from pyncm.apis.login import (
    GetCurrentLoginStatus,
    GetLoginQRCodeUrl,
    LoginLogout,
    LoginQrcodeCheck,
    LoginQrcodeUnikey,
    LoginRefreshToken,
    LoginViaAnonymousAccount,
    LoginViaCellphone,
    LoginViaCookie,
    LoginViaEmail,
    SetSendRegisterVerifcationCodeViaCellphone,
)

from utils import random_uppercase, fancy_title, emoji_number, eggs


LoginViaAnonymousAccount()

title = random_uppercase('nacman')

st.set_page_config(page_title=title, page_icon=":dvd:")

title = ":dvd: " + (eggs[title] if title in eggs else fancy_title(title))

main_title = st.title(title)

with st.sidebar:
    sidebar_title = st.title(title)
    st.json(status := GetCurrentLoginStatus())

if profile := status["profile"]:  # type: ignore
    st.session_state["profile"] = profile

    create_time = datetime.fromtimestamp(profile["createTime"] / 1000)
    birthday = date.fromtimestamp(profile["birthday"] / 1000)

    if date.today().replace(year=birthday.year) == birthday:
        title += " & :rainbow[Happy birthday!] :birthday:"
        main_title.title(title)
        sidebar_title.title(title)
        st.balloons()

    days_since_create = (datetime.now() - create_time).days

    st.markdown(f"""
        Welcome to {title.replace("&", "and")}, {profile["nickname"]}!

        Today is your Day {emoji_number(days_since_create)} on Cloud Village.

        Open the sidebar to see more options or use the buttons below.
    """)

    search, logout, quit = st.columns(3)

    with search:
        if st.button("Search", "search", width="stretch"):
            st.switch_page("pages/search.py")

    with logout:
        if st.button("Logout", "logout", width="stretch"):
            LoginLogout()

    with quit:
        if st.button("Quit Session", "quit", width="stretch"):
            SetCurrentSession(CreateNewSession())

    st.stop()

if "unikey" not in st.session_state:
    st.session_state["unikey"] = LoginQrcodeUnikey()["unikey"]  # type: ignore


st.text("Welcome! please login via:")
cellphone, email, cookie = st.tabs(["Cellphone", "Email", "Cookie"])

with cellphone:
    phone = st.text_input("Cellphone Number", key="phone")
    phone_valid = re.match(r"^1\d{10}$", phone)

    captcha, password = st.tabs(["Captcha", "Password"])
    with captcha:
        left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
        captcha = left.text_input("Captcha", key="captcha")
        if right.button("Send Captcha", "send_captcha",
                        disabled=not phone_valid, width="stretch"):
            SetSendRegisterVerifcationCodeViaCellphone(phone)
    with password:
        password = st.text_input("Password", key="password", type="password")

    if st.button("Login", "login", width="stretch",
                 disabled=not (phone_valid and captcha or password)):
        LoginViaCellphone(phone, password=password, captcha=captcha)

    st.divider()
    url = GetLoginQRCodeUrl(unikey := st.session_state["unikey"])

    left, right = st.columns([0.8, 0.2], vertical_alignment="center")
    left.markdown(f"""Or you can login via QR Code with key `{unikey}`.""")
    if right.button("Refresh Unikey", "refresh", width="stretch"):
        LoginRefreshToken()
        st.session_state.pop("unikey")

    left, right = st.columns(2)
    left.link_button("Scan the QR Code", url=url, width="stretch")
    if right.button("And Check Here", "check", width="stretch"):
        # FIXME: Code: 8821, 需要行为验证码验证
        st.write(LoginQrcodeCheck(unikey))

with email:
    email = st.text_input("Email Address", key="email")
    email_valid = re.match(r"^[\w.%+-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$", email)
    left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
    password = left.text_input("Password", key="password2", type="password")
    if right.button("Login", "login2", width="stretch",
                    disabled=not (email_valid and password)):
        # FIXME: Code: 8821, 需要行为验证码验证
        LoginViaEmail(email, password=password)

with cookie:
    left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
    cookie = left.text_input("Cookie", key="cookie")
    if right.button("Login", "login3", width="stretch", disabled=not cookie):
        LoginViaCookie(cookie=cookie)
