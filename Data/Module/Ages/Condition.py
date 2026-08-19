import os
import re

def Function_Track_Guid(Back_Mod, hasteE1_Mod, HasteE1_leave_Mod):
    path = [Back_Mod, hasteE1_Mod, HasteE1_leave_Mod]
    for file in path:
        file_path = file
        with open(file_path, "rb") as r0:
            context = r0.read()
            Tracks = re.findall(rb'<Track trackName="(.*?)</Track>', context, re.DOTALL)
            if Tracks:
                for i in range(len(Tracks)):
                    trackName = Tracks[i]
                    guid_track = (re.findall(rb'guid="(.+?)" enabled', trackName)[0]).decode()
                    guid_true = str.encode(f'id="{i}" guid="{guid_track}"')
                    IdGuidFalse = re.findall(str.encode(rf'id="(.+?)" guid="{guid_track}"'), context)
                    if IdGuidFalse:
                        for j in range(len(IdGuidFalse)):
                            j = IdGuidFalse[j].decode()
                            guid_false = str.encode(f'id="{j}" guid="{guid_track}"')
                            context = context.replace(guid_false, guid_true)
        with open(file_path, "wb") as w0:
            w0.write(context)     
            
def Function_Track_Guid_AddGetHoliday(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if not os.path.isfile(file_path):
            continue        
        with open(file_path, "rb") as r0:
            context = r0.read()
            Tracks = re.findall(rb'<Track trackName="(.*?)</Track>', context, re.DOTALL)
            if Tracks:
                for i in range(len(Tracks)):
                    trackName = Tracks[i]
                    guid_track = (re.findall(rb'guid="(.+?)" enabled', trackName)[0]).decode()
                    guid_true = str.encode(f'id="{i}" guid="{guid_track}"')
                    IdGuidFalse = re.findall(str.encode(rf'id="(.+?)" guid="{guid_track}"'), context)
                    if IdGuidFalse:
                        for j in range(len(IdGuidFalse)):
                            j = IdGuidFalse[j].decode()
                            guid_false = str.encode(f'id="{j}" guid="{guid_track}"')
                            context = context.replace(guid_false, guid_true)
        with open(file_path, "wb") as w0:
            w0.write(context)
           