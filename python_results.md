time="2026-04-21T17:14:16+03:00" level=warning msg="C:\\Users\\arina\\OneDrive\\Desktop\\Аида ВКР\\go-python-backend-comparison\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] down 4/4
 ✔ Container python-service                                 Removed                              0.7s 
 ✔ Container postgres_python                                Removed                              0.6s 
 ✔ Network go-python-backend-comparison_default             Removed                              0.3s 
 ✔ Volume go-python-backend-comparison_postgres_python_data Removed                              0.0s 
time="2026-04-21T17:14:17+03:00" level=warning msg="C:\\Users\\arina\\OneDrive\\Desktop\\Аида ВКР\\go-python-backend-comparison\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"                                                      time="2026-04-21T17:14:17+03:00" level=warning msg="No services to build"                             [+] up 4/4                                                                                             ✔ Network go-python-backend-comparison_default             Created                              0.1s 
 ✔ Volume go-python-backend-comparison_postgres_python_data Created                              0.0s 
 ✔ Container postgres_python                                Healthy                              6.1s 
 ✔ Container python-service                                 Created                              0.1s 
Ожидание запуска сервиса.... ГОТОВО!

--- ШАГ 1: ПРОВЕРКА СОСТОЯНИЯ (HEALTH CHECK, PYTHON) ---


StatusCode        : 200
StatusDescription : OK
Content           : {"status":"ok"}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 15
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:25 GMT
                    Server: uvicorn

                    {"status":"ok"}
Forms             :
Headers           : {[Content-Length, 15], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:14:25 GMT], [Server, uvicorn]}                                                 Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 15


--- ШАГ 2: МЕТРИКИ (METRICS, PYTHON) ---
StatusCode        : 200
StatusDescription : OK
Content           : # HELP http_requests_total Total number of HTTP requests
                    # TYPE http_requests_total counter
                    http_requests_total{endpoint="/health",method="GET",status="200"} 2.0
                    # HELP http_requests_created Total num...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 2626
                    Content-Type: text/plain; version=0.0.4; charset=utf-8
                    Date: Tue, 21 Apr 2026 14:14:25 GMT
                    Server: uvicorn

                    # HELP http_requests_total Total number of HTTP r...
Forms             :
Headers           : {[Content-Length, 2626], [Content-Type, text/plain; version=0.0.4; charset=utf-8] 
                    , [Date, Tue, 21 Apr 2026 14:14:25 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 2626


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
                    Content-Length: 107
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn

                    [{"id":2,"name":"Smartphone","price":50000,"stock":100},{"id":1,"name":"La...     
Forms             :
Headers           : {[Content-Length, 107], [Content-Type, application/json], [Date, Tue, 21 Apr 2026 
                     14:14:26 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 107


--- ШАГ 6: СОЗДАНИЕ ЗАКАЗА 1 ---

id         : 1
status     : new
created_at : 2026-04-21T14:14:26.994668Z
items      : {@{product_id=1; quantity=5; price_at_order=100000}}


--- ШАГ 7: ПРОВЕРКА ОСТАТКОВ (ТОВАР 1) ---

id    : 1
name  : Laptop
price : 100000
stock : 45


--- ШАГ 8: СОЗДАНИЕ ЗАКАЗА 2 ---

id         : 2
status     : new
created_at : 2026-04-21T14:14:27.155301Z
items      : {@{product_id=2; quantity=1; price_at_order=50000}}


--- ШАГ 9: ПРОВЕРКА ОСТАТКОВ (ТОВАР 2) ---

id    : 2
name  : Smartphone
price : 50000
stock : 99


--- ШАГ 10: СОЗДАНИЕ ЗАКАЗА 3 ---

id         : 3
status     : new
created_at : 2026-04-21T14:14:27.302739Z
items      : {@{product_id=1; quantity=1; price_at_order=100000}, @{product_id=2; quantity=2; price_a 
             t_order=50000}}


--- ШАГ 11: ФИНАЛЬНЫЕ ОСТАТКИ ---

id    : 1
name  : Laptop
price : 100000
stock : 44                                                                                                                                                                                                                                                                                                        id    : 2                                                                                             
name  : Smartphone
price : 50000
stock : 97


--- ШАГ 12: ИТОГО ПО ЗАКАЗУ 3 ---
StatusCode        : 200
StatusDescription : OK
Content           : {"order_id":3,"total":200000}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 29
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn

                    {"order_id":3,"total":200000}
Forms             :
Headers           : {[Content-Length, 29], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:14:26 GMT], [Server, uvicorn]}                                                 Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 29


--- ШАГ 13: СВОДКА ПО ЗАКАЗУ 3 ---
StatusCode        : 200
StatusDescription : OK
Content           : {"order_id":3,"status":"new","created_at":"2026-04-21T14:14:27.302739Z","items":[ 
                    {"product_id":1,"quantity":1,"price_at_order":100000},{"product_id":2,"quantity": 
                    2,"price_at_order":50000}],"total":200...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 240
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn

                    {"order_id":3,"status":"new","created_at":"2026-04-21T14:14:27.302739Z","i...     
Forms             :
Headers           : {[Content-Length, 240], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:14:26 GMT], [Server, uvicorn]}                                                Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 240


--- ШАГ 14: АНАЛИТИКА (СРЕДНИЙ ЧЕК) ---
StatusCode        : 200
StatusDescription : OK
Content           : {"average":250000.0}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 20
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn

                    {"average":250000.0}
Forms             :
Headers           : {[Content-Length, 20], [Content-Type, application/json], [Date, Tue, 21 Apr 2026                      14:14:26 GMT], [Server, uvicorn]}                                                 Images            : {}                                                                                InputFields       : {}                                                                                
Links             : {}
ParsedHtml        :
RawContentLength  : 20


--- ШАГ 15: АНАЛИТИКА (ТОП ТОВАРОВ) ---
StatusCode        : 200
StatusDescription : OK
Content           : [{"product_id":1,"total_quantity":6},{"product_id":2,"total_quantity":3}]
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 73
                    Content-Type: application/json
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn

                    [{"product_id":1,"total_quantity":6},{"product_id":2,"total_quantity":3}]
Forms             :
Headers           : {[Content-Length, 73], [Content-Type, application/json], [Date, Tue, 21 Apr 2026  
                    14:14:26 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        :
RawContentLength  : 73

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
                    Date: Tue, 21 Apr 2026 14:14:26 GMT
                    Server: uvicorn


BaseResponse      : System.Net.HttpWebResponse
Headers           : {[Date, Tue, 21 Apr 2026 14:14:26 GMT], [Server, uvicorn]}


id    : 1
name  : Laptop Pro
price : 110000
stock : 45


--- ШАГ 18: ТЕСТ ОШИБКИ УДАЛЕНИЯ ---

IsMutuallyAuthenticated : False
Cookies                 : {}
Headers                 : {Content-Length, Content-Type, Date, Server}
SupportsHeaders         : True
ContentLength           : 89
ContentEncoding         :
ContentType             : application/json
CharacterSet            :
Server                  : uvicorn
LastModified            : 21.04.2026 17:14:27
StatusCode              : Conflict
StatusDescription       : Conflict
ProtocolVersion         : 1.1
ResponseUri             : http://localhost:8080/products/2
Method                  : DELETE
IsFromCache             : False