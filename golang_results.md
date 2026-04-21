time="2026-04-21T17:15:06+03:00" level=warning msg="C:\\Users\\arina\\OneDrive\\Desktop\\Аида ВКР\\go-python-backend-comparison\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] down 1/1
 ✔ Volume go-python-backend-comparison_postgres_python_data Removed                              0.1s 
time="2026-04-21T17:15:06+03:00" level=warning msg="C:\\Users\\arina\\OneDrive\\Desktop\\Аида ВКР\\go-python-backend-comparison\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"                                                      time="2026-04-21T17:15:06+03:00" level=warning msg="No services to build"                             [+] up 4/4                                                                                             ✔ Network go-python-backend-comparison_default         Created                                  0.0s 
 ✔ Volume go-python-backend-comparison_postgres_go_data Created                                  0.0s 
 ✔ Container postgres_go                                Healthy                                  6.1s 
 ✔ Container golang-service                             Created                                  0.1s 
Ожидание запуска сервиса.... ГОТОВО!

--- ШАГ 1: ПРОВЕРКА СОСТОЯНИЯ (HEALTH CHECK) ---


StatusCode        : 200
StatusDescription : OK
Content           : {"status":"ok"}

RawContent        : HTTP/1.1 200 OK
                    Content-Length: 16
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:14 GMT

                    {"status":"ok"}

Forms             :
Headers           : {[Content-Length, 16], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:15:14 GMT]}                                                                    Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 16


--- ШАГ 2: МЕТРИКИ ---
StatusCode        : 200
StatusDescription : OK
Content           : # HELP app_cpu_seconds_total Total CPU time used by the application (placeholder) 
                    # TYPE app_cpu_seconds_total counter
                    app_cpu_seconds_total 0
                    # HELP app_memory_bytes Application memory usage in bytes...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 1619
                    Content-Type: text/plain; version=0.0.4; charset=utf-8; escaping=underscores      
                    Date: Tue, 21 Apr 2026 14:15:14 GMT

                    # HELP app_cpu_seconds_total Total CPU time ...
Forms             :
Headers           : {[Content-Length, 1619], [Content-Type, text/plain; version=0.0.4; charset=utf-8; 
                     escaping=underscores], [Date, Tue, 21 Apr 2026 14:15:14 GMT]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 1619


--- ШАГ 3: СОЗДАНИЕ ТОВАРА 1 ---

id    : 1
name  : Laptop
price : 100000
stock : 50

                                                                                                      --- ШАГ 4: СОЗДАНИЕ ТОВАРА 2 ---                                                                                                                                                                            id    : 2                                                                                             
name  : Smartphone
price : 50000
stock : 100


--- ШАГ 5: СПИСОК ТОВАРОВ ---
StatusCode        : 200
StatusDescription : OK
Content           : [{"id":2,"name":"Smartphone","price":50000,"stock":100},{"id":1,"name":"Laptop","
                    price":100000,"stock":50}]

RawContent        : HTTP/1.1 200 OK
                    Content-Length: 108
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:14 GMT

                    [{"id":2,"name":"Smartphone","price":50000,"stock":100},{"id":1,"name":"Laptop"," 
                    price":100...
Forms             :
Headers           : {[Content-Length, 108], [Content-Type, application/json], [Date, Tue, 21 Apr 2026 
                     14:15:14 GMT]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 108


--- ШАГ 6: СОЗДАНИЕ ЗАКАЗА 1 (Товар 1: 5 шт) ---

id         : 1
status     : new
created_at : 2026-04-21T14:15:14.907897Z
items      : {@{product_id=1; quantity=5; price_at_order=100000}}


--- ШАГ 7: ПРОВЕРКА ОСТАТКОВ (ТОВАР 1, ожидается 45) ---

id    : 1
name  : Laptop
price : 100000
stock : 45


--- ШАГ 8: СОЗДАНИЕ ЗАКАЗА 2 (Товар 2: 1 шт) ---

id         : 2
status     : new
created_at : 2026-04-21T14:15:14.975728Z
items      : {@{product_id=2; quantity=1; price_at_order=50000}}


--- ШАГ 9: ПРОВЕРКА ОСТАТКОВ (ТОВАР 2, ожидается 99) ---

id    : 2
name  : Smartphone
price : 50000
stock : 99


--- ШАГ 10: СОЗДАНИЕ ЗАКАЗА 3 (Смешанный) ---

id         : 3
status     : new
created_at : 2026-04-21T14:15:15.039766Z
items      : {@{product_id=1; quantity=1; price_at_order=100000}, @{product_id=2; quantity=2; price_a 
             t_order=50000}}


--- ШАГ 11: ФИНАЛЬНЫЕ ОСТАТКИ ---
Товар 1:

id    : 1
name  : Laptop
price : 100000
stock : 44
                                                                                                      Товар 2:                                                                                                                                                                                                    id    : 2                                                                                             
name  : Smartphone
price : 50000
stock : 97


--- ШАГ 12: ИТОГО ПО ЗАКАЗУ 3 ---
StatusCode        : 200
StatusDescription : OK
Content           : {"order_id":3,"total":200000}

RawContent        : HTTP/1.1 200 OK
                    Content-Length: 30
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:15 GMT

                    {"order_id":3,"total":200000}

Forms             :
Headers           : {[Content-Length, 30], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:15:15 GMT]}                                                                    Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 30


--- ШАГ 13: СВОДКА ПО ЗАКАЗУ 3 ---
StatusCode        : 200
StatusDescription : OK
Content           : {"order_id":3,"status":"new","created_at":"2026-04-21T14:15:15.039766Z","items":[ 
                    {"product_id":1,"quantity":1,"price_at_order":100000},{"product_id":2,"quantity": 
                    2,"price_at_order":50000}],"total":200...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 241
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:15 GMT

                    {"order_id":3,"status":"new","created_at":"2026-04-21T14:15:15.039766Z","items":[ 
                    {"product_...
Forms             :
Headers           : {[Content-Length, 241], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:15:15 GMT]}                                                                   Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 241


--- ШАГ 14: АНАЛИТИКА (СРЕДНИЙ ЧЕК) ---
StatusCode        : 200
StatusDescription : OK
Content           : {"average":250000}

RawContent        : HTTP/1.1 200 OK
                    Content-Length: 19
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:15 GMT

                    {"average":250000}

Forms             :
Headers           : {[Content-Length, 19], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:15:15 GMT]}                                                                    Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 19


--- ШАГ 15: АНАЛИТИКА (ТОП ТОВАРОВ) ---
StatusCode        : 200
StatusDescription : OK
Content           : [{"product_id":1,"total_quantity":6},{"product_id":2,"total_quantity":3}]

RawContent        : HTTP/1.1 200 OK
                    Content-Length: 74
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:15:15 GMT

                    [{"product_id":1,"total_quantity":6},{"product_id":2,"total_quantity":3}]

Forms             :
Headers           : {[Content-Length, 74], [Content-Type, application/json], [Date, Tue, 21 Apr 2026  
                    14:15:15 GMT]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 74

                                                                                                      --- ШАГ 16: ОБНОВЛЕНИЕ ТОВАРА ---                                                                                                                                                                           id    : 1                                                                                             
name  : Laptop Pro
price : 110000
stock : 44


--- ШАГ 17: УДАЛЕНИЕ ПОЗИЦИИ ИЗ ЗАКАЗА 3 ---

Content           : {}
StatusCode        : 204
StatusDescription : No Content
RawContentStream  : Microsoft.PowerShell.Commands.WebResponseContentMemoryStream
RawContentLength  : 0
RawContent        : HTTP/1.1 204 No Content
                    Date: Tue, 21 Apr 2026 14:15:15 GMT


BaseResponse      : System.Net.HttpWebResponse
Headers           : {[Date, Tue, 21 Apr 2026 14:15:15 GMT]}

Остаток после восстановления:

id    : 1
name  : Laptop Pro
price : 110000
stock : 45


--- ШАГ 18: ТЕСТ ОШИБКИ УДАЛЕНИЯ ---

IsMutuallyAuthenticated : False
Cookies                 : {}
Headers                 : {Content-Length, Content-Type, Date}
SupportsHeaders         : True
ContentLength           : 90
ContentEncoding         :
ContentType             : application/json
CharacterSet            :
Server                  :
LastModified            : 21.04.2026 17:15:15
StatusCode              : Conflict
StatusDescription       : Conflict
ProtocolVersion         : 1.1
ResponseUri             : http://localhost:8080/products/2
Method                  : DELETE
IsFromCache             : False