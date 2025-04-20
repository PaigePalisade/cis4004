var socket = io.connect('http://' + document.domain + ':' + location.port);
var user = "";
var roomname = "";

socket.on('connect', function () {
    console.log('Connected to the server');
    user = document.getElementById("username").textContent;
    roomname = document.getElementById("roomname").textContent;
    socket.emit('getBacklog', roomname);
});

socket.on('backlog', function(data) {
    let arr = JSON.parse(data);
    document.getElementById("chatbody").innerHTML = "";
    for (let i = 0; i < arr.length; i++) {
        // let username = arr[i].username;
        // let body = arr[i].body;
        // const messageParagraph = document.createElement('p');
        // messageParagraph.textContent = username + ": " + body;
        // document.getElementById("chatbody").appendChild(messageParagraph);
        addMessageToBody(arr[i]);
    }
});

socket.on('newMessage', function (data) {
    console.log('Server says: ' + data);
    let obj = JSON.parse(data);
    addMessageToBody(obj);
});

function sendMessage() {
    var message = document.getElementById('message').value;
    socket.emit('message', JSON.stringify({'body': message, 'roomname': roomname}));
}

function addMessageToBody(obj) {
    let username = obj.username;
    let body = obj.body;
    let display_name = obj.displayname;

    let mainDiv = document.createElement('div');
    mainDiv.className = 'message';
    let messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    let pfpDiv = document.createElement('div');
    let pfp = document.createElement('img');
    pfp.className = 'pfp'
    pfp.src = '/static/pfp/' + username + '.webp';
    pfpDiv.appendChild(pfp);
    let nameDiv = document.createElement('div');
    let displayNameP = document.createElement('p');
    displayNameP.className = 'display-name';
    displayNameP.textContent = display_name;
    let usernameP = document.createElement('p');
    usernameP.className = 'username';
    usernameP.textContent = '@' + username;
    nameDiv.appendChild(displayNameP);
    nameDiv.appendChild(usernameP);
    messageHeader.appendChild(pfpDiv);
    messageHeader.appendChild(nameDiv);
    let messageBodyP = document.createElement('p');
    messageBodyP.className = 'message-body';
    messageBodyP.textContent = body;
    mainDiv.appendChild(messageHeader);
    mainDiv.appendChild(messageBodyP);
    document.getElementById("chatbody").appendChild(mainDiv);

    if (username != user) {
        mainDiv.classList.add("right");
    }
}