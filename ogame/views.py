import requests
from django.shortcuts import render
from django.http import HttpResponse


def api_root(request):
    return render(request, 'api_root.html')


def wiki(request):
    return HttpResponse(requests.get('https://github.com/brunolcarli/Invictus/wiki').content)