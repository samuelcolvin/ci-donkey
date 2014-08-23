var last_response = null;
function update(){
	$.getJSON(pogress_url, function(data) {
	  // console.log(data);
	  last_response = data;
		$('#pre-build').text(data.prelog);

	  if (data.pre_script !== null){
			$('#pre-script').text(data.pre_script.join('\n'));
		}

	  if (data.main_script !== null){
			$('#main-script').text(data.main_script.join('\n'));
		}

	  if (data.mainlog !== null){
	  	$('#main-build').text(data.mainlog);
	  }

	  if (data.finished){
	  	finished('Build Finished');
	  }

	  if (data.term_error){
	  	finished('Build Error');
	  }
	})
  .fail(function(data) {
	  console.log(data);
	  clearInterval(clear_check);
    finished('Error Occurred, stopping progress updates: <pre>' + data.responseText + '</pre>');
  });
}

function finished(message){
	clearInterval(clear_check);
	$('#build-message').html(message);
}

if (pogress_url != ''){
	var clear_check = setInterval(update, 2000);
}