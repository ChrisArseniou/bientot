from queue import Full
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
import threading
import random
import time

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate('firebase_adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore collections
USERS_COLLECTION = 'users'
DATES_COLLECTION = 'dates'

# Helper function to generate a unique ID
def generate_id():
    return firestore.client().collection(USERS_COLLECTION).document().id

# Health Check Endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'success', 'message': 'Server is up and running!'}), 200



# 1. User Authorization (Sign-up / Login) - tested
@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({'error': 'Missing email, password, or name'}), 400

    try:
        # Create a new Firebase Authentication user
        user = auth.create_user(email=email, password=password, display_name=name)
        user_data = {
            'user_id': user.uid,
            'name': name,
            'email': email,
            'bio': '',
            'age': None,
            'gender': '',
            'interests': [],
            'created_at': firestore.SERVER_TIMESTAMP,
        }
        db.collection(USERS_COLLECTION).document(user.uid).set(user_data)
        return jsonify({'message': 'User registered successfully', 'user_id': user.uid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# tested
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    try:
        user = auth.get_user_by_email(email)
        return jsonify({'message': 'User logged in successfully', 'user_id': user.uid}), 200
    except Exception as e:
        return jsonify({'error': 'User not found or incorrect credentials'}), 404

# 2. CRUD for User Information - tested
@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_doc = db.collection(USERS_COLLECTION).document(user_id).get()
        if user_doc.exists:
            return jsonify(user_doc.to_dict()), 200
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    try:
        db.collection(USERS_COLLECTION).document(user_id).update(data)
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        db.collection(USERS_COLLECTION).document(user_id).delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 3. Background Service to Suggest Dates
def suggest_dates():
    while True:
        users = db.collection(USERS_COLLECTION).stream()

        #if(len(users == 0)):
        #    return
        '''
        user_list = [user.to_dict() for user in users]

        if len(user_list) > 1:
             user_a = random.choice(user_list)
             user_b = random.choice(user_list)
            
             if user_a['user_id'] != user_b['user_id']:
                date_suggestion = {
                    'date_id' : generate_id(),
                     'user_a_id': user_a['user_id'],
                     'user_b_id': user_b['user_id'],
                     'status': 'suggested',
                     'timestamp': firestore.SERVER_TIMESTAMP
                }
                db.collection(DATES_COLLECTION).add(date_suggestion)
        '''
        time.sleep(3600)  # Run every 60 seconds

threading.Thread(target=suggest_dates, daemon=True).start()


# 4. CRUD for Suggested Dates 

@app.route('/dates/suggested/<sugested_date_id>', methods=['GET'])
def get_date(sugested_date_id):
    try:
        date_doc = db.collection(DATES_COLLECTION).document(sugested_date_id).get()
        if date_doc.exists:
            return jsonify(date_doc.to_dict()), 200
        return jsonify({'error': 'Date not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dates/suggested/<sugested_date_id>', methods=['PUT'])
def update_date(sugested_date_id):
    data = request.json
    try:
        db.collection(DATES_COLLECTION).document(sugested_date_id).update(data)
        return jsonify({'message': 'Date updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dates/suggested/<sugested_date_id>', methods=['DELETE'])
def delete_date(sugested_date_id):
    try:
        db.collection(DATES_COLLECTION).document(sugested_date_id).delete()
        return jsonify({'message': 'Date deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    
# 5. Functionality for Accepted/Declined Dates 
# The idea here is that when a used decides to continue with a date, we change the status to accepted, and when the user declines a date we change the status to decline

# Accept a Suggested Date (Change status to "accepted")
@app.route('/dates/accept/<date_id>', methods=['POST'])
def accept_suggested_date(date_id):
    try:
        # Reference the suggested date
        date_ref = db.collection(DATES_COLLECTION).document(date_id)
        date_doc = date_ref.get()
        
        if not date_doc.exists:
            return jsonify({'status': 'error', 'message': 'Date not found'}), 404
        
        # Update the status to "accepted"
        date_ref.update({'status': 'accepted'})
        
        return jsonify({'status': 'success', 'message': 'Date accepted successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    

# Decline a Suggested Date (Change status to "declined")
@app.route('/dates/decline/<date_id>', methods=['POST'])
def decline_suggested_date(date_id):
    try:
        # Reference the suggested date
        date_ref = db.collection(DATES_COLLECTION).document(date_id)
        date_doc = date_ref.get()
        
        if not date_doc.exists:
            return jsonify({'status': 'error', 'message': 'Date not found'}), 404
        
        # Update the status to "declined"
        date_ref.update({'status': 'declined'})
        
        return jsonify({'status': 'success', 'message': 'Date declined successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Get Dates by Status for a Specific User
@app.route('/dates/user/<user_id>/<status>', methods=['GET'])
def get_dates_by_status(user_id, status):
    try:
        dates_ref = db.collection(DATES_COLLECTION)
        dates_query = dates_ref.where('status', '==', status).where('user_a_id', '==', user_id).stream()
        dates_query += dates_ref.where('status', '==', status).where('user_b_id', '==', user_id).stream()
        
        dates_list = [date.to_dict() for date in dates_query]
        
        if dates_list:
            return jsonify({'status': 'success', 'dates': dates_list}), 200
        else:
            return jsonify({'status': 'success', 'message': f'No {status} dates found'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# Get All Dates by User ID
@app.route('/dates/<user_id>', methods=['GET'])
def get_dates_by_user_id(user_id):
    try:
        # Query Firestore to find dates involving the given user
        dates_ref = db.collection(DATES_COLLECTION)
        suggested_dates = dates_ref.where('user_a_id', '==', user_id).stream()
        suggested_dates += dates_ref.where('user_b_id', '==', user_id).stream()
        
        suggestions = []
        for date in suggested_dates:
            suggestions.append(date.to_dict())
        
        # Return the list of suggested dates
        if suggestions:
            return jsonify({'status': 'success', 'dates': suggestions}), 200
        else:
            return jsonify({'status': 'success', 'message': 'No suggested dates found'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500










if __name__ == '__main__':
    app.run(debug=True)