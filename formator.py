#!/usr/bin/python2.7
#coding:utf8

"""
Author:         handalin
Filename:       Formator.py
Last modified:  2019-03-29 12:20
Description:
    写入 Gogs DB 的时候，做格式转换
    Format converting when writing into Gogs DB

"""
#from pprint import pprint
from datetime import datetime
import calendar

from torndb import Connection
from config import DB_conf

def iso8601_from_epoch(timestamp):
    """
    epoch_to_iso8601 - convert the unix epoch time into a iso8601 formatted date
    >>> epoch_to_iso8601(1341866722)
    '2012-07-09T22:45:22'
    """
    return datetime.fromtimestamp(timestamp).isoformat()

def epoch_from_iso8601(datestring):
    """
    iso8601_to_epoch - convert the iso8601 date into the unix epoch time
    >>> iso8601_to_epoch("2012-07-09T22:27:50.272517")
    1341872870
    """
    return calendar.timegm(datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%SZ").timetuple())


class Formator(object):

    def __init__(self, owner='', repo=''):
        conn = Connection(**DB_conf)
        # get staff map
        sql = 'select id, name from user'
        ret = conn.query(sql)
        self.staff_id_from_name = dict( [(x['name'], x['id']) for x in ret ] )

        sql = 'select id, color from label'
        ret = conn.query(sql)
        self.label_id_from_color = dict( [(x['color'][1:], x['id']) for x in ret ] )

        # get owner_id by owner
        owner_id = self.staff_id_from_name[owner]

        sql = 'select id from repository where owner_id = %s and name = %s'
        ret = conn.get(sql, owner_id, repo)
        repo_id = ret['id']

        self.repo_id = repo_id

        conn.close()

    def label_gogs_from_github(self, label):
        # add sharp(#)
        label['color'] = '#' + label['color']
        label['repo_id'] = self.repo_id
        return label

    def comment_gogs_from_github(self, comment):
        # common field mapping
        field_map = {
            'content': 'body',
            'created_unix': 'created_at',
            'updated_unix': 'updated_at',
        }
        for k, v in field_map.items():
            comment[k] = comment.get(v)
            if k.endswith('_unix'):
                comment[k] = epoch_from_iso8601(comment[k])

        # other fields
        username = comment['user']['login']
        comment['poster_id'] = self.staff_id_from_name[username]

        # TODO: commit_id, line, commit_sha

        return comment

    def issue_gogs_from_github(self, issue):
        # common field mapping
        field_map = {
            'index': 'number',
            'name': 'title',
            'content': 'body',
            'created_unix': 'created_at',
            'updated_unix': 'updated_at',
        }
        for k, v in field_map.items():
            issue[k] = issue.get(v)
            if k.endswith('_unix'):
                issue[k] = epoch_from_iso8601(issue[k])

        # other fields
        if issue['milestone']:
            #  TODO: 'id' or 'number' ?
            issue['milestone_id'] = issue['milestone']['id']
        else:
            issue['milestone_id'] = None

        # TODO: priority
        issue['priority'] = 0
        issue['deadline_unix'] = 0

        if issue['assignee']:
            username = issue['assignee']['login']
            issue['assignee_id'] = self.staff_id_from_name[username]

        state = str(issue.get('state'))
        if state == 'open':
            issue['is_closed'] = 0
        else:
            issue['is_closed'] = 1

        if 'pull_request' in issue:
            issue['is_pull'] = 1
        else:
            issue['is_pull'] = 0

        if issue['comments']:
            issue['num_comments'] = len(issue['comments'])
        else:
            issue['num_comments'] = 0

        # user related
        poster_username = issue['user']['login']
        issue['poster_id'] = self.staff_id_from_name[poster_username]

        issue['assignee_ids'] = []
        assignees = [ u['login'] for u in issue['assignees'] ]
        for assignee in assignees:
            issue['assignee_ids'].append(self.staff_id_from_name[assignee])

        # label related
        for label in issue['labels']:
            color = str(label['color'])
            label['label_id'] = self.label_id_from_color[color]

        # comments related
        _comments = []
        if issue['comments']:
            for comment in issue['comments']:
                _comments.append(self.comment_gogs_from_github(comment))

        issue['comments'] = _comments
        issue['repo_id'] = self.repo_id
        return issue

    def milestone_gogs_from_github(self, milestone):
        # common field mapping
        field_map = {
            'name': 'title',
            'content': 'description',
            'num_issues': 'open_issues',
            'num_closed_issues': 'closed_issues',
            'deadline_unix': 'due_on',
            'closed_date_unix': 'closed_at',
        }
        for k, v in field_map.items():
            milestone[k] = milestone.get(v)
            if k.endswith('_unix') and milestone[k]:
                milestone[k] = epoch_from_iso8601(milestone[k])

        # other fields
        state = str(milestone.get('state'))
        if state == 'open':
            milestone['is_closed'] = 0
        else:
            milestone['is_closed'] = 1

        # completeness
        num_closed = milestone['num_closed_issues']
        num = milestone['num_issues']
        milestone['completeness'] = int(100.0 * num_closed / num)

        milestone['repo_id'] = self.repo_id
        return milestone

if __name__ == '__main__':
    pass
