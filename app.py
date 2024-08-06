from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import requests
from datetime import date, datetime, timedelta
from time import time
from flask import Flask, render_template, request, jsonify, session
import re
import pytz




  
app = Flask(__name__)


app.secret_key = 'supersecretkey'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)

GPT_MODEL = "gpt-3.5-turbo-0613"
openai_api_key = "sk-proj-mZlcMaG0OV8Xbi0gmJCxT3BlbkFJ6jFuKVszNOatklwrjB6z"
day_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIMEZONE = pytz.timezone('Asia/Kolkata')

def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai_api_key,
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def localize_datetime(date_str, time_str):
    dt_str = date_str + " " + time_str.replace("PM", "").replace("AM", "").strip()
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return TIMEZONE.localize(dt)

limit1 = datetime.strptime("10:00:00", "%H:%M:%S").time()
limit2 = datetime.strptime("17:00:00", "%H:%M:%S").time()
limit3 = datetime.strptime("12:00:00", "%H:%M:%S").time()

def appointment_booking(arguments):
    try:
        provided_date = str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM", "").replace("AM", "").strip(), "%H:%M:%S").time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Asia/Kolkata')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
        email_address = json.loads(arguments)['email_address']
        end_date_time = start_date_time + timedelta(hours=2)

        if provided_date and provided_time and email_address:
            slot_checking = appointment_checking(arguments)
            if slot_checking == "Slot is available for appointment. Would you like to proceed?":
                if start_date_time < datetime.now(timezone):
                    return "Please enter valid date and time."
                else:
                    if day_list[start_date_time.date().weekday()] == "Saturday":
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                            event = {
                                'summary': "Appointment booking With AI Chatbot",
                                'location': "Islamabad",
                                'description': "This appointment has been scheduled as the demo of the appointment booking chatbot using OpenAI function calling feature by Pragnakalp Techlabs.",
                                'start': {
                                    'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'end': {
                                    'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'attendees': [
                                    {'email': email_address},
                                ],
                                'reminders': {
                                    'useDefault': False,
                                    'overrides': [
                                        {'method': 'email', 'minutes': 24 * 60},
                                        {'method': 'popup', 'minutes': 10},
                                    ],
                                },
                            }
                            service.events().insert(calendarId='primary', body=event).execute()
                            return "Appointment added successfully."
                        else:
                            return "Please try to book an appointment during working hours, which is 10 AM to 2 PM on Saturday."
                    else:
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                            event = {
                                'summary': "Appointment booking Chatbot using OpenAI's function calling feature",
                                'location': "Ahmedabad",
                                'description': "This appointment has been scheduled as the demo of the appointment booking chatbot using OpenAI function calling feature by Pragnakalp Techlabs.",
                                'start': {
                                    'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'end': {
                                    'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'attendees': [
                                    {'email': email_address},
                                ],
                                'reminders': {
                                    'useDefault': False,
                                    'overrides': [
                                        {'method': 'email', 'minutes': 24 * 60},
                                        {'method': 'popup', 'minutes': 10},
                                    ],
                                },
                            }
                            service.events().insert(calendarId='primary', body=event).execute()
                            return "Appointment added successfully."
                        else:
                            return "Please try to book an appointment during working hours, which is 10 AM to 7 PM."
            else:
                return slot_checking
        else:
            return "Please provide all necessary details: Start date, End date, and Email address."
    except:
        return "We are facing an error while processing your request. Please try again."

def appointment_reschedule(arguments):
    try:
        provided_date = str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM", "").replace("AM", "").strip(), "%H:%M:%S").time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Asia/Kolkata')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
        email_address = json.loads(arguments)['email_address']

        if provided_date and provided_time and email_address:
            if start_date_time < datetime.now(timezone):
                return "Please enter valid date and time."
            else:
                if day_list[start_date_time.date().weekday()] == "Saturday":
                    if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                        end_date_time = start_date_time + timedelta(hours=2)
                        events = service.events().list(calendarId="primary").execute()
                        id = ""
                        final_event = None
                        for event in events['items']:
                            if event['attendees'][0]['email'] == email_address:
                                id = event['id']
                                final_event = event
                                break
                        if final_event:
                            final_event['start'] = {'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': 'Asia/Kolkata'}
                            final_event['end'] = {'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': 'Asia/Kolkata'}
                            service.events().update(calendarId='primary', eventId=id, body=final_event).execute()
                            return "Appointment rescheduled successfully."
                        else:
                            return "No appointment found for the provided email address."
                    else:
                        return "Please try to book an appointment during working hours, which is 10 AM to 2 PM on Saturday."
                else:
                    if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                        end_date_time = start_date_time + timedelta(hours=2)
                        events = service.events().list(calendarId="primary").execute()
                        id = ""
                        final_event = None
                        for event in events['items']:
                            if event['attendees'][0]['email'] == email_address:
                                id = event['id']
                                final_event = event
                                break
                        if final_event:
                            final_event['start'] = {'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': 'Asia/Kolkata'}
                            final_event['end'] = {'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': 'Asia/Kolkata'}
                            service.events().update(calendarId='primary', eventId=id, body=final_event).execute()
                            return "Appointment rescheduled successfully."
                        else:
                            return "No appointment found for the provided email address."
                    else:
                        return "Please try to book an appointment during working hours, which is 10 AM to 7 PM."
        else:
            return "Please provide all necessary details: Start date, End date, and Email address."
    except:
        return "We are facing an error while processing your request. Please try again."

def appointment_checking(arguments):
    provided_date = str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
    provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM", "").replace("AM", "").strip(), "%H:%M:%S").time())
    start_date_time = provided_date + " " + provided_time
    timezone = pytz.timezone('Asia/Kolkata')
    start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))

    start = start_date_time.isoformat()
    end = (start_date_time + timedelta(hours=2)).isoformat()
    events_result = service.events().list(calendarId='primary', timeMin=start, timeMax=end, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return "Slot is available for appointment. Would you like to proceed?"
    else:
        return "This slot is not available for appointment. Please try another slot."

def appointment_deletion(arguments):
    try:
        email_address = json.loads(arguments)['email_address']
        events = service.events().list(calendarId="primary").execute()
        id = ""
        final_event = None
        for event in events['items']:
            if event['attendees'][0]['email'] == email_address:
                id = event['id']
                final_event = event
                break
        if final_event:
            service.events().delete(calendarId='primary', eventId=id).execute()
            return "Appointment deleted successfully."
        else:
            return "No appointment found for the provided email address."
    except:
        return "We are facing an error while processing your request. Please try again."
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('prompt')
    session['messages'] = session.get('messages', [])
    messages = session['messages']
    messages.append({"role": "user", "content": user_input})

    functions = [
        {
            "name": "appointment_booking",
            "description": "Booking an appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date of appointment in the format YYYY-MM-DD"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of appointment in the format HH:MM:SS"
                    },
                    "email_address": {
                        "type": "string",
                        "description": "Email address of the person booking the appointment"
                    }
                },
                "required": ["date", "time", "email_address"]
            }
        },
        {
            "name": "appointment_reschedule",
            "description": "Rescheduling an appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date of appointment in the format YYYY-MM-DD"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of appointment in the format HH:MM:SS"
                    },
                    "email_address": {
                        "type": "string",
                        "description": "Email address of the person booking the appointment"
                    }
                },
                "required": ["date", "time", "email_address"]
            }
        },
        {
            "name": "appointment_deletion",
            "description": "Deleting an appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_address": {
                        "type": "string",
                        "description": "Email address of the person booking the appointment"
                    }
                },
                "required": ["email_address"]
            }
        },
        {
            "name": "appointment_checking",
            "description": "Checking the availability of an appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date of appointment in the format YYYY-MM-DD"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of appointment in the format HH:MM:SS"
                    }
                },
                "required": ["date", "time"]
            }
        }
    ]

    completion_response = chat_completion_request(messages, functions=functions)
    response_message = completion_response.json()

    if response_message['choices'][0]['finish_reason'] == 'function_call':
        function_call = response_message['choices'][0]['message']['function_call']
        function_name = function_call['name']
        function_arguments = function_call['arguments']

        if function_name == 'appointment_booking':
            function_response = appointment_booking(function_arguments)
        elif function_name == 'appointment_reschedule':
            function_response = appointment_reschedule(function_arguments)
        elif function_name == 'appointment_deletion':
            function_response = appointment_deletion(function_arguments)
        elif function_name == 'appointment_checking':
            function_response = appointment_checking(function_arguments)
        else:
            function_response = "Sorry, I can't handle this function."

        messages.append({
            "role": "assistant",
            "content": response_message['choices'][0]['message']['content'],
            "function_call": function_call
        })
        messages.append({
            "role": "function",
            "name": function_name,
            "content": function_response
        })
    else:
        messages.append({"role": "assistant", "content": response_message['choices'][0]['message']['content']})

    session['messages'] = messages
    return jsonify({"response": messages[-1]["content"]})

if __name__ == "__main__":
  app.run(debug=True)
