import csv

def mostrar_city():
    with open ('city.csv', mode= 'r', newline='') as file:
        spamreader = csv.reader(file, delimiter=';', quotechar='|')
        for row in spamreader:
            print(' '.join(row))

mostrar_city()