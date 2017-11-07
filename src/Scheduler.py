import MySQLdb
from collections import defaultdict
import secrets
# import copy

# TODO: create .env file for this info
db = MySQLdb.connect(host=secrets.DBHOST, user=secrets.DBUSER, passwd=secrets.DBPASSWD, db=secrets.DBNAME)
cur = db.cursor()


def findSections(courses):
    sections = []
    for course in courses:
        sectionCode = False
        sectionComp = False
        courseCode = course
        if '-' in course:
            courseCode = course.split('-')
            sectionCode = courseCode[1]
            courseCode = courseCode[0]

        cur.execute("SELECT id FROM course WHERE code='" + courseCode + "';")
        courseID = str(cur.fetchone()[0])
        if sectionCode:
            cur.execute("SELECT component FROM SECTION WHERE section = '" + sectionCode + "' and  course_id='" + courseID + "';")
            sectionComp = cur.fetchone()[0]

        cur.execute(("SELECT Distinct component FROM section WHERE course_id='" + courseID + "';"))
        sectionID = cur.fetchall()
        # add each component of each class to sections as its own list
        for sect in sectionID:
            if sectionComp == sect[0]:
                cur.execute(
                    "SELECT * FROM section WHERE course_id='" + courseID + "' AND section ='" + sectionCode + "';")
            else:
                cur.execute("SELECT * FROM section WHERE course_id='" + courseID + "' AND component ='" + sect[0] + "';")
            sections.append(cur.fetchall())

    sections.sort(key=lambda course: len(
        course))  # sorts sections so the courses with least sections are first for performance
    return sections



def BuildGraph(sections):
    def isCompat(a, b):
        # index 6 is string of days section meets ex: MTWRF
        # index 4 is start time of section meeting (24hr)
        # index 5 is finish time of section meeting (24hr)
        if (a[6] == "ONLINE" or b[6] == "ONLINE"):  # online classes don't have time conflicts
            return True
        for day in a[6]:
            if day in b[6]:
                if (a[4] < b[4]):  # if a starts before b starts
                    if (a[5] > b[4]):  # a must finish before b starts
                        return False
                elif (a[4] < b[5]):  # b must finish before a starts
                    return False
                break  # if compatible on 1 day where both meet, always compatible
        return True

    intersect = defaultdict(set)
    for i in range(len(sections)):  # traverse through each course
        for j in range(len(sections[i])):  # traverse through each section of a course

            sectID = str(sections[i][j][0])
            for k in range(1, len(sections) - i):  # traverse relevant courses (row i + 1 is first row below self in matrix)
                for l in range(len(sections[k + i])):  # traverse through sections of each course
                    if isCompat(sections[i][j], sections[i + k][l]):
                        newSectID = str(sections[i + k][l][0])
                        intersect[sectID].add(newSectID)
                        intersect[newSectID].add(sectID)
    return intersect


class Day:
    def __init__(self):
        self.start = None
        self.finish = None
        self.classes = []
        self.dayLength = 0
        self.timeInClass = 0

    def hasClass(self):
        if self.dayLength > 0:
            return True
        else:
            return False

    def getDayLen(self):
        return self.dayLength

    def addClass(self, sectionID, start, finish):
        self.classes.append(sectionID)
        if start:  # checks not online class
            self.timeInClass += (finish - start).seconds
            if self.start:
                startDelta = self.start.seconds - start.seconds  # if start is earlier than self.start will be positive
                if startDelta > 0:
                    self.dayLength += startDelta
                    self.start = start
                finishDelta = finish.seconds - self.finish.seconds  # if finish is later than self.finish will be positive
                if finishDelta > 0:
                    self.dayLength += finishDelta
                    self.finish = finish
            else:
                self.start = start
                self.finish = finish
                self.dayLength = finish.seconds - start.seconds


class Week:
    def __init__(self, sections):
        self.days = {'M': Day(), 'T': Day(), 'W': Day(), 'R': Day(), 'F': Day()}
        for sectionID in sections:
            cur.execute("SELECT start, finish, days FROM section WHERE id='" + str(sectionID) + "';")
            sectionInfo = cur.fetchone()
            if sectionInfo[2] != "ONLINE":
                for day in sectionInfo[2]:
                    self.days[day].addClass(sectionID, sectionInfo[0], sectionInfo[1])

    def getWeekTime(self):
        time = 0
        for k, day in self.days.items():
            time += day.getDayLen()
        return time


    def longestDayLen(self):
        length = 0
        for k, day in self.days.items():
            curDayLen = day.getDayLen()
            if curDayLen > length:
                length = curDayLen
        return length

    def daysOfClass(self):
        days = 0
        for k, day in self.days.items():
            if day.hasClass():
                days += 1
        return days




def printSched(scheds):
    for sectionID in scheds:
        cur.execute("SELECT course_id, component, section FROM SECTION WHERE id = '" + str(sectionID) + "';")
        sectionInfo = cur.fetchone()
        cur.execute("SELECT name, code FROM course WHERE id='" + str(sectionInfo[0]) + "';")
        courseInfo = cur.fetchone()
        print(courseInfo[1] + "-" + str(sectionInfo[2]) + "     " + courseInfo[0] + "  " + sectionInfo[1])
    print("============================================")

#    def computeRanking(self):
#        # figure out avg day length (start of first class to end of last), free time in day, start of earliest class, end of latest class, number of days with class, longest day length
#        # compute score based off of this
#        self.week = Week(self.Sched)
#        self.longestDay = self.week.longestDayLen()
#        self.numDays = self.week.daysOfClass()
#        self.avgDayLen = self.week.getWeekTime()/self.numDays
#
#    def getNumDays(self):
#        return self.numDays
#
#    def getLongestDay(self):
#        return self.longestDay
#
#    def getAVGDayLength(self):
#        return self.avgDayLen


def makeScheds(edges, required):

    def addComplete():
        nonlocal solutions
        courses = defaultdict(list)
        for section in compsub:
            cur.execute("SELECT course_id FROM SECTION WHERE id = '" + section + "';")
            courseCode = cur.fetchone()[0]
            courses[str(courseCode)].append(section)
        for course in list(courses.keys()):
            cur.execute("SELECT COUNT(DISTINCT component) FROM section WHERE course_id =" + course + ";")
            if (len(courses[course]) != cur.fetchone()[0]):
                courses.pop(course)
        if required:
            for thing in required:
                cur.execute("SELECT id from course where  code = '"+ thing + "';")
                if(str(cur.fetchone()[0]) not in courses):
                    return
        courses = list(courses.values())
        courses = [item for sublist in courses for item in sublist]
        courses.sort(key=lambda x: int(x))
        courses = tuple(courses)
        solutions.add(courses)
    def recurfunct(candidates, nays):
        nonlocal compsub
        if not candidates and not nays:
            addComplete()
        else:
            for selected in candidates.copy():
                candidates.remove(selected)
                candidatesTemp = getConnected(selected, candidates)
                naysTemp = getConnected(selected, nays)
                compsub.append(selected)
                recurfunct(candidatesTemp, naysTemp)
                compsub.pop()
                nays.add(selected)

    def getConnected(vertex, oldSet):
        newSet = set()
        for neighbor in edges[str(vertex)]:
            if neighbor in oldSet:
                newSet.add(neighbor)
        return newSet

    compsub = []
    solutions = set()
    possibles = set(edges.keys())
    recurfunct(possibles, set())
    return solutions









def main():
    #TODO: make interface to get class list from user
    #TODO: add way to filter what sections (i.e. I want section 1 of CSCI3104 and not section 2 of MATH3510 and no classes before 10)
    classes = "CSCI 3104-200B, MATH 3510, HIND1020-1, CSCI3155, CSCI3022, PHYS1140"  # list of desired courses
    requiredCourses = ["MATH3510"]
    courses = list(set(classes.strip().replace(" ", "").split(',')))  # make list of course codes
    sections = findSections(courses)
    edges = BuildGraph(sections)
    scheds = makeScheds(edges, requiredCourses)  # creates list(q) of all possible schedules
    i = 1
    for item in scheds:
        print(i)
        printSched(item)
        i += 1
    #Scheds.computeRanking()
    #Scheds.printSchedules()
    #TODO: make GUI to visually represent each sched on a calendar for visual comparison
    #TODO: come up with ways to rank schedules by how good they are (avg day length, days of class, shortes day, earliest class, latest class etc)
    print("bye")


if __name__== "__main__":
    main()
    exit(0)
