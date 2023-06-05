# Predikcija ishoda mečeva - Riot API

## Uvod

Cilj ove dokumentacije je predstaviti projekt koji koristi Riot Games API za predviđanje rezultata mečeva u igri League of Legends (LoL) na temelju statistike timova. Riot API pruža pristup obilju podataka o igri, omogućujući dubinsku analizu i istraživanje performansi igrača i timova.

Koristeći Random Forest algoritam, cilj nam je identificirati uzorke unutar podataka i razviti prediktivni model koji može prognozirati rezultate mečeva. U ovom izvještaju ćemo raspravljati o procesu izdvajanja podataka iz Riot API-ja, odabiru i prilagodbi podataka i razvoju prediktivnog modela.

## Riot API

### API ključ

API-ji su sučelja koja pomažu u izgradnji softvera i definiraju kako se komponente softvera međusobno interaktiraju. Oni kontroliraju zahtjeve koji se šalju između programa, način na koji se ti zahtjevi šalju te formate podataka koji se koriste.

API ključ je jedinstveni ključ koji omogućuje autorizirani pristup API-u. Služi kao akreditacija, omogućavajući korisnicima interakciju s API-em, dohvat podataka ili izvođenje radnji.

Kako bi pristupili Riot API-u, moramo se prijaviti kako bi dobili API ključ.

![](https://hackmd.io/_uploads/rJFlTz8Ih.png)

Na slici možemo vidjeti ograničenja broja zahtjeva za besplatne korisnike API-a. Ta informacija nam je bitna kako nam Riot API ne bi blokirao pristup informacijama radi slanja previše zahtjeva.

Budući da mi promatramo League of Legends mečeve, koristit ćemo slijedeći API: MATCH-V5 - /lol/match/v5/matches/{matchId}

### matchId

"matchId" je identifikacijska oznaka svakog meča u Riot API. Kako bi smo mogli početi sakupljati podatke o mečevima treba nam početni matchId. Koristeći API SUMMONER-V4 /lol/summoner/v4/summoners/by-name/{summonerName} možemo pronaći informacije o bilo kojem "summoneru" ("summoner name" je korisnička oznaka koja se vidi u igri). Informacija koja nam treba je "PUUID", odnosno jedinstvena oznaka igrača. "Summoner name" i "Summoner ID" su jedinstveni samo na serveru, a "PUUID" je jedinstven globalno.

![](https://hackmd.io/_uploads/HyuT-QLU2.png)


Koristeći MATCHES-V5- /lol/match/v5/matches/by-puuid/{puuid}/idsGet možemo konačno dohvatiti početni matchId.

![](https://hackmd.io/_uploads/rJIdfQ8Uh.png)

Nama je potreban samo jedan matchId. Po strukturi matchId-a možemo vidjeti da se sastoji od servera i broja. Držat ćemo se EUN1 servera, a brojeve ćemo obilatizi redom, "bruteforce" metodom. U našem slučaju to je najjednostavniji način jer rezultira s puno jednostavnijim kodom. Otprilike 50% prikupljenih matchId-jeva ovim načinom je iskoristivo za našu svrhu predviđanja rezultata.

## Prikupljanje podataka

Naše prikupljene podatke pohranjujemo u MongoDB bazu podatka. Da bismo pokrenuli mongo server u cmd upisujemo naredbu:
```
mongod
```

U config.py pohranili smo neke osnovne informacije koje nam trebaju kao što su ime baze podataka i vrijednost API ključa:

```python
config = {
    'include_timeline': False, #nije nam bitna minuta igre kada je podatak zabilježen
    'api_key': 'RGAPI-a6cd2efd-fc71-45bf-afdf-6f54c19b729e',
    'is_production_key': False,
    'mongodb': {
        'host': 'localhost',
        'port': 27017,
        'db': 'lol'
    }
}
```

Sada se možemo povezati s Mongodb bazom podataka:

```python
api_key = config['api_key']
mongodb_host = config['mongodb']['host']
mongodb_port = config['mongodb']['port']
mongodb_db = config['mongodb']['db']

region = 'europe'

# spajanje s mongodb
client = MongoClient(mongodb_host, mongodb_port)
db = client[mongodb_db]
matches_collection = db["lol"]
```

Idući korak je definiranje funkcije koja dohvaća podatke s API-a:

```python
def get_match_data(match_id):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    match_data = response.json()
    return match_data
```
Zatim radimo rekurzivnu funkciju koja prima početnu vrijednost, pa s tom vrijednošću poziva prethodnu funkciju, a zatim samu sebe, ali s početnom vrijednosti podignutom za 1:

```python
def gather_match_data(match_id):
        match_data = get_match_data(match_id)
        if match_data:
            matches_collection.insert_one(match_data)
            print(f"Match with ID {match_id} fetched and saved.")
            # Wait for 1.5 seconds
            time.sleep(1.5)
            # Run gather_match_data for the new match ID
            gather_match_data(increment_match_id(match_id))
        else:
            print(f"Failed to fetch match with ID {match_id}. Skipping...")
```

Funkcija koja mijenja početnu vrijednost rekurzivne funkcije svaki put kad se pozove je increment_match_id, koja rastavi string na string i broj, zatim broj poveča za 1, pa ponovo sastavi nazad u string:

```python
def increment_match_id(match_id):
    prefix, number = match_id.split("_")
    number = int(number)
    number += 1
    return f"{prefix}_{number}"
```

Sve što nam je preostalo je postaviti početnu vrijesnot, odnosno prvi matchId i pozvati funkciju:

```python
start_match_id = "EUN1_3377732531"


gather_match_data(start_match_id)
```
Cijeli kod:

```python
import requests
from pymongo import MongoClient
from config import config
import sys
import time

sys.setrecursionlimit(100000)

api_key = config['api_key']
mongodb_host = config['mongodb']['host']
mongodb_port = config['mongodb']['port']
mongodb_db = config['mongodb']['db']

region = 'europe'

# spajanje s mongodb
client = MongoClient(mongodb_host, mongodb_port)
db = client[mongodb_db]
matches_collection = db["lol"]

# dohvacanje podataka pomocu matchId
def get_match_data(match_id):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    match_data = response.json()
    return match_data

# rekurzivna funkcija za pozivanje get_match_data
def gather_match_data(match_id):
        match_data = get_match_data(match_id)
        if match_data:
            matches_collection.insert_one(match_data)
            print(f"Match with ID {match_id} fetched and saved.")
            # Wait for 1.5 seconds
            time.sleep(1.5)
            # Run gather_match_data for the new match ID
            gather_match_data(increment_match_id(match_id))
        else:
            print(f"Failed to fetch match with ID {match_id}. Skipping...")

#bruteforce mijenjanje matchid-a
def increment_match_id(match_id):
    prefix, number = match_id.split("_")
    number = int(number)
    number += 1
    return f"{prefix}_{number}"

start_match_id = "EUN1_3377732531"


gather_match_data(start_match_id)

```
## Prikupljeni podaci

Na prikupljenim podacima još ne možemo raditi nikakve predikcije, prvo ih moramo urediti. Koristeći MongoDB Compass možemo vidjeti kakve podatke imamo.

![](https://hackmd.io/_uploads/H1SonQU8n.png)

Možemo vidjeti da imamo preko 11 tisuća mečeva, a svaki meč ima preko 2000 podataka, odnosno oko 200 podataka po igraču, a igrača je 10 i još nešto podataka o svakom timu, a radi se o 2 tima. Nama nije potrebno 200 podataka o svakom igraču pa ćemo odabrati one za koje mislimo da imaju utjecaja na pobjedu ili poraz. Na slici možemo vidjeti isječak kako izgleda isječak .json dokumenta za jedan meč u ovom koraku procesa.

![](https://hackmd.io/_uploads/Byp-C7U8n.png)

Radi toga moramo izraditi pipeline koji filtrira i odabire podatke koje želimo:

```python
pipeline = [
    {
        "$match": {
            "info.mapId": 11,
            "info.gameMode":"CLASSIC",
            "info.gameType": "MATCHED_GAME"            
        }
    },
    {
        "$project": {
            "_id": 1,
            "info.gameDuration": 1,
            "info.participants.allInPings": 1,
            "info.participants.assists": 1,
            "info.participants.champExperience": 1,
            "info.participants.goldEarned": 1,
            "info.participants.firstBloodKill": 1,
            "info.participants.visionScore": 1,
            "info.participants.visionWardsBoughtInGame": 1,
            "info.participants.kills": 1,
            "info.participants.deaths": 1,
            "info.participants.assists": 1,
            "info.participants.win": 1,
            "info.teams.objectives": 1,
            "info.teams.teamId": 1,
            "info.teams.win": 1
        }
    }
]
```

Odabrali smo 15 podataka za koje znamo da utječu na igru i svi su podaci numerički (ili Boolean) što će nam biti važno u idućem koraku. Također smo filtirali mečeve da odabiremo samo one koji su igrani na 5v5 mapi i koji su "MATCHED_GAME", odnosno protivnici i (neki) suigrači su nasumični. Cijeli kod za spremanje rezultata u novu kolekciju:

```python
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
s
source_db = client["lol"]
destination_db = client["lol"]
source_collection = source_db["lol"]
destination_collection = destination_db["matches"]

pipeline = [
    {
        "$match": {
            "info.mapId": 11, #mapa 5v5
            "info.gameMode":"CLASSIC",
            "info.gameType": "MATCHED_GAME"            
        }
    },
    {
        "$project": {
            "_id": 1,
            "info.gameDuration": 1,
            "info.participants.allInPings": 1,
            "info.participants.assists": 1,
            "info.participants.champExperience": 1,
            "info.participants.goldEarned": 1,
            "info.participants.firstBloodKill": 1,
            "info.participants.visionScore": 1,
            "info.participants.visionWardsBoughtInGame": 1,
            "info.participants.kills": 1,
            "info.participants.deaths": 1,
            "info.participants.assists": 1,
            "info.participants.win": 1,
            "info.teams.objectives": 1,
            "info.teams.teamId": 1,
            "info.teams.win": 1
        }
    }
]

transformed_data = list(source_collection.aggregate(pipeline))
destination_collection.insert_many(transformed_data)

print(destination_collection.count_documents({}))

```
Nova kolekcija nam se zove matches i prikaz iz Mongodb Compassa možemo vidjeti na slici.

![](https://hackmd.io/_uploads/rkM-gV88n.png)

Također, na slici vidimo da nam se broj dokumenata smanjio na 9.6 tisuća. Razlika je vidljiva i u .json datoteci jednog meča:

![](https://hackmd.io/_uploads/rk1ufN8Lh.png)


Na slici vidimo kako nam se isti podaci ponavljaju za više igrača. Također nisu svi podaci na istoj "dubini" u dokumentu. To je problem kojem ćemo se postvetiti u idućem koraku.

## Transformacija podataka

Cilj sakupljanja ovih podataka je da treniramo model za predikciju meča. Budući da mi, po zadanim podacima, želimo predvidjeti hoće li tim pobjediti ili ne, ne trebaju nam statistike svakog igrača posebno. Zato ćemo sve podatke iz istog tima zbrojiti, a svaki dokument ćemo razdvojiti na dva dokumenta- po jedan za svaki tim. Da bismo postigli to, nadogradit ćemo stari pipeline, te sada izgleda ovako:

```python
pipeline = [
    {
        "$match": {
            "info.mapId": 11, #mapa 5v5
            "info.gameMode":"CLASSIC",
            "info.gameType": "MATCHED_GAME"            
        }
    },
    {
        '$unwind': '$info.participants'
    },
    {
        '$group': {
            '_id': {
                'matchId': '$metadata.matchId',
                'win': '$info.participants.win'
            },
            'allInPings': {'$sum': '$info.participants.allInPings'},
            'assists': {'$sum': '$info.participants.assists'},
            'champExperience': {'$sum': '$info.participants.champExperience'},
            'deaths': {'$sum': '$info.participants.deaths'},
            'goldEarned': {'$sum': '$info.participants.goldEarned'},
            'kills': {'$sum': '$info.participants.kills'},
            'visionScore': {'$sum': '$info.participants.visionScore'},
            'visionWardsBoughtInGame': {'$sum': '$info.participants.visionWardsBoughtInGame'}

        }
    },
    {
        '$project': {
            '_id': 0,
            'matchId': '$_id.matchId',
            'win': '$_id.win',
            'allInPings': 1,
            'assists': 1,
            'champExperience': 1,
            'deaths': 1,
            'goldEarned': 1,
            'kills': 1,
            'visionScore': 1,
            'visionWardsBoughtInGame': 1

        }
    }
]
```
Također smo i napravili dodatnu selekciju varijabli koje ćemo uključiti.

Budući da smo svaku datoteku razdvojili na dvije, a podatke smo pojednostavili, sada imamo 19.1 tisuća datoteka i puno su čitljivije. 

Na slici možemo vidjeti da smo pretražili meč po matchId-u i dobili smo dva rezultata.

![](https://hackmd.io/_uploads/SkBOLNLU2.png)

## Treniranje modela - Random Forest algoritam

Algoritam Slučajne šume pokušava riješiti problem modela jednog stabla
izgradnjom više stabala na skupu za treniranje. Upotrebom nešto različitijih podataka za izgradnju svakog stabla dodaje različitost modelima.

Uprosječenjem rezultata više stabala smanjuje se rizik od overfittinga.

Treniranje modela odrađeno je u Google Colab-u.
Prvo unesemo podatke:
```python
drive.mount('/content/drive')


with open('/content/drive/MyDrive/teamSum.json', 'r') as file:
    data = json.load(file)


df = pd.DataFrame(data)

X = df.drop('win', axis=1) 
X = X.drop('_id', axis=1)  
X = X.drop('matchId', axis=1) 

y = df['win'] 
```
Iz X smo izbacili 'win', zato što je to podatak koji želimo predvijeti i '_id' i 'matchId' zato što ti podaci ne služe za predviđanje.

Možemo vidjeti kako podaci trenutno izgledaju:
![](https://hackmd.io/_uploads/H1AJjVLL3.png)

Zatim radimo random forest klasifikator 
```python

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf_classifier = RandomForestClassifier(n_estimators=100)

rf_classifier.fit(X_train, y_train)

y_pred = rf_classifier.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print("Accuracy:", accuracy)
```
Dobivena preciznost je 92%:
![](https://hackmd.io/_uploads/HkM6j48Uh.png)


Na slici možemo vidjeti matricu konfuzije:
![](https://hackmd.io/_uploads/HkybnNLL2.png)


![](https://hackmd.io/_uploads/Hy5qnNILh.png)

# Zaključak

U ovom seminaru smo predstavili projekt koji koristi Riot Games API za predviđanje rezultata mečeva u igri League of Legends (LoL) na temelju statistike timova. Korištenjem Random Forest algoritma, razvijen je prediktivni model koji identificira uzorke u podacima i može prognozirati rezultate mečeva.

Za pristup Riot API-u koristili smo jedinstveni API ključ koji omogućuje autorizirani pristup. Kroz postupak prikupljanja podataka, koristili smo matchId kao identifikacijsku oznaku za svaki meč. Prikupljeni podaci su pohranjeni u MongoDB bazu podataka.

Nakon prikupljanja podataka, koristili smo pipeline za filtriranje, odabir i transformaciju samo relevantnih podataka za predviđanje rezultata. Odabrali smo 8 numeričkih (ili Boolean) podataka koji utječu na ishod igre.

Na kraju, rezultirajući podaci su prikazani u novoj kolekciji MongoDB baze. Ovaj skraćeni postupak omogućio nam je rad s manjim skupom podataka koji su relevantni za predviđanje rezultata mečeva.

Kroz ovaj projekt smo pokazali kako se Riot API može koristiti za predviđanje rezultata mečeva u igri League of Legends. Daljnji rad na projektu može uključivati optimizaciju modela i uključivanje vremenskih podataka tako da se predviđanje može odvijati za vrijeme trajanja meča.
