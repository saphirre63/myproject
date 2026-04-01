from flask import Flask, render_template_string, request, jsonify
import random
import secrets
import os
from typing import Optional

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ==================== DATA CONFIGURATION ====================

CARBON_PRICE_DEFAULT = 50.0 

CARBON_INTENSITY = {
    "US": 424, "IN": 705, "DE": 369, "FR": 57, "BR": 89,
    "CA": 130, "AU": 680, "JP": 480, "GB": 230, "IT": 300,
    "MX": 380, "ZA": 850, "KR": 450, "ES": 200, "SE": 15,
    "CN": 580, "RU": 470, "AR": 360, "EG": 450, "NG": 400,
    "NO": 8, "IS": 0, "NZ": 120, "CH": 30, "FI": 90,
    "DK": 150, "NL": 390, "BE": 220, "AT": 140, "PL": 690
}

CURRENCY_SYMBOL = {
    "US": "$", "IN": "₹", "DE": "€", "FR": "€", "BR": "R$",
    "CA": "$", "AU": "$", "JP": "¥", "GB": "£", "IT": "€",
    "MX": "$", "ZA": "R", "KR": "₩", "ES": "€", "SE": "kr",
    "CN": "¥", "RU": "₽", "AR": "$", "EG": "E£", "NG": "₦",
    "NO": "kr", "IS": "kr", "NZ": "$", "CH": "Fr", "FI": "€",
    "DK": "kr", "NL": "€", "BE": "€", "AT": "€", "PL": "zł"
}

ELECTRICITY_RATE = {
    "US": 0.14, "IN": 7.0, "DE": 0.36, "FR": 0.19, "BR": 0.80,
    "CA": 0.13, "AU": 0.35, "JP": 27.0, "GB": 0.34, "IT": 0.28,
    "MX": 2.0, "ZA": 2.5, "KR": 120, "ES": 0.25, "SE": 2.5,
    "CN": 0.6, "RU": 5.0, "AR": 50.0, "EG": 1.5, "NG": 50.0,
    "NO": 1.5, "IS": 18.0, "NZ": 0.30, "CH": 0.25, "FI": 0.17,
    "DK": 2.5, "NL": 0.30, "BE": 0.30, "AT": 0.25, "PL": 0.70
}

RENEWABLE_POTENTIAL = {
    "US": {"solar": "excellent", "wind": "good", "hydro": "moderate"},
    "IN": {"solar": "excellent", "wind": "moderate", "hydro": "good"},
    "DE": {"solar": "moderate", "wind": "excellent", "hydro": "low"},
    "FR": {"solar": "good", "wind": "good", "hydro": "excellent"},
    "BR": {"solar": "excellent", "wind": "good", "hydro": "excellent"},
    "CA": {"solar": "moderate", "wind": "excellent", "hydro": "excellent"},
    "AU": {"solar": "excellent", "wind": "excellent", "hydro": "low"},
    "JP": {"solar": "good", "wind": "moderate", "hydro": "good"},
    "GB": {"solar": "low", "wind": "excellent", "hydro": "moderate"},
    "SE": {"solar": "low", "wind": "good", "hydro": "excellent"}
}

ENERGY_TIPS = {
    "ac": ["Set AC to 24-26°C. Each degree lower uses 6% more energy.", "Use ceiling fans with AC.", "Clean filters monthly."],
    "heating": ["Lower thermostat by 1°C saves 10%.", "Seal windows/doors.", "Use solar heating."],
    "office": ["Use laptops (80% less power).", "Smart power strips.", "Enable sleep mode."],
    "ev": ["Charge off-peak (10PM-6AM).", "Maintain battery at 20-80%."],
    "appliances": ["Wash clothes in cold water.", "Air dry dishes.", "Full loads only."],
    "lighting": ["Switch to LEDs.", "Use natural light.", "Install motion sensors."]
}

INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

CITIES_BY_STATE = {
    "Karnataka": ["Bengaluru", "Mysore", "Hubli", "Mangalore", "Bidar", "Belgaum"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"]
}

BIDAR_TOWNS = ["Aurad", "Basavakalyan", "Bhalki", "Chitgoppa", "Hulsoor", "Humnabad", 
               "Kamalnagar", "Old City", "New City", "Gumpa", "Mailoor", "Chidri"]

EXAMPLES = [
    {"name": "Urban Apt (US)", "location": "US", "usage": 12, "habits": "AC in summer, WFH setup", "icon": "🏢"},
    {"name": "Family Home (IN)", "location": "IN", "usage": 16, "habits": "Fans, Lights, TV, Fridge", "icon": "🏠"},
    {"name": "Eco Student (DE)", "location": "DE", "usage": 6, "habits": "Laptop, LED lights, No AC", "icon": "📚"}
]

# ==================== BACKEND LOGIC ====================

def get_current_weather(location: str) -> Optional[dict]:
    coord_map = {
        "US": (37.09, -95.71), "IN": (20.59, 78.96), "DE": (51.16, 10.45),
        "FR": (46.22, 2.21), "BR": (-14.23, -51.92), "CA": (56.13, -106.34),
        "AU": (-25.27, 133.77), "JP": (36.20, 138.25), "GB": (55.37, -3.43),
        "IT": (41.87, 12.56)
    }
    lat, lon = coord_map.get(location, (0, 0))
    if lat == 0: return None
    try:
        params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,relative_humidity_2m"}
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=3)
        if r.status_code == 200:
            data = r.json()['current']
            desc_map = {0: "Clear", 1: "Mainly Clear", 2: "Cloudy", 3: "Overcast", 45: "Foggy", 61: "Rain", 80: "Showers"}
            return {
                "temperature": data['temperature_2m'],
                "humidity": data['relative_humidity_2m'],
                "description": desc_map.get(data['weather_code'], "Variable")
            }
    except: return None
    return None

# ==================== FRONTEND TEMPLATE ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eco-Genius | Intelligent Energy</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/gsap@3.12.5/dist/gsap.min.js"></script>
    <script src="https://unpkg.com/gsap@3.12.5/dist/ScrollToPlugin.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    
    <style>
        body { 
            font-family: 'Inter', sans-serif; 
            background: #050510; 
            color: #e2e8f0; 
            overflow-x: hidden; 
        }
        
        /* Modern Gradient Background */
        .gradient-bg {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(125deg, #0a0f1c 0%, #0f1729 25%, #0a1628 50%, #051119 75%, #0a0f1c 100%);
            background-size: 400% 400%; animation: gradientShift 20s ease infinite; z-index: -2;
        }
        @keyframes gradientShift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
        
        /* Rain Bubble Effect */
        canvas#rainCanvas {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; z-index: -1;
        }

        /* Glassmorphism from TR file */
        .glass-card {
            background: rgba(30, 41, 59, 0.4); 
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); 
            transition: all 0.3s ease;
        }
        .glass-card:hover { 
            transform: translateY(-5px); 
            border-color: rgba(6, 182, 212, 0.3); /* Cyan hint */
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
        }

        /* Glass Bubble Button Effect */
        .glass-btn {
            position: relative; overflow: hidden;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .glass-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(6, 182, 212, 0.5);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
            transform: scale(1.02);
        }
        /* Bubble Elements inside button */
        .glass-btn::before {
            content: ''; position: absolute; top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            transform: scale(0); transition: transform 0.6s ease-out;
        }
        .glass-btn:hover::before { transform: scale(1); }
        
        .bubble-decoration {
            position: absolute; border-radius: 50%; background: rgba(255,255,255,0.1);
            transition: all 0.5s ease;
        }
        .glass-btn:hover .bubble-decoration { transform: translate(10px, -10px); }

        /* Form Elements */
        select, input, textarea {
            background: rgba(15, 23, 42, 0.6); 
            border: 1px solid rgba(148, 163, 184, 0.2); 
            color: white; border-radius: 0.75rem;
            transition: all 0.3s;
        }
        select:focus, input:focus, textarea:focus {
            outline: none; border-color: #06b6d4; 
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
        }

        #map { height: 350px; border-radius: 16px; width: 100%; z-index: 0; border: 1px solid rgba(255,255,255,0.1); }
        
        /* Utility */
        .text-gradient {
            background: linear-gradient(to right, #22d3ee, #3b82f6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        
        /* Modal */
        #errorModal {
            transition: opacity 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="gradient-bg"></div>
    <canvas id="rainCanvas"></canvas>

    <div id="errorModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 hidden opacity-0">
        <div class="glass-card p-8 max-w-md text-center transform scale-95 transition-transform duration-300" id="errorContent">
            <div class="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4 text-red-400 text-3xl">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h3 class="text-xl font-bold text-white mb-2">Input Required</h3>
            <p class="text-slate-300 mb-6">Please enter your energy habits and usage details to generate an accurate plan.</p>
            <button onclick="closeModal()" class="glass-btn px-6 py-2 rounded-xl text-sm">Got it</button>
        </div>
    </div>

    <nav class="fixed w-full z-50 bg-slate-900/80 backdrop-blur-md border-b border-white/10 transition-all duration-300" id="navbar">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-20">
                <div class="flex items-center gap-2">
                    <div class="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-cyan-500/20">
                        <i class="fas fa-leaf"></i>
                    </div>
                    <span class="text-2xl font-extrabold text-white tracking-tight">Eco<span class="text-cyan-400">Genius</span></span>
                </div>
                
                <div class="hidden md:flex space-x-8">
                    <a href="#home" class="text-sm font-medium text-slate-300 hover:text-cyan-400 transition relative group py-2">
                        HOME
                        <span class="absolute bottom-0 left-0 w-0 h-0.5 bg-cyan-400 transition-all group-hover:w-full"></span>
                    </a>
                    <a href="#calculator" class="text-sm font-medium text-slate-300 hover:text-cyan-400 transition relative group py-2">
                        ANALYSIS
                        <span class="absolute bottom-0 left-0 w-0 h-0.5 bg-cyan-400 transition-all group-hover:w-full"></span>
                    </a>
                    <a href="#estimators" class="text-sm font-medium text-slate-300 hover:text-cyan-400 transition relative group py-2">
                        ESTIMATORS
                        <span class="absolute bottom-0 left-0 w-0 h-0.5 bg-cyan-400 transition-all group-hover:w-full"></span>
                    </a>
                </div>

                <button class="md:hidden text-slate-300 hover:text-white" onclick="toggleMobileMenu()">
                    <i class="fas fa-bars text-2xl"></i>
                </button>
            </div>
        </div>
        
        <div id="mobileMenu" class="hidden md:hidden bg-slate-900 border-t border-white/10 absolute w-full">
            <div class="flex flex-col p-4 space-y-4">
                <a href="#home" class="text-slate-300 hover:text-cyan-400" onclick="toggleMobileMenu()">Home</a>
                <a href="#calculator" class="text-slate-300 hover:text-cyan-400" onclick="toggleMobileMenu()">Analysis</a>
                <a href="#estimators" class="text-slate-300 hover:text-cyan-400" onclick="toggleMobileMenu()">Estimators</a>
            </div>
        </div>
    </nav>

    <section id="home" class="pt-32 pb-20 px-4 min-h-screen flex items-center relative overflow-hidden">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[100px] animate-pulse"></div>
        <div class="absolute bottom-1/3 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[100px] animate-pulse delay-700"></div>

        <div class="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center relative z-10">
            <div class="text-left fade-in-up">
                <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-sm font-semibold mb-6">
                    <span class="relative flex h-2 w-2">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                    </span>
                    AI-Powered Sustainability
                </div>
                <h1 class="text-5xl md:text-7xl font-black mb-6 leading-tight text-white tracking-tight">
                    Optimize Your <br>
                    <span class="text-gradient">Energy Future</span>
                </h1>
                <p class="text-lg md:text-xl text-slate-400 mb-8 leading-relaxed max-w-lg">
                    Advanced algorithms to analyze your habits, calculate your footprint, and guide your transition to renewable energy.
                </p>
                <div class="flex flex-wrap gap-4">
                    <button onclick="scrollToCalc()" class="glass-btn px-8 py-4 rounded-xl flex items-center gap-3 text-lg group">
                        Start Analysis 
                        <i class="fas fa-arrow-right group-hover:translate-x-1 transition-transform"></i>
                        <div class="bubble-decoration w-8 h-8 -top-2 -right-2"></div>
                    </button>
                </div>
            </div>
            
            <div class="relative fade-in-up delay-200 hidden md:block">
                <div class="glass-card p-1 border border-white/10 relative z-10 transform hover:rotate-1 transition-transform duration-500">
                    <div class="bg-slate-900/80 rounded-[22px] overflow-hidden p-6 relative">
                        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 to-blue-600"></div>
                        <div class="flex items-center justify-between mb-8">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400"><i class="fas fa-chart-pie"></i></div>
                                <div>
                                    <h3 class="font-bold text-white">Live Impact</h3>
                                    <p class="text-xs text-slate-400">System Monitoring</p>
                                </div>
                            </div>
                            <span class="text-xs font-mono text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded">ACTIVE</span>
                        </div>
                        <div class="space-y-6">
                            <div>
                                <div class="flex justify-between text-sm mb-2 text-slate-300">
                                    <span>Efficiency Score</span>
                                    <span class="text-cyan-400 font-bold">94%</span>
                                </div>
                                <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
                                    <div class="h-full bg-gradient-to-r from-cyan-400 to-blue-500 w-[94%]"></div>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div class="bg-slate-800 p-3 rounded-lg text-center border border-white/5">
                                    <div class="text-xl font-bold text-white">1.2T</div>
                                    <div class="text-[10px] text-slate-400 uppercase tracking-wider">CO₂ Saved</div>
                                </div>
                                <div class="bg-slate-800 p-3 rounded-lg text-center border border-white/5">
                                    <div class="text-xl font-bold text-white">$450</div>
                                    <div class="text-[10px] text-slate-400 uppercase tracking-wider">Yr Savings</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="py-12 bg-slate-900/30">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
            <h2 class="text-2xl md:text-3xl font-bold text-white mb-8 text-center">Quick Start <span class="text-cyan-400">Templates</span></h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {% for ex in examples %}
                <div class="glass-card p-6 cursor-pointer group" onclick="loadExample('{{ ex.location }}', {{ ex.usage }}, `{{ ex.habits }}`)">
                    <div class="flex justify-between items-start mb-4">
                        <span class="text-4xl group-hover:scale-110 transition-transform duration-300">{{ ex.icon }}</span>
                        <span class="text-xs bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 px-3 py-1 rounded-full font-semibold">{{ ex.location }}</span>
                    </div>
                    <h3 class="font-bold text-white text-lg mb-2 group-hover:text-cyan-400 transition-colors">{{ ex.name }}</h3>
                    <p class="text-sm text-slate-400 line-clamp-2">{{ ex.habits }}</p>
                    <div class="mt-4 flex items-center text-xs text-cyan-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0">
                        Load Template <i class="fas fa-chevron-right ml-1"></i>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>

    <section id="calculator" class="py-24 relative">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
            <div class="text-center mb-12">
                <span class="text-cyan-400 font-bold tracking-widest text-xs uppercase mb-2 block">AI Analysis Engine</span>
                <h2 class="text-3xl md:text-5xl font-bold text-white">Generate Your <span class="text-gradient">Eco Plan</span></h2>
            </div>

            <div class="glass-card p-6 md:p-10 border border-white/10">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    
                    <div class="space-y-8">
                        <div class="bg-slate-800/40 p-6 rounded-2xl border border-white/5">
                            <label class="block text-sm font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                                <i class="fas fa-globe"></i> Location
                            </label>
                            <select id="location" class="w-full p-4 text-base cursor-pointer hover:border-cyan-500/50" onchange="handleLocationChange()">
                                <option value="US">🇺🇸 United States</option>
                                <option value="IN">🇮🇳 India</option>
                                <option value="DE">🇩🇪 Germany</option>
                                <option value="FR">🇫🇷 France</option>
                                <option value="BR">🇧🇷 Brazil</option>
                                <option value="CA">🇨🇦 Canada</option>
                                <option value="AU">🇦🇺 Australia</option>
                                <option value="JP">🇯🇵 Japan</option>
                                <option value="GB">🇬🇧 United Kingdom</option>
                            </select>

                            <div id="india-fields" class="hidden mt-4 space-y-4 pl-4 border-l-2 border-cyan-500/30">
                                <div>
                                    <label class="block text-xs text-slate-400 mb-1">State</label>
                                    <select id="state" class="w-full p-3 text-sm" onchange="handleStateChange()">
                                        <option value="">Select State</option>
                                        {% for state in india_states %}
                                        <option value="{{ state }}">{{ state }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <div id="city-wrapper" class="hidden">
                                    <label class="block text-xs text-slate-400 mb-1">City</label>
                                    <select id="city" class="w-full p-3 text-sm" onchange="handleCityChange()">
                                        <option value="">Select City</option>
                                    </select>
                                </div>
                                <div id="town-wrapper" class="hidden">
                                    <label class="block text-xs text-cyan-400 font-bold mb-1">Bidar Town (Solar Data)</label>
                                    <select id="town" class="w-full p-3 text-sm bg-cyan-900/20 border-cyan-500/50">
                                        <option value="">Select Town</option>
                                        {% for town in bidar_towns %}
                                        <option value="{{ town }}">{{ town }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-semibold text-cyan-400 mb-2">Daily Usage (Hrs)</label>
                                <input type="number" id="daily_hours" class="w-full p-4" placeholder="e.g. 12" min="1" max="24">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold text-cyan-400 mb-2">Cost/Ton CO₂</label>
                                <div id="carbonPriceDisplay" class="w-full p-4 bg-slate-800/60 rounded-xl border border-white/10 text-slate-300 text-sm flex items-center">
                                    Loading...
                                </div>
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-semibold text-cyan-400 mb-2">Habits & Appliances</label>
                            <textarea id="habits" class="w-full p-4 h-32 resize-none" 
                                placeholder="E.g., 'I work from home, run AC for 6 hours, have an electric vehicle charging at night...'"></textarea>
                        </div>

                        <button onclick="analyze()" class="glass-btn w-full py-4 rounded-xl text-lg shadow-lg group mt-4">
                            <span class="relative z-10 flex items-center justify-center gap-2">
                                Generate Analysis <i class="fas fa-magic group-hover:rotate-12 transition-transform"></i>
                            </span>
                            <div class="bubble-decoration w-12 h-12 top-0 right-0 opacity-20"></div>
                        </button>
                    </div>

                    <div class="space-y-6">
                        <div class="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
                            <div id="map"></div>
                            <div class="absolute top-4 right-4 bg-slate-900/90 backdrop-blur px-3 py-1 rounded text-xs text-cyan-400 border border-cyan-500/30 z-[400]">
                                <i class="fas fa-satellite-dish mr-1"></i> Live View
                            </div>
                        </div>
                        
                        <div id="weatherDisplay" class="glass-card p-5 hidden flex items-center justify-between border-l-4 border-yellow-400">
                            <div class="flex items-center gap-4">
                                <div class="text-4xl text-yellow-400"><i class="fas fa-sun" id="weatherIcon"></i></div>
                                <div>
                                    <p class="text-2xl font-bold text-white" id="tempDisplay">--</p>
                                    <p class="text-sm text-slate-400 capitalize" id="weatherDesc">--</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-slate-500 uppercase tracking-wider">Humidity</div>
                                <div class="text-white font-bold" id="humidityDisplay">--%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section id="results" class="hidden py-12 px-4 sm:px-6 relative">
        <div class="absolute inset-0 bg-gradient-to-b from-transparent to-slate-900/50 pointer-events-none"></div>
        <div class="max-w-7xl mx-auto space-y-10 relative z-10">
            
            <div class="glass-card p-8 border-t-4 border-cyan-500">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-white/10 pb-6 mb-8 gap-4">
                    <div>
                        <h3 class="text-3xl font-bold text-white">Analysis Report</h3>
                        <p class="text-slate-400 mt-1 italic text-sm" id="habits-summary"></p>
                    </div>
                    <div id="profile-tags" class="flex gap-2 flex-wrap"></div>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-center">
                    <div class="p-6 bg-slate-800/50 rounded-2xl border border-white/5 hover:border-red-500/30 transition group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider font-bold group-hover:text-red-400">Carbon Footprint</p>
                        <p class="text-3xl font-black text-white mt-2"><span id="res-carbon" class="text-red-400">0</span> <span class="text-sm text-slate-500 font-normal">kg</span></p>
                    </div>
                    <div class="p-6 bg-slate-800/50 rounded-2xl border border-white/5 hover:border-emerald-500/30 transition group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider font-bold group-hover:text-emerald-400">Trees Needed</p>
                        <p class="text-3xl font-black text-white mt-2"><span id="res-trees" class="text-emerald-400">0</span> <span class="text-sm text-slate-500 font-normal">🌳</span></p>
                    </div>
                    <div class="p-6 bg-slate-800/50 rounded-2xl border border-white/5 hover:border-yellow-500/30 transition group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider font-bold group-hover:text-yellow-400">Annual Savings</p>
                        <p class="text-3xl font-black text-white mt-2"><span id="res-savings" class="text-yellow-400">0</span></p>
                    </div>
                    <div class="p-6 bg-slate-800/50 rounded-2xl border border-white/5 hover:border-blue-500/30 transition group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider font-bold group-hover:text-blue-400">ROI Period</p>
                        <p class="text-3xl font-black text-white mt-2"><span id="res-payback" class="text-blue-400">0</span> <span class="text-sm text-slate-500 font-normal">yrs</span></p>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="glass-card p-8">
                    <h4 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <span class="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400"><i class="fas fa-clipboard-check"></i></span>
                        30-Day Action Plan
                    </h4>
                    <ul id="action-list" class="space-y-4"></ul>
                </div>

                <div class="glass-card p-8">
                    <h4 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <span class="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400"><i class="fas fa-solar-panel"></i></span>
                        Renewable Strategy
                    </h4>
                    <ul id="renewable-list" class="space-y-4"></ul>
                </div>
            </div>

            <div class="glass-card p-8">
                <h4 class="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    <i class="fas fa-lightbulb text-yellow-400"></i> Smart Efficiency Tips
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="tips-grid"></div>
            </div>
        </div>
    </section>

    <section id="estimators" class="py-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Investment <span class="text-gradient">Estimators</span></h2>
                <p class="text-slate-400">Calculate upfront costs and potential returns for renewable tech.</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="glass-card p-8 border-t-4 border-yellow-500 hover:shadow-yellow-500/10 group">
                    <div class="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center text-yellow-400 text-2xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fas fa-sun"></i>
                    </div>
                    <h3 class="font-bold text-white text-xl mb-4">Solar PV</h3>
                    <div class="space-y-4">
                        <input type="number" id="solarRoof" placeholder="Roof Size (sq ft)" value="500" class="w-full p-3 text-sm">
                        <button onclick="calcSolar()" class="glass-btn w-full py-3 rounded-lg text-sm border-yellow-500/30 hover:border-yellow-500">Calculate</button>
                        <div id="solar-res" class="hidden mt-4 p-4 bg-black/40 rounded-xl text-sm border border-white/5 space-y-2">
                            <div class="flex justify-between"><span class="text-slate-400">Est. Cost:</span> <b id="solar-cost" class="text-white"></b></div>
                            <div class="flex justify-between"><span class="text-slate-400">Yr Savings:</span> <b id="solar-save" class="text-emerald-400"></b></div>
                        </div>
                    </div>
                </div>

                <div class="glass-card p-8 border-t-4 border-blue-500 hover:shadow-blue-500/10 group">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-400 text-2xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fas fa-wind"></i>
                    </div>
                    <h3 class="font-bold text-white text-xl mb-4">Wind Turbine</h3>
                    <div class="space-y-4">
                        <input type="number" id="windSize" placeholder="Turbine Size (kW)" value="5" class="w-full p-3 text-sm">
                        <button onclick="calcWind()" class="glass-btn w-full py-3 rounded-lg text-sm border-blue-500/30 hover:border-blue-500">Calculate</button>
                        <div id="wind-res" class="hidden mt-4 p-4 bg-black/40 rounded-xl text-sm border border-white/5 space-y-2">
                            <div class="flex justify-between"><span class="text-slate-400">Est. Cost:</span> <b id="wind-cost" class="text-white"></b></div>
                            <div class="flex justify-between"><span class="text-slate-400">Generation:</span> <b id="wind-kwh" class="text-cyan-400"></b></div>
                        </div>
                    </div>
                </div>

                <div class="glass-card p-8 border-t-4 border-cyan-500 hover:shadow-cyan-500/10 group">
                    <div class="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 text-2xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fas fa-water"></i>
                    </div>
                    <h3 class="font-bold text-white text-xl mb-4">Micro Hydro</h3>
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-2">
                            <input type="number" id="hydroFlow" placeholder="Flow L/s" value="20" class="w-full p-3 text-sm">
                            <input type="number" id="hydroHead" placeholder="Head m" value="5" class="w-full p-3 text-sm">
                        </div>
                        <button onclick="calcHydro()" class="glass-btn w-full py-3 rounded-lg text-sm border-cyan-500/30 hover:border-cyan-500">Calculate</button>
                        <div id="hydro-res" class="hidden mt-4 p-4 bg-black/40 rounded-xl text-sm border border-white/5 space-y-2">
                            <div class="flex justify-between"><span class="text-slate-400">Size:</span> <b id="hydro-size" class="text-white"></b></div>
                            <div class="flex justify-between"><span class="text-slate-400">Est. Cost:</span> <b id="hydro-cost" class="text-cyan-400"></b></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <footer class="bg-black/80 backdrop-blur border-t border-white/10 pt-16 pb-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 text-center">
            <div class="flex justify-center items-center gap-3 mb-6">
                 <div class="w-8 h-8 bg-cyan-500 rounded-md flex items-center justify-center text-white"><i class="fas fa-leaf"></i></div>
                 <span class="font-bold text-2xl text-white">EcoGenius</span>
            </div>
            <p class="text-slate-500 mb-8 max-w-md mx-auto">Empowering homeowners and businesses to make data-driven decisions for a sustainable future.</p>
            <div class="flex justify-center gap-8 text-2xl text-slate-600 mb-12">
                <i class="fab fa-github hover:text-white cursor-pointer transition transform hover:-translate-y-1"></i>
                <i class="fab fa-twitter hover:text-cyan-400 cursor-pointer transition transform hover:-translate-y-1"></i>
                <i class="fab fa-linkedin hover:text-blue-500 cursor-pointer transition transform hover:-translate-y-1"></i>
            </div>
            <div class="border-t border-white/5 pt-8 text-sm text-slate-600">
                &copy; 2024 Eco-Genius. All rights reserved.
            </div>
        </div>
    </footer>

    <script>
        // --- RAIN EFFECT ---
        const canvas = document.getElementById('rainCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const bubbles = [];
        class Bubble {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height - canvas.height;
                this.size = Math.random() * 2 + 1;
                this.speedY = Math.random() * 1 + 0.5;
                this.opacity = Math.random() * 0.5 + 0.1;
            }
            update() {
                this.y += this.speedY;
                if (this.y > canvas.height) {
                    this.y = -10;
                    this.x = Math.random() * canvas.width;
                }
            }
            draw() {
                ctx.fillStyle = `rgba(165, 243, 252, ${this.opacity})`; // Cyan tint
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        function initRain() {
            for(let i=0; i<100; i++) bubbles.push(new Bubble());
        }
        function animateRain() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            bubbles.forEach(b => { b.update(); b.draw(); });
            requestAnimationFrame(animateRain);
        }
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
        initRain();
        animateRain();

        // --- DATA ---
        const citiesByState = {{ cities_by_state | tojson }};

        // --- MOBILE MENU ---
        function toggleMobileMenu() {
            const menu = document.getElementById('mobileMenu');
            menu.classList.toggle('hidden');
        }

        // --- MODAL LOGIC ---
        function showModal() {
            const modal = document.getElementById('errorModal');
            const content = document.getElementById('errorContent');
            modal.classList.remove('hidden');
            // Small delay for CSS transition
            setTimeout(() => {
                modal.classList.remove('opacity-0');
                content.classList.remove('scale-95');
                content.classList.add('scale-100');
            }, 10);
        }

        function closeModal() {
            const modal = document.getElementById('errorModal');
            const content = document.getElementById('errorContent');
            modal.classList.add('opacity-0');
            content.classList.remove('scale-100');
            content.classList.add('scale-95');
            setTimeout(() => modal.classList.add('hidden'), 300);
        }

        // --- MAP ---
        let map;
        function initMap() {
            map = L.map('map').setView([20, 0], 1);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CARTO'
            }).addTo(map);

            const coords = {
                "US": [37.09, -95.71], "IN": [20.59, 78.96], "DE": [51.16, 10.45],
                "FR": [46.22, 2.21], "BR": [-14.23, -51.92], "CA": [56.13, -106.34],
                "AU": [-25.27, 133.77], "JP": [36.20, 138.25], "GB": [55.37, -3.43]
            };
            
            for(const [code, pos] of Object.entries(coords)){
                L.circleMarker(pos, { color: '#06b6d4', radius: 6, fillOpacity: 0.8, fillColor: '#22d3ee' })
                  .addTo(map).bindPopup(code)
                  .on('click', () => {
                     document.getElementById('location').value = code;
                     handleLocationChange();
                  });
            }
        }

        // --- FORM LOGIC ---
        function scrollToCalc() {
            gsap.to(window, {duration: 1, scrollTo: "#calculator", ease: "power2.inOut"});
        }

        function handleLocationChange() {
            const loc = document.getElementById('location').value;
            const indiaFields = document.getElementById('india-fields');
            
            if(loc === 'IN') {
                indiaFields.classList.remove('hidden');
                gsap.from("#india-fields", {height: 0, opacity: 0, duration: 0.4});
            } else {
                indiaFields.classList.add('hidden');
            }
            
            fetchWeather(loc);
            fetchCarbonPrice(loc);
            
            // Map pan
            const coords = {
                "US": [37.09, -95.71], "IN": [20.59, 78.96], "DE": [51.16, 10.45],
                "FR": [46.22, 2.21], "BR": [-14.23, -51.92], "CA": [56.13, -106.34],
                "AU": [-25.27, 133.77], "JP": [36.20, 138.25], "GB": [55.37, -3.43]
            };
            if(coords[loc]) map.flyTo(coords[loc], 4);
        }

        function handleStateChange() {
            const state = document.getElementById('state').value;
            const citySelect = document.getElementById('city');
            const cityWrapper = document.getElementById('city-wrapper');
            citySelect.innerHTML = '<option value="">Select City</option>';
            if(citiesByState[state]) {
                cityWrapper.classList.remove('hidden');
                citiesByState[state].forEach(c => {
                   citySelect.innerHTML += `<option value="${c}">${c}</option>`;
                });
            } else { cityWrapper.classList.add('hidden'); }
        }

        function handleCityChange() {
            const city = document.getElementById('city').value;
            const townWrapper = document.getElementById('town-wrapper');
            if(city === 'Bidar') townWrapper.classList.remove('hidden');
            else townWrapper.classList.add('hidden');
        }

        function loadExample(loc, hrs, habits) {
            document.getElementById('location').value = loc;
            document.getElementById('daily_hours').value = hrs;
            document.getElementById('habits').value = habits;
            handleLocationChange();
            scrollToCalc();
        }

        // --- API ---
        async function fetchWeather(loc) {
            try {
                const res = await fetch(`/weather?location=${loc}`);
                const data = await res.json();
                if(data && data.temperature) {
                    const disp = document.getElementById('weatherDisplay');
                    disp.classList.remove('hidden');
                    document.getElementById('tempDisplay').innerText = `${data.temperature}°C`;
                    document.getElementById('weatherDesc').innerText = data.description;
                    document.getElementById('humidityDisplay').innerText = `${data.humidity}%`;
                    
                    // Icon logic
                    let icon = 'fa-cloud';
                    if(data.description.includes('Clear')) icon = 'fa-sun';
                    else if(data.description.includes('Rain')) icon = 'fa-cloud-rain';
                    document.getElementById('weatherIcon').className = `fas ${icon}`;
                }
            } catch(e) {}
        }

        async function fetchCarbonPrice(loc) {
            try {
                const res = await fetch('/carbon-price');
                const data = await res.json();
                // Client-side currency map for quick display update
                const currencyMap = {"US":"$","IN":"₹","DE":"€","GB":"£","JP":"¥","AU":"$","CA":"$","BR":"R$","FR":"€"};
                const sym = currencyMap[loc] || '$';
                // Simple conversion for display (backend does accurate one)
                const rate = loc === 'IN' ? 83 : (loc === 'DE' || loc === 'FR' ? 0.9 : 1);
                const val = data * rate;
                document.getElementById('carbonPriceDisplay').innerText = `Current Rate: ${sym}${val.toFixed(2)}/ton`;
            } catch(e) {}
        }

        // --- ANALYSIS ---
        async function analyze() {
            // Validation
            const habits = document.getElementById('habits').value.trim();
            const usage = document.getElementById('daily_hours').value;
            
            if(!habits || !usage) {
                showModal();
                return;
            }

            const btn = document.querySelector('button[onclick="analyze()"]');
            const originalHTML = btn.innerHTML;
            btn.innerHTML = `<i class="fas fa-circle-notch fa-spin"></i> Processing...`; btn.disabled = true;

            const payload = {
                location: document.getElementById('location').value,
                daily_hours: usage,
                habits: habits,
                state: document.getElementById('state').value,
                city: document.getElementById('city').value,
                town: document.getElementById('town').value
            };

            try {
                const res = await fetch('/analyze', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if(data.error) { alert(data.error); return; }

                const resultsSec = document.getElementById('results');
                resultsSec.classList.remove('hidden');
                
                // Update DOM
                document.getElementById('res-carbon').innerText = data.carbon_footprint_kg;
                document.getElementById('res-trees').innerText = data.trees_needed;
                document.getElementById('res-savings').innerText = data.annual_savings;
                document.getElementById('res-payback').innerText = data.payback_period;
                document.getElementById('habits-summary').innerText = data.habits_summary;

                document.getElementById('profile-tags').innerHTML = data.profile_tags.map(t => 
                    `<span class="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-xs font-bold text-cyan-300">${t}</span>`
                ).join('');

                document.getElementById('action-list').innerHTML = data.action_plan.map(i => 
                    `<li class="flex items-start gap-3 p-4 bg-slate-800/50 rounded-xl border border-white/5">
                        <i class="fas fa-check-circle text-emerald-400 mt-1"></i>
                        <span class="text-sm text-slate-300">${i}</span>
                     </li>`
                ).join('');

                document.getElementById('renewable-list').innerHTML = data.renewable_recommendations.map(i => 
                    `<li class="flex items-start gap-3 p-4 bg-slate-800/50 rounded-xl border border-white/5">
                        <i class="fas fa-bolt text-cyan-400 mt-1"></i>
                        <span class="text-sm text-slate-300">${i}</span>
                     </li>`
                ).join('');

                document.getElementById('tips-grid').innerHTML = data.efficiency_tips.map(tip => 
                    `<div class="p-4 bg-slate-800/50 rounded-xl text-sm text-slate-300 border-l-4 border-yellow-400">
                        ${tip}
                     </div>`
                ).join('');
                
                setTimeout(() => {
                    gsap.to(window, {duration: 1, scrollTo: "#results", ease: "power2.out"});
                    gsap.from("#results > div", {y: 30, opacity: 0, duration: 0.8, stagger: 0.1});
                }, 100);

            } catch(e) {
                console.error(e);
            } finally {
                btn.innerHTML = originalHTML; btn.disabled = false;
            }
        }

        // --- ESTIMATORS (With Correct Currency) ---
        async function calcSolar() {
            const loc = document.getElementById('location').value;
            const roof = document.getElementById('solarRoof').value;
            if(!roof) { alert("Enter roof size"); return; }
            
            const res = await fetch('/solar-cost', { 
                method: 'POST', headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({location: loc, roof_size_sqft: roof}) 
            });
            const data = await res.json();
            document.getElementById('solar-res').classList.remove('hidden');
            document.getElementById('solar-cost').innerText = data.total_cost;
            document.getElementById('solar-save').innerText = data.annual_savings;
        }

        async function calcWind() {
            const loc = document.getElementById('location').value;
            const size = document.getElementById('windSize').value;
            if(!size) { alert("Enter turbine size"); return; }

            const res = await fetch('/wind-estimate', { 
                method: 'POST', headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({location: loc, turbine_size_kw: size}) 
            });
            const data = await res.json();
            document.getElementById('wind-res').classList.remove('hidden');
            document.getElementById('wind-cost').innerText = data.total_cost;
            document.getElementById('wind-kwh').innerText = data.annual_energy_kwh;
        }

        async function calcHydro() {
            const loc = document.getElementById('location').value;
            const flow = document.getElementById('hydroFlow').value;
            const head = document.getElementById('hydroHead').value;
            if(!flow || !head) { alert("Enter flow and head"); return; }

            const res = await fetch('/hydro-estimate', { 
                method: 'POST', headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({location: loc, flow_rate_lps: flow, head_height_m: head}) 
            });
            const data = await res.json();
            document.getElementById('hydro-res').classList.remove('hidden');
            document.getElementById('hydro-cost').innerText = data.total_cost;
            document.getElementById('hydro-size').innerText = data.system_size_kw;
        }

        // Init
        window.onload = function() {
            initMap();
            fetchWeather('US');
            fetchCarbonPrice('US');
            gsap.from("#navbar", {y: -100, duration: 1, ease: "power2.out"});
        }
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                india_states=INDIA_STATES, 
                                cities_by_state=CITIES_BY_STATE, 
                                bidar_towns=BIDAR_TOWNS,
                                examples=EXAMPLES)

@app.route('/weather')
def weather_route():
    loc = request.args.get('location', 'US')
    return jsonify(get_current_weather(loc) or {})

@app.route('/carbon-price')
def price_route():
    return jsonify(CARBON_PRICE_DEFAULT)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    loc = data.get('location', 'US')
    habits = data.get('habits', '').lower()
    
    try:
        daily_hours = float(data.get('daily_hours', 0))
    except:
        return jsonify({"error": "Invalid hours"}), 400

    avg_load_kw = 0.5 
    profile_tags = [f"📍 {loc}"]
    
    if any(x in habits for x in ['ac', 'cooling', 'air con']):
        avg_load_kw += 1.5
        profile_tags.append("❄️ Heavy Cooling")
    if any(x in habits for x in ['heat', 'heater', 'winter']):
        avg_load_kw += 1.5
        profile_tags.append("🔥 Electric Heating")
    if any(x in habits for x in ['ev', 'tesla', 'car', 'vehicle']):
        avg_load_kw += 2.0
        profile_tags.append("🚗 EV Owner")
    if any(x in habits for x in ['office', 'wfh', 'computer', 'laptop']):
        avg_load_kw += 0.2
        profile_tags.append("💻 Remote Worker")
    
    monthly_kwh = daily_hours * 30 * avg_load_kw
    
    ci = CARBON_INTENSITY.get(loc, 450)
    carbon_kg = round((monthly_kwh * ci) / 1000, 2)
    trees = round(carbon_kg * 12 / 21)
    
    curr = CURRENCY_SYMBOL.get(loc, '$')
    rate = ELECTRICITY_RATE.get(loc, 0.15)
    
    annual_cost = monthly_kwh * 12 * rate
    potential_savings = annual_cost * 0.30 
    
    tips = []
    action_plan = []
    action_plan.append("Day 1: Install a smart energy monitor.")

    if "ac" in habits:
        tips.extend(random.sample(ENERGY_TIPS['ac'], 2))
        action_plan.append("Day 5: Service AC filters.")
    if "ev" in habits:
        tips.extend(random.sample(ENERGY_TIPS['ev'], 2))
        action_plan.append("Day 10: Schedule EV charging for off-peak.")
    
    while len(tips) < 4:
        tips.append(random.choice(ENERGY_TIPS['appliances'] + ENERGY_TIPS['lighting']))
    
    tips = list(set(tips))[:4] 

    renewables = []
    pot = RENEWABLE_POTENTIAL.get(loc, {"solar": "moderate", "wind": "low"})
    if pot['solar'] == 'excellent': renewables.append("☀️ Rooftop Solar: High potential.")
    
    town = data.get('town', '')
    if loc == "IN":
        action_plan.append("Day 15: Check 'PM Surya Ghar' scheme.")
        if town in BIDAR_TOWNS:
             renewables.insert(0, f"☀️ Bidar Specific: High solar irradiance detected.")
             profile_tags.append(f"📍 {town}")

    if len(action_plan) < 4: action_plan.append("Day 30: Review monthly bill.")

    summary = f"Based on {daily_hours}h daily usage and detected habits."

    return jsonify({
        "carbon_footprint_kg": carbon_kg,
        "trees_needed": trees,
        "annual_savings": f"{curr}{potential_savings:,.0f}",
        "payback_period": "3-5" if "solar" in str(renewables).lower() else "1-2",
        "action_plan": action_plan,
        "renewable_recommendations": renewables,
        "efficiency_tips": tips,
        "profile_tags": profile_tags,
        "habits_summary": summary
    })

# --- ESTIMATORS (With Localized Currency) ---
@app.route('/solar-cost', methods=['POST'])
def solar_cost():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    cost_per_watt = 1.0 if loc == 'IN' else 3.0 # Simplified
    total = float(d.get('roof_size_sqft',500)) * 15 * cost_per_watt 
    return jsonify({"total_cost": f"{curr}{total:,.0f}", "annual_savings": f"{curr}{total*0.15:,.0f}"})

@app.route('/wind-estimate', methods=['POST'])
def wind_estimate():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    cost = 1200 if loc == 'IN' else 3500
    kw = float(d.get('turbine_size_kw',5))
    return jsonify({"total_cost": f"{curr}{kw*cost:,.0f}", "annual_energy_kwh": f"{kw*24*365*0.25:,.0f}"})

@app.route('/hydro-estimate', methods=['POST'])
def hydro_estimate():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    kw = 9.81 * (float(d.get('flow_rate_lps',20))/1000) * float(d.get('head_height_m',5)) * 0.8
    cost_per_kw = 1500 if loc == 'IN' else 4000
    return jsonify({"system_size_kw": f"{kw:.2f}", "total_cost": f"{curr}{max(2000, kw*cost_per_kw):,.0f}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
