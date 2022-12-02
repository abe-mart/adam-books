import streamlit as st
import urllib.request
from pandas import json_normalize
import pandas as pd
import xmltodict
import openlibrary
import random
from fuzzywuzzy import fuzz

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

# if 'data' not in st.session_state:
#     st.session_state['data'] = []
#     st.session_state['data'] = get_book_data()
    
st.image('Images/banner2.jpg',use_column_width='always')

st.title('The Forgotten')
st.write('Books you haven\'t rated from your top 20 authors.  (Or that have titles off by at least one letter :D)')
print('Incompletes')



# Get data and sort top 20 authors by rating multiplied by number of ratings
# df = st.session_state['data']
print('Get book data')
df = get_book_data()
df = df.copy()

df['rating'] = df['rating'].astype(int)

df_author_group = df.groupby('book.authors.author.id').mean()
df_author_group_count = df.groupby('book.authors.author.id').count()
df_author_group['rating'] = df_author_group['rating'] * df_author_group_count['id']
top_authors_id = df_author_group['rating'].nlargest(20).index.values

@st.cache
def get_incompletes(top_authors_id):
    # Loop over author ids
    author_names = []
    book_display = []
    for id in top_authors_id:
        print(id)
        # id = top_authors_id[0]
        
        # Get the name of the authors
        books_from_author = df[df['book.authors.author.id']==id]
        author_name = books_from_author['book.authors.author.name'].values[0]
        print(author_name)
        
        # Get list of books by that author
        api = openlibrary.BookSearch()
        res = api.get_by_author(author_name)
        df_author = pd.DataFrame(res._data['docs'])
        
        # Filter to only english versions
        df_author = df_author[df_author['language'].astype(str).str.contains('eng')]
        
        # Get books that author has written that have not been read
        no_match = []
        for title in df_author['title']:
            title = title.replace("'", "")
            title = title.replace('"', "")
            title = title.split(':')[0]
            title = title.split('(')[0]
            print(title)
            # matches = books_from_author.loc[books_from_author['book.title_without_series'].str.contains(title,case=False)]
            matches = []
            for read_title in books_from_author['book.title_without_series']:
                
                if fuzz.ratio(read_title,title) >= 50:
                    matches.append(read_title)
                else:
                    print(read_title)
            # matches = books_from_author.loc[fuzz.ratio(books_from_author['book.title_without_series'].str,title)>=90]
            if len(matches) == 0:
                no_match.append(title)
        print(no_match)
        
        author_names.append(author_name)
        book_display.append(no_match)
        
    return author_names, book_display

author_names, book_display = get_incompletes(top_authors_id)

for ind, author_name in enumerate(author_names):
        
    # Display results
    st.subheader(author_name)
    j = 0
    no_match = book_display[ind]
    c = st.columns(4)
    for title in no_match[:min(15,len(no_match))]:
        with c[j%3]:
            st.write(title)
            j = j + 1
