from flask import Flask, jsonify, request, render_template, redirect, url_for
import json
import os

app = Flask(__name__)

# Path to the base data file
DATA_FILE = "./data/data.json"

# Load data from a file or initialize with default
def load_data(file_name=DATA_FILE):
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            return json.load(file)
    else:
        return {}

# Save data to a specified file
def save_data(data, file_name):
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_input = request.form.get('input')
        if user_input:
            new_file = f"./data/data_{user_input}.json"
            if not os.path.exists(new_file):
                # Copy data from the base file to the new file
                data = load_data()
                save_data(data, new_file)
            # Redirect to the new path
            return redirect(url_for('index', input=user_input))
        else:
            return render_template('home.html', error="Please provide a valid input.")
    return render_template('home.html')

@app.route('/<input>', methods=['GET', 'POST'])
def index(input):
    file_name = f"./data/data_{input}.json"
    if not os.path.exists(file_name):
        return f"No data file found for input: {input}", 404

    if request.method == 'POST':
        update_request = request.json
        path = update_request.get("path")
        value = update_request.get("value")

        data = load_data(file_name)

        # Navigate and update nested data
        if path:
            target = data
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value

            # Save changes to the specific file
            save_data(data, file_name)
            return jsonify({"message": "Data updated successfully", "data": data})
        else:
            return jsonify({"error": "Invalid path"}), 400

    # Render index template with data
    data = load_data(file_name)
    return render_template('index.html', data=data, api_url=url_for('api', input=input))

@app.route('/api/<input>', methods=['GET', 'POST'])
def api(input):
    file_name = f"./data/data_{input}.json"
    if not os.path.exists(file_name):
        return jsonify({"error": f"No data file found for input: {input}"}), 404

    data = load_data(file_name)

    if request.method == 'POST':
        if 'updates' in request.json:
            updates = request.json.get('updates')
            for update in updates:
                path = update.get('path')
                value = update.get('value')
                if path:
                    target = data
                    for idx, key in enumerate(path[:-1]):
                        if isinstance(target, list):
                            # Ensure the key is a valid index
                            if not isinstance(key, int) and not str(key).isdigit():
                                return jsonify({"error": f"Invalid list index: {key} in path"}), 400
                            key = int(key)  # Convert key to an integer
                            if key >= len(target):
                                return jsonify({"error": f"List index out of range: {key} in path"}), 400
                            target = target[key]
                        elif isinstance(target, dict):
                            # If the target is a dictionary, use setdefault
                            target = target.setdefault(key, {} if idx < len(path) - 2 else [])
                        else:
                            return jsonify({"error": f"Path {path} does not resolve to a valid target"}), 400

                    target[path[-1]] = value
                else:
                    return jsonify({"error": "Invalid path in updates"}), 400
            save_data(data, file_name)
            return jsonify({"message": "Data updated successfully", "data": data})
        else:
            update_request = request.json
            path = update_request.get("path")
            value = update_request.get("value")

            # Navigate and update nested data
            if path:
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value

                # Save changes to the specific file
                save_data(data, file_name)
                return jsonify({"message": "Data updated successfully", "data": data})
            else:
                return jsonify({"error": "Invalid path"}), 400

    # GET request returns the current data
    return jsonify({"data": data})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
