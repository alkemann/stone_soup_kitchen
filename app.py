import math
import re
import glob
import urllib.request as req
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from statistics import median

DETAILS = False
VERSION = sys.argv[1] if len(sys.argv) > 1 else False
# VERSION = '0.23'

hp = re.compile('Health:\s+-?\d+/(?P<hp>\d+) .*XL:\s+(?P<xl>\d+).*')
fp = re.compile('\s*[O\+\-\*] Level (\d+\.\d+)[( ].*')
level_pattern = re.compile('\d+ (?P<name>\w+).*level (?P<level>\d+).*')
named_pattern = re.compile('[\w\s-]+ [\w\s\)\(]+\s+Turns: (?P<turns>\d+), Time: (?P<time>[\d:]+)')
role_pattern = re.compile('\s+Began as (a|an) (?P<role>[\w\s]+) on .*')
runes_pattern = re.compile('\}: (?P<runes>\d+)/15 runes')

def make_char(lines):
    global VERSION
    c = {"hf": False, "fi": 0, 'won': False, 'god': 'Atheist'}
    c['version'] = lines[0][34:38]
    if VERSION and c['version'] != VERSION:
        return None

    for s in lines:
        if "Escaped with the Orb" in s:
            c['won'] = True
        if "/15 runes" in s:
            c['runes'] = runes_pattern.match(s).group('runes')

        if "You worshipped" in s:
            c['god'] = s[15:-2]

        if "Health: " in s:
            m = hp.match(s)
            if not m: print("HEALTH ERROR", s);exit(1)
            c['hp'] = int(m.group('hp'))
            c['xl'] = int(m.group('xl'))
            c['lh'] = c['hp'] / c['xl']

        # if "Fighting" in s and "Level" in s:
        #     m = fp.match(s)
        #     if not m: print("FIGHTING ERROR", s); exit(1)
        #     if m:
        #         c['hf'] = True
        #         c['fi'] = float(m.group(1))

        if "HPs" in s:
            m = level_pattern.match(s)
            if not m: print("NAME/LEVEL ERROR: " + s); exit(1);
            c['name'] = m.group("name")
            c['level'] = m.group("level")

        if "Began as" in s:
            m = role_pattern.match(s)
            if not m: print("ROLE ERROR: " + s); exit(1)
            c['role'] = m.group('role')

        if "Time: " in s:
            m = named_pattern.match(s)
            if not m: print("ERROR: " + s); exit(1)
            c['turns'] = m.group("turns")
            c['time'] = t = m.group("time")
            hours = int(t[:2])
            minutes = int(t[3:5])
            seconds = int(t[6:8])
            c['duration'] = (hours * 60) + minutes + (1 if seconds > 30 else 0)

    return c


def grab_online_morgue(URL):
    page = req.urlopen(URL)
    soup = BeautifulSoup(page, "html.parser")
    for a in soup.find_all('a'):
        if "morgue-" not in "%s"%a:
            continue

        fn = a.attrs['href']
        if fn[-3:] != 'txt':
            continue

        my_file = Path("files/" + fn)
        if my_file.is_file():
            continue
        # print(URL + fn)
        with open("files/" + fn, "w") as text_file:
            text_file.write(req.urlopen(URL + fn).read().decode('utf-8'))


def grab_local_morgue(path="files"):
    chars = []
    for fn in glob.glob(path + "/morgue*.txt"):
        with open(fn, "r", encoding="utf-8", errors="ignore") as f:
            # print(fn)
            c = make_char(f.readlines())
            if c is not None:
                chars.append(c)
    return chars


def plots():
    X = []
    Y = []
    for c in chars:
        X.append(c['fi'])
        Y.append(c['hp'])

    plt.scatter(X,Y)
    plt.xlabel('Fighting')
    plt.ylabel('HP per level')

    plt.title('Fighting and HP/level')

    plt.show()

if __name__ == '__main__':

    print(" - ")

    print(" Results for %s"%("All versions recorded" if VERSION is False else VERSION ))

    # Add one of these for each online server you play at, value should be to the "folder"
    grab_online_morgue('https://underhound.eu/crawl/morgue/alkemann/')
    grab_online_morgue('https://underhound.eu/crawl/morgue/lextramoth/')
    grab_online_morgue("https://crawl.xtahua.com/crawl/morgue/lextramoth/")

    # You can also put any locally played morgues in the 'files' folder
    chars = grab_local_morgue()
    wins = list(filter(lambda w: w['won'], chars))

    wun_roles = {}
    roles = {}
    levels = {}
    attempts = {}
    gods = {}
    wun_gods = {}
    total_duration = 0
    for c in chars:
        l = int(c['level'])
        if l in levels:
            levels[l] += 1
        else:
            levels[l] = 1

        role = c['role']
        if (role in roles and roles[role] < l) or role not in roles:
            roles[role] = l

        attempts[role] = attempts[role] + 1 if role in attempts else 1

        g = c['god']
        gods[g] = gods[g] + 1 if g in gods else 1

        if c['won']:
            wun_roles[role] = wun_roles[role] + 1 if role in wun_roles else 1
            wun_gods[g] = wun_gods[g] + 1 if g in wun_gods else 1

        total_duration += c['duration']

        # print(c['name'] + " level " + c['level'] + " " + c['role'] + " [ " + c['turns'] + " " + c['time'] + ']')

    # print(" - ")

    # for l,c in reversed(sorted(levels.items())):
    #     print("Level %s: %s characters" % (l, c))

    if DETAILS:
        print(" - ")

        print("Max\tRuns\tRole")
        for r,l in reversed(sorted(roles.items(), key=lambda x:x[1])):
            print(" %s\t %s\t%s" % (l, attempts[r], r))

        print(" - ")

        print("#\tGods")
        for r,l in reversed(sorted(gods.items(), key=lambda x:x[1])):
            print(" %s\t %s" % (l, r))

    print(" - ")

    if len(wun_roles) > 0:
        print("Wins\tRuns\tGod")
        for r, l in reversed(sorted(wun_gods.items(), key=lambda x: x[1])):
            print(" %s\t %s\t%s" % (l, gods[r], r))

        print(" - ")

        print("Wins\tRuns\tRole")
        for r, l in reversed(sorted(wun_roles.items(), key=lambda x: x[1])):
            print(" %s\t %s\t%s" % (l, attempts[r], r))

        print(" - ")

        dur = "%s hours %s minutes" % (math.floor(total_duration / 60), total_duration % 60)
        print("For a total play time of: %s" % (dur))
        games = len(chars)
        print("From %s games with %s wins" % (games, len(wins)))

        win_durations = list(map(lambda x: x['duration'], wins))
        qw = int(min(win_durations))
        print("With quickest win at: %s hours %s minutes"%(math.floor(qw/60), qw % 60))
        aw = median(win_durations)
        print("With an median win at: %s hours %s minutes"%(math.floor(aw/60), aw % 60))
        sw = int(max(win_durations))
        print("With slowest win at: %s hours %s minutes"%(math.floor(sw/60), sw % 60))
    else:
        dur = "%s hours %s minutes" % (math.floor(total_duration / 60), total_duration % 60)
        print("For a total play time of: %s" % (dur))
        games = len(chars)
        print("From %s games with no wins" % (games))
        print("With an average play time of: %s minutes"%(int(total_duration / games)))
        max_duration = max(list(map(lambda x: x['duration'], chars)))
        print("And longest game at: %s hours %s minutes"%(math.floor(max_duration/60), max_duration % 60))

    print(" - ")
