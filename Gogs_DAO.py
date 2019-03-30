#!/usr/bin/python2.7
# coding:utf8

"""
Author:         handalin
Filename:       Gogs_client.py
Last modified:  2019-03-29 12:20
Description:
    直接操作 Gogs DB, 还原 issue 相关信息
    Operate Gogs DB directly
"""
from pprint import pprint
import json
import os
import sys
import requests

from torndb import Connection
from config import DB_conf

from formator import Formator

_valid_fields = {
    'repository': None,
    'milestone': None,
    'label': None,
    'issue': None,
    'issue_user': None,
    'issue_label': None,
    'comment': None,
}

conn = Connection(**DB_conf)
for table in _valid_fields:
    sql = 'select COLUMN_NAME from information_schema.COLUMNS where table_name = %s and table_schema = %s'
    ret = conn.query(sql, table, 'gogs')
    _valid_fields[table] = [ x['COLUMN_NAME'] for x in ret ]

class GogsDAO(object):
    owner = ''
    repo = ''
    repo_id = -1
    formator = None

    def __init__(self, owner='', repo=''):
        if owner:
            self.owner = owner
        if repo:
            self.repo = repo

        self.formator = Formator(owner, repo)
        self.repo_id = self.formator.repo_id

    # baisc CRUD operations
    def _create(self, table, **kv):
        k_list = []
        v_list = []
        for k, v in kv.items():
            if table in _valid_fields and k not in _valid_fields[table]:
                continue
            k_list.append( "`%s`" % k )
            v_list.append(v)

        k_content = ', '.join(k_list)
        v_content = ', '.join([ '%s' for i in range(len(v_list)) ])
        sql = 'insert into `%s` (%s) values (%s)' % (table, k_content, v_content)

        db = Connection(**DB_conf)

        ret = db.execute(sql, *v_list)
        db.close()

        return ret

    def _read(self, _id=None):
        '''
            no implementation
        '''
        pass

    def _update(self, table, **kv):
        where = kv.pop('where')
        v_list = []
        update_list = []
        where_list = []
        update_v_list = []
        where_v_list = []
        for k, v in kv.items():
            if table in _valid_fields and k not in _valid_fields[table]:
                continue
            if k in where:
                # where pair
                if k == 'st':
                    where_list.append(' `ctime` >= %s ')
                elif k == 'ed':
                    where_list.append(' `ctime` <= %s ')
                else:
                    where_list.append(' %s = %%s ' % (k))
                where_v_list += [v]
            else:
                update_list.append('%s = %%s ' % (k))
                update_v_list += [v]

        set_part = ', '.join(update_list)
        where_part = ' and '.join(where_list)
        v_list = update_v_list + where_v_list

        sql = 'update `%s` set %s where %s' % (table, set_part, where_part)

        db = Connection(**DB_conf)
        ret = db.execute(sql, *v_list)
        db.close()

        return ret


    def _delete(self, issue):
        '''
            no implementation
        '''
        pass

    def milestone_create(self, milestone):
        milestone = self.formator.milestone_gogs_from_github(milestone)
        return self._create(table = 'milestone', **milestone)

    def label_create(self, label):
        label = self.formator.label_gogs_from_github(label)
        return self._create(table = 'label', **label)

    def issue_create(self, issue):
        issue = self.formator.issue_gogs_from_github(issue)

        comments = issue['comments']
        labels = issue['labels']

        poster_id = issue['poster_id']
        assignee_ids = issue['assignee_ids']

        ret = self._create(table = 'issue', **issue)
        issue_id = ret

        # insert into `issue_user```
        self._create(table = 'issue_user',
                    uid = poster_id,
                    is_poster = True,
                    issue_id = issue_id)
        for assignee_id in assignee_ids:
            self._create(table = 'issue_user',
                        uid = assignee_id,
                        is_assigned = True,
                        issue_id = issue_id)

        # insert into `issue_label`
        for label in labels:
            label_id = label['label_id']
            self._create(table = 'issue_label', label_id = label_id, issue_id = issue_id)

        # insert into `comment`
        for comment in comments:
            try:
                ret = self._create(table = 'comment', **comment)
            except Exception as e:
                pprint(comment)
                print '[ERROR] Maybe it\'s the Emoji problem ?'
                is_continue = raw_input('Skip it & continue?(Y/n)\n')
                if is_continue.upper() == 'N':
                    raise e
                else:
                    pass

        return issue_id


if __name__ == '__main__':
    pass
