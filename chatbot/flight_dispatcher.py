from datetime import datetime, timedelta
from vk_api.utils import get_random_id


def return_every_day_of_week(start):
    dates = []
    for i in range(52):
        dates.append(start + timedelta(days=7))
    return dates


def return_every_day(start, *days):
    dates = []
    for day in days:
        for i in range(52):
            date = datetime(year=start.year, month=start.month, day=day, hour=start.hour,
                            minute=start.minute) + timedelta(days=7) * i
            dates.append(date)
    return dates


def get_flight(api, user_id, data, date, departure_city, destination_city):
    date = datetime.strptime(date, "%d-%m-%Y")
    dates = data[departure_city][destination_city]
    # убрать из списка дат, даты меньше текущей
    for d in dates:
        if d < datetime.now():
            dates.remove(d)
    nearest_dates = []
    # находим ближайшие даты к date
    amount = len(dates) if len(dates) < 5 else 5
    for i in range(amount):
        t = min(dates, key=lambda x: abs(x - date))
        dates.remove(t)
        nearest_dates.append(t)

    for i, d in enumerate(nearest_dates, start=1):
        text_to_send = f'{i}. {departure_city} - {destination_city} {d}'
        api.messages.send(message=text_to_send,
                          random_id=get_random_id(),
                          user_id=user_id)
    if nearest_dates:
        return ",".join([str(date) for date in nearest_dates])
    else:
        api.messages.send(message="По выбранным датам нет сообщения, выберите другую дату",
                          random_id=get_random_id(),
                          user_id=user_id)
