import subprocess

def get_git_repo_info():
    """Retrieves the GitHub repository owner and name from the remote URL."""
    try:
        # Get the remote URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()

        # Extract owner and repo name
        # Handles both SSH and HTTPS formats
        if url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            parts = url.split(":")[1].split("/")
            owner = parts[0]
            repo = parts[1].replace(".git", "")
        elif url.startswith("https://"):
            # HTTPS format: https://github.com/owner/repo.git
            parts = url.split("/")
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
        else:
            return None, None

        return owner, repo

    except (subprocess.CalledProcessError, IndexError):
        return None, None