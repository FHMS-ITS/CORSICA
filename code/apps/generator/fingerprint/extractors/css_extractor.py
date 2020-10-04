from io import open
import tinycss
from tinycss.css21 import RuleSet
from utils.exceptions import EmptyFileException, NoFingerprintFoundException


class CssFingerprintExtractor:
    @staticmethod
    def create_fingerprint(file):
        fingerprints = []
        try:
            elements = CssFingerprintExtractor.___extract_fingerprint("{f.local_path}/{f.filename}".format(f=file))

            for elem in elements["class"]:
                if elem["en"] == "" or elem["en"] == "body":
                    continue

                fp = {"t": "c", "ct": 0}
                fp.update(elem)
                fingerprints.append(fp)

            for elem in elements["id"]:
                if elem["en"] == "" or elem["en"] == "body":
                    continue
                fp = {"t": "c", "ct": 1}
                fp.update(elem)
                fingerprints.append(fp)

            for elem in elements["plain"]:
                if elem["en"] == "" or elem["en"] == "body":
                    continue
                fp = {"t": "c", "ct": 2}
                fp.update(elem)
                fingerprints.append(fp)
            return fingerprints

        except EmptyFileException:
            pass
        return {}

    @staticmethod
    def ___extract_fingerprint(file):
        data = {"class": [], "id": [], "plain": []}
        blklst_style_values = ['0px', '#000000', 'block', 'none', 'auto', '16px']
        blklst_style_attrib = ['border', 'border-left', 'border-right', 'border-top', 'border-bottom']
        blklst_elem_type = ['body']

        with open(file, "r", encoding="ascii", errors="ignore") as f:
            content = f.read()

        parser = tinycss.make_parser('page3')
        stylesheet = parser.parse_stylesheet(content)
        if len(stylesheet.rules) == 0:
            raise EmptyFileException

        for rule in stylesheet.rules:
            if type(rule) is not RuleSet:
                continue

            selector = rule.selector.as_css()
            for sel in selector.split(","):
                if " " in sel or ":" in sel:
                    continue

                if "." in sel:
                    split_char = "."
                    key = "class"
                elif "#" in sel:
                    split_char = "#"
                    key = "id"
                else:
                    split_char = ""
                    key = "plain"

                if sel.startswith(".") or sel.startswith("#"):
                    elem_type = "div"
                else:
                    try:
                        tmp = sel.split(split_char)
                        elem_type = tmp[0]
                        sel = "." + tmp[1]
                    except ValueError:
                        elem_type = sel.lower()
                        sel = ""

                for declaration in rule.declarations:
                    style_value = declaration.value.as_css().replace("\"", "")
                    if style_value in blklst_style_values or declaration.name in blklst_style_attrib or elem_type in blklst_elem_type:
                        continue

                    data[key].append({"et": elem_type.strip(),
                                      "en": sel[1:].strip(),
                                      "sa": declaration.name,
                                      "sv": style_value})
        if not (data["id"] or data["class"] or data["plain"]):
            raise NoFingerprintFoundException
        return data
