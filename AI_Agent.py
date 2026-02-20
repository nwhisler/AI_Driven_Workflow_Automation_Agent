import ollama
import os
import subprocess
import threading
import json
import asyncio
import sys
import subprocess
import re
import tkinter as tk
from aiosmtpd.controller import Controller
from smtplib import SMTP
from pypdf import PdfReader
from pydantic import BaseModel, Field
from email_dir.Email import Email_APP, SMTP_Handler
from calendar_dir.Calendar import Calendar_App
from datetime import datetime, date
from typing import Optional, Dict, Tuple, List, Any
from dateutil.relativedelta import relativedelta
from utils.util import find_project_root, load_prompts
from pathlib import Path
from copy import deepcopy


#Each extraction class establishes variables to extract values from the LLM response to a prompt.

class JobEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    is_internship: Optional[bool] = None

class EducationEntry(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    school: Optional[str] = None
    year: Optional[int] = None

class DataExtraction(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    education: List[EducationEntry] = Field(default_factory=list)
    work: List[JobEntry] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)

class AvailableDates(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None

class AvailableDatesList(BaseModel):
    slots: List[AvailableDates] = None

class InterviewSetup(BaseModel):
    interview_message:str

class ResponseVariables(BaseModel):
    scheduled_interview: bool
    date_chosen: Optional[str] = None
    time_chosen: Optional[str] = None

class CompareDates(BaseModel):
    date_in_list:bool

class TimeChosen(BaseModel):
    message:str
    new_date_provided:bool
    new_time_provided:bool

class IncludesDate(BaseModel):
    includes_dates:bool

#Loads state variables

def load_state_vars(state: Dict[str, Any]) -> Dict[str, Any]:

    EMAIL_APP = Email_APP()
    CALENDAR_APP = Calendar_App()

    US_STATES = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
        "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
        "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
        "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
        "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
        "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
        "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
        "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
        "district of columbia": "DC", "washington dc": "DC", "washington, dc": "DC",
        "d.c.": "DC", "dc": "DC",
    }

    USPS = set(US_STATES.values())

    BACHELORS_DEGREE_KEYWORDS = (

        "bs", "b.s", "bsc", "b.sc", "ba", "b.a", "beng", "b.eng", "bba", "bfa","barch", "b.arch", "bcom", "b.com", "bpharm", "b.pharm", "btech", "b.tech",
        "bed", "b.ed", "bcs","bstat", "bmath", "bachelor", "bachelors", "bachelor's", "bachelor of science", "bachelor of arts", "bachelor of engineering", "bachelor of business administration",
        "bachelor of fine arts", "bachelor of architecture", "bachelor of commerce", "bachelor of technology", "bachelor of education", "bachelor of computer science",
        "bachelor of mathematics", "bachelor of statistics"
    )


    MASTERS_DEGREE_KEYWORDS = (
        "ms", "msc", "m.s", "m.sc", "ma", "m.a", "meng", "m.eng", "mba", "mfa", "mph", "mpp", "mpa", "mfin", "m.finance", "mscs", "mcs", "m.c.s",
        "mres", "med", "m.ed", "mlis", "mlis", "mstat", "m.stats", "m.arch", "march", "master", "masters", "master's", "master of science", "master of arts", "master of engineering",
        "master of business administration", "master of public health", "master of public policy", "master of public administration", "master of fine arts",
        "master of education", "master of architecture", "master of finance", "master of statistics",
    )

    PHD_KEYWORDS = (
        "phd", "ph.d", "dphil", "d.phil", "edd", "ed.d", "dba", "dsc", "d.sc", "dsci", "d.sci", "engd", "eng.d", "thd", "th.d",
        "md", "m.d", "jd", "j.d", "dds", "d.d.s", "dmd", "d.m.d",  "od", "o.d", "dvm", "d.v.m", "dpt", "d.p.t", "psyd", "psy.d",
        "pharmd", "pharm.d", "doctor", "doctors", "doctor's", "doctor of philosophy", "doctor of education", "doctor of business administration", "doctor of science",
        "doctor of engineering", "doctor of theology", "doctor of medicine", "doctor of dental surgery", "doctor of dental medicine",
        "doctor of veterinary medicine", "doctor of pharmacy", "doctor of physical therapy", "doctor of psychology",
    )

    MONTHS = {
        "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
        "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
    }

    dates_degrees = {}
    dates_degrees["US_STATES"] = US_STATES
    dates_degrees["USPS"] = USPS
    dates_degrees["BACHELORS_DEGREE_KEYWORDS"] = BACHELORS_DEGREE_KEYWORDS
    dates_degrees["MASTERS_DEGREE_KEYWORDS"] = MASTERS_DEGREE_KEYWORDS
    dates_degrees["PHD_KEYWORDS"] = PHD_KEYWORDS
    dates_degrees["MONTHS"] = MONTHS

    DATE_RE = re.compile(
        r"""
        \b
        (?:
            (
                jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
                jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|
                nov(?:ember)?|dec(?:ember)?
            )
            \.?\s+
            (?:\d{1,2}(?:st|nd|rd|th)?\,?\s+)?
            (\d{4})
        |
            (\d{4})\s+
            (
                jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
                jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|
                nov(?:ember)?|dec(?:ember)?
            )
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE
    )

    RE_ISO_YEAR_MONTH = re.compile(r"\b(\d{4})[-/](\d{1,2})\b")          
    RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR = re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b") 
    RE_MONTH_YEAR = re.compile(r"\b(\d{1,2})[-/](\d{4})\b")      

    TIME_PATTERN = re.compile(r"\d{2}:\d{2}")

    regex_dict = {}
    regex_dict["DATE_RE"] = DATE_RE
    regex_dict["RE_ISO_YEAR_MONTH"] = RE_ISO_YEAR_MONTH
    regex_dict["RE_MONTH_YEAR"] = RE_MONTH_YEAR
    regex_dict["RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR"] = RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR 

    return {"EMAIL_APP": EMAIL_APP, "CALENDAR_APP": CALENDAR_APP, "dates_degrees": dates_degrees, "regex_dict": regex_dict, "TIME_PATTERN": TIME_PATTERN}

#Starts the ollama server
def run_ollama_serve():
    subprocess.Popen(["ollama", "serve"])

#Threads the ollama server

def start_server(state: Dict[str, Any]) -> Dict[str, Any]:

    thread = threading.Thread(target=run_ollama_serve)
    thread.start()
    import time
    time.sleep(5)

    return {"thread": thread}

#Parses all the text from a resume

def read_resume(path: Path) -> str:

    str_path = str(path)
    reader = PdfReader(str_path)

    text = "Resume text:\n\n"
    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text

#LLM uses prompt to extract values such as name, email, education, work experience, and location.

def parse_resume(system_prompt: str, user_prompt: str) -> Dict[str, Any]:

    response = ollama.chat(model='llama3', messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ], format=DataExtraction.model_json_schema())
    
    data = json.loads(response['message']['content'])

    return data

#Parses resume and appends extracted values as previously described in a list of dictionaries.

def resume_data(state: Dict[str, Any]) -> Dict[str, Any]:

    print("--------------------------------------------------------------------------------")
    print("-------------------Reading-Resumes-and-Generating-Candidate-Profiles------------")
    print("--------------------------------------------------------------------------------")

    if not isinstance(state, dict):
        state = {}

    regex_dict = state.get("regex_dict")
    if not isinstance(regex_dict, dict):
        regex_dict = {}

    dates_degrees = state.get("dates_degrees")
    if not isinstance(dates_degrees, dict):
        dates_degrees = {}

    prompts = state.get("prompts")
    if not isinstance(prompts, dict):
        prompts = {}

    system_prompt = prompts.get("parser")
    system_prompt = system_prompt.strip() if isinstance(system_prompt, str) else ""

    root = state.get("root")
    root = Path(root.strip()).resolve() if isinstance(root, str) else ""
    if not root:
        root = find_project_root()

    resumes_dir = root / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)

    candidates: List[Dict[str, Any]] = []
    resumes = os.listdir("./resumes")

    for resume in resumes:
        resume_path = resumes_dir / resume
        user_prompt = read_resume(resume_path)
        data = parse_resume(system_prompt, user_prompt) 
        candidate_profile = complete_candidate_profile(data, regex_dict, dates_degrees)
        candidates.append(candidate_profile)

    return {"candidates": candidates}

#Transforms a variable state name into it's corresponding abbreviation.

def normalize_state(value: Optional[str], USPS: Optional[set], US_STATES: Dict[str, Any]) -> Optional[str]:
    
    if value is None:
        return None

    string = value.strip()
    if not string:
        return None

    str_clean = re.sub(r"[.,;:]+$", "", string).strip()

    if len(str_clean) == 2 and str_clean.upper() in USPS:
        return str_clean.upper()

    key = re.sub(r"\s+", " ", str_clean).strip().lower()
    
    return US_STATES.get(key, value)

#Removes punctation and strips out degree literal value such as bachelor(s) or ms

def normalize_degree(text: str) -> str:
    
    text = text.lower()
    text = re.sub(r"[.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    
    return text.split()[0].strip()


#Normalizes each candidates profile

def complete_candidate_profile(data: Dict[str, Any], regex_dict: Dict[str, Any], dates_degrees: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(data, dict):
        data = {}

    if not isinstance(regex_dict, dict):
        regex_dict = {}

    if not isinstance(dates_degrees, dict):
        dates_degrees = {}

    USPS = dates_degrees.get("USPS")
    US_STATES = dates_degrees.get("US_STATES")
    BACHELORS_DEGREE_KEYWORDS = dates_degrees.get("BACHELORS_DEGREE_KEYWORDS")
    MASTERS_DEGREE_KEYWORDS = dates_degrees.get("MASTERS_DEGREE_KEYWORDS")
    PHD_KEYWORDS = dates_degrees.get("PHD_KEYWORDS")

    profile: Dict[str, Any] = {}

    name = data.get("name")
    name = name.strip() if isinstance(name, str) else ""
    if not name:
        return {}
    profile["name"] = name
    
    email = data.get("email")
    email = email.strip() if isinstance(email, str) else ""
    if not email:
        return {}
    profile["email"] = email

    city = data.get("city")
    city = city.strip() if isinstance(city, str) else ""
    profile["city"] = city

    state = data.get("state")
    state = state.strip() if isinstance(state, str) else ""
    state = normalize_state(state, USPS, US_STATES)
    profile["state"] = state

    country = data.get("country")
    country = country.lower().strip() if isinstance(country, str) else ""
    profile["country"] = country

    work = data.get("work")
    if not isinstance(work, list):
        work = []
    job_list = []
    for job in work:
        job_dictionary = {}
        if isinstance(job, dict):
            title = job.get("title")
            title = title.strip() if isinstance(title, str) else ""
            if not title:
                continue
            job_dictionary["title"] = title
            company = job.get("company")
            company = company.strip() if isinstance(company, str) else ""
            if not company:
                continue
            job_dictionary["company"] = company
            start = job.get("start")
            start = start.strip() if isinstance(start, str) else ""
            if not start:
                continue
            job_dictionary["start"] = start
            end = job.get("end")
            end = end.strip() if isinstance(end, str) else ""
            if not end:
                continue
            job_dictionary["end"] = end
            is_internship = job.get("is_internship")
            if not isinstance(is_internship, bool):
                is_internship = False
            is_internship = bool(is_internship)
            job_dictionary["is_internship"] = is_internship
            job_list.append(job_dictionary)
    work = job_list
    profile["work"] = work

    education = data.get("education")
    if not isinstance(education, list):
        education = []
    education_list = []
    for edu in education:
        if isinstance(edu, dict):
            edu_dictionary = {}
            degree = edu.get("degree")
            degree = degree.strip() if isinstance(degree, str) else ""
            if not degree:
                continue
            edu_dictionary["degree"] = degree
            field = edu.get("field")
            field = field.strip() if isinstance(field, str) else ""
            edu_dictionary["field"] = field
            school = edu.get("school")
            school = school.strip() if isinstance(school, str) else ""
            if not school:
                continue
            edu_dictionary["school"] = school
            year = edu.get("year")
            if not isinstance(year, (int, float)):
                year = None
            if year is None:
                continue
            else:
                year = int(year)
            edu_dictionary["year"] = year
            education_list.append(edu_dictionary)
    education = education_list
    profile["education"] = education

    projects = data.get("projects")
    if not isinstance(projects, list):
        projects = []
    projects = [string for string in projects if isinstance(string, str)]
    profile["has_projects"] = len(projects) > 2

    is_located_in_the_US = False
    if country in ("us", "usa", "united states", "u.s", "u.s.a"):
        is_located_in_the_US = True
    else:
        if state in USPS:
            is_located_in_the_US = True
    profile["is_located_in_the_US"] = is_located_in_the_US
    
    has_bachelor = False
    has_masters = False
    has_doctorate = False

    for edu in education:
        degree = edu.get("degree").lower().strip()
        degree = normalize_degree(degree)
        if degree in BACHELORS_DEGREE_KEYWORDS:
            has_bachelor = True
        elif degree in MASTERS_DEGREE_KEYWORDS:
            has_masters = True
        elif degree in PHD_KEYWORDS:
            has_doctorate = True
    profile["has_bachelor"] = has_bachelor
    profile["has_masters"] = has_masters
    profile["has_doctorate"] = has_doctorate

    profile["has_three_years_work_experience"], profile["has_five_years_work_experience"] = extract_work_experience(work, regex_dict, dates_degrees)

    return profile

#As stated it calculates how long someone has worked.

def extract_work_experience(work: List[Dict[str, Any]], regex_dict: Dict[str, Any], dates_degrees: Dict[str, Any]) -> bool:

    three_years = False
    five_years = False

    working_years = working_months = 0
    for job in work:
        if isinstance(job, dict):
            start = job.get("start")
            start = start.strip() if isinstance(start, str) else ""
            if not start:
                continue
            start_year, start_month = parse_date(start, regex_dict, dates_degrees)
            start_date = date(start_year, start_month, 1)
            end = job.get("end")
            end = end.strip() if isinstance(end, str) else ""
            if not end:
                continue
            end_year, end_month = parse_date(end, regex_dict, dates_degrees)   
            end_date = date(end_year, end_month, 1)
            difference = relativedelta(end_date, start_date)
            working_years += difference.years
            working_months += difference.months
    working_years += (working_months % 12)

    if working_years > 2:
        three_years = True
    
    if working_years > 4:
        five_years = True
    
    return three_years, five_years

#Extracts dates from degrees
        
def parse_date(text: Optional[str], regex_dict: Dict[str, Any], dates_degrees: Dict[str, Any]) -> Optional[Tuple[int, int]]:

    MONTHS = dates_degrees.get("MONTHS")

    DATE_RE = regex_dict.get("DATE_RE")
    RE_ISO_YEAR_MONTH = regex_dict.get("RE_ISO_YEAR_MONTH")
    RE_MONTH_YEAR = regex_dict.get("RE_MONTH_YEAR")
    RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR  = regex_dict.get("RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR")

    text = text.lower().strip() if isinstance(text, str) else ""
    
    if not text:
        return None

    if "present" in text or "current" in text:
        now = datetime.utcnow()
        return (now.year, now.month)

    parsed_date = DATE_RE.search(text)
    if parsed_date:
        groups = parsed_date.groups()
        if groups[0] and groups[1]:
            month = groups[0]
            try:
                year = int(groups[1])
            except:
                year = None
        else:
            month = groups[3]
            try:
                year = int(groups[2])
            except:
                year = None

        month = MONTHS.get(month.lower().rstrip("."), None)
        if year is not None and month is not None:
            return (year, month)

    parsed_date = RE_ISO_YEAR_MONTH.search(text)
    if parsed_date:
        try:
            year = int(parsed_date.group(1))
            month = int(parsed_date.group(2))
        except:
            year = month = None

        if year is not None and month is not None:
            return (year, month)

    parsed_date = RE_MONTH_YEAR.search(text)
    if parsed_date:
        try:
            month = int(parsed_date.group(1))
            year = int(parsed_date.group(2))
        except:
            month = year = None

        if month is not None and year is not None:
            return (year, month)

    parsed_date = RE_MONTH_DAY_YEAR__DAY_MONTH_YEAR.search(text)
    if parsed_date:
        try:
            day = int(parsed_date.group(1))
            month = int(parsed_date.group(2))
            year = int(parsed_date.group(3))
            if month > 12:
                temp_month = day
                day = month
                month = temp_month
        except:
            day = month = year = None
        
        if day is not None and month is not None and year is not None:
            return (year, month)

    return None

#Filters out candidates based on qualifications.

def pass_conditions(candidate: Dict[str, Any]) -> bool:

    is_located_in_the_US = candidate.get("is_located_in_the_US")
    if not isinstance(is_located_in_the_US, bool):
        is_located_in_the_US = False

    has_bachelor = candidate.get("has_bachelor")
    if not isinstance(has_bachelor, bool):
        has_bachelor = False

    has_masters = candidate.get("has_masters")
    if not isinstance(has_masters, bool):
        has_masters = False

    has_doctorate = candidate.get("has_doctorate")
    if not isinstance(has_doctorate, bool):
        has_doctorate = False

    has_three_years_work_experience = candidate.get("has_three_years_work_experience")
    if not isinstance(has_three_years_work_experience, bool):
        has_three_years_work_experience = False

    has_five_years_work_experience = candidate.get("has_five_years_work_experience")
    if not isinstance(has_five_years_work_experience, bool):
        has_five_years_work_experience = False

    has_projects = candidate.get("has_projects")
    if not isinstance(has_projects, bool):
        has_projects = False

    if (has_doctorate or has_masters) and is_located_in_the_US:
        return True

    elif (has_bachelor and has_five_years_work_experience):
        return True

    elif (has_doctorate or has_masters) and (has_three_years_work_experience or has_projects):
        return True

    else:
        return False

#Iterates through candidates and filters out a list of final candidates

def filter_candidates(state: Dict[str, Any]) -> Dict[str, Any]:

    print("--------------------------------------------------------------------------------")
    print("-------------------Filtering Candidates-----------------------------------------")
    print("--------------------------------------------------------------------------------")

    candidates = state.get("candidates")
    if not isinstance(candidates, list):
        candidates = []

    final_candidates = []

    for candidate in candidates:
        passed = pass_conditions(candidate)
        if passed:
            final_candidates.append(candidate)

    FINAL_CANDIDATE_AMOUNT = len(final_candidates)
    return {"final_candidates": final_candidates, "FINAL_CANDIDATE_AMOUNT": FINAL_CANDIDATE_AMOUNT}

#Generates a list of available datetimes with respect to an unavailable datetime list compiled from calendar data.

def date_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:

    print("--------------------------------------------------------------------------------")
    print("-------------------Generating-Dates-and-Times-for-Interviews--------------------")
    print("--------------------------------------------------------------------------------")

    if not isinstance(state, dict):
        state = {}

    CALENDAR_APP = state.get("CALENDAR_APP", None)
    if CALENDAR_APP is None:
        CALENDAR_APP = Calendar_App()

    prompts = state.get("prompts")
    if not isinstance(prompts, dict):
        prompts = {}

    system_prompt = prompts.get("dates")
    system_prompt = system_prompt.strip() if isinstance(system_prompt, str) else ""

    current_dir = Path(__file__).resolve().parent
    calendar_dir = current_dir / "calendar_dir"
    calendar_dir.mkdir(parents=True, exist_ok=True)
    calendar_path = calendar_dir / "calendar.json"

    FINAL_CANDIDATE_AMOUNT = state.get("FINAL_CANDIDATE_AMOUNT")
    if not isinstance(FINAL_CANDIDATE_AMOUNT, (int, float)):
        FINAL_CANDIDATE_AMOUNT = 0
    FINAL_CANDIDATE_AMOUNT = int(FINAL_CANDIDATE_AMOUNT)

    number_of_datetimes_to_generate = 6 * FINAL_CANDIDATE_AMOUNT

    data = CALENDAR_APP.data_extraction(calendar_path)
    if not isinstance(data, list):
        data = []
    datetimes_list = []
    unavailable_datetimes = {}
    for value in data:
        if isinstance(value, dict):
            date = value.get("date")
            date = date.strip() if isinstance(date, str) else ""
            if not date:
                continue
            time = value.get("time")
            time = time.strip() if isinstance(time, str) else ""
            if not time:
                continue
            current_datetime = {"date": date, "time": time}
            datetimes_list.append(current_datetime)
    unavailable_datetimes["unavailable_datetimes"] = datetimes_list
    unavailable_json = json.dumps(unavailable_datetimes, sort_keys=True, separators=(",", ":"))

    datetimes_after = {}
    set_datetime = datetime.now()
    current_date = set_datetime.strftime("%Y-%m-%d")
    current_time = set_datetime.strftime("%H-%M")
    datetimes_after["current_date"] = current_date
    datetimes_after["current_time"] = current_time
    datetime_after_json = json.dumps(datetimes_after, sort_keys=True, separators=(",", ":"))

    user_prompt = f"""
                Unavailable dates and times:\n 
                {unavailable_json}
                \n\n\n 
                Current date and time:\n 
                {datetime_after_json}
                \n\n\n 
                Number of slots to generate:\n
                {number_of_datetimes_to_generate}
                """
    response = ollama.chat(model='llama3', messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ], format=AvailableDatesList.model_json_schema())

    json_data = json.loads(response['message']['content'])
    available_datetimes = json_data.get("slots")

    return {"available_datetimes": available_datetimes}     

#Generates the congratulation email that also sends available dates times to schedule an interview.

def generate_congratulations_email(name: str, available_datetimes: List[Dict[str, Any]], system_prompt: str, company: str) -> str:

    user_prompt = {}
    user_prompt["name"] = name
    user_prompt["available_datetimes"] = available_datetimes
    user_prompt["company"] = company 
    user_prompt["role"] = "Researcher"
    user_prompt_json = json.dumps(user_prompt, sort_keys=True, separators=(",", ":"))

    response = ollama.chat(model='llama3', messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt_json
        }
    ])
    
    interview_response = response['message']['content'] 

    return interview_response

#Sends the interview scheduling emails to the list of final candidates.

def send_candidate_emails(state: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(state, dict):
        state = {}

    root = state.get("root")
    root = Path(root.strip()).resolve() if isinstance(root, str) else ""
    if not root:
        root = find_project_root()

    scheduled_interviews_dir_path = root / "scheduled_interviews"
    scheduled_interviews_dir_path.mkdir(parents=True, exist_ok=True)

    scheduled_interviews_file_path = scheduled_interviews_dir_path / "scheduled_interviews.json"
    if not scheduled_interviews_file_path.exists() or not scheduled_interviews_file_path.is_file():
        scheduled_interviews_file_path.write_text("{}", encoding="utf-8")

    with open(str(scheduled_interviews_file_path), "r") as fh:
        json_object = json.load(fh)

    if not isinstance(json_object, dict):
        json_object = {}

    INTERVIEW_SCHEDULED = json_object.get("INTERVIEW_SCHEDULED")
    if not isinstance(INTERVIEW_SCHEDULED, list):
        INTERVIEW_SCHEDULED = []

    scheduled_emails = [entry.get("Email") for entry in INTERVIEW_SCHEDULED if isinstance(entry, dict)]

    EMAIL_APP = state.get("EMAIL_APP", None)
    if EMAIL_APP is None:
        EMAIL_APP = Email_APP()

    final_candidates = state.get("final_candidates")
    if not isinstance(final_candidates, list):
        final_candidates = []

    FINAL_CANDIDATE_AMOUNT = state.get("FINAL_CANDIDATE_AMOUNT")
    if not isinstance(FINAL_CANDIDATE_AMOUNT, (int, float)):
        FINAL_CANDIDATE_AMOUNT = 0
    FINAL_CANDIDATE_AMOUNT = int(FINAL_CANDIDATE_AMOUNT)

    available_datetimes = state.get("available_datetimes")
    if not isinstance(available_datetimes, list):
        available_datetimes = []

    prompts = state.get("prompts")
    if not isinstance(prompts, dict):
        prompts = {}

    system_prompt = prompts.get("congratulations")
    system_prompt = system_prompt.strip() if isinstance(system_prompt, str) else ""

    print("--------------------------------------------------------------------------------")
    print("-------------------Generating-and-Sending-Interview-Invite-Emails---------------")
    print("--------------------------------------------------------------------------------")

    controller = Controller(SMTP_Handler(), hostname='127.0.0.1', port=8025, ready_timeout=5.0)
    controller.start()

    if int(FINAL_CANDIDATE_AMOUNT) != 0:
        ratio = len(available_datetimes) // FINAL_CANDIDATE_AMOUNT
    else:
        ratio = 0  
    start_idx = 0

    if ratio >= 6:
        end_idx = 6
    elif ratio >= 4:
        end_idx = 4
    elif ratio >= 2:
        end_idx = 2
    else:
        if ratio == 0:
            end_idx = 0
        else:
            end_idx = 1

    for candidate in final_candidates:

        if start_idx >= len(available_datetimes):
            continue
        elif end_idx >= len(available_datetimes):
            available_datetimes_subset = available_datetimes[start_idx:]
        else:
            available_datetimes_subset = available_datetimes[start_idx:end_idx]

        name = candidate.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if not name:
            continue
        email = candidate.get("email")
        email = email.strip() if isinstance(email, str) else ""
        if not email:
            continue
        company = "tutelage"
        if email not in scheduled_emails:
            INTERVIEW_SCHEDULED.append({"Name": name, "Email": email, "Scheduled": False})
            message = generate_congratulations_email(name, available_datetimes_subset, system_prompt, company)
            EMAIL_APP.send_mail(controller.hostname, controller.port, message, "hr@tutelage.com", email)
        else:
            for entry in INTERVIEW_SCHEDULED:
                entry_email = entry.get("Email")
                entry_email = entry_email.strip() if isinstance(entry_email, str) else ""
                if not entry_email:
                    continue
                entry_scheduled = entry.get("Scheduled")
                if not isinstance(entry_scheduled, bool):
                    entry_scheduled = True
                if entry_email == email and not entry_scheduled:
                    message = generate_congratulations_email(name, available_datetimes_subset, system_prompt, company)
                    EMAIL_APP.send_mail(controller.hostname, controller.port, message, "hr@tutelage.com", email)
        start_idx += ratio
        end_idx += ratio

    return {"controller": controller, "INTERVIEW_SCHEDULED": INTERVIEW_SCHEDULED}

#Creates a GUI for the email so the user can validate the emails were sent
#and simulate a candidate returning an email for it to be scheduled by the AI Agent.

def repsond_to_interviews(state: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(state, dict):
        state = {}

    controller = state.get("controller")

    EMAIL_APP = state.get("EMAIL_APP", None)
    if EMAIL_APP is None:
        EMAIL_APP = Email_APP()

    FINAL_CANDIDATE_AMOUNT = state.get("FINAL_CANDIDATE_AMOUNT")
    if not isinstance(FINAL_CANDIDATE_AMOUNT, (int, float)):
        final_candidates_list = state.get("final_candidates")
        if not isinstance(final_candidates_list, list):
            final_candidates_list = []
        FINAL_CANDIDATE_AMOUNT = len(final_candidates_list)

    print("--------------------------------------------------------------------------------")
    print("-------------------Bringing-up-inbox-to-validate-emails-were-sent---------------")
    print("--------------------------------------------------------------------------------")
    print(f"-------------------There-are-{FINAL_CANDIDATE_AMOUNT}-final-candidates---------------------------------")
    print("--------------------------------------------------------------------------------")
    EMAIL_APP.check_inbox()
    prompt = "-------------------How-many-simulated-responses-would-you-like-to-send:"
    action = input(prompt)
    total_len = len(prompt) + len(action)
    remaining_dashes = 80 - total_len
    print(f"\033[1A\033[{total_len}C" + "-" * remaining_dashes)
    print("--------------------------------------------------------------------------------")
    
    for idx in range(int(action)):
        EMAIL_APP.send(controller.hostname, controller.port)

    print("--------------------------------------------------------------------------------")
    print("-------------------Validating-simulated-emails-were-sent------------------------")
    print("--------------------------------------------------------------------------------")
    EMAIL_APP.check_inbox()

    return {}

#Parses the email response for the date along with the time the candidate chose for their interview.

def parse_email_response(system_prompt: str, message: str, available_datetimes: List[Dict[str, Any]]) -> Tuple[bool, str, str]:

    user_prompt = {}
    user_prompt["message"] = message
    user_prompt["available_datetimes"] = available_datetimes

    user_prompt_json = json.dumps(user_prompt, sort_keys=True, separators=(",", ":"))

    response = ollama.chat(model='llama3', messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt_json
        }
    ], format=ResponseVariables.model_json_schema())
    
    data = json.loads(response['message']['content'])
    scheduled_interview = data.get("scheduled_interview", None)
    date_chosen = data.get("date_chosen", None)
    time_chosen = data.get("time_chosen", None)

    return scheduled_interview, date_chosen, time_chosen
    
#Updates calendar data

def update_calendar(update_dict: Dict[str, Any], CALENDAR_APP: type(Calendar_App), path: Path) -> None:

    CALENDAR_APP.file_handling(path, update_dict)

#Returns whether an interview has been scheduled yet.

def scheduled(mail_from: str, INTERVIEW_SCHEDULED: List[Dict[str, Any]]) -> bool:

    is_scheduled = False

    for entry in INTERVIEW_SCHEDULED:
        if isinstance(entry, dict):
            email = entry.get("Email")
            email = email.strip() if isinstance(email, str) else ""
            if not email:
                continue
            if mail_from == email:
                is_scheduled = entry.get("Scheduled")
                if not isinstance(is_scheduled, bool):
                    is_scheduled = False  
    return is_scheduled

#Updates the INTERVIEW_SCHEDULED list to confirm a candidate has had an interview scheduled.

def update_scheduled_interview_list(mail_from: str, INTERVIEW_SCHEDULED: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    for idx, entry in enumerate(INTERVIEW_SCHEDULED):
        if isinstance(entry, dict):
            entry_email = entry.get("Email")
            entry_email = entry_email.strip() if isinstance(entry_email, str) else ""
            if not entry_email:
                continue
            if entry_email == mail_from:
                INTERVIEW_SCHEDULED[idx]["Scheduled"] = True

    return INTERVIEW_SCHEDULED

# Validates the chosen datetimes are valid and correspondingly scheduled them and then pulls up a calendar GUI to validate scheduling.
# There should not be any overlap in scheduling as available_datetimes are subsectioned for independent values for each candidate before sending.

def schedule_interviews(state: Dict[str, Any]) -> Dict[str, Any]:

    print("--------------------------------------------------------------------------------")
    print("-------------------Scheduling-Interviews----------------------------------------")
    print("--------------------------------------------------------------------------------")

    was_scheduled = False

    if not isinstance(state, dict):
        state = {}

    EMAIL_APP = state.get("EMAIL_APP", None)
    if EMAIL_APP is None:
        EMAIL_APP = Email_APP()

    CALENDAR_APP = state.get("CALENDAR_APP", None)
    if CALENDAR_APP is None:
        CALENDAR_APP = Calendar_App()

    root = state.get("root")
    root = Path(root.strip()).resolve() if isinstance(root, str) else ""
    if not root:
        root = find_project_root()

    calendar_dir = root / "calendar_dir"
    calendar_dir.mkdir(parents=True, exist_ok=True)
    calendar_json_path = calendar_dir / "calendar.json"

    email_dir = root / "email_dir"
    email_dir.mkdir(parents=True, exist_ok=True)
    email_json_path = email_dir / "email.json"

    prompts = state.get("prompts")
    if not isinstance(prompts, dict):
        prompts = {}

    system_prompt = prompts.get("response")
    system_prompt = system_prompt.strip() if isinstance(system_prompt, str) else ""

    available_datetimes = state.get("available_datetimes")
    if not isinstance(available_datetimes, list):
        available_datetimes = []

    taken_times = []
    available_datetimes_list = [(entry.get("date"), entry.get("time")) for entry in available_datetimes if isinstance(entry, dict)]

    INTERVIEW_SCHEDULED = state.get("INTERVIEW_SCHEDULED")
    if not isinstance(INTERVIEW_SCHEDULED, list):
        INTERVIEW_SCHEDULED = []

    RESCHEDULE = []

    name_email_index = {}
    email_addresses = []
    for value in INTERVIEW_SCHEDULED:
        if isinstance(value, dict):
            value_name = value.get("Name")
            value_name = value_name.strip() if isinstance(value_name, str) else ""
            if not value_name:
                continue
            value_email = value.get("Email")
            value_email = value_email.strip() if isinstance(value_email, str) else ""
            if not value_email:
                continue
            email_addresses.append(value_email)
            name_email_index[value_email] = value_name

    mail_list = EMAIL_APP.get_mail_list(path=email_json_path)
    calendar_data = CALENDAR_APP.data_extraction(calendar_json_path)
    dates = []
    date_event_index = {}
    for entry in calendar_data:
        if isinstance(entry, dict):
            entry_date = entry.get("Date")
            entry_date = entry_date.strip() if isinstance(entry_date, str) else ""
            if not entry_date:
                continue
            entry_event = entry.get("Event")
            entry_event = entry_event.strip() if isinstance(entry_event, str) else ""
            if not entry_event:
                continue
            if entry_date in date_event_index:
                date_event_index[entry_date].append(entry_event)
            else:
                date_event_index[entry_date]= [entry_event]
    dates = list(sorted(date_event_index.keys()))

    for mail in mail_list:

        mail_from = mail["From"]
        if not mail_from:
            continue
        mail_to = mail["To"]
        if not mail_to:
            continue
        mail_message = mail["Message"]
        if not mail_message:
            continue
        name = name_email_index.get(mail_from, None)
        if not name:
            continue
        is_scheduled = scheduled(mail_from, INTERVIEW_SCHEDULED)

        if (not is_scheduled) and (mail_from in email_addresses):
            scheduled_interview, date_chosen, time_chosen = parse_email_response(system_prompt, mail_message, available_datetimes)
            if not scheduled_interview or not date_chosen or not time_chosen:
                continue
            schedule_date_time = (date_chosen, time_chosen)
            if schedule_date_time in taken_times:
                RESCHEDULE.append({"Name": name, "Email": mail_from, "Date_Chosen": date_chosen, "Time_Chosen": time_chosen})
            else:
                INTERVIEW_SCHEDULED = update_scheduled_interview_list(mail_from, INTERVIEW_SCHEDULED)
                update_dict = {}
                update_dict["Name"] = name
                update_dict["Email"] = mail_from
                update_dict["Date"] = date_chosen
                update_dict["Time"] = time_chosen
                update_dict["Event"] = f"Interview with {name} at {time_chosen}"
                update_calendar(update_dict, CALENDAR_APP, calendar_json_path)
                was_scheduled = True
                taken_times.append(schedule_date_time)
                available_datetimes_list = [(entry[0], entry[1]) for entry in available_datetimes_list if isinstance(entry, tuple)]
           
    if was_scheduled:
        print("--------------------------------------------------------------------------------")
        print("-------------------Validating-Interviews-Scheduled------------------------------")
        print("--------------------------------------------------------------------------------")

        CALENDAR_APP.display_calendar()
        persist_secheduled_interviews(INTERVIEW_SCHEDULED, root)

    return {"INTERVIEW_SCHEDULED": INTERVIEW_SCHEDULED, "RESCHEDULE": RESCHEDULE, "available_datetimes": available_datetimes}

# Saves the current list of interviews scheduled.

def persist_secheduled_interviews(INTERVIEW_SCHEDULED: List[Dict[str, Any]], root: Path) -> None:

    final_interview_scheduled = []
    for entry in INTERVIEW_SCHEDULED:
        if entry not in final_interview_scheduled:
            final_interview_scheduled.append(entry)

    scheduled_interviews_dir_path = root / "scheduled_interviews"
    scheduled_interviews_dir_path.mkdir(parents=True, exist_ok=True)
    scheduled_interviews_file_path = scheduled_interviews_dir_path / "scheduled_interviews.json"

    with open(str(scheduled_interviews_file_path), "w") as fh:
        json.dump({"INTERVIEW_SCHEDULED": final_interview_scheduled}, fh, indent=2)

# Used to merge top level keys into a state object that a LangGraph would pass.

def combine_dicts(state: Dict[str, Any], dict_two: Dict[str, Any]) -> Dict[str, Any]:

    for key, value in dict_two.items():
        state[key] = value

    return state

if __name__ == "__main__":

    state = {}
    
    load_state_vars_dict = load_state_vars(state)
    state = combine_dicts(state, load_state_vars_dict)

    thread_dict = start_server(state)
    state = combine_dicts(state, thread_dict)

    prompt_dict = load_prompts(state)
    state = combine_dicts(state, prompt_dict)

    resume_dict = resume_data(state)
    state = combine_dicts(state, resume_dict)

    filter_dict = filter_candidates(state)
    state = combine_dicts(state, filter_dict)

    date_dict = date_retrieval(state)
    state = combine_dicts(state, date_dict)

    send_email_dict = send_candidate_emails(state)
    state = combine_dicts(state, send_email_dict)

    repsond_to_interviews_dict = repsond_to_interviews(state)
    state = combine_dicts(state, repsond_to_interviews_dict)

    # filtered_state = filter_state(state)

    # with open("state.json", "w") as fh:
    #     json.dump(filtered_state, fh, indent=2)

    # with open("state.json", "r") as fh:
    #     state = json.load(fh)
    
    schedule_interviews_dict = schedule_interviews(state)
    state = combine_dicts(state, schedule_interviews_dict)