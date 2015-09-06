"use strict";

var express = require('express');

var app = express();

var server = require('http').Server(app);
var io = require('socket.io')(server);

app.use(express.static('assets'));

app.get('/', function(req,res) {
	res.sendFile(__dirname + '/index.html');
});

io.on('connection', function(socket) {
	socket.on('chat message', function(msg) {
		io.emit('chat message', msg);
	}); 
});

server.listen(process.env.PORT || '8080', function() {
  console.log('App listening at http://%s:%s', server.address().address, server.address().port);
  console.log("Press Ctrl+C to quit.");
});