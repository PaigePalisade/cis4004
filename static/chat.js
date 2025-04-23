var socket = io.connect(location.origin);
var user = "";
var roomname = "";

socket.on('connect', function () {
    console.log('Connected to the server');
    user = document.getElementById("username").textContent;
    roomname = document.getElementById("roomname").textContent;
    // when first connecting to the server, get the backlog of messages
    socket.emit('getBacklog', roomname);
});

socket.on('backlog', function(data) {
    let arr = JSON.parse(data);
    // clear any messages, then fill them back up
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
    // clear the message field, then send
    var message = document.getElementById('message').value;
    if (message != "") {
        document.getElementById('message').value = '';
        socket.emit('message', JSON.stringify({'body': message, 'roomname': roomname}));
    }
}

// check if the user has pressed the enter key
function checkSubmit(e) {
    if(e && e.keyCode == 13) {
        sendMessage();
    }
}

// https://stackoverflow.com/a/5774055
// adds a leading 0 if the value is less than 10, to aid in formatting the date
function pad(d) {
    return (d < 10) ? '0' + d.toString() : d.toString();
}

// adds a message to the HTML DOM, I don't know if there is an easier way of doing this lol
// just creates a bunch of HTML elements, sets their data, parents them, and adds them to the DOM
function addMessageToBody(obj) {
    let username = obj.username;
    let body = obj.body;
    let display_name = obj.displayname;
    // format the time YYYY-MM-DD HH:MM (24 hour time because parsing am/pm is a few more lines)
    // Year-month-day is disambiguous
    let date = new Date(obj.timestamp);
    let timeStr = date.getFullYear() + '-' + pad(date.getMonth()+1) + '-' + pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes());
    let pfpAddr = obj.pfp;

    // check if the user is scrolled to the bottom of the page
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

    // messages not sent by the user should be displayed on the right
    if (username != user) {
        mainDiv.classList.add("right");
    }
    // scroll down if the user was scrolled to the bottom
    if (isScrolled) {
        window.scrollTo(0, document.body.scrollHeight);
    }
}