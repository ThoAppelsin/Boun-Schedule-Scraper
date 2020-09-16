from pprint import pprint
from bs4 import BeautifulSoup
import requests
import re
import sys
from collections import OrderedDict
import traceback

deptcodesnames = {
        'ASIA': 'ASIAN+STUDIES',
        'ASIA': 'ASIAN+STUDIES+WITH+THESIS',
        'ATA': 'ATATURK+INSTITUTE+FOR+MODERN+TURKISH+HISTORY',
        'AUTO': 'AUTOMOTIVE+ENGINEERING',
        'BM': 'BIOMEDICAL+ENGINEERING',
        'BIS': 'BUSINESS+INFORMATION+SYSTEMS',
        'BIS': 'BUSINESS+INFORMATION+SYSTEMS+(WITH+THESIS)',
        'CHE': 'CHEMICAL+ENGINEERING',
        'CHEM': 'CHEMISTRY',
        'CE': 'CIVIL+ENGINEERING',
        'COGS': 'COGNITIVE+SCIENCE',
        'CSE': 'COMPUTATIONAL+SCIENCE+%26+ENGINEERING',
        'CET': 'COMPUTER+EDUCATION+%26+EDUCATIONAL+TECHNOLOGY',
        'CMPE': 'COMPUTER+ENGINEERING',
        'CEM': 'CONSTRUCTION+ENGINEERING+AND+MANAGEMENT',
        'PRED': 'EARLY+CHILDHOOD+EDUCATION',
        'EQE': 'EARTHQUAKE+ENGINEERING',
        'EC': 'ECONOMICS',
        'EF': 'ECONOMICS+AND+FINANCE',
        'ED': 'EDUCATIONAL+SCIENCES',
        'CET': 'EDUCATIONAL+TECHNOLOGY',
        'EE': 'ELECTRICAL+%26+ELECTRONICS+ENGINEERING',
        'ELED': 'ELEMENTARY+TEACHER+EDUCATION+(WITHOUT+THESIS)',
        'ETM': 'ENGINEERING+AND+TECHNOLOGY+MANAGEMENT',
        'ENV': 'ENVIRONMENTAL+SCIENCES',
        'ENVT': 'ENVIRONMENTAL+TECHNOLOGY',
        'XMBA': 'EXECUTIVE+MBA',
        'FE': 'FINANCIAL+ENGINEERING',
        'PA': 'FINE+ARTS',
        'FLED': 'FOREIGN+LANGUAGE+EDUCATION',
        'FLT': 'FOREIGN+LANGUAGE+TEACHING+(WITHOUT+THESIS)',
        'GED': 'GEODESY',
        'GPH': 'GEOPHYSICS',
        'GUID': 'GUIDANCE+%26+PSYCHOLOGICAL+COUNSELING',
        'HIST': 'HISTORY',
        'HUM': 'HUMANITIES+COURSES+COORDINATOR',
        'IE': 'INDUSTRIAL+ENGINEERING',
        'INCT': 'INTERNATIONAL+COMPETITION+AND+TRADE',
        'MIR': 'INTERNATIONAL+RELATIONS%3aTURKEY%2cEUROPE+AND+THE+MIDDLE+EAST',
        'MIR': 'INTERNATIONAL+RELATIONS%3aTURKEY%2cEUROPE+AND+THE+MIDDLE+EAST+WITH+THESIS',
        'INTT': 'INTERNATIONAL+TRADE',
        'INTT': 'INTERNATIONAL+TRADE+MANAGEMENT',
        'LS': 'LEARNING+SCIENCES',
        'LING': 'LINGUISTICS',
        'AD': 'MANAGEMENT',
        'MIS': 'MANAGEMENT+INFORMATION+SYSTEMS',
        'MATH': 'MATHEMATICS',
        'SCED': 'MATHEMATICS+AND+SCIENCE+EDUCATION',
        'ME': 'MECHANICAL+ENGINEERING',
        'MECA': 'MECHATRONICS+ENGINEERING+(WITH+THESIS)',
        'MECA': 'MECHATRONICS+ENGINEERING+(WITHOUT+THESIS)',
        'BIO': 'MOLECULAR+BIOLOGY+%26+GENETICS',
        'PHIL': 'PHILOSOPHY',
        'PE': 'PHYSICAL+EDUCATION',
        'PHYS': 'PHYSICS',
        'POLS': 'POLITICAL+SCIENCE%26INTERNATIONAL+RELATIONS',
        'PSY': 'PSYCHOLOGY',
        'YADYOK': 'SCHOOL+OF+FOREIGN+LANGUAGES',
        'SPL': 'SOCIAL+POLICY+WITH+THESIS',
        'SOC': 'SOCIOLOGY',
        'SWE': 'SOFTWARE+ENGINEERING',
        'SWE': 'SOFTWARE+ENGINEERING+WITH+THESIS',
        'TRM': 'SUSTAINABLE+TOURISM+MANAGEMENT',
        'SCO': 'SYSTEMS+%26+CONTROL+ENGINEERING',
        'TRM': 'TOURISM+ADMINISTRATION',
        'WTR': 'TRANSLATION',
        'TR': 'TRANSLATION+AND+INTERPRETING+STUDIES',
        'TK': 'TURKISH+COURSES+COORDINATOR',
        'TKL': 'TURKISH+LANGUAGE+%26+LITERATURE',
        'PRSO': 'UNDERGRADUATE+PROGRAM+IN+PRESCHOOL+EDUCATION',
        'LL': 'WESTERN+LANGUAGES+%26+LITERATURES'
}

def getcells(tr):
    return [td.text.strip() for td in tr("td")]

days = ['M', 'T', 'W', 'Th', 'F', 'S']
daysmap = dict(zip(days, range(len(days))))
TOTAL_HOURS = 14

def cellids(days, hours):
    return [TOTAL_HOURS * day + hour - 1 for day, hour in zip(days, hours)]

def parsedayshours(ncells):
    ncells['days'] = [daysmap[day] for day in re.findall(r'M|Th?|W|F|S', ncells['days'])]
    possiblehours = [[]]
    for c in ncells['hours']:
        forks = []
        for hs in possiblehours:
            if len(hs) > 0 and hs[-1] == '1':
                fork = hs[:]
                fork[-1] += c
                forks.append(fork)
            hs.append(c)
        possiblehours.extend(forks)
    possiblehours = [list(map(int, hs)) for hs in possiblehours if len(hs) == len(ncells['days'])]

    if len(possiblehours) == 1:
        ncells['hours'] = possiblehours[0]
        ncells['cellIds'] = cellids(ncells['days'], ncells['hours'])
    else:
        ncells['hours'] = possiblehours
        ncells['cellIds'] = [cellids(ncells['days'], hours) for hours in ncells['hours']]

def scrapedept(deptaddress):
    raw = requests.get(deptaddress).text
    soup = BeautifulSoup(raw, features="html.parser")

    titlerow = soup.select(".schtitle")[0] # Hopefully there is just one
    titles = OrderedDict((t, t) for t in getcells(titlerow))
    titles['Hours'] = 'hours'
    titles['Days'] = 'days'
    titles['Rooms'] = 'rooms'
    titles['Name'] = 'fullName'
    titles['Code.Sec'] = 'name'
    titles['Cr.'] = 'credits'
    titles['Ects'] = 'ects'
    titles['Exam'] = 'exam'
    titles['Sl.'] = 'sl'
    titles['Departments'] = 'dep'
    titles['Required for Dept.(*)'] = 'req'
    titles['Instr.'] = 'parentName'
    titles['Course Delivery Method'] = 'place'
    titles['Final Exam Location'] = 'final'

    courses = []

    try:
        course = None
        for row in soup.select(".schtd, .schtd2"):
            namedcells = dict(zip(titles.values(), getcells(row)))
            parsedayshours(namedcells)
            if namedcells['name'] == "":
                course['extras'].append(namedcells)
            else:
                course = namedcells
                course['areaCode'], course['digitCode'], course['sectionCode'] = re.match(r'([A-Z]+)\s*([^.]+)\.(\d+)', course['name']).groups()
                course['extras'] = []
                courses.append(course)
    except Exception as err:
        traceback.print_exc()
        # print(err)
    finally:
        return courses

# top level code
if len(sys.argv) > 1:
    deptcourses = scrapedept(sys.argv[1])
    pprint(deptcourses)
else:
    depts = []
    for deptcode, deptname in deptcodesnames.items():
        depts.append({'code': deptcode, 'courses': scrapedept(f"https://registration.boun.edu.tr/scripts/sch.asp?donem=2020/2021-1&kisaadi={deptcode}&bolum={deptname}")})
    pprint(depts)

# import itertools
# cs = list(itertools.chain(*(d['courses'] for d in depts)))
# pprint(sorted(cs, key=lambda c: max([int(x) for x in c['Hours']], default=0), reverse=True)[0:75])
