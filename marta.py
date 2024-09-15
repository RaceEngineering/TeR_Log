prueba= open("prueba.txt","a")
b="marta"
prueba.write(b)
prueba.close()

prueba = open("prueba.txt", "r")
log = prueba.read()
print(log)