from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import pandas as pd
import africastalking
import os
import pip
pip.main(["install", "openpyxl"])

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Configure Africa's Talking API
username = os.getenv("AFRICASTALKING_USERNAME")
api_key = os.getenv("API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def format_phone_number(phone):
    #import pdb; pdb.set_trace()
    if isinstance(phone, int):
        if str(phone).startswith('+2547'):  # Do not modify numbers starting with '+2547'
            return phone
        elif str(phone).startswith('07') and len(str(phone)) == 10:  # Assuming the phone number length is 10
            return '+2547' + str(phone)[2:]  # Replace '07' with '+2547'
        elif str(phone).startswith('01') and len(str(phone)) == 10:  # Assuming the phone number length is 10
            return '+2541' + str(phone)[2:]  # Replace '01' with '+2541'
        elif str(phone).startswith('7') and len(str(phone)) == 9:  # Assuming the phone number length is 9
            return '+254' + str(phone)  # Replace leading '7' with '+254'
        elif str(phone).startswith('1') and len(str(phone)) == 9:  # Assuming the phone number length is 9
            return '+254' + str(phone)  # Replace leading '7' with '+254'
    return str(phone)

@app.route('/', methods=[''])
@cross_origin
def home():
    return jsonify({'Home':'Welcome'})

@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    figure = request.form.get('amount')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and file.filename.endswith('.xlsx'):
        try:
            # Load Excel file into pandas DataFrame
            df = pd.read_excel(file, sheet_name=0)
            
            # Check if 'contacts' column exists
            if 'contacts' in df.columns:
                # Remove duplicates from 'contacts' column
                df.drop_duplicates(subset='contacts', keep='first', inplace=True)


                # Format phone numbers to international format
                df['contacts'] = df['contacts'].apply(format_phone_number)

                # Filter out non-string values (e.g., integers) that couldn't be formatted
                df['contacts'] = df['contacts'].astype(str)
               
                # Get unique contacts
                contacts = df['contacts'].tolist()
                
                # Send SMS to unique contacts
                message = "Habari wakulima, \n"
                message += f"Karibu! Tuna furaha kuwajulisha kuwa bei ya kununua mahindi ni {figure} Ksh kwa gunia la kilo 90 lenye unyevu wa 13%. Kwa maelezo zaidi, tafadhali wasiliana nasi kupitia nambari 0714931331.\n"
                message += "Shukrani \n"
                message += "TALLAM'S GENERAL STORES"

                try:
                    response = sms.send(message, contacts)
                    print(response)  # Log the response to check if the SMS was sent successfully
                    return jsonify({'message': 'SMS sent successfully'}), 200
                except Exception as e:
                    print(f"Failed to send SMS: {str(e)}")
                    return jsonify({'error': f'Failed to send SMS: {str(e)}'}), 500
            
            else:
                return jsonify({'error': 'Column "contacts" not found in the Excel file'}), 400
        
        except Exception as e:
            print(f'Error processing the file: {str(e)}')
            return jsonify({'error': f'Error processing the file: {str(e)}'}), 500
    
    else:
        return jsonify({'error': 'Invalid file format. Please upload an Excel file (.xlsx)'}), 400

if __name__ == '__main__':
    app.run(debug=True)
