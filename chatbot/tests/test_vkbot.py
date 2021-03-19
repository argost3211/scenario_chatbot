import unittest
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock
from vk_api.bot_longpoll import VkBotMessageEvent
from ..settings import SCENARIOS, DEFAULT_ANSWER
from ..vkbot import VKBot


class VKBotTest(TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object': {'message':
                                {'date': 1598861807, 'from_id': 86348584, 'id': 59, 'out': 0, 'peer_id': 86348584,
                                 'text': '/ticket', 'conversation_message_id': 59, 'fwd_messages': [],
                                 'important': False,
                                 'random_id': 0, 'attachments': [], 'is_hidden': False},
                            'client_info':
                                {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                                 'keyboard': True, 'inline_keyboard': True, 'carousel': False, 'lang_id': 0}
                            },
                 'group_id': 198183850,
                 'event_id': '435e552059cb942ed52a3aee654c5747c492040e'}

    INPUTS = [
        "/ticket",
        "Хочу полететь из вашингТонА",
        "В лонДоН хочу полететь",
        "Тогда в МОСКВУ",
        "22-02-2021",
        "5",
        "/help",
        "2",
        "Хочу 2 места у окна",
        "Да",
        "89012345678"
    ]
    EXPECTED_OUTPUTS = [
        SCENARIOS["registration"]["steps"]["step1"]["text"],  # "Выберите город отправления."
        SCENARIOS["registration"]["steps"]["step2"]["text"],  # "Выберите город назначения."
        SCENARIOS["registration"]["steps"]["step2"]["failure_text"],
        # "Неправильно указан город или между этими городами нет сообщения. Попробуйте еще раз."
        SCENARIOS["registration"]["steps"]["step3"]["text"],  # "Выберите дату поездки в формате ДД-ММ-ГГГГ."
        '1. Вашингтон - Москва 2021-02-15 08:00:00',
        '2. Вашингтон - Москва 2021-03-15 08:00:00',
        '3. Вашингтон - Москва 2021-04-15 08:00:00',
        '4. Вашингтон - Москва 2021-05-15 08:00:00',
        '5. Вашингтон - Москва 2021-06-15 08:00:00',
        SCENARIOS["registration"]["steps"]["step4"]["text"],  # "Выберите рейс из предложенных ниже вариантов."
        SCENARIOS["registration"]["steps"]["step5"]["text"],  # "Выберите количество мест (1-5)."
        DEFAULT_ANSWER,
        SCENARIOS["registration"]["steps"]["step6"]["text"],  # "Укажите ваши пожелания."
        SCENARIOS["registration"]["steps"]["step7"]["text"].format(departure_city="Вашингтон",
                                                                   destination_city="Москва",
                                                                   date="2021-06-15 08:00:00", place_amount="2",
                                                                   comment="Хочу 2 места у окна"),  # Уточняем данные
        SCENARIOS["registration"]["steps"]["step8"]["text"],  # "Введите номер телефона"
        SCENARIOS["registration"]["steps"]["step9"]["text"]
    ]

    def test_run(self):
        count = 5
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        events = Mock(return_value=[event] * count)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = events
        with patch("vkbot.vk_api.VkApi"):
            with patch("vkbot.VkBotLongPoll", return_value=long_poller_listen_mock):
                bot_test = VKBot("", "")
                bot_test.event_receiver = Mock()
                bot_test.run()

                bot_test.event_receiver.assert_called()
                bot_test.event_receiver.assert_any_call(event)
                assert bot_test.event_receiver.call_count == count

    def test_run_ok(self):
        api_mock = Mock()
        send_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event["object"]["message"]["text"] = input_text
            events.append(VkBotMessageEvent(raw=event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch("vkbot.VkBotLongPoll", return_value=long_poller_mock):
            bot = VKBot("", "")
            bot.api = api_mock
            bot.run()

        assert send_mock.call_count == len(self.INPUTS) + 5  # метод get_flight отправляет юзеру 5 полетов дополнительно

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs["message"])

        assert real_outputs == self.EXPECTED_OUTPUTS


if __name__ == '__main__':
    unittest.main()
