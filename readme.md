1 /geonames/api/get_by_geonameid

Принимает идентификатор geonameid и возвращает информацию о городе 

Параметр    Тип данных

geonameid   integer

Пример запроса - /geonames/api/get_by_geonameid?geonameid=451747




2 /geonames/api/get_page

Принимает страницу и количество отображаемых на странице городов и 
возвращает список городов с их информацией

Параметр    Тип данных

page        integer

on_page     integer

page - номер страницы 
on_page - количество отображаемых на странице городов

Пример запроса /geonames/api/get_page?page=1&on_page=100




3 /geonames/api/city_compare

Принимает названия двух городов (на русском языке), сравнивает их и 
возвращает информацию о результате сравнения: 
какой из них расположен севернее и одинаковая ли у них временная зона

Параметр    Тип данных

geoname1    string

geoname2    string

Пример запроса - /geonames/api/city_compare?geoname1=Москва&geoname2=Томск

Ответ содержит поле northern - более северный город и 
поле timezone - которое принимает значение False если города в разных временных зонах и True в обратном случае




4 /geonames/api/get_prompts

Принимает начало названия города, возвращает список возможных продолжений

Параметр    Тип данных

beginning    string

Пример запроса - /geonames/api/get_prompts?beginning=Toms
