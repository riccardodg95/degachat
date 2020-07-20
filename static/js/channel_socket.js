document.addEventListener('DOMContentLoaded', () => {

  // disable send button if input form is empty
  document.querySelector('#chat_send').disabled = true;

  document.querySelector('#chat_text').onkeyup = () => {
    if (document.querySelector('#chat_text').value.length > 0){
      document.querySelector('#chat_send').disabled = false;
    } else {
      document.querySelector('#chat_send').disabled = true;
    }
  };

  updateScroll();

  // Connect to websocket
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

  // When connected configure button to send message
  socket.on('connect', () => {

    // user has enetered the channel
    socket.emit('join');

    // send new message
    document.querySelector('#chat_send').addEventListener('click', () => {
      event.preventDefault();
      let text = document.getElementById('chat_text').value;
      if (text.length > 0){
        socket.emit('text to send', text);
        document.querySelector('#chat_text').value = '';
        updateScroll();
        removeButton(); //remove previous 'delete' buttons
      };
    });


    // user has left the channel
    document.querySelector('#leave_channel').addEventListener('click', () => {
      localStorage.removeItem('user_joined_channel')
      socket.emit('leave');
    });

    // user has left the channel (logout event)
    document.querySelector('#logout').addEventListener('click', () => {
      localStorage.removeItem('user_joined_channel')
      socket.emit('leave');
    });
  });

  // When a new message arrives add to the unordered list
  socket.on('send text', data => {
    const li = document.createElement('li');
    li.innerHTML = `<b>${data.user}</b>(${data.timestamp}): ${data.text} <button class="delete_button" id="delete_button">Delete</button>`;
    document.querySelector('#timestamp').append(li);
    updateScroll();
    document.getElementById("delete_button").onclick = function() {
    socket.emit("delete_last_msg")}
    });

    //when user joins
    socket.on('joined', data => {

      localStorage.setItem('user_joined_channel', data.channel)

      const li = document.createElement('li');
      li.innerHTML = `--- <b>${data.user}</b> has joined the chat ---`;
      document.querySelector('#timestamp').append(li);

      updateScroll();
    });

    //when user leaves
    socket.on('left', data => {
      const li = document.createElement('li');
      li.innerHTML = `--- <b>${data.user}</b> has left the chat ---`;
      document.querySelector('#timestamp').append(li);

      updateScroll();
    });

    socket.on('remove_delete_button', data => {
      removeMessage()
    })
});


function updateScroll() {
    // scroll to the bottom of the chat
    var element = document.getElementsByClassName("chat_text")[0];
    element.scrollTop = element.scrollHeight +100;
  }

function removeButton() {
    // remove all 'delete' buttons
    var button = document.getElementsByClassName("delete_button");
    while(button.length > 0){
      button[0].parentNode.removeChild(button[0]);
    }
  }
function removeMessage(){
    // remove last message when button is clicked
    var last_msg = document.getElementById("timestamp").getElementsByTagName("li");
    last_msg[last_msg.length-1].innerHTML = `<i style="color: grey">This message has been deleted</i>`;
  }
