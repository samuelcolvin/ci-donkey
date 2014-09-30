var start_delay = 5000;
var update_delay = 20000;
$(document).ready(function(){
  delay_update(start_delay);
});

function delay_update(timeout){
    setTimeout(update, timeout);
}

function update(){
  var el = $('[load-from]');
  el.load(el.attr('load-from'), function(response, status, xhr){
    var code = xhr.status;
    if (code == 200) {
      delay_update(start_delay);
    }
    else if (code == 201){
      delay_update(update_delay);
    }
  });
}
