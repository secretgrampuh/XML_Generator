import os
from glob import glob
import time
from lxml import etree, objectify
from datetime import datetime
# from ..convenience import is_cv3
import cv2
import sys
import shutil
import shotgun_api3

final_comps=[]
slap_comps=[]
directors_comps=[]
regular_comps=[]
v01_comps=[]
SG_chromakey_comps=[]

missing_comps=[]


comp_dict={}
errorReport=[]
errorReport2=[]

######  Collect Arguments
## sys.argv[1] = XML Start Date
## sys.argv[2] = XML End Date

if len(sys.argv) > 1:
    XML_START_DATE = sys.argv[1]
    if str(XML_START_DATE)[:4] not in ['2023','2024']:
        sys.exit('Dates must be formatted as YYYYMMDD')
    XML_START_DATE_INT=int(XML_START_DATE)
    XML_END_DATE = sys.argv[2]
    if str(XML_START_DATE)[:4] not in ['2023','2024']:
        sys.exit('Dates must be formatted as YYYYMMDD')  
    XML_END_DATE_INT=int(XML_END_DATE)  
    print('starting')    
elif len(sys.argv)==1:
    print("No XML_END_DATE given. Using today's date. If you don't want that, press ctrl+c in the next 10 seconds.")
    XML_END_DATE = int(datetime.now().strftime("%Y%m%d"))
    XML_START_DATE = sys.argv[1]
    if str(XML_START_DATE)[:4] not in ['2023','2024']:
        sys.exit('Dates must be formatted as YYYYMMDD')
    XML_START_DATE_INT=int(XML_START_DATE)
else:
    sys.exit("Script Requires Inputs: XML_START_DATE, then XML_END_DATE. Please try again.")

def Get_Latest_Shots_From_SG(start_date_arg,end_date_arg):
    SG_LIST_start_time = time.time()
    SG_shot_comps_dict={}
    sg_version_dict={}
    SG_shot_comps_dict_chroma_test={}
    SG_shots_to_include=[]
    SG_shots_to_include_Alpha=[]
    SG_shots_to_include_nonAlpha=[]
    SERVER_PATH = "https://trioscope.shotgrid.autodesk.com"
    SCRIPT_NAME = 'PythonScript'
    SCRIPT_KEY = 'fgkqrcqrsbKai@cds7xltcqtd'

    trioscope_sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

    trioscope_filters = [['project', 'is', {'type': 'Project', 'id':311}]]
    trioscope_fields = [
        'id',
        'code',
        'entity',
        'description',
        'playlists',
        'step_0',
        'created_at',
        'sg_task',
        'sg_job_id',
        'sg_uploaded_movie',
        'status',
        'Status',
        'Level',
        'Phase',
        'user',
        'open_notes',
        'attachments',
        'sg_status_list',
        'step',
        'sg_versions',
        'tasks',
    ]
    version_list_start_time=time.time()
    All_Trioscope_Versions = trioscope_sg.find('Version', trioscope_filters, trioscope_fields)
    for version in All_Trioscope_Versions:
        version_name=version['code'].split('.')[0].lower()
        try:
            creator=version['user']['name']
        except:
            creator='brian'
        playlists=version['playlists']
        date_created=int(str(version['created_at']).split(' ')[0].replace('-',''))
        if date_created>=start_date_arg and date_created<=end_date_arg and 'brian' not in creator and 'comp' in version_name:
            if 'chroma' in str(playlists):
                SG_shots_to_include_Alpha.append(version_name)
            else:
                SG_shots_to_include_nonAlpha.append(version_name)

        # sg_version_dict[version_id_]=[date_created,playlists,creator]
    # SG_shots_to_include=SG_shots_to_include_nonAlpha+SG_shots_to_include_Alpha
    return SG_shots_to_include_nonAlpha,SG_shots_to_include_Alpha

    version_list_complete_time=version_list_start_time-time.time()
    print(f'\ncreating version list took {version_list_complete_time} seconds\n')

    shot_list_start_time=time.time()
    All_Trioscope_Shots = trioscope_sg.find('Shot', trioscope_filters, trioscope_fields)
    for shot in All_Trioscope_Shots:
        shotcode=shot['code'].lower()
        assoc_versions=shot['sg_versions']
        # for version in assoc_versions:

        latest_date=0
        latest_date_chroma_test=0
        i=len(assoc_versions)-1
        while i>=0:
            version=assoc_versions[i]
            version_id=version['id']
            version_code=version['name']
            version['name']=version_code.split('.')[0]
            date_created=sg_version_dict[version_id][0]
            version_playlists=sg_version_dict[version_id][1]
            version_creator=sg_version_dict[version_id][2].lower()
            if date_created>latest_date_chroma_test and 'brian' not in version_creator: #For testing purposes only. This dictionary is the true LATEST VERSION, but does not remove ROTO versions
                latest_date_chroma_test=date_created
                SG_shot_comps_dict_chroma_test[shotcode]=version['name'].lower()
            if 'chroma' not in str(version_playlists).lower() and 'comp' in str(version_code).lower() and 'brian' not in version_creator:
                if date_created>latest_date:
                    latest_date=date_created
                    SG_shot_comps_dict[shotcode]=version['name'].lower()

            i-=1
        # print(SG_shot_comps_dict[shotcode])
    for key in SG_shot_comps_dict_chroma_test.keys():
        if key not in SG_shot_comps_dict.keys() and 'comp' in SG_shot_comps_dict_chroma_test[key]:
            SG_shot_comps_dict[key]=SG_shot_comps_dict_chroma_test[key]
    shot_list_complete_time=shot_list_start_time- time.time()
    print(f'creating shot list took {shot_list_complete_time} seconds...\n')
    SG_Latest_Comps_As_List=[]
    for comp in SG_shot_comps_dict.values():
         SG_Latest_Comps_As_List.append(comp)
    SG_Sort_time = time.time() - SG_LIST_start_time
    print(f"SG_List process took {SG_Sort_time} seconds...\n")

    return SG_shot_comps_dict,SG_shot_comps_dict_chroma_test,SG_Latest_Comps_As_List

def Get_SG_Lists():
    SG_LIST_start_time = time.time()
    SG_final_comps=[]
    SG_chromakey=[]
    SERVER_PATH = "https://trioscope.shotgrid.autodesk.com"
    SCRIPT_NAME = 'PythonScript'
    SCRIPT_KEY = 'fgkqrcqrsbKai@cds7xltcqtd'

    trioscope_sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

    trioscope_filters = [['project', 'is', {'type': 'Project', 'id':311}]]
    trioscope_fields = [
        'id',
        'code',
        'entity',
        'description',
        'playlists',
        'step_0',
        'sg_task',
        'sg_job_id',
        'sg_uploaded_movie',
        'status',
        'Status',
        'Level',
        'Phase',
        'open_notes',
        'attachments',
        'sg_status_list',
        'step',
        'tasks',
    ]
    All_Trioscope_Versions = trioscope_sg.find('Version', trioscope_filters, trioscope_fields)
    for version in All_Trioscope_Versions:
        version_code=version['code'].split('.')[0].lower()
        if 'chroma' in str(version['playlists']).lower():
            SG_chromakey.append(version_code)
        if 'final' in str(version['playlists']).lower():
            SG_final_comps.append(version_code)
    SG_Sort_time = time.time() - SG_LIST_start_time
    print(f"SG_List process took {SG_Sort_time} seconds...\n")

    return SG_final_comps,SG_chromakey

def count_frames(path, override=False):
	video = cv2.VideoCapture(path)
	total = 0
	if override:
		total = count_frames_manual(video)
	else:
		try:
			try:
				total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
			except:
				total = int(video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
		except:
			total = count_frames_manual(video)
	video.release()
	return total

def count_frames_manual(video):
	total = 0
	while True:
		(grabbed, frame) = video.read()
		if not grabbed:
			break
		total += 1
	return total         

def Create_original_file_id(current_FileID_List,idx):
    file_id_number=str(len(current_FileID_List)+idx+1)  #Create a new file ID by adding the length of file_ID_List (the number of file-IDs pulled from the original XML), plus adding the idx of the comp that we're processing now, plus one (since enumerate starts at 0)
    currentFileID=f"file-{file_id_number}"  
    if currentFileID in current_FileID_List:
        new_number=idx+1
        currentFileID=Create_original_file_id(current_FileID_List,new_number) # If the File_ID has already been used, do this function recursively and add 1
    else:
        current_FileID_List.append(currentFileID)
    if current_FileID_List not in current_FileID_List:
        current_FileID_List.append(currentFileID)
    return currentFileID


def Create_Update_XML(SG_shots_to_include_nonAlpha,SG_shots_to_include_Alpha):
    comp_path_dict={}
    start_time = time.time()
    ####  Search  for all **comp**.mov** and return as a list, sorted backwards by date, most recent first
    PATH=r"W:\TKO\SHOTS\\"
    allComps = [y for x in os.walk(PATH) for y in glob(os.path.join(x[0], '*comp*.mov'))]
    allComps.sort(reverse=True,key=lambda x: os.path.getmtime(x))
    index_duration = time.time() - start_time
    print(f"indexing process took {index_duration} seconds...\n\nSorting comps by priority...")

    #### Weed out all shots that are in a ChromaKey playlist, make 2 playlists - One that is COMPs and one that is CHROMA

    sorting_start=time.time()
    for current_comp in allComps:
        version_code=os.path.basename(current_comp).split('.')[0].lower()
        if version_code in SG_shots_to_include_Alpha:
            SG_chromakey_comps.append(current_comp)
        elif version_code in SG_shots_to_include_nonAlpha:
            final_comps.append(current_comp)

    #### Create a new list by concatenating the 2 lists. COMP first, then CHROMA
    allComps=[]
    allComps=final_comps+SG_chromakey_comps
    sort_time=time.time() - sorting_start
    print(f"sorting process took {sort_time} seconds...\n\nSorting comps by priority...")

    #### Begin parsing the XML

    videoTrackLists=[[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
    print("crunching xml...")
    xml_file = etree.parse(r"C:\Users\zlamplugh\Documents\zProjects\XML_Generator\TKO_PictureLock_20240403_ZachDelivery_PictureLock_06.xml")
    xml_tree=xml_file.getroot()
    xml_tree_Final=xml_file.getroot()
    xml_tree_to_write=xml_file.getroot()

    # Create an empty dictionary to store the nodes
    node_dict = {}  
    node_dict_2 = {}

    global current_FileID_List
    current_FileID_List=["file-0"]
    # Get all CLIPITEM nodes in the XML file
    nodes = xml_tree.xpath('//video[1]//clipitem')

    # Store each node in the dictionary, using the shotcode as the key
    for node in nodes:
        file_node=node.find('file')
        file_ID_Number=file_node.attrib['id']
        current_FileID_List.append(file_ID_Number)
        name_node = node.find('name')
        if file_node.find('pathurl')!=None:
            if name_node is not None and name_node.getparent() == node:
                shotCode=name_node.text.split(".")[0].split("_MERGED")[0].split('_V0')[0].split('_v0')[0].split('_Layer')[0]
                videoTrackLists[0].append(shotCode)
                if shotCode not in node_dict.keys():
                    node_dict[shotCode] = node
                else:
                    node_dict_2[shotCode] = node


    ### Goes through the concatenated list of stuff to add (from XML start to end dates)
    for idx,item in enumerate(allComps):       ### First correct issues in the paths
        item=item.replace("\\","/").replace("\\\\","/").replace("SHOTS//","SHOTS/")

        #### USE XML to Create a list of all plates locations. Basically this keeps the script from bringing in a newly created shot as a COMP
        dupeCheck_list=[]
        dupecheck_node_find = xml_tree.xpath('//video[1]//pathurl')
        for pathnode in dupecheck_node_find:
            version_path=pathnode.text
            dupeCheck_list.append(version_path)

        # Weed out certain folders here, SHARED, _Trailer, _TKO_TRAILER_SEQUENCES_
        if "SHARED" in item:
            pass
        elif "_Trailer" in item:
            pass
        elif "_TKO_TRAILER_SEQUENCES_" in item:
            pass
        else:
            #### First concatenate the proper directory as read by Premiere.
            newFile_BaseName=os.path.basename(item)
            try:
                newFile_Path="file://tri-stor01/Projects/TKO/SHOTS"+(item.split("SHOTS")[1]).replace("\\","/").replace("\\\\","/").replace("SHOTS//","SHOTS/")
            except:
                print(item)
            #### Do all this crap to format file path so Premiere can read it
            if "SHOTS//" in newFile_Path:
                newFile_Path.replace("SHOTS//","SHOTS/")
            if "_Sh" in newFile_BaseName:
                shotCode=(newFile_BaseName.split("_Sh")[0])+"_Sh"+((newFile_BaseName.split("_Sh")[1]).split("_")[0].split("-")[0].split(".")[0])
            elif "_SH" in newFile_BaseName: 
                shotCode=(newFile_BaseName.split("_SH")[0])+"_Sh"+((newFile_BaseName.split("_SH")[1]).split("_")[0].split("-")[0].split(".")[0])
            if shotCode not in node_dict.keys() and not shotCode.startswith("TKO_"):
                shotCode="TKO_"+shotCode.split("TKO_")[1]
            if shotCode not in node_dict.keys() and not shotCode.endswith("0"):
                shotCode=shotCode+"0"

            ### If the shot exists in the XML
            if shotCode in node_dict.keys() and newFile_Path not in dupeCheck_list:
                nodeToAppend2=etree.tostring(node_dict[shotCode]) ### Convert the node to a string and back again
                nodeToAppend=etree.fromstring(nodeToAppend2)
                nameNodes=nodeToAppend.findall('name') # Find all name nodes within the clipitem node
                for nameNode in nameNodes:
                    if ".mov" in nameNode.text:
                        nameNode.text=newFile_BaseName      # If .mov is in the name node, then update it to be the basename of the new file version, i.e. TKO_001_INT_Sh00010_FinalComp_V04.mov
                for valueNode in nodeToAppend.xpath('.//value'):    # Update all value nodes to be 100 so that stuff isn't overscaled, because the animatic was overscaled
                    if valueNode.text=="300" or valueNode.text=="200":
                        valueNode.text="100"

                durationNode=nodeToAppend.find('duration')  # Get the duration of the original plate from the XML clipitem node
                nodeDuration=durationNode.text
                frameNum=str(count_frames(newFile_Path))    # Get the number of frames from the new file to be appended

                if frameNum!=str(nodeDuration):             # Do some math to clip the new file if it needs to be clipped
                    durationNode.text=frameNum
                    outPointNode=nodeToAppend.find('out')
                    outPointNode.text=frameNum
                    endPointNode=nodeToAppend.find('end')
                    startPointNode=nodeToAppend.find('start')
                    newEndPoint=str(int(startPointNode.text)+int(frameNum))
                    if int(newEndPoint) <= int(endPointNode.text):
                        endPointNode.text=newEndPoint

                fileNode=nodeToAppend.find('file')          # Get the file node from the original clipitem
                currentFileID=Create_original_file_id(current_FileID_List,idx)  # Generate original file_id attribute, i.e. file-0, file-1, all the way through file-1729
                fileNode.attrib['id']=currentFileID

                pathURLNode=fileNode.find('pathurl')        # Update <pathurl> node to be the newfile_path that we are using
                pathURLNode.text=newFile_Path

                i=0
                while i < len(videoTrackLists):             # Goes through each list in videoTrackLists, (which has been organized by date), and attempts to append the current node to that Track. There will only be 3 tracks available though, so this will cut off at 2 new versions
                    if shotCode not in videoTrackLists[i]:
                        videoTrackLists[i].append(shotCode)
                        trackLayer=i+2
                        videoNode=xml_tree_Final.find(f'*//video/track[{trackLayer}]')
                        try:
                            videoNode.append(nodeToAppend) 
                        except:
                            errorReport.append(f"Could not append {shotCode}.... maybe not enough video layers...")
                        break       
                    else:
                        i+=1
            elif shotCode in node_dict_2.keys() and newFile_Path not in dupeCheck_list:         # Does the same process again if the clip exists at 2 places. I.e. Sh00690 exists on the template timeline 2x as 2 different clipitems
                nodeToAppend2=etree.tostring(node_dict[shotCode]) ### Convert the node to a string and back again
                nodeToAppend=etree.fromstring(nodeToAppend2)
                nameNodes=nodeToAppend.findall('name') # Find all name nodes within the clipitem node
                for nameNode in nameNodes:
                    if ".mov" in nameNode.text:
                        nameNode.text=newFile_BaseName      # If .mov is in the name node, then update it to be the basename of the new file version, i.e. TKO_001_INT_Sh00010_FinalComp_V04.mov
                for valueNode in nodeToAppend.xpath('.//value'):    # Update all value nodes to be 100 so that stuff isn't overscaled, because the animatic was overscaled
                    if valueNode.text=="300" or valueNode.text=="200":
                        valueNode.text="100"

                durationNode=nodeToAppend.find('duration')  # Get the duration of the original plate from the XML clipitem node
                nodeDuration=durationNode.text
                frameNum=str(count_frames(newFile_Path))    # Get the number of frames from the new file to be appended

                if frameNum!=str(nodeDuration) and int(frameNum)<int(nodeDuration):             # Do some math to clip the new file if it needs to be clipped
                    durationNode.text=frameNum
                    outPointNode=nodeToAppend.find('out')
                    outPointNode.text=frameNum
                    endPointNode=nodeToAppend.find('end')
                    startPointNode=nodeToAppend.find('start')
                    newEndPoint=str(int(startPointNode.text)+int(frameNum))
                    # if '15545' in str(nodeToAppend.find('name').text):
                    #     pass
                        # endPointNode.text=newEndPoint
                    if int(newEndPoint) <= int(endPointNode.text):
                        endPointNode.text=newEndPoint

                fileNode=nodeToAppend.find('file')          # Get the file node from the original clipitem
                currentFileID=Create_original_file_id(current_FileID_List,idx)  # Generate original file_id attribute, i.e. file-0, file-1, all the way through file-1729
                fileNode.attrib['id']=currentFileID

                pathURLNode=fileNode.find('pathurl')        # Update <pathurl> node to be the newfile_path that we are using
                pathURLNode.text=newFile_Path

                i=0
                while i < len(videoTrackLists):             # Goes through each list in videoTrackLists, (which has been organized by date), and attempts to append the current node to that Track. There will only be 3 tracks available though, so this will cut off at 2 new versions
                    if shotCode not in videoTrackLists[i]:
                        videoTrackLists[i].append(shotCode)
                        trackLayer=i+1
                        videoNode=xml_tree_Final.find(f'*//video/track[{trackLayer}]')
                        try:
                            videoNode.append(nodeToAppend) 
                        except:
                            errorReport.append(f"Could not append {shotCode}.... maybe not enough video layers...")
                        break       
                    else:
                        i+=1
            else:
                errorReport.append(f"{shotCode} not found in XML Node Dictionary... probably misspelled... {item}")
    
    Video_Track_02=xml_tree_Final.find(f'*//video/track[3]')    #This chunk of code swaps the video tracks around. Puts Track 2 on Track 3, puts Track 3 on Track 2
    Video_Track_03=xml_tree_Final.find(f'*//video/track[4]')
    Video_Track_To_Append=xml_tree_to_write.find(f'*//video')
    Video_Track_To_Append.append(Video_Track_03)
    Video_Track_To_Append.append(Video_Track_02)



    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d_%H_%M_%S")
    sequenceName=f"_allComps_{dt_string}"
    sequenceNameNode=xml_tree.xpath('//sequence/name')
    for node in sequenceNameNode:
        node.text=sequenceName

    tree = etree.ElementTree(xml_tree_to_write)
    xml_Folder=r'W:/TKO/SHOTS/_Edit/XML_updates/'
    xml_Archive=r'W:/TKO\SHOTS/_Edit/XML_updates/zArchive/'
    # xml_Folder=r"W:\TKO\SHOTS\_Edit\XML_updates\zTest"
    # xml_Archive=r'W:\TKO\SHOTS\_Edit\XML_updates\zTest\archive'

    allXMLs = [y for x in os.walk(xml_Folder) for y in glob(os.path.join(x[0], '*.xml'))]
    for XML in allXMLs:
        if "zArchive" not in XML:
            baseName=os.path.basename(XML)
            newPath=xml_Archive+"\\"+baseName
            shutil.move(XML,newPath)

    newXML_update_baseFile=f"_allComps_{dt_string}.xml"
    newXML_Update_Path=os.path.join(xml_Folder,newXML_update_baseFile)
    tree.write(newXML_Update_Path, encoding='UTF-8')

    duration = time.time() - start_time
    print("\n")
    print(f"New XML completed... process took {duration} seconds...")

    print("\n\n\n ###### ERROR REPORT: \n\n")
    for item in errorReport:
        if item not in errorReport2:
            errorReport2.append(item)
    for item in errorReport2:
        print(item)

#### this returns shots uploaded WITHIN the XML date range
SG_shots_to_include_nonAlpha,SG_shots_to_include_Alpha=Get_Latest_Shots_From_SG(XML_START_DATE_INT,XML_END_DATE_INT)


Create_Update_XML(SG_shots_to_include_nonAlpha,SG_shots_to_include_Alpha)

# schedule.every(10).minutes.do(Create_Update_XML)
# while True: 
#     schedule.run_pending()
#     time.sleep(1)
