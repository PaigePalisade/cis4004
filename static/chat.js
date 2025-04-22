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
        addMessageToBody(arr[i]);
    }
});

socket.on('newMessage', function (data) {
    let obj = JSON.parse(data);
    addMessageToBody(obj);
});

function sendMessage() {
    var message = document.getElementById('message').value;
    if (message != "") {
        document.getElementById('message').value = '';
        socket.emit('message', JSON.stringify({'body': message, 'roomname': roomname}));
    }
}

function checkSubmit(e) {
    if(e && e.keyCode == 13) {
        sendMessage();
    }
}

// https://stackoverflow.com/a/5774055
function pad(d) {
    return (d < 10) ? '0' + d.toString() : d.toString();
}

function addMessageToBody(obj) {
    let username = obj.username;
    let body = obj.body;
    let display_name = obj.displayname;
    let date = new Date(obj.timestamp);
    let timeStr = date.getFullYear() + '-' + pad(date.getMonth()+1) + '-' + pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes());
    let pfpAddr = obj.pfp;

    console.log("scroll height: " + document.body.scrollHeight);
    console.log("inner height: " + window.innerHeight);
    console.log("scroll y: " + window.scrollY);

    let isScrolled = window.innerHeight + window.scrollY >= document.body.scrollHeight;

    let mainDiv = document.createElement('div');
    mainDiv.className = 'message';
    let messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    let pfpDiv = document.createElement('div');
    let pfp = document.createElement('img');
    pfp.className = 'pfp'
    pfp.src = pfpAddr;
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
    let timeDiv = document.createElement('div');
    timeDiv.className = 'time';
    let timeP = document.createElement('p');
    timeP.textContent = timeStr;
    timeDiv.appendChild(timeP);
    messageHeader.appendChild(pfpDiv);
    messageHeader.appendChild(nameDiv);
    messageHeader.appendChild(timeDiv);
    let messageBodyP = document.createElement('p');
    messageBodyP.className = 'message-body';
    messageBodyP.textContent = body;
    mainDiv.appendChild(messageHeader);
    mainDiv.appendChild(messageBodyP);
    document.getElementById("chatbody").appendChild(mainDiv);

    if (username != user) {
        mainDiv.classList.add("right");
    }
    if (isScrolled) {
        window.scrollTo(0, document.body.scrollHeight);
    }
}