#!/usr/bin/env python
"""
Whenever a new reusable workflow is created or updated, we want to open a PR in every repository from which we want to call it.

First create a template for the caller workflow in .github/workflows/caller-templates, that will be copied into the target repos.

This script takes the template file name and a list of target repositories as a comma-separated list, eg.

    python stale.yml catalogue-api,catalogue-pipeline

will copy the stale.yml file stored locally in .github/workflows/caller-templates folder (source directory)
into the .github/workflows directory of the target repositories.


For each repository it:
- gets the last PR merged to the .github repository for reference in the target repository PR
- clones the target repository into a temporary directory, and cd into it
- write the source directory's template_workflow_file into the target's /.github/workflows directory
- git checkout, add, commit and push to the target's remote 
- open a PR against origin/main
- request a review from "scala-reviewers" and "js-ts-reviewers"
"""

import sys
import subprocess
import contextlib
import os
import re
import shutil
import tempfile
import boto3
import httpx

def _subprocess_run(cmd, exit_on_error=True):
    print("*** Running %r" % " ".join(cmd))

    output = []
    pipe = subprocess.Popen(
        cmd, encoding="utf8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    # Await command completion and print lines as they come in
    for stdout_line in iter(pipe.stdout.readline, ""):
        print(stdout_line, end="")
        output.append(stdout_line)

    # Extract results
    pipe.communicate()
    return_code = pipe.returncode

    if return_code != 0 and exit_on_error:
        sys.exit(return_code)

    return "".join(output).strip()


def git(*args, exit_on_error=True):
    """Run a Git command and return its output."""
    cmd = ["git"] + list(args)

    return _subprocess_run(cmd, exit_on_error=exit_on_error)

@contextlib.contextmanager
def working_directory(target_dir):
    """
    Changes the working directory to the given path, then returns to the
    original directory when done.
    """
    source_dir = os.getcwd()

    os.chdir(target_dir)
    try:
        yield
    finally:
        os.chdir(source_dir)


@contextlib.contextmanager
def cloned_repo(git_url):
    """
    Clones the repository and changes the working directory to the cloned
    repo.  Cleans up the clone when it's done.
    """
    target_dir = tempfile.mkdtemp()

    git("clone", git_url, target_dir)

    try:
        with working_directory(target_dir):
            yield
    finally:
        shutil.rmtree(target_dir)


class AlreadyAtLatestVersionException(Exception):
    pass


def create_or_update_github_workflow(source_file_path):
    with open(source_file_path, "r") as source_file, open(f".github/workflows/{template_workflow_file}", "w") as target_file:
        for line in source_file:
            target_file.write(line)

def get_last_merged_pr_number():
    for line in git("log", "--oneline").splitlines():
        m = re.match(r"^[0-9a-f]{7} Merge pull request #(?P<pr_number>\d+)", line)

        if m is not None:
            return m.group("pr_number")

def get_github_api_key():
    session = boto3.Session()
    secrets_client = session.client("secretsmanager")
    # using the scala_libs_pr_bumps secret for now but this should have its own secret
    secret_value = secrets_client.get_secret_value(SecretId="builds/github_wecobot/scala_libs_pr_bumps")

    return secret_value["SecretString"]

def create_pull_request(template_workflow_file, repository):
    api_key = get_github_api_key()
    client = httpx.Client(api_key)

    # get the number of the PR that was last merged to .github repository
    pr_number = get_last_merged_pr_number()

    pr_body = "New Github workflow available:\n" + f"See wellcomecollection/.github#{pr_number}"
    branch_name = f"use-{template_workflow_file}-reusable-workflow"
    pr_title = f"Use {template_workflow_file} reusable workflow"
    
    # we get path to template workflow before we move to the cloned repo directory in with cloned_repo
    source_file_path = f"{os.getcwd()}/caller-templates/{template_workflow_file}"

    with cloned_repo(f"git@github.com:wellcomecollection/{repository}.git"):
      create_or_update_github_workflow(source_file_path)

      git("checkout", "-b", branch_name)
      git("add", f".github/workflows/{template_workflow_file}")
      git("commit", "-m", pr_title)
      git("push", "origin", branch_name)

      r = client.post(
          f"https://api.github.com/repos/wellcomecollection/{repository}/pulls",
          headers={"Accept": "application/vnd.github.v3+json"},
          json={
              "head": branch_name,
              "base": "main",
              "title": pr_title,
              "maintainer_can_modify": True,
              "body": pr_body,
          }
      )

      try:
          r.raise_for_status()
          new_pr_number = r.json()["number"]
      except Exception:
          print(r.json())
          raise

      r = client.post(
          f"https://api.github.com/repos/wellcomecollection/{repository}/pulls/{new_pr_number}/requested_reviewers",
          headers={"Accept": "application/vnd.github.v3+json"},
          json={"team_reviewers": ["scala-reviewers", "js-ts-reviewers"]}
      )

      print(r.json())

      try:
          r.raise_for_status()
      except Exception:
          raise


if __name__ == '__main__':
    template_workflow_file = sys.argv[1]
    for repository in sys.argv[2].split(','):
      create_pull_request(template_workflow_file, repository) 