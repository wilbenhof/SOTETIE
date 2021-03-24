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
    
    for(var i = 0; i < data.length; i++){
        

    }
}

/*
function renderData(data) {
    var rootElement = document.getElementById("joku");
    // tänne looppi ja datan renderöinti 
    console.log(rootElement);

    

}
*/