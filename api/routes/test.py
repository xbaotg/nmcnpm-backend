from datetime import date, time, datetime, timedelta

time_string = "23:12 31/05/2024"
start = datetime.strptime(time_string, f"%H:%M %d/%m/%Y")
start_time = datetime.strptime(time_string, f"%H:%M %d/%m/%Y")
finish = start + timedelta(hours=1, minutes=30)

print(start)
print(finish)
print(finish.time().minute)
if start < finish:
    print("true")
