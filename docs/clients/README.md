# Server-to-Server OAuth аутентификация

### Client Credentials Grant Type:

> Аутентификационные данные выдаются админом и должны хранится в секретах!

 - **realm** - Область системы в которой работает приложение.
 - **client_id** - Публичный уникальный идентификатор приложения.
 - **client_secret** - Секретный пароль приложения.
 - **scope** - Ресурсы к которым приложение имеет доступ.


## API документация

Базовый URL: `/{realm}/oauth` (где **realm** название области системы, передаётся при каждом запросе)

## Получение токена

### POST `/token`

Получает access token для отправки запросов к другим клиентам.

<b>Request</b><sup>required</sup>

Тело запроса

```json
{
  "grant_type": "client_credentials",
  "client_id": "string",
  "client_secret": "string",
  "scope": "string"
}
```

 - **grant_type** - Метод аутентификации.
 - **client_id** - Публичный id клиента.
 - **client_secret** - Секретный 'пароль' клиента.
 - **scope** - Запрашиваемый ресурсы к которым нужен доступ.</br> 
   Пример строки scope:</br>
   ```python
   scope = "api:read profile courses:write"
   ```

<b>Response</b>

 - **200 OK**

```json
{
   "access_token": "string",
   "expires_at": 12345
}
```

 - **access_token** - Access токен передаваемый при каждом запросе к другим клиентам.
 - **expires_at** - Время истечение токена в формате timestamp.

 - **400 Bad request**

Неверный grant_type

 - **401 Unauthorized**

Неверные аутентификационные данные (client_id; client_secret)

 - **403 Forbidden**

Нет доступа к запрашиваемым ресурсам (скорее всего проблема в scope)


## Валидация и декодирование токена

### POST `/introspect`

Производит декодирование и валидацию токена. Использовать для получения данных из токена.

<b>Request</b><sup>required</sup>

Тело запроса

```json
{
   "token": "string"
}
```

 - **token** - JWT который нужно валидировать.

<b>Response</b>

 - **200 OK** (Возвращает 200 даже если токен не валиден)

| Поле JSON                 | Описание                                       |
|---------------------------|------------------------------------------------|
 | active<sup>required</sup> | Активен ли токен                               |
| cause<sup>optional</sup>  | Причина почему токен неактивен                 |
 | token_type                | Тип токена 'access' или 'refresh'              |
  | iss                       | Тот кто подписал токен, https://sso.example.ru |
   | sub                       | client_id                                      |
 | exp                       | Время истечение токена в формате timestamp     |
| iat                       | Время подписания токена в формате timestamp    |
 | jti                       | Уникальный идентификатор токена                |
 | realm                     | Область в которой действителен токен           |
 | scope                     | Права доступа к ресурсам                       |

 - Успешная валидация токена

```json
{
   "active": true,
   "token_type": "access",
   "iss": "https://sso.example.ru",
   "sub": "1ef0141d-57a2-41d3-b1d2-3ef77290a8d8",
   "exp": 12345.00,
   "iat": 12335.00,
   "jti": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "realm": "education",
  "scope": "api:read api:write profiles"
}
```

 - Токен истёк

```json
{
  "active": false,
  "cause": "Token expired"
}
```

 - **401 Unauthorized**

Не получилось декодировать токен (возникает при попытке подменить токен) или же неверная область.
