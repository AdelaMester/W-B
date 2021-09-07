from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import os
from uuid import uuid4
import urllib.parse
import requests
import json
import psycopg2

client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
redirect_uri = "https://oauth-crudapp.herokuapp.com/callback"


# Create your views here.
def index(request):
    return render(request, "crudapp/index.html")

def home(request):
    if request.method == 'GET':
        print("session:"+str(request.session['name']))
        return render(request, "crudapp/home.html",{
            'name': request.session['name']

        })

def profile(request):
    if request.method == 'GET':
        return render(request, "crudapp/profile.html")
    if request.method == 'POST':
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        if request.POST.get('Address'):
            address = request.POST.get('Address')
            cur.execute("UPDATE users SET address =%s WHERE username=%s", (address, request.session['name']))
            conn.commit()
        elif request.POST.get('Contact_number'):
            number = request.POST.get('Contact_number')
            cur.execute("UPDATE users SET contact_number =%s WHERE username=%s", (number, request.session['name']))
            conn.commit()
        cur.close()
        conn.close()
        return render(request,"crudapp/profile.html")

def updateprofile(request):
    if request.method == 'GET':
        return render(request, "crudapp/updateprofile.html")

def deleteinformation(request):
    if request.method == 'GET':
        return render(request, "crudapp/deleteinformation.html")

def request_identity(request):
    state = str(uuid4())
    params = {"client_id": client_id,
              "response_type": "code",
              "redirect_uri": redirect_uri,
              "state": state,
              "scope": "user"
              }
    return HttpResponseRedirect('https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params))

def callback(request):
    if request.method == 'GET':
        code = request.GET.get('code')
        state= request.GET.get('state')
        post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": redirect_uri,
                 "client_id": client_id,
                 "client_secret": client_secret
                 }
        response = requests.post("https://github.com/login/oauth/access_token", data=post_data)
        at = response.text[13:53]
        print(at)
        name = username(at)
        request.session['name'] = name
        print(name)
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (name,))
        row = cur.fetchone()
        if not row[0]:
            cur.execute("INSERT INTO users (username, access_token) VALUES (%s, %s)", (name, at));
            conn.commit()
        cur.close()
        conn.close()
        return render(request, "crudapp/home.html", {
            "name": name
        })

def username(access_token):
    headers = {"Authorization": "token " + str(access_token)}
    response = requests.get("https://api.github.com/user", headers=headers)
    name = response.json()
    return name["login"]


