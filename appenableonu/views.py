from django.shortcuts import render, redirect
from django.contrib import messages
from .servicios.olt import habilitar


def main(request):
    return render(request, "main.html")


def habilitar_onu(request):

    if request.method == "POST":

        fabricante = request.POST.get("fabricante")
        identificador = request.POST.get("identificador", "").strip()

        if fabricante == "tplink":
            resultado = habilitar(identificador)

        elif fabricante == "huawei":
            resultado = habilitar(identificador)

        else:
            resultado = "Fabricante no válido"

        if resultado["success"]:
            messages.success(request, resultado["message"])
        else:
            messages.error(request, resultado["message"])

    return render(request, "main.html")