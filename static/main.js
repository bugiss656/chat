document.addEventListener('DOMContentLoaded', () => {


  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);



  document.querySelector('#join-channel').onclick = () => {
    joinRoom(channel);
    document.querySelector('#message-form').style.display = 'block';
    document.querySelector('#join-channel').style.display = 'none';
  };



  document.querySelector('#leave-channel').onclick = () => {
    leaveRoom(channel);
  };



  function leaveRoom(channel) {
    socket.emit('leave', {'user': user, 'room': channel});
  }



  function joinRoom(channel) {
    socket.emit('join', {'user': user, 'room': channel});
  }



  document.querySelector('#send-message').onclick = e => {
    e.preventDefault();

    var message = document.querySelector('#message-input').value;
    socket.send({'message': message, 'user': user, 'room': channel});
    document.querySelector('#message-form').reset();
  };



  socket.on('message', data => {
    const li =  `
      <li>
        <div class="row">
          <b>${data.user}</b><span class="timestamp"><small>${data.timestamp}</small></span>
        </div>
        <div class="row">
          ${data.message}
        </div>
      </li>
    `;

    document.querySelector('#message-box').innerHTML += li;
  });

});
