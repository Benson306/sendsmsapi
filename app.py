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
    return str(phone)

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
                df['contacts'] = df['contacts'].drop_duplicates()

                # Format phone numbers to international format
                df['contacts'] = df['contacts'].apply(format_phone_number)

                # Filter out non-string values (e.g., integers) that couldn't be formatted
                df['contacts'] = df['contacts'].astype(str)
               
                # Get unique contacts
                contacts = df['contacts'].tolist()
                
                # Send SMS to unique contacts
                message = f"Bei ya kununua mahindi leo ni {figure}"

                try:
                    sms.send(message, contacts)
                except Exception as e:
                    print(f"Failed to send SMS: {str(e)}")
                # for contact in contacts:
                #     try:
                #         print(contact)
                #         #sms.send(message, [contact])
                #     except Exception as e:
                #         # Handle exception (e.g., log error)
                #         print(f"Failed to send SMS to {contact}: {str(e)}")
                
                return jsonify({'message': 'SMS sent successfully'})
            
            else:
                return jsonify({'error': 'Column "contacts" not found in the Excel file'})
        
        except Exception as e:
            print(f'Error processing the file: {str(e)}')
            return jsonify({'error': f'Error processing the file: {str(e)}'}) 
    
    else:
        return jsonify({'error': 'Invalid file format. Please upload an Excel file (.xlsx)'})

if __name__ == '__main__':
    app.run(debug=True)
