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

	  if (data.processing_complete){
	  	finished('Build Finished', data.build_id);
	  }

	  if (data.term_error){
	  	finished('Build Error', data.build_id);
	  }
	})
  .fail(function(data) {
	  console.log(data);
	  clearInterval(clear_check);
    finished('Error Occurred, stopping progress updates: <pre>' + data.responseText + '</pre>');
  });
}
var redirected = false;
function redirect(build_id){
  if (redirected) return;
  redirected = true;
  document.location.href = '/show_build/' + build_id;
}

function finished(message, build_id){
  clearInterval(clear_check);
  $('#build-message').html(message);
  if (build_id !== null){
    setTimeout(redirect, 2500, build_id);
  }
}

if (pogress_url != ''){
  update();
	var clear_check = setInterval(update, 2000);
}
