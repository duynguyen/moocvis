def handle_clickstream_file(f):
	for chunk in f.chunks():
		print chunk
	# return render_to_response('upload_clickstream.html', {'form': UploadFileForm()})
