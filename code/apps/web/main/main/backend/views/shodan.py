# coding: utf-8
import json
from django.shortcuts import render
from main.backend.models import ShodanDevice, ShodanQuery
from django.contrib.auth.decorators import login_required


@login_required
def shodan(request):
    return_data = {'queries': []}
    if request.method == "POST":
        query = request.POST.get('query', False)
        if query:
            sq = ShodanQuery(query=query)
            sq.save()

    for query in ShodanQuery.objects.order_by("id"):
        devices = ShodanDevice.objects.filter(query_id=query.id)
        return_data["queries"].append({'query': query, 'device_count': len(devices), 'devices': devices})

    return render(request, 'backend/shodan.html', return_data)
