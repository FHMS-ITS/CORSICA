# coding: utf-8
import json
from django.shortcuts import render
from main.backend.models import FirmwareMeta, TSRemoteResult
from django.contrib.auth.decorators import login_required


@login_required
def remote_tester(request):
    return_data = {'results': [], 'numbers': {'correct': 0, 'multiple': 0, 'incorrect': 0, 'error': 0}}
    test_results = TSRemoteResult.objects.order_by('-id').all()
    tested = []
    for result in test_results:
        data = {
            'id': result.id,
            'fw_id': result.fw_id,
            'date': result.date,
            'browser': result.browser
        }

        if result.result != "{}":
            result_data = json.loads(result.result)
            data['count'] = {'correct': len(result_data['true']),
                             'correct_elem': result_data['true'],
                             'incorrect': len(result_data['false']),
                             'online': len(result_data['device_status']['online']),
                             'offline': len(result_data['device_status']['offline'])
                             }
            if len(result_data['true']) > 0:
                if len(result_data['false']) > 0:
                    return_data['numbers']['multiple'] += 1
                else:
                    return_data['numbers']['correct'] += 1
            elif len(result_data['false']) > 0:
                return_data['numbers']['incorrect'] += 1

        else:
            data['count'] = {'online': "ERROR"}
            return_data['numbers']['error'] += 1
        tested.append(result.id)
        return_data['results'].append(data)

    return_data['firmware_without_test'] = [x.id for x in FirmwareMeta.objects.exclude(id__in=list(set(tested)))]
    return render(request, 'backend/remote_tester.html', return_data)
