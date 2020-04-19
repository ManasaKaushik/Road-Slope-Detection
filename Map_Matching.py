import multiprocessing
import math
import csv

def cvrt_pt2line(point,st,end):
    line_vec= (float(end[0])-float(st[0]),float(end[1])-float(st[1]))
    pt_vec = (float(point[0])-float(st[0]),float(point[1])-float(st[1]))
    lengthOfLine = math.sqrt(line_vec[0]*line_vec[0] + line_vec[1]*line_vec[1])
    unitLineVec = (line_vec[0]/math.sqrt(line_vec[0]*line_vec[0] + line_vec[1]*line_vec[1]),line_vec[1]/math.sqrt(line_vec[0]*line_vec[0] + line_vec[1]*line_vec[1]))
    scalingPoint = (pt_vec[0]*1.0/lengthOfLine,pt_vec[1]*1.0/lengthOfLine)
    dot_product = unitLineVec[0]*scalingPoint[0]+unitLineVec[1]*scalingPoint[1]
    if dot_product < 0.0: dot_product = 0.0
    elif dot_product > 1.0:dot_product =1.0
    closest = (line_vec[0]*dot_product,line_vec[1]*dot_product)
    temp = (pt_vec[0] - closest[0],pt_vec[1] - closest[1])
    distance =  math.sqrt(temp[0]*temp[0]+temp[1]*temp[1])
    closest = (closest[0]+float(st[0]),closest[1]+float(st[1]))
    return (distance,closest)

def calcSlope():
    elevation = open('Elevation.csv', 'w').close()  # need to add header
    with open("Partition6467MatchedPoints.csv", "r") as probe_file:
        elevation = open('Elevation.csv', 'w+')
        data_ele = csv.writer(elevation)
        data_ele.writerow(
            ['sampleID', 'dateTime', 'sourceCode', 'latitude', 'longitude', 'altitude', 'speed', 'heading', 'linkPVID',
             'direction', 'distFromRef', 'distFromLink'])
        prev = None
        reader_probe = csv.reader(probe_file, delimiter=",")
        header = next(reader_probe)
        for line in reader_probe:
            probe = {}
            probe['sampleId'] = line[0]
            probe['dateTime'] = line[1]
            probe['sourceCode'] = line[2]
            probe['latitude'] = float(line[3])
            probe['longitude'] = float(line[4])
            probe['altitude'] = line[5]
            probe['speed'] = line[6]
            probe['heading'] = line[7]
            probe['linkPVID'] = line[8]
            probe['direction'] = line[9]
            probe['distFromRef'] = line[10]
            probe['distFromLink'] = line[11]
            probe['street_assigned'] = None
            probe['elevation'] = None
            probe['slope'] = None

            if not prev:
                probe['slope'] = 'X'
            elif probe['linkPVID'] != prev['linkPVID']:
                probe['slope'] = 'X'
            else:
                end_point = list(map(float, [prev['longitude'], prev['latitude']]))
                start_point = list(map(float, [probe['longitude'], probe['latitude']]))
                opp = float(probe['altitude']) - float(prev['altitude'])
                hyp = distanceBetweenPoints(start_point, end_point) / 1000
                if float(hyp) != 0.0:
                    probe['slope'] = math.atan(float(opp) / float(hyp))
                    probe['slope'] = (2 * math.pi * probe['slope']) / 360
                    for link in link_list:
                        if probe['linkPVID'] == link['linkPVID'] and link['slopeInfo'] != '':
                            link['probepoints'].append(probe)
                            break
            data_ele.writerow(
                [probe['sampleId'], probe['dateTime'], probe['sourceCode'], str(probe['latitude']),
                 str(probe['longitude']),
                 probe['altitude'], probe['speed'], probe['heading'], probe['linkPVID'], probe['direction'],
                 str(probe['distFromRef']), str(probe['distFromLink']), str(probe['slope'])])
            prev = probe

        elevation.close()
    print("elevation file written")
    slope = open("SlopeData.csv", "w").close()  # Need to add header

    slope = open("SlopeData.csv", "w")
    data_slp = csv.writer(slope)
    data_slp.writerow(['LinkPVID', 'Calc Slope'])
    for link in link_list:
        if len(link['probepoints']) > 0:
            sum, sumSlope, cslp, culmulate = 0.0, 0.0, 0.0, 0.0
            prbcnt = 0
            mslpe = []
            for probe in link['probepoints']:
                if probe['direction'] == 'T': probe['slope'] = -probe['slope']
                if probe['slope'] != 'X':
                    if probe['slope'] != 0:
                        sum = sum + probe['slope']
                        prbcnt += 1

            if prbcnt != 0:
                cslp = sum / prbcnt
                culmulate = sum
            else:
                cslp = 0
            slpe = link['slopeInfo'].strip().split('|')
            for slope in slpe:
                sumSlope += float(slope.strip().split('/')[1])

            mslpe = sumSlope / len(slpe)
            output = "LinkId %s mean %s calc mean %f" % (link['linkPVID'], mslpe, cslp)
            print(output)
            data_slp.writerow([probe['linkPVID'], cslp])

def partOfStreet(link):
    street = link['shapeInfo']
    lat_lng_ele = street.split("|")
    parts = []
    for i in range(len(lat_lng_ele)-1):
        lat1,lng1, ele1 = lat_lng_ele[i].split("/")
        lat2, lng2, ele2 = lat_lng_ele[i+1].split("/")
        parts.append(([lat1, lng1],[lat2, lng2]))
    return parts

def distanceBetweenPoints(start,end):
    long1, latt1, long2, latt2 = map(math.radians, [start[1], start[0], end[1], end[0]])
    dlong = long2 - long1
    dlatt = latt2 - latt1
    a = math.sin(dlatt / 2) ** 2 + math.cos(latt1) * math.cos(latt2) * math.sin(dlong / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km

def pointDistance( start, end):
    start = list(map(float, start))
    end = list(map(float, end))
    return distanceBetweenPoints(start,end)

def distanceReference(edgePositionIndex,mapMatchedPoint,link):
    parts = partOfStreet(link)
    dis = 0
    for i in range(edgePositionIndex-1):
        dis = dis + pointDistance(parts[i][0],parts[i][1])
    dis += pointDistance(parts[edgePositionIndex][0],mapMatchedPoint)
    return dis*1000
print("Map Matching started")
link_list = []
with open("Partition6467LinkData.csv", "r") as link_file:
    reader_link = csv.reader(link_file, delimiter=",")
    for line in reader_link:
        link_list.append({'linkPVID':line[0],'refNodeId':line[1],'nrefNodeID':line[2],'length':line[3],'class':line[4],
                          'direction':line[5],'speedCategory':line[6],'fromRefSpped':line[7],'toRefSpeed':line[8],
                          'fromRefNumLanes':line[9],'toRefNumLanes':line[10],'multiDigitized':line[11],'urban':line[12],
                          'timezone':line[13],'shapeInfo':line[14],'curvatureInfo':line[15],'slopeInfo':line[16]})
link_file.close()
line_cnt = 0
with open("Partition6467ProbePoints.csv", "r") as probe_file:
    reader_probe = csv.reader(probe_file,delimiter = ",")
    map_match_file = open('Partition6467MatchedPoints.csv','w')
    data = csv.writer(map_match_file)
    data.writerow(['sampleID','dateTime','sourceCode','latitude','longitude','altitude','speed','heading','linkPVID','direction','distFromRef','distFromLink'])
    for line in reader_probe:
        probe = {}
        probe['sampleId'] = line[0]
        probe['dateTime'] = line[1]
        probe['sourceCode'] = line[2]
        probe['latitude'] = float(line[3])
        probe['longitude'] = float(line[4])
        probe['altitude'] = line[5]
        probe['speed'] = line[6]
        probe['heading'] = line[7]
        probe_point = [probe['latitude'], probe['longitude']]
        distanceFromRefPoint, edgePositionIndex, leastDistance = 0,0,0
        for link in link_list:
            part_to_dist = []
            streetParts = partOfStreet(link)
            for part in streetParts:
                start,end = part
                distFromMatchedPoint, matchedPoint = cvrt_pt2line(probe_point,start,end)
                distFromMatchedPoint = distFromMatchedPoint * 1000
                part_to_dist.append(distFromMatchedPoint)
            currentDistance = min(part_to_dist)
            if link is link_list[0]:
                leastDistance = currentDistance
                closestLink = link['linkPVID']
                edgePositionIndex = part_to_dist.index(currentDistance)
                distanceFromRefPoint = distanceReference(edgePositionIndex,matchedPoint,link)
            elif currentDistance<leastDistance:
                leastDistance = currentDistance
                closestLink = link['linkPVID']
                edgePositionIndex = part_to_dist.index(currentDistance)
                distanceFromRefPoint = distanceReference(edgePositionIndex, matchedPoint, link)
        if leastDistance > 15: continue
        if line_cnt == 0:
            oldDistance = distanceFromRefPoint
            oldLink = closestLink
            direc = 'X'
            oldSampleID = probe['sampleId']
        else:
            if probe['sampleId'] == oldSampleID and oldLink == closestLink:
                if distanceFromRefPoint < oldDistance: direc = 'T'
                elif distanceFromRefPoint > oldDistance: direc = 'F'
                else: direc = 'X'
            else: direc = 'X'
            oldDistance = distanceFromRefPoint
            oldLink = closestLink
            oldSampleID = probe['sampleId']
        print("Running Probe",line_cnt)
        data.writerow([probe['sampleId'],probe['dateTime'],probe['sourceCode'],str(probe['latitude']),str(probe['longitude']),probe['altitude'],probe['speed'],probe['heading'],closestLink,direc,str(distanceFromRefPoint),str(leastDistance)])
        line_cnt += 1

print("Map Matching Finished")
map_match_file.close()
probe_file.close()

calcSlope()


