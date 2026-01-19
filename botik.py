import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import json
import time
from datetime import datetime, timedelta

# Конфигурация бота
GROUP_ID = '235436178'
TOKEN = 'vk1.a.EgkR2bJaDuQLgr_339kosMO2KLAVopbKQYXvGml6NEMvsTrqxfsYkojqfWcWk0WKxNOZVyAexK6CgA_vn7bPYjSoWUzu1v2oTGx2l2dB_QSatccPglzh0WPxBwwoK6GDzGe5QQuYbwy_M532DgIDvaq0Py2CyWfmTLjmrYOPGg82UFo3mEnHbSmz6ZBxnK2sZNNYK8zVe0toP8ftpJz18A'
ADMINS = [865505970]  # СЮДА НАПИШИ СВОЙ АЙДИ АККАУНТА 

# Инициализация
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# Базы данных (в реальном проекте используйте БД)
nicknames = {}
roles = {}
custom_roles = {}
banned_users = []
muted_users = {}  # {user_id: unmute_time}

def save_data():
    data = {
        'nicknames': nicknames,
        'roles': roles,
        'custom_roles': custom_roles,
        'banned_users': banned_users
    }
    with open('bot_data.json', 'w') as f:
        json.dump(data, f)

def load_data():
    global nicknames, roles, custom_roles, banned_users
    try:
        with open('bot_data.json', 'r') as f:
            data = json.load(f)
            nicknames = data.get('nicknames', {})
            roles = data.get('roles', {})
            custom_roles = data.get('custom_roles', {})
            banned_users = data.get('banned_users', [])
    except FileNotFoundError:
        pass

def send_message(peer_id, message):
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        random_id=get_random_id()
    )

def is_admin(user_id):
    return user_id in ADMINS

def get_user_name(user_id):
    user = vk.users.get(user_ids=user_id)[0]
    return f"{user['first_name']} {user['last_name']}"

def handle_command(event):
    user_id = event.message['from_id']
    peer_id = event.message['peer_id']
    text = event.message['text'].lower()
    words = text.split()
    
    if not words:
        return
    
    command = words[0]
    
    # Проверка на бан
    if user_id in banned_users:
        send_message(peer_id, "🚫 Вы заблокированы и не можете использовать команды.")
        return
    
    # Проверка на мут
    if user_id in muted_users and muted_users[user_id] > time.time():
        send_message(peer_id, "🔇 Вы в муте и не можете писать.")
        return
    
    # Обработка команд
    if command == '/start':
        send_message(peer_id, "🤖 Бот активирован! Используйте /help для списка команд.")
    
    elif command == '/id':
        send_message(peer_id, f"🆔 Ваш ID: {user_id}")
    
    elif command == '/kick' and is_admin(user_id):
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
            send_message(peer_id, f"👢 Пользователь {get_user_name(target_id)} исключен из чата.")
        else:
            send_message(peer_id, "❌ Используйте: /kick в ответ на сообщение пользователя.")
    
    elif command == '/pin' and is_admin(user_id):
        if 'reply_message' in event.message:
            message_id = event.message['reply_message']['id']
            vk.messages.pin(peer_id=peer_id, message_id=message_id)
            send_message(peer_id, "📌 Сообщение закреплено.")
        else:
            send_message(peer_id, "❌ Используйте: /pin в ответ на сообщение.")
    
    elif command == '/unpin' and is_admin(user_id):
        vk.messages.unpin(peer_id=peer_id)
        send_message(peer_id, "📌 Сообщение откреплено.")
    
    elif command == '/snick':
        if len(words) > 2 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            nickname = ' '.join(words[2:])
            nicknames[str(target_id)] = nickname
            save_data()
            send_message(peer_id, f"🏷 Пользователю {get_user_name(target_id)} установлен ник: {nickname}")
        else:
            send_message(peer_id, "❌ Используйте: /snick [ник] в ответ на сообщение пользователя.")
    
    elif command == '/rnick':
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            if str(target_id) in nicknames:
                del nicknames[str(target_id)]
                save_data()
                send_message(peer_id, f"🏷 Ник пользователя {get_user_name(target_id)} удален.")
            else:
                send_message(peer_id, f"ℹ️ У пользователя {get_user_name(target_id)} нет ника.")
        else:
            send_message(peer_id, "❌ Используйте: /rnick в ответ на сообщение пользователя.")
    
    elif command == '/nlist':
        if nicknames:
            nlist = "\n".join([f"{get_user_name(int(id))}: {nick}" for id, nick in nicknames.items()])
            send_message(peer_id, f"📋 Список ников:\n{nlist}")
        else:
            send_message(peer_id, "ℹ️ Ники не установлены.")
    
    elif command == '/gnick':
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            nickname = nicknames.get(str(target_id), "не установлен")
            send_message(peer_id, f"🏷 Ник пользователя {get_user_name(target_id)}: {nickname}")
        else:
            send_message(peer_id, "❌ Используйте: /gnick в ответ на сообщение пользователя.")
    
    elif command == '/role':
        if len(words) > 2 and is_admin(user_id) and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            role = ' '.join(words[2:])
            roles[str(target_id)] = role
            save_data()
            send_message(peer_id, f"🎭 Пользователю {get_user_name(target_id)} выдана роль: {role}")
        else:
            send_message(peer_id, "❌ Используйте: /role [роль] в ответ на сообщение пользователя.")
    
    elif command == '/roles':
        if roles:
            role_list = "\n".join([f"{get_user_name(int(id))}: {role}" for id, role in roles.items()])
            send_message(peer_id, f"🎭 Список ролей:\n{role_list}")
        else:
            send_message(peer_id, "ℹ️ Роли не выданы.")
    
    elif command == '/rr' and is_admin(user_id):
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            if str(target_id) in roles:
                del roles[str(target_id)]
                save_data()
                send_message(peer_id, f"🎭 Роль пользователя {get_user_name(target_id)} удалена.")
            else:
                send_message(peer_id, f"ℹ️ У пользователя {get_user_name(target_id)} нет роли.")
        else:
            send_message(peer_id, "❌ Используйте: /rr в ответ на сообщение пользователя.")
    
    elif command == '/admins':
        admin_list = "\n".join([get_user_name(admin) for admin in ADMINS])
        send_message(peer_id, f"👑 Администраторы:\n{admin_list}")
    
    elif command == '/ban' and is_admin(user_id):
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            if target_id not in banned_users:
                banned_users.append(target_id)
                save_data()
                send_message(peer_id, f"🚫 Пользователь {get_user_name(target_id)} заблокирован.")
            else:
                send_message(peer_id, f"ℹ️ Пользователь {get_user_name(target_id)} уже заблокирован.")
        else:
            send_message(peer_id, "❌ Используйте: /ban в ответ на сообщение пользователя.")
    
    elif command == '/unban' and is_admin(user_id):
        if len(words) > 1 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            if target_id in banned_users:
                banned_users.remove(target_id)
                save_data()
                send_message(peer_id, f"✅ Пользователь {get_user_name(target_id)} разблокирован.")
            else:
                send_message(peer_id, f"ℹ️ Пользователь {get_user_name(target_id)} не заблокирован.")
        else:
            send_message(peer_id, "❌ Используйте: /unban в ответ на сообщение пользователя.")
    
    elif command == '/addrole' and is_admin(user_id):
        if len(words) > 2:
            role_name = ' '.join(words[1:])
            custom_roles[role_name.lower()] = role_name
            save_data()
            send_message(peer_id, f"🎭 Создана новая роль: {role_name}")
        else:
            send_message(peer_id, "❌ Используйте: /addrole [название роли]")
    
    elif command == '/mute' and is_admin(user_id):
        if len(words) > 2 and 'reply_message' in event.message:
            target_id = event.message['reply_message']['from_id']
            try:
                minutes = int(words[1])
                unmute_time = time.time() + minutes * 60
                muted_users[target_id] = unmute_time
                send_message(peer_id, f"🔇 Пользователь {get_user_name(target_id)} замьючен на {minutes} минут.")
            except ValueError:
                send_message(peer_id, "❌ Укажите время в минутах: /mute [минуты]")
        else:
            send_message(peer_id, "❌ Используйте: /mute [минуты] в ответ на сообщение пользователя.")
    
    elif command == '/del' and is_admin(user_id):
        if 'reply_message' in event.message:
            message_id = event.message['reply_message']['id']
            vk.messages.delete(message_ids=message_id, delete_for_all=1)
            send_message(peer_id, "🗑 Сообщение удалено.")
        else:
            send_message(peer_id, "❌ Используйте: /del в ответ на сообщение.")
    
    elif command == '/help':
        help_text = """
📋 Список команд:
/start - Активация бота
/id - Узнать свой ID
/kick - Исключить пользователя (только админы)
/pin - Закрепить сообщение (только админы)
/unpin - Открепить сообщение (только админы)
/snick [ник] - Установить ник (в ответ на сообщение)
/rnick - Удалить ник (в ответ на сообщение)
/nlist - Список всех ников
/gnick - Узнать ник пользователя (в ответ на сообщение)
/role [роль] - Выдать роль (в ответ на сообщение, только админы)
/roles - Список всех ролей
/rr - Удалить роль (в ответ на сообщение, только админы)
/admins - Список админов
/ban - Забанить пользователя (только админы)
/unban - Разбанить пользователя (только админы)
/addrole [название] - Создать новую роль (только админы)
/mute [минуты] - Мут пользователя (только админы)
/del - Удалить сообщение (только админы)
"""
        send_message(peer_id, help_text)

# Загрузка данных
load_data()

# Очистка устаревших мутов
def clean_mutes():
    current_time = time.time()
    to_remove = [user_id for user_id, unmute_time in muted_users.items() if unmute_time < current_time]
    for user_id in to_remove:
        del muted_users[user_id]

# Основной цикл
print("Бот запущен...")
while True:
    try:
        clean_mutes()
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_command(event)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)