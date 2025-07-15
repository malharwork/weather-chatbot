from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime, timedelta
import anthropic
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')

if CLAUDE_API_KEY:
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
else:
    claude_client = None
    print("Warning: CLAUDE_API_KEY not set. Chat functionality will be limited.")

INDIAN_LOCATIONS = {
    "Andhra Pradesh": {
        "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
        "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
        "Guntur": {"lat": 16.3067, "lon": 80.4365},
        "Nellore": {"lat": 14.4426, "lon": 79.9865},
        "Kurnool": {"lat": 15.8281, "lon": 78.0373},
        "Tirupati": {"lat": 13.6288, "lon": 79.4192},
        "Rajahmundry": {"lat": 17.0005, "lon": 81.8040},
        "Anantapur": {"lat": 14.6819, "lon": 77.6006},
        "Kadapa": {"lat": 14.4674, "lon": 78.8241},
        "Chittoor": {"lat": 13.2172, "lon": 79.1003}
    },
    "Arunachal Pradesh": {
        "Itanagar": {"lat": 27.0844, "lon": 93.6053},
        "Tawang": {"lat": 27.5860, "lon": 91.8687},
        "Ziro": {"lat": 27.5337, "lon": 93.8289},
        "Pasighat": {"lat": 28.0700, "lon": 95.3300},
        "Bomdila": {"lat": 27.2644, "lon": 92.4247},
        "Naharlagun": {"lat": 27.1039, "lon": 93.6947},
        "Tezu": {"lat": 27.9167, "lon": 96.1667},
        "Roing": {"lat": 28.1478, "lon": 95.8346}
    },
    "Assam": {
        "Guwahati": {"lat": 26.1445, "lon": 91.7362},
        "Silchar": {"lat": 24.8333, "lon": 92.7789},
        "Dibrugarh": {"lat": 27.4728, "lon": 94.9120},
        "Jorhat": {"lat": 26.7577, "lon": 94.2037},
        "Tezpur": {"lat": 26.6338, "lon": 92.8000},
        "Nagaon": {"lat": 26.3483, "lon": 92.6838},
        "Tinsukia": {"lat": 27.4886, "lon": 95.3558},
        "Bongaigaon": {"lat": 26.4835, "lon": 90.5562},
        "Dhubri": {"lat": 26.0112, "lon": 90.0000},
        "Karimganj": {"lat": 24.8649, "lon": 92.3619}
    },
    "Bihar": {
        "Patna": {"lat": 25.5941, "lon": 85.1376},
        "Gaya": {"lat": 24.7955, "lon": 85.0002},
        "Bhagalpur": {"lat": 25.2425, "lon": 86.9842},
        "Muzaffarpur": {"lat": 26.1209, "lon": 85.3647},
        "Darbhanga": {"lat": 26.1542, "lon": 85.8918},
        "Purnia": {"lat": 25.7771, "lon": 87.4753},
        "Munger": {"lat": 25.3708, "lon": 86.4734},
        "Bihar Sharif": {"lat": 25.1981, "lon": 85.5210},
        "Arrah": {"lat": 25.5565, "lon": 84.6630},
        "Begusarai": {"lat": 25.4182, "lon": 86.1272}
    },
    "Chhattisgarh": {
        "Raipur": {"lat": 21.2514, "lon": 81.6296},
        "Bhilai": {"lat": 21.1938, "lon": 81.3509},
        "Bilaspur": {"lat": 22.0796, "lon": 82.1391},
        "Korba": {"lat": 22.3595, "lon": 82.7501},
        "Durg": {"lat": 21.1904, "lon": 81.2849},
        "Raigarh": {"lat": 21.8974, "lon": 83.3952},
        "Jagdalpur": {"lat": 19.0868, "lon": 82.0313},
        "Rajnandgaon": {"lat": 21.0971, "lon": 81.0298},
        "Ambikapur": {"lat": 23.1179, "lon": 83.1953}
    },
    "Goa": {
        "Panaji": {"lat": 15.4909, "lon": 73.8278},
        "Margao": {"lat": 15.2832, "lon": 73.9862},
        "Vasco da Gama": {"lat": 15.3982, "lon": 73.8113},
        "Mapusa": {"lat": 15.5916, "lon": 73.8138},
        "Ponda": {"lat": 15.4027, "lon": 74.0078},
        "Bicholim": {"lat": 15.5881, "lon": 73.9480},
        "Curchorem": {"lat": 15.2685, "lon": 74.1086},
        "Sanquelim": {"lat": 15.5636, "lon": 73.9880}
    },
    "Gujarat": {
        "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
        "Surat": {"lat": 21.1702, "lon": 72.8311},
        "Vadodara": {"lat": 22.3072, "lon": 73.1812},
        "Rajkot": {"lat": 22.3039, "lon": 70.8022},
        "Bhavnagar": {"lat": 21.7645, "lon": 72.1519},
        "Jamnagar": {"lat": 22.4707, "lon": 70.0577},
        "Junagadh": {"lat": 21.5222, "lon": 70.4579},
        "Gandhinagar": {"lat": 23.2156, "lon": 72.6369},
        "Anand": {"lat": 22.5645, "lon": 72.9289},
        "Navsari": {"lat": 20.9467, "lon": 72.9520}
    },
    "Haryana": {
        "Gurugram": {"lat": 28.4595, "lon": 77.0266},
        "Faridabad": {"lat": 28.4089, "lon": 77.3178},
        "Panipat": {"lat": 29.3909, "lon": 76.9635},
        "Ambala": {"lat": 30.3782, "lon": 76.7767},
        "Yamunanagar": {"lat": 30.1290, "lon": 77.2674},
        "Rohtak": {"lat": 28.8955, "lon": 76.6066},
        "Hisar": {"lat": 29.1492, "lon": 75.7217},
        "Karnal": {"lat": 29.6857, "lon": 76.9905},
        "Sonipat": {"lat": 28.9931, "lon": 77.0151},
        "Panchkula": {"lat": 30.6942, "lon": 76.8606}
    },
    "Himachal Pradesh": {
        "Shimla": {"lat": 31.1048, "lon": 77.1734},
        "Manali": {"lat": 32.2396, "lon": 77.1887},
        "Dharamshala": {"lat": 32.2190, "lon": 76.3234},
        "Solan": {"lat": 30.9045, "lon": 77.0967},
        "Mandi": {"lat": 31.7081, "lon": 76.9313},
        "Kullu": {"lat": 31.9579, "lon": 77.1093},
        "Bilaspur": {"lat": 31.3309, "lon": 76.7619},
        "Hamirpur": {"lat": 31.6862, "lon": 76.5213},
        "Una": {"lat": 31.4685, "lon": 76.2708},
        "Chamba": {"lat": 32.5634, "lon": 76.1258}
    },
    "Jharkhand": {
        "Ranchi": {"lat": 23.3441, "lon": 85.3096},
        "Jamshedpur": {"lat": 22.8046, "lon": 86.2029},
        "Dhanbad": {"lat": 23.7957, "lon": 86.4304},
        "Bokaro": {"lat": 23.6693, "lon": 86.1511},
        "Hazaribagh": {"lat": 23.9925, "lon": 85.3637},
        "Deoghar": {"lat": 24.4871, "lon": 86.6952},
        "Giridih": {"lat": 24.1841, "lon": 86.3012},
        "Ramgarh": {"lat": 23.6275, "lon": 85.5222},
        "Dumka": {"lat": 24.2677, "lon": 87.2520},
        "Chaibasa": {"lat": 22.5529, "lon": 85.8314}
    },
    "Karnataka": {
        "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
        "Mysuru": {"lat": 12.2958, "lon": 76.6394},
        "Mangaluru": {"lat": 12.9141, "lon": 74.8560},
        "Hubli": {"lat": 15.3647, "lon": 75.1240},
        "Belgaum": {"lat": 15.8497, "lon": 74.4977},
        "Davanagere": {"lat": 14.4644, "lon": 75.9218},
        "Ballari": {"lat": 15.1394, "lon": 76.9214},
        "Vijayapura": {"lat": 16.8302, "lon": 75.7100},
        "Kalaburagi": {"lat": 17.3297, "lon": 76.8343},
        "Shimoga": {"lat": 13.9299, "lon": 75.5681}
    },
    "Kerala": {
        "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
        "Kochi": {"lat": 9.9312, "lon": 76.2673},
        "Kozhikode": {"lat": 11.2588, "lon": 75.7804},
        "Thrissur": {"lat": 10.5276, "lon": 76.2144},
        "Kollam": {"lat": 8.8932, "lon": 76.6141},
        "Palakkad": {"lat": 10.7867, "lon": 76.6548},
        "Alappuzha": {"lat": 9.4981, "lon": 76.3388},
        "Kannur": {"lat": 11.8745, "lon": 75.3704},
        "Kottayam": {"lat": 9.5916, "lon": 76.5222},
        "Malappuram": {"lat": 11.0510, "lon": 76.0711}
    },
    "Madhya Pradesh": {
        "Bhopal": {"lat": 23.2599, "lon": 77.4126},
        "Indore": {"lat": 22.7196, "lon": 75.8577},
        "Gwalior": {"lat": 26.2183, "lon": 78.1828},
        "Jabalpur": {"lat": 23.1815, "lon": 79.9864},
        "Ujjain": {"lat": 23.1765, "lon": 75.7885},
        "Sagar": {"lat": 23.8388, "lon": 78.7378},
        "Dewas": {"lat": 22.9676, "lon": 76.0534},
        "Satna": {"lat": 24.5839, "lon": 80.8322},
        "Ratlam": {"lat": 23.3315, "lon": 75.0367},
        "Rewa": {"lat": 24.5307, "lon": 81.3037}
    },
    "Maharashtra": {
        "Mumbai": {"lat": 19.0760, "lon": 72.8777},
        "Pune": {"lat": 18.5204, "lon": 73.8567},
        "Nagpur": {"lat": 21.1458, "lon": 79.0882},
        "Nashik": {"lat": 19.9975, "lon": 73.7898},
        "Thane": {"lat": 19.2183, "lon": 72.9781},
        "Aurangabad": {"lat": 19.8762, "lon": 75.3433},
        "Solapur": {"lat": 17.6599, "lon": 75.9064},
        "Amravati": {"lat": 20.9374, "lon": 77.7796},
        "Kolhapur": {"lat": 16.7050, "lon": 74.2433},
        "Nanded": {"lat": 19.1383, "lon": 77.3210}
    },
    "Manipur": {
        "Imphal": {"lat": 24.8170, "lon": 93.9368},
        "Thoubal": {"lat": 24.6321, "lon": 94.0119},
        "Bishnupur": {"lat": 24.6221, "lon": 93.7850},
        "Churachandpur": {"lat": 24.3293, "lon": 93.6820},
        "Ukhrul": {"lat": 25.0474, "lon": 94.3662},
        "Kakching": {"lat": 24.4951, "lon": 93.9851},
        "Chandel": {"lat": 24.3295, "lon": 94.0079},
        "Senapati": {"lat": 25.2751, "lon": 94.0203}
    },
    "Meghalaya": {
        "Shillong": {"lat": 25.5788, "lon": 91.8933},
        "Tura": {"lat": 25.5126, "lon": 90.2306},
        "Jowai": {"lat": 25.4512, "lon": 92.1987},
        "Nongpoh": {"lat": 25.8523, "lon": 91.8754},
        "Baghmara": {"lat": 25.1974, "lon": 90.6345},
        "Nongstoin": {"lat": 25.5173, "lon": 91.2655},
        "Williamnagar": {"lat": 25.4956, "lon": 90.6168},
        "Mairang": {"lat": 25.5602, "lon": 91.6367}
    },
    "Mizoram": {
        "Aizawl": {"lat": 23.7307, "lon": 92.7173},
        "Lunglei": {"lat": 22.8827, "lon": 92.7348},
        "Champhai": {"lat": 23.4704, "lon": 93.3256},
        "Serchhip": {"lat": 23.3031, "lon": 92.8477},
        "Kolasib": {"lat": 24.2232, "lon": 92.6778},
        "Lawngtlai": {"lat": 22.5301, "lon": 92.8934},
        "Mamit": {"lat": 23.9219, "lon": 92.4861},
        "Saiha": {"lat": 22.4823, "lon": 92.9748}
    },
    "Nagaland": {
        "Kohima": {"lat": 25.6751, "lon": 94.1086},
        "Dimapur": {"lat": 25.9042, "lon": 93.7261},
        "Mokokchung": {"lat": 26.3120, "lon": 94.5183},
        "Tuensang": {"lat": 26.2663, "lon": 94.8244},
        "Wokha": {"lat": 26.0968, "lon": 94.2580},
        "Mon": {"lat": 26.7190, "lon": 95.0335},
        "Zunheboto": {"lat": 26.0096, "lon": 94.5253},
        "Phek": {"lat": 25.6743, "lon": 94.4472}
    },
    "Odisha": {
        "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245},
        "Cuttack": {"lat": 20.4625, "lon": 85.8830},
        "Rourkela": {"lat": 22.2604, "lon": 84.8536},
        "Brahmapur": {"lat": 19.3150, "lon": 84.7941},
        "Sambalpur": {"lat": 21.4669, "lon": 83.9812},
        "Puri": {"lat": 19.8135, "lon": 85.8312},
        "Balasore": {"lat": 21.4942, "lon": 86.9335},
        "Baripada": {"lat": 21.9349, "lon": 86.7344},
        "Angul": {"lat": 20.8341, "lon": 85.1022},
        "Jharsuguda": {"lat": 21.8556, "lon": 84.0063}
    },
    "Punjab": {
        "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
        "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
        "Amritsar": {"lat": 31.6340, "lon": 74.8723},
        "Jalandhar": {"lat": 31.3260, "lon": 75.5762},
        "Patiala": {"lat": 30.3398, "lon": 76.3869},
        "Bathinda": {"lat": 30.2110, "lon": 74.9455},
        "Hoshiarpur": {"lat": 31.5327, "lon": 75.9115},
        "Mohali": {"lat": 30.7046, "lon": 76.7179},
        "Pathankot": {"lat": 32.2745, "lon": 75.6521},
        "Moga": {"lat": 30.8158, "lon": 75.1708}
    },
    "Rajasthan": {
        "Jaipur": {"lat": 26.9124, "lon": 75.7873},
        "Jodhpur": {"lat": 26.2389, "lon": 73.0243},
        "Udaipur": {"lat": 24.5854, "lon": 73.7125},
        "Kota": {"lat": 25.2138, "lon": 75.8648},
        "Bikaner": {"lat": 28.0229, "lon": 73.3119},
        "Ajmer": {"lat": 26.4499, "lon": 74.6399},
        "Bhilwara": {"lat": 25.3407, "lon": 74.6313},
        "Alwar": {"lat": 27.5530, "lon": 76.6346},
        "Sikar": {"lat": 27.6094, "lon": 75.1399},
        "Bharatpur": {"lat": 27.2152, "lon": 77.5030}
    },
    "Sikkim": {
        "Gangtok": {"lat": 27.3389, "lon": 88.6065},
        "Namchi": {"lat": 27.1659, "lon": 88.3637},
        "Gyalshing": {"lat": 27.2896, "lon": 88.2558},
        "Mangan": {"lat": 27.5098, "lon": 88.5298},
        "Rangpo": {"lat": 27.1757, "lon": 88.5305},
        "Singtam": {"lat": 27.2344, "lon": 88.4696},
        "Jorethang": {"lat": 27.1058, "lon": 88.3237},
        "Pelling": {"lat": 27.2971, "lon": 88.2379}
    },
    "Tamil Nadu": {
        "Chennai": {"lat": 13.0827, "lon": 80.2707},
        "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
        "Madurai": {"lat": 9.9252, "lon": 78.1198},
        "Tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
        "Salem": {"lat": 11.6643, "lon": 78.1460},
        "Tirunelveli": {"lat": 8.7139, "lon": 77.7567},
        "Erode": {"lat": 11.3410, "lon": 77.7172},
        "Vellore": {"lat": 12.9165, "lon": 79.1325},
        "Thanjavur": {"lat": 10.7870, "lon": 79.1378},
        "Thoothukudi": {"lat": 8.7642, "lon": 78.1348}
    },
    "Telangana": {
        "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
        "Warangal": {"lat": 17.9784, "lon": 79.6000},
        "Nizamabad": {"lat": 18.6725, "lon": 78.0880},
        "Karimnagar": {"lat": 18.4386, "lon": 79.1288},
        "Khammam": {"lat": 17.2473, "lon": 80.1514},
        "Ramagundam": {"lat": 18.7552, "lon": 79.4838},
        "Mahbubnagar": {"lat": 16.7374, "lon": 78.0092},
        "Nalgonda": {"lat": 17.0577, "lon": 79.2663},
        "Adilabad": {"lat": 19.6641, "lon": 78.5320},
        "Siddipet": {"lat": 18.1018, "lon": 78.8520}
    },
    "Tripura": {
        "Agartala": {"lat": 23.8315, "lon": 91.2868},
        "Udaipur": {"lat": 23.5355, "lon": 91.4828},
        "Dharmanagar": {"lat": 24.3745, "lon": 92.1746},
        "Kailashahar": {"lat": 24.3319, "lon": 92.0043},
        "Ambassa": {"lat": 23.9381, "lon": 91.8556},
        "Belonia": {"lat": 23.2523, "lon": 91.4554},
        "Melaghar": {"lat": 23.8862, "lon": 91.3168},
        "Khowai": {"lat": 24.0619, "lon": 91.6053}
    },
    "Uttar Pradesh": {
        "Lucknow": {"lat": 26.8467, "lon": 80.9462},
        "Kanpur": {"lat": 26.4499, "lon": 80.3319},
        "Agra": {"lat": 27.1767, "lon": 78.0081},
        "Varanasi": {"lat": 25.3176, "lon": 82.9739},
        "Meerut": {"lat": 28.9845, "lon": 77.7064},
        "Allahabad": {"lat": 25.4358, "lon": 81.8463},
        "Bareilly": {"lat": 28.3670, "lon": 79.4304},
        "Aligarh": {"lat": 27.8974, "lon": 78.0880},
        "Moradabad": {"lat": 28.8386, "lon": 78.7733},
        "Saharanpur": {"lat": 29.9680, "lon": 77.5552}
    },
    "Uttarakhand": {
        "Dehradun": {"lat": 30.3165, "lon": 78.0322},
        "Haridwar": {"lat": 29.9457, "lon": 78.1642},
        "Nainital": {"lat": 29.3803, "lon": 79.4636},
        "Haldwani": {"lat": 29.2183, "lon": 79.5130},
        "Rudrapur": {"lat": 28.9875, "lon": 79.3950},
        "Rishikesh": {"lat": 30.0869, "lon": 78.2676},
        "Roorkee": {"lat": 29.8543, "lon": 77.8880},
        "Kashipur": {"lat": 29.2104, "lon": 78.9619},
        "Almora": {"lat": 29.5971, "lon": 79.6591},
        "Pithoragarh": {"lat": 29.5829, "lon": 80.2182}
    },
    "West Bengal": {
        "Kolkata": {"lat": 22.5726, "lon": 88.3639},
        "Howrah": {"lat": 22.5958, "lon": 88.2636},
        "Durgapur": {"lat": 23.5204, "lon": 87.3119},
        "Siliguri": {"lat": 26.7271, "lon": 88.6395},
        "Asansol": {"lat": 23.6739, "lon": 86.9524},
        "Bardhaman": {"lat": 23.2406, "lon": 87.8615},
        "Malda": {"lat": 25.0109, "lon": 88.1411},
        "Baharampur": {"lat": 24.0945, "lon": 88.2502},
        "Kharagpur": {"lat": 22.3302, "lon": 87.3237},
        "Haldia": {"lat": 22.0667, "lon": 88.0698}
    },
}
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'bn': 'Bengali'
}

@app.route('/')
def index():
    return render_template('index.html', 
                         states=INDIAN_LOCATIONS, 
                         languages=SUPPORTED_LANGUAGES)

@app.route('/get_districts/<state>')
def get_districts(state):
    districts = list(INDIAN_LOCATIONS.get(state, {}).keys())
    return jsonify(districts)

@app.route('/get_weather', methods=['POST'])
def get_weather():
    data = request.json
    state = data.get('state')
    district = data.get('district')
    language = data.get('language', 'en')
    
    if not state or not district:
        return jsonify({'error': 'Please select both state and district'}), 400
    
    location = INDIAN_LOCATIONS.get(state, {}).get(district)
    if not location:
        return jsonify({'error': 'Location not found'}), 404
    
    weather_data = get_weather_data(location['lat'], location['lon'])
    
    if not weather_data:
        return jsonify({'error': 'Failed to fetch weather data'}), 500
    
    response = format_weather_response(weather_data, district, state)
    
    if language != 'en':
        try:
            response = translate_text(response, language)
        except Exception as e:
            print(f"Translation failed: {e}")
    
    return jsonify({'response': response})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    language = data.get('language', 'en')
    context = data.get('context', '')
    
    if language != 'en':
        message = translate_text(message, 'en')
    
    response = get_claude_response(message, context)
    
    if language != 'en':
        response = translate_text(response, language)
    
    return jsonify({'response': response})

def get_weather_data(lat, lon):
    """Fetch comprehensive weather data from Open-Meteo API (FREE, no key required)"""
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m',
        'hourly': 'temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max',
        'timezone': 'Asia/Kolkata',
        'forecast_days': 16  
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_weather_description(weather_code):
    """Convert Open-Meteo weather codes to descriptions"""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, "Unknown")

def format_weather_response(data, district, state):
    """Format Open-Meteo weather data into a readable response"""
    if not data:
        return "Sorry, I couldn't fetch the weather data. Please try again."
    
    current = data.get('current', {})
    daily = data.get('daily', {})
    hourly = data.get('hourly', {})
    
    response = f"**Current Weather in {district}, {state}:**\n"
    response += f"🌡️ Temperature: {current.get('temperature_2m', 'N/A')}°C\n"
    response += f"🤔 Feels like: {current.get('apparent_temperature', 'N/A')}°C\n"
    response += f"☁️ Condition: {get_weather_description(current.get('weather_code', 0))}\n"
    response += f"💧 Humidity: {current.get('relative_humidity_2m', 'N/A')}%\n"
    response += f"🌧️ Precipitation: {current.get('precipitation', 0)} mm\n"
    response += f"💨 Wind Speed: {current.get('wind_speed_10m', 'N/A')} km/h\n\n"
    
    if daily.get('temperature_2m_max') and daily.get('temperature_2m_min'):
        response += f"**Today's Range:** {daily['temperature_2m_min'][0]}°C - {daily['temperature_2m_max'][0]}°C\n"
        if daily.get('sunrise') and daily.get('sunset'):
            sunrise = datetime.fromisoformat(daily['sunrise'][0]).strftime('%I:%M %p')
            sunset = datetime.fromisoformat(daily['sunset'][0]).strftime('%I:%M %p')
            response += f"🌅 Sunrise: {sunrise} | 🌇 Sunset: {sunset}\n\n"
    
    response += "**Next 24 Hours:**\n"
    for i in range(0, min(24, len(hourly['time'])), 6):  # Every 6 hours
        time = datetime.fromisoformat(hourly['time'][i]).strftime('%I %p')
        temp = hourly['temperature_2m'][i]
        rain_prob = hourly.get('precipitation_probability', [0] * len(hourly['time']))[i]
        response += f"{time}: {temp}°C, {rain_prob}% rain chance\n"
    
    # 14-day forecast
    response += "\n**14-Day Forecast:**\n"
    for i in range(1, min(15, len(daily['time']))):  # Next 14 days
        date = datetime.fromisoformat(daily['time'][i])
        day_name = date.strftime('%a, %b %d')
        max_temp = daily['temperature_2m_max'][i]
        min_temp = daily['temperature_2m_min'][i]
        weather = get_weather_description(daily['weather_code'][i])
        rain = daily['precipitation_sum'][i]
        rain_prob = daily['precipitation_probability_max'][i]
        
        response += f"\n**{day_name}**: {weather}\n"
        response += f"   🌡️ {min_temp}°C - {max_temp}°C"
        if rain > 0:
            response += f" | 🌧️ {rain:.1f}mm ({rain_prob}% chance)"
        response += "\n"
    
    # Weather alerts/suggestions
    response += "\n**💡 Tips:**\n"
    current_temp = current.get('temperature_2m', 25)
    if current_temp > 35:
        response += "- 🥵 Very hot! Stay hydrated and avoid sun exposure\n"
    elif current_temp > 30:
        response += "- ☀️ Hot weather - wear light clothing\n"
    elif current_temp < 15:
        response += "- 🧥 Cool weather - carry a jacket\n"
    
    if current.get('precipitation', 0) > 0 or any(daily['precipitation_probability_max'][:3]) > 60:
        response += "- ☔ Rain expected - carry an umbrella\n"
    
    return response

def get_claude_response(message, context=""):
    """Get response from Claude API"""
    if not claude_client:
        return "Chat service is not configured. Please set up your Claude API key."
    
    try:
        system_prompt = """You are a helpful weather assistant for India. 
        You can answer questions about weather, climate, and provide weather-related advice.
        Be friendly and informative. If asked about specific weather data, 
        remind users to use the weather lookup feature for accurate information."""
        
        full_context = f"{context}\n\nUser: {message}" if context else message
        
        response = claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=500,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": full_context}
            ]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Error with Claude API: {e}")
        return "I'm having trouble connecting to the chat service. Please try again."

def translate_text(text, target_language):
    """Translate text to target language using deep-translator"""
    try:
        if target_language == 'en':
            return text
        
        language_map = {
            'hi': 'hindi',
            'ta': 'tamil',
            'te': 'telugu',
            'kn': 'kannada',
            'ml': 'malayalam',
            'mr': 'marathi',
            'gu': 'gujarati',
            'bn': 'bengali'
        }
        
        target_lang = language_map.get(target_language, target_language)
        translator = GoogleTranslator(source='english', target=target_lang)
        
        if len(text) > 4500:
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            for chunk in chunks:
                translated_chunks.append(translator.translate(chunk))
            return ' '.join(translated_chunks)
        else:
            return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  

if __name__ == '__main__':
    # Check if Claude API key is set (optional for chat features)
    if not CLAUDE_API_KEY:
        print("\n⚠️  WARNING: CLAUDE_API_KEY not found in environment variables!")
        print("Chat functionality will be limited without Claude API key.")
        print("Get your API key from: https://console.anthropic.com/")
        print("\n✅ Weather functionality will work perfectly without any API key!\n")
    
    print("🌤️  Starting Indian Weather Chatbot...")
    print("📍 Using Open-Meteo API (FREE - No API key required!)")
    print("📊 Features: 16-day forecast, hourly data, current conditions")
    print("🌐 Access at: http://localhost:5000\n")
    
    app.run(debug=True, port=5000)
