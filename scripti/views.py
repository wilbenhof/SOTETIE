from django.http import HttpResponse
import requests
import json
import sys
import re
import string
import pymongo
from django.shortcuts import render
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn.metrics import recall_score, precision_score, f1_score

from bson.json_util import dumps
from io import StringIO

from celery import Celery
from celery.schedules import crontab

# ajastusominaisuus, haetaan kurssitiedot joka maanantai klo 2.30
app = Celery()
app.conf.timezone = 'UTC+2'

def ajastus(home):
    sender.add_periodic_task(
        crontab(minute=30, hour=2, day_of_week=1),
        home()
    )

def home(request):
    print("Fetching classified courses");

    classifiedcourses = getCourses();

    print("Fetching done");
    
    return render(
        request,
        'FrontEnd/display.html',
        {
            'response':classifiedcourses

        }
    )


def getCourses():
    headers_id = {'Caller-id': '123'}; # opintopolun headers
    rows = str(10000); # tuotantovaiheen hakumääräsäädin
    search_list = [
                "https://opintopolku.fi/lo/search?start=0&rows="+rows+"&lang=fi&searchType=LO&text=*&facetFilters=teachingLangCode_ffm:EN&facetFilters=educationType_ffm:et01.05&facetFilters=theme_ffm:teemat_12",
                "https://opintopolku.fi/lo/search?start=0&rows="+rows+"&lang=fi&searchType=LO&text=*&facetFilters=teachingLangCode_ffm:EN&facetFilters=educationType_ffm:et01.04&facetFilters=theme_ffm:teemat_12",
                "https://opintopolku.fi/lo/search?start=0&rows="+rows+"&lang=fi&searchType=LO&text=*&facetFilters=teachingLangCode_ffm:FI&facetFilters=educationType_ffm:et01.05&facetFilters=theme_ffm:teemat_12",
                "https://opintopolku.fi/lo/search?start=0&rows="+rows+"&lang=fi&searchType=LO&text=*&facetFilters=teachingLangCode_ffm:FI&facetFilters=educationType_ffm:et01.04&facetFilters=theme_ffm:teemat_12"
                ];
   
    #[0] - englanninkielinen yliopistokoulutus terveysalalta
    #[1] - englanninkielinen amk koulutus terveysalalta
    #[2] - suomenkielinen yliopistokoulutus terveysalalta
    #[3] - suomenkielinen yliopistokoulutus terveysalalta

    course_amount = 0; #Kurssimäärä printCourseAmount() varten
    classifiedcourses = []; #lista suodatetuille kursseille
    
    knowledges = [
                "Asiakaslähtöisyys",
                "Ohjaus- ja neuvontaosaaminen",
                "Palvelujärjestelmät",
                "Lainsäädännön ja etiikan tuntemus",
                "Tutkimus- ja kehittämisosaaminen",
                "Robotiikka ja digitalisaatio",
                "Vaikuttavuus-, kustannus- ja laatutietoisuus",
                "Kestävän kehityksen osaaminen",
                "Viestintäosaaminen",
                "Työntekijyysosaaminen",
                "Monialainen yhteistoiminta",
                "Muu"
                ];
    
    classes = createKnowledges(); #luodaan osaamisiin kuuluvat avainsanat
    
    createTrainingDataset(headers_id,classes,knowledges,"NaiveBayesCourses"); #Oppimisainiston lista mongoon

    classifiermodel, vectorizer = createClassifierModel(); #Luodaan oppimismalli
    
    for search in search_list: #tehdään rajaavat kurssihaut tietokantaan
        try:
            response = requests.get(search,headers=headers_id);
            data = response.json();
            json_str = json.dumps(data);
            resp = json.loads(json_str);
            respond = resp['results']; # Muunnetaan data käsiteltävään muotoon
        
            course_amount = course_amount + len(respond); # tarkastusarvo kaikille kursseille jos ne printataan konsolissa (printCourseAmount)
        except:
            print("Exception in search: "+search);
            continue;

        for result in respond: #Tehdään jokaisen haun kurssille luokittelu
            classify(result,classes,classifiedcourses,knowledges,classifiermodel,vectorizer); # luokittelu
    
    printCourseAmount(classifiedcourses,knowledges,course_amount); #tulostetaan kurssien luokat
    
    sendtoMongo(classifiedcourses,"kurssit");
    #Luokiteltujen kurssien siirto tietokantaan
    return classifiedcourses;
    
 
def sendtoMongo(classifiedcourses,database):
    
    # [0] - kurssin id - lista[string]
    # [1] - kurssinimi - string
    # [2] - kurssikuvaus - string
    # [3] - kurssitavoitteet - string
    # [4] - kurssin tarjoajat[] - lista[string]
    # [5] - tarjoajien kaupungit - lista[string]
    # [6] - maksullisuus - lista[int]
    # [7] - opintopisteet - lista[int] 
    # [8] - geneerinen osaaminen - lista[string]
    # [9] - opetuskielet - lista[string]

    server = "mongodb+srv://rmuser:hakutyokalu123@cluster0.mtzby.mongodb.net/myFirstDatabase?retryWrites=true&w=majority" #Mongodb osoite
    server_client = "testaillaan"; #Mongodb projekti
    server_db = database; #Mongodb kurssihaun tietokanta
    backup_db = "backup"; # backup tietokanta

    client = pymongo.MongoClient(server); 
    db = client[server_client];
    
    kurssit = db[server_db];
    
    if (database == "kurssit"): #Tehdään vain viikottaisessa kurssisiirrossa

        pipeline =  [ {"$match": {}}, # siirto päätietokannasta varatietokantaan ennen poistoa
                    {"$out": backup_db},
                ]

        db.kurssit.aggregate(pipeline) #siirto
    
        kurssit.remove({}); #päätietokannan tyhjennys ennen kurssien ajoa

        for course in classifiedcourses: #kurssiajo tietokantaan, kaikki ei luokitellut kurssit jätetään pois
            if (course[8][0] != "Muu"):
            
                kurssi = {  "kurssinimi": course[1],
                            "kurssiId": course[0],
                            "kurssikuvaus": course[2],
                            "kurssitavoiteet": course[3],
                            "kurssintarjoajat": course[4],
                            "kaupungit": course[5],
                            "maksullisuus": course[6],
                            "opintopisteet": course[7],
                            "osaaminen": course[8],
                            "opetuskielet": course[9]
                        }
                x = kurssit.insert_one(kurssi)
            else:
                continue;
        return;

    if (database == "NaiveBayesCourses"): #Kurssiajo tietokantaan jos kyseessä on oppimismallin aineiston luonti
        kurssit.remove({});

        for course in classifiedcourses:
            kurssi = {
                        "kurssiId": course[0],
                        "osaaminen": course[1],
                        "osaamisId": course[2],
                        "kurssikuvaus": course[3],
                        
                    }
            x = kurssit.insert_one(kurssi)
        


#---------------------------------------------------------------
# printCourseAmount on funktio jolla listataan eri kurssimäärät nopeasti ennen mongoon lähettämistä
#---------------------------------------------------------------

def printCourseAmount(classifiedcourses, knowledges,course_amount):

    knowledge_amount = [];

    for a in knowledges:
        knowledge_amount.append(0);
        # luodaan lista osaamisten muuttujamääristä
    
    for course in classifiedcourses:
        i = 0;
        for knowledge in knowledges:

            for course_knowledge in course[8]:
                if (course_knowledge is knowledge):
                    knowledge_amount[i] = knowledge_amount[i]+len(course[0]);
                    #otetaan laskuun kurssin id[0] listan pituus jolloin saadaan myös muut kurssit
            i = i+1;
    
    i = 0;
    classified_amount = 0;

    for knowledge in knowledges: #tulostetaan luokka ja määrä
        print(knowledge+": "+str(knowledge_amount[i]));
        classified_amount = classified_amount + knowledge_amount[i];    
        i = i+1;

    print("Poistetut: "+ str(course_amount-classified_amount)); # tulostetaan poisjätettyjen määrä


#------------------------------------------------------------------
#createKnowledges on muuttuja, missä voi säätää haettavia osaamisia ja osaamisten sisältöä
#------------------------------------------------------------------

def createKnowledges():
    asiakaslahtoisyys = ["asiakaslähtöi", "osallisuus", "kohtaaminen", "palvelutar", "asiakasprosessi","asiakasymmärrys"];
    ohjausJaNeuvonta = ["ohjaus","neuvonta","palvelujärjestelmä","vuorovaikutus","kommunikaatio","traumat"];
    palvelujarjestelmat = ["palvelujärjestelmä","palveluohjaus","neuvonta","palveluverkosto","palvelutuottajat"];
    lainsaadantoJaEtiikka = ["etiikka","lainsäädäntö","tietosuoja","vastuu","eettinen"];
    tutkimusJaKehittamisosaaminen = ["tutkimus","innovaatio","kehittäminen"];
    robotiikkaJaDigitalisaatio = ["robotiikka","digi","tekoäly","sote-palvelut","tietoturva","tietosuoja"];
    kustannusJaLaatutietoisuus = ["laatu","laadun","vaikuttavuu","vaikutusten","kustannukset"];
    kestavanKehityksenOsaaminen = ["kestävä","ekolog","kestävyys","kierrätys","ympäristö","energiakulutus"];
    viestintaOsaaminen = ["viestintä","tunnetila","empatia","selko"];
    tyontekijyysOsaaminen = ["osaamisen","johtaminen","työhyvinvointi","muutososaaminen","muutosjoustavuus","urakehitys","verkostotyö","työyhteisö","moniammatillisuus","johtajuus"];
    monialainenYhteistoiminta = ["monialaisuu","moniammatillisuu","monitiet","yhteistyö","verkostoituminen","asiantuntijuus"];
    muu = [];

    osaamisAlueet = [];

    osaamisAlueet.append(asiakaslahtoisyys);
    osaamisAlueet.append(ohjausJaNeuvonta);
    osaamisAlueet.append(palvelujarjestelmat);
    osaamisAlueet.append(lainsaadantoJaEtiikka);
    osaamisAlueet.append(tutkimusJaKehittamisosaaminen);
    osaamisAlueet.append(robotiikkaJaDigitalisaatio);
    osaamisAlueet.append(kustannusJaLaatutietoisuus);
    osaamisAlueet.append(kestavanKehityksenOsaaminen);
    osaamisAlueet.append(viestintaOsaaminen);
    osaamisAlueet.append(tyontekijyysOsaaminen);
    osaamisAlueet.append(monialainenYhteistoiminta);
    osaamisAlueet.append(muu);

    return osaamisAlueet;


#------------------------------------------------------------------
# classify muuttujassa suoritetaan kurssien osaamisten lajittelu
#------------------------------------------------------------------

def classify(result,classes,classified,osaamiset,classifiermodel,vectorizer):
    
    
    # luodaan jaotellut kurssit:
    # [0] - kurssin id - lista[string]
    # [1] - kurssinimi - string
    # [2] - kurssikuvaus - string
    # [3] - kurssitavoitteet - string
    # [4] - kurssin tarjoajat[] - lista[string]
    # [5] - tarjoajien kaupungit - lista[string]
    # [6] - maksullisuus - lista[int]
    # [7] - opintopisteet - lista[int]
    # [8] - geneerinen osaaminen[] - lista[string]
    # [9] - kieli - lista[string]
    
    course_credit = result["credits"]; # otetaan kurssin opintopisteet tarkastusta varten
    
    course_credit = ''.join(filter(str.isdigit, course_credit)); #putsataan opintopiste int muuttujaksi
    
    if (course_credit != ''): #Tehdään tarkastus opintopisteille, jos opintopisteitä ei ole merkattu tai sen määrä ylittää 60 op, se hylätään. Näin tutkinnot saadaan poistettua
        course_credit = int(course_credit);
        if (course_credit > 60 or course_credit <= 0):
            
            return;
    else:
        return;
    
    
    course_id = result["id"]; # otetaan kurssin id tarkempaa tietokantahakua varten, jotta saadaan kurssin tavoitteet ja sisältö
    headers_id = {'Caller-id': '123'}; #headers hakuun
    
    search = "https://opintopolku.fi:443/lo/koulutus/"+course_id; #opintopolkuun tehtävä tarkempi kurssihaku
    course_response = requests.get(search,headers=headers_id);
    
    if (course_response.status_code == 404): #Jos kurssin id:tä ei löydy, kurssi hylätään, sillä kurssia ei tällöin löydy opintopolun omiltakaan sivuilta
        return
    
    course_data = course_response.json(); 
    course_json_str = json.dumps(course_data);
    course = json.loads(course_json_str);
    #muunnellaan kurssin tarkemmat tiedot työstettävään muotoon
    

    if (course["content"] is None): #Tehdään kurssin sisällöstä tyhjä jos sitä ei ole
        course_content = "";
    else:
        course_content = course["content"];
        course_content = re.sub("<.*?>", " ", course_content); #Siistitään kurssisisällöstä html tagit pois
        course_content = re.sub("\xa0", " ", course_content);
    
        
    if (course["goals"] is None): # Tehdään kurssin sisällöstä tyhjä jos sitä ei ole
        course_goals = "";

    else:
        course_goals = course["goals"];
        course_goals = re.sub("<.*?>", " ", course_goals); #Siistitään kurssisisällöstä html tagit pois
        course_goals = re.sub("\xa0", " ", course_goals);    
    
    
    course_charge = course["charge"]; #kurssin maksullisuus
    course_homeplace = course["provider"]["homeplace"]; #Kurssin kaupunki
    course_languages = course["teachingLanguages"]; #kurssin kielet listattuna
    name = result["name"]; # Kurssin nimi
    
    for classifiedcourse in classified: # Tarkasteetaan onko kurssinimi jo listassa, jos on niin lisätään nimen alle id, tarjoaja, paikkakunta, maksu ja opintopisteet
        
        clearName = name.lower();
        clearName = re.sub('[^A-Za-z0-9]+()', ' ', clearName); #putsataan tietokannasta otetun kurssin nimi

        clearClassified = classifiedcourse[1].lower(); #putsataan jo luokitellun kurssin nimi
        clearClassified = re.sub('[^A-Za-z0-9]+()', ' ', clearClassified);

        if (clearName == clearClassified): #verrataan putsattuja nimiä keskenään
            classifiedcourse[0].append(result["id"]); #lisätään samannimisen nimen id listaan
            classifiedcourse[4].append(result["lopNames"][0]); #lisätään tarjoaja listaan
            classifiedcourse[5].append(course_homeplace); #lisätään paikkakunta listaan
            classifiedcourse[6].append(course_charge); #lisätään kurssin maksu listaan
            classifiedcourse[7].append(course_credit); #lisätään kurssin opintopisteet listaan
            
            return;

    # tarkastetaan jo laitetuista kursseista onko samannimisiä kursseja, jos on niin lisätään
    # järjestäjä ja id kurssin listoihin

    
    classifiedknowledge = []; # luodaan lista osaamisille
        
    courseinfo = []; # Luodaan lista jo luokitellulle kurssille

    courseinfo.append([]); #Luodaan lista kurssi id:stä
    courseinfo[0].append(result["id"]); #kurssin id [0]
    
    courseinfo.append(name); #kurssin puhdistettu nimi [1]
    courseinfo.append(course_content); #kurssisisältö [2]
    courseinfo.append(course_goals); #kurssitavoitteet [3]

    courseinfo.append([]); # Luodaan lista kurssin tarjoajista
    courseinfo[4].append(result["lopNames"][0]); #tarjoajat [4]
    
    courseinfo.append([]); # Luodaan lista kurssin kaupungeista
    courseinfo[5].append(course_homeplace); # Kurssin kaupunki [5]
    
    courseinfo.append([]); # Luodaan lista kurssin hinnoista
    courseinfo[6].append(course_charge); # Kurssihinta [6]

    courseinfo.append([]); #Luodaan lista kurssin opintopisteistä
    courseinfo[7].append(course_credit); #opintopisteet [7]
    
    

    i = 0; # mones osaaminen
    classified_course = False; # parametri, jolla kurssi laitetaan muu kategoriaan
    
           
    if (result["subjects"] is not None): # Nullcheck

        for knowledgeclass in classes: #kaydaan lapi geneeriset osaamiset
            c = 0; # parametri, jolla poistetaan osaamisluokan duplikaatit, ettei sama kurssi saa montaa kertaa samaa kategoriaa

            for knowledge in knowledgeclass: #kaydaan lapi rajaavat avainsanat


                if knowledge in result["subjects"] and c == 0: #kaydaan lapi kurssin avainsanat
                    classifiedknowledge.append(osaamiset[i]); # Lisätään osaaminen listaan jos avainsana löytyy osaamisesta
                    
                    classified_course = True; # Jos kurssilla on osaaminen, true. Kurssi ei silloin voi olla "Muu"
                    c+=1;
                    

                if knowledge in name and c == 0:
                    classifiedknowledge.append(osaamiset[i]); # Lisätään osaaminen listaan jos avainsana löytyy osaamisesta
                    
                    classified_course = True; # Jos kurssilla on osaaminen, true. Kurssi ei silloin voi olla "Muu"
                    c+=1;

            i+=1; #osoitin listalle


    if (classified_course == False): # Jos kurssia ei ole kategorisoitu, se kategorisoidaan oppimisalgoritmillä
        
        if (course_languages[0] == "suomi"): #vain suomenkielisistä kursseista aineistoa malliin
            course_info = name+" "+course_content+" "+course_goals; #luodaan String muuttuja nimestä, tavoitteista ja kurssisisällöstä
            course_info_array = [cleanUpText(course_info)]; #sklearn tukee vain sanalistoja .predict
        
            vectorizer_matrix = vectorizer.transform(course_info_array);

            knowledgescore = classifiermodel.predict(vectorizer_matrix); #Muunnetaan aineisto oppimisalgoritmille

            if knowledgescore[0] == 999: #jos kurssia ei voitu kategorisoida annetuihin kategorioihin, se saa arvon 999, eli sille annetaan kategoria "muu"
                knowledgescore[0] = len(osaamiset)-1;
        
            classifiedknowledge.append(osaamiset[knowledgescore[0]]); #lisätään kurssin kategoria
            
        else:
            classifiedknowledge.append(osaamiset[len(osaamiset)-1]); #Koska algoritmi ei voi käsitellä englanninkielisiä kursseja aineiston vähyyden takia, englanninkielisiä
            #kursseja ei voi kategorisoida => "muu"

    courseinfo.append(classifiedknowledge); # geneeriset osaamiset [8]
    courseinfo.append(course_languages); # lisätään lista kurssin kielistä [9]
    

    classified.append(courseinfo); #Lisätään kurssin tiedot luokiteltujen kurssien listaan
    

#------------------------------------------------------------------
# createTrainingDataset funktiossa luodaan aineisto mongodbseen oppimisalgoritmia varten
# Käytetään avainsanolistoja, joita hyödyntämällä etsitään kaikista kursseista esimerkiksi etiikkaan liittyvät kurssit (avainsanat createKnowledges() muuttujassa)
# kun hakusana löytyy joko kurssin avainsanasta tai otsikosta, se lisätään oppimisalgoritmille tietyllä osaamisella
# lopulta kurssit lähetetään mongodbseen, mistä niitä hyödynnetään oppimisalgoritmin luonnissa
#------------------------------------------------------------------

def createTrainingDataset(headers,classes,knowledges,database):
    
    classifiedcourse = [];
    listofIds = [];
    

    #luodaan mongoon valmis lista kaikista kursseista avainsanojen avulla
    # [0] - id
    # [1] - osaamisluokka
    # [2] - osaamisluokan id
    # [3] - kurssikuvaus
    
    
    i = 0;

    for knowledge in knowledges: #käydään läpi osaamiset
        for knowledge_class in classes[i]: #Käydään läpi osaamisene liittyvät avainsanat, katso createKnowledges()

            notclassifiedcourses = 5; # Määrä, kuinka monta "muu" kurssia otetaan listaan
            search = "https://opintopolku.fi:443/lo/search?text="+knowledge_class+"&&&facetFilters=teachingLangCode_ffm%3AFI&&&lang=FI&ongoing=false&upcoming=false&upcomingLater=false&start=0&rows=1000&&order=asc&&&&&searchType=LO";
            # Tällä hetkellä haetaan kaikista kursseista avainsanalla, esim. "etiikka"

            response = requests.get(search,headers=headers);
            data = response.json();
            json_str = json.dumps(data);
            resp = json.loads(json_str);
            respond = resp['results']; #Hankitaan aineisto
            
            for course in respond: #Käydään läpi kurssi kerrallaan aineistoa

                course_credit = course["credits"]; # otetaan kurssin opintopisteet tarkastusta varten

                if (course_credit is None):
                    continue;
                    
                course_credit = ''.join(filter(str.isdigit, course_credit)); #putsataan opintopiste int muuttujaksi
    
                if (course_credit != ''): #Tehdään tarkastus opintopisteille, jos opintopisteitä ei ole merkattu tai sen määrä ylittää 60 op, se hylätään. Näin tutkinnot saadaan poistettua
                    course_credit = int(course_credit);
                    if (course_credit > 60 or course_credit <= 0):
                        continue;
                else: #jos opintopiste muuttuja on tyhjä, hypätään yli
                    continue;

                if course["subjects"] is None: #Jos kurssilla ei ole avainsanoja, se hypätään yli
                    continue;
                
                if (course["id"]) in listofIds: # Jos kurssi:id löytyy jo listasta, kurssia ei enään oteta mukaan, koska käytetty oppimisalgoritmi ei tällä aineistolla voi tehokkaasti
                    #arvioida montaa eri osaamista kurssille
                    continue;
                
                if knowledge_class in course["subjects"]: #Jos kurssin avainsanoista löytyy osaaminen, se lisätään
                    
                    course_info = [];
                    course_info.append(course["id"]);
                    listofIds.append(course["id"]);
                    course_info.append(knowledge);
                    course_info.append(i);

                    classifiedcourse.append(course_info);
                    continue;

                if knowledge_class in course["name"]: # Jos kurssin nimestä löytyy osaaminen, se lisätään
                    course_info = [];
                    course_info.append(course["id"]);
                    listofIds.append(course["id"]);
                    course_info.append(knowledge);
                    course_info.append(i);

                    classifiedcourse.append(course_info);
                    
                else: # Kurssi lisätään "muu" kategoriaan tukemaan oppimisalgoritmia
                    if (notclassifiedcourses > 0):
                        course_info = [];
                        course_info.append(course["id"]);
                        listofIds.append(course["id"]);
                        course_info.append("muu");
                        course_info.append(999);

                        classifiedcourse.append(course_info);
                        notclassifiedcourses = notclassifiedcourses - 1;
            
        i = i+1;

    print("Training done fetching courseID:s");

    for course in classifiedcourse: # Haetaan kursseihin niiden nimet, tavoitteet ja sisältö oppimisalgoritmille
        
        search = "https://opintopolku.fi:443/lo/koulutus/"+ course[0];
        response = requests.get(search,headers=headers);
        data = response.json();
        json_str = json.dumps(data);
        respond = json.loads(json_str);
        
        if (response.status_code == 404): #Jos kurssin id:tä ei löydy, kurssi hylätään, sillä kurssia ei tällöin löydy opintopolun omiltakaan sivuilta
            
            course.append(""); #eli kurssikuvaus on tyhjä
            continue;

        if (respond["content"] is None): #Tehdään kurssin sisällöstä tyhjä jos sitä ei ole
            course_content = "";
        else:
            course_content = respond["content"];
            course_content = cleanUpText(course_content); #putsataan content
    
        
        if (respond["goals"] is None): # Tehdään kurssin sisällöstä tyhjä jos sitä ei ole
            course_goals = "";

        else:
            course_goals = respond["goals"];
            course_goals = cleanUpText(course_goals); #putsataan goals

        course_name = respond["name"];
        course_name = cleanUpText(course_name); #putsataan nimi

        course.append(course_name+" "+course_content +" "+ course_goals); #lisätään mallille kurssia kuvavaat tekstit
        
        
    classifiedcourse_clear = [];

    for course in classifiedcourse:
        if (course[3] != ""): # poistetaan kurssit joissa ei ole mitään tietoja saatavilla
            classifiedcourse_clear.append(course);

    print("Completed creating dataset, sending to mongo:");

    sendtoMongo(classifiedcourse_clear,database);
    print("Completed sending to mongo");

#------------------------------------------------------------------
# cleanUpText() putsaa annetut aineistot kaikesta ylimääräisestä
#------------------------------------------------------------------

def cleanUpText(text):
    text = re.sub("<.*?>", " ", text); #Siistitään kurssisisällöstä html tagit pois
    text = re.sub("\xa0", " ", text);
    text = re.sub(r'[0-9]+', ' ', text); #Siistitään numerot pois
    text = re.sub("[\W\d_]", " ", text); #Siistitään erikoismerkit
    text = text.lower(); #muunnetaan sanat pienikirjaimiseksi
    
    with open('stopwords.json') as data_file: #poistetaan tekstistä stopwordit, katso stopwords.json
        stopwords = json.load(data_file);

        for word in stopwords['words']:
            text = text.replace(" "+word+" ", ' '); #poistetaan stopwordit
            
    text = re.sub(' +', ' ', text) #Poistetaan ylimääräiset välilyönnit
    

    return text; #palautetaan standardoitu teksti oppimismallille

#------------------------------------------------------------------
# createClassifierModel() luo tukiverktorikone-mallin mukaisen koneoppimismallin ja antaa sen arvosanat
#------------------------------------------------------------------
def createClassifierModel():

    dataset = fetchTrainingData();
    json_data = dumps(dataset);
    data = pd.read_json(StringIO(json_data));

    vectorizer = CountVectorizer(); #luo teksteistä vektoreita ja laskee sanamäärät jne, alustus mallille

    all_features = vectorizer.fit_transform(data.kurssikuvaus); #Lisätään aineisto CountVectorizeriin

    x_train, x_test, y_train, y_test = train_test_split(all_features, data.osaamisId, test_size=0.25,random_state=70) #Jaetaan käytettävä aineisto mallille

    classifier = svm.SVC(class_weight ='balanced',kernel='linear');  #Muokkaa jos löytyy fiksumpaa mallia scikitlearnista

    classifier.fit(x_train,y_train); #Lisätään aineisto malliin
    
    print("Classifier score "+str(classifier.score(x_test,y_test))); #Montako malli arvaa oikein prosentuaalisesti
    print("Precision: "+str(precision_score(y_test,classifier.predict(x_test),average='weighted'))); # Precision
    print("f1_score: "+str(f1_score(y_test,classifier.predict(x_test),average='weighted'))); #F1_score
    
    return classifier,vectorizer;

#------------------------------------------------------------------
# fetchTrainingData() tuo mongodbsta oppimisalgoritmissa hyödynnettävän aineiston kursseista
#------------------------------------------------------------------
def fetchTrainingData():
    server = "mongodb+srv://rmuser:hakutyokalu123@cluster0.mtzby.mongodb.net/myFirstDatabase?retryWrites=true&w=majority" #Mongodb osoite
    server_client = "testaillaan"; #Mongodb projekti
    server_db = "NaiveBayesCourses"; #Mongodb kurssihaun tietokanta
    

    client = pymongo.MongoClient(server); 
    db = client[server_client];
    
    kurssit = db[server_db];
    
    results = kurssit.find({});
    return results;
    
    
