import urllib.request

import gender_guesser.detector as gender
import matplotlib
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import streamlit as st
import xmltodict
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.figure import Figure
from pandas import json_normalize
from streamlit_lottie import st_lottie
import string
import random
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import StringIO
from html.parser import HTMLParser


st.set_page_config(page_title="The Books of Adam", layout="wide")


def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# lottie_book = load_lottieurl("https://assets4.lottiefiles.com/temp/lf20_aKAfIn.json")
# st_lottie(lottie_book, speed=1, height=200, key="initial")

st.image('Images/banner.jpg',use_column_width='always')


matplotlib.use("agg")

_lock = RendererAgg.lock


sns.set_style("darkgrid")
st.title("The Books of Adam")

user_input = "https://www.goodreads.com/user/show/113122191-adam-martin"

user_id = "".join(filter(lambda i: i.isdigit(), user_input))
user_name = user_input.split(user_id, 1)[1].split("-", 1)[1].replace("-", " ")

st.header("Analyzing the Reading History of: **{}**".format(string.capwords(user_name)))

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

with st.spinner('Getting book data'):
    df_out = st.session_state['data']
    df = df_out.copy()
    st.session_state['data'] = df
    

u_books = len(df["book.id.#text"].unique())
u_authors = len(df["book.authors.author.id"].unique())
df['read_at_year'] = pd.to_datetime(df['date_added'],utc=True).dt.year
# df["read_at_year"] = [i[-4:] if i != None else i for i in df["read_at"]]
has_records = any(df["read_at_year"])

st.write("")
row3_space1, row3_1, row3_space2, row3_2, row3_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)


with row3_1, _lock:
    st.subheader("Books Added")
    if has_records:
        year_df = pd.DataFrame(df["read_at_year"].dropna().value_counts()).reset_index()
        year_df = year_df.sort_values(by="index")
        fig = Figure()
        ax = fig.subplots()
        sns.barplot(
            x=year_df["index"], y=year_df["read_at_year"], color="goldenrod", ax=ax
        )
        ax.set_xlabel("Year")
        ax.set_ylabel("Books Added")
        st.pyplot(fig)
    else:
        st.markdown("We do not have information to find out _when_ you read your books")

    st.markdown(
        "It looks like you've read a grand total of **{} books with {} authors,** with {} being your most read author! That's awesome. Here's what your reading habits look like since you've started using Goodreads.".format(
            u_books, u_authors, df["book.authors.author.name"].mode()[0]
        )
    )


with row3_2, _lock:
    st.subheader("Book Publication Date")
    fig = Figure()
    ax = fig.subplots()
    sns.histplot(
        pd.to_numeric(df["book.publication_year"], errors="coerce")
        .dropna()
        .astype(np.int64),
        kde_kws={"clip": (0.0, 2020)},
        ax=ax,
        kde=True,
    )
    ax.set_xlabel("Book Publication Year")
    ax.set_ylabel("Density")
    st.pyplot(fig)

    avg_book_year = str(int(np.mean(pd.to_numeric(df["book.publication_year"]))))
    row_young = df.sort_values(by="book.publication_year", ascending=False).head(1)
    youngest_book = row_young["book.title_without_series"].iloc[0]
    row_old = df.sort_values(by="book.publication_year").head(1)
    oldest_book = row_old["book.title_without_series"].iloc[0]

    st.markdown(
        "Looks like the average publication date is around **{}**, with your oldest book being **{}** and your youngest being **{}**.".format(
            avg_book_year, oldest_book, youngest_book
        )
    )

st.write("")
row4_space1, row4_1, row4_space2, row4_2, row4_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)

with row4_1, _lock:
    st.subheader("How Do You Rate Your Reads?")
    rating_df = pd.DataFrame(
        pd.to_numeric(
            df[df["rating"].isin(["1", "2", "3", "4", "5"])]["rating"]
        ).value_counts(normalize=True)
    ).reset_index()
    fig = Figure()
    ax = fig.subplots()
    sns.barplot(x=rating_df["index"], y=rating_df["rating"], color="goldenrod", ax=ax)
    ax.set_ylabel("Percentage")
    ax.set_xlabel("Your Book Ratings")
    st.pyplot(fig)

    df["rating_diff"] = pd.to_numeric(df["book.average_rating"]) - pd.to_numeric(
        df[df["rating"].isin(["1", "2", "3", "4", "5"])]["rating"]
    )

    difference = np.mean(df["rating_diff"].dropna())
    row_diff = df[abs(df["rating_diff"]) == abs(df["rating_diff"]).max()]
    title_diff = row_diff["book.title_without_series"].iloc[0]
    rating_diff = row_diff["rating"].iloc[0]
    pop_rating_diff = row_diff["book.average_rating"].iloc[0]

    if difference > 0:
        st.markdown(
            "It looks like on average you rate books **lower** than the average Goodreads user, **by about {} points**. You differed from the crowd most on the book {} where you rated the book {} stars while the general readership rated the book {}".format(
                abs(round(difference, 3)), title_diff, rating_diff, pop_rating_diff
            )
        )
    else:
        st.markdown(
            "It looks like on average you rate books **higher** than the average Goodreads user, **by about {} points**. You differed from the crowd most on the book {} where you rated the book {} stars while the general readership rated the book {}".format(
                abs(round(difference, 3)), title_diff, rating_diff, pop_rating_diff
            )
        )

with row4_2, _lock:
    st.subheader("How do Goodreads Users Rate Your Reads?")
    fig = Figure()
    ax = fig.subplots()
    sns.histplot(
        pd.to_numeric(df["book.average_rating"], errors="coerce").dropna(),
        kde_kws={"clip": (0.0, 5.0)},
        ax=ax,
        kde=True,
    )
    ax.set_xlabel("Goodreads Book Ratings")
    ax.set_ylabel("Density")
    st.pyplot(fig)
    st.markdown(
        "Here is the distribution of average rating by other Goodreads users for the books that you've read."
    )

st.write("")
row5_space1, row5_1, row5_space2, row5_2, row5_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)

with row5_1, _lock:
    # page breakdown
    st.subheader("Book Length Distribution")
    fig = Figure()
    ax = fig.subplots()
    sns.histplot(pd.to_numeric(df["book.num_pages"].dropna()), ax=ax, kde=True)
    ax.set_xlabel("Number of Pages")
    ax.set_ylabel("Density")
    st.pyplot(fig)

    book_len_avg = round(np.mean(pd.to_numeric(df["book.num_pages"].dropna())))
    book_len_max = pd.to_numeric(df["book.num_pages"]).max()
    row_long = df[pd.to_numeric(df["book.num_pages"]) == book_len_max]
    longest_book = row_long["book.title_without_series"].iloc[0]

    st.markdown(
        "Your average book length is **{} pages**, and your longest book read is **{} at {} pages!**.".format(
            book_len_avg, longest_book, int(book_len_max)
        )
    )


with row5_2, _lock:
    # length of time until completion
    st.subheader("How Quickly Do You Read?")
    if has_records:
        df["days_to_complete"] = (
            pd.to_datetime(df["read_at"]) - pd.to_datetime(df["started_at"])
        ).dt.days
        fig = Figure()
        ax = fig.subplots()
        sns.histplot(pd.to_numeric(df["days_to_complete"].dropna()), ax=ax, kde=True)
        ax.set_xlabel("Days")
        ax.set_ylabel("Density")
        st.pyplot(fig)
        days_to_complete = pd.to_numeric(df["days_to_complete"].dropna())
        time_len_avg = 0
        if len(days_to_complete):
            time_len_avg = round(np.mean(days_to_complete))
        st.markdown(
            "On average, it takes you **{} days** between you putting on Goodreads that you're reading a title, and you getting through it!".format(
                time_len_avg
            )
        )
    else:
        st.markdown(
            "We do not have information to find out _when_ you finished reading your books"
        )


st.write("")
row6_space1, row6_1, row6_space2, row6_2, row6_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)


with row6_1, _lock:
    st.subheader("Author Gender Breakdown")
    # gender algo
    d = gender.Detector()
    new = df["book.authors.author.name"].str.split(" ", n=1, expand=True)

    df["first_name"] = new[0]
    df["author_gender"] = df["first_name"].apply(d.get_gender)
    df.loc[df["author_gender"] == "mostly_male", "author_gender"] = "male"
    df.loc[df["author_gender"] == "mostly_female", "author_gender"] = "female"
    df.loc[df["author_gender"] == "andy", "author_gender"] = ""

    author_gender_df = pd.DataFrame(
        df["author_gender"].value_counts(normalize=True)
    ).reset_index()
    fig = Figure()
    ax = fig.subplots()
    sns.barplot(
        x=author_gender_df["index"],
        y=author_gender_df["author_gender"],
        color="goldenrod",
        ax=ax,
    )
    ax.set_ylabel("Percentage")
    ax.set_xlabel("Gender")
    st.pyplot(fig)


# with row6_2, _lock:
#     st.subheader("Gender Distribution Over Time")
    
    # authors = df['book.authors.author.name'].astype('category')
    
    # others = authors.value_counts().index[30:]
    # label = 'Other'
    
    # authors = authors.cat.add_categories([label])
    # authors = authors.replace(others, label)
    
    # authors = authors.to_frame()
    
    # authors.groupby('book.authors.author.name').size().plot(kind='pie')

    # if has_records:
    #     year_author_df = pd.DataFrame(
    #         df.groupby(["read_at_year"])["author_gender"].value_counts(normalize=True)
    #     )
    #     year_author_df.columns = ["Percentage"]
    #     year_author_df.reset_index(inplace=True)
    #     year_author_df = year_author_df[year_author_df["read_at_year"] != ""]
    #     fig = Figure()
    #     ax = fig.subplots()
    #     sns.lineplot(
    #         x=year_author_df["read_at_year"],
    #         y=year_author_df["Percentage"],
    #         hue=year_author_df["author_gender"],
    #         ax=ax,
    #     )
    #     ax.set_xlabel("Year")
    #     ax.set_ylabel("Percentage")
    #     st.pyplot(fig)
    # else:
    #     st.markdown("We do not have information to find out _when_ you read your books")

st.write("")

# Wordcloud
st.write('The most common words in your book descriptions')
desc = df['book.description'].dropna()
text = strip_tags(' '.join(desc))
wordcloud = WordCloud(background_color="white",width=1280,height=640).generate(text)
fig, ax = plt.subplots()
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()
st.pyplot(fig)

st.subheader('Total Stats')

c = st.columns(4)

with c[0]:
    st.metric('**Total Books Read**',len(df))
    
with c[1]:
    st.metric('**Unique Authors**',len(df['book.authors.author.name'].unique()))
    

st.subheader('SanderStats')

sanderbooks = df[df['book.authors.author.name'].str.contains('Sanderson')].copy()

c = st.columns(4)

# Favorite Sanderson Book
sanderbooks['rating'] = pd.to_numeric(sanderbooks['rating'])
sanderbooks = sanderbooks.sort_values('rating',ascending=False)
sander_top = sanderbooks.iloc[0]
sanderbooks = sanderbooks.sort_values('rating',ascending=True)
sander_bottom = sanderbooks.iloc[0]

# First added
sanderbooks['date_added'] = pd.to_datetime(sanderbooks['date_added'])
sanderbooks = sanderbooks.sort_values('date_added',ascending=True)
sander_first = sanderbooks.iloc[0]
sanderbooks = sanderbooks.sort_values('date_added',ascending=False)
sander_last = sanderbooks.iloc[0]

# Pages
sanderbooks['book.num_pages'] = pd.to_numeric(sanderbooks['book.num_pages'])
sanderbooks = sanderbooks.sort_values('book.num_pages',ascending=True)
sander_short = sanderbooks.iloc[0]
sanderbooks = sanderbooks.sort_values('book.num_pages',ascending=False)
sander_long = sanderbooks.iloc[0]

with c[0]:
    # Get total number of Sanderson books read
    sander_count = len(sanderbooks)
    st.metric('**Total Sanderson Books Read**',sander_count)
    
    st.markdown('**Your last Sanderson book**')
    st.write(sander_last['book.title'])


with c[1]:
    st.markdown('**Your highest rated Sanderson book**')
    st.write(sander_top['book.title'])
    
    st.markdown('**Your shortest Sanderson book**')
    st.write(sander_short['book.title'])

with c[2]:
    st.markdown('**Your lowest rated Sanderson book**')
    st.write(sander_bottom['book.title'])
    
    st.markdown('**Your longest Sanderson book**')
    st.write(sander_long['book.title'])
    
with c[3]:
    st.markdown('**Your first Sanderson book**')
    st.write(sander_first['book.title'])
# Ideas - show most obscure books and authors read, and most popular - Done
# Show series with unread books, or favorite authors with unread books - Done
# Word cloud on book descriptions - Done
# Your favorite and least favorite sanderson book, most recently read sanderson book, first added sanderson book, longest, shortest

st.subheader('Popularity')

# Most obscure books
df['book.ratings_count'] = pd.to_numeric(df['book.ratings_count'])
df_rating_sort = df.sort_values('book.ratings_count',ascending=False)
# df_rating_sort['book.title'].head(15)
st.write('Your most popular books (based on rating counts)')
st.table(df_rating_sort[['book.title','book.authors.author.name','book.ratings_count']].head(15))

st.subheader('Obscurity')

# Most obscure books
df['book.ratings_count'] = pd.to_numeric(df['book.ratings_count'])
df_rating_sort = df.sort_values('book.ratings_count')
# df_rating_sort['book.title'].head(15)
st.write('Your most obscure books (based on rating counts)')
st.table(df_rating_sort[['book.title','book.authors.author.name','book.ratings_count']].head(15))


