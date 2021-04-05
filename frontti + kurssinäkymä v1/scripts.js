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
    const response = await fetch('http://localhost:3000/api/courses');
    const data = await response.json();
    console.log(data);
    var li = document.getElementById("courseElem");
    renderData(data);
    for(var i = 0; i < data.length; i++){

    }
}

// Näytetään kurssit 
function renderData(data) {
    var rootElement = document.getElementById("datat");
    var bg = "w";
    var str = 'Nettisivu';
    var jar = '';
    // kurssien läpikäynti
    for (var i = 0; i < data.length; i++){
        // mahd hakuehtojen tarkistus tähän väliin
        // esim if(data[i] sisältää hakusanan){
        // (data[i] = tarkastelussa oleva kurssi)

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
        //taustavärin vuorottelu
        if(bg == "w") bg = "g";
        else bg = "w";
        //}hakuehto kiinni
    }
    console.log(rootElement);
}
