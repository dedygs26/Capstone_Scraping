from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests
import re 
import numpy as np
import seaborn as sns


#don't change this
matplotlib.use('Agg')
app = Flask(__name__) #do not change this

#insert the scrapping here
url_get = requests.get('https://www.imdb.com/search/title/?release_date=2020-01-01,2020-12-31')
soup = BeautifulSoup(url_get.content,"html.parser")

table = soup.find('div', class_='lister-item mode-advanced')
temp = [] #initiating a tuple
page = requests.get('https://www.imdb.com/search/title/?release_date=2020-01-01,2020-12-31&start=1&ref_=adv_nxt')
table = soup.find_all('div', class_='lister-item mode-advanced')
for ia in table:
        #title
        title = ia.find('h3',class_='lister-item-header').find('a',href=True).text
        #print(title)

        # year
        year = ia.find('span',class_='lister-item-year text-muted unbold').text
        #print(year)

        # imdb_rat
        imdb = ia.find('div',class_="inline-block ratings-imdb-rating").strong.text
        #print(imdb)

        if ia.find('div',class_="inline-block ratings-metascore") is None:
            metascores=ia.find('div',class_="inline-block ratings-metascore")
        else :
            metascores=ia.find('div',class_="inline-block ratings-metascore").span.text
        #print(metascores)

        # votes
        votes = ia.find('p',class_='sort-num_votes-visible').text.split()[1]
        #print(votes)
        
        # duration
        if ia.find('p', class_="text-muted").find(class_="runtime") is None:
           duration = ia.find('p', class_="text-muted").find(class_="runtime")
        else:
           duration = ia.find('p', class_="text-muted").find(class_="runtime").text
        #print(duration)
        
        # genre
        genre = ia.find('span',class_='genre').text.strip()
        #print(genre)

        temp.append((title,year,imdb,metascores,votes,duration,genre))

# function to extract director and stars
def extract_director_star(text):
    split_result = re.sub("Director:|Stars:||\n|\s{2}", '', text).split('|')
    if len(split_result) == 2 :# ada director
        director = split_result[0]
    else: # tidak ada director
        director = None 

    star = split_result[-1]
    return director, star 

# get soup object 
url = 'https://www.imdb.com/search/title/?release_date=2020-01-01,2020-12-31&start=1&ref_=adv_nxt'
url_get = requests.get(url)
soup = BeautifulSoup(url_get.content,"html.parser")

# get all director and stars elements
director_stars = soup.find_all('p', {'class':''})
directors, stars = list(zip(*[extract_director_star(element.text) for element in director_stars]))

import pandas as pd 
# transform list object into dataframe
df_star_director = pd.DataFrame([stars, directors], index=['star', 'director']).T

temp = temp[::-1]

#change into dataframe
df = pd.DataFrame(temp,columns=('title','year','imdb','meta','votes','duration','genre'))
df['title']=df['title'].drop_duplicates()
df.dropna(how='any')

datas =pd.concat([df,df_star_director],axis=1)

#insert data wrangling here
fix_datas = datas.dropna()
fix_datas['duration']= fix_datas['duration'].apply(str).str.replace("min","")
fix_datas['duration']= fix_datas['duration'].astype('int64')
fix_datas['rank_popularity']=range(1,len(fix_datas)+1)
fix_datas['imdb']=fix_datas['imdb'].astype('float64')
fix_datas['votes']=fix_datas['votes'].apply(str).str.replace(",","").astype('int64')
fix_datas['meta'] = fix_datas['meta'].fillna(0).astype('int64')
genre = fix_datas['genre'].str.split(",",3,expand=True)

#for assign each genre
fix_datas['genre_1']=genre[0]
fix_datas['genre_2']=genre[1]
fix_datas['genre_3']=genre[2]

# kondisi kolom
action = (fix_datas['genre_1']=="Action") | (fix_datas['genre_2']=="Action") | (fix_datas['genre_3']=="Action")
drama = (fix_datas['genre_1']=="Drama") | (fix_datas['genre_2']=="Drama") | (fix_datas['genre_3']=="Drama")
thriller = (fix_datas['genre_1']=="Thriller") | (fix_datas['genre_2']=="Thriller") | (fix_datas['genre_3']=="Thriller")

#membuat kolom baru berdasarkan kondisi
fix_datas['Action'] = np.where(action,'Yes','No')
fix_datas['Drama'] = np.where(drama,'Yes','No')
fix_datas['Thriller'] = np.where(thriller,'Yes','No')

fix_datas2 = fix_datas.groupby('title').sum()[["imdb"]].sort_values(by="imdb",ascending=False)

#end of data wranggling 

@app.route("/")
def index(): 
	
	card_data = fix_datas["imdb"].mean().round(2)

	# generate plot data 1
	ax = fix_datas2.sort_values(by="imdb",ascending=True).head(8).plot(kind="barh",xlabel="Film",ylabel="Value",figsize = (20,8)),
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result = str(figdata_png)[2:-1]

	# data2
	fig_dims = (8, 5)
	fig, ax = plt.subplots(figsize=fig_dims)
	m, b = np.polyfit(fix_datas['votes'],fix_datas['imdb'],1)
	sns.scatterplot(data=fix_datas, x='votes', y='imdb',s=80, ax=ax, color='green')
	plt.plot(fix_datas['votes'],m*fix_datas['votes']+b)
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result2 = str(figdata_png)[2:-1]

	# data3
	fig_dims = (8, 5)
	fig, ax = plt.subplots(figsize=fig_dims)
	m, b = np.polyfit(fix_datas['rank_popularity'],fix_datas['votes'],1)
	sns.scatterplot(data=fix_datas, x='rank_popularity', y='votes',s=80, ax=ax, color='green')
	plt.plot(fix_datas['rank_popularity'],m*fix_datas['rank_popularity']+b)
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result3 = str(figdata_png)[2:-1]

	fig_dims = (8, 5)
	fig, ax = plt.subplots(figsize=fig_dims)
	m, b = np.polyfit(fix_datas['rank_popularity'],fix_datas['imdb'],1)
	sns.scatterplot(data=fix_datas, x='rank_popularity', y='imdb',s=80, ax=ax, color='green')
	plt.plot(fix_datas['rank_popularity'],m*fix_datas['rank_popularity']+b)
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result4 = str(figdata_png)[2:-1]

	# render to html
	return render_template('index.html',
		card_data = card_data, 
		plot_result=plot_result,
		plot_result2=plot_result2,
		plot_result3=plot_result3,
		plot_result4=plot_result4
		)


if __name__ == "__main__": 
    app.run(debug=True)
