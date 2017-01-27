import urllib2
import re
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import mysql.connector


page = 'http://www.avclub.com/features/movie-review'

page_to_scrape = urllib2.urlopen(page)

soup = BeautifulSoup(page_to_scrape,"html.parser")

def find_title_and_grade(arg):
	page = urllib2.urlopen(arg)
	soup = BeautifulSoup(page,"html.parser")
	name = soup.find('h2',attrs={'class':'title'})
	title = name.text.strip()
	if(title=="Cameraperson"):
		return
	if(soup.find('a',attrs={'class':'author'})):
		writer = soup.find('a',attrs={'class':'author'})
		author = writer.text.strip()
	else:
		return
	gradebox = soup.find('div',attrs={'class':'meta movie-review short-meta'})
	found = gradebox.find('div',attrs={'class':'grade color-me film'})
	if not found:
		found = gradebox.find('div',attrs={'class':'grade color-me tv'})
		if not found:
			return
	letter_grade = found.text.strip()
	invalid_grade = "-"
	if(letter_grade == invalid_grade):
		return
	#add search for duplicate to script can be run again without adding the same movies
	if(gradebox.find('div',attrs={'class':'director'})):
		m_director = gradebox.find('div',attrs={'class':'director'})
		director = m_director.text.strip()
		director = director[10:]
		director = re.sub('\([^)]*\)','',director)
		directors = [x.strip() for x in director.split(', ')]
		directors = [str(x) for x in directors]
	else:
		directors = []

	if(gradebox.find('div',attrs={'class':'cast'})):
		m_cast = gradebox.find('div',attrs={'class':'cast'})
		cast = m_cast.text.strip()
		cast = cast[6:]
		cast = cast.replace('\n',"")
		cast = re.sub('\([^)]*\)','',cast)
		cast_members = [x.strip() for x in cast.split(', ')]
		cast_members = [str(x) for x in cast_members]
	else:
		cast_members = []

	if(gradebox.find('div',attrs={'class':'mpaa-rating'})):
		mpaa_rating = gradebox.find('div',attrs={'class':'mpaa-rating'})
		rating = mpaa_rating.text.strip()
		rating = rating[8:]
	else:
		rating = "N/A"

	print title
	print letter_grade
	#print ("Director(s): " + "[%s]" % ', '.join(map(str,directors)))
	#print("Cast: " + "[%s]" % ', '.join(map(str,cast_members)))
	print("Review written by " + author + "\n")
	moviesdb = mysql.connector.connect(user='root',password='cr3m3d3R4P3',database='movies')

	cursor = moviesdb.cursor(buffered=True)

	#cursor.execute("INSERT INTO movies VALUES (%s,%s,%s,%s,%s)",(movie_id,title,letter_grade,rating,author)
	add_movie = ("INSERT INTO movies " "(title,letter_grade,rating,author)" "VALUES (%s,%s,%s,%s)")
	new_movie = (title,letter_grade,rating,author)
	cursor.execute('''SELECT author FROM movies WHERE title = "%s"'''%title)
	duplicate = cursor.fetchone()
	print duplicate
	
	if not duplicate:
		cursor.execute(add_movie,new_movie)
		moviesdb.commit()
		
		add_movie_actor = ("INSERT INTO movies_actors " "(movie_id,actor_id)" "VALUES (%s,%s)")
		add_movie_director = ("INSERT INTO movies_directors " "(movie_id,director_id)" "VALUES (%s,%s)")

		for actor in cast_members:
			add_actor = ("INSERT INTO actors (name) VALUES (%s)")
			new_actor = actor.replace(",","")
			new_actor = new_actor.replace('"',"'")
			if(new_actor!="Documentary"):
				print "actor name: " + new_actor
				query = '''SELECT name FROM actors WHERE name = "%s"''' %new_actor
				cursor.execute(query)
				actor_name = cursor.fetchall()
				if not actor_name:
					cursor.execute(add_actor,(new_actor,))
					moviesdb.commit()
					print new_actor + " added."
				query1 = '''SELECT id FROM actors WHERE name = "%s"''' %new_actor
				cursor.execute(query1)
				result = cursor.fetchone()
				actor_id = result[0]
				print "title is" + title
				query2 = '''SELECT id FROM movies WHERE title = "%s"''' %title
				print "query is" + query2
				cursor.execute(query2)
				movie_result = cursor.fetchone()
				movie_id = movie_result[0]
				cursor.execute('''SELECT * FROM movies_actors WHERE movie_id = "%s" AND actor_id="%s"''',(movie_id,actor_id)) 

				movie_actor = cursor.fetchall()
				if not movie_actor:
					new_movie_actor = (movie_id,actor_id)
					cursor.execute(add_movie_actor,new_movie_actor)
					moviesdb.commit()
				

		for director in directors:
			add_director = ("INSERT INTO directors (name) VALUES (%s)")
			new_director = director.replace(",","")
			#new_director = new_director.replace("'","")
			print new_director
			query = '''SELECT name FROM directors WHERE name = "%s"'''%new_director
			cursor.execute(query)
			director_name = cursor.fetchall()
			if not director_name:
				cursor.execute(add_director,(new_director,))
				moviesdb.commit()
			query1 = '''SELECT id FROM directors WHERE name = "%s"''' %new_director
			cursor.execute(query1)
			result = cursor.fetchone()
			director_id = result[0]
			query2 = '''SELECT id FROM movies WHERE title = "%s"''' %title
			cursor.execute(query2)
			movie_result = cursor.fetchone()
			if not movie_result:
				if "Hillary" in title:
					temp_title = "Hillary's America"
					query3 = '''SELECT id FROM movies WHERE CONTAINS (title,"%s")''' %temp_title
					cursor.execute(query3)
					movie_result = cursor.fetchone()
					print "Result is " + movie_result
				else:
					query3 = '''SELECT id FROM movies WHERE CONTAINS (title,"%s")''' %title
					cursor.execute(query3)
					movie_result = cursor.fetchone()
			movie_id = movie_result[0]
			cursor.execute('''SELECT * FROM movies_directors WHERE movie_id = "%s" AND director_id="%s"''',(movie_id,director_id))
			movie_director = cursor.fetchall()
			if not movie_director:
				new_movie_director = (movie_id,director_id)
				cursor.execute(add_movie_director,new_movie_director)
				moviesdb.commit()
	else:
		cursor.execute('''SELECT author FROM movies WHERE title = "%s"'''%title)
		numrows = cursor.rowcount
		same_movie = cursor.fetchall()
		print same_movie
		duplicate = 0
		for x in range(0,numrows):
			if(same_movie[x]!=author):
				duplicate = 1
		if(duplicate==0):
			cursor.execute(add_movie,new_movie)
			moviesdb.commit()
			
			add_movie_actor = ("INSERT INTO movies_actors " "(movie_id,actor_id)" "VALUES (%s,%s)")
			add_movie_director = ("INSERT INTO movies_directors " "(movie_id,director_id)" "VALUES (%s,%s)")

			for actor in cast_members:
				add_actor = ("INSERT INTO actors (name) VALUES (%s)")
				new_actor = actor.replace(",","")
				new_actor = new_actor.replace('"',"'")
				if(new_actor!="Documentary"):
					print "actor name: " + new_actor
					query = '''SELECT name FROM actors WHERE name = "%s"''' %new_actor
					cursor.execute(query)
					actor_name = cursor.fetchall()
					if not actor_name:
						cursor.execute(add_actor,(new_actor,))
						moviesdb.commit()
						print new_actor + " added."
					query1 = '''SELECT id FROM actors WHERE name = "%s"''' %new_actor
					cursor.execute(query1)
					result = cursor.fetchone()
					actor_id = result[0]
					print "title is" + title
					query2 = '''SELECT id FROM movies WHERE title = "%s"''' %title
					print "query is" + query2
					cursor.execute(query2)
					movie_result = cursor.fetchone()
					movie_id = movie_result[0]
					cursor.execute('''SELECT * FROM movies_actors WHERE movie_id = "%s" AND actor_id="%s"''',(movie_id,actor_id)) 

					movie_actor = cursor.fetchall()
					if not movie_actor:
						new_movie_actor = (movie_id,actor_id)
						cursor.execute(add_movie_actor,new_movie_actor)
						moviesdb.commit()
					

			for director in directors:
				add_director = ("INSERT INTO directors (name) VALUES (%s)")
				new_director = director.replace(",","")
				#new_director = new_director.replace("'","")
				print new_director
				query = '''SELECT name FROM directors WHERE name = "%s"'''%new_director
				cursor.execute(query)
				director_name = cursor.fetchall()
				if not director_name:
					cursor.execute(add_director,(new_director,))
					moviesdb.commit()
				query1 = '''SELECT id FROM directors WHERE name = "%s"''' %new_director
				cursor.execute(query1)
				result = cursor.fetchone()
				director_id = result[0]
				query2 = '''SELECT id FROM movies WHERE title = "%s"''' %title
				cursor.execute(query2)
				movie_result = cursor.fetchone()
				if not movie_result:
					if "Hillary" in title:
						temp_title = "Hillary's America"
						query3 = '''SELECT id FROM movies WHERE CONTAINS (title,"%s")''' %temp_title
						cursor.execute(query3)
						movie_result = cursor.fetchone()
						print "Result is " + movie_result
					else:
						query3 = '''SELECT id FROM movies WHERE CONTAINS (title,"%s")''' %title
						cursor.execute(query3)
						movie_result = cursor.fetchone()
				movie_id = movie_result[0]
				cursor.execute('''SELECT * FROM movies_directors WHERE movie_id = "%s" AND actor_id="%s"''',(movie_id,director_id))
				movie_director = cursor.fetchall()
				if not movie_director:
					new_movie_director = (movie_id,director_id)
					cursor.execute(add_movie_director,new_movie_director)
					moviesdb.commit()
		else:
			return

	

def go_thru_page(soup):

	articlebox = soup.find('section',attrs={'class':'article-list'})

	if not articlebox:
		print("Articlebox failed.")
		return
	for tag in articlebox.find_all('a',href=True):
		if re.findall('/review/',tag['href']):
			if(not tag.has_attr('class')):
				link = 'http://www.avclub.com' + tag['href']
				if(link != 'http://www.avclub.com/review/spoiler-space-martyrs-231035' and link !="http://www.avclub.com/review/holy-rollers-41368"):
					find_title_and_grade(link)
	if(soup.find('a',attrs={'class':'next alt'})):
		tag2 = soup.find('a',attrs={'class':'next alt'})
		new_page = urllib2.urlopen('http://www.avclub.com' + tag2['href'])
		soup = BeautifulSoup(new_page)
		go_thru_page(soup)

go_thru_page(soup)
	
cursor.close()
moviesdb.close()
