
from flask import Blueprint, request, render_template, flash, redirect, url_for, Response, make_response, g, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired
from api.models import db, users, user_data, keys
from api.core import create_response, serialize_list, logger
from sqlalchemy import inspect
from flask_googlemaps import GoogleMaps
from datetime import date, datetime
from math import log, pow
from statistics import stdev
from wtforms.fields.html5 import DateField
from datetime import datetime
import os
import bcrypt
import sys
import smtplib, email, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random, string
import geopy.distance

main = Blueprint("main", __name__)  # initialize blueprint

# Below is the function used to create the statistical analysis
# More info on the statistical analysis can be found at:
# https://producesafetyalliance.cornell.edu/sites/producesafetyalliance.cornell.edu/files/shared/documents/2017%20GM%20STV%20Worksheet%20v1.0.pdf
def computeStats(stats):
  data = []
  logged_total = 0.0
  GM = 0.0
  STV = 0.0
  index = 0
  for index in range(20):
    logged_total += log(float(stats[index]['datapoint']), 10)
    data.append(float(stats[index]['datapoint']))
  GM = logged_total / 20
  STV = log(GM + (1.282 * stdev(data)), 10)
  STV = 10**STV
  GM = pow(10,GM)
  return GM, STV

# Below is various forms used to get data from the users in through html
class NewDataForm(FlaskForm):
    date = DateField('Date Sampled', format='%Y-%m-%d')
    location = StringField('Location', render_kw={"placeholder": "Smith Rd, BLK 20"})
    xgeo = StringField('GPS (X - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "46.691752"})
    ygeo = StringField('GPS (Y - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "-120.581846"})
    data = StringField('Data', validators=[DataRequired()], render_kw={"placeholder": "100.0"})
    unit = SelectField(u'Unit Type', choices=[('MPN', 'MPN'), ('CFU', 'CFU')])
    comments = StringField('Comments', render_kw={"placeholder": "&lt; / Rained the day before / etc."})
    submit = SubmitField('submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Reset')

class AddForm(FlaskForm):
    email = StringField('Email of new user', validators=[DataRequired()])
    submit = SubmitField('Send Key')


class NewUser(FlaskForm):
    username = StringField('Username (This will be public)', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    irdistrict = StringField('Irrigation District', validators=[DataRequired()])
    defaultloclat = StringField('GPS (X - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "46.691752"})
    defaultloclong = StringField('GPS (Y - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "-120.581846"})
    password = PasswordField('Password', validators=[DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired()])
    key = StringField('Access Key', validators=[DataRequired()])
    submit = SubmitField('Create')

class ChangePassword(FlaskForm):
    password = PasswordField('Password (The password sent to your account email)', validators=[DataRequired()])
    newpassword = PasswordField('New Password', validators=[DataRequired()])
    confirmpassword = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change')

class ChangeLocation(FlaskForm):
    xgeo = StringField('GPS (X - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "46.691752"})
    ygeo = StringField('GPS (Y - Coordinate)', validators=[DataRequired()], render_kw={"placeholder": "-120.581846"})
    submit = SubmitField('Change')

class RadiusForm(FlaskForm):
    radius = StringField('Distance from your location to select points (miles)', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewTestUser(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Create')

class Changelocation(FlaskForm):
    defaultloclat = StringField('GPS (X - coordinate)', validators=[DataRequired()])
    defaultloclong = StringField('GPS (Y - coordinate)', validators=[DataRequired()])
    submit = SubmitField('Change Location')

# Function to convert to our desired date format
def ymd(fmt):
    def trans(date_str):
        return datetime.strptime(date_str, fmt)
    return trans

# Temporary class to store user information in routes
class TempUser():
    name = "bob"
    userName = "JimBob"
    eMail = "JimBob@jimbo.mail"
    uid = 0
    username = "username"
    email = "email"

# The main page, that is basically home/user profile
@main.route("/index")
def index():
    # The following two lines esnures the user is logged in
    # They are in most routes
    if not session.get('username'):
        return redirect('/login')

    curr_user = TempUser()
    # set tuser.userName to current username
    tuser = TempUser()
    logger.info("User sign in page being accessed")
    ird = ""
    _users = users.query.all()

    # Next we get the user data from the database
    for user in _users:
      if user.username == session['username']:
        if user.isadmin == 1:
            return redirect('/admin')
        curr_user = user
        curr_user.userName = user.username
        curr_user.username = user.username
        curr_user.name = user.name
        ird = user.irdistrict
 
   #curr user now holds info on the current user
    tuser.userName = curr_user.username
    tuser.eMail = curr_user.email
    tuser.name = curr_user.name
    tuser.uid = curr_user.id

    #Need to display the current data points for this user
    #Gets the datapoints for the curr user and places them into a new list
    datapoints = user_data.query.all()
    datapoints.sort(key=lambda x: tuple(map(int, x.date.split('-'))), reverse=True)
    user_points = []
    for point in datapoints:
      if point.user_id == tuser.uid:
        user_points.append(point)

    #user_points now holds this users data points
    data2 = {}
    index = 0

    #Set data up for the html
    for point in user_points:
      data2[index] = {}
      data2[index]['dataid'] = point.id
      data2[index]['datapoint'] = point.datapoint
      data2[index]['dataunit'] = point.dataunit
      data2[index]['location'] = point.location
      data2[index]['date'] = str(point.date)
      data2[index]['comments'] = point.comments
      data2[index]['xgeo'] = point.xgeo
      data2[index]['ygeo'] = point.ygeo
      index += 1

    #Necessary info is now available, pass to template with correct data
    return render_template('userProfile.html', title='Profile', tuser=tuser, data = data2, len = len(data2), ird=ird)

# Route for inserting a new point
@main.route("/newpoint", methods=["GET", "POST"])
def newpoint():
    if not session.get('username'):
        return redirect('/login')

    #Finding the current user to attach to the data point
    curr_user = TempUser()
    tuser = TempUser()
    # This errors list willl hold error codes for when a user inputs invalid data
    errors = []
    #Need to display information for the current user
    #Accessing the current user object
    _users = users.query.all()
    for user in _users:
      if(user.username == session['username']):
        curr_user = user

    #curr user now holds info on the current user
    tuser.userName = curr_user.username
    tuser.eMail = curr_user.email
    tuser.name = curr_user.name

    form = NewDataForm()

    # Error checking the entered user data
    if form.validate_on_submit():
        try:
            float(form.data.data)
        except ValueError:
            errors.append(1)
        try: 
            float(form.xgeo.data)
        except ValueError:
            errors.append(2)
        try:
            float(form.ygeo.data)
        except ValueError:
            errors.append(3)
        if not form.date.data:
            errors.append(4)
        if not errors:
            if float(form.ygeo.data) > 180 or float(form.ygeo.data) < -180:
                errors.append(5)
            if float(form.xgeo.data) > 90 or float(form.xgeo.data) < -90:
                errors.append(6)

       #Adding data point to the db
        if not errors:
           new_datapoint = user_data(datapoint=form.data.data,dataunit=form.unit.data, location=form.location.data,xgeo=form.xgeo.data,ygeo=form.ygeo.data,date=form.date.data,comments=form.comments.data,user_id=curr_user.id)
           db.session.add_all([new_datapoint])
           db.session.commit()
           return redirect('/index')

    return render_template('newData.html', title='Profile', tuser=tuser, form=form, errors=errors)

# Profile page for admin and master accounts. 
# The min difference in this page from the normal index route is admins can delete user accounts
@main.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get('username'):
        return redirect('/login')

    _users = users.query.all()
    data2 = {}
    index = 0
    curr_user = TempUser()
    ird = ""
    datapoints = user_data.query.all()
    datapoints.sort(key=lambda x: tuple(map(int, x.date.split('-'))), reverse=True)
    master = False
    for user in _users:
      if(user.username == session['username']):
        curr_user = user
        curr_user.userName = user.username
        curr_user.username = user.username
        curr_user.name = user.name
        ird = user.irdistrict
        if user.isadmin == 0:
            return redirect('/index')
        if user.ismaster == 1:
            master = True

    # grab all users to allow deletion
    # admins cant see other admins and no one can delete the system master account
    # system master account can delete admins
    for u in _users:
        if u.ismaster != 1:
            if u.isadmin == 0 and not master:
                data2[index] = {}
                data2[index]['username'] = u.username
                data2[index]['name'] = u.name
                data2[index]['email'] = u.email
                data2[index]['irdistrict'] = u.irdistrict
                index += 1
            elif u.isadmin == 1 and master:
                data2[index] = {}
                data2[index]['username'] = u.username
                data2[index]['name'] = u.name
                data2[index]['email'] = u.email
                data2[index]['irdistrict'] = u.irdistrict
                index += 1

    tuser = TempUser()

    #Need to display information for the current user
    #Accessing the current user object
    #curr user now holds info on the current user
    tuser.userName = curr_user.username
    tuser.eMail = curr_user.email
    tuser.name = curr_user.name
    tuser.uid = curr_user.id
    if request.method == 'POST':

        # Parse through data points and delete all points that are linked to an acoount marked for deletion
        # then delete the accounts marked for deletion
        delete_list = []
        delete_list = request.form.getlist('delete')
        for x in range(len(delete_list)):
            for user in _users:
                if (user.username == str(delete_list[x])):
                        for point in datapoints:
                            if (str(user.id) == str(point.user_id)):
                                db.session.delete(point)
                                db.session.commit
                        db.session.delete(user)
                        db.session.commit()
        return redirect('/admin')
        
    return render_template('adminProfile.html', title='Admin Profile Page', tuser=tuser, data = data2, len = len(data2), ird=ird)


@main.route('/data', methods=['GET', 'POST'])
def data():
    if not session.get('username'):
        return redirect('/login')

    curr_user = TempUser()
    #Need to display the current data points for this user
    #Gets the datapoints for the curr user and places them into a new list
    datapoints = user_data.query.all()
    datapoints.sort(key=lambda x: tuple(map(int, x.date.split('-'))), reverse=True)
    errors = []
    #user_points now holds this users data points
    data2 = {}
    index = 0
    form = RadiusForm()
    GM = 0.0
    STV = 0.0
    _users = users.query.all()

    #Set data up for the html
    for point in datapoints:
      data2[index] = {}
      data2[index]['dataid'] = point.id
      data2[index]['username'] = "Default"
      for user in _users:
        if point.user_id == user.id:
            data2[index]['username'] = user.username
      data2[index]['datapoint'] = point.datapoint
      data2[index]['dataunit'] = point.dataunit
      data2[index]['location'] = point.location
      data2[index]['date'] = str(point.date)
      data2[index]['comments'] = point.comments
      data2[index]['x'] = float(point.xgeo)
      data2[index]['y'] = float(point.ygeo)
      index += 1

    tuser = TempUser()

    #Need to display information for the current user
    #Accessing the current user object
    xgeo = 0.0
    ygeo = 0.0
    for user in _users:
      if(user.username == session['username']):
        curr_user = user
        xgeo = user.defaultloclat
        ygeo = user.defaultloclong
    
    #curr user now holds info on the current user
    tuser.userName = curr_user.username
    tuser.eMail = curr_user.email
    tuser.name = curr_user.name

    if request.method == 'POST':  
      datapoints = user_data.query.all()
      datapoints.sort(key=lambda x: tuple(map(int, x.date.split('-'))), reverse=True)
      # Check that the distance entered by the user is a number
      try:
          float(form.radius.data)
      except ValueError:
          errors.append(8)
          return render_template('dataView.html', title = 'Data View Page', tuser=tuser, data = data2, len = len(data2), GM=GM, STV=STV, xgeo=xgeo, ygeo=ygeo, form=form, errors=errors)


      r = float(form.radius.data)
      data2 = {}
      index = 0
      errors = []
      GM = 0.0
      STV = 0.0
      tuser = TempUser()
      xgeo = 0.0
      ygeo = 0.0
      for user in _users:
        if(user.username == session['username']):
            curr_user = user
            xgeo = user.defaultloclat
            ygeo = user.defaultloclong
    
      tuser.userName = curr_user.username
      tuser.eMail = curr_user.email
      tuser.name = curr_user.name
      dp = []
      stats = {}
      stats['size'] = 20
      # sort the data points to ensure newest points are first 
      datapoints.sort(key=lambda x: tuple(map(int, x.date.split('-'))), reverse=True)
      
      # find all points in the specified distance from the user's defualt location value
      for point in datapoints:
          if (float(geopy.distance.vincenty((float(xgeo), float(ygeo)), (float(point.xgeo), float(point.ygeo))).miles) <= r):
            data2[index] = {}
            data2[index]['dataid'] = point.id
            data2[index]['username'] = "Default"
            for user in _users:
                if point.user_id == user.id:
                    data2[index]['username'] = user.username

            data2[index]['datapoint'] = point.datapoint
            data2[index]['dataunit'] = point.dataunit
            data2[index]['location'] = point.location
            data2[index]['date'] = str(point.date)
            data2[index]['comments'] = point.comments
            data2[index]['x'] = float(point.xgeo)
            data2[index]['y'] = float(point.ygeo)
            dp.append(point.datapoint)
            index += 1

      # Ensure there are 20 points in the desired area
      if(len(dp) >= 20):
          for x in range(20):
              stats[x] = {}
              stats[x]['datapoint'] = dp[x]
          GM, STV = computeStats(stats)
      else:
          errors.append(3)

      return render_template('dataView.html', title = 'Data View Page', tuser=tuser, data = data2, len = int(len(data2)), GM=GM, STV=STV, xgeo=xgeo, ygeo=ygeo, form=form, errors=errors)

    return render_template('dataView.html', title = 'Data View Page', tuser=tuser, data = data2, len = len(data2), GM=GM, STV=STV, xgeo=xgeo, ygeo=ygeo, form=form, errors=errors)

# Logout route. Removes user from the session
@main.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# Login route
@main.route('/login',  methods=['GET', 'POST'])
def Login():
  errors = []
  form = LoginForm()
  if form.validate_on_submit():
    #Log in the user here
    _users = users.query.all()
    for user in _users:
        if form.username.data == user.username:
            if bcrypt.checkpw(form.password.data, user.password):
                session['username'] = form.username.data
                return redirect('/index')
            else:
                errors.append(1)
    errors.append(2)
  return render_template('login.html', title='Login', form=form, errors=errors)

# Route to reset a user's password
@main.route('/reset', methods=['GET', 'POST'])
def Reset():
    errors = []
    form = ResetForm()
    if form.validate_on_submit():
        _users = users.query.all()
        for user in _users:
            if form.email.data == user.email:
                letters = string.ascii_lowercase
                newp = ''.join(random.choice(letters) for i in range(7))
                # Here the new password is set to a random string of 7 lowercase letters
                user.password = bcrypt.hashpw(str(newp), bcrypt.gensalt())
                db.session.commit()
                # here we send the new password to the user's email
                # the address used has a setting that allows 3rd part applications to be used
                # so if you want to use a different gmail that setting will need to be turned on
                sender = "agh2owsu@gmail.com"
                receivers = []
                receiver = form.email.data
                receivers.append(receiver)
                message = MIMEMultipart()
                body = "Hello, your new password is:\n" + str(newp)
                message["From"] = sender
                message["To"] = receiver
                message["Subject"] = "Password Reset"
                message.attach(MIMEText(body))
                # if you want to use a non gmail service different smtplib seeting will be needed
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login("agh2owsu", "AGwater20")
                server.sendmail(sender, receivers, message.as_string())
                return redirect('/login')
            else:
                errors.append(1)
       # errors.append(1)
    return render_template('reset.html', title='Reset', form=form, errors=errors)

# This routes allows users to change their password
@main.route('/change', methods=['GET', 'POST'])
def Change():
    if not session.get('username'):
        return redirect('/login')
    
    errors = []
    form = ChangePassword() 
    if form.validate_on_submit():
        _users = users.query.all()
        for user in _users:
            if user.username == session['username']:
                if bcrypt.checkpw(form.password.data, user.password):
                    if form.newpassword.data == form.confirmpassword.data:
                        user.password = bcrypt.hashpw(form.newpassword.data, bcrypt.gensalt())
                        db.session.commit()
                        return redirect('/login')
                    else:
                        errors.append(2)
                else:
                    errors.append(1)
                
    return render_template('change.html', title='Change Password', form=form, errors=errors)

# This route allows users to change thier default location
# this location is sued to center the map on the dataview page and to locate the closest 
# points to them for the statistical analysis
@main.route('/changeloc', methods=['GET', 'POST'])
def Changeloc():
    if not session.get('username'):
        return redirect('/login')

    errors = []
    form = ChangeLocation()
    if form.validate_on_submit():
        _users = users.query.all()
        for user in _users:
            if user.username == session['username']:
                try:
                    float(form.xgeo.data)
                except ValueError:
                    errors.append(2)
                try:
                    float(form.ygeo.data)
                except ValueError:
                    errors.append(3)
                if not errors: 
                    if float(form.ygeo.data) > 180 or float(form.ygeo.data) < -180:
                        errors.append(4)
                    if float(form.xgeo.data) > 90 or float(form.xgeo.data) < -90:
                        errors.append(5)
                if len(errors) > 0:
                    return render_template('changeloc.html', title='Change Location', form=form, errors=errors)

                if not errors:
                    user.defaultloclat = form.xgeo.data
                    user.defaultloclong = form.ygeo.data
                    db.session.commit()
                    return redirect('/index')

    return render_template('changeloc.html', title='Change Location', form=form, errors=errors)

# signup page
@main.route('/signup', methods=['GET', 'POST'])
def Signup():
    errors = []
    tempKL = []
    form = NewUser()
    if form.validate_on_submit():
        if form.password.data != form.confirmPassword.data:
            errors.append(2)
        _users = users.query.all()
        for user in _users:
            if form.username.data == user.username:
                #username already taken error
                errors.append(1)
            if form.email.data == user.email:
                # email already used error
                errors.append(10)
        keylist = keys.query.all()
        for k in keylist:
            tempKL.append(k.key)
            if form.key.data == k.key and k.is_used == 0:
                try:
                    float(form.defaultloclat.data)
                except ValueError:
                    errors.append(4)
                try:
                    float(form.defaultloclong.data)
                except ValueError:
                    errors.append(5)
                if not errors:            
                    if float(form.defaultloclong.data) > 180 or float(form.defaultloclong.data) < -180:
                        errors.append(6)
                    if float(form.defaultloclat.data) > 90 or float(form.defaultloclat.data) < -90:
                        errors.append(7)
                if len(errors) > 0:
                    return render_template('testUser.html', title='Signup', form=form, errors=errors)

                if not errors:
                    # Creating a new user
                    new_user = users(name=form.name.data,username=form.username.data,email=form.email.data,irdistrict=form.irdistrict.data,defaultloclat=form.defaultloclat.data,defaultloclong=form.defaultloclong.data,password=bcrypt.hashpw(form.password.data, bcrypt.gensalt()),isadmin=k.is_admin,ismaster=0)
                    db.session.add_all([new_user])
                    k.is_used = 1
                    db.session.commit()
                    session['username'] = form.username.data
                    return redirect('/index')
        if form.key.data not in tempKL:
            if tempKL:
                errors.append(3)
        if not tempKL:
            errors.append(3)
    return render_template('testUser.html', title='Signup', form=form, errors=errors)

# route to invite a user to join the website by sending them an access key
@main.route("/adduser", methods=['GET', 'POST'])
def adduser():
    if not session.get('username'):
        return redirect('/login')
    logger.info("Add user page being accessed")
    form = AddForm()
    curr_user = TempUser()
    tuser = TempUser()
    _users = users.query.all()
    for user in _users:
      if user.username == session['username']:
        if user.isadmin == 2:
            return redirect('/index')
        curr_user = user
        curr_user.userName = user.username
        curr_user.username = user.username
        curr_user.name = user.name

    tuser.userName = curr_user.username
    tuser.eMail = curr_user.email
    tuser.name = curr_user.name
    for user in _users:
        if user.username == session['username']:
            curr_user_id = user.id
    
    #New user to be created so generate the key and prep the email text
    if request.method == 'POST':
        letters = string.ascii_lowercase        
        gen_key = ''.join(random.choice(letters) for i in range(7))
        now = datetime.now()
        is_admin = request.form.getlist('addadmin')
        body = ""
        if len(is_admin) == 0:
            new_key = keys(key=str(gen_key),date_created=str(now),is_admin=0,is_used=0)
            body = "Hello, your access key for AGH2O is:\n" + str(new_key.key)
        elif len(is_admin) == 1:
            new_key = keys(key=str(gen_key),date_created=str(now),is_admin=1,is_used=0)
            body = "Hello, your administrator access key for AGH2O is:\n" + str(new_key.key)
        # add the new key to the database
        db.session.add_all([new_key])
        db.session.commit()


        # prep the email information
        sender = "agh2owsu@gmail.com"
        receivers = []
        receiver = form.email.data
        receivers.append(receiver)
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = "AGH2O Acess Key"
        message.attach(MIMEText(body))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("agh2owsu", "AGwater20")
        server.sendmail(sender, receivers, message.as_string())
        return redirect('/index')
        

    return render_template('adduser.html', title='Add User', form=form)

# catch all route thet redirects to index. index redirects to login if the suer is not logged in
@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def catch_all(path):
    return redirect('/index')
