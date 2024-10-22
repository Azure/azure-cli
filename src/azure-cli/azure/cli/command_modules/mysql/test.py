from datetime import datetime, timedelta
from dateutil import parser
from dateutil.tz import tzutc
from time import sleep

current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
earliest_restore_time = "2024-10-21T14:50:54.352240+00:00"
seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
print(current_time)
print(seconds_to_wait)
sleep(max(0, seconds_to_wait) + 180)
print("------------end-----------")
