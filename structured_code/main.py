# URL to result pages of all the years of PSL
# You can replace these with URLS to some other series result pages and the script should worl
import json
import time
import pandas as pd

from utils.general_utils import get_psl_data_for_year

psl_urls = {
    "2016": "https://www.espncricinfo.com/series/pakistan-super-league-2015-16-923069/match-results",
    "2017": "https://www.espncricinfo.com/series/psl-2016-17-1075974/match-results",
    "2018": "https://www.espncricinfo.com/series/psl-2017-18-1128817/match-results",
    "2019": "https://www.espncricinfo.com/series/psl-2018-19-1168814/match-results",
    "2020": "https://www.espncricinfo.com/series/psl-2019-20-2020-21-1211602/match-results",
    "2021": "https://www.espncricinfo.com/series/psl-2020-21-2021-1238103/match-schedule-fixtures-and-results",
}

# Extracting all Data
start = time.time()
all_rows = []
all_error_url = []
for psl_year, url in psl_urls.items():
    psl_data, url_with_error = get_psl_data_for_year(psl_year, url)
    all_error_url.extend(url_with_error)
    all_rows.extend(psl_data)
with open(f"error_url.json", "w") as f:
    json.dump(all_error_url, f)
df = pd.DataFrame(all_rows)
df = df[
    [
        "psl_year",
        "match_number",
        "team_1",
        "team_2",
        "inning",
        "over",
        "ball",
        "runs",
        "wicket",
        "total_runs",
        "wickets",
        "is_four",
        "is_six",
        "is_wicket",
        "wicket_text",
        "result",
    ]
]
df.to_csv("PSL-2016-2022.csv", index=False)
end = time.time()

print(f"Total Time Taken : {end - start}")
