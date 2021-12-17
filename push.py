import subprocess
import os
def run_comando(comando):
	process = subprocess.Popen(comando, stdout=subprocess.PIPE)
	output = process.communicate()[0]

comentario = input("Introduzca comentario: ")
run_comando(["git", "init"])
run_comando(["git", "add", "--all"])
run_comando(["git", "commit", "-m", comentario])
run_comando(["git", "push", "-u", "origin", "master"])
os.system("pause")