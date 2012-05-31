# -*- coding: utf-8 *-*
from pygithub3 import Github
from pygithub3.services.repos import Commits
from assembla.models import *
from auth import assembla_auth, sendgrid_auth, github_auth
import sendgrid
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import parse
from mailing_list import email_to

#run this code once at the end of day, or setup a crontab.


def main():
    s = sendgrid.Sendgrid(sendgrid_auth[0], sendgrid_auth[1], secure=True)

    #Github object with authentication credentials    
    gh = Github(login=github_auth[0], password=github_auth[1])
    
    #Get agiliq user object and repos
    agiliq = gh.users.get('agiliq')
    agiliq_repos = gh.repos.list('agiliq').all()
    
    # Retrieve the Stream Events.
    # These are similar to those appearing on http://www.assembla.com/start (right side)

    api = API(assembla_auth, use_cache=True)
    events = api.events()
    spaces = api.spaces()
    local_zone = tz.tzlocal()

    # Retrieve the events happened in all spaces for an Organization, for a day.

    tday = datetime.now()
    tday = tday.replace(tzinfo=local_zone)
    this_day = (tday - timedelta(hours=48)).date()
    subject = "Agiliq-Assembla Summary for the day " + tday.strftime("%b %d %Y")
    plain_body = ""
    colors = {'funderhub': 'cyan', 'Occasio': 'green', 'TexStar University': 'brown'}
    user_activity = {}

    github_body = ""
    github_user_activity = {}


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

                if name == user[2]:
                    github_body += "<hr/> <b>{0}</b> @ <font color=".format(
                        commit_date_time.strftime("%H:%M"),
                        name
                        ) + 'red' + ">{0}</font> <a href='{3}'>{1}</a> <br/> {2} <br/>".format(
                        repo.name,
                        "comitted",
                        k.sha[:10],
                        repo.html_url,
                        )
                    github_body += "<font color='violet'>" + k.commit.message + "</font><br/>"                
                    
                    if github_body:
                        github_user_activity[name] += github_body
                    github_body = ""

    user_activity.update(github_user_activity)
    
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
