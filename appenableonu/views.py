from django.shortcuts import render, redirect
from django.contrib import messages
from .servicios.olt import habilitar


def main(request):
    return render(request, "main.html")


def habilitar_onu(request):

    if request.method != "POST":
        return redirect("main")

    mac = request.POST.get("mac", "").strip().upper()

    mac_limpia = mac.replace(":", "")

    if len(mac_limpia) != 12 or any(
        c not in "0123456789ABCDEF" for c in mac_limpia
    ):
        messages.error(request, "La dirección MAC no es válida.")
        return redirect("main")

    resultado = habilitar(mac)

    if resultado["success"]:
        messages.success(request, resultado["message"])
    else:
        messages.error(request, resultado["message"])

    return render(request, "main.html", {"mac": mac})