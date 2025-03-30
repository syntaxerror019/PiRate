import requests
import subprocess

class GitUpdater:
    def __init__(self, github_owner, github_repo, branch="main"):
        """
        Initialize the GitUpdater.

        :param github_owner: GitHub username or organization
        :param github_repo: Repository name
        :param branch: Branch to check for updates (default: main)
        """
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.branch = branch

    def get_latest_commit(self):
        """Fetches the latest commit hash from GitHub."""
        url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/commits/{self.branch}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()["sha"]
        except requests.RequestException as e:
            print(f"Error fetching latest commit: {e}")
            return None

    def get_local_commit(self):
        """Gets the latest local commit hash."""
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode()
        except subprocess.CalledProcessError as e:
            print(f"Error getting local commit: {e}")
            return None
        
    def latest_commit_information(self):
        """
        Fetches the latest commit information from GitHub.

        :return: A dictionary with commit details or None if an error occurs
        """
        url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/commits/{self.branch}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            commit_info = response.json()
        except requests.RequestException as e:
            print(f"Error fetching latest commit information: {e}")
            return None
    
        return {
                "sha": commit_info["sha"],
                "message": commit_info["commit"]["message"],
                "author": commit_info["commit"]["author"]["name"],
                "date": commit_info["commit"]["author"]["date"]
            }

    def check_for_updates(self):
        """
        Checks if an update is available.
        
        :return: True if an update is available, False otherwise
        """
        latest_commit = self.get_latest_commit()
        local_commit = self.get_local_commit()
        
        print(f"Latest commit on GitHub: {latest_commit}")
        print(f"Local commit: {local_commit}")

        if latest_commit and local_commit:
            if latest_commit != local_commit:
                print("Update available!")
                return True, self.latest_commit_information()
            else:
                print("Already up to date.")
                return False, None

    def pull_updates(self):
        """Pulls the latest changes while preserving local modifications."""
        try:
            # Stash local changes to avoid conflicts
            subprocess.run(["git", "stash"], check=True)
            
            # Pull the latest changes
            subprocess.run(["git", "pull", "--rebase"], check=True)

            # Reapply stashed changes
            subprocess.run(["git", "stash", "pop"], check=True)
            print("Update applied successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error updating repository: {e}")

    def update_if_available(self):
        """
        Checks for updates and applies them if available.
        """
        if self.check_for_updates():
            self.pull_updates()
