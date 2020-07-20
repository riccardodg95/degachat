//disable create button when input form is empty
document.addEventListener('DOMContentLoaded', () => {

  document.querySelector('#submit').disabled = true;

  document.querySelector('#channel').onkeyup = () => {
      if (document.querySelector('#channel').value.length > 0)
          document.querySelector('#submit').disabled = false;
      else
          document.querySelector('#submit').disabled = true;
  };
});

//redirect when selecting a channel from drop-down menu
function redirectFunction(obj) {
  var joined_channel = obj.value;
  if (joined_channel){
    var loc = "/channel/"+ joined_channel;
    window.location.href = loc;
  }
}
