from fastapi import FastAPI
import requests
import json
import os
from google.oauth2 import service_account
import google.auth.transport.requests
from google.cloud import firestore
from typing import Optional
app = FastAPI()

# --- CONFIG ---
SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"
SCOPES = [
    "https://www.googleapis.com/auth/firebase.messaging",
    "https://www.googleapis.com/auth/datastore",
]

PROJECT_ID = "chopchop-aya"

# --- FIREBASE CREDENTIALS SETUP ---
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
    creds_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    db = firestore.Client(credentials=creds, project=PROJECT_ID)
else:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)

# if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
#     # ✅ For Render (use environment variable)
#     creds_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
#     creds = service_account.Credentials.from_service_account_info(
#         creds_info, scopes=SCOPES
#     )
#     db = firestore.Client(credentials=creds, project=PROJECT_ID)
# else:
#     # ✅ For local development (use local JSON file)
#     creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES
#     )
#     db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)

# ✅ Generate Firebase access token for FCM
def get_access_token():
    credentials = creds.with_scopes(SCOPES)
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


# ✅ Fetch user FCM token from Firestore
def get_user_fcm_token(uid: str):
    doc_ref = db.collection("user").document(uid)
    doc = doc_ref.get()
    if doc.exists:
        user_data = doc.to_dict()
        return user_data.get("fcm_token")
    return None


# ✅ Fetch username for personalization
def get_username(uid: str):
    doc_ref = db.collection("user").document(uid)
    doc = doc_ref.get()
    if doc.exists:
        user_data = doc.to_dict()
        return user_data.get("userName")
    return None


# ✅ Send FCM Notification
@app.post("/send_notification/")
async def send_notification(uid: str, title: str, body: str,screen: Optional[str] = None,):
    # Step 1: Get user's FCM token
    token = get_user_fcm_token(uid)
    if not token:
        return {"status": 404, "message": f"No FCM token found for UID {uid}"}

    # Step 2: Get Firebase access token
    access_token = get_access_token()
    userName = get_username(uid)
    personalized_body = f"{userName}, {body}" if userName else body

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    data_payload = {"uid": uid}
    if screen:
        data_payload["screen"] = screen


    # Step 3: Build FCM message
    message = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": personalized_body},
             "data": data_payload,
            # "data": {"uid": uid},
        }
    }

    # Step 4: Send via HTTP v1 API
    response = requests.post(
        f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send",
        headers=headers,
        data=json.dumps(message),
    )

    return {"status": response.status_code, "response": response.json()}


# ✅ Root route (for Render health check)
@app.get("/")
def home():
    return {"message": "FastAPI Firebase Notification service is running!"}


# from fastapi import FastAPI
# import requests
# import json
# from google.oauth2 import service_account
# import google.auth.transport.requests
# from google.cloud import firestore

# app = FastAPI()

# # --- CONFIG ---
# SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"
# SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
# PROJECT_ID = "chata-45dca"

# # --- FIRESTORE CLIENT ---
# db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)


# # ✅ Generate Firebase access token for FCM
# def get_access_token():
#     credentials = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES
#     )
#     credentials.refresh(google.auth.transport.requests.Request())
#     return credentials.token


# # ✅ Fetch user FCM token from Firestore
# def get_user_fcm_token(uid: str):
#     doc_ref = db.collection("user").document(uid)
#     doc = doc_ref.get()
#     if doc.exists:
#         user_data = doc.to_dict()
#         return user_data.get("fcm_token")  # adjust field name if needed
#     return None

# def get_username(uid: str):
#     doc_ref = db.collection("user").document(uid)
#     doc = doc_ref.get()
#     if doc.exists:
#         user_data = doc.to_dict()
#         return user_data.get("userName")  # adjust field name if needed
#     return None



# # ✅ Send FCM Notification
# @app.post("/send_notification/")
# async def send_notification(uid: str, title: str, body: str):
#     # Step 1: Get user's FCM token from Firestore
#     token = get_user_fcm_token(uid)
#     if not token:
#         return {"status": 404, "message": f"No FCM token found for UID {uid}"}

#     # Step 2: Get Firebase access token
#     access_token = get_access_token()
#     userName = get_username(uid)
#     personalized_body = f"{userName}, {body}"

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json; UTF-8",
#     }

#     # Step 3: Create FCM message
#     message = {
#         "message": {
#             "token": token,
#             "notification": {
#                 "title": title,
#                 "body": personalized_body
#             },
#             "data": {  # optional: extra data
#                 "uid": uid
#             }
#         }
#     }

#     # Step 4: Send via HTTP v1 API
#     response = requests.post(
#         f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send",
#         headers=headers,
#         data=json.dumps(message),
#     )

#     return {"status": response.status_code, "response": response.json()}

