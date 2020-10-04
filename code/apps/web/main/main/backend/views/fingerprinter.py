# coding: utf-8
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def fingerprinter(request):
    return_data = {'firmwares': []}

    return render(request, 'backend/fingerprinter.html', return_data)
