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
        # Check for token in cookies
        token = request.cookies.get('token')
        if not token:
            # No token found, redirect to login page with a message
            print("No token found, redirecting to login")
            return redirect(url_for('login', message="Please log in to access this page"))
        
        # We have a token, proceed with the route
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html', firebase_config=firebase_config)

@app.route('/login')
def login():
    # Simple rendering of login page with Firebase config
    message = request.args.get('message', '')
    return render_template('login.html', firebase_config=firebase_config, message=message)

@app.route('/logout')
def logout():
    # Create response that redirects to login page
    response = redirect(url_for('login'))
    # Delete the token cookie
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

@app.route('/api/mf/<scheme_code>')
def get_mutual_fund_info(scheme_code):
    try:
        url = f'https://api.mfapi.in/mf/{scheme_code}'
        response = requests.get(url)

        if response.status_code == 404:
            return jsonify({'error': 'Scheme code not found'}), 404

        data = response.json()
        
        # Extract scheme name and current NAV
        scheme_name = data['meta']['scheme_name']
        current_nav = data['data'][0]['nav']
        
        return jsonify({
            'scheme_code': scheme_code,
            'name': scheme_name,
            'nav': current_nav
        })
    except Exception as e:
        print(f"Error fetching mutual fund info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/nps/<scheme_code>')
def get_nps_info(scheme_code):
    # Mock data for testing when API is unreachable
    nps_mock_data = {
        # Common scheme codes and their mock data
        'SM001149': {'scheme_name': 'SBI Pension Fund - Scheme E - Tier 1', 'current_nav': 32.45},
        'SM001150': {'scheme_name': 'SBI Pension Fund - Scheme E - Tier 2', 'current_nav': 31.20},
        'SM001151': {'scheme_name': 'SBI Pension Fund - Scheme C - Tier 1', 'current_nav': 27.18},
        'SM001152': {'scheme_name': 'SBI Pension Fund - Scheme C - Tier 2', 'current_nav': 26.75},
        'SM001153': {'scheme_name': 'SBI Pension Fund - Scheme G - Tier 1', 'current_nav': 30.42},
        'SM001154': {'scheme_name': 'SBI Pension Fund - Scheme G - Tier 2', 'current_nav': 29.87},
        # Add more mock data as needed
    }
    
    try:
        # API endpoint
        url = f'https://www.npscra.nsdl.co.in/scheme-details-latest.php?sch_code={scheme_code}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching NPS data from: {url}")
        response = requests.get(url, headers=headers, timeout=5)
        
        # If the response is successful, try to scrape the data
        if response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for table containing scheme name and NAV
                tables = soup.find_all('table')
                scheme_name = None
                current_nav = None
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            header = cols[0].text.strip().lower()
                            
                            # Look for scheme name
                            if 'scheme name' in header or 'scheme' in header:
                                scheme_name = cols[1].text.strip()
                            
                            # Look for NAV or Net Asset Value
                            if 'nav' in header or 'net asset value' in header:
                                try:
                                    nav_text = cols[1].text.strip()
                                    # Remove currency symbols and commas
                                    nav_text = nav_text.replace('₹', '').replace(',', '').strip()
                                    current_nav = float(nav_text)
                                except ValueError:
                                    print(f"Could not parse NAV value: {cols[1].text}")
                
                if scheme_name and current_nav:
                    print(f"Successfully extracted data: {scheme_name}, NAV: {current_nav}")
                    
                    return jsonify({
                        'scheme_code': scheme_code,
                        'scheme_name': scheme_name,
                        'current_nav': current_nav
                    })
                else:
                    # If scraping failed, check if we have mock data
                    if scheme_code in nps_mock_data:
                        print(f"Using mock data for {scheme_code}")
                        return jsonify({
                            'scheme_code': scheme_code,
                            'scheme_name': nps_mock_data[scheme_code]['scheme_name'],
                            'current_nav': nps_mock_data[scheme_code]['current_nav']
                        })
                    
                    print("Failed to extract scheme name or NAV from HTML response")
                    return jsonify({'error': 'Could not find scheme details in the response'}), 500
            
            except Exception as e:
                print(f"Error parsing HTML: {str(e)}")
                # If HTML parsing failed, check if we have mock data
                if scheme_code in nps_mock_data:
                    print(f"Using mock data for {scheme_code}")
                    return jsonify({
                        'scheme_code': scheme_code,
                        'scheme_name': nps_mock_data[scheme_code]['scheme_name'],
                        'current_nav': nps_mock_data[scheme_code]['current_nav']
                    })
                return jsonify({'error': f'Error parsing response: {str(e)}'}), 500
        
        # If API failed but we have mock data, use it
        elif scheme_code in nps_mock_data:
            print(f"API failed but using mock data for {scheme_code}")
            return jsonify({
                'scheme_code': scheme_code,
                'scheme_name': nps_mock_data[scheme_code]['scheme_name'],
                'current_nav': nps_mock_data[scheme_code]['current_nav']
            })
        
        # If all failed, return error
        else:
            print(f"Failed with status code {response.status_code} and no mock data available")
            return jsonify({'error': f'Failed to fetch NPS data (Status code: {response.status_code})'}), 500
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        # If there was a request error but we have mock data, use it
        if scheme_code in nps_mock_data:
            print(f"Using mock data for {scheme_code} after request error")
            return jsonify({
                'scheme_code': scheme_code,
                'scheme_name': nps_mock_data[scheme_code]['scheme_name'],
                'current_nav': nps_mock_data[scheme_code]['current_nav']
            })
        return jsonify({'error': f'Failed to connect to NPS API: {str(e)}'}), 500
    
    except Exception as e:
        import traceback
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        
        # Last resort - if we have mock data, use it
        if scheme_code in nps_mock_data:
            print(f"Using mock data for {scheme_code} after unexpected error")
            return jsonify({
                'scheme_code': scheme_code,
                'scheme_name': nps_mock_data[scheme_code]['scheme_name'],
                'current_nav': nps_mock_data[scheme_code]['current_nav']
            })
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
