import re
from datetime import date, datetime

import streamlit as st
from pyncm.apis.login import (GetCurrentLoginStatus, GetLoginQRCodeUrl,
                              LoginLogout, LoginQrcodeCheck, LoginQrcodeUnikey,
                              LoginRefreshToken, LoginViaAnonymousAccount,
                              LoginViaCellphone, LoginViaCookie, LoginViaEmail,
                              SetSendRegisterVerifcationCodeViaCellphone)

from utils import EGGS, emoji_number, fancy_title, random_uppercase

title = random_uppercase('nacman')

st.set_page_config(
    page_title=title,
    page_icon=":dvd:",
    layout="centered"
)

title = ":dvd: " + (EGGS[title] if title in EGGS else fancy_title(title))

main_title = st.title(title)

LoginViaAnonymousAccount()

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

        Open the sidebar to see more options.
    """)

    st.button("Logout", key="logout", on_click=LoginLogout)  # type: ignore

    st.stop()

st.text("Welcome! please login via:")
phone_tab, email_tab, cookie_tab = st.tabs(["Cellphone", "Email", "Cookie"])

with phone_tab:
    phone = st.text_input("Cellphone Number", key="phone")
    phone_valid = re.match(r"^1\d{10}$", phone)

    sms_code_tab, password_tab = st.tabs(
        ["SMS Verification Code", "Password"])

    with sms_code_tab.container(horizontal=True, vertical_alignment="bottom"):
        sms_code = st.text_input("SMS Verification Code", key="sms_code")
        st.button(
            "Send SMS Verification Code", key="send_sms_code",
            disabled=not phone_valid,
            on_click=SetSendRegisterVerifcationCodeViaCellphone,  # type: ignore
            args=(phone,)
        )

    with password_tab:
        password = st.text_input(
            "Password", key="phone_password", type="password")

    st.button(
        "Login", key="phone_login", width="stretch",
        disabled=not (phone_valid and (sms_code or password)),
        on_click=LoginViaCellphone,  # type: ignore
        kwargs=dict(phone=phone, password=password, captcha=sms_code)
    )

    st.divider()

    if "unikey" not in st.session_state:
        unikey = LoginQrcodeUnikey()["unikey"]  # type: ignore
        st.session_state["unikey"] = unikey

    url = GetLoginQRCodeUrl(unikey := st.session_state["unikey"])

    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f"Or you can login via QR Code with key: `{unikey}`")
        st.button(
            "Refresh Unikey", key="refresh_unikey",
            on_click=lambda: [  # type: ignore
                st.session_state.pop("unikey"),
                LoginRefreshToken()
            ]
        )

    with st.container(horizontal=True, vertical_alignment="center"):
        st.link_button("Scan the QR Code", url=url, width="stretch")
        # FIXME: Code: 8821, 需要行为验证码验证
        st.button(
            "And Check Here", key="check_qrcode", width="stretch",
            on_click=lambda: st.write(LoginQrcodeCheck(unikey))
        )


with email_tab:
    email = st.text_input("Email Address", key="email")
    email_valid = re.match(r"^[\w.%+-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$", email)

    with st.container(horizontal=True, vertical_alignment="bottom"):
        password = st.text_input(
            "Password", key="email_password", type="password")
        # FIXME: Code: 8821, 需要行为验证码验证
        st.button(
            "Login", key="email_login",
            disabled=not (email_valid and password),
            on_click=LoginViaEmail,  # type: ignore
            kwargs=dict(email=email, password=password)
        )


with cookie_tab:
    with st.container(horizontal=True, vertical_alignment="bottom"):
        cookie = st.text_input("Cookie (MUSIC_U)", key="cookie")
        st.button(
            "Login", key="cookie_login",
            disabled=not cookie,
            on_click=LoginViaCookie,  # type: ignore
            args=(cookie,)
        )
