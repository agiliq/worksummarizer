from auth import github_auth, sendgrid_auth
from pygithub3 import Github
from pygithub3.services.repos import Commits
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import parse
from mailing_list import email_to
import sendgrid

#run this code once at the end of day.

def main():
    s = sendgrid.Sendgrid(sendgrid_auth[0], sendgrid_auth[1], secure=True)
    
    #Github object with authenticated credentials    
    gh = Github(login=github_auth[0], password=github_auth[1])
    
    #Get agiliq user object and repos
    agiliq = gh.users.get('agiliq')
    agiliq_repos = gh.repos.list('agiliq').all()

    local_zone = tz.tzlocal()

    tday = datetime.now()
    tday = tday.replace(tzinfo=local_zone)
    this_day = (tday - timedelta(hours=24)).date()
    
    subject = "Agiliq-Github Summary for the day " + tday.strftime("%b %d %Y")
    plain_body = ""
    colors = {'funderhub': 'cyan', 'Occasio': 'green', 'TexStar University': 'brown'}
    user_activity = {}

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
                if name == user[2]:
                    if name not in user_activity.keys():
                        user_activity[name] = plain_body

                    plain_body += "<hr/> <b>{0}</b> @ <font color=".format(
                        commit_date_time.strftime("%H:%M"),
                        name
                        ) + \
                    colors.get(repo.name, 'red') + ">{0}</font> <a href='{3}'>{1}</a> <br/> {2} <br/>".format(
                        repo.name,
                        "comitted",
                        k.sha[:10],
                        repo.html_url,
                        )
                    plain_body += "<font color='violet'>" + k.commit.message + "</font><br/>"                
                    
                    if plain_body:
                        user_activity[name] += plain_body
                    plain_body = ""

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
    
    print 'done!'

if __name__ == '__main__':
    main()
