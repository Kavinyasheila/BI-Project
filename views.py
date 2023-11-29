from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import UserRegisterForm
from .forms import PricePredictionForm
from .models import CustomUser
import joblib
from django.shortcuts import render
from .forms import PricePredictionForm
from sklearn.preprocessing import LabelEncoder
from .models import PricePredictionInput
import re
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import CustomUserChangeForm

# Load the pre-trained model outside the view function
model = joblib.load('C:/Users/user/Documents/GitHub/135399/webapp/models/linear_regression_model.joblib')

#load the Encoder
le_name = joblib.load('C:/Users/user/Documents/GitHub/135399/webapp/models/label_encoder_name.joblib')

def home(request):
    return render(request, 'users/home.html')


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Hi {username}, your account was created successfully')
            return redirect('home')
    else:
        form = UserRegisterForm()
        return render(request, 'users/register.html', {'form': form})


    
          

def extract_numeric(value):
    try:
        return float(re.search(r'\d+\.*\d*', value).group())
    except (AttributeError, ValueError):
        return 1.0 

def predict_price(request):
    form = PricePredictionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user_input = form.cleaned_data

        # Encode product name using the loaded LabelEncoder
        user_name_encoded = le_name.transform([user_input['Name']])

        # Retrieve 'Price Per Each' from the trained model based on the user's product name
        product_price_per_each = model.predict([[user_name_encoded[0], 0, 0]])[0]  # Assuming the model takes three features

        # Preprocess user input for quantity
        user_quantity = extract_numeric(user_input['Quantity'])

        # Calculate the estimated total price
        total_price = product_price_per_each * user_quantity

        # Save user input and predicted price to the database
        prediction_instance = PricePredictionInput(
            Name=user_input['Name'],
            Quantity=user_quantity,
            PredictedPrice=total_price
        )

        # Save the instance to the database
        prediction_instance.save()
        

        # Pass the estimated total price as a success message
        messages.success(request, f'The estimated total price for {user_input["Quantity"]} of {user_input["Name"]} is {total_price:.2f} KSH.')

        context = {'form': form}

        return redirect('predict_price')

    context = {'form': form}
    return render(request, 'users/predict_price.html', context)

def profile(request):
     #user_predictions = PricePredictionInput.objects.filter(user=request.user)

     #context = {'user_predictions': user_predictions} 
     return render(request, 'users/profile.html')

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

