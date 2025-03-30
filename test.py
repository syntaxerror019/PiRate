import requests

owner = "<owner>"
repo = "<repo>"

url = f"https://api.github.com/repos/syntaxerror019/PiRate/commits"
response = requests.get(url)

# Pagination handling
if response.status_code == 200:
    total_commits = int(response.headers['X-Total-Count'])
    print(f"Total commits: {total_commits}")
else:
    print(f"Error fetching commits: {response.status_code}")
