saved = []

with open("saved.txt", "r", encoding = "utf-8-sig") as urls:
	for url in urls :
		if url[-2] != "/" :
			url = url[:-1] + "/\n"
		if url not in saved :
			saved.append(url)

with open("saved2.txt", "w+", encoding = "utf-8-sig") as f :
	for url in saved :
		f.write(url)