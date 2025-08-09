// Global map variable
let map;

// Initialize map and set up event listeners once on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initializeMap();
    document.getElementById("auth-modal").style.display = "flex"; // Show auth modal
});

// Initialize map
function initializeMap() {
    map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add map click event to fetch weather data
    map.on('click', ({ latlng: { lat, lng } }) => fetchWeatherData(lat, lng));
}

// Toggle between login and register forms
function toggleForm(showLogin = true) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const buttons = document.querySelectorAll('.tabs button');

    loginForm.style.display = showLogin ? 'block' : 'none';
    registerForm.style.display = showLogin ? 'none' : 'block';

    // Set active tab styling
    buttons.forEach((btn, index) => btn.classList.toggle('active-tab', showLogin === (index === 0)));
}

// Handle user authentication (login and register)
async function authUser(endpoint, payload, successMessage) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
            alert(successMessage);
            closeAuthModal();
            if (endpoint === 'register') toggleForm(true);
            if (endpoint === 'login') localStorage.setItem('token', data.token);
        } else {
            console.error("Server error:", data.error);
            alert(data.error || `Failed to ${endpoint}. Please try again.`);
        }
    } catch (error) {
        console.error(`Error during ${endpoint}:`, error);
    }
}

function loginUser() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    authUser('login', { email, password }, 'Login successful!');
}

function registerUser() {
    const userDetails = {
        name: document.getElementById('register-name').value,
        email: document.getElementById('register-email').value,
        phone: document.getElementById('register-phone').value,
        location: document.getElementById('register-location').value,
        password: document.getElementById('register-password').value
    };
    authUser('register', userDetails, 'Registration successful!');
}

// Close the auth modal
function closeAuthModal() {
    document.getElementById("auth-modal").style.display = "none";
}

// Fetch weather and fire prediction data
async function fetchWeatherData(lat, lon) {
    const apiKey = 'ba0e904efab2a46da694e914c225f789';
    const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        displayWeatherAndPrediction(data);

        // Send SMS with location and weather details
        await sendSMS({
            location: data.name || `Lat: ${lat}, Lon: ${lon}`,
            temperature: data.main.temp,
            humidity: data.main.humidity,
            wind_speed: data.wind.speed,
            wind_direction: data.wind.deg
        });
    } catch (error) {
        console.error('Error fetching weather data:', error);
    }
}

// Send SMS with location and weather details
async function sendSMS(weatherDetails) {
    try {
        const response = await fetch('http://127.0.0.1:5000/send_sms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(weatherDetails)
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('Failed to send SMS:', error);
        } else {
            console.log('SMS sent successfully!');
        }
    } catch (error) {
        console.error('Error sending SMS:', error);
    }
}

// Display weather and fire prediction
async function displayWeatherAndPrediction(weatherData) {
    const { name, main: { temp, humidity }, wind: { speed, deg } } = weatherData;

    // Update weather elements
    const elements = {
        location: `Location: ${name}`,
        temperature: `Temperature: ${temp}°C`,
        humidity: `Relative Humidity: ${humidity}%`,
        windSpeed: `Wind Speed: ${speed} m/s`,
        windDirection: `Wind Direction: ${deg}°`
    };

    Object.entries(elements).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = text;
    });

    // Fetch and display fire risk prediction
    try {
        const prediction = await getFirePrediction({ temperature: temp, humidity, speed, deg });
        displayPredictionResult(prediction, temp);
    } catch (error) {
        console.error('Error displaying prediction:', error);
    }
}

// Fetch fire prediction
async function getFirePrediction({ temperature, humidity, speed, deg }) {
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                temperature,
                relative_humidity: humidity,
                wind_speed: speed,
                rain: 0,
                wind_direction: deg,
                phone: "+919342999486"
            })
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('Prediction error:', error);
            throw new Error(error.error || 'Failed to fetch prediction');
        }

        const { probability } = await response.json();
        return probability;
    } catch (error) {
        console.error('Error fetching fire prediction:', error);
        throw error;
    }
}

// Display prediction result
function displayPredictionResult(prediction, temperature) {
    const riskLevels = [
        { threshold: 0.5, label: "Very High" },
        { threshold: 0.3, label: "High" },
        { threshold: 0.1, label: "Moderate" },
        { threshold: 0.05, label: "Low" },
        { threshold: 0.0, label: "Very Low" }
    ];
    

    // Adjust prediction for temperatures below 0
    const adjustedPrediction = temperature < 0 && prediction > 0.8 ? 0.2 : prediction;

    // Determine risk level based on thresholds
    const riskLevel = riskLevels.find(({ threshold }) => adjustedPrediction >= threshold)?.label || "Very Low";

    // Update the HTML element with only the risk level
    const predictionElement = document.getElementById('prediction');
    if (predictionElement) {
        predictionElement.textContent = `Fire Risk Level: ${riskLevel}`;
        predictionElement.className = riskLevel.toLowerCase().replace(' ', '-');
    }
}

