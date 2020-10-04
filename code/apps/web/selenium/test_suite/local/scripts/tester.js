var result = {'true': [], 'false': []};
var done = {};

var hashCode = function (s) {
    return s.split("").reduce(function (a, b) {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a
    }, 0);
};

function get_frame_document(frame) {
    return frame.contentDocument || frame.contentWindow.document;
}

function normalize_css_values(fingerprint, style) {
    // Normalize colors
    var rgb_elements = style.match(/rgb\([0-9]*, [0-9]*, [0-9]*\)/g);
    if (rgb_elements) {
        for (var color in rgb_elements) {
            var rgb = rgb_elements[color].split(',');
            var col = "#" + ((1 << 24) + (parseInt(rgb[0].substring(4)) << 16) + (parseInt(rgb[1]) << 8) + parseInt(rgb[2])).toString(16).slice(1);
            style = style.replace(rgb_elements[color], col);
        }
    }

    if (style.indexOf("px") > 0 && fingerprint.sv.indexOf("pt") > 0) {
        style = 3 / 4 * parseInt(style.match(/[0-9]*px/)[0].replace("px", "")) + "pt";
    }

    style = style.toLowerCase();
    fingerprint.sv = fingerprint.sv.toLowerCase();
    style = style.replace(/,\s/g, ",");
    fingerprint.sv = fingerprint.sv.replace(/,\s/g, ",");

    if (fingerprint.sa === "font-family") {
        style = style.replace(/"/g, "");
        fingerprint.sv = fingerprint.sv.replace(/"/g, "");
    }

    return {"fingerprint": fingerprint, "computed_style": style}
}

function test_img(address, frame, node) {
    var img_exists = function () {
        var res = false;
        for (var id in node["fingerprints"]) {
            var fingerprint = node["fingerprints"][id];
            if (img.width === fingerprint.w && img.height === fingerprint.h) {
                res = true;
                break;
            }
        }
        continue_testing(address, frame, node, res);
    };

    var img = document.createElement('img');
    img.id = 'img' + hashCode(address + node.path);
    img.src = '../data/files/' + address + node.path;
    img.onload = img_exists;
    img.onerror = img_exists;
    get_frame_document(frame).body.appendChild(img);
    get_frame_document(frame).body.removeChild(img);
}

function test_css(address, frame, node) {
    var css_exists = function () {
        for (var id in node["fingerprints"]) {
            var fingerprint = node["fingerprints"][id];
            var type = fingerprint.et;
            if (type === "")
                type = "div";

            var element = document.createElement(type);

            if (fingerprint.ct === 0 || fingerprint.ct === 2)
                element.className = fingerprint.en;
            else if (fingerprint.ct === 1 || fingerprint.ct === 2)
                element.id = fingerprint.en;

            get_frame_document(frame).body.appendChild(element);
            var computed_style = "";
            if (window.getComputedStyle) {
                computed_style = window.getComputedStyle(element, null).getPropertyValue(fingerprint.sa);
            }
            else {
                computed_style = element.currentStyle.getPropertyValue(fingerprint.sa);
            }

            var normalized = normalize_css_values(fingerprint, computed_style);
            fingerprint = normalized["fingerprint"];
            computed_style = normalized["computed_style"];

            var res = false;
            if (computed_style === fingerprint.sv) {
                res = true;
                break;
            }

            get_frame_document(frame).body.removeChild(element);
        }
        get_frame_document(frame).body.removeChild(lnk);
        continue_testing(address, frame, node, res);

    };

    var lnk = document.createElement('link');
    lnk.rel = 'stylesheet';
    lnk.type = 'text/css';
    lnk.href = '../data/files/' + address + node.path;
    lnk.media = 'all';
    lnk.onerror = css_exists;
    lnk.onload = css_exists;
    get_frame_document(frame).body.appendChild(lnk);

}

function test_js_function(address, frame, node) {
    var js_function_exists = function () {
        var res = false;
        for (var id in node["fingerprints"]) {
            var fingerprint = node["fingerprints"][id];
            try {
                if (fingerprint.f) {
                    if (eval("typeof frame.contentWindow." + fingerprint.f + " === 'function'")) {
                        res = true;
                        break;
                    }
                } else if (fingerprint.v) {
                    if (eval("typeof frame.contentWindow." + fingerprint.v + " !== 'undefined'")) {
                        res = true;
                        break;
                    }
                }
            } catch (e) {

            }
        }
        get_frame_document(frame).body.removeChild(script_elem);
        continue_testing(address, frame, node, res);
    };
    var script_elem = document.createElement('script');
    script_elem.src = '../data/files/' + address + node.path;
    script_elem.onreadystatechange = js_function_exists;
    script_elem.onload = js_function_exists;
    script_elem.onerror = js_function_exists;
    get_frame_document(frame).body.appendChild(script_elem);
}

function test_element(web_root, frame, node, id) {
    if (node["left"] == null && node["right"] == null) {
        if ("final" in node) {
            var success = false;
            if (parseInt(node["webroots"]) === parseInt(web_root))
                success = true;

            save_result(web_root, node["webroots"], success)

        } else {
            request_count[web_root]++;
            test_fine(web_root, frame, node);
        }
        return;
    }
    request_count[web_root]++;
    var func;
    switch (node["fingerprints"][0].type) {
        case "i":
            func = test_img;
            break;
        case "c":
            func = test_css;
            break;
        case "j":
            func = test_js_function;
            break;
    }
    func(web_root, frame, node);
}

function continue_testing(web_root, frame, node, result) {
    var next_element;
    if (result) {
        next_element = node["left"];
    } else {
        next_element = node["right"];
    }
    test_element(web_root, frame, next_element, 0);

}

// ToDo: Support multiple fingerprint-files per web root fingerprint
function generate_fine_fingerprinting_tree(web_root, web_root_fingerprints) {
    if (!web_root_fingerprints || !web_root_fingerprints.length)
        return null;
    return {
        "path": web_root_fingerprints[0]["file"],
        "webroots": [web_root],
        "fingerprints": [web_root_fingerprints[0]],
        "left": {"webroots": [web_root], "final": true},
        "right": {"webroots": [0], "final": true},
        "final": true
    };

}

function test_fine(address, frame, node) {
    var fine_tree;
    for (var i in node["webroots"]) {
        fine_tree = generate_fine_fingerprinting_tree(node["webroots"][i], fingerprints[node["webroots"][i]]);

        if (fine_tree != null)
            test_element(address, frame, fine_tree, 0);
        else
            save_result(address, node["webroots"], true)
    }
}

function save_result(web_root, node_roots, res) {
    var elem = {
        'web_root': web_root,
        'node_root': node_roots,
        'request_count': request_count[web_root],
        'firmware': web_roots[web_root]
    };
    done[web_root] = 1;
    if (res) {
        result['true'].push(elem)
    } else {
        result['false'].push(elem)
    }

    if (Object.keys(done).length >= Object.keys(web_roots).length) {
        var result_element = document.createElement('span');
        result_element.id = 'result';
        result_element.textContent = JSON.stringify(result);
        document.body.appendChild(result_element);
    }
}


var request_count = {};
var test;

function __create_testing_iframe(web_root) {
    var frame = document.createElement("iframe");
    frame.id = "frame_" + web_root;
    frame.style = "display:none";
    document.body.appendChild(frame);
    var frame_doc = get_frame_document(frame);
    frame_doc.open();
    frame_doc.write("<html><body></body></html>");
    frame_doc.close();
    return frame;
}


function fingerprint(web_root) {
    request_count[web_root] = 0;
    var frame = __create_testing_iframe(web_root);
    test_element(web_root, frame, tree, 0);
}
