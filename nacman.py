import random
import re
from datetime import date

from pyncm.apis.login import *
import streamlit as st

LoginViaAnonymousAccount()

title = ''.join(random.choice([char.upper(), char]) for char in 'nacman')

st.set_page_config(page_title=title, page_icon=':dvd:')

title = ':dvd: ' + {
    'NaCMan': ':rainbow[NaCMan] :dvd:',
    'nAcmAN': ':rainbow[nAcmAN] :dvd:',
    'nACMan': 'n:blue[A]:yellow[C]:red[M]an :balloon:',
    'NacmAN': 'N:blue[a]:yellow[c]:red[m]AN :balloon:',
}.get(title, ''.join(
    f':{random.choice(['orange', 'red', 'blue', 'green'])}[{char}]'
    if char.isupper() else char for char in title
))


main_title = st.title(title)

with st.sidebar:
    sidebar_title = st.title(title)
    st.json(status := GetCurrentLoginStatus())

if profile := status['profile']:
    st.session_state['profile'] = profile
    birthday = date.fromtimestamp(profile['birthday'] / 1000)
    if date.today().replace(year=birthday.year) == birthday:
        st.balloons()
        title += ' & :rainbow[Happy birthday!] :birthday:'
        main_title.title(title)
        sidebar_title.title(title)
    st.markdown(f'Welcome to {title.replace("&", "and")}, {profile['nickname']}!')
    st.button('Logout', on_click=LoginLogout)
    st.stop()

# if 'unikey' not in st.session_state:
#     st.session_state['unikey'] = LoginQrcodeUnikey()['unikey']
# st.write(unikey := st.session_state['unikey'])

st.text("Welcome! please login via:")
cellphone, email = st.tabs(['Cellphone', 'Email'])

with cellphone:
    phone = st.text_input('Cellphone Number')
    phone_valid = re.match(r'^1\d{10}$', phone)

    with (tabs := st.tabs(['Captcha', 'Password']))[0]:
        left, right = st.columns([0.8, 0.2], vertical_alignment='bottom')
        captcha = left.text_input('Captcha', key='captcha')
        send_captcha_button = right.button(
            'Send Captcha', disabled=not phone_valid, use_container_width=True,
            on_click=SetSendRegisterVerifcationCodeViaCellphone, args=(phone,)
        )
    password = tabs[1].text_input('Password', key='password', type='password')
    st.button(
        'Login', disabled=not (phone_valid and captcha or password),
        on_click=LoginViaCellphone, kwargs=dict(
            phone=phone,
            password=password,
            captcha=captcha
        ), use_container_width=True)

    # st.divider()
    # left, right = st.columns([0.57, 0.43], vertical_alignment='center')
    # left.html(f'<div style="text-align: end;">Or scan the <a href="{
    #     GetLoginQRCodeUrl(unikey)
    # }">QR Code</a> and</div>')
    # right.button('Check', on_click=lambda: cellphone.write(LoginQrcodeCheck(unikey)))

with email:
    email = st.text_input('Email Address', key='email')
    email_valid = re.match(r'^[\w.%+-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$', email)
    left, right = st.columns([0.8, 0.2], vertical_alignment='bottom')
    password = left.text_input('Password', key='password2')
    login_button = right.button(
        'Login', key='login2', disabled=not (email_valid and password),
        use_container_width=True, on_click=LoginViaEmail, args=(email,)
    )
