import os
from github import Github
from utility import *

def main():
    # Initialize GitHub API with token
    g = Github(os.getenv('GITHUB_TOKEN'))

    # Get the repo path and PR number from the environment variables
    repo_path = os.getenv('REPO_PATH')
    pull_request_number = int(os.getenv('PR_NUMBER'))
    
    # Get the repo object
    repo = g.get_repo(repo_path)

    # Fetch README content (assuming README.md)
    readme_content = repo.get_contents("README.md")

    yml_content = repo.get_contents("_mart__models.yml")
    
    # print(readme_content)
    # Fetch pull request by number
    pull_request = repo.get_pull(pull_request_number)

    # Get the diffs of the pull request
    pull_request_diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        } 
        for file in pull_request.get_files()
    ]
    
    # Get the commit messages associated with the pull request
    commit_messages = [commit.commit.message for commit in pull_request.get_commits()]

    # Format data for OpenAI prompt
    prompt_readme = format_data_for_openai(pull_request_diffs, readme_content, commit_messages)
    prompt_dbt_yml = format_dbt_yml_data_for_openai(pull_request_diffs, yml_content)

    system_prompt_readme = 'You are an AI trained to help with updating README files based commit messages and code files.'
    system_prompt_dbt_yml = 'You are an AI trained to help with adding DTB test based commited yml and sql files.'

    # Call OpenAI to generate the updated README content
    updated_readme = call_openai(prompt_readme, system_prompt_readme)
    updated_dbt_yml = call_openai(prompt_dbt_yml, system_prompt_dbt_yml)

    # Create PR for Updated PR
    update_readme_yml_and_create_pr(repo, updated_readme, updated_dbt_yml, readme_content.sha, yml_content.sha)

if __name__ == '__main__':
    main()
