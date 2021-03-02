from django.http import HttpResponse
import requests
import json
import sys
import re
import string
import pymongo
from django.shortcuts import render


def home(request):

    
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
    
    for search in search_list: #tehdään rajaavat kurssihaut tietokantaan
        response = requests.get(search,headers=headers_id);
        data = response.json();
        json_str = json.dumps(data);
        resp = json.loads(json_str);
        respond = resp['results']; # Muunnetaan data käsiteltävään muotoon
        
        course_amount = course_amount + len(respond); # tarkastusarvo kaikille kursseille jos ne printataan konsolissa (printCourseAmount)

        for result in respond: #Tehdään jokaisen haun kurssille luokittelu
            classify(result,classes,classifiedcourses,knowledges); # luokittelu
    
    printCourseAmount(classifiedcourses,knowledges,course_amount); #tulostetaan kurssien luokat
    

    sendtoMongo(classifiedcourses); #Luokiteltujen kurssien siirto tietokantaan
 
    return render(
        request,
        'FrontEnd/display.html',
        {
            'response':classifiedcourses

        }
    )


def sendtoMongo(classifiedcourses):
    
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
    server_db = "kurssit"; #Mongodb kurssihaun tietokanta
    backup_db = "backup"; # backup tietokanta

    client = pymongo.MongoClient(server); 
    db = client[server_client];
    
    kurssit = db[server_db];
    
    
    pipeline =  [ {"$match": {}}, # siirto päätietokannasta varatietokantaan ennen poistoa
                 {"$out": backup_db},
                ]

    db.kurssit.aggregate(pipeline) #siirto
    
    kurssit.remove({}); #päätietokannan tyhjennys ennen kurssien ajoa

    for course in classifiedcourses: #kurssiajo tietokantaan, kaikki ei luokitellut kurssit jätetään pois
        if (course[8][0] != "Muu"):
           
            kurssi = {  "kurssinimi": course[1],
                        "kurssi-id": course[0],
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


def createKnowledges():
    asiakaslahtoisyys = ["asiakaslähtöi", "osallisuus", "kohtaaminen", "palvelutar", "asiakasprosessi"];
    ohjausJaNeuvonta = ["ohjaus","neuvonta","palvelujärjestelmä","vuorovaikutus","kommunikaatio"];
    palvelujarjestelmat = ["palvelujärjestelmä","palveluohjaus","neuvonta","palveluverkosto","palvelutuottajat"];
    lainsaadantoJaEtiikka = ["etiikka","lainsäädäntö","tietosuoja","vastuu","eettinen"];
    tutkimusJaKehittamisosaaminen = ["tutkimus","innovaatio","kehittäminen"];
    robotiikkaJaDigitalisaatio = ["robotiikka","digi","tekoäly","sote-palvelut","tietoturva","tietosuoja"];
    kustannusJaLaatutietoisuus = ["laatu","laadun","vaikuttavuu","vaikutusten","kustannukset"];
    kestavanKehityksenOsaaminen = ["kestävä","ekolog","kestävyys","kierrätys","ympäristö","energiakulutus"];
    viestintaOsaaminen = ["viestintä","tunnetila","empatia","selko"];
    tyontekijyysOsaaminen = ["osaamisen","johtaminen","työhyvinvointi","muutososaaminen","muutosjoustavuus","urakehitys","verkostotyö","työyhteisö","moniammatillisuus"];
    monialainenYhteistoiminta = ["monialaisuu","moniammatillisuu","monitiet","yhteistyö","verkostoituminen","asiantuntijuus"];

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

    return osaamisAlueet;


def classify(result,classes,classified,osaamiset):
    
    
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
            c = 0; # parametri, jolla poistetaan osaamisluokan duplikaatit

            for knowledge in knowledgeclass: #kaydaan lapi rajaavat avainsanat


                if knowledge in result["subjects"] and c == 0: #kaydaan lapi kurssin avainsanat
                    classifiedknowledge.append(osaamiset[i]); # Lisätään osaaminen listaan jos avainsana löytyy osaamisesta
                    
                    classified_course = True; # Jos kurssilla on osaaminen, true. Kurssi ei silloin voi olla "Muu"
                    c+=1;

            i+=1; 


    if (classified_course == False):
        classifiedknowledge.append(osaamiset[i]);
        # jos ei löydy osaamista, sille annetaan listan viimeinen arvo "muu". Vaihtoehtoisesti tähän luokittelualgoritmi
       

    courseinfo.append(classifiedknowledge); # geneeriset osaamiset [8]
    courseinfo.append(course_languages); # lisätään lista kurssin kielistä [9]
    

    classified.append(courseinfo); #Lisätään kurssin tiedot luokiteltujen kurssien listaan
    

   
    
