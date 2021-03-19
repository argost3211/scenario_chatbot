from settings import FLIGHT_LIST
import re

re_Moscow = re.compile(r'\b[М|м][О|о][С|с][К|к][В|в]\w*\b')
re_Paris = re.compile(r'\b[П|п][А|а][Р|р][И|и][Ж|ж]\w*\b')
re_Berlin = re.compile(r'\b[Б|б][Е|е][Р|р][Л|л][И|и][Н|н]\w*\b')
re_London = re.compile(r'\b[Л|л][О|о][Н|н][Д|д][О|о][Н|н]\w*\b')
re_Washington = re.compile(r'\b[В|в][А|а][Ш|ш][И|и][Н|н][Г|г][Т|т][О|о][Н|н]\w*\b')

re_cities = {"Москва": re_Moscow, "Париж": re_Paris, "Берлин": re_Berlin, "Лондон": re_London, "Вашингтон": re_Washington}


def handle_departure_city(text, context, data):
    for city, re_city in re_cities.items():
        if re.findall(re_city, text):
            context["departure_city"] = city
            return True
    else:
        return False


def handle_destination_city(text, context, data):
    for city, re_city in re_cities.items():
        if re.findall(re_city, text):
            try:
                FLIGHT_LIST[context["departure_city"]][city]
            except KeyError:
                return False
            else:
                context["destination_city"] = city
                return True
    else:
        return False


re_date = re.compile(r'\b([0-3]\d-[0-1]\d-[2][\d][\d][\d])\b')


def handle_date(text, context, data):
    match = re.match(re_date, text)
    if match:
        context["date"] = match.group()
        return True
    else:
        return False


def handle_flight(text, context, data):
    data = data.split(",")
    if text in ('1', '2', '3', '4', '5'):
        context["date"] = data[int(text)-1]
        context["flight_number"] = text
        return True
    else:
        return False


def handle_place(text, context, data):
    if text in ('1', '2', '3', '4', '5'):
        context["place_amount"] = text
        return True
    else:
        return False


def handle_comment(text, context, data):
    if text:
        context['comment'] = text
        return True
    else:
        return False


def handle_answer(text, context, data):
    text = text.lower()
    if text == 'да':
        context['confirmed'] = True
        return True
    elif text == 'нет':
        return False
    else:
        return False


re_phone_number = re.compile(r'\b((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}\b')


def handle_phone_number(text, context, data):
    match = re.match(re_phone_number, text)
    if match:
        context["phone_number"] = match.group()
        return True
    else:
        return False
