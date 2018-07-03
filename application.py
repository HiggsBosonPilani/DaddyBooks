from flask import Flask, render_template, redirect, url_for, request, flash, session, Response, stream_with_context 
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from camera import VideoCamera
import time
import pyzbar.pyzbar as pyzbar
from scrape import my_scrape

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///librarybooks.db'
app.config['SESSION_PERMANENT'] = False 
app.config['SESSION_TYPE'] = "filesystem"

Session(app)

db = SQLAlchemy(app)

book_details = {}

class books(db.Model):

   id = db.Column('book_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   author = db.Column(db.String(100))
   publisher = db.Column(db.String(100))
   ISBN = db.Column(db.Integer)
   room = db.Column(db.Integer)
   cupboard = db.Column(db.Integer)
   location = db.Column(db.String(100))
   binding = db.Column(db.String(100))

   def __init__(self,name,author,publisher,ISBN,room,cupboard,location,binding):
      self.name = name
      self.author = author
      self.publisher = publisher
      self.ISBN = ISBN
      self.room = room 
      self.cupboard = cupboard
      self.location = location
      self.binding = binding

@app.route('/')
def show_all():

   if not session.get('logged_in'):
      return render_template('login.html')

   else:   
      last_id = books.query.count()
      return render_template("show_all.html",books = books.query.all(),lastbook = last_id,book_details = book_details)

@app.route('/login',methods = ['POST'])
def login():

   if request.form.get('password') == 'admin' and request.form.get('username') == 'admin':
      session['logged_in'] = True

   else:
      flash('Wrong Password!') 
   return redirect(url_for('show_all'))  
   
@app.route('/logout')     
def logout():
   session['logged_in'] = False 
   return redirect(url_for('show_all'))       

@app.route('/new', methods = ['GET','POST'])
def new():
   global book_details
   if not session.get('logged_in'):
      return render_template('login.html')

   else:  
      if request.method == 'POST':
         if not request.form.get('name') or not request.form.get('author') or not request.form.get('publisher') or not request.form.get('ISBN') or not request.form.get('room') or not request.form.get('cupboard') or not request.form.get('location') or not request.form.get('binding'):
            flash('Please enter all the fields', 'error')
            book_details = {}
         else:
            book = books(request.form.get('name'),request.form.get('author'),request.form.get('publisher'),int(request.form.get('ISBN')),int(request.form.get('room')),int(request.form.get('cupboard')),request.form.get('location'),request.form.get('binding'))  
            db.session.add(book)
            db.session.commit()
            book_details = {}
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
      return render_template('new.html',book_details = book_details) 

@app.route('/delete', methods = ['GET','POST'])
def delete():
   if not session.get('logged_in'):
      return render_template('login.html')

   else:  
      if request.method == 'POST':
         book_dict = {}

         if request.form.get('name'):
            book_dict['name'] = request.form.get('name')

         if request.form.get('author'):
            book_dict['author'] = request.form.get('author') 

         if request.form.get('publisher'):
            book_dict['publisher'] = request.form.get('publisher')

         if request.form.get('ISBN'):
            book_dict['ISBN'] = request.form.get('ISBN')

         if request.form.get('binding'):
            book_dict['binding'] = request.form.get('binding')   



         book_list = books.query.filter_by(**book_dict).all()
         
         if not len(book_list) == 0:  
            for book in book_list:
               db.session.delete(book)
            db.session.commit()
            flash('Record was successfully deleted')
         else:
            flash('No such record found')   
         return redirect(url_for('show_all'))
      return render_template('delete.html')

@app.route('/find', methods=['GET','POST'])
def find():
   if not session.get('logged_in'):
      return render_template('login.html')

   else:  
      if request.method == 'POST':
         
         book_name = ""
         book_author = ""
         book_publisher = ""
         book_ISBN = ""
         book_binding = ""

         if request.form.get('name'):
            book_name = request.form.get('name')

         if request.form.get('author'):
            book_author = request.form.get('author') 

         if request.form.get('publisher'):
            book_publisher = request.form.get('publisher')

         if request.form.get('ISBN'):
            book_ISBN = request.form.get('ISBN')

         if request.form.get('binding'):
            book_binding = request.form.get('binding')   

         book_list = books.query.filter(books.name.like("%"+book_name+"%"),books.author.like("%"+book_author+"%"),books.publisher.like("%"+book_publisher+"%"),books.ISBN.like("%"+book_ISBN+"%"),books.binding.like("%"+book_binding+"%")).all()

         last_id = len(book_list)
         
         return render_template("show_all.html",books = book_list,lastbook = last_id)
      return render_template('find.html')   

def gen(camera):
   while True:
      global book_details
      frame = camera.get_frame()
      decodedObjects = pyzbar.decode(camera.raw_frame())

      if len(decodedObjects) > 0:
         decodedObject = decodedObjects.pop()
         base_url = "https://isbndb.com/search/books/"+str(decodedObject.data)
         book_details = my_scrape(base_url)
         print "FOUND BARCODE"
         del camera 
         break
         

      yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
      #time.sleep(0.25)   
   


count=0
@app.route('/video_feed')
def video_feed():
   global count
   return Response(stream_with_context(gen(VideoCamera())),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera',methods = ['GET','POST'])
def camera():

   return render_template("camera.html")    


if __name__ == '__main__':
   app.secret_key = os.urandom(12)
   db.create_all()
   app.run(debug = True)

