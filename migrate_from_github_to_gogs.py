#!/usr/bin/python2.7
#coding:utf8

"""
Author:         handalin
Filename:       migrate.py
Last modified:  2019-03-28 18:41
Description:
             issues + milestones + labels + comments
    Github ------------------------------------------- > Gogs

    从 Github 迁移 issues 到 Gogs
    Move issues ( milestone/label/comments also ) from Github to Gogs

"""
import os
import json
import sys
from pprint import pprint
from Gogs_DAO import GogsDAO
from Github_client import GithubClient
from config import OWNER, REPO, GITHUB_ACCESS_TOKEN

if __name__ == '__main__':
    gogs_cli = GogsDAO(owner=OWNER, repo=REPO)

    github_client = GithubClient(
                    token=GITHUB_ACCESS_TOKEN,
                    owner = OWNER,
                    repo = REPO)

    clear_tables()
    print '[START] migration start.'

    print '#' * 20
    print '# Milestone: '
    print '#' * 20
    milestones = github_client.milestone_read()
    for milestone in milestones:
        #pprint(milestone)
        _id = gogs_cli.milestone_create(milestone)
        milestone['milestone_id'] = _id

    print '#' * 20
    print '# label: '
    print '#' * 20
    labels = github_client.label_read()
    #pprint(labels)
    for label in labels:
        ret = gogs_cli.label_create(label)

    print '#' * 20
    print '# issue: '
    print '#' * 20

    # file cache avoiding fetch from Github everytime
    # (if you wanna do something else)
    if not os.path.exists('issues.txt'):
        page = 1
        issues = []
        while True:
            these_issues = github_client.issue_read(page = page)
            page += 1

            if not these_issues:
                break
            issues += these_issues

        issues.reverse()

        with open('issues.txt', 'wb') as fout:
            fout.write(json.dumps(issues))
    else:
        with open('issues.txt', 'r') as fin:
            issues = json.loads(fin.read())

    flag = raw_input('issue count: %d, import them？(Y/n)' % len(issues))
    if flag and flag.upper() == 'N':
        sys.exit(0)

    for issue in issues:
        ret = gogs_cli.issue_create(issue)
    print '#' * 20

    print 'UPDATE repository...'

    # repo counting
    repo_count = {
        'where': ['id'],
        'id': gogs_cli.repo_id,
        'num_issues': 0,
        'num_closed_issues': 0,
        'num_milestones': 0,
        'num_closed_milestones': 0,
    }
    for ms in milestones:
        state = ms['state']
        repo_count['num_milestones'] += 1
        if not state == u'open':
            repo_count['num_closed_milestones'] += 1

    for issue in issues:
        state = issue['state']
        repo_count['num_issues'] += 1
        if not state == u'open':
            repo_count['num_closed_issues'] += 1

    gogs_cli._update(table = 'repository', **repo_count)

    print '[END] migration done.'
