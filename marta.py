prueba= open("prueba.txt","a")
b="marta"
prueba.write(b)
prueba.close()

prueba = open("prueba.txt", "r")
print(prueba.read())