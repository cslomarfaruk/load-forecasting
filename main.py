from flask import Flask, request, jsonify, render_template
from datetime import datetime
from DB import DB
from model import predict_day, predict_hour
from auto_input import start_auto_input
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the database connection
DB.init()

@app.route("/")
def home():
    # Get the current date and time
    now = datetime.now()
    logging.debug(f"Current datetime: {now}")
    
    data = DB.get_data()
    logging.debug(f"Data from DB.get_data(): {data}")
    
    last_p = DB.get_closest_predictions()
    logging.debug(f"Closest predictions from DB.get_closest_predictions(): {last_p}")
    
    return render_template(
        "index.html",
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        humidity=data['humidity'],
        temperature=data['temperature'],
        history=DB.get_predictions(),
        last_hour=last_p['hourly'],
        last_day=last_p['daily'],
    )

@app.route('/insert', methods=['POST'])
def insert_data():
    try:
        humidity = request.form.get('humidity')
        temperature = request.form.get('temperature')
        device_id = request.form.get('device_id')

        logging.debug(f"Insert data request: humidity={humidity}, temperature={temperature}, device_id={device_id}")

        if not humidity or not temperature or not device_id:
            return jsonify({"error": "All fields are required"}), 400

        # Insert data into the database
        inserted_id = DB.insert_data('readings', {
            'temperature': temperature,
            'humidity': humidity,
            'device_id': device_id
        })

        logging.debug(f"Inserted ID: {inserted_id}")

        if inserted_id:
            return jsonify({
                "message": "Data inserted successfully",
                "id": inserted_id
            }), 201
        else:
            return jsonify({"error": "Failed to insert data"}), 500
    except Exception as e:
        logging.error(f"Error inserting data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        hour = request.form.get('hour')
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')
        nldc_demand = request.form.get('demand')
        temperature = request.form.get('temperature')
        humidity = request.form.get('humidity')

        if not all([nldc_demand, temperature, humidity, day, month, year]):
            return jsonify({"error": "Missing required input data"}), 400

        nldc_demand = float(nldc_demand)
        temperature = float(temperature)
        humidity = float(humidity)
        day = int(day)
        month = int(month)
        year = int(year)

        if hour:
            hour = int(hour)
            user_input = [nldc_demand, temperature, humidity, hour, day, month, year]
            prediction = predict_hour(user_input)
        else:
            user_input = [nldc_demand, temperature, humidity, day, month, year]
            prediction = predict_day(user_input)

        DB.insert_data('predictions', {
            'type': 'hourly' if hour else 'daily',
            'prediction': prediction,
        })

        return jsonify({
            "prediction": prediction,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except ValueError as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500


def format_datetime(value, format="%d %b (%I%p)"):
    if not isinstance(value, datetime):
        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value.strftime(format)

app.jinja_env.filters['strftime'] = format_datetime

start_auto_input()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="3000")
