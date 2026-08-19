import os
import re
import uuid

def AddGetHolidayResourcePath(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if not os.path.isfile(file_path):
            continue

        with open(file_path, "rb") as f:
            context = f.read()

        tracks = re.findall(rb'(<Track\b.*?</Track>)', context, re.DOTALL)
        if not tracks:
            continue

        for track in tracks:
            if b'enabled="false"' in track or b'AutoY' in track or b'tongyong_effects' in track:
                continue

            conds = re.findall(rb'(\r?\n\s*<Condition\s+[^>]*/>)', track)
            condition_xml = b"".join(conds)

            matches = re.findall(rb'<String name="(.*?)" value="((?:[Pp]refab_[Ss]kill_[Ee]ffects).*?)" refParamName="" useRefParam="false"\s*/>', track)
            if not matches:
                continue

            all_getholiday = b""
            updated_track = track

            for name, full_path in matches:
                try:
                    guid = str(uuid.uuid4())
                    resource_name = full_path.decode()
                    short_name = "KMㅤModㅤAov - " + guid
                    
                    getholiday = (f'<Track trackName="KM MOD AOV" eventType="GetHolidayResourcePathTick" guid="{guid}" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">').encode()

                    if condition_xml:
                        getholiday += condition_xml + b"\r\n"
                    else:
                        getholiday += b"\r\n"

                    getholiday += (
                        f'      <Event eventName="GetHolidayResourcePathTick" time="0.000" isDuration="false" guid="{guid}">\r\n        <String name="holidayResourcePathPrefix" value="{resource_name}" refParamName="" useRefParam="false" />\r\n        <String name="outPathParamName" value="{short_name}" refParamName="" useRefParam="false" />\r\n      </Event>\r\n    </Track>\r\n    ').encode()

                    all_getholiday += getholiday

                    updated_track = re.sub(rb'<String name="' + re.escape(name) + rb'" value="' + re.escape(full_path) + rb'" refParamName="" useRefParam="false"\s*/>', (f'<String name="{name.decode()}" value="" refParamName="{short_name}" useRefParam="true" />').encode(), updated_track)

                except Exception:
                    continue
                    
            context = context.replace(track, all_getholiday + updated_track)

        with open(file_path, "wb") as f:
            f.write(context)