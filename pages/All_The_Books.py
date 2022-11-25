import streamlit as st
from st_clickable_images import clickable_images
import requests
import urllib.request
from pandas import json_normalize
import pandas as pd
import xmltodict


st.set_page_config(page_title="The Books of Adam", layout="wide")

user_input = "https://www.goodreads.com/user/show/113122191-adam-martin"

user_id = "".join(filter(lambda i: i.isdigit(), user_input))
user_name = user_input.split(user_id, 1)[1].split("-", 1)[1].replace("-", " ")

def get_user_data(
    user_id, key="ZRnySx6awjQuExO9tKEJXw", v="2", shelf="read", page=1, per_page="200"
):
    api_url_base = "https://www.goodreads.com/review/list/"
    final_url = (
        api_url_base
        + user_id
        + ".xml?key="
        + key
        + "&v="
        + v
        + "&shelf="
        + shelf
        + "&per_page="
        + per_page
        + "&page="
        + page
    )
    contents = urllib.request.urlopen(final_url).read()
    return contents

@st.cache
def get_book_data():

    df = pd.DataFrame()
    for i in range(5):
        print('Getting page ' + str(i+1))
        contents = get_user_data(user_id=user_id, v="2", shelf="read", page=str(i+1), per_page="200")
        contents = xmltodict.parse(contents)
        df_new = json_normalize(contents["GoodreadsResponse"]["reviews"]["review"])
        df = pd.concat([df,df_new],ignore_index=True)
    return df

if 'data' not in st.session_state:
    st.session_state['data'] = get_book_data()

df = st.session_state['data']

no_image = 'https://s.gr-assets.com/assets/nophoto/book/111x148-bcc042a9c91a29c1d680899eff700a03.png'

df = df[df["book.image_url"].str.contains(no_image)==False]

def show_images():
    clicked = clickable_images(
        df['book.image_url'].tolist(),
        titles=df['book.title_without_series'].tolist(),
        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
        img_style={"margin": "5px", "height": "200px"},
    )
    return clicked

st.title('Books You Have Read')

show_images()