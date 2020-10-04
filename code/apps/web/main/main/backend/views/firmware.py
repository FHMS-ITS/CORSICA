filter# coding: utf-8
import json
from django.shortcuts import render, redirect
from main.backend.models import TestDevice, FirmwareMeta
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict


@login_required
def firmware(request):
    return_data = {'firmwares': []}
    firmwares = FirmwareMeta.objects.order_by("id")
    for firmware in firmwares:
        fw = model_to_dict(firmware)
        fw['test_devices'] = TestDevice.objects.filter(fw_id=firmware.id).count()
        return_data['firmwares'].append(fw)

    return render(request, 'backend/firmware.html', return_data)
