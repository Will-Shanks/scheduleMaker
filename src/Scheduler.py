import MySQLdb
from collections import defaultdict
import itertools
import copy
import secrets

db = MySQLdb.connect(host=secrets.DBHOST, user=secrets.DBUSER, passwd=secrets.DBPASSWD, db=secrets.DBNAME)
cur = db.cursor()


class Node:
    def __init__(self, sections):
        self.days = {'M': [], 'T': [], 'W': [], 'R': [], 'F': []}
        self.sections = sections
        if isinstance(sections, int):
            self.addSection(sections)
        else:
            for section in sections:
                self.addSection(section)
        for day in self.days:
            self.days[day].sort()

    def addSection(self, sectionID):
        cur.execute("SELECT start, finish, days FROM section WHERE id='" + str(sectionID) + "';")
        sectionInfo = cur.fetchone()
        if sectionInfo[2] == "ONLINE":
            return
        for day in sectionInfo[2]:
            self.days[day].append([sectionInfo[0], sectionInfo[1]])

    def isCompat(self, b):
        for day in self.days:
            if self.days[day] != [] and b.days[day] != []:
                for timeRange in self.days[day]:
                    i = 0
                    while i < len(b.days[day]):
                        if timeRange[0] == b.days[day][i][0] or timeRange[1] == b.days[day][i][1]:
                            return False
                        if timeRange[0] < b.days[day][i][0]: # self starts before b
                            if timeRange[1] > b.days[day][i][0]:
                                return False
                        if timeRange[0] > b.days[day][i][0]:
                            if timeRange[1] < b.days[day][i][1]:
                                return False
                        i += 1
        return True

# Takes course/section ID
# Returns matrix of Nodes (course component x section) (each section is a node)
def getCourseComponents(course):
    courseComponents = []
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
        cur.execute(
            "SELECT component FROM SECTION WHERE section = '" + sectionCode + "' and  course_id='" + courseID + "';")
        sectionComp = cur.fetchone()[0]

    cur.execute(("SELECT Distinct component FROM section WHERE course_id='" + courseID + "';"))
    sectionID = cur.fetchall()
    # add each component of each class to sections as its own list
    for sect in sectionID:
        if sectionComp == sect[0]:
            cur.execute(
                "SELECT id FROM section WHERE course_id='" + courseID + "' AND section ='" + sectionCode + "';")
        else:
            cur.execute(
                "SELECT id FROM section WHERE course_id='" + courseID + "' AND component ='" + sect[0] + "';")
        componentSectionIDs = cur.fetchall()
        component = []
        for compSectID in componentSectionIDs:
            component.append(Node(compSectID))
        courseComponents.append(component)
    return courseComponents

# Takes matrix of Nodes
# Returns dict of lists node: [edges]
def buildGraph(vertexNodes):
    graph = defaultdict(set)
    if len(vertexNodes) == 1:
        for vertex in vertexNodes[0]:
            graph[vertex] = None
    else:
        for i in range(len(vertexNodes) - 1):
            for j in range(len(vertexNodes[i])):
                k = len(vertexNodes) - 1
                while k > i:
                    for l in range(len(vertexNodes[k])):
                        if vertexNodes[i][j].isCompat(vertexNodes[k][l]):
                            graph[vertexNodes[i][j]].add(vertexNodes[k][l])
                            graph[vertexNodes[k][l]].add(vertexNodes[i][j])
                    k -= 1
    return graph

# Takes dict of lists of nodes and their edges
# Returns list of nodes where each node is a clique of size <numNodesToChoose> of the input nodes
def getCliques(graphEdges, numNodesToChoose):
    def addComplete():
        courses = defaultdict(list)
        for item in compsub:
            for sectID in item.sections:
                cur.execute("SELECT course_id FROM SECTION WHERE id = '" + str(sectID) + "';")
                courseCode = cur.fetchone()[0]
                courses[str(courseCode)].append(sectID)
        for course in courses.keys():
            cur.execute("SELECT COUNT(DISTINCT component) FROM section WHERE course_id =" + course + ";")
            if (len(courses[course]) != cur.fetchone()[0]):
                courses.pop(course)
        if len(courses) < numNodesToChoose:
            return
        courseCombos = list(itertools.combinations(courses, numNodesToChoose))
        nonlocal solutions
        for combo in courseCombos:
            option = []
            for thing in combo:
                option += courses[thing]
                option.sort()
            solutions.add(tuple(option))

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
                nays.append(selected)
                pass

    def getConnected(vertex, oldSet):
        newSet = []
        for neighbor in graphEdges[vertex]:
            try:
                if neighbor in oldSet:
                    newSet.append(neighbor)
            except Exception as inst:
                pass
        if newSet is None:
            pass
        return newSet

    solutions = set()

    if all(v is None for v in graphEdges.values()):
        for x in graphEdges.keys():
            compsub = [x]
            addComplete()
    else:
        compsub = []
        possibles = list(graphEdges.keys())
        recurfunct(possibles, [])
    results = [Node(x) for x in solutions]
    return results

def main(choices):
    # options will be matrix of section nodes
    options = []
    # choice == ["course1", ... "coursen"], numToChoose
    # makes matrix of nodes where each node is a clique
    for choice in choices:
        # getSections will return list of lists of nodes sections[course component][section]
        if isinstance(choice[0], str):
            components = getCourseComponents(choice[0])
        else:
            components = []
            for courseID in choice[0]:
                components += getCourseComponents(courseID)

        if len(components) == 1:
            # if only 1 section then only 1 node in graph and no edges
            options.append([components[0][0]])
        else:
            components.sort(key=lambda comp: len(comp))
            # edges is a list of edges for each node
            # edges[i] = [[edges], [sectionIDs]]
            edges = buildGraph(components)
            # getCliques returns list of nodes (each possible clique is a node
            #getCliques(list of edges, num of nodes to choose
            options.append(getCliques(edges, choice[1]))

    options.sort(key=lambda comp: len(comp))
    edges = buildGraph(options)
    numToChoose = 0
    for choice in choices:
        numToChoose += choice[1]
    options = getCliques(edges, numToChoose)
    sections = [x.sections for x in options]
    sections.sort()
    pass
    for x in sections:
        print(x)


if __name__ == "__main__":
    choices = [[["Math3510", "CSCI3104"], 2]]#, [["HIND1020"], 1]]#, [["CSCI3155"], 1], [["CSCI3022"], 1], [["PHYS1140"], 1]]
    main(choices)
    exit(0)