import numpy as np
import pandas as pd
from flask import Flask, flash, request, render_template, flash, redirect, url_for, session,  request, abort

import config
from datetime import datetime

import mysql.connector


import pickle




mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="diabetes"
)

mycursor = mydb.cursor()

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
dataset = pd.read_csv('diabetes.csv')

dataset_X = dataset.iloc[:,[1, 2, 5, 7]].values

from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range = (0,1))
dataset_scaled = sc.fit_transform(dataset_X)




@app.route('/')
def home():
    return render_template('home.html',login=config.isLoggedIn())   

@app.route('/home')
def hom():
    return render_template('home.html',login=config.isLoggedIn())




@app.route('/signup')
def signup():
    return render_template('register.html',login=config.isLoggedIn())

@app.route('/signup', methods=['GET', 'POST'])
def register_post():
    # Output message if something goes wrong...
    msg = '' 
    
    name = request.form['name']
    
    mobile = request.form['mob'] 
    email = request.form['email'] 
    blood = request.form['blood'] 
    address = request.form['address'] 
    date = request.form['date'] 
    doctor = request.form['doc'] 
    password = request.form['password']
    
    mycursor.execute('SELECT * FROM users WHERE email =%s',(email,))
    account = mycursor.fetchone() 
    if account: 
        msg = 'Account already exists !'
    else:
        sq='INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)'
        mycursor.execute(sq, (name, mobile, email, blood, address, date, doctor, password, )) 
        mydb.commit()
        msg = 'You have successfully registered !'    
    return render_template('register.html', msg = msg) 


@app.route('/login')
def login():
    return render_template('log.html',login=config.isLoggedIn())

@app.route('/login', methods =['POST']) 
def login_post(): 
    msg = ''
    email = request.form['txtEmail']  
    password = request.form['password'] 
    print(email)
    print(password)
   
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * FROM users WHERE email = %s and password = %s', (email, password, )) 
    account = mycursor.fetchone()  
    if account: 
        session['loggedin'] = True
        session['id'] = account[0] 
        session['name'] = account[1] 
        session['email'] = account[3]
        session['mobile'] = account[4] 
        msg = 'Logged in successfully !'
        return redirect(url_for('dashboard')) 
    else: 
        msg = 'Incorrect username / password !'
        return render_template('log.html', msg = msg) 

@app.route('/contact')
def contactus():
    return render_template('contact-us.html',login=config.isLoggedIn())

@app.route('/contact', methods=['POST'])
def contact_form_post():
    mycursor = mydb.cursor()
    name = request.form['name']
    mobile = request.form['phonenumber']
    email = request.form['email']
    messageData = request.form['messages']


    try:
        sq='INSERT INTO contact VALUES (%s, %s, %s, %s, NULL)'
        mycursor.execute(sq, (name, mobile, email, messageData, )) 
        mydb.commit()
        flash="Hey "+ name +"! Your Message Has Been Sent Successfully ."
    except:
        flash="Hey "+ name +"! Sorry ... Some Internal Problem"
    return render_template('contact-us.html', flash=flash) 

@app.route('/dashboard')
def dashboard():
    if config.isLoggedIn():
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))


@app.route('/dashboard/profile')
def profile():
    if config.isLoggedIn():
        uid=session['id']

        mycursor.execute('SELECT * FROM users WHERE uid =%s',(uid,))
        
        account = mycursor.fetchone()
        
        if account:
            name = account[1] 
            mobile = account[2]
            blood = account[4] 
            dob = account[6]
            address = account[5] 
            doctor = account[7]
            mycursor.execute('SELECT * FROM predict WHERE uid =%s',(uid,))
            acc = mycursor.fetchone()
            glucose=acc[2]
            if acc[6] == '1':
                predict=True
            else:
                predict=False





        return render_template('dashboard/profile.html',login=config.isLoggedIn(),uid=session['id'], name=name,mobile=mobile,blood=blood,dob=dob,address=address,doctor=doctor,predict=predict,glucose=glucose)
    else:
        return redirect(url_for('login'))
    
  
@app.route('/dashboard/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('email', None)
    session.pop('id', None)
    session.pop('name', None)
  
    flash="Logged Out Successfully"
    
    return render_template('log.html',msg1=flash)

@app.route('/dashboard/logout',methods=['POST'])
def logout_post():
    msg = ''
    email = request.form['txtEmail']  
    password = request.form['password'] 
    print(email)
    print(password)
   
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * FROM users WHERE email = %s and password = %s', (email, password, )) 
    account = mycursor.fetchone()  
    if account: 
        session['loggedin'] = True
        session['id'] = account[0] 
        session['name'] = account[1] 
        session['email'] = account[3]
        session['mobile'] = account[4] 
        msg = 'Logged in successfully !'
        return redirect(url_for('dashboard')) 
    else: 
        msg = 'Incorrect username / password !'
        return render_template('log.html', msg = msg) 


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',login=config.isLoggedIn())

@app.route('/dashboard/predict')
def prdict():
    if config.isLoggedIn():
        return render_template('/dashboard/predict.html',login=config.isLoggedIn())
    else:
        return redirect(url_for('login'))

@app.route('/dashboard/predict',methods=['POST'])
def predic_post():
    '''
    For rendering results on HTML GUI
    '''
    
    float_features = [float(x) for x in request.form.values()]
    final_features = [np.array(float_features)]
    prediction = model.predict( sc.transform(final_features) )

    uid=session['id']
    glucose = request.form['Glucose Level']
    insulin = request.form['Insulin']
    bmi = request.form['BMI']
    age = request.form['Age']
    

    if prediction == 1:
        pred = "You have Diabetes, please Check patient info for precautions."
        pr='1'
    elif prediction == 0:
        pred = "You don't have Diabetes."
        pr='0'
    output = pred
    predict=pr
    mycursor.execute('SELECT * FROM predict WHERE uid = %s ', (uid, )) 
    account = mycursor.fetchone()  
    if account:
        sql='UPDATE `predict` SET `glucose`=%s,`insulin`=%s,`bmi`=%s,`age`=%s,`predict`=%s WHERE uid =%s'
        mycursor.execute(sql, (glucose, insulin, bmi, age, predict, uid,  ))
        mydb.commit()
    else:
        sql='INSERT INTO predict VALUES (NULL, %s, %s, %s, %s, %s, %s)'
        mycursor.execute(sql, (uid, glucose, insulin, bmi, age, predict, ))
        mydb.commit()
   
    return render_template('/dashboard/predict.html', prediction_text='{}'.format(output))

if __name__ == "__main__":
    app.run(debug=True)
