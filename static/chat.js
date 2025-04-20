var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function () {
    console.log('Connected to the server');
});

socket.on('backlog', function(data) {
    let arr = JSON.parse(data);
    document.getElementById("chatbody").innerHTML = "";
    for (let i = 0; i < arr.length; i++) {
        let username = arr[i].username;
        let message = arr[i].message;
        const messageParagraph = document.createElement('p');
        messageParagraph.textContent = username + ": " + message;
        document.getElementById("chatbody").appendChild(messageParagraph);
    }
});

socket.on('newMessage', function (data) {
    console.log('Server says: ' + data);
    let obj = JSON.parse(data);
    let username = obj.username;
    let message = obj.message;
    const messageParagraph = document.createElement('p');
    messageParagraph.textContent = username + ": " + message;
    document.getElementById("chatbody").appendChild(messageParagraph);
});

function sendMessage() {
    var message = document.getElementById('message').value;
    socket.emit('message', message);
}