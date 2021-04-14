/* Tarkennettu haku nappi toiminnallisuus */
function specifiedSearchBtn() {    
    var x = document.getElementById("openSpecifiedSearch")
    if (x.style.display == "none") {
        x.style.display = "table-cell";
    } else {
        x.style.display = "none";
    }
}

/* Haetaan kurssi-data BackEndistä */
async function getData() { 
    //hakunapppi pois käytöstä
    var btn = document.getElementById("btnH");
    btn.disabled = true;
    btn.classList.remove("searchButton");
    btn.classList.add("searchButtonD");

    const response = await fetch('http://localhost:3000/api/courses');
    const data = await response.json();
    console.log(data);
    //kutsutaan kurssien renderöinti tässä
    renderData(data);    
}
//hakunappi takaisin käyttöön
function disButton() {    
    var btn = document.getElementById("btnH");
    btn.classList.remove("searchButtonD");
    btn.classList.add("searchButton");    
    btn.disabled = false;
}
// Mitkä kurssit näytetään
function renderData(data) {        
    var rootElement = document.getElementById("datat");
    datat.innerHTML = "";
    var hakus = document.getElementById("hakusana").value.toLowerCase();
    var bg = "w";
    var str = 'Nettisivu';
    var jar = '';
    // kurssien läpikäynti
    //jos hakuehtoja
    for (var i = 0; i < data.length; i++){
        //kurssin json stringiksi
        var info = JSON.stringify(data[i]).toLocaleLowerCase();
        //hakuehtojen tarkistus
        if((info.length == 0 || info.includes(hakus))/*<===tarkentavan haun lisäys esim. tähän perään:  &&(kenttää 1 ei valittu || ehto 1 täyttyy)&&(kenttää 2 ei valittu || ehto 2 täyttyy) jne.*/){
            printCourse(data, i, rootElement, bg, str, jar);
            //taustavärin vuorottelu
            if(bg == "w") bg = "g";
            else bg = "w";
        }
    }
    //jos ei hakuehtoja(näytetään kaikki)
    console.log(rootElement);
}
//kurssin tietojen printtaus
function printCourse(data, i, rootElement, bg, str, jar){
    //div kurssin näyttämiseen
    var div = document.createElement("div");
    div.style.padding = "25px";
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
