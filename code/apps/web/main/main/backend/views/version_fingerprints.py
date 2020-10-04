# coding: utf-8
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from main.backend.models import FirmwareMeta
from main.backend.models import WebRoots
from main.backend.utils.plugin_data import plugin_data
from main.backend.models import JobQueue


@login_required
def version_fingerprints(request):

    firmware = {}
    web_root_to_firmware = {}
    for x in WebRoots.objects.all():
        web_root_to_firmware[x.id] = x.firmware
    for x in FirmwareMeta.objects.all():
        firmware[x.id] = x

    data = json.load(open("/tmp/corsica/plugins.json", "r"))
    vulns = plugin_data['vulns']
    ret_data = []
    for plugin in data:
        affected_to_fixed = plugin_data['plugins'][plugin]['affected_version_to_fixed']
        version_to_vuln = plugin_data['plugins'][plugin]['version_to_vuln']

        ret = []
        for web_root in data[plugin]:
            # Get Version String from web_root
            version_str = web_root_to_firmware[int(web_root)].version
            if version_str in affected_to_fixed:
                fixed_version_str = affected_to_fixed[version_str]
                for sub_version in data[plugin][web_root]:
                    sub_version_str = web_root_to_firmware[int(sub_version)].version
                    if sub_version_str == fixed_version_str:
                        # Found the fixed_in version
                        if len(data[plugin][web_root][sub_version]) > 0:
                            # vulnerable version is distinguishable from fixed version
                            ret.append({'affected':version_str, 'fixed_in': sub_version_str, 'vuln': vulns[str(version_to_vuln[version_str])]})
                        break
        if ret:
            ret_data.append({"plugin": plugin, "data": ret})
    return_data = {'data': ret_data, 'plugin_count': len(ret_data), 'plugin_count_total': len(data)}

    return render(request, 'backend/version_fingerprints.html', return_data)
