import os
import base64
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'File: {file["filename"]}\nDiff: \n{file["patch"]}\n'
        for file in diffs
    ])

    # Combine all commit messages
    commit_messages = '\n'.join(commit_messages) + '\n\n'

    # Decode the README content
    readme_content = base64.b64decode(readme_content.content).decode('utf-8')

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Please review the following code changes and commit messages from a GitHub pull request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messages:\n"
        f"{commit_messages}"
        "Here is the current README file content:\n"
        f"{readme_content}\n"
        "Consider the code changes and commit messages, determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
        "Updated README:\n"
    )

    return prompt

def format_dbt_yml_data_for_openai(diffs, yml_content, sql_content):
    prompt = None

    # # Combine the changes into a string with clear delineation.
    # changes = '\n'.join([
    #     f'File: {file["filename"]}\nDiff: \n{file["patch"]}\n'
    #     for file in diffs
    #     if file["filename"].endswith('.sql')
    # ])

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'{file["filename"]}\n'
        for file in diffs
        if file["filename"].endswith('.sql')
    ])

    # sql_contnet = '\n'.join([
    #     f'{file["raw_data"]}\n'
    #     for file in diffs
    #     if file["filename"].endswith('.sql')
    # ])
    
    print(sql_content)

    # Decode the README content
    model_file = base64.b64decode(yml_content.content).decode('utf-8')
    sql_file = base64.b64decode(yml_content.content).decode('utf-8')

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        f"FILE_CONTENT: {sql_file}\n"
        f"CURRENT_YML: {model_file}\n"
        f"Update the CURRENT_YML to include dbt relationship integrity tests for the model matching {changes}. Use the FILE_CONTENT to help inform the relationships. Create these test using the same structure as the other tests.\n"
        "Don't delete existing models or comments.\n"
        "Please don't wrap code in ``` or any other block notation.\n"
        "Updated YML:\n"

        # "Please review the following filenames:\n"
        # f"{changes}\n"
        # "Please review the sql content for the above file:\n"
        # f"{sql_content}\n"
        # "Here is the current yml file content:\n"
        # f"{model_file}\n"
        # "Update the current yml with relationship integrity dbt tests for models that have a similar name to a filename I asked you to review above. Use the provided sql to help inform the relationships.\n"
        # "Please don't wrap code in ``` or any other block notation.\n"
        # "Updated YML:\n"
    )

    print('prompt: ', prompt)

    return prompt

def call_openai(prompt, system_prompt):
    client = ChatOpenAI(api_key=os.getenv('OPEN_AI_KEY'), model='gpt-3.5-turbo')

    try:
        messages = [
            { 'role': 'system', 'content': system_prompt},
            { 'role': 'user', 'content': prompt }
        ]

        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)

        return content
    except Exception as e:
        print(f'Error making LLM call: {e}')

def update_readme_yml_and_create_pr(repo, updated_readme, updated_dbt_yml, readme_sha, yml_sha):
    commit_message = 'AI COMMIT: Proposed README or yml updated based on recent code changes.'
    commit_sha = os.getenv('COMMIT_SHA')
    main_branch = repo.get_branch('main')
    new_branch_name = f'update-readme-{commit_sha[:7]}'
    new_branch = repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=main_branch.commit.sha)

    repo.update_file('README.md', commit_message, updated_readme, readme_sha, branch=new_branch_name)
    repo.update_file('_mart__models.yml', commit_message, updated_dbt_yml, yml_sha, branch=new_branch_name)

    pr_title = 'AI PR: Update README and yml based on recent change'
    pr_body = 'This is an AI PR. Please review the README and YML'
    pull_request = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base='main')

    return pull_request