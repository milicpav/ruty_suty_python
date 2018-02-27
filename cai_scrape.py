#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 17:08:44 2018

@author: jan
"""
#packages
import pandas as pd
from pathlib import Path
from urllib.request import urlopen
from bs4 import BeautifulSoup
from tabulate import tabulate

#variables definition
excel_file_name = 'kontakty_laboratore.xlsx'
excel_sheet_name = 'laboratore'
data_file_name = 'scraped_data_file.txt'
pg_total = 52
scraped_data = []

# function for web scraping
#out format: [ic, name, desc, cert_info, address, tel, fax, mail, web, contact_person]
def load_data(pg_total):
    data_all = []
    for pg_number in range(1, pg_total+1):
        print("Processing page " + str(pg_number)+ "/" + str(pg_total))
        response = urlopen("http://www.cai.cz/Subjekty?DisableFilter=true&page=" + str(pg_number)+"&ScopeId=L")
        pagesource = response.read()
        soup = BeautifulSoup(pagesource, "html.parser")
        
        toi = soup.body.table # the table with the data 
        toi_entries = toi.find_all("tr", recursive = False) 
        for toi_entry in toi_entries:
            name = " ".join(toi_entry.td.div.div.a.get_text().split())
            in_tbls = toi_entry.div.find_all("table")
            
            toi_entry_tbl1 = in_tbls[0]
            tbl1_tr = toi_entry_tbl1.find_all("tr")
            ic = tbl1_tr[0].td.get_text().split()[1]
            desc = tbl1_tr[1].td.get_text().strip()
            
            toi_entry_tbl2 = in_tbls[1]
            cert_info = " ".join(toi_entry_tbl2.tr.td.get_text().split())
            
            toi_entry_tbl3 = in_tbls[2]
            rest_data = []
            tbl3_trs = toi_entry_tbl3.find_all("tr")
            for i in range(6):
                str_tmp = tbl3_trs[i].td.find_next_sibling().get_text()
                str_tmp = " ".join(str_tmp.split())
                rest_data.append(str_tmp)
            
            data = [ic, name, desc, cert_info] + rest_data
            data_all.append(data)
    return data_all

#getting data if exists from file or scrape the website
my_file = Path('/home/jan/Documents/Diploma_thesis/' + data_file_name)

if my_file.is_file():
    with open(data_file_name, "r") as ins:
        scraped_data = [line.strip() for line in ins]
        
    for laboratory in range(len(scraped_data)):
        scraped_data[laboratory] = scraped_data[laboratory].split('%')
        scraped_data[laboratory] = list(map(str.strip, scraped_data[laboratory]))
        
    print('Data retrieved from file.'+'\n')
    
else:
    scraped_data = load_data(pg_total)
    
    with open(data_file_name, 'w') as ins:
        for laboratory in scraped_data:
          for inf_idx in range(len(laboratory)-1):
              ins.write(laboratory[inf_idx] + ' % ')
          ins.write(laboratory[-1])
          ins.write('\n')
            
    print('Data retrieved from website.'+'\n')

    
# transforming data from list to datagrame, using pandas
labels = ['IČ', 'Kód a název', 'Popis', 'Informace o akreditaci', 'Adresa', 'Telefon', 'Fax', 'Email', 'Webové stránky', 'Kontaktní osoba']

labs = pd.DataFrame.from_records(scraped_data, columns=labels)

writer = pd.ExcelWriter(excel_file_name, engine='xlsxwriter')
labs.to_excel(writer, sheet_name= excel_sheet_name)
writer.save()

# finding a printing duplicate ICO companies
dup_idx = labs.duplicated('IČ', False)
dup_lab = labs.loc[dup_idx, ['IČ', 'Kód a název', 'Popis', 'Informace o akreditaci']]
dup_lab_srt = dup_lab.sort_values(by=['IČ','Kód a název'])
dup_lab_srt['Kód a název'] = dup_lab_srt['Kód a název'].str[:30]
dup_lab_srt['Popis'] = dup_lab_srt['Popis'].str[:20]
dup_lab_srt['Informace o akreditaci'] = dup_lab_srt['Informace o akreditaci'].str[:21]
print('Table with duplicated IČ in laboratory database')
print(tabulate(dup_lab_srt, tablefmt='psql', headers = ['č.', 'IČ', 'Kód a název', 'Popis', 'Informace o akreditaci'])+'\n')
