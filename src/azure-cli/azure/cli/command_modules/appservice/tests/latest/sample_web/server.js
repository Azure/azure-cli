var express = require('express');
var app = express();
var port = process.env.PORT || 3000;
var server = app.listen(port,function(){
    console.log("We have started our server on port 3000");
});

app.get('/', function (req, res) {
  console.log('PORT is:' + process.env.PORT)
  console.error("Something wrong");
  console.log("Something normal");
  res.send('Hello world');
});
