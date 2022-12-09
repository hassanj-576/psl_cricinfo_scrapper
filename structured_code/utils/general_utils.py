# Givn a PSL result page, get URL for all matches
# Given a match URL, get all of its data
import traceback
import urllib

import requests
from bs4 import BeautifulSoup
import json
from collections import defaultdict
import copy

from tqdm import tqdm


def get_data_for_url(url):
    overs = defaultdict(list)
    previous_over = 20
    next_over = "stuf"
    while next_over:
        content = requests.get(url)
        next_over = content.json().get("nextInningOver")
        json_data = content.json()
        for comment in json_data.get("comments"):
            over = comment.get("overNumber")
            wicket_text = comment.get("dismissalText")
            if wicket_text:
                wicket_text = wicket_text.get("short")
            ball_obj = {
                "ball": comment.get("ballNumber"),
                "runs": comment.get("totalRuns"),
                "is_four": comment.get("isFour"),
                "is_six": comment.get("isSix"),
                "is_wicket": comment.get("isWicket"),
                "wicket": comment.get("dismissalType"),
                "wicket_text": wicket_text,
            }
            overs[over].append(ball_obj)
        if f"fromInningOver={previous_over}" in url:

            url = url.replace(
                f"fromInningOver={previous_over}", f"fromInningOver={next_over}"
            )
        else:
            url = f"{url}&fromInningOver={next_over}"

        previous_over = next_over

    return overs


# Given all Data, Generate the rows for the CSV from extracted data
def get_row_list_from_all_match_data(all_match_data, psl_year):
    all_rows = []
    for index, match in enumerate(all_match_data):
        for ining, value in match["data"].items():
            wickets = 0
            runs = 0
            for over in range(1, 21):
                if over in value:
                    for ball_result in reversed(value[over]):
                        row = {}
                        runs = runs + (ball_result["runs"])
                        ball = ball_result["ball"]
                        if ball_result["is_wicket"]:
                            wickets += 1
                        row = copy.deepcopy(ball_result)
                        row["psl_year"] = psl_year
                        row["match_number"] = index + 1
                        row["over"] = over
                        row["inning"] = ining
                        row["team_1"] = match["team_1"]
                        row["team_2"] = match["team_2"]
                        row["result"] = match["result"]
                        row["total_runs"] = runs
                        row["wickets"] = wickets
                        all_rows.append(row)
    return all_rows


def get_all_matches_data_from_url_list(url_list):
    all_match_data = []
    url_with_error = []
    for match_url in tqdm(url_list):
        print(match_url)
        try:
            url_split = match_url.split("/")
            series_id = url_split[4].split("-")[-1]
            match_id = url_split[5].split("-")[-1]
            match_data = defaultdict(int)
            team1, team2, result = get_winner_name(match_url)
            for inning_number in range(1, 3):
                score_url = f"https://hs-consumer-api.espncricinfo.com/v1/pages/match/comments?seriesId={series_id}&matchId={match_id}&inningNumber={inning_number}&commentType=ALL"
                match_data[inning_number] = get_data_for_url(score_url)
            all_match_data.append(
                {"team_1": team1, "team_2": team2, "result": result, "data": match_data}
            )

        except Exception as e:
            print("ERROR While running ")
            print(e)
            traceback.print_exc()
            url_with_error.append(match_url)
    return all_match_data, url_with_error


# Get the winner name from the header
def get_winner_name(url):
    content = requests.get(url).text
    soup = BeautifulSoup(content, "html.parser")
    match_info = soup.find(
        "div", {"class": "ds-text-compact-xxs ds-p-2 ds-px-4 lg:ds-py-3"}
    )
    winner = match_info.find(
        "p", {"class": "ds-text-tight-m ds-font-regular ds-truncate ds-text-typo-title"}
    )
    teams = match_info.find(
        "div", {"class": "ds-flex ds-flex-col ds-mt-3 md:ds-mt-0 ds-mt-0 ds-mb-1"}
    )
    team1, team2 = teams.find_all(
        "a", {"class": "ds-inline-flex ds-items-start ds-leading-none"}
    )
    team1 = team1.text
    team2 = team2.text
    if "abandoned" in winner.text:
        return team1, team2, "abondoned"
    elif "tied" in winner.text:
        return team1, team2, "tied"
    elif "No result" in winner.text:
        return team1, team2, "no_result"
    else:
        return team1, team2, winner.text.split(" ")[0]


# Given a URL for an API call, get all of its Data


def get_all_url_for_psl_url(url):
    content = requests.get(url).text
    soup = BeautifulSoup(content, "html.parser")
    main_div = soup.find("div", {"class": "ds-p-0"})
    url_list = []
    for div in main_div:
        wrong_url = div.find("a")["href"]
        url = f"https://www.espncricinfo.com{wrong_url}"
        url_list.append(url)
    return url_list


# For a given year of PSL, get all data
def get_psl_data_for_year(psl_year, url):
    print(f"Getting Data for year {psl_year}")
    url_list = get_all_url_for_psl_url(url)
    all_match_data, url_with_error = get_all_matches_data_from_url_list(url_list)
    with open(f"psl_{psl_year}.json", "w") as f:
        json.dump(all_match_data, f)
    print(f" JSON DUMP DATA LEN : {len(all_match_data)}")
    return get_row_list_from_all_match_data(all_match_data, psl_year), url_with_error
