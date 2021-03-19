# -*- coding: utf-8 -*-

import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import logging
import handlers
import flight_dispatcher as fd
from models import UserState

try:
    from chatbot.settings import TOKEN, GROUP_ID, SCENARIOS, DEFAULT_ANSWER, FLIGHT_LIST
except ImportError:
    TOKEN = None
    GROUP_ID = None
    SCENARIOS = None
    DEFAULT_ANSWER = None
    FLIGHT_LIST = None
    print("Ошибки импорта. Завершение программы.")
    exit()

log = logging.getLogger('VKBot')


def configure_logger():
    log.setLevel(logging.DEBUG)

    fh = logging.FileHandler('VKBot.log', 'w', 'utf-8')
    fh.setLevel(logging.INFO)
    formatter_fh = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M')
    fh.setFormatter(formatter_fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    formatter_sh = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter_sh)

    log.addHandler(fh)
    log.addHandler(sh)


class VKBot:

    def __init__(self, group_id, bot_token):
        log.debug("Инициализация бота.")
        self.group_id = group_id
        self.token = bot_token
        self.vk = vk_api.VkApi(token=self.token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        log.debug("Вызов метода run.")
        for event in self.long_poller.listen():
            # log.info(f"Произошло событие {event.type}")
            try:
                self.event_receiver(event)
            except Exception:
                log.exception("Произошла ошибка.")

    @db_session
    def event_receiver(self, event):
        log.debug("Вызов метода _event_receiver")
        events = VkBotEventType
        if event.type != events.MESSAGE_NEW:
            log.info(f"Мы пока не умеем обрабатывать сообщения данного типа. {event.type}")
            return

        user_id = event.object.message['from_id']  # получаем уникальный id пользователя
        text = event.object.message['text']  # текст сообщения отправленного пользователем

        state = UserState.get(user_id=str(user_id))

        if text == '/ticket':
            log.debug("Запуск сценария.")
            text_to_send = self.start_scenario('registration', user_id, state)
        elif text == '/help':
            text_to_send = DEFAULT_ANSWER
        else:
            if state is not None:  # проверяем находится ли пользователь на каком-то шаге сценария
                log.debug("Продолжение сценария.")
                text_to_send = self.continue_scenario(text, state)  # продолжение сценария
            else:
                text_to_send = DEFAULT_ANSWER
        log.debug("Отправка сообщения.")
        self.api.messages.send(message=text_to_send,
                               random_id=get_random_id(),
                               user_id=user_id)  # отправляем пользователю сообщение

    @staticmethod
    def start_scenario(scenario_name, user_id, state):
        if state:
            state.delete()  # убираем пользователя из states, если метод вызван во время прохождения сценария
        scenario = SCENARIOS[scenario_name]  # сценарий dict
        first_step = scenario['first_step']  # название первого шага
        step = scenario['steps'][first_step]  # присвоение первого шага текущему шагу
        text_to_send = step['text']  # получение текста из шага
        UserState(user_id=str(user_id),
                  scenario_name=scenario_name,
                  step_name=first_step,
                  context={})  # создание состояния пользователя
        return text_to_send

    def continue_scenario(self, text, state):
        steps = SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])

        if handler(text=text, context=state.context, data=state.act_result):
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                # переходим на next_step если он есть
                state.step_name = step['next_step']
                state.act_result = self.action(state)  # дополнительные действия, если на определенном шаге они есть
            else:
                # закончить сценарий
                log.info(f'{state.context}')
                state.delete()  # удаляем пользователя из базы
        else:
            # повторить текущий
            text_to_send = step['failure_text']
            if step['rerun']:  # если rerun == True запуск сценария с начала
                text_to_send = self.start_scenario(state.scenario_name, state.user_id, state)

        return text_to_send

    def action(self, state):
        steps = SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        if step['action']:
            act = getattr(fd, step['action'])
            return act(api=self.api, user_id=state.user_id, data=FLIGHT_LIST, **state.context)
        else:
            return state.act_result


if __name__ == '__main__':
    configure_logger()
    bot = VKBot(group_id=GROUP_ID, bot_token=TOKEN)
    bot.run()
