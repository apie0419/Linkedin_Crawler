import parser as htmlparser
import codecs, logging
import json

def extract_fields(file):
	f = codecs.open(file, 'r', 'utf-8')
	html_text = f.read()
	#Logger
	country_code = 'sg'
	logger_name = country_code+'_profile_logger'
	logger = logging.getLogger(logger_name)
	#print('raw html: \n' + html_text)
	parsed_data = htmlparser.parseProfile(html_text,logger_name)
	print(parsed_data)
	#wf = codecs.open('parsed_profile.txt','w','utf-8')
	#wf.write(parsed_data)
	if parsed_data:
		# write to a file
		with open("parsed_profile.json","w") as f:
		  json.dump(parsed_data, f)
	return html_text


src = extract_fields("data/xavier-siddarth-b5344961.html")
