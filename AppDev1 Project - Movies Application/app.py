import base64
import csv
import datetime
import os
from flask import Flask, jsonify,  render_template, request, redirect, url_for, session
from jinja2 import Template
import sqlite3

app = Flask(__name__)

import jwt

# Define a secret key to sign the token
app.secret_key = 'my_secret_key'

# Define a function to generate a JWT token
def generate_token(user_id):
    payload = {
        'user_id': user_id
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')  
    return token


@app.route("/",methods=["GET","POST"])
def index():
    if request.method=="POST":
        username = request.form['username']
        password = request.form['password']
        dropdown_value = request.form.get('dropdown')
        sqliteConnection = sqlite3.connect('database.db')
        cursor = sqliteConnection.cursor()
        sqlite_select_Query = "select * from users_data;"
        cursor.execute(sqlite_select_Query)
        record = cursor.fetchall()
        for i in record:
            if i[1]==username and i[2]==password and dropdown_value=="user":
                session['user_id']=i[0]
                session['username']=i[1]
                return redirect(url_for('homepage'))
            elif i[1]==username and i[2]==password and i[3]==1 and dropdown_value=="admin":
                session['user_id']=i[0]
                session['username']=i[1]
                return redirect(url_for('ViewVenue'))
                
        return render_template("errorpage.html")
    else:
        return render_template("index.html")

@app.route("/viewshows",methods=["GET","POST"])
def homepage():
    if request.method=="GET":
        try:
            user_id=session.get('user_id')
            username=session.get('username')
            sqliteConnection = sqlite3.connect('database.db')
            cursor = sqliteConnection.cursor()
            venues_query = "select * from venues;"
            cursor.execute(venues_query)
            venues = cursor.fetchall()
            shows_query = "select * from shows;"
            cursor.execute(shows_query)
            shows = cursor.fetchall()
            venue_shows = {}
            for k in shows:
                if k[2] in venue_shows.keys():
                    venue_shows[k[2]]["shows"].append(k)
                else:
                    for j in venues:
                        if j[0]==k[2]:
                            venue_shows[k[2]]={}
                            venue_shows[k[2]]["venue"]=j
                            venue_shows[k[2]]["shows"]=[]
                            venue_shows[k[2]]["shows"].append(k)                 
            cursor.close()
        except sqlite3.Error as err:
            print("Error while connecting to sqlite", err)       
        return render_template("homepage.html",user_id=user_id,username=username,venuelist=venue_shows)

@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method=="GET":
        return render_template("singupPage.html")
    else:
        username = request.form['username']
        password = request.form['password']
        try:
            sqliteConnection = sqlite3.connect('database.db')
            cursor = sqliteConnection.cursor()
            sqlite_select_Query = "select * from users_data;"
            cursor.execute(sqlite_select_Query)
            record = cursor.fetchall()
            admincode = request.form['admincode']
            if admincode=="my_secret_code":
                for i in record:
                    if i[1]==username:
                        return render_template("singupPage.html",error="Username already exists !!")
                
                Insert_Query = "INSERT INTO users_data (username,password,admin) VALUES (?,?,?)"
                cursor.execute(Insert_Query,(username,password,1))
                sqliteConnection.commit()
            else:
                return render_template("singupPage.html")

        except sqlite3.Error as error:
            for i in record:
                if i[1]==username:
                    return render_template("singupPage.html",error="Username already exists !!")
        
            Insert_Query = "INSERT INTO users_data (username,password) VALUES (?,?)"
            cursor.execute(Insert_Query,(username,password,0))
            sqliteConnection.commit()
        
        cursor.close()
        
        return redirect(url_for('index'))


@app.route("/showDetails",methods=["GET","POST"])
def ViewShow():
    if request.method=="GET":
        show_id = request.args.get("show_id")
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        shows_query = "select * from shows;"
        cursor.execute(shows_query)
        shows = cursor.fetchall()
        venues_query = "select * from venues;"
        cursor.execute(venues_query)
        venues = cursor.fetchall()
        for i in shows:
            if int(show_id)==i[0]: 
                for j in venues:
                    if j[0]==i[2]:
                        return render_template("showdetails.html",showdata=i,venuedata=j,totalPrice="")          
        return render_template("errorpage.html")
    else:
        show_id = request.args.get("show_id")
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        shows_query = "select * from shows;"
        cursor.execute(shows_query)
        shows = cursor.fetchall()
        venues_query = "select * from venues;"
        cursor.execute(venues_query)
        venues = cursor.fetchall()
        for i in shows:
            if int(show_id)==i[0]: 
                for j in venues:
                    if j[0]==i[2]:
                        try:
                            tickets = int(request.form['tickets'])
                            if tickets>0 and tickets<i[8]:
                                return render_template("showdetails.html",showdata=i,venuedata=j,totalPrice=tickets*i[4],tickets=tickets)
                        except:
                            return render_template("showdetails.html",showdata=i,venuedata=j,totalPrice="")          
        return render_template("errorpage.html")
    
@app.route("/confirmBooking",methods=["GET","POST"])
def confirm():
    if request.method=="POST":
        show_id = request.form['show_id']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        shows_query = "select * from shows;"
        cursor.execute(shows_query)
        shows = cursor.fetchall()
        venues_query = "select * from venues;"
        cursor.execute(venues_query)
        venues = cursor.fetchall()
        for i in shows:
            if int(show_id)==i[0]:     
                for j in venues:
                    if j[0]==i[2]:
                        if i[8]-tickets<tickets:
                            
                        else:
                            try:   
                                tickets = int(request.form['confirmtickets']) 
                                confirm=request.form['confirm']
                                if confirm=="Click To Confirm Tickets!":
                                    user_id = session.get('user_id')                             
                                    cursor.execute('''UPDATE shows SET capacity = ? WHERE id = ?''', (i[8]-tickets, show_id))
                                    conn.commit()
                                    cursor.execute("INSERT INTO user_shows (user_id, show_id, tickets) VALUES (?, ?, ?)",(user_id,show_id,tickets))
                                    conn.commit()
                                    return redirect(url_for('ViewShow',show_id=show_id))
                            except Exception as e:
                                return redirect(url_for('ViewShow',show_id=show_id))
                            
        return render_template("errorpage.html")  
    
@app.route("/mybookings",methods=["GET","POST"])
def MyBookings():
    user_id=session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_shows_query = "select * from user_shows;"
    cursor.execute(user_shows_query)
    user_shows = cursor.fetchall()
    shows_query = "select * from shows;"
    cursor.execute(shows_query)
    shows = cursor.fetchall()
    this_user_shows_ids=[]
    this_user_shows=[]
    shows_tickets={}
    for i in user_shows:
        if i[1]==int(user_id):
            if i[2] not in shows_tickets:
                shows_tickets[i[2]]=i[3]
            else:
                shows_tickets[i[2]]+=i[3]
            this_user_shows_ids.append(int(i[2]))
        
    for i in shows:
        if i[0] in this_user_shows_ids:
            this_user_shows.append(i)
                    
    return render_template('bookingspage.html',this_user_shows=this_user_shows,shows_tickets=shows_tickets)
                
@app.route("/myprofile",methods=["GET","POST"])
def MyProfile():
    user_id=session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_shows_query = "select * from user_shows;"
    cursor.execute(user_shows_query)
    user_shows = cursor.fetchall()
    no_of_shows=0
    for i in user_shows:
        if i[1]==int(user_id):
            no_of_shows+=1
    return render_template("profilepage.html",no_of_shows=no_of_shows)

@app.route("/addvenue",methods=["GET","POST"])
def AddVenue():
    if request.method=="GET":
        return render_template('addvenue.html')
    else:
        user_id=session.get('user_id')
        name=request.form['name']
        place=request.form['place']
        capacity=request.form['capacity']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Venues (name, place, capacity, owner) VALUES (?, ?, ?, ?)",(name, place,capacity, user_id))
        conn.commit()
        session['user_id']=user_id
        return redirect(url_for('ViewVenue'))
    

@app.route("/viewvenues",methods=["GET","POST"])
def ViewVenue():
    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    venues_query = "select * from venues;"
    cursor.execute(venues_query)
    venues = cursor.fetchall()
    venue_shows = {}
    admin_venues=[]
    for j in venues:
        if j[4]==int(user_id):
            admin_venues.append(j)
    if admin_venues!=[]:
        shows_query = "select * from shows;"
        cursor.execute(shows_query)
        shows = cursor.fetchall()
        
        for i in admin_venues:
            venue_shows[i[0]]={}
            venue_shows[i[0]]["venue"]=i
            venue_shows[i[0]]["shows"]=[]
            for j in shows:
                    if int(i[0])==j[2]:
                        venue_shows[i[0]]["shows"].append(j)
    return render_template("adminpage.html",user_id=user_id,admin_venues=admin_venues,venue_shows=venue_shows)

@app.route("/editvenues",methods=["GET","POST"])
def EditVenue():
    if request.method=="GET":
        venue_id=request.args.get('venue_id')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("select * from venues where id=?",(venue_id,))
        row = cursor.fetchone()
        return render_template("editvenue.html",venue_id=venue_id,name=row[1],place=row[2],capacity=row[3])
    else:
        venue_id=request.form["venue_id"]
        user_id=session.get('user_id')
        name=request.form["name"]
        place=request.form["place"]
        capacity=request.form["capacity"]
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE Venues SET name = ?, place = ?, capacity = ? WHERE id=?",(name, place, capacity,venue_id))
        conn.commit()
        return redirect(url_for('ViewVenue'))
            
        
    
@app.route("/addshow",methods=["GET","POST"])
def AddShow():
    if request.method=="GET":
        venue_id=request.args.get('venue_id')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("select * from venues where id=?",(venue_id,))
        row = cursor.fetchone()
        return render_template("addshow.html",venue_id=venue_id,capacity=row[3])
    else:
        venue_id=request.form['venue_id']
        capacity=request.form['capacity']
        user_id=request.form['user_id']
        name=request.form['name']
        rating=request.form['rating']
        stime=request.form['stime']
        etime=request.form['etime']
        tags=request.form['tags']
        price=request.form['price']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO shows (name, venue_id, rating, price, start_time, end_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",(name,venue_id, rating, price, stime, etime, capacity))
        conn.commit()
        return redirect(url_for('ViewVenue'))

@app.route("/editshow",methods=["GET","POST"])
def EditShow():
    if request.method=="GET":
        show_id=request.args.get('show_id')
        user_id=session.get('user_id')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("select * from shows where id = ?",(show_id,))
        show = cursor.fetchone()
        try:
            cursor.execute("select owner from venues where id = ?",(int(show[2]),))
            owner = cursor.fetchone()
            if int(owner[0]) == int(user_id):
                row = cursor.fetchone()
                return render_template("editshow.html",show=show)
        except:
            return render_template("errorpage.html")  
    else:
        show_id=request.args.get('show_id') 
        user_id=session.get('user_id')
        name=request.form['name']
        rating=request.form['rating']
        stime=request.form['stime']
        etime=request.form['etime']
        tags=request.form['tags']
        price=request.form['price']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE shows SET name = ?, rating = ?, price = ?, start_time = ?, end_time = ? WHERE id = ?", (name, rating, price, stime, etime, show_id))
        conn.commit()
        return redirect(url_for('ViewVenue'))
        


@app.route("/deleteshow",methods=["GET","POST"])
def DeleteShow():
    if request.method=="GET":
        show_id=request.args.get('show_id')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shows where id=?",(show_id,))
        conn.commit()
        return redirect(url_for('ViewVenue'))

@app.route("/deletevenue",methods=["GET","POST"])
def DeleteVenue():
    if request.method=="GET":
        venue_id=request.args.get('venue_id')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("select id from shows where venue_id = ?",(venue_id,))
        shows_to_delete = cursor.fetchall()
        for id in shows_to_delete:
            cursor.execute("DELETE FROM shows where id=?",(id[0],))
        conn.commit()
        cursor.execute("DELETE FROM Venues where id=?",(venue_id,))
        conn.commit()
        return redirect(url_for('ViewVenue'))
    
@app.route("/summary")
def Summary():        
    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("select * from Venues where owner = ?",(user_id,))
    admin_venues = cursor.fetchall()
    
    admin_venues_id=[]
    for i in admin_venues:
        admin_venues_id.append(i[0])
        
    admin_shows = []
    admin_shows_id = []
    
    shows_visited={}
    venues_visited={}
    venue_shows = {}
    
    shows_query = "select * from shows;"
    cursor.execute(shows_query)
    shows = cursor.fetchall()
    
    for i in shows:
        if i[2] in admin_venues_id:
            admin_shows.append(i)
            admin_shows_id.append(i[0])
            
    shows_query = "select * from user_shows;"
    cursor.execute(shows_query)
    
    user_shows = cursor.fetchall()
    for i in user_shows:
        print(i[2])
        if i[2] in admin_shows_id:
            if i[2] not in shows_visited:
                shows_visited[i[2]]=i[3]
            else:                
                shows_visited[i[2]]+=i[3]
    
    for i in admin_venues:
        for j in admin_shows:
            if j[2]==i[0] and j[0] in shows_visited:
                if i[0] not in venues_visited:
                    venues_visited[i[0]]=shows_visited[j[0]]
                else:                
                    venues_visited[i[0]]+=shows_visited[j[0]]
    
               
    for i in admin_venues:
        venue_shows[i[0]]={}
        venue_shows[i[0]]["venue"]=i
        venue_shows[i[0]]["shows"]=[]
        for j in shows:
                if int(i[0])==j[2]:
                    venue_shows[i[0]]["shows"].append(j)
    return render_template("summary.html",user_id=user_id,admin_venues=admin_venues,venue_shows=venue_shows,venues_visited=venues_visited,shows_visited=shows_visited)

        
        
        
if __name__=="__main__":
    app.run(debug=True)
    