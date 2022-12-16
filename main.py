import os
import sys
from pyicloud import PyiCloudService
from tqdm import tqdm

pc_username = os.getlogin()


def auth(user_login: str, user_password: str):

    """
    Функция выполняет двухфакторную аутентификацию пользователя
    """
    api = PyiCloudService(user_login, user_password)

    if api.requires_2fa:
        print('Требуется двухфакторная аутентификация')
        code = input('Введите полученный код: ')
        result = api.validate_2fa_code(code)
        print('Результат проверки кода: %s' % result)

        if not result:
            print('Не удалось проверить код безопасности')
            sys.exit(1)

        if not api.is_trusted_session:
            print('Сессия не является доверенной. Требует доверия...')
            result = api.trust_session()
            print('Результат сессии %s' % result)

            if not result:
                print('Не удалось запросить доверие. '
                      'Скорее всего, вам снова будет предложено ввести код в ближайшую неделю')
    elif api.requires_2sa:
        import click
        print('Требуется двухэтапная аутентификация. Вашими надежными устройствами являются:')

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print(
                "  %s: %s" % (i, device.get('deviceName',
                "СМС на %s" % device.get('phoneNumber')))
            )

        device = click.prompt('Какое устройство вы хотели бы использовать?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Не удалось отправить проверочный код")
            sys.exit(1)

        code = click.prompt('Пожалуйста, введите код подтверждения')
        if not api.validate_verification_code(device, code):
            print('Не удалось проверить код')
            sys.exit(1)


def create_folder(folder_name):

    """
    Функция создаёт папку.
    Если она уже была создана ранее, ничего не происходит
    :param folder_name: имя папки/директории
    :return: создание папки
    """

    try:
        os.mkdir(folder_name)
    except FileExistsError:
        pass


def main(user_login: str, user_password: str):

    """
    Основной интерфейс.
    Функция сохраняет все медиа-файлы из iCloud в папках, именуемых по дате их создания
    """
    api = PyiCloudService(user_login, user_password)

    create_folder(fr"C:\Users\{pc_username}\Pictures\iCloudPhotoDownloader")

    # получение дат и времени создания каждого файла в виде списка
    print('\nПодготовка данных..')
    date_times = []
    for photo in api.photos.albums['All Photos']:
        date_times.append(photo.created)

    # оставляем у каждого элемента списка только дату (после пробела время отсекается)
    dates = list(map(lambda x: str(x).split()[0], date_times))
    # сохраняем только уникальные даты
    unique_dates = set(dates)

    # создание папок, именованных по датам
    print('Каталогизация по датам создания файлов..')
    for i in unique_dates:
        create_folder(fr"C:\Users\{pc_username}\Pictures\iCloudPhotoDownloader\{i}")

    # загрузка медиафайлов в папки по датам в зависимости от того, когда был создан файл
    print('\nЗагрузка медиафайлов..')
    for photo in tqdm(api.photos.albums['All Photos']):
        folder = str(photo.created).split()[0]

        if os.path.isfile(fr"C:\Users\{pc_username}\Pictures\iCloudPhotoDownloader\{folder}\{photo.filename}") is True:
            # если файл уже есть в соответствующей папке, то мы не тратим на него время и не скачиваем
            continue
        else:
            # загрузка файла в соответствующую папку
            download = photo.download('original')
            with open(fr"C:\Users\{pc_username}\Pictures\iCloudPhotoDownloader\{folder}\{photo.filename}", 'wb') as opened_file:
                opened_file.write(download.raw.read())
    print('\nМедиафайлы загружены на ПК')


if __name__ == '__main__':
    login = input('Введите адрес почты iCloud (example@icloud.com): ')
    password = input('Введите пароль: ')
    auth(login, password)
    main(login, password)
