import json
import os
import re
import psutil
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from main.backend.models import JobQueue, TSRemoteResult, FirmwareMeta, WebRootFiles, ShodanQuery, TestDevice, \
    FingerprinterElement, WebRoots, JavaScriptValue
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.template import defaultfilters as filters
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
def main(request):
    ret = {}
    ret["open"] = False
    return Response(ret)


# @login_required
@api_view(['GET', 'POST', 'DELETE', 'HEAD'])
def jobs(request, job_id=0):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        humanize = request.GET.get('humanize', False)
        limit = request.GET.get('limit', 10)
        if job_id:
            try:
                jobs = [JobQueue.objects.filter(id=int(job_id)).get()]
            except ObjectDoesNotExist:
                return Response({'success': False, 'data': []})
        else:
            jobs = JobQueue.objects.order_by('-id')[:int(limit)]

        for x in jobs:
            ret['data'].append(
                {'id': x.id,
                 'service': x.service,
                 'action': x.action,
                 'creation': naturaltime(x.creation) if humanize else x.creation,
                 'status': x.status,
                 'in_data': x.in_data,
                 'out_data': x.out_data,
                 'log': x.log
                 })
    elif request.method == 'POST':
        job = JobQueue()
        job.service = request.POST.get('service', "")
        job.action = request.POST.get('action', "")
        job.in_data = request.POST.get('in_data', "{}")
        job.save()
        if job.service and job.action:
            ret["data"] = model_to_dict(job)
        else:
            ret["success"] = False

    elif request.method == 'DELETE':
        if job_id:
            try:
                JobQueue.objects.filter(id=int(job_id), status=0).delete()
            except ObjectDoesNotExist:
                ret['success'] = False

    return Response(ret)


@login_required
@api_view(['GET', 'HEAD'])
def tests(request, test_id=0):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        humanize = request.GET.get('humanize', False)
        limit = request.GET.get('limit', 10)
        if test_id:
            try:
                remote_tests = [TSRemoteResult.objects.filter(id=int(test_id)).get()]
            except ObjectDoesNotExist:
                return Response({'success': False, 'data': []})
        else:
            remote_tests = TSRemoteResult.objects.order_by('-id')[:int(limit)]

        for x in remote_tests:
            ret['data'].append(
                {'id': x.id,
                 'firmware': model_to_dict(FirmwareMeta.objects.filter(id=int(x.fw_id)).get()),
                 'date': naturaltime(x.date) if humanize else x.date,
                 'browser': x.browser,
                 'result': x.result,
                 })
    return Response(ret)


@login_required
@api_view(['GET', 'HEAD'])
def lead_info(request):
    ret = {'success': True, 'data': {}}
    if request.method == 'GET':
        try:
            web_roots = json.loads(request.GET.get('web-roots', []))
        except Exception as e:
            return Response({'success': False, 'data': []})

        for web_root_id in web_roots:
            files = WebRootFiles.objects.filter(web_root=web_root_id)
            ret['data'][web_root_id] = []
            for file in files:
                ret['data'][web_root_id].append(model_to_dict(file))

    return Response(ret)


@login_required
@api_view(['GET', 'POST', 'DELETE', 'HEAD'])
def shodan_query(request, query_id=0):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        limit = request.GET.get('limit', 10)
        if query_id:
            try:
                queries = [ShodanQuery.objects.filter(id=int(query_id)).get()]
            except ObjectDoesNotExist:
                return Response({'success': False, 'data': []})
        else:
            queries = ShodanQuery.objects.order_by('-id')[:int(limit)]

        for x in queries:
            ret['data'].append(
                {'id': x.id,
                 'status': x.status,
                 'query': x.query
                 })
    elif request.method == 'POST':
        query = request.POST.get('query', "")
        if query:
            ShodanQuery(query=query).save()
        else:
            ret['success'] = False
    elif request.method == 'DELETE':
        if query_id:
            try:
                ShodanQuery.objects.filter(id=int(query_id), status=0).delete()
            except ObjectDoesNotExist:
                ret['success'] = False
        else:
            ret['success'] = False
    return Response(ret)


@login_required
@api_view(['GET', 'HEAD'])
def log_view(request):
    ret = {'success': True, 'data': []}
    log_path = '/tmp/log/'
    log_file = request.GET.get('log_file', "corsica_daemon")
    request_path = '{}/{}.log'.format(log_path, log_file)
    real_request_dir = os.path.commonprefix((os.path.realpath('{}/{}.log'.format(log_path, log_file)), log_path))
    if real_request_dir == log_path and os.path.isfile(request_path):

        ret['data'] = open(request_path, 'r').read()
    else:
        ret['success'] = False
    return Response(ret)


@login_required
@api_view(['POST', 'HEAD'])
def session(request):
    ret = {'success': True, 'data': {}}
    key = request.POST.get('key', None)
    value = request.POST.get('value', None)

    if key == "auto_refresh":
        request.session['auto_refresh'] = 1 if value == "1" else 0
        ret['data'] = request.session['auto_refresh']
    else:
        ret['success'] = False
    return Response(ret)


@login_required
@api_view(['GET', 'HEAD'])
def firmwares(request, fw_id=0):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        humanize = request.GET.get('humanize', False)
        limit = request.GET.get('limit', 0)
        if fw_id:
            try:
                fws = [FirmwareMeta.objects.filter(id=int(fw_id)).get()]
            except ObjectDoesNotExist:
                return Response({'success': False, 'data': []})
        else:
            if limit:
                fws = FirmwareMeta.objects.order_by('id')[:int(limit)]
            else:
                fws = FirmwareMeta.objects.order_by('id')

        for x in fws:
            test_devices = TestDevice.objects.filter(fw_id=x.id).count()
            ret['data'].append(
                {'id': x.id,
                 'created': naturaltime(x.created) if humanize else x.created,
                 'filename': x.filename,
                 'vendor': x.vendor,
                 'version': x.version,
                 'devicename': x.devicename,
                 'size': filters.filesizeformat(x.size),
                 'hash_sum': x.hash_sum,
                 'processed': x.processed,
                 'test_devices': test_devices
                 })

    return Response(ret)

@login_required
@api_view(['GET', 'HEAD'])
def cpu_mem_info_view(request):
    memory = {}
    mem_info = psutil.virtual_memory()

    for name in mem_info._fields:
        value = getattr(mem_info, name)
        memory[name.capitalize()] = value
    ret = {'cpu_info': psutil.cpu_times_percent(percpu=True),
           'mem_info': memory}

    return Response(ret)


@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
@api_view(['GET', 'HEAD'])
def get_javascript_values(request):
    ret = {'tree': json.loads(JavaScriptValue.objects.filter(name='tree').order_by('-id')[0].value),
           'file_fingerprints': json.loads(
               JavaScriptValue.objects.filter(name='file_fingerprints').order_by('-id')[0].value),
           'fine_fingerprinting_files':
               json.loads(JavaScriptValue.objects.filter(name='fine_fingerprinting_files').order_by('-id')[0].value)
           }

    return Response(ret)


@login_required
@api_view(['GET', 'HEAD', 'POST'])
def fingerprinter_view(request, elem_id=0):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        humanize = request.GET.get('humanize', False)
        reverse_order = request.GET.get('reverse_order', False)
        limit = request.GET.get('limit', 0)
        if elem_id:
            try:
                elements = [FingerprinterElement.objects.filter(id=int(elem_id)).get()]
            except ObjectDoesNotExist:
                return Response({'success': False, 'data': []})
        else:
            if limit:
                elements = FingerprinterElement.objects.order_by('-id' if reverse_order else 'id')[:int(limit)]
            else:
                elements = FingerprinterElement.objects.order_by('-id' if reverse_order else 'id')

        web_root_to_firmware = {}
        for elem in WebRoots.objects.order_by('id'):
            web_root_to_firmware[elem.id] = model_to_dict(elem.firmware)

        for elem in elements:
            el = model_to_dict(elem)
            try:
                el['result'] = json.loads(el['result'])
                el['result']['result_elements'] = []
                for web_root in el['result']['web_roots']:
                    if web_root in web_root_to_firmware:
                        el['result']['result_elements'].append(web_root_to_firmware[web_root])
            except:
                el['result'] = {}
            ret['data'].append(el)
    elif request.method == 'POST':
        addresses = []
        allowed_browsers = ["chrome", "firefox"]

        input = request.POST.get("addresses")
        browser = request.POST.get("browser")

        if browser not in allowed_browsers:
            ret = {'success': False,
                   'message': 'Browser {} not supported. Supported Browsers: {}'.format(browser, allowed_browsers)}
            return Response(ret, status=status.HTTP_406_NOT_ACCEPTABLE)

        for address in input.split("\n"):
            address = address.strip()
            if not re.match("http(?:s?):\/\/.*", address):
                ret = {'success': False, 'message': 'Malformed Entry: {}'.format(address)}
                return Response(ret, status=status.HTTP_406_NOT_ACCEPTABLE)
            addresses.append(address)

        for entry in addresses:
            FingerprinterElement(url=entry, browser=browser, status=0).save()

    return Response(ret)


@login_required
@api_view(['GET', 'HEAD', 'POST'])
def version_fingerprints(request):
    ret = {'success': True, 'data': []}
    if request.method == 'GET':
        firmwares = FirmwareMeta.objects.order_by('vendor', 'devicename')
        fingerprints = json.loads(JavaScriptValue.objects.filter(name='fine_fingerprinting_files').order_by('-id')[0].value)
        plugins = {}
        for firm in firmwares:
            dat = {'firm': model_to_dict(firm), 'fingerprint': fingerprints[str(firm.id)]}
            if firm.vendor in plugins:
                if firm.devicename in plugins[firm.vendor]:
                    plugins[firm.vendor][firm.devicename].append(dat)
                else:
                    plugins[firm.vendor][firm.devicename] = [dat]
            else:
                plugins[firm.vendor] = {firm.devicename: [dat]}

        ret['data'] = plugins
    return Response(ret)