"""Name pools by naming culture, with the spelling variants that make screening hard.

Each canonical name part maps to its variants: transliterations (Muhammad, Mohammed, Mohamed), German
transcriptions of Cyrillic (Kusnezow), dropped diacritics (Yilmaz), umlaut spellings (Mueller). A list
entry and a customer can be the same person under different spellings, and different people under the
same one.
"""

from __future__ import annotations

CULTURES: dict[str, dict] = {
    "arabic": {
        "countries": ["SY", "IQ", "LB", "AE", "EG", "JO"],
        "cities": {"SY": ["Damascus", "Aleppo", "Homs"], "IQ": ["Baghdad", "Basra", "Mosul"],
                   "LB": ["Beirut", "Tripoli", "Sidon"], "AE": ["Dubai", "Sharjah", "Abu Dhabi"],
                   "EG": ["Cairo", "Alexandria", "Giza"], "JO": ["Amman", "Zarqa", "Irbid"]},
        "given_m": {"Mohammed": ["Muhammad", "Mohamed", "Mohammad"], "Ahmed": ["Ahmad"], "Hassan": ["Hasan"],
                    "Hussein": ["Husain", "Hussain"], "Omar": ["Umar"], "Abdullah": ["Abdallah"],
                    "Yusuf": ["Youssef", "Yousef"], "Ali": [], "Khalid": ["Khaled"], "Karim": ["Kareem"],
                    "Samir": ["Sameer"], "Tariq": ["Tarek"]},
        "given_f": {"Fatima": ["Fatma", "Fatimah"], "Aisha": ["Aysha", "Aischa"], "Layla": ["Leila", "Laila"],
                    "Mariam": ["Maryam"], "Nour": ["Noor", "Nur"]},
        "surnames": {"Al-Hassan": ["Al Hassan", "Alhassan"], "Haddad": [], "Khoury": ["Khouri", "Khuri"],
                     "Nasser": ["Nasir", "Naser"], "Saleh": ["Salih"], "Mansour": ["Mansur"], "Abbas": [],
                     "Hamdan": [], "Darwish": ["Darwich"], "Barakat": [], "Rahman": ["Rahmen"],
                     "Al-Masri": ["Al Masri", "Elmasry"]},
    },
    "slavic": {
        "countries": ["RU", "UA", "BY", "KZ"],
        "cities": {"RU": ["Moscow", "Saint Petersburg", "Kazan"], "UA": ["Kyiv", "Odesa", "Kharkiv"],
                   "BY": ["Minsk", "Brest", "Gomel"], "KZ": ["Almaty", "Astana", "Karaganda"]},
        "given_m": {"Aleksandr": ["Alexander", "Oleksandr", "Aleksander"], "Sergei": ["Sergey", "Serhiy"],
                    "Dmitri": ["Dmitry", "Dmytro"], "Mikhail": ["Mykhailo", "Michail"],
                    "Vladimir": ["Volodymyr", "Wladimir"], "Yuri": ["Yury", "Yuriy", "Juri"],
                    "Andrei": ["Andrey", "Andriy"], "Nikolai": ["Nikolay", "Mykola"], "Igor": ["Ihor"],
                    "Pavel": ["Pawel", "Pavlo"]},
        "given_f": {"Olga": ["Olha"], "Tatiana": ["Tatyana", "Tetiana"], "Elena": ["Yelena", "Olena"],
                    "Natalia": ["Natalya", "Nataliya"], "Irina": ["Iryna"]},
        "surnames": {"Ivanov": ["Iwanow"], "Petrov": ["Petrow"], "Kuznetsov": ["Kusnezow", "Kuznetsow"],
                     "Sokolov": ["Sokolow"], "Volkov": ["Wolkow"], "Morozov": ["Morosow"],
                     "Novikov": ["Nowikow"], "Fedorov": ["Fyodorov", "Fjodorow"], "Pavlenko": [],
                     "Shevchenko": ["Schewtschenko", "Sevcenko"], "Kovalenko": ["Kowalenko"], "Bondarenko": []},
        "feminine_suffix": True,
    },
    "german": {
        "countries": ["DE", "AT", "CH"],
        "cities": {"DE": ["Berlin", "Hamburg", "Munich", "Cologne", "Leipzig"], "AT": ["Vienna", "Graz"],
                   "CH": ["Zurich", "Basel"]},
        "given_m": {"Thomas": [], "Andreas": [], "Michael": [], "Stefan": ["Stephan"], "Christian": [],
                    "Markus": ["Marcus"], "Jan": [], "Lukas": ["Lucas"]},
        "given_f": {"Sabine": [], "Katrin": ["Kathrin", "Catrin"], "Julia": [], "Anna": [], "Petra": []},
        "surnames": {"Müller": ["Mueller", "Muller"], "Schmidt": ["Schmitt", "Schmid"], "Schneider": [],
                     "Fischer": [], "Weber": [], "Meyer": ["Meier", "Maier", "Mayer"], "Wagner": [],
                     "Becker": [], "Schulz": ["Schultz"], "Hoffmann": ["Hofmann"], "Krüger": ["Krueger"]},
    },
    "romanian": {
        "countries": ["RO", "MD"],
        "cities": {"RO": ["Bucharest", "Cluj-Napoca", "Iasi", "Timisoara"], "MD": ["Chisinau"]},
        "given_m": {"Andrei": [], "Mihai": [], "Ion": ["Ioan"], "Gheorghe": ["George"], "Vasile": []},
        "given_f": {"Elena": [], "Ioana": [], "Maria": [], "Andreea": ["Andrea"]},
        "surnames": {"Popescu": [], "Ionescu": [], "Popa": [], "Stan": [], "Dumitrescu": [], "Constantin": []},
    },
    "turkish": {
        "countries": ["TR"],
        "cities": {"TR": ["Istanbul", "Ankara", "Izmir", "Bursa"]},
        "given_m": {"Mehmet": ["Mehmed"], "Mustafa": [], "Ahmet": [], "Emre": [], "Hüseyin": ["Huseyin"]},
        "given_f": {"Ayşe": ["Ayse"], "Fatma": [], "Elif": [], "Zeynep": []},
        "surnames": {"Yılmaz": ["Yilmaz"], "Kaya": [], "Demir": [], "Şahin": ["Sahin"], "Çelik": ["Celik"],
                     "Öztürk": ["Ozturk", "Oeztuerk"]},
    },
    "spanish": {
        "countries": ["ES", "MX", "VE", "CO"],
        "cities": {"ES": ["Madrid", "Barcelona"], "MX": ["Mexico City", "Monterrey"], "VE": ["Caracas"],
                   "CO": ["Bogota", "Medellin"]},
        "given_m": {"José": ["Jose"], "Juan": [], "Carlos": [], "Luis": [], "Miguel": []},
        "given_f": {"María": ["Maria"], "Carmen": [], "Lucía": ["Lucia"]},
        "surnames": {"García": ["Garcia"], "Rodríguez": ["Rodriguez"], "Martínez": ["Martinez"],
                     "López": ["Lopez"], "González": ["Gonzalez"], "Hernández": ["Hernandez"]},
    },
}

COMPANY_WORDS = ["Aurora", "Baltic", "Crescent", "Delta", "Eastern", "Falcon", "Golden", "Horizon", "Iron",
                 "Jade", "Kestrel", "Lotus", "Meridian", "Northern", "Orion", "Pacific", "Royal", "Silk Road",
                 "Titan", "Unity", "Vertex", "Westbridge", "Amber", "Cedar", "Harbor", "Summit", "Polar",
                 "Granite", "Sapphire", "Monarch"]
COMPANY_KINDS = {"Trading": ["Trading", "Trade"], "Shipping": ["Shipping", "Maritime"],
                 "Holding": ["Holding", "Holdings"], "Import Export": ["Import Export", "Imp. Exp."],
                 "Logistics": ["Logistics", "Logistik"], "Petroleum": ["Petroleum", "Oil"],
                 "Consulting": ["Consulting", "Consultancy"], "Metals": ["Metals", "Steel"]}
LEGAL_FORMS = {"AE": ["LLC", "FZE"], "RU": ["OOO", "LLC"], "DE": ["GmbH", "UG"], "UK": ["Ltd", "Limited"],
               "CY": ["Ltd", "Limited"], "TR": ["A.S.", "Ltd. Sti."], "RO": ["SRL"], "ES": ["S.L."],
               "LB": ["SAL"], "SY": ["LLC"]}
LEGAL_VARIANTS = {"LLC": ["L.L.C."], "Ltd": ["Limited"], "Limited": ["Ltd"], "GmbH": ["G.m.b.H."], "FZE": ["F.Z.E."]}

OCCUPATIONS = ["engineer", "teacher", "nurse", "software developer", "shop owner", "taxi driver", "accountant",
               "architect", "student", "chef", "pharmacist", "logistics manager", "consultant", "electrician",
               "real-estate agent", "car dealer", "importer", "shipping agent"]
GERMAN_CITIES = ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Leipzig", "Dresden",
                 "Hanover", "Nuremberg"]
UK_CITIES = ["London", "Manchester", "Birmingham", "Leeds", "Bristol"]


# More surnames without listed variants, so that a name is not a near-certain collision.
EXTRA_SURNAMES = {'arabic': ['Qasim', 'Hijazi', 'Jaber', 'Khalil', 'Najjar', 'Sabbagh', 'Tamimi', 'Zaher', 'Farouk', 'Ghanem', 'Hamoud', 'Issa', 'Jarrah', 'Kanaan', 'Laham', 'Maalouf', 'Nassif', 'Obeid', 'Qassem', 'Rizk', 'Shami', 'Tawil', 'Yassin', 'Zein', 'Bitar', 'Chami', 'Dabbagh', 'Fakhoury'], 'slavic': ['Lebedev', 'Kozlov', 'Stepanov', 'Orlov', 'Makarov', 'Zaitsev', 'Belov', 'Gusev', 'Titov', 'Kuzmin', 'Romanov', 'Vasiliev', 'Zhukov', 'Frolov', 'Melnyk', 'Tkachenko', 'Kravchenko', 'Oliynyk', 'Polishchuk', 'Lysenko', 'Marchenko', 'Rudenko', 'Savchenko', 'Klimenko', 'Yakovlev', 'Grigoriev', 'Nikitin', 'Sorokin'], 'german': ['Schäfer', 'Koch', 'Richter', 'Klein', 'Wolf', 'Neumann', 'Schwarz', 'Zimmermann', 'Braun', 'Hartmann', 'Lange', 'Werner', 'Krause', 'Lehmann', 'Köhler', 'Herrmann', 'Walter', 'König', 'Mayr', 'Kaiser', 'Fuchs', 'Peters', 'Lang', 'Scholz', 'Jung', 'Möller', 'Keller', 'Vogel'], 'romanian': ['Stoica', 'Gheorghiu', 'Rusu', 'Munteanu', 'Matei', 'Ciobanu', 'Lungu', 'Marin', 'Tudor', 'Moldovan', 'Barbu', 'Nistor', 'Florea', 'Sandu', 'Ilie', 'Dinu', 'Neagu', 'Radu', 'Cristea', 'Toma'], 'turkish': ['Aydın', 'Arslan', 'Doğan', 'Kılıç', 'Aslan', 'Çetin', 'Kara', 'Koç', 'Kurt', 'Özdemir', 'Şimşek', 'Polat', 'Erdoğan', 'Güneş', 'Aktaş', 'Yıldız', 'Bulut', 'Tekin', 'Acar', 'Keskin'], 'spanish': ['Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Cruz', 'Morales', 'Reyes', 'Gutiérrez', 'Ortiz', 'Jiménez', 'Ruiz', 'Vargas', 'Castillo', 'Romero', 'Herrera', 'Medina']}
for _c, _names in EXTRA_SURNAMES.items():
    for _n in _names:
        CULTURES[_c]["surnames"].setdefault(_n, [])

EXTRA_GIVEN = {'arabic': (['Bilal', 'Faisal', 'Hamza', 'Ibrahim', 'Jamal', 'Majid', 'Nabil', 'Rami', 'Saeed', 'Walid', 'Ziad', 'Adnan', 'Bassam', 'Fadi', 'Ghassan', 'Hadi'], ['Amina', 'Dalia', 'Hiba', 'Huda', 'Jana', 'Lina', 'Mona', 'Rania', 'Salma', 'Yasmin', 'Zainab', 'Rana']), 'slavic': (['Boris', 'Denis', 'Evgeny', 'Gennady', 'Konstantin', 'Leonid', 'Maxim', 'Oleg', 'Roman', 'Stanislav', 'Timur', 'Vadim', 'Viktor', 'Anton', 'Artem', 'Kirill'], ['Anastasia', 'Daria', 'Ekaterina', 'Galina', 'Ksenia', 'Larisa', 'Ludmila', 'Marina', 'Svetlana', 'Valentina', 'Yulia', 'Vera']), 'german': (['Florian', 'Matthias', 'Tobias', 'Sebastian', 'Daniel', 'Martin', 'Frank', 'Uwe', 'Jürgen', 'Dirk', 'Holger', 'Kai', 'Moritz', 'Felix', 'Jonas', 'Tim'], ['Claudia', 'Monika', 'Susanne', 'Nicole', 'Stefanie', 'Birgit', 'Jana', 'Lena', 'Laura', 'Sarah', 'Miriam', 'Ute']), 'romanian': (['Adrian', 'Bogdan', 'Cristian', 'Dan', 'Florin', 'Gabriel', 'Marius', 'Radu', 'Sorin', 'Valentin', 'Ovidiu', 'Lucian'], ['Alina', 'Cristina', 'Daniela', 'Gabriela', 'Mihaela', 'Raluca', 'Simona', 'Diana', 'Oana', 'Irina']), 'turkish': (['Ali', 'Burak', 'Can', 'Deniz', 'Emir', 'Hakan', 'Kemal', 'Murat', 'Oğuz', 'Serkan', 'Tolga', 'Volkan', 'Yusuf', 'Cem'], ['Aylin', 'Buse', 'Derya', 'Ebru', 'Gül', 'Hande', 'Melis', 'Selin', 'Tuba', 'Yasemin', 'Esra', 'Pınar']), 'spanish': (['Alejandro', 'Andrés', 'Diego', 'Fernando', 'Javier', 'Manuel', 'Pablo', 'Rafael', 'Sergio', 'Tomás', 'Raúl', 'Óscar'], ['Ana', 'Beatriz', 'Claudia', 'Elena', 'Isabel', 'Laura', 'Marta', 'Paula', 'Rosa', 'Sofía', 'Teresa', 'Pilar'])}
for _c, (_m, _f) in EXTRA_GIVEN.items():
    for _n in _m:
        CULTURES[_c]["given_m"].setdefault(_n, [])
    for _n in _f:
        CULTURES[_c]["given_f"].setdefault(_n, [])
