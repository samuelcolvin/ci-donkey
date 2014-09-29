var default_delay = 1000;
$(document).ready(function(){
  delay_update(default_delay);
});

function delay_update(timeout){
    setTimeout(update, timeout);
}

function update(){
  var el = $('[load-from]');
  el.load(el.attr('load-from'), function(response, status, xhr){
    var code = xhr.status;
    if (code == 200) {
      delay_update(default_delay);
    }
    else if (code == 201){
      delay_update(10000);
    }
  });
}