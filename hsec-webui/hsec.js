var express   = require('express');
var https     = require('https');
var fs        = require('fs');
var auth      = require('basic-auth');
var zmq       = require('zmq');
var logger    = require('morgan');

var app       = express();

console.log("starting")


// require authorization everywhere
app.use(function(req, res, next) {
    var user = auth(req);

    if (user === undefined || user['name'] !== 'user' || user['pass'] !== 'pass') {
      res.statusCode = 401;
      res.setHeader('WWW-Authenticate', 'Basic realm="MyRealmName"');
      res.end('Unauthorized');
    } else {
      res.writeHead(200);
      res.write('Access granted');
      res.end(req.url)

      next();
    }
});


var publisher = zmq.socket('pub')

//var jsonObject=[["Upper Windows", "arm"]];

//var stringObject=JSON.stringify(jsonObject);

publisher.bind('tcp://*:5563', function(err) {
  if(err)
    console.log(err)
  else
    console.log('Listening on 5563')
})


app.use(logger('short'));

function stateSend(command) {
  var stringObject1=JSON.stringify(command);
  console.log(stringObject1);

  //if you pass an array, send() uses SENDMORE flag automatically
  publisher.send( "control_events", zmq.ZMQ_SNDMORE);
  publisher.send( stringObject1);
}

//setInterval(function() {
  //var jsonObject=[["Upper Windows", "arm"]];
  //stateSend(jsonObject);
//},10000);

app.get('/disarm/:zone', function(req,res) {
  var jsonObject1=[[req.params.zone, "disarm"]];
  stateSend(jsonObject1);
});

app.get('/arm/:zone', function(req,res) {
  var jsonObject1=[[req.params.zone, "arm"]];
  stateSend(jsonObject1);
});

app.use(function(request,response,next) {
  request.on('error', function(err) {
    // This prints the error message and stack trace to `stderr`.
    console.error(err.stack);
  });
 
    console.log(request.body);
    console.log(request.url);
  next();
});

const options = {
  key: fs.readFileSync('hsec.key'),
  cert: fs.readFileSync('hsec.crt'),
};
https.createServer(options, app ).listen(3000);


// exit processing example from:
// http://stackoverflow.com/questions/14031763/doing-a-cleanup-action-just-before-node-js-exits
process.stdin.resume();//so the program will not close instantly

function exitHandler(options, err) {
    if (options.cleanup) console.log('clean');
    if (err) console.log(err.stack);
    if (options.exit) process.exit();
}

function exit1(options,err) {
    console.log('exit')
    process.exit();
}

function exit2(options,err) {
    console.log('sigint');
    var rv=publisher.close();
    //console.log(rv);
    process.exit();
}

function exit3(options,err) {
    if (err) console.log(err.stack);
    console.log(err);
    process.exit();
}

//do something when app is closing
process.on('exit',              exit1.bind(null, {cleanup:true}));

//catches ctrl+c event
process.on('SIGINT',            exit2.bind(null, {exit:true }));

//catches uncaught exceptions
process.on('uncaughtException', exit3.bind(null, {exit:true}));


