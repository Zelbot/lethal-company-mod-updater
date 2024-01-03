# BUILTIN
import os
import requests
import shutil
import stat
import sys
import time
import zipfile
from datetime import datetime
# PIP
from bs4 import BeautifulSoup
# CUSTOM
import importlib.util
spec = importlib.util.spec_from_file_location('config', './config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)


def config(config_var):
    value = getattr(config_module, config_var, None)
    assert value is not None, f'Cannot find config variable {config_var}'
    return value


BEPINEX_FOLDER = 'BepInEx'
BEPINEX_FOLDER_PATH = os.path.join(config('lethal_company_install_directory'), BEPINEX_FOLDER)


def verify_install_directory():
    if not os.path.exists(config('lethal_company_install_directory')):
        print('Could not find Lethal Company installation at '
              f'"{config("lethal_company_install_directory")}", please adjust the config')
        sys.exit(1)


def backup_current_bepinex():
    current_time = datetime.now().strftime('%d.%m.%Y_%H-%M-%S')
    backup_destination = os.path.join(config('backups_directory'), current_time)

    os.makedirs('backups', exist_ok=True)
    os.makedirs(backup_destination, exist_ok=True)
    shutil.copytree(BEPINEX_FOLDER_PATH, os.path.join(backup_destination, BEPINEX_FOLDER))
    print(f'Created BepInEx backup: {backup_destination}\n')


def install_bepinexpack():
    if os.path.exists(BEPINEX_FOLDER_PATH):
        return

    print('Installing BepInExPack...')
    bepinexpack_page_source = get_mod_page_source(config('bepinexpack_thunderstore_url'))
    bepinexpack_download_link = parse_latest_download_url(bepinexpack_page_source)
    file_name = '-'.join(bepinexpack_download_link.strip('/').split('/')[-2:])

    download_mod(bepinexpack_download_link)
    setup_bepinexpack(file_name)
    delete_bepinexpack_download(file_name)
    print('BepInExPack was installed successfully')


def setup_bepinexpack(file_name):
    extracted_mod_folder_path = extract_mod_zip(file_name + '.zip')

    shutil.copytree(
        os.path.join(extracted_mod_folder_path, 'BepInExPack'), 
        config('lethal_company_install_directory'),
        dirs_exist_ok=True
    )
    os.makedirs(os.path.join(config('lethal_company_install_directory'), 'BepInEx', 'cache'))
    os.makedirs(os.path.join(config('lethal_company_install_directory'), 'BepInEx', 'patchers'))
    os.makedirs(os.path.join(config('lethal_company_install_directory'), 'BepInEx', 'plugins'))


def remove_readonly_file(func, path, _excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def delete_bepinexpack_download(file_name):
    shutil.rmtree(os.path.join(config('mods_directory'), file_name), onerror=remove_readonly_file)
    os.remove(os.path.join(config('mods_directory'), file_name + '.zip'))


def get_mod_page_source(thunderstore_mod_url):
    return requests.get(thunderstore_mod_url).text


def parse_latest_download_url(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    manual_download_el = soup.find(
        lambda tag: tag.name == 'a' and 'Manual Download' in tag.stripped_strings
    )
    return manual_download_el['href']


def download_mod(download_link):
    os.makedirs(config('mods_directory'), exist_ok=True)
    file_name = '-'.join(download_link.strip('/').split('/')[-2:]) + '.zip'
    save_path = os.path.join(os.getcwd(), 'mods', file_name)

    if os.path.exists(save_path):
        print(f'Skipping download of {file_name} as it is already present')
        return

    response = requests.get(download_link)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f'Successfully downloaded {file_name}')
    else:
        print(f'Failed to download {file_name}. Status code: {response.status_code}')


def delete_old_mods(download_link):
    mod_name = download_link.strip('/').split('/')[-2]
    mod_version = download_link.strip('/').split('/')[-1]

    zip_files = [f for f in os.listdir(config('mods_directory')) if f.endswith('.zip')]
    for zip_file in zip_files:
        zip_mod_name, zip_mod_version = os.path.splitext(zip_file)[0].rsplit('-', 1)

        if zip_mod_name == mod_name and zip_mod_version != mod_version:
            os.remove(os.path.join(config('mods_directory'), zip_file))
            print(f'Deleted old version {mod_version} of {mod_name}')


def extract_mod_zip(zip_file):
    extracted_mod_folder_path = os.path.join(
        config('mods_directory'),
        os.path.splitext(zip_file)[0]
    )
    os.makedirs(extracted_mod_folder_path, exist_ok=True)

    zip_file_path = os.path.join(config('mods_directory'), zip_file)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_mod_folder_path)

    return extracted_mod_folder_path


def copy_bepinex_config_files(source_config_path, destination_config_path):
    source_config_files = os.listdir(source_config_path)
    for config_file in source_config_files:
        source_config_file_path = os.path.join(source_config_path, config_file)
        destination_config_file_path = os.path.join(destination_config_path, config_file)

        if os.path.exists(destination_config_file_path):
            print(f'  Will not copy already present {config_file}'
                  ' as to not overwrite custom settings')
        else:
            shutil.copy2(source_config_file_path, destination_config_file_path)


def copy_bepinex_files(extracted_mod_folder_path, destination_bepinex_path):
    source_bepinex_path = os.path.join(extracted_mod_folder_path, BEPINEX_FOLDER)
    source_config_path = os.path.join(source_bepinex_path, 'config')

    if os.path.exists(source_config_path):
        copy_bepinex_config_files(
            source_config_path,
            os.path.join(destination_bepinex_path, 'config')
        )
    shutil.copytree(
        source_bepinex_path, destination_bepinex_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('config')
    )


def copy_lone_dll_and_cfg_files(extracted_mod_folder_path, destination_bepinex_path):
    for root, dirs, files in os.walk(extracted_mod_folder_path):
        for file in files:
            source_file_path = os.path.join(root, file)

            if file.endswith('.dll'):
                destination_path = os.path.join(destination_bepinex_path, 'plugins')
                shutil.copy(source_file_path, destination_path)
            elif file.endswith('.cfg'):
                destination_path = os.path.join(destination_bepinex_path, 'config')
                destination_file = os.path.join(destination_path, file)

                if os.path.isfile(destination_file):
                    print(f'  Will not copy already present {file}'
                          ' as to not overwrite custom settings')
                else:
                    shutil.copy(source_file_path, destination_path)


def copy_all_mods():
    zip_files = [f for f in os.listdir(config('mods_directory')) if f.endswith('.zip')]
    for zip_file in zip_files:
        extracted_mod_folder_path = extract_mod_zip(zip_file)

        try:
            copy_bepinex_files(extracted_mod_folder_path, BEPINEX_FOLDER_PATH)
            print(f'Extracted {zip_file}, copied BepInEx contents to {BEPINEX_FOLDER_PATH}')
        except FileNotFoundError:  # No 'BepInEx' folder in mod's .zip file
            copy_lone_dll_and_cfg_files(extracted_mod_folder_path, BEPINEX_FOLDER_PATH)
            print(f'Extracted {zip_file}, copied'
                  f' .dll and new .cfg files to {BEPINEX_FOLDER_PATH}')


def clean_mod_folder():
    non_zip_files = [file for file in (os.listdir(config('mods_directory')))
                     if not file.lower().endswith('.zip')]
    for non_zip_file in non_zip_files:
        file_path = os.path.join(config('mods_directory'), non_zip_file)
        shutil.rmtree(file_path, onerror=remove_readonly_file)
    print('\nDeleted extracted folders again to save space')


def close_after_ten_seconds():
    print('\n\nAll done :) Much love, z <3')
    print('\nClosing in 10...')
    time.sleep(5)
    for i in range(5, 0, -1):
        print(f'{i}...')
        time.sleep(1)


def main():
    verify_install_directory()
    install_bepinexpack()
    backup_current_bepinex()

    for mod_urls in config('thunderstore_mod_urls'):
        mod_page_source = get_mod_page_source(mod_urls)
        mod_download_link = parse_latest_download_url(mod_page_source)
        download_mod(mod_download_link)
        delete_old_mods(mod_download_link)
    print()

    copy_all_mods()
    clean_mod_folder()
    close_after_ten_seconds()


if __name__ == '__main__':
    main()
