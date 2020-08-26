var express = require('express');
var app = express();
var port = process.env.PORT || 3000;
var server = app.listen(port,function(){
    console.log("We have started our server on port 3000");
});

app.get('/', function (req, res) {
  var hostname = req.headers.host.split(":")[0];

  if(hostname.startsWith("admin."))
    res.send("this is admin response!");
  else {
    console.log('PORT is:' + process.env.PORT)
    console.error("Something wrong");
    console.log("Something normal");
    res.send('Hello world from Node ' + process.version);
  }
});
