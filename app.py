from flask import Flask, jsonify, request, render_template, send_from_directory
import os
import joblib
import numpy as np
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from psycopg2 import pool
import jwt
import datetime
import xgboost as xgb
from twilio.rest import Client

# Initialize Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

# Secret key for JWT
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', 'your_twilio_phone_number')
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER', '+917094366822')  # Replace with the recipient's phone number

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Utility function to send SMS
def send_sms(phone_number, message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"SMS sent to {phone_number}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

# Database connection pool
db_pool = pool.SimpleConnectionPool(1, 20,
    database="weather_app",
    user="postgres",
    password="unlock",
    host="localhost",
    port="5432"
)

# Load XGBoost model
model = xgb.Booster()
model.load_model('D:\\Devs\\intern\\mini\\Thirdtry\\fire_spread_model.json')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    print("Received data:", data)
    required_keys = ["temperature", "relative_humidity", "wind_speed", "rain", "wind_direction", "phone"]
    if not all(key in data for key in required_keys):
        return jsonify({"error": "Missing data"}), 400

    features = np.array([
        data['temperature'],
        data['relative_humidity'],
        data['wind_speed'],
        data['rain'],
        data['wind_direction']
    ]).reshape(1, -1)
    
    dtest = xgb.DMatrix(features)
    prediction = model.predict(dtest)[0]
    risk_threshold = 0.8  # Set your threshold here

    # If prediction exceeds threshold, send SMS alert
    if prediction >= risk_threshold:
        user_phone = data['phone']
        alert_message = f"Fire Risk Alert! Probability: {prediction * 100:.2f}% - Stay safe!"
        send_sms(user_phone, alert_message)

    return jsonify({"probability": float(prediction)})

@app.route('/send_sms', methods=['POST'])
def send_sms_endpoint():
    data = request.json
    try:
        location = data.get('location', 'Unknown Location')
        temperature = data.get('temperature', 'N/A')
        humidity = data.get('humidity', 'N/A')
        wind_speed = data.get('wind_speed', 'N/A')
        wind_direction = data.get('wind_direction', 'N/A')

        # Format the SMS content
        sms_content = (
            f"Weather Alert!\n"
            f"Location: {location}\n"
            f"Temperature: {temperature}°C\n"
            f"Humidity: {humidity}%\n"
            f"Wind Speed: {wind_speed} m/s\n"
            f"Wind Direction: {wind_direction}°"
        )
        # From your code:
        USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER', '+919342999486')  # Default recipient

        # Send the SMS
        send_sms(USER_PHONE_NUMBER, sms_content)

        return jsonify({"message": "SMS sent successfully!"}), 200
    except Exception as e:
        print(f"Error in /send_sms: {e}")
        return jsonify({"error": "Failed to send SMS."}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    location = data.get('location')
    password = data.get('password')

    # Ensure all fields are provided
    if not (name and email and password):
        return jsonify({"error": "Please fill out all required fields"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Insert user into the database
    try:
        with db_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, phone, location, password) VALUES (%s, %s, %s, %s, %s)",
                    (name, email, phone, location, hashed_password)
                )
                conn.commit()
        return jsonify({"message": "Registration successful!"}), 201
    except Exception as e:
        print("Error during registration:", e)
        return jsonify({"error": "Registration failed. Please try again."}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json

    with db_pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (data['email'],))
            user = cur.fetchone()

            if user and bcrypt.check_password_hash(user[1], data['password']):
                token = jwt.encode(
                    {'user_id': user[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                    SECRET_KEY
                )
                return jsonify({"token": token}), 200
            else:
                return jsonify({"error": "Invalid email or password"}), 401

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
