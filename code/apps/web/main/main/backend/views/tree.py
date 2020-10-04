# coding: utf-8
import json
from django.shortcuts import render, redirect
from main.backend.models import JavaScriptValue, WebRootFiles, FirmwareMeta, WebRoots
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict


@login_required
def tree(request, group_id=""):
    return_data = {}
    trees = JavaScriptValue.objects.filter(name="tree").order_by("-id")
    group_ids = []
    for elem in trees:
        group_ids.append(elem.group_id)

    tree_obj = trees[0]
    if group_id:
        try:
            tree_obj = JavaScriptValue.objects.filter(group_id=group_id, name="tree").get()
        except:
            pass

    tree_data = json.loads(tree_obj.value)
    if tree_data:
        return_data = {'node': construct_tree(tree_data), 'group_ids': group_ids, 'actual_id': group_id}
    return render(request, 'backend/tree.html', return_data)


def construct_tree(node):
    new_node = Node(node['webroots'])
    new_node.path = node['path']
    new_node.files = node['files']

    if node['left']:
        new_node.left = construct_tree(node['left'])
    if node['right']:
        new_node.right = construct_tree(node['right'])
    return new_node


@login_required
def modal_leaf_info(request):
    return_data = {'web_roots': []}
    try:
        web_roots = json.loads(request.GET.get('web-roots', []))
        file_count = {}
        for web_root_id in web_roots:
            files = WebRootFiles.objects.filter(web_root=web_root_id)

            arr = {'web_root_id': web_root_id, 'files': []}
            for file in files:
                arr['files'].append(model_to_dict(file))
                file_identifier = "{file.web_full_path};{file.hash}".format(file=file)
                if file_identifier in file_count:
                    file_count[file_identifier].append(web_root_id)
                else:
                    file_count[file_identifier] = [web_root_id]

            return_data['web_roots'].append(arr)

        files = []
        for key in file_count:
            files.append({'path': key.split(";")[0], 'hash': key.split(";")[1], 'web_roots': file_count[key],
                          "count": len(file_count[key])})
        return_data['files'] = files

    except Exception as e:
        return_data['error'] = str(e)

    return render(request, 'modal/leaf_info.html', return_data)


class Node:
    def __init__(self, web_roots=None):
        if web_roots is None:
            web_roots = []
        self.web_roots = web_roots
        self.web_roots_count = len(json.loads(web_roots))
        self.firmwares = []
        for web_root in json.loads(web_roots):
            try:
                self.firmwares.append(model_to_dict(WebRoots.objects.filter(id=web_root).first().firmware))
            except:
                pass

        self.path = ""
        self.left = None
        self.right = None
        self.fingerprints = []

    def __str__(self):
        return "{node.path}".format(node=self)
