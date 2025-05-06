from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from .forms import UploadCSVForm
import seaborn as sns
import os
import matplotlib.pyplot as plt
import pandas as pd
import uuid
from django.conf import settings
from sklearn.linear_model import LinearRegression
from io import BytesIO
import base64
# Create your views here.


def home(request):
    form = UploadCSVForm()
    data=None
    chart_url = None
    regression_result = None

    if request.method=='POST':
        form = UploadCSVForm(request.POST,request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_csv(file)

            data = df.head().to_html()  # show top 5 rows
            
            # save a graph
            plt.figure(figsize=(6,4))
            sns.countplot(data=df,x=df.columns[0])   # Plot first column
            graph_name = f"{uuid.uuid4().hex}.png"
            graph_path = os.path.join(settings.MEDIA_ROOT, graph_name)
            plt.savefig(graph_path)
            chart_url = settings.MEDIA_URL + graph_name
            plt.close()


            # simple ML model - Linear egresion.
            numeric_columns = df.select_dtypes(include='number').columns

            if len(numeric_columns) >= 2:
                try: 
                    x = df[[numeric_columns[0]]]  # first column as feature
                    y = df[numeric_columns[1]]    # second column as label

                    
                    model = LinearRegression()
                    model.fit(x, y)
                    prediction = model.predict(x)

                    # Plot regression
                    plt.figure(figsize=(6, 4))
                    plt.scatter(x, y, color='blue', label='Actual')
                    plt.plot(x, prediction, color='red', label='Predicted')
                    plt.xlabel(numeric_columns[0])
                    plt.ylabel(numeric_columns[1])                        
                    plt.legend()

                    # Save in memory as base64
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    chart_url = 'data:image/png;base64,' + base64.b64encode(image_png).decode('utf-8')
                    plt.close()

                    regression_result = f"Regression line plotted between <b>{numeric_columns[0]}</b> (x-axis) and <b>{numeric_columns[1]} (y-axis)</b>"
                except Exception as e:
                    regression_result = f"Error in ML model: {str(e)}"
            else:
                regression_result = "Not enough numeric columns for regression"


    return render(request, 'dashboard/home.html', {'form':form, 'data':data, 'chart_url':chart_url , 'regression_result':regression_result})



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')
