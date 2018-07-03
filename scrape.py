from bs4 import BeautifulSoup
import requests



def my_scrape(base_url):

	r = requests.get(base_url)

	soup = BeautifulSoup(r.text,"html.parser")

	details = soup.find_all('dt')

	book_details = {}

	for detail in details:
		full_text = detail.text 
		descriptor = detail.find("strong").text 
		specific_detail = str(full_text.replace(descriptor,'').replace('  ','').replace('\n',''))
		if len(specific_detail) != 0 and specific_detail[len(specific_detail) - 1] == ' ':
			specific_detail = specific_detail[:len(specific_detail) - 1]
		descriptor = descriptor.replace(':','')
		book_details[descriptor] = specific_detail

	return book_details	
