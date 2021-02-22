from django.http import HttpResponse
import requests
import json
import sys
from django.shortcuts import render

def home(request):
    headers_id = {'Caller-id': '123'};
    search = "https://opintopolku.fi/lo/search?start=0&rows=10000&lang=fi&searchType=LO&text=*&facetFilters=teachingLangCode_ffm:FI&facetFilters=educationType_ffm:et01.05&facetFilters=theme_ffm:teemat_12";
    response = requests.get(search,headers=headers_id);
    # haetaan data opintopolusta

    data = response.json();
    json_str = json.dumps(data);
    resp = json.loads(json_str);
    lista = resp['results'];
    # luodaan työstettävä data

    classes = createClasses();
    # luodaan haluttavat "osaamiset"

    classifiedcourses = [];
    
    osaamiset = [
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
                "Monialainen yhteistoiminta"
                ];

    num = [0,0,0,0,0,0,0,0,0,0,0,0];
    # luodaan jaotellut kurssit
    # [0] - kurssin id - string
    # [1] - kurssinimi - string
    # [2] - kurssin tarjoajat[] - lista[string]
    # [3] - opintopisteet - int
    # [4] - geneerinen osaaminen - lista[string]

    for result in lista: 
        classify(result,classes,classifiedcourses,osaamiset,num);
    
    
    
     # eritellään data osaamisalueittain
    
    i = 0;

    for a in osaamiset:
        print(a + ": "+str(num[i]))
        i +=1;

    print("Muu: "+ str(num[i]));
    return render(
        request,
        'FrontEnd/display.html',
        {
            'response':classifiedcourses

        }
    )

def createClasses():
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


def classify(result,classes,classified,osaamiset,num):
    
    # result = listan yksittainen kurssi
    # knowledge = osaamisalueen yksittainen osaaminen
    # courseinfo = kurssin tiedot

    # luodaan jaotellut kurssit
    # [0] - kurssin id - string - (lista id:sta eri tarjoajilta?)
    # [1] - kurssinimi - string
    # [2] - kurssin tarjoajat[] - lista[string]
    # [3] - opintopisteet - int
    # [4] - geneerinen osaaminen[] - lista[string]
    
    name = result["name"];
    # nimet pitää siistiä
    
    for classifiedcourse in classified:
        
        if (name == classifiedcourse[1]):
            classifiedcourse[2].append(result["lopNames"][0]);
            return;

    classifiedknowledge = [];
        
    courseinfo = [];

    courseinfo.append(result["id"]); #kurssin id
    courseinfo.append(name); #kurssin puhdistettu nimi
    courseinfo.append(result["lopNames"]); #tarjoajat
    courseinfo.append(result["credits"]);
    
    i = 0; # mones osaaminen
    a = 0; # parametri, jolla kurssi laitetaan muu kategoriaan
    
           
    if (result["subjects"] is not None):

        for knowledgeclass in classes: #kaydaan lapi geneeriset osaamiset
            c = 0; # parametri, jolla poistetaan osaamisluokan duplikaatit

            for knowledge in knowledgeclass: #kaydaan lapi rajaavat avainsanat


                if knowledge in result["subjects"] and c == 0: #kaydaan lapi kurssin avainsanat
                    classifiedknowledge.append(osaamiset[i]);
                    num[i] = num[i]+1;
                    a+=1;
                    c+=1;

            i+=1; 


    if (a == 0):
        classifiedknowledge.append("Muu")
        num[11] = num[11]+1;

    courseinfo.append(classifiedknowledge);

    classified.append(courseinfo);
    

   
    
