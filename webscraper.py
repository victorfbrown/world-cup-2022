import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import string
import time
from datetime import datetime
from datetime import date
import pytz

IST = pytz.timezone('US/Central')
today = date.today()
month = str(today.month)[:3]
day = str(today.day)

scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    '../credentials/client_secret_personal.json', scope)
client = gspread.authorize(creds)
alphabet = list(string.ascii_uppercase)
num = list(range(1, 27))
alphanum_dict = {}
for number, letter in zip(num, alphabet):
    alphanum_dict[letter] = number


# Scrapes data from FIFA World Cup 2022 Wikipedia Page
URL = "https://en.wikipedia.org/wiki/2022_FIFA_World_Cup"

page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

# Finds all Final Scores
all_matches = soup.find_all("th", class_="fscore")

list_scores = []
for match in all_matches:
    indiv_dict = {}
    score = match.text
    score = score.strip(' (a.e.t)')
    both_scores = score.split("–")
    a = match.a
    text_descriptor = a.get('href')
    split_text = text_descriptor.split("#")
    both_teams = split_text[1]
    split = both_teams.split("vs")
    # Only adds to the dictionary if the game has happened
    if len(split) == 2 and len(both_scores) == 2:
        first_team = split[0][:-1]
        second_team = split[1][1:]
        first_team = first_team.replace("_", " ")
        second_team = second_team.replace("_", " ")
        indiv_dict[first_team] = int(both_scores[0])
        indiv_dict[second_team] = int(both_scores[1])
        # Adds a dict of type {team1:score1, team2:score2}
        list_scores.append(indiv_dict)


def find_result(team1, pred_score1, pred_score2, team2):
    score = 0
    for match in list_scores:  # iterates through all possible match scores
        if team1 in match.keys() and team2 in match.keys():  # checks if both teams are in the dictionary
            pred_score_diff = pred_score1-pred_score2
            actual_score1 = match[team1]
            actual_score2 = match[team2]
            actual_score_diff = actual_score1-actual_score2

            # correct result
            if actual_score1 > actual_score2 and pred_score1 > pred_score2:
                score += 2
            elif actual_score1 == actual_score2 and pred_score1 == pred_score2:
                score += 2
            elif actual_score1 < actual_score2 and pred_score1 < pred_score2:
                score += 2

            # correct goal difference
            if pred_score_diff == actual_score_diff:
                score += 1

            # correct goals predicted for team1
            if pred_score1 == actual_score1:
                score += 1

            # correct goals predicted for team2
            if pred_score2 == actual_score2:
                score += 1

            if score == 5:
                score += 2
            break

    return score


group_locations = [("A3", "D8"), ("F3", "I8"), ("K3", "N8"), ("P3", "S8"),
                   ("A11", "D16"), ("F11", "I16"), ("K11", "N16"), ("P11", "S16")]

group_dict = {}
for loc, group in zip(group_locations, alphabet[:8]):
    group_dict[group] = loc


def score_group(group, spec_sheet):
    top_left_idx = group_dict[group][0]
    bottom_right_idx = group_dict[group][1]
    top_left_row = int(top_left_idx[1:])
    top_left_col = alphanum_dict[top_left_idx[0]]
    bottom_right_row = int(bottom_right_idx[1:])
    bottom_right_col = alphanum_dict[bottom_right_idx[0]]

    for row in range(top_left_row, bottom_right_row+1):
        team1 = spec_sheet.cell(row, top_left_col).value
        score1 = int(spec_sheet.cell(row, top_left_col+1).value)
        score2 = int(spec_sheet.cell(row, bottom_right_col-1).value)
        team2 = spec_sheet.cell(row, bottom_right_col).value
        if team1 == "USA":
            team1 = "United States"
        if team2 == "USA":
            team2 = "United States"
        score = find_result(team1, score1, score2, team2)
        print(team1, "vs", team2, end="\n"*2)
        spec_sheet.update_cell(row, bottom_right_col+1, score)
    now = datetime.now(IST)
    hour = now.hour if now.hour < 12 else now.hour % 12
    update_string = month + "/" + day + \
        " at " + str(hour) + ":"+str(now.minute)
    spec_sheet.update_cell(20, 1, update_string)


def score_sheet(sheet, groups=alphabet[:8]):
    print(sheet)
    for group in groups:
        score_group(group, sheet)
        time.sleep(30)


victor = client.open('Soccer Predictions').worksheet("Victor - WC22")
daniel = client.open('Soccer Predictions').worksheet("Daniel - WC22")
niko = client.open('Soccer Predictions').worksheet("Niko - WC22")
guillermo = client.open('Soccer Predictions').worksheet("Guillermo - WC22")
luca = client.open('Soccer Predictions').worksheet("Luca - WC22")

all_sheets = [victor, daniel, niko, luca, guillermo]


def score_all_sheets(sheets, groups=alphabet[:8]):
    for sheet in sheets:
        score_sheet(sheet, groups)


score_all_sheets(all_sheets)