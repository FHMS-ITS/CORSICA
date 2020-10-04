import re
from io import open
from pyjsparser import PyJsParser

from utils.exceptions import EmptyFileException, NoFingerprintFoundException


class JavaScriptFingerprintExtractor:
    @staticmethod
    def create_fingerprint(file):
        fingerprints = []
        try:
            js_fingerprint = JavaScriptFingerprintExtractor.___extract_js_fingerprint(
                "{f.local_path}/{f.filename}".format(f=file))

            for elem in js_fingerprint["f"]:
                fingerprints.append({"t": "j", "f": elem})
            for elem in js_fingerprint["v"]:
                fingerprints.append({"t": "j", "v": elem})

        except EmptyFileException:
            pass
        return fingerprints

    @staticmethod
    def ___extract_js_fingerprint(file):
        data = {"v": [], "f": []}
        with open(file, "r", encoding="ascii", errors="ignore") as f:
            js_content = f.read()
            if not JavaScriptFingerprintExtractor.____clean_js_from_dynamic(js_content):
                return data

        if js_content == "":
            raise EmptyFileException

        p = PyJsParser()
        js = p.parse(js_content)["body"]

        for a in js:
            obj_type = a["type"]
            if obj_type == "ExpressionStatement":
                expr = a["expression"]
                if expr["type"] == "AssignmentExpression":
                    if expr["operator"] == "=":
                        val = JavaScriptFingerprintExtractor.____recursive_object_parser(expr["left"])
                        if val is not None:
                            data["v"].append(val)
                elif expr["type"] == "CallExpression":
                    pass
            elif obj_type == "VariableDeclaration":
                for decl in a["declarations"]:
                    if decl["init"] is not None and "name" in decl["id"]:
                        data["v"].append(decl["id"]["name"])
            elif obj_type == "FunctionDeclaration":
                data["f"].append(a["id"]["name"])

        if not (data["f"] or data["v"]):
            raise NoFingerprintFoundException
        return data

    @staticmethod
    def ____recursive_object_parser(obj):
        if "property" not in obj:
            return obj["name"]
        if "name" in obj["property"]:
            return JavaScriptFingerprintExtractor.____recursive_object_parser(obj["object"]) + "." + obj["property"][
                "name"]

    @staticmethod
    def ____clean_js_from_dynamic(js_str):
        dynamic_parts = [
            ["<\?.*?\?>", re.I],
            ["<\?.*?\?>[^'\"]", re.S],
            ["<script.*?>", re.I],
            ["</script>", re.I],
            ["<style.*?>.*?<\/style>", re.S],
            ["<\?.*?\?>", re.S],
            ["<!--.*?-->", re.I]
        ]

        for c in dynamic_parts:
            if re.findall(c[0], js_str, flags=c[1]):
                return False
        return True
