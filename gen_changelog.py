#!/usr/bin/env python3

# Generate and upload changelog

from git import Repo, exc
from github import Github
import os
import sys

upload_changelog = True

try:
    current_tag = os.environ['TRAVIS_TAG']
    if current_tag == '':
        current_tag = 'HEAD'
        upload_changelog = False
    print('TRAVIS_TAG is set to {}'.format(current_tag))
except KeyError:
    print('TRAVIS_TAG not set - not uploading changelog')
    current_tag = 'HEAD'
    upload_changelog = False

try:
    api_key = os.environ['GITHUB_OAUTH_TOKEN']
except KeyError:
    print('GITHUB_OAUTH_TOKEN not set - not uploading changelog')
    api_key = None
    upload_changelog = False

try:
    repo_slug = os.environ['TRAVIS_REPO_SLUG']
except KeyError:
    print('TRAVIS_REPO_SLUG not set - cannot determine remote repository')
    repo_slug = ''
    exit(1)

repo_owner = repo_slug.split()[0]
print('Repo owner is set to {}'.format(repo_owner))

if len(sys.argv) > 1:
    repo_path = sys.argv[1]
else:
    repo_path = '.'

print('Opening repository at {}'.format(repo_path))
repo = Repo(repo_path)
git = repo.git()
try:
    print('Unshallowing repository')
    git.fetch('--unshallow', '--tags')
except exc.GitCommandError:
    print('Repository already unshallowed')
if current_tag != 'HEAD':
    print('Attempting to get base tag from current tag')
    base_tag = current_tag.split('-')[0]
    print('Base tag set to {}'.format(base_tag))
else:
    description = git.describe()
    print('Attempting to get base tag from git description: {}'.format(description))
    base_tag = description.split('-')[0]
    print('Base tag set to {}'.format(base_tag))

#changelog = git.log('{}...{}'.format(base_tag, current_tag), '--pretty=format:* %s (%an) %H\n')
# Note: the base repository is hardcoded; this is something we should probably think about
changelog_link = 'https://github.com/PX4/Firmware/compare/{}...{}:{}'.format(base_tag, repo_owner, current_tag)
print('Current changelog: \n{}'.format(changelog_link))

# Only interact with Github if uploading is enabled
if upload_changelog:
    gh = Github(api_key)
    gh_repo = gh.get_repo(repo_slug)
    # Get all releases and find ours by its tag name
    gh_release = None
    for release in gh_repo.get_releases():
        if release.tag_name == current_tag:
            gh_release = release
    if gh_release is None:
        # We could not find the correct release, so here's our last resort. It will most likely fail.
        gh_release = gh_repo.get_release(current_tag)
    gh_body = gh_release.body
    if gh_body is None:
        gh_body = ''
    gh_body = '{}\n## Changes between {} and {}:\n\n{}'.format(gh_body, base_tag, current_tag, changelog_link)
    print('New release body: {}'.format(gh_body))
    gh_release.update_release(gh_release.tag_name, gh_body, draft=True, prerelease=True,
                              tag_name=gh_release.tag_name, target_commitish=gh_release.target_commitish)
