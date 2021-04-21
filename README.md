# SOTETIE
Ohjelmistotuotanto 2 kurssilla toteutettu projekti. Sisältää hakutyökalun, jolla haetaan kursseja ammattikorkeakouluista ja yliopistoista.

1. Asenna tietokoneeseesi Git, jos sinulla ei jo sitä ole. -> https://git-scm.com/downloads
2. Asenna myös Node.JS, jos sinulla ei jo sitä ole. -> https://nodejs.org/en/download/
    - tämän lisäksi tarvitset nodemonin ja expressin, joten aja komennot:
    $ npm install nodemon
    $ npm install express

3. Kloonaa repo omalle koneellesi vaikka käyttämällä Git Bash:a komennolla
    -> $ git clone https://github.com/wilbenhof/SOTETIE.git
    
4. Avaa tiedosto koodieditorissasi, vaikka VSCode.

5. Tarvitset vielä .env tiedoston jolla ottetaan yhteys tietokantaan
   -  Lisää sovellukkseen tiedosttorakenteen BackEnd kansioon uusi tiedosto ja nimeä se .env -nimellä
   -  Kopioi tiedostoon ja määritä:
      DB_CONNECTION_STRING = "mongodb+srv://rmuser:SALASANA@cluster0.mtzby.mongodb.net/DATABASEN_NIMI"
      PORT = 5000
      
6.  Käynnistä yhteys tietokantaan terminaalista ajamalla "$ npm start" -komento BackEnd kansiossa.
7.  Avaa selain osoitteessa 127.0.0.1:5500 (tai mitä satut käyttämäänkään) tai käynnistä Live Server laajennus
    Käyttöliitymän pitäisi toimia täysin nyt selaimessa ja olla yhteydessä tietokantaan.
