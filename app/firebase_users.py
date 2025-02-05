import os
from typing import Optional, Union
import firebase_admin
from firebase_admin import credentials, db
import uuid
import zlib
import base64
import json
import re
from .appmode import CH_DISABLE_FIREBASE
from .globalVariable import *
from .utilities import *
import streamlit as st
import sys
import logging
import ast
import copy
import numpy as np
import numpy.typing as npt
import random
import json

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("ChatHAP")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to initialize the Firebase app if not already initialized
def initialize_firebase_users():
    if CH_DISABLE_FIREBASE:
        return
    if not firebase_admin._apps:
        # Path to the service account key file
        for path in [
            '../chathap-20643-firebase-adminsdk-cdmp4-239330e418.json',
            os.path.join(SCRIPT_DIR, '../chathap-20643-firebase-adminsdk-cdmp4-239330e418.json')
        ]:
            try:
                cred = credentials.Certificate(path)
                break
            except FileNotFoundError:
                pass
        else:
            raise FileNotFoundError("Firebase service account key file not found")
        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://chathap-20643-default-rtdb.firebaseio.com/'
        })

def backup_data():
    if CH_DISABLE_FIREBASE:
        return

    ref = db.reference('/')
    data_chunks = {}
    for key in ref.get(shallow=True).keys():  # type: ignore # Get top-level keys
        data_chunks[key] = ref.child(key).get()  # Fetch data for each top-level key

    backup_dir = os.path.join(SCRIPT_DIR, '../../../User study/backup')
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, 'output_data.json')

    with open(backup_path, 'w') as json_file:
        json.dump(data_chunks, json_file, indent=4)

    print(f"Data has been saved to {backup_path}")

# Generate a unique user ID
def generate_unique_user_id():
    return str(uuid.uuid4())

def compress_data(data):
    data_str = json.dumps(data)
    compressed_data = zlib.compress(data_str.encode('utf-8'))
    return base64.b64encode(compressed_data).decode('utf-8')

def decompress_data(data):
    compressed_data = base64.b64decode(data.encode('utf-8'))
    data_str = zlib.decompress(compressed_data).decode('utf-8')
    return json.loads(data_str)

# Add data to Realtime Database with a unique user ID
def add_data():
    if CH_DISABLE_FIREBASE:
        return
    user_id = generate_unique_user_id()
    start_time = get_time()

    for DB in DB_write:
        ref = db.reference(f'{DB}/{user_id}')
        ref.set({
            '01_start_time': start_time
        })
        print(f'User added with ID: {user_id}')

    return user_id

# Update data in Realtime Database
def update_data(user_id, vib_num, content):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        ref = db.reference(f'{DB}/{user_id}/vibration/{vib_num}')
        ref.update(content)

# Update compressed data in Realtime Database
def update_compressed_data(user_id, vib_num, key, content):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        ref = db.reference(f'{DB}/{user_id}/vibration/{vib_num}/{key}')
        compressed_content = compress_data(content)
        ref.set(compressed_content)

# Update rating in Realtime Database
def update_rating(user_id, vib_num, content):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        ref = db.reference(f'{DB}/{user_id}/vibration/{vib_num}')
        ref.update(content)

# Update conversation in Realtime Database
def update_conversation(user_id, new_content):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        ref = db.reference(f'{DB}/{user_id}/conversation')
        current_data = ref.get()

        if current_data:
            if isinstance(current_data, list):
                current_data.append(new_content)
            else:
                current_data = [current_data, new_content]
        else:
            current_data = [new_content]
        ref.set(current_data)

# Update ratings to vibrations in Realtime Database
def update_vibration_rating(user_id, vib_class, vib_num, clicked_num, temp_rating):
    if CH_DISABLE_FIREBASE:
        return

    if vib_class == "feature":
        vib_class = "approach-navigation"
    elif vib_class == "parameter":
        vib_class = "approach-parameter"
    elif vib_class == "modify":
        vib_class = "approach-modify"
    else:
        logger.error(f"No data found for vibration approach class {vib_class}")

    for DB in DB_write:
        ref_read = db.reference(f'{DB}/{user_id}/vibration/{vib_num}')
        current_data_read = ref_read.get()

        # Check if the current data read is valid
        if not current_data_read:
            logger.error(f"No data found for user {user_id} and vibration {vib_num}")
            return

        resource = current_data_read.get('resource') # type: ignore
        # rating = current_data_read.get('rating')
        rating = temp_rating
        feature_list = []
        change_list = []

        if resource is not None and rating is not None:
            feature_str = current_data_read.get('feature') # type: ignore
            if feature_str is not None:
                try:
                    feature_list = ast.literal_eval(feature_str)
                except (ValueError, SyntaxError) as e:
                    feature_list = feature_str
                    # logger.debug(f"Error converting string to list: {e}")
                feature_list = [sanitize_key(item.split(": ")[1]) if ": " in item else sanitize_key(item) for item in feature_list]
                # limit the number of features to a maximum of five
                if len(feature_list) > 5:
                    feature_list = feature_list[:5]
                logger.debug(f"feature_list: {feature_list}")
            else:
                logger.debug(f"FEATURE not found in the current data for user {user_id} and vibration {vib_num}")

            change_str = current_data_read.get('change') # type: ignore
            if change_str is not None:
                try:
                    change_list = ast.literal_eval(change_str)
                except (ValueError, SyntaxError) as e:
                    change_list = change_str
                    # logger.debug(f"Error converting string to list: {e}")
            else:
                logger.debug(f"CHANGE not found in the current data for user {user_id} and vibration {vib_num}")
        else:
            logger.error(f"Resource or rating not found in the current data for user {user_id} and vibration {vib_num}")
            return

        if feature_str is not None:
            ref_rating_update = db.reference(f'vibration_{DB}/{vib_class}/{resource}/navigation')
            current_rating_update = ref_rating_update.get()

            # Initialize rating if it doesn't exist
            if not current_rating_update:
                current_rating_update = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}

            current_rating = current_rating_update

            # Ensure current_rating is a dictionary
            if not isinstance(current_rating, dict):
                current_rating = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}

            # Update the vibration rating based on the input rating
            if clicked_num <= 1:
                if rating == 1:
                    current_rating['THUMBS_UP'] += 1
                elif rating == -1:
                    current_rating['THUMBS_DOWN'] += 1
            else:
                if rating == 1:
                    current_rating['THUMBS_UP'] += 1
                    current_rating['THUMBS_DOWN'] -= 1
                elif rating == -1:
                    current_rating['THUMBS_UP'] -= 1
                    current_rating['THUMBS_DOWN'] += 1

            ref_rating_update.update(current_rating)


            ref_feature_update = db.reference(f'vote-feature_{DB}')
            current_feature_update = ref_feature_update.get()

            if not current_feature_update:
                current_feature_update = {feature: {resource: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}} for feature in feature_list}

            # Ensure current_feature_update is a dictionary of dictionaries
            if not all(isinstance(value, dict) for value in current_feature_update.values()): # type: ignore
                current_feature_update = {feature: {resource: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}} for feature in feature_list}

            # Update the feature rating based on the input rating
            for feature in feature_list:
                if feature not in current_feature_update:
                    current_feature_update[feature] = {resource: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}} # type: ignore

                if resource not in current_feature_update[feature]: # type: ignore
                    current_feature_update[feature][resource] = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} # type: ignore

                if clicked_num <= 1:
                    if rating == 1:
                        current_feature_update[feature][resource]['THUMBS_UP'] += 1 # type: ignore
                    elif rating == -1:
                        current_feature_update[feature][resource]['THUMBS_DOWN'] += 1 # type: ignore
                else:
                    if rating == 1:
                        current_feature_update[feature][resource]['THUMBS_UP'] += 1 # type: ignore
                        current_feature_update[feature][resource]['THUMBS_DOWN'] -= 1 # type: ignore
                    elif rating == -1:
                        current_feature_update[feature][resource]['THUMBS_UP'] -= 1 # type: ignore
                        current_feature_update[feature][resource]['THUMBS_DOWN'] += 1 # type: ignore

            ref_feature_update.update(current_feature_update)

        if change_str is not None:
            ref_rating_update = db.reference(f'vibration_{DB}/{vib_class}/{resource}/parameter')
            current_rating_update = ref_rating_update.get()

            # Initialize rating if it doesn't exist
            if not current_rating_update:
                current_rating_update = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}

            current_rating = current_rating_update

            # Ensure current_rating is a dictionary
            if not isinstance(current_rating, dict):
                current_rating = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}

            # Update the vibration rating based on the input rating
            if clicked_num <= 1:
                if rating == 1:
                    current_rating['THUMBS_UP'] += 1
                elif rating == -1:
                    current_rating['THUMBS_DOWN'] += 1
            else:
                if rating == 1:
                    current_rating['THUMBS_UP'] += 1
                    current_rating['THUMBS_DOWN'] -= 1
                elif rating == -1:
                    current_rating['THUMBS_UP'] -= 1
                    current_rating['THUMBS_DOWN'] += 1

            ref_rating_update.update(current_rating)

            if  change_list == []:
                change_list = ['none', 'none', 'none']

            try:
                feature = change_list[0].strip("'")
                change = change_list[1].strip("'")
                direction = change_list[2].strip("'")
            except:
                logger.error(f"Resource or rating not found in the current data for change_list {change_list} and vibration {vib_num}")

            direction_list = ['POSITIVE', 'NEGATIVE', 'NONE']

            if change_list != ['none', 'none', 'none']:
                ref_change_update = db.reference(f'vote-change_{DB}')
                current_change_update = ref_change_update.get()

                # Initialize change if it doesn't exist
                if not current_change_update:
                    current_change_update = {feature: {change: {dir: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} for dir in direction_list}}}

                # Ensure current_change_update is a dictionary of dictionaries
                if not all(isinstance(value, dict) for value in current_change_update.values()): # type: ignore
                    current_change_update = {feature: {change: {dir: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} for dir in direction_list}}}

                # Update the change rating based on the input rating
                if feature not in current_change_update:
                    current_change_update[feature] = {change: {dir: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} for dir in direction_list}} # type: ignore

                if change not in current_change_update[feature]: # type: ignore
                    current_change_update[feature][change] = {dir: {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} for dir in direction_list} # type: ignore

                if direction not in current_change_update[feature][change]: # type: ignore
                    current_change_update[feature][change][direction] = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0} # type: ignore

                if clicked_num <= 1:
                    if rating == 1:
                        current_change_update[feature][change][direction]['THUMBS_UP'] += 1 # type: ignore
                    elif rating == -1:
                        current_change_update[feature][change][direction]['THUMBS_DOWN'] += 1 # type: ignore
                else:
                    if rating == 1:
                        current_change_update[feature][change][direction]['THUMBS_UP'] += 1 # type: ignore
                        current_change_update[feature][change][direction]['THUMBS_DOWN'] -= 1 # type: ignore
                    elif rating == -1:
                        current_change_update[feature][change][direction]['THUMBS_UP'] -= 1 # type: ignore
                        current_change_update[feature][change][direction]['THUMBS_DOWN'] += 1 # type: ignore

                ref_change_update.update(current_change_update)


# Read data from Realtime Database
def read_nav_rating(resourceLists: list[str], featureLists: list[str], importanceLists_i: Optional[list[float]] = None, preference: bool = True, num_clip: int = 5, min_clip: float = 0.01):
    if CH_DISABLE_FIREBASE:
        return random.choice(resourceLists)

    ref = db.reference(f'vote-feature_{DB_read}')
    current_data = ref.get()

    # Initialize current_data if it's None
    if current_data is None:
        current_data = {}
        for feature in featureLists:
            valid_feature = replace_invalid_chars(feature)
            current_data[valid_feature] = {}
            for resource in resourceLists:
                valid_resource = replace_invalid_chars(resource)
                current_data[valid_feature][valid_resource] = {'THUMBS_UP': 0, 'THUMBS_DOWN': 0}
        ref.set(current_data)  # Update the database with the initialized structure


    resource_data = {}

    # Initialize feature_weights if not provided
    if importanceLists_i is None:
        # Equal weights if not specified
        importanceLists = {feature: 1 for feature in featureLists}
    else:
        importanceLists = dict(zip(featureLists, importanceLists_i))

    # Initialize resource data for all features
    for feature in featureLists:
        if feature not in resource_data:
            resource_data[feature] = {}
        for resource in resourceLists:
            if resource not in resource_data[feature]:
                resource_data[feature][resource] = {
                    'THUMBS_UP': 0,
                    'THUMBS_DOWN': 0,
                    'P_org': 0,
                    'P_clip': 0,
                    'P_soft': 0
                }

    for feature in featureLists:
        valid_feature = replace_invalid_chars(feature)
        if valid_feature not in current_data:
            logger.error(f"Feature {feature} not found in current data")
            continue

        for resource in resourceLists:
            valid_resource = replace_invalid_chars(resource)
            if valid_resource not in current_data[valid_feature]: # type: ignore
                logger.error(f"Resource {resource} not found under feature {feature}")
                continue

            resource_data[feature][resource]['THUMBS_UP'] = current_data[valid_feature][valid_resource]['THUMBS_UP'] # type: ignore
            resource_data[feature][resource]['THUMBS_DOWN'] = current_data[valid_feature][valid_resource]['THUMBS_DOWN'] # type: ignore
            total_votes = current_data[valid_feature][valid_resource]['THUMBS_UP'] + current_data[valid_feature][valid_resource]['THUMBS_DOWN'] # type: ignore
            resource_data[feature][resource]['P_org'] = current_data[valid_feature][valid_resource]['THUMBS_UP'] / total_votes if total_votes > 0 else 0 # type: ignore
            resource_data[feature][resource]['P_clip'] = 1.0 if total_votes < num_clip else resource_data[feature][resource]['P_org']
            resource_data[feature][resource]['P_clip'] = min_clip if current_data[valid_feature][valid_resource]['THUMBS_DOWN'] == 0 and total_votes > 0 else resource_data[feature][resource]['P_org'] # type: ignore

        # Calculate the soft probabilities
        total_softs = sum(np.exp(resource_data[feature][resource]['P_clip']) for resource in resourceLists)
        if total_softs > 0:
            for resource in resourceLists:
                resource_data[feature][resource]['P_soft'] = np.exp(resource_data[feature][resource]['P_clip']) / total_softs
        else:
            for resource in resourceLists:
                resource_data[feature][resource]['P_soft'] = 0

    logger.debug(f"resource_data: {resource_data}")

    # Calculate weighted sum for each resource
    resource_scores = {resource: 0 for resource in resourceLists}
    for feature in featureLists:
        for resource in resourceLists:
            resource_scores[resource] += importanceLists[feature] * resource_data[feature][resource]['P_soft']

    # Normalize scores to create a probability distribution
    total_score = sum(resource_scores.values())
    if total_score > 0:
        resource_probabilities = {resource: score / total_score for resource, score in resource_scores.items()}
    else:
        resource_probabilities = {resource: 1 / len(resourceLists) for resource in resourceLists}

    # Select a resource based on the probabilities
    resources = list(resource_probabilities.keys())
    probabilities = list(resource_probabilities.values())
    logger.info(f"resources: {resources}")

    # Check if resources and probabilities are not empty before selecting
    if not resources or not probabilities:
        logger.error("No resources or probabilities available for selection.")
        return None
    else:
        if preference:
            selected_resource = random.choices(resources, probabilities)[0]
            logger.info(f"resource_probabilities: {resource_probabilities}")
        else:
            selected_resource = random.choices(resources)[0]

    logger.info(f"Selected resource: {selected_resource}")

    return selected_resource

def update_signal_data(user_id, content: dict, signal: npt.NDArray[np.float64], t: npt.NDArray[np.float64], key_counter: int):
    content_s = {"signal": signal.tolist()}
    content_t = {"t": t.tolist()}
    if user_id:
        update_data(user_id, f'vibration_{key_counter}', content)
        update_compressed_data(user_id, f'vibration_{key_counter}', "signal", content_s)
        update_compressed_data(user_id, f'vibration_{key_counter}', "t", content_t)
    else:
        logger.error("user_id is not defined in session state")

def submit_signal_data(user_id, content: dict, signal: npt.NDArray[np.float64], t: npt.NDArray[np.float64], key_counter: int):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        content_s = {"signal": signal.tolist()}
        content_t = {"t": t.tolist()}
        if user_id:
            ref = db.reference(f'{DB}/{user_id}/submission/vibration_{key_counter}')
            ref.update(content)

            ref_content_s = db.reference(f'{DB}/{user_id}/submission/vibration_{key_counter}/signal')
            compressed_content_s = compress_data(content_s)
            ref_content_s.set(compressed_content_s)

            ref_content_t = db.reference(f'{DB}/{user_id}/submission/vibration_{key_counter}/t')
            compressed_content_t = compress_data(content_t)
            ref_content_t.set(compressed_content_t)

        else:
            logger.error("user_id is not defined in session state")

def update_noResponse_data(user_id: str, content: dict, key_counter: int):
    if CH_DISABLE_FIREBASE:
        return

    for DB in DB_write:
        if user_id:
            ref = db.reference(f'{DB}/{user_id}/noResponse/vibration_{key_counter}')
            if content:
                ref.update(content)
            else:
                logger.error("Content is empty and cannot be updated")
        else:
            logger.error("user_id is not defined in session state")

def sanitize_key(key):
    """Sanitize the key to ensure it is valid for Firebase."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', key)

def replace_invalid_chars(name):
    # Replace invalid characters with underscores
    return name.replace('.', '_').replace('$', '_').replace('#', '_').replace('[', '_').replace(']', '_').replace('/', '_')



# Read data from Realtime Database
def read_data():
    if CH_DISABLE_FIREBASE:
        return
    ref = db.reference(f'{DB_read}')
    snapshot = ref.get()
    print(snapshot)

# Delete data from Realtime Database
def delete_data(user_id):
    if CH_DISABLE_FIREBASE:
        return
    ref = db.reference(f'{DB_write}/{user_id}')
    ref.delete()


# Call the functions
# add_data()
# read_data()
# update_data()
# delete_data()