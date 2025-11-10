import re
from datetime import date, datetime
from typing import Callable

from pyncm import SetCurrentSession, CreateNewSession
from pyncm.apis.login import *
from streamlit.delta_generator import DeltaGenerator
import streamlit as st

from utils import random_uppercase, fancy_title, emoji_number, eggs

LoginViaAnonymousAccount()

title = random_uppercase('nacman')
st.set_page_config(page_title=title, page_icon=":dvd:")
title = ":dvd: " + (eggs[title] if title in eggs else fancy_title(title))
main_title = st.title(title)
with st.sidebar:
    sidebar_title = st.title(title)
    st.json(status := GetCurrentLoginStatus())

if profile := status["profile"]:
    st.session_state["profile"] = profile
    create_time = datetime.fromtimestamp(profile["createTime"] / 1000)
    birthday = date.fromtimestamp(profile["birthday"] / 1000)
    days = emoji_number((datetime.now() - create_time).days)
    if date.today().replace(year=birthday.year) == birthday:
        st.balloons()
        title += " & :rainbow[Happy birthday!] :birthday:"
        main_title.title(title)
        sidebar_title.title(title)

    st.markdown('<div style="font-size: 1.2em;">\n' + f"""
Welcome to {title.replace("&", "and")}, {profile["nickname"]}!

Today is your Day {days} on Cloud Village.

Open the sidebar to see more options or use the buttons below.
</div>""", unsafe_allow_html=True)

    def apply(dg: DeltaGenerator, render: Callable):
        with dg:
            render()

    def navigate_to_search():
        if st.button("Search", key="search", use_container_width=True):
            st.switch_page("pages/search.py")

    _ = [apply(dg, func) for dg, func in zip(st.columns(4), [
        navigate_to_search,
        lambda: st.button("Logout", key="logout", use_container_width=True,
                          on_click=LoginLogout),
        lambda: st.button("Quit Session", key="quit", use_container_width=True,
                          on_click=lambda: SetCurrentSession(CreateNewSession()))
    ])]

    st.stop()

if "unikey" not in st.session_state:
    st.session_state["unikey"] = LoginQrcodeUnikey()["unikey"]

st.text("Welcome! please login via:")
cellphone, email, cookie = st.tabs(["Cellphone", "Email", "Cookie"])

with cellphone:
    phone = st.text_input("Cellphone Number")
    phone_valid = re.match(r"^1\d{10}$", phone)

    captcha, password = st.tabs(["Captcha", "Password"])
    with captcha:
        left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
        captcha = left.text_input("Captcha", key="captcha")
        right.button("Send Captcha", key="send_captcha", args=(phone,),
                     on_click=SetSendRegisterVerifcationCodeViaCellphone,
                     use_container_width=True, disabled=not phone_valid)
    password = password.text_input("Password", key="password", type="password")

    st.button("Login", key="login", use_container_width=True,
              disabled=not (phone_valid and captcha or password),
              on_click=LoginViaCellphone,
              kwargs=dict(phone=phone, password=password, captcha=captcha))

    st.divider()
    url = GetLoginQRCodeUrl(unikey := st.session_state["unikey"])
    left, right = st.columns([0.8, 0.2], vertical_alignment="center")
    left.markdown(
        f"Or you can login via QR Code, your Unikey is <> now.")
    right.button("Refresh Unikey", key="refresh", use_container_width=True,
                 on_click=lambda: [LoginRefreshToken(),
                                   st.session_state.pop("unikey")])
    left, right = st.columns(2)
    left.link_button("Scan the QR Code", use_container_width=True, url=url)
    right.button("And Check Here", key="check", use_container_width=True,
                 on_click=lambda: cellphone.write(LoginQrcodeCheck(unikey)))
    # FIXME: Code: 8821, 需要行为验证码验证

with email:
    email = st.text_input("Email Address", key="email")
    email_valid = re.match(r"^[\w.%+-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$", email)
    left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
    password = left.text_input("Password", key="password2", type="password")
    right.button("Login", key="login2", use_container_width=True,
                 disabled=not (email_valid and password),
                 on_click=LoginViaEmail, args=(email, password))
    # FIXME: Code: 8821, 需要行为验证码验证

with cookie:
    left, right = st.columns([0.8, 0.2], vertical_alignment="bottom")
    cookie = left.text_input("Cookie", key="cookie")
    right.button("Login", key="login3", use_container_width=True,
                 disabled=not cookie, on_click=LoginViaCookie, args=(cookie,))
