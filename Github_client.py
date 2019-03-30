#!/usr/bin/python2.7
# coding:utf8

"""
Author:         handalin
Filename:       Gogs_client.py
Last modified:  2019-03-29 12:20
Description:
    Github API client
"""
import json
import os
import sys
import subprocess
import commands
import requests

class GithubClient(object):
    host = 'https://api.github.com'
    token = ''
    owner = ''
    repo = ''
    obj = ''
    path = '/repos/{owner}/{repo}/{obj}'
    headers = {
        'Content-Type': 'application/json',
    }

    def __init__(self, user='', token='', owner='', repo=''):
        self.user = user

        if token:
            self.set_header(Authorization = 'token %s' % token)
        if owner:
            self.owner = owner
        if repo:
            self.repo = repo

    def set_owner(self, owner):
        self.owner = owner

    def set_repo(self, repo):
        self.repo = repo

    def set_obj(self, obj):
        self.obj = obj

    def set_header(self, **kv):
        for k, v in kv.items():
            self.headers[k] = str(v)

    # baisc CRUD operations
    def _create(self, obj, headers=None):

        path = self.path.format(owner=self.owner,
                                    repo=self.repo,
                                    obj=self.obj)
        # send request to read iss
        url = self.host + path

        if not headers: headers = self.headers
        r = requests.post(url, data=json.dumps(obj), headers=headers)
        return r.json()

    def _read(self, _id=None, headers=None, page=0, per_page=100):

        path = self.path.format(owner=self.owner,
                                repo=self.repo,
                                obj=self.obj)

        # filter / paginating
        if _id and (isinstance(_id, int) or _id.isdigit()):
            path += '/%d' % _id
        else:
            # get all issue
            path += '?state=all'
            if page:
                # paginating
                path += '&page=%s&per_page=%s' % (page, per_page)

        # send request to read
        url = self.host + path

        if not headers: headers = self.headers

        print 'Fetch: -----------' + url
        r = requests.get(url, headers=headers)
        return r.json()

    def _update(self, obj):
        '''
            no implementation
        '''
        pass

    def _delete(self, obj):
        '''
            no implementation
        '''
        pass

    def milestone_create(self, milestone):
        self.set_obj('milestones')
        return self._create(milestone)

    def milestone_read(self, milestone_id=None):
        self.set_obj('milestones')
        return self._read(milestone_id)

    def label_create(self, label):
        self.set_obj('labels')
        return self._create(label)

    def label_read(self, label_id=None):
        self.set_obj('labels')
        return self._read(label_id)

    def issue_create(self, issue):
        self.set_obj('issues')
        return self._create(issue)

    def issue_read(self, issue_id=None, page=0, per_page=100):
        self.set_obj('issues')
        issues = self._read(_id = issue_id,
                            page = page,
                            per_page = per_page)
        for issue in issues:
            if isinstance(issue['comments'], int):
                if issue['comments'] > 0:
                    self.set_obj('issues/%s/comments' % issue['number'])
                    issue['comments'] = self._read()
                else:
                    issue['comments'] = []
        return issues

if __name__ == '__main__':
    pass
