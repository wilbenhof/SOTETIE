const { response } = require("express");
const express = require("express");
const mongoose = require("mongoose");
const dbModels = require("./dbModels/kurssi.js");

require("dotenv/config");

const app = express();

app.get("/", (req, res) => {
    res.send("First Request !!!")
});

app.get("/api", (req, res) => {
    kurssi.translateAliases(kurssi.find(null, (err, obj) => {
        if (err) {
            res.status(500);
            res.send(err);
            return;
        }
        const data = obj;
        console.log(data);
        res.json(data);
    }));
});


mongoose.connect(process.env.DB_CONNECTION_STRING,
    { 
        useUnifiedTopology: true, 
        useNewUrlParser: true 
    }).then(() => {
        console.log("Connected to the database");
    }).catch(() => {
        console.log("Failed to connect database", err);
});

const kurssiSchema = new mongoose.Schema(dbModels.kurssi);
const kurssi = mongoose.model("kurssi", kurssiSchema, "kurssit");

app.listen(3000, () => {
    console.log("Listening to 3000")
});