# coding: utf-8
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from main.backend.models import TestDevice, CrawlerTarget
from django.contrib.auth.decorators import login_required


@login_required
def crawler(request):
    return_data = {'device_name': '', 'vendor_name': '', 'device_ips': ''}
    if request.method == "POST":
        ip_addresses = []
        device_name = request.POST.get('device_name', False)
        vendor_name = request.POST.get('vendor_name', False)
        device_ips = request.POST.get('device_ips', False)

        if not all([device_name, vendor_name, device_ips]):
            messages.error(request, "Please fill all required fields")
            return_data = {'device_name': device_name, 'vendor_name': vendor_name, 'device_ips': device_ips}
            return render(request, 'backend/main.html', return_data)

        # ToDo: Add ip Address validator
        """
        from django.core.validators import validate_ipv46_address
        from django.core.exceptions import ValidationError
        for row in device_ips.split('\n'):
            try:
                addr = row.split(":")
                validate_ipv46_address(addr[0])
                if len(addr) == 2:
                    if not addr[1].isdigit():
                    raise ValidationError("")
            except ValidationError:
                messages.error(request, "Please only enter valid IP-Adresses and optional Port into the text field")
                return render(request, 'backend/main.html', return_data)
        """
        for line in device_ips.split("\n"):
            ip_addresses.append(line.strip())

        crawler_target = CrawlerTarget(url=json.dumps(ip_addresses), vendor=vendor_name, device_name=device_name)
        crawler_target.save()
        messages.success(request, "Job erfolgreich angelegt")

    targets = CrawlerTarget.objects.order_by('-id')
    return_data["targets"] = targets

    return render(request, 'backend/crawler.html', return_data)
