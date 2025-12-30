import ollama
import os
import subprocess
import threading
import json
import asyncio
import sys
import subprocess
import tkinter as tk
from Email import SMTP_Handler
from aiosmtpd.controller import Controller
from smtplib import SMTP
from pypdf import PdfReader
from pydantic import BaseModel
from Email import Email_APP
from Calendar import Calendar_App
from datetime import datetime

#Each extraction class establishes variables to extract values from the LLM response to a prompt.

class DataExtraction(BaseModel):
    name:str
    email:str
    address:str
    education:str
    work:str
    projects:str
    has_masters:bool
    has_doctorate:bool
    has_five_years_work_experience:bool
    has_projects:bool
    is_located_in_the_US:bool

class AvailableDates(BaseModel):
    dates:str
    times:str

class InterviewSetup(BaseModel):
    interview_message:str

class ResponseVariables(BaseModel):
    scheduled_interview:bool
    date_chosen:str
    time_chosen:str

class CompareDates(BaseModel):
    date_in_list:bool

class TimeChosen(BaseModel):
    message:str
    new_date_provided:bool
    new_time_provided:bool

class IncludesDate(BaseModel):
    includes_dates:bool

class AIAgent:

    #Instantiates an instance of the email_app and calendar_app

    def __init__(self):

        self.email_app = Email_APP()
        self.calendar_app = Calendar_App()
        self.interview_scheduled = []

    #Starts the ollama server

    def run_ollama_serve(self):
        subprocess.Popen(["ollama", "serve"])

    #Threads the ollama server

    def start_server(self):

        thread = threading.Thread(target=self.run_ollama_serve)
        thread.start()
        import time
        time.sleep(5)

    #Parses all the text from a resume

    def read_resume(self, path):

        reader = PdfReader("./resumes/" + path)

        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text

    #Prompt to parse resume

    def parsing_prompt(self, text):

        prompt = f"""
            You are processing resumes to extract the name of the candidate, their email, address, education, work experience, and any projects completed. 
            From that data you are to extrapolate and record whether they have a Doctorate or Masters Degree, at least 5 years work experience, at least two personal projects,
            and is located in the United States.
            {text}
          """
        return prompt

    #LLM uses prompt to extract values such as name, email, education and work experience, and location.

    def parse_resume(self, prompt):

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format=DataExtraction.model_json_schema())
        
        data = json.loads(response['message']['content'])

        return data

    #Parses resume and appends extracted values as previously described in a list of dictionaries.

    def resume_data(self):

        candidates = []
        resumes = os.listdir("./resumes")

        for resume in resumes:

            text = self.read_resume(resume)
            prompt = self.parsing_prompt(text)
            data = self.parse_resume(prompt) 
            candidates.append(data)

        return candidates

    #Filters resumes passed on extracted value conditions.

    def pass_conditions(self, candidate):

        if (candidate["has_doctorate"] or candidate["has_masters"]) and candidate["is_located_in_the_US"]:

            return True

        elif (candidate["has_doctorate"] or candidate["has_masters"]) and candidate["has_five_years_work_experience"]:
            return True

        elif candidate["has_five_years_work_experience"] and candidate["has_projects"]:

            return True

        else:

            return False

    #Iterates through candidates and filters out a list of final candidates

    def filter_candidates(self, candidates):

        final_candidates = []

        for candidate in candidates:

            passed = self.pass_conditions(candidate)

            if passed:

                final_candidates.append(candidate)

        return final_candidates

    #Runs the filter

    def run_filter(self):

        print("--------------------------------------------------------------------------------")
        print("Reading Resumes and Filtering Candidates")
        print("--------------------------------------------------------------------------------")

        candidates = self.resume_data()

        return self.filter_candidates(candidates)

    #Extracts all dates from the calendar and prompts the LLM to choose a new list of dates because the initial 
    #ones are all unavailable.

    def date_retrieval(self):

        print("Generating Dates and Times for Interviews")
        print("--------------------------------------------------------------------------------")

        data = self.calendar_app.data_exraction()
        dates = [date["Date"] for date in data]
        string_dates = ", ".join(dates)

        prompt = f"""
                    These dates are unavailable {string_dates}. Generate multiple dates and times excluding weekends for job interviews in 2026.
                  """

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format=AvailableDates.model_json_schema())

        json_data = json.loads(response['message']['content'])
        dates = json_data["dates"]
        times = json_data["times"]

        if dates is None or dates == "None" or dates == "" or dates == "N/A" or times is None or times == "None" or times == "" or times == "N/A":

            self.date_retrieval()

        return dates, times

    #Checks to make sure a prompt includes dates. Returns a True or False value.

    def check_for_dates(self, message):

        prompt = f"""
                    You are checking a message to make sure it includes dates. Return a True values if it does and a False value
                    if it does not. Here is the message: {message}
                  """

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format=IncludesDate.model_json_schema())
        
        data = json.loads(response['message']['content'])


        return data["includes_dates"]       

    #Generates the congratulation email that also sends available dates times to schedule an interview.

    def generate_congratulations_email(self, name, dates, times):

        prompt = f"""
                    You are designing a congratulations mesage to {name} a job candidate for a teaching position at Tutelage an educational company. 
                    They have been selected for the next stage in the interview process. Let them know the dates {dates}
                    at {times} are available for them to schedule an interview. The company itself will send the email. Just return the message.
                    Do not use any emotes or any intro that says here is the message. Start it with Dear {name}, and go from there.
                    Also remind them to input the date they choose as month/day/year in the email. A final note you are to insert the provided dates and times
                    that will not be done manually.
                  """

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        
        interview_response = response['message']['content'] 
        includes_dates = self.check_for_dates(interview_response)

        if not includes_dates:

            self.generate_congratulations_email(name, dates, times)

        return interview_response

    #Sends the interview scheduling emails to the list of final candidates.

    def send_candidate_emails(self):

        final_candidates = self.run_filter()
        dates, times = self.date_retrieval()

        print("Generating and Sending Interview Invite Emails.")
        print("--------------------------------------------------------------------------------")

        controller = Controller(SMTP_Handler(), hostname='127.0.0.1', port=8025, ready_timeout=5.0)
        controller.start()

        for candidate in final_candidates:

            name = candidate["name"]
            email = candidate["email"]
            message = self.generate_congratulations_email(name, dates, times)
            self.interview_scheduled.append({"Email":email,"Scheduled":False})

            self.email_app.send_mail(controller.hostname, controller.port, message, "hr@tutelage.com", email)

        return controller

    #Creates a GUI for both email and calendar so the user can validate the emails were sent
    #and simulate a candidate returning an email for it to be schedule by the AI Agent.

    def schedule_interviews(self, controller):
        print("Bringing up inbox to validate emails were sent.")
        print("--------------------------------------------------------------------------------")
        self.email_app.check_inbox()
        action = input("How many simulated responses from candidates would you like to send? ")
        print("--------------------------------------------------------------------------------")
        
        for idx in range(int(action)):
            self.email_app.send(controller.hostname, controller.port)

        self.email_app.check_inbox()

    #Returns whether an interview has been scheduled yet.

    def scheduled(self, mail_from):

        for email in self.interview_scheduled:

            if mail_from == email["Email"]:

                return email["Scheduled"]

        return None

    #Parses the email response for the date along with the time the candidate chose for their interview.

    def parse_email_response(self, message):

        prompt = f"""
                    You are parsing a response to a job interview invite. Extract whether the job candidate decided to schedule and interview. If they
                    decided to schedule an interview extract what date including the full month name and day they scheduled it for and what time. 
                    Here is the response from the candidate that is to be parsed:
                    {message}
                  """

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format=ResponseVariables.model_json_schema())
        
        data = json.loads(response['message']['content'])
        scheduled_interiew = data["scheduled_interview"]
        date_chosen = data["date_chosen"]
        time_chosen = data["time_chosen"]

        return scheduled_interiew, date_chosen, time_chosen

    #Compares whether the date has already been scheduled.

    def compare_dates(self, date, dates_list):

        return date in dates_list

    #If date has already been chosen this method chooses a new date and time for the candidate to choose from
    #then sends them a follow up email with those options.

    def compare_time_chosen(self, time_chosen, date_chosen):

        prompt = f"""
                    You are to come up with new times for an interview because the previous date had been taken already. This is the date taken:
                    {date_chosen}. Find new dates and times and return a message referencing the available dates and times because
                    the previous date was taken.
                  """

        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format=TimeChosen.model_json_schema())

        data = json.loads(response['message']['content'])
        message = data["message"]
        date_provided = data["new_date_provided"]
        time_provided = data["new_time_provided"]

        return message, time_provided, date_provided

    #Sends follow up email with new dates and times for an interview because the previous choice was taken.

    def send_follow_up(self, new_time_message, controller, mail_to, mail_from):

        self.email_app.send_mail(controller.hostname, controller.port, new_time_message, mail_from, mail_to)
        
    #Updates calendar data

    def update_calendar(self, date_chosen, time_chosen):

        current_data = {"Date":date_chosen,"Event": "Interview at " + time_chosen}
        self.calendar_app.file_handling(current_data)

    #Formats extracted dates, compares dates to determine if they are already taken, 
    #creates follow up email responses and schedules interviews in the calendar.
    def monitor_email(self, controller):

        print("Scheduling Interviews and Sending Out Follow Up Emails If Conflicting Times")
        print("--------------------------------------------------------------------------------")

        mail_list = self.email_app.get_mail_list()
        email_addresses = [email["Email"] for email in self.interview_scheduled]
        format_pattern = "%m/%d/%Y"
        
        for mail in mail_list:

            calendar_data = self.calendar_app.data_exraction()
            dates = [datetime.strptime(date["Date"],format_pattern) for date in calendar_data]

            mail_from = mail["From"]
            mail_to = mail["To"]
            mail_message = mail["Message"]
            scheduled = self.scheduled(mail_from)
            input_string = None
            temp_date_object = None
            final_date_object = None

            if (not scheduled) and (mail_from in email_addresses):

                scheduled_interview, date_chosen, time_chosen = self.parse_email_response(mail_message)

                if not scheduled_interview or date_chosen == "N/A" or date_chosen == None or date_chosen == "None":
                    pass

                if "2026" in date_chosen:
                    date_chosen= date_chosen.strip("2026")

                if ", " in date_chosen:
                    date_chosen = date_chosen.strip(", ")

                if "," in date_chosen:
                    date_chosen = date_chosen.strip(",")

                if "th" in date_chosen:
                    date_chosen = date_chosen.strip("th")

                if "st" in date_chosen:
                    date_chosen = date_chosen.strip("st")
                
                if "rd" in date_chosen:
                    date_chosen = date_chosen.strip("rd")

                if "nd" in date_chosen:
                    date_chosen = date_chosen.strip("nd")

                if date_chosen is not None and date_chosen != "" and date_chosen != "None":
                    temp_date_object = datetime.strptime(date_chosen, '%B %d')

                if temp_date_object is not None:
                    year = 2026
                    final_date_object = temp_date_object.replace(year=year)
                    string_time = final_date_object.strftime('%m/%d/%Y')

                if final_date_object is not None:
                    date_in_list = self.compare_dates(final_date_object, dates)

                else:
                    if date_chosen != "" and date_chosen != "None" and date_chosen is not None:
                        final_date_object = datetime.strptime(date_chosen, format_pattern)
                        string_tine = final_date_object.strftime('%m/%d/%Y')
                        date_in_list = self.compare_dates(final_date_object, dates)

                if date_in_list:

                    if final_date_object is not None:

                        new_time_message, new_time_provided, new_date_provided = self.compare_time_chosen(time_chosen, final_date_object)

                    else:

                        new_time_message, new_time_provided, new_date_provided = self.compare_time_chosen(time_chosen, date_chosen)

                    if new_time_provided and new_date_provided:

                        self.send_follow_up(new_time_message, controller, mail_from, mail_to)

                elif scheduled_interview and not date_in_list:

                    self.update_calendar(string_time, time_chosen)
                    message = "You're interview time has been confirmed and we look forward to speaking with you then. \n\nThank you.\n\nBest,\nTutelage"
                    self.email_app.send_mail(controller.hostname, controller.port, message, mail_to, mail_from)

if __name__ == "__main__":

    AI_Agent = AIAgent()

    #Starts server
    AI_Agent.start_server()

    #Sends candidate emails to the filtered job candidates
    controller = AI_Agent.send_candidate_emails()

    #Generates the GUI interface for user validation and simulation
    AI_Agent.schedule_interviews(controller)

    #Schedules interviews and sends follow up emails
    AI_Agent.monitor_email(controller)

    #Displays final inbox
    print("Final inbox values")
    print("--------------------------------------------------------------------------------")
    AI_Agent.email_app.check_inbox()