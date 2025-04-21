CODEX 

Обзор проекта Codex
Codex — это L1‑блокчейн, специально разработанный для мгновенных межбанковских переводов стейблкоинов с минимальными комиссиями и высокой пропускной способностью . В апреле 2025 г. проект успешно привлёк $15,8 млн в посевном раунде, который возглавило DragonFly Capital; в числе других инвесторов — Coinbase Ventures, Circle Ventures и Wintermute .

Функционал скрипта
Этот инструмент автоматизирует массовое добавление в Waitlist (ожидательный список) на платформе Codex:

Загрузка e‑mail
Построчно читает адреса из файла email.txt.

Генерация имён и фамилий
Для каждого адреса создаёт случайное имя и фамилию.

Использование прокси
Поддерживает HTTP‑прокси из файла proxies.txt (формат IP:PORT или USERNAME:PASS@IP:PORT).

Добавление в Waitlist
Отправляет запросы на включение в ожидательный список через API/веб‑формы Codex.

Сохранение результатов
Сохраняет успешные запросы в result/success.txt и неудачные — в result/failed.txt.

Установка и запуск
Клонируйте репозиторий:

bash
git clone https://github.com/airdrop-cmd/CODEX.git

Подготовьте файлы в корне проекта:
email.txt — список e‑mail, по одному адресу на строку
proxies.txt — список прокси в формате IP:PORT или USERNAME:PASS@IP:PORT

Запустите скрипт:
start.bat

Проверьте результаты в папке result/:

success.txt — успешно добавленные в Waitlist адреса
failed.txt — адреса, для которых запрос не прошёл

___________________________________________________

CODEX

Project Overview
Codex is an L1 blockchain specifically designed for instant, low‑fee stablecoin transfers with high throughput. In April 2025, the project successfully raised $15.8 million in a seed round led by DragonFly Capital; other participants included Coinbase Ventures, Circle Ventures, and Wintermute.

Script Functionality
This tool automates bulk additions to the Codex waitlist:

Email Input
Reads email addresses one per line from email.txt.

Name Generation
Generates a random first name and last name for each address.

Proxy Support
Uses HTTP proxies listed in proxies.txt (format IP:PORT or USERNAME:PASS@IP:PORT).

Waitlist Signup
Sends requests to join the waitlist via the Codex API or web forms.

Result Logging

Successful sign‑ups are saved to result/success.txt.

Failed attempts are saved to result/failed.txt.

Installation & Usage
Clone the repository:

git clone https://github.com/airdrop-cmd/CODEX.git
Prepare the input files in the project root:

email.txt — list of email addresses (one per line)
proxies.txt — list of proxies (IP:PORT or USERNAME:PASS@IP:PORT)

Run the script:
start.bat

Check the results in the result/ folder:

success.txt — emails successfully added to the waitlist
failed.txt — emails for which the request failed
