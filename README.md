# scoring-api
## Домашняя работа по ООП

### Установка и запуск

1. Склонируйте репозиторий
2. Установите зависимость с помощью команды

    ```bash 
    make install 
    ```

3. Запустите проект с помощью команды

    ```bash
    make run
    ```

4. Запустите тесты с помощью команды 
    ```bash
    make test
    ```
   
Пример успешного запроса от пользователя:
```
curl --location 'http://127.0.0.1:8080/method/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "account": "horns&hoofs",
    "login": "h&f",
    "method": "online_score",
    "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
    "arguments": {
        "phone": "79175002040",
        "email": "stupnikov@otus.ru",
        "first_name": "Стансилав",
        "last_name": "Ступников",
        "birthday": "01.01.1990",
        "gender": 1
    }
}'
```
Пример успешного запроса от админа:
```
curl --location 'http://127.0.0.1:8080/method' \
--header 'Content-Type: application/json' \
--data-raw '{
    "account": "horns&hoofs",
    "login": "admin",
    "method": "online_score",
    "token": "3f1f78d4912b092606b10851117f866de3292b049c2c19b36c0ba38032348426bfea6e3a62dccd5ff79661b162a3a791e5625e6a85cc0d572ec49a32ba427a6c",
    "arguments": {
        "phone": "79175002040",
        "email": "stupnikov@otus.ru",
        "first_name": "Стансилав",
        "last_name": "Ступников",
        "birthday": "01.01.1990",
        "gender": 1
    }
}'
```

Пример неуспешного запроса с невалидными данными: 
```
curl --location 'http://127.0.0.1:8080/method' \
--header 'Content-Type: application/json' \
--data '{
    "account": "horns&hoofs",
    "login": "admin",
    "method": "online_score",
    "token": "3f1f78d4912b092606b10851117f866de3292b049c2c19b36c0ba38032348426bfea6e3a62dccd5ff79661b162a3a791e5625e6a85cc0d572ec49a32ba427a6c",
    "arguments": {
        "phone": "79175002",
        "email": "stupnikovs.ru",
        "first_name": 2,
        "last_name": "Ступников",
        "birthday": "01.01.1890",
        "gender": -3
    }
}'
```