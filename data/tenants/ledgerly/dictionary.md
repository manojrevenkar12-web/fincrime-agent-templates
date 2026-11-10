# Ledgerly export

One record per business customer, with its people under `parties`.
Ledgerly's onboarding runs on its US parent's stack.

| field | meaning |
|---|---|
| entity_id | screening id |
| legal_name | registered name |
| reg_no | registration number |
| country | country of registration, ISO alpha-2 |
| parties[].role | director or ubo |
| parties[].full_name | GIVEN SURNAME, upper case |
| parties[].dob | MM/DD/YYYY |
| parties[].country_of_birth | English country name |
| parties[].city_of_birth | city |
| parties[].nationality | ISO alpha-2 |
