import pickle
import os
import sklearn
import json
import csv
from django.templatetags import static
from django.contrib.staticfiles.finders import find
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Text, CustomUser
from django.http import HttpResponse

from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm


def homePage(request):
    model_path = find('models/model_svm1.pkl')
    if request.method == 'POST':
        text = request.POST.get('text', '')
        if len(text) < 1:
            messages.error(request, "enter a text befor you atempt to submit")
            return render(request, 'home.html')
        else:

            with open(model_path, 'rb') as file:
                model = pickle.load(file)
            predictions = model.predict([text])[0]

            if request.user.is_authenticated:
                user = request.user
                create_text = Text(user=user,
                                   text=text,
                                   predictions=predictions
                                   )
                create_text.save()

            else:
                create_text = Text(
                                text=text,
                                predictions=predictions
                                )
                create_text.save()
            return render(request, 'home.html', {'predictions': predictions})
    else:
        return render(request, 'home.html', {})


def about(request):
    return render(request, 'about.html', {})


def allTexts(request):
    texts = Text.objects.all().order_by('-created_at')
    return render(request, 'admin_data.html', {"texts": texts})


def dashboard(request):
    texts = Text.objects.all()

    # Prepare data for chart
    labels = [text.text[:20] for text in texts]
    predictions = [text.predictions for text in texts]

    # Convert data to JSON
    chart_data = {
        'labels': labels,
        'predictions': predictions
    }

    return render(request, 'dashboard.html', {'chart_data': json.dumps(chart_data)})


def texts(request):
    if request.user.is_authenticated:
        current_user = CustomUser.objects.get(id=request.user.id)
        texts = Text.objects.filter(user=current_user)
        return render(request, "your_data.html", {"texts": texts})
    return render(request, 'your_data.html', {})


def download_csv(request):
    response = HttpResponse(content_type='text/csv')
    response["Content-Disposition"] = "attachment; filename=data.csv"
    writer = csv.writer(response)
    writer.writerow(['users', 'Text',
                     'verdict'])
    data = Text.objects.all().values_list('user', 'text', 'predictions')
    for row in data:
        writer.writerow(row)

    return response


def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You logged in successfully')
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials, please try again")
            return redirect('login')
    return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out")
    return redirect('home')


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data['email']  # Use email
            password = form.cleaned_data['password1']

            user = authenticate(email=email, password=password)  # Authenticate using email
            if user is not None:
                login(request, user)
                messages.success(request, 'Account created successfully')
                return redirect('home')
            else:
                messages.error(request, 'Authentication failed')
                return redirect('register')
        else:
            messages.error(request, 'There was a problem creating your account')
    else:
        form = SignUpForm()

    return render(request, 'register.html', {'form': form})


def update_user(request):
    if request.user.is_authenticated:
        current_user = CustomUser.objects.get(id=request.user.id)

        user_form = UpdateUserForm(request.POST or None, instance=current_user)
        if user_form.is_valid():
            user_form.save()
            login(request, current_user)
            messages.success(request, 'You have successfully updated your profile')
            return redirect('home')
        return render(request, 'update_user.html', {'user_form': user_form})
    else:
        messages.error(request, 'You must be logged in to access that page.')
        return redirect('home')


def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == "POST":
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "You have successfully updated your password. Please log in to continue.")
                login(request, current_user)
                return redirect('update_user')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
        else:
            form = ChangePasswordForm(current_user)
        return render(request, 'update_password.html', {'form': form})
    else:
        messages.error(request, "You must be logged in to access this page.")
        return redirect('home')


from django.shortcuts import render
from collections import Counter
from .models import Text

def dashboard(request):
    # Fetch all predictions from the database
    all_predictions = Text.objects.all()

    # Count occurrences of each class
    class_counts = Counter([text.predictions for text in all_predictions])

    class_labels = list(class_counts.keys())
    class_counts_list = list(class_counts.values())
    print(class_labels, class_counts_list)

    # Get statistics
    total_predictions = all_predictions.count()
    hate_count = sum(1 for t in all_predictions if t.predictions in ["Hate Speech", "Offensive"])
    non_hate_count = total_predictions - hate_count
    most_common_class = class_labels[class_counts_list.index(max(class_counts_list))] if class_labels else "None"

    # Get the latest predictions
    recent_predictions = Text.objects.order_by('-created_at')[:10]


    context = {
        'class_labels': class_labels,
        'class_counts': class_counts_list,
        'total_predictions': total_predictions,
        'hate_count': hate_count,
        'non_hate_count': non_hate_count,
        'most_common_class': most_common_class,
        'recent_predictions': recent_predictions,
    }


    return render(request, 'dashboard.html', context)
