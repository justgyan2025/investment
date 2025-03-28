from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import json
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

# Firebase configuration
firebase_config = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID')
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html', firebase_config=firebase_config)

@app.route('/login')
def login():
    return render_template('login.html', firebase_config=firebase_config)

@app.route('/logout')
def logout():
    response = redirect(url_for('index'))
    response.delete_cookie('token')
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', firebase_config=firebase_config)

@app.route('/stocks')
@login_required
def stocks():
    return render_template('stocks.html', firebase_config=firebase_config)

@app.route('/mutual_funds')
@login_required
def mutual_funds():
    return render_template('mutual_funds.html', firebase_config=firebase_config)

@app.route('/insurance')
@login_required
def insurance():
    return render_template('insurance.html', firebase_config=firebase_config)

@app.route('/nps')
@login_required
def nps():
    return render_template('nps.html', firebase_config=firebase_config)

@app.route('/others')
@login_required
def others():
    return render_template('others.html', firebase_config=firebase_config)

@app.route('/api/stock/<symbol>')
def get_stock_details(symbol):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = f'https://www.google.com/finance/quote/{symbol}:NSE'
        response = requests.get(url, headers=headers)
        
        if not response.ok:
            return jsonify({'error': 'Failed to fetch stock data'}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get company name - it's in the div with class 'zzDege'
        company_name_elem = soup.select_one('div[class*="zzDege"]')
        if not company_name_elem:
            return jsonify({'error': 'Stock not found'}), 404
        company_name = company_name_elem.text.strip()
        
        # Get current price - it's in a div with class 'YMlKec fxKbKc'
        price_elem = soup.select_one('div[class*="YMlKec fxKbKc"]')
        if not price_elem:
            return jsonify({'error': 'Price data not found'}), 404
            
        # Clean up the price string (remove ₹ and convert to number)
        price_text = price_elem.text.strip()
        price = price_text.replace('₹', '').replace(',', '').strip()
        
        # Get price change and percentage - in divs with class 'P2Luy Ez2Ioe'
        changes = soup.select('div[class*="P2Luy Ez2Ioe"]')
        if changes and len(changes) >= 2:
            change = changes[0].text.strip()
            change_percent = changes[1].text.strip()
        else:
            change = '0'
            change_percent = '0%'

        stock_data = {
            'symbol': symbol,
            'name': company_name,
            'price': price,
            'change': change,
            'change_percent': change_percent
        }
        
        print(f"Fetched stock data: {stock_data}")  # Debug print
        return jsonify(stock_data)

    except requests.RequestException as e:
        print(f"Error fetching stock data: {str(e)}")
        return jsonify({'error': 'Failed to fetch stock data'}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/mutual_fund/<scheme_code>')
@login_required
def get_mutual_fund_info(scheme_code):
    try:
        url = f'https://api.mfapi.in/mf/{scheme_code}'
        response = requests.get(url)
        data = response.json()
        
        # Extract scheme name and current NAV
        scheme_name = data['meta']['scheme_name']
        current_nav = data['data'][0]['nav']
        
        return jsonify({
            'scheme_code': scheme_code,
            'scheme_name': scheme_name,
            'current_nav': current_nav
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nps/<scheme_code>')
@login_required
def get_nps_info(scheme_code):
    try:
        url = f'https://npsnav.in/api/detailed/{scheme_code}'
        response = requests.get(url)
        data = response.json()
        
        # Extract scheme name and current NAV
        scheme_name = data['scheme_name']
        current_nav = data['nav']
        
        return jsonify({
            'scheme_code': scheme_code,
            'scheme_name': scheme_name,
            'current_nav': current_nav
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 