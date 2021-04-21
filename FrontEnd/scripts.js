var data = "";

// valintavaihtoehdot tarkennettuun hakuun
function getChoices(){
    var kaup = document.getElementById("kaupunki");
    var onko = 0;
    //data läpi
    for(var i = 0; i<data.length; i++){
        for(j = 0; j < data[i].kaupungit.length; j++){
            //listassa olevat kaupungit läpi
            for(var k = 0; (k < kaup.options.length && onko == 0); k++){          
                //jos on listassa, siirrytään seuraavaan       
                if(kaup.options[k].value == JSON.stringify(data[i].kaupungit[j])){
                    onko = 1;
                }
            }
            //jos kaupunkia ei löytynyt, lisätään vaihtoihin
            if(onko == 0){
                var option = document.createElement("option");
                option.text = JSON.stringify(data[i].kaupungit[j]);
                kaup.add(option);
            }
            onko = 0;
        }
    }
}
/* Haetaan kurssi-data BackEndistä */
async function getData() { 
    const response = await fetch('http://localhost:3000/api/courses');
    data = await response.json();
    console.log(data);
    getChoices();
}

// Mitkä kurssit näytetään
function renderData() {
    //elementit käyttöliittymästä       
    var rootElement = document.getElementById("datat");
    datat.innerHTML = "";
    var hakus = document.getElementById("hakusana").value.toLowerCase();
    var osa = document.getElementById("osaaminen").value.toLowerCase();
    var koulu = document.getElementById("koulu").value.toLowerCase();
    if(koulu == "ammattikorkeakoulu")koulu="amk";
    var kieli = document.getElementById("kieli").value.toLowerCase();
    var kaup = document.getElementById("kaupunki").value.toLowerCase();
    var maksu = document.getElementById("maksu").value.toLowerCase();
    var bg = "w";
    var str = 'Nettisivu';
    var jar = '';
    // kurssien läpikäynti
    for (var i = 0; i < data.length; i++){
        //hakuehtojen tarkistus
        //hakusana
        if((hakus.length == 0 || JSON.stringify(data[i]).toLocaleLowerCase().includes(hakus)) &&
        //osaaminen
        (osa.toString()=="kaikki" || JSON.stringify(data[i].osaaminen).toLocaleLowerCase().includes(osa)) &&
        //järjestäjä
        (koulu.toString()=="kaikki" || JSON.stringify(data[i].koulustyyppi).toLocaleLowerCase().includes(koulu)) &&
        //opetuskieli
        (kieli.toString()=="kaikki" || JSON.stringify(data[i].opetuskielet).toLocaleLowerCase().includes(kieli)) &&
        //kaupunki
        (kaup.toString()=="kaikki" || JSON.stringify(data[i].kaupungit).toLocaleLowerCase().includes(kaup))&&
        //maksullisuus
        (maksu.toString() == "kaikki" ||  true === true)){
            //näytetään kurssi
            printCourse(i, rootElement, bg, str, jar);
            //taustavärin vuorottelu
            if(bg == "w") bg = "g";
            else bg = "w";
        }
    }
    console.log(rootElement);
}
//kurssin maksullisuuden tarkistus
function isFree(i, maksu){
    for(j=0;j<data[i].maksullisuus.length;j++){
        var hinta = JSON.stringify(data[i].maksullisuus[j]);
        var pit = hinta.length;
        if(maksu=="ei"){
            if(hinta.includes("0") && pit === 3) {
                return true;
            }
        }
        else if(!hinta.includes("0") || pit > 3){
            return true;
        }
    }
    return false;
}
//kurssin tietojen muotoilu
function printCourse(i, rootElement, bg, str, jar){
    //div kurssin näyttämiseen
    var div = document.createElement("div");
    div.style.padding = "25px";
    div.style.backgroundColor = "white"
    if(bg == "g") div.style.backgroundColor = "Gainsboro";
    //kurssin sisältö       
    div.innerHTML = 'Kurssin nimi: '+data[i].kurssinimi+"<br>"+'Kurssikuvaus: '+data[i].kurssikuvaus+
    "<br>"+'Kurssitavoitteet: '+data[i].kurssitavoiteet+"<br>"+'Osaaminen: '+data[i].osaaminen+
    "<br>"+'Opetuskielet: '+data[i].opetuskielet+"<br>"+
    "<br>"+'Kurssin järjestäjät: '+"<br>";
    //eri järjestäjät
    for(j = 0; j < data[i].kaupungit.length; j++){
        //estetään toisto
        if(jar != data[i].kurssiId[j]){
            jar = data[i].kurssiId[j];
            //järjestäjän lapsielementti
            var divi = document.createElement("div");
            //sisältö
            divi.innerHTML= "<br>"+'Järjestäjä: '+data[i].kurssintarjoajat[j]+"<br>"+'Kaupunki: '+data[i].kaupungit[j]+
            "<br>"+'Maksullisuus: '+data[i].maksullisuus[j]+"<br>"+'Opintopisteet: '+data[i].opintopisteet[j]+"<br>"+
            str.link('https://opintopolku.fi/app/#!/koulutus/'+data[i].kurssiId[j]);
            //liitetään järjestäjä kurssiin
            div.appendChild(divi);
        }
    }
    //liitetään kurssi hakunäkymään
    rootElement.appendChild(div);
}