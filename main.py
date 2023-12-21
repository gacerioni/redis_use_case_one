from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import redis
from dotenv import load_dotenv
import config
import logging

# GABS - FLASK PART SO I CAN PRESENT IT LATER
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Redis host and port from environment variables or use fallbacks
REDIS_HOST_OSS = os.getenv('REDIS_HOST_OSS', config.DEFAULT_REDIS_HOST_OSS)
REDIS_PORT_OSS = os.getenv('REDIS_PORT_OSS', config.DEFAULT_REDIS_PORT_OSS)
REDIS_HOST_ENTERPRISE = os.getenv('REDIS_HOST_ENTERPRISE', config.DEFAULT_REDIS_HOST_ENTERPRISE)
REDIS_PORT_ENTERPRISE = os.getenv('REDIS_PORT_ENTERPRISE', config.DEFAULT_REDIS_PORT_ENTERPRISE)

# Gabs Logger configs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Define log format
log_format = "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"  # Define date format

# GABS -  console handler and formatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(log_format, datefmt=date_format)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)


def get_redis_conn_obj(redis_host: str, redis_port: int):
    # Connect to Redis
    r = redis.Redis(host=redis_host, port=int(redis_port), db=0)

    return r


def add_hundred_integers_sorted_set(db_conn_obj, starting_pos: int):
    # Define the name of the Sorted Set
    sorted_set_name = "integer_gabs_sorted"

    # Clear the existing sorted set, if it exists
    db_conn_obj.delete(sorted_set_name)

    starting_pos = int(starting_pos)

    # Create a dictionary where both the score and the member are the integer values
    members = {i: i for i in range(int(starting_pos), int(starting_pos) + 100)}

    # Add all members to the sorted set in one command
    db_conn_obj.zadd(sorted_set_name, members)

    logger.info(f"Integers from {starting_pos} to {starting_pos + 99} have been added to the Redis sorted set.")


def delete_integers_sorted_set():
    try:
        db_conn_obj = get_redis_conn_obj(REDIS_HOST_OSS, REDIS_PORT_OSS)
        # Delete the entire Sorted Set
        db_conn_obj.delete("integer_gabs_sorted")
        logger.info("Deleted the sorted set from Redis.")
        return jsonify({"message": "Deleted the sorted set from Redis."}), 200
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


def add_hundred_integers_list(db_conn_obj, starting_pos: int):
    list_name = "integer_gabs_list"
    starting_pos = int(starting_pos)

    # Create a list of integers
    integers = [str(i) for i in range(starting_pos, starting_pos + 100)]

    # Add all integers to the list in one command
    db_conn_obj.rpush(list_name, *integers)

    logger.info(f"Integers from {starting_pos} to {starting_pos + 99} have been added to the Redis list.")


def delete_integers_list():
    db_conn_obj = get_redis_conn_obj(REDIS_HOST_OSS, REDIS_PORT_OSS)
    db_conn_obj.delete("integer_gabs_list")
    logger.info("Deleted the list from Redis.")


# GABS- FLASK ENDPOINTS START HERE


@app.route('/add_sorted_set', methods=['GET', 'POST'])
def add_sorted_set():
    if request.method == 'POST':
        # Get data from form
        starting_pos = request.form.get('starting_pos', 1)
        # Your logic to add integers
        add_hundred_integers_sorted_set(get_redis_conn_obj(REDIS_HOST_OSS, REDIS_PORT_OSS), starting_pos)
        return redirect(url_for('index'))
    # Render the add_integers_sorted_sets.html template for GET requests
    return render_template('add_integers_sorted_sets.html')


@app.route('/delete_sorted_set', methods=['GET', 'POST'])
def delete_sorted_set():
    if request.method == 'POST':
        delete_integers_sorted_set()
        return redirect(url_for('index'))
    return render_template('delete_integers_sorted_sets.html')


@app.route('/view_asc_sorted_set')
def view_sorted_set_asc_sorted_set():
    try:
        db_conn_obj = get_redis_conn_obj(REDIS_HOST_ENTERPRISE, REDIS_PORT_ENTERPRISE)
        # Retrieve integers in ascending order
        integers = [int(i.decode('utf-8')) for i in db_conn_obj.zrange("integer_gabs_sorted", 0, -1, withscores=False)]
        return render_template('view_sorted_set.html', integers=integers, order="Ascending")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/view_desc_sorted_set')
def view_sorted_set_desc_sorted_set():
    try:
        db_conn_obj = get_redis_conn_obj(REDIS_HOST_ENTERPRISE, REDIS_PORT_ENTERPRISE)
        # Retrieve integers in descending order
        integers = [int(i.decode('utf-8')) for i in
                    db_conn_obj.zrevrange("integer_gabs_sorted", 0, -1, withscores=False)]
        return render_template('view_sorted_set.html', integers=integers, order="Descending")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/add_list', methods=['GET', 'POST'])
def add_list():
    if request.method == 'POST':
        starting_pos = request.form.get('starting_pos', 1)
        add_hundred_integers_list(get_redis_conn_obj(REDIS_HOST_OSS, REDIS_PORT_OSS), starting_pos)
        return redirect(url_for('index'))
    return render_template('add_integers_list.html')


@app.route('/delete_list', methods=['GET', 'POST'])
def delete_list():
    if request.method == 'POST':
        delete_integers_list()
        return redirect(url_for('index'))
    return render_template('delete_integers_list.html')


@app.route('/view_asc_list')
def view_asc_list():
    db_conn_obj = get_redis_conn_obj(REDIS_HOST_ENTERPRISE, REDIS_PORT_ENTERPRISE)
    integers = db_conn_obj.lrange("integer_gabs_list", 0, -1)
    integers = [int(i.decode('utf-8')) for i in integers]
    return render_template('view_list.html', integers=integers, order="Ascending")


@app.route('/view_desc_list')
def view_desc_list():
    db_conn_obj = get_redis_conn_obj(REDIS_HOST_ENTERPRISE, REDIS_PORT_ENTERPRISE)
    integers = db_conn_obj.lrange("integer_gabs_list", 0, -1)
    integers = [int(i.decode('utf-8')) for i in integers][::-1]
    return render_template('view_list.html', integers=integers, order="Descending")


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    logger.info("Starting Gabs Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
