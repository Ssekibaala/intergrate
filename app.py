import requests
import time
import logging
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Replace these with your actual credentials
CLIENT_ID = 'teletrac.services.integrate'
CLIENT_SECRET = '84snk3xtPCDNPNQX'
USERNAME = 'brian.s@teletracfleets.com'
PASSWORD = 'Gloriamaria123.'
SCOPE = 'offline_access MiX.Integrate'
TOKEN_URL = 'https://identity.za.mixtelematics.com/core/connect/token'

# Global variables for caching the token
access_token_cache = None
token_expiry_time = None

# Function to get access token
def get_access_token():
    global access_token_cache, token_expiry_time

    # Check if cached token is still valid
    if access_token_cache and token_expiry_time and time.time() < token_expiry_time:
        return access_token_cache

    body = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'scope': SCOPE
    }
    auth = (CLIENT_ID, CLIENT_SECRET)

    try:
        response = requests.post(TOKEN_URL, data=body, auth=auth)
        response.raise_for_status()  # Raise an error for bad responses
        access_token_cache = response.json().get('access_token')
        token_expiry_time = time.time() + 3600  # Set expiry to 1 hour from now
        return access_token_cache
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token: {str(e)}")
        return None

# Helper function to handle API requests
def make_api_request(url, headers, payload=None):
    try:
        response = requests.post(url, headers=headers, json=payload) if payload else requests.get(url, headers=headers)
        response.raise_for_status()  # Raise error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        return {"error": str(e)}

# Endpoint 1: Get list of organisations
@app.route('/organisations', methods=['GET'])
def get_organisations():
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    url = "https://integrate.za.mixtelematics.com/api/organisationgroups"
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers)
        return jsonify(response.json()) if response.status_code == 200 else jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint 2: Get assets for multiple organisations
@app.route('/assets', methods=['GET'])
def get_assets():
    org_ids = request.args.get('organisationIds')
    if not org_ids:
        return jsonify({"error": "organisationIds parameter is required"}), 400

    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}'}
    all_assets = []

    for i, org_id in enumerate(org_ids.split(',')):
        if i > 0:
            time.sleep(30)
        url = f"https://integrate.za.mixtelematics.com/api/assets/group/{org_id}"
        all_assets.append({org_id: make_api_request(url, headers)})

    return jsonify(all_assets)

# Endpoint 3: Get drivers for multiple organisations
@app.route('/drivers', methods=['GET'])
def get_drivers():
    org_ids = request.args.get('organisationIds')
    if not org_ids:
        return jsonify({"error": "organisationIds parameter is required"}), 400

    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}'}
    all_drivers = []

    for i, org_id in enumerate(org_ids.split(',')):
        if i > 0:
            time.sleep(30)
        url = f"https://integrate.za.mixtelematics.com/api/drivers/organisation/{org_id}"
        all_drivers.append({org_id: make_api_request(url, headers)})

    return jsonify(all_drivers)

# Endpoint 4: Get events for multiple organisations
@app.route('/events', methods=['GET'])
def get_events():
    org_ids = request.args.get('organisationIds')
    if not org_ids:
        return jsonify({"error": "organisationIds parameter is required"}), 400

    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}'}
    all_events = []

    for i, org_id in enumerate(org_ids.split(',')):
        if i > 0:
            time.sleep(30)
        url = f"https://integrate.za.mixtelematics.com/api/libraryevents/organisation/{org_id}"
        all_events.append({org_id: make_api_request(url, headers)})

    return jsonify(all_events)

# Endpoint 5: Get positions for multiple organisations
@app.route('/positions', methods=['POST'])
def get_positions():
    data = request.json
    org_ids = data.get('organisationIds')  # Get the list of organisationIds

    if not org_ids:
        return jsonify({"error": "organisationIds parameter is required"}), 400

    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    url = "https://integrate.za.mixtelematics.com/api/positions/groups/latest/1"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    all_positions = []  # List to store positions for all organisations

    for i, org_id in enumerate(org_ids):
        if i > 0:
            time.sleep(30)  # Delay between requests after the first one

        # Payload must be a simple JSON array containing the organisationId
        payload = [org_id]

        # Log request for debugging
        logging.debug(f"Request URL: {url}, Payload: {payload}")

        try:
            # Make the request to the API
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                all_positions.append({org_id: response.json()})  # Append the response data to all_positions
            else:
                all_positions.append({org_id: {"error": response.text}})  # Append the error message for this org_id

        except Exception as e:
            all_positions.append({org_id: {"error": str(e)}})  # Append the exception message for this org_id

    return jsonify(all_positions), 200


# 6. Retrieves trips for multiple organisations by date range, entity type, and subtrips option
@app.route('/trips', methods=['POST'])
def get_trips_by_entitytype():
    data = request.json
    organisation_ids = data.get('organisationIds')
    from_date = data.get('fromDate')
    to_date = data.get('toDate')
    include_subtrips = data.get('includeSubtrips', False)
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    all_trips = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(35)  # Adding a delay between API calls

        url = f"https://integrate.za.mixtelematics.com/api/trips/groups/from/{from_date}/to/{to_date}/entitytype/Asset?includeSubtrips={str(include_subtrips).lower()}"
        payload = [org_id]
        all_trips.append({org_id: make_api_request(url, headers, payload)})

    return jsonify(all_trips)



# 7. Retrieves positions for multiple organisations for the given date/time range
@app.route('/positions_date_range', methods=['POST'])
def get_positions_date_range():
    data = request.json
    organisation_ids = data.get('organisationIds')
    from_date = data.get('fromDate')
    to_date = data.get('toDate')
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    all_positions = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(30)  # Adding a delay between API calls
        url = f"https://integrate.za.mixtelematics.com/api/positions/groups/from/{from_date}/to/{to_date}"
        payload = [org_id]
        all_positions.append({org_id: make_api_request(url, headers, payload)})

    return jsonify(all_positions)

# 8. Retrieves events created since a specific timestamp for multiple organisations
@app.route('/events_since', methods=['POST'])
def get_events_since():
    data = request.json
    organisation_ids = data.get('organisationIds')
    since_token = data.get('sinceToken', 'NEW')  # Default to 'NEW'
    quantity = data.get('quantity', 100)  # Default to 100
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}'}
    all_events = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(30)  # Adding a delay between API calls

        url = f"https://integrate.za.mixtelematics.com/api/events/groups/createdsince/organisation/{org_id}/sincetoken/{since_token}/quantity/{quantity}"
        response = make_api_request(url, headers, {})
        all_events.append({org_id: response})

    return jsonify(all_events)

# 9. Retrieves filtered events created since a specific timestamp for multiple organisations
@app.route('/events_since_filtered', methods=['POST'])
def get_events_since_filtered():
    data = request.json
    organisation_ids = data.get('organisationIds')
    since_token = data.get('sinceToken', 'NEW')
    quantity = data.get('quantity', 100)
    event_type_ids = data.get('eventTypeIds', [])
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    all_filtered_events = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(30)  # Adding a delay between API calls

        url = f"https://integrate.za.mixtelematics.com/api/events/groups/createdsince/organisation/{org_id}/sincetoken/{since_token}/quantity/{quantity}"
        payload = event_type_ids
        all_filtered_events.append({org_id: make_api_request(url, headers, payload)})

    return jsonify(all_filtered_events)

# 10. Retrieves positions created since a specific timestamp for multiple organisations
@app.route('/positions_since', methods=['POST'])
def get_positions_since():
    data = request.json
    organisation_ids = data.get('organisationIds')
    since_token = data.get('sinceToken', 'NEW')
    quantity = data.get('quantity', 100)
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    all_positions_since = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(30)  # Adding a delay between API calls

        url = f"https://integrate.za.mixtelematics.com/api/positions/groups/createdsince/organisation/{org_id}/sincetoken/{since_token}/quantity/{quantity}"
        response = make_api_request(url, headers, {})
        all_positions_since.append({org_id: response})

    return jsonify(all_positions_since)

# 11. Retrieves trips created since a specific timestamp for multiple organisations
@app.route('/trips_since', methods=['POST'])
def get_trips_since():
    data = request.json
    organisation_ids = data.get('organisationIds')
    since_token = data.get('sinceToken', 'NEW')
    quantity = data.get('quantity', 100)
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 500

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    all_trips_since = []

    # Loop through all organisations and make a separate API call
    for i, org_id in enumerate(organisation_ids):
        if i > 0:
            time.sleep(30)  # Adding a delay between API calls

        url = f"https://integrate.za.mixtelematics.com/api/trips/groups/createdsince/organisation/{org_id}/sincetoken/{since_token}/quantity/{quantity}"
        response = make_api_request(url, headers, {})
        all_trips_since.append({org_id: response})

    return jsonify(all_trips_since)







if __name__ == "__main__":
    app.run(debug=True)
