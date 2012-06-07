# -*- coding: utf-8 *-*
from pygithub3 import Github
from pygithub3.services.repos import Commits
from assembla.assembla.models import *
from auth import assembla_auth, sendgrid_auth, github_auth, unfuddle_auth
import sendgrid
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import parse
from mailing_list import email_to
import getpass
import simplejson
import urllib2

#run this code once at the end of day, or setup a crontab.

class Unfuddle(object):
    def __init__(self):
        self.ACCOUNT_DETAILS = {
            'account': unfuddle_auth[0],
            'username': unfuddle_auth[1],
            'password': unfuddle_auth[2],
        }
        self.base_url = 'https://%s.unfuddle.com' % (self.ACCOUNT_DETAILS['account'])
        self.api_base_path = '/api/v1/'

    def get_data(self, api_end_point):
        # url = 'https://subdomain.unfuddle.com/api/v1/projects'
        url = self.base_url + self.api_base_path + api_end_point

        auth_handler = urllib2.HTTPBasicAuthHandler() 
        auth_handler.add_password(realm='Unfuddle API', 
                                  uri=url, 
                                  user=self.ACCOUNT_DETAILS['username'], 
                                  passwd=self.ACCOUNT_DETAILS['password']) 

        opener = urllib2.build_opener(auth_handler) 
        opener.addheaders = [('Content-Type', 'application/xml'), ('Accept', 'application/json')] 

        # print '', url, ''
        try: 
            response = opener.open(url).read().strip() 
            # print 'response:', response 
            return simplejson.loads(response)
        except IOError, e: 
            print IOError, e

    def get_account_activity(self, parameter=None):
        end_point = 'account/activity'
        if parameter == None:
            return self.get_data(end_point)
        else :
            return self.get_data(end_point + "?" + parameter)
            
    def get_people(self):
        return self.get_data('people')

    def get_project(self):
        return self.get_data('projects')

unfuddle = Unfuddle()
persons = {}
projects = {}

def main():
    s = sendgrid.Sendgrid(sendgrid_auth[0], sendgrid_auth[1], secure=True)

    # Github object with authentication credentials    
    gh = Github(login=github_auth[0], password=github_auth[1])
    
    # Get agiliq user object and repos
    agiliq = gh.users.get('agiliq')
    agiliq_repos = gh.repos.list('agiliq').all()
    
    # Get ids and names of people from agiliq.unfuddle.com
    people = unfuddle.get_people()
    for i in people:
        persons[i['id']] = i['first_name']

    # Get ids and names of projects from agiliq.unfuddle.com
    project = unfuddle.get_project()
    for i in project:
        projects[i['id']] = i['title']
    
    # Retrieve the Stream Events.
    # These are similar to those appearing on http://www.assembla.com/start (right side)

    api = API(assembla_auth, use_cache=True)
    events = api.events()
    spaces = api.spaces()
    local_zone = tz.tzlocal()

    # Retrieve the events happened in all spaces for an Organization, for a day.


    tday = datetime.now()
    tday = tday.replace(tzinfo=local_zone)
    this_day = (tday - timedelta(hours=24)).date()
    uthis_day = tday.date()     # Unfuddle start date value
    unext_day = (tday + timedelta(hours=24)).date()     # Unfuddle end date value
    subject = "Agiliq-Assembla Summary for the day " + tday.strftime("%b %d %Y")
    plain_body = ""
    colors = {'funderhub': 'cyan', 'Occasio': 'green', 'TexStar University': 'brown'}
    user_activity = {}

    github_body = ""
    github_user_activity = {}

    unfuddle_activity = {}
    unfuddle_body = ''
    parameter = 'start_date=' + str(uthis_day) + '&end_date=' + str(unext_day) + '&limit=0'
    activity = unfuddle.get_account_activity(parameter)

    for event in events:
        edt = parse(event.date)
        event_date_time = edt.astimezone(local_zone)
        event_date = event_date_time.date()
        if not event_date > this_day:
            break
        for space in spaces:
            for user in space.users():
                if user.name not in user_activity.keys():
                    user_activity[user.name] = plain_body
                if user.id == event.author['id'] and event.space['id'] == space.id:
                    plain_body += "<hr/> <b>{0}</b> @ <font color=".format(
                        event_date_time.strftime("%H:%M"),
                        event.author['name']
                        ) + \
                    colors.get(event.space['name'], 'red') + ">{0}</font> <a href='{3}'>{1}</a> <br/> {2} <br/>".format(
                        event.space['name'],
                        event.operation,
                        event.title,
                        event.url,
                        #event.whatchanged,
                        #event.comment_or_description,
                        )
                    if event.object == 'Ticket' and event.operation != 'created':
                        if getattr(event, 'whatchanged', None):
                            plain_body += "<font color='violet'>" + event.whatchanged + "</font><br/>"
                        elif getattr(event, 'comment_or_description', None):
                            plain_body += "<font color='violet'>" + event.comment_or_description + "</font><br/>"
                    if plain_body:
                        user_activity[user.name] += plain_body
                    plain_body = ""

    for repo in agiliq_repos:

        if repo.name == 'blog' or repo.name == 'becomingguru.github.com':
            continue

        agiliq_commit = Commits(user='agiliq', repo=repo.name)
        commit_list = agiliq_commit.list(sha='master', path=None).all()

        for k in commit_list:
            cdt = parse(k.commit.committer.date)
            commit_date_time = cdt.astimezone(local_zone)
            commit_date = commit_date_time.date()
            if not commit_date > this_day:
                break
            name = k.commit.committer.name.encode('ascii', 'ignore')
            for user in email_to:
                if name not in github_user_activity.keys():
                        github_user_activity[name] = github_body

                if name == user[2] or name == user[1]:
                    commit_url = repo.html + '/commit/' + k.sha
                    github_body += "<hr/> <b>{0}</b> @ <font color=".format(
                        commit_date_time.strftime("%H:%M"),
                        name
                        ) + 'red' + ">{0}</font> <a href='{3}'>{1}</a> <br/> {2} <br/>".format(
                        repo.name,
                        "comitted",
                        k.sha[:10],
                        commit_url,
                        )
                    github_body += "<font color='violet'>" + k.commit.message + "</font><br/>"                
                    
                    if github_body:
                        github_user_activity[name] += github_body
                    github_body = ""
    
    for i in activity:
        if i['person_id'] in persons.keys():
            person = persons[i['person_id']]
        else:
            continue
        if i['project_id'] in projects.keys():
           project_name = projects[i['project_id']]
        else:
            continue
        if person not in unfuddle_activity.keys():
            unfuddle_activity[person] = unfuddle_body
        adt = parse(i['created_at'])
        # print adt.tzinfo
        activity_date_time = adt.astimezone(local_zone)

        record_type = i['record_type']#.encode('ascii', 'ignore')
        unfuddle_body += "<hr/> <b>{0}</b> @ <font color=".format(
                        activity_date_time.strftime("%H:%M"),
                        person
                        ) + 'red' + ">{0}</font> <a href='{3}'>{1}</a> <br/> {2} <br/>".format(
                        project_name,
                        record_type,
                        i['id'],
                        unfuddle.base_url + '/a#/projects/' + str(i['project_id']),
                        )
        # unfuddle_body += '\nRecord Type : ' + record_type
        # unfuddle_body += '\nPerson : ' + person
        unfuddle_body += "<font color='violet'>" + '\nEvent : ' + i['event'] + "</font><br/>"        

        if record_type == 'Message':
            record_message_title = i['record']['message']['title']
            record_message_body = i['record']['message']['body']
            unfuddle_body += "<font color='violet'>" + '\nMessage Title :  %s' % record_message_title + "</font><br/>"
            unfuddle_body += "<font color='violet'>" + '\nMessage Body : %s' % record_message_body + "</font><br/>"
        elif record_type == 'Milestone':
            record_milestone_title = i['record']['milestone']['title']
            record_milestone_desc = i['record']['milestone']['description']
            unfuddle_body += "<font color='violet'>" + '\nMilestone Title : %s' % record_milestone_title + "</font><br/>"
            unfuddle_body += "<font color='violet'>" + '\nMilestone Description : %s' % record_milestone_desc + "</font><br/>"
        elif record_type == 'Ticket':
            record_ticket_summary = i['record']['ticket']['summary']
            record_ticket_desc = i['record']['ticket']['description']
            unfuddle_body += "<font color='violet'>" + '\nTicket Summary : %s' % record_ticket_summary + "</font><br/>"
            unfuddle_body += "<font color='violet'>" + '\nTicket Description : %s' % record_ticket_desc + "</font><br/>"
        elif record_type == 'TimeEntry':
            record_timeentry_desc = i['record']['time_entry']['description']
            unfuddle_body += "<font color='violet'>" + '\nTimeEntry Description : %s' % record_timeentry_desc + "</font><br/>"
        elif record_type == 'Changeset':
            record_Changeset_commit_message = i['record']['changeset']['message']
            unfuddle_body += "<font color='violet'>" + '\nCommit Message : %s' % record_Changeset_commit_message + "</font><br/>"
        elif record_type == 'Comment':
            record_comment_body = i['record']['comment']['body']
            unfuddle_body += "<font color='violet'>" + '\nComment Body : %s' % record_comment_body + "</font><br/>"
    
        if unfuddle_body:
            unfuddle_activity[person] += unfuddle_body
            unfuddle_body = ""

    #check if a user has same name in assembla, github and unfuddle
    for k in user_activity.keys():
        if k in github_user_activity.keys():
            user_activity[k] = user_activity[k] + github_user_activity[k]
            github_user_activity.pop(k)
        if k in unfuddle_activity.keys():
            user_activity[k] = user_activity[k] + unfuddle_activity[k]
            unfuddle_activity.pop(k)
    
    user_activity.update(github_user_activity)
    user_activity.update(unfuddle_activity)

    html = "<html><body>"
    holiday = True
    for k, v in user_activity.iteritems():
        #display summary per each user.
        if v:
            html += "<div>" + "<h3>" + k + "</h3>" + v + "</div>"
            holiday = False
    html += "</body></html>"
    
    #check if no activity done. if so do not send mail.
    if not holiday:
        message = sendgrid.Message("ramana@agiliq.com", subject, "", "<div>" + html + "</div>")
        for person in email_to:
            message.add_to(person[0], person[1])
        s.smtp.send(message)


if __name__ == '__main__':
    main()
