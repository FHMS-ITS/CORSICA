var result = {'request_count': 0, 'web_roots_uncleaned': [], 'web_roots': [], 'nodes_to_test': 0};
var colors = {
    "#F0FFF0": "HoneyDew",
    "#800080": "Purple",
    "#98FB98": "PaleGreen",
    "#DC143C": "Crimson",
    "#663399": "RebeccaPurple",
    "#FF4500": "OrangeRed",
    "#ADD8E6": "LightBlue",
    "#F5DEB3": "Wheat",
    "#DDA0DD": "Plum",
    "#FFEFD5": "PapayaWhip",
    "#FFDEAD": "NavajoWhite",
    "#F0F8FF": "AliceBlue",
    "#00008B": "DarkBlue",
    "#4682B4": "SteelBlue",
    "#FFFFF0": "Ivory",
    "#008080": "Teal",
    "#BDB76B": "DarkKhaki",
    "#6B8E23": "OliveDrab",
    "#8FBC8F": "DarkSeaGreen",
    "#B0E0E6": "PowderBlue",
    "#FFFFFF": "White",
    "#F5FFFA": "MintCream",
    "#9ACD32": "YellowGreen",
    "#FA8072": "Salmon",
    "#556B2F": "DarkOliveGreen",
    "#778899": "LightSlateGrey",
    "#87CEEB": "SkyBlue",
    "#0000FF": "Blue",
    "#F5F5F5": "WhiteSmoke",
    "#FFEBCD": "BlanchedAlmond",
    "#E9967A": "DarkSalmon",
    "#A0522D": "Sienna",
    "#FF00FF": "Magenta",
    "#FF7F50": "Coral",
    "#000080": "Navy",
    "#BA55D3": "MediumOrchid",
    "#DB7093": "PaleVioletRed",
    "#FFE4C4": "Bisque",
    "#FFA07A": "LightSalmon",
    "#F8F8FF": "GhostWhite",
    "#FFF8DC": "Cornsilk",
    "#A52A2A": "Brown",
    "#FFDAB9": "PeachPuff",
    "#8B4513": "SaddleBrown",
    "#808000": "Olive",
    "#4169E1": "RoyalBlue",
    "#483D8B": "DarkSlateBlue",
    "#00FF00": "Lime",
    "#DA70D6": "Orchid",
    "#9932CC": "DarkOrchid",
    "#7B68EE": "MediumSlateBlue",
    "#6495ED": "CornflowerBlue",
    "#00CED1": "DarkTurquoise",
    "#9370DB": "MediumPurple",
    "#66CDAA": "MediumAquaMarine",
    "#00FF7F": "SpringGreen",
    "#8B008B": "DarkMagenta",
    "#DEB887": "BurlyWood",
    "#FFFACD": "LemonChiffon",
    "#FFFF00": "Yellow",
    "#CD5C5C": "IndianRed",
    "#90EE90": "LightGreen",
    "#9400D3": "DarkViolet",
    "#ADFF2F": "GreenYellow",
    "#D2B48C": "Tan",
    "#4B0082": "Indigo",
    "#5F9EA0": "CadetBlue",
    "#EEE8AA": "PaleGoldenRod",
    "#FF0000": "Red",
    "#FFF0F5": "LavenderBlush",
    "#C71585": "MediumVioletRed",
    "#006400": "DarkGreen",
    "#D3D3D3": "LightGrey",
    "#696969": "DimGrey",
    "#32CD32": "LimeGreen",
    "#AFEEEE": "PaleTurquoise",
    "#F5F5DC": "Beige",
    "#FFFAF0": "FloralWhite",
    "#228B22": "ForestGreen",
    "#B22222": "FireBrick",
    "#FFFAFA": "Snow",
    "#E6E6FA": "Lavender",
    "#40E0D0": "Turquoise",
    "#D2691E": "Chocolate",
    "#87CEFA": "LightSkyBlue",
    "#000000": "Black",
    "#F0E68C": "Khaki",
    "#CD853F": "Peru",
    "#FFD700": "Gold",
    "#A9A9A9": "DarkGrey",
    "#EE82EE": "Violet",
    "#FF8C00": "DarkOrange",
    "#FF6347": "Tomato",
    "#DCDCDC": "Gainsboro",
    "#FDF5E6": "OldLace",
    "#FFF5EE": "SeaShell",
    "#00FFFF": "Cyan",
    "#7CFC00": "LawnGreen",
    "#DAA520": "GoldenRod",
    "#C0C0C0": "Silver",
    "#BC8F8F": "RosyBrown",
    "#FF1493": "DeepPink",
    "#00FA9A": "MediumSpringGreen",
    "#F08080": "LightCoral",
    "#1E90FF": "DodgerBlue",
    "#7FFF00": "Chartreuse",
    "#0000CD": "MediumBlue",
    "#191970": "MidnightBlue",
    "#2F4F4F": "DarkSlateGrey",
    "#FAEBD7": "AntiqueWhite",
    "#008000": "Green",
    "#8A2BE2": "BlueViolet",
    "#F4A460": "SandyBrown",
    "#800000": "Maroon",
    "#B0C4DE": "LightSteelBlue",
    "#808080": "Grey",
    "#20B2AA": "LightSeaGreen",
    "#008B8B": "DarkCyan",
    "#FFE4E1": "MistyRose",
    "#FFC0CB": "Pink",
    "#FFB6C1": "LightPink",
    "#00BFFF": "DeepSkyBlue",
    "#8B0000": "DarkRed",
    "#F0FFFF": "Azure",
    "#2E8B57": "SeaGreen",
    "#FAF0E6": "Linen",
    "#48D1CC": "MediumTurquoise",
    "#FF69B4": "HotPink",
    "#B8860B": "DarkGoldenRod",
    "#FFE4B5": "Moccasin",
    "#7FFFD4": "Aquamarine",
    "#3CB371": "MediumSeaGreen",
    "#6A5ACD": "SlateBlue",
    "#FFFFE0": "LightYellow",
    "#D8BFD8": "Thistle",
    "#FFA500": "Orange",
    "#FAFAD2": "LightGoldenRodYellow",
    "#E0FFFF": "LightCyan",
    "#708090": "SlateGrey"
}

var existing_files = [];
var frame;
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

    if (style.toUpperCase() in colors) {
        if (fingerprint.sv.toLowerCase().includes(colors[style.toUpperCase()].toLowerCase()))
            style = colors[style.toUpperCase()].toLowerCase()
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

    return {"css_fingerprint": fingerprint, "computed_style": style}
}


function test_img(address, frame, node) {
    var img_exists = function () {
        var res = false;
        for (var file_id in node["files"]) {
            var fingerprint = file_fingerprints[node["files"][file_id]][0];
            if (img.width === fingerprint.w && img.height === fingerprint.h) {
                existing_files.push(node["files"][file_id]);
                res = true;
                break;
            }
        }
        continue_testing(address, frame, node, res);
    };
    result['request_count']++;
    var img = document.createElement('img');
    img.id = 'img' + hashCode(address + node.path);
    img.src = address + node.path;
    img.onload = img_exists;
    img.onerror = img_exists;
    get_frame_document(frame).body.appendChild(img);
    get_frame_document(frame).body.removeChild(img);
}

function test_css(address, frame, node) {
    var css_exists = function () {
        var file_found;
        for (var file_id in node["files"]) {
            file_found = true;
            var fingerprints = file_fingerprints[node["files"][file_id]];

            for (var id in fingerprints) {
                var fingerprint = fingerprints[id];
                var type = fingerprint.et;
                if (type === "")
                    type = "div";
                var element;
                try {
                    element = document.createElement(type);
                } catch (e) {
                    element = document.createElement("div");
                }

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

                fingerprint = normalized["css_fingerprint"];
                computed_style = normalized["computed_style"];

                if (computed_style !== fingerprint.sv) {
                    console.log("NOPE: "+ node["files"][file_id])
                    console.log(fingerprint);
                    console.log(computed_style +": "+ fingerprint.sv)
                    file_found = false;
                    break;
                }

                get_frame_document(frame).body.removeChild(element);
            }
            if (file_found) {

                existing_files.push(node["files"][file_id]);
                break;
            }
        }
        get_frame_document(frame).body.removeChild(lnk);
        continue_testing(address, frame, node, file_found);

    };
    result['request_count']++;
    var lnk = document.createElement('link');
    lnk.rel = 'stylesheet';
    lnk.type = 'text/css';
    lnk.href = address + node.path;
    lnk.media = 'all';
    lnk.onerror = css_exists;
    lnk.onload = css_exists;
    get_frame_document(frame).body.appendChild(lnk);


}

function test_js_function(address, frame, node) {
    var js_function_exists = function () {
        var res = false;
        var file_found;
        for (var file_id in node["files"]) {
            file_found = true;
            var fingerprints = file_fingerprints[node["files"][file_id]];
            for (var id in fingerprints) {
                var fingerprint = fingerprints[id];
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
            if (file_found) {
                existing_files.push(node["files"][file_id]);
                break;
            }
        }
        get_frame_document(frame).body.removeChild(script_elem);
        continue_testing(address, frame, node, res);
    };
    result['request_count']++;
    var script_elem = document.createElement('script');
    script_elem.src = address + node.path;
    script_elem.onreadystatechange = js_function_exists;
    script_elem.onload = js_function_exists;
    script_elem.onerror = js_function_exists;
    get_frame_document(frame).body.appendChild(script_elem);
}

function test_element(address, frame, node) {
    if (node["left"] == null && node["right"] == null) {
        if ("final" in node) {
            save_result(address, node);
        } else {

            test_fine(address, frame, node);
        }
        return;
    }
    var func;
    console.log(node);
    switch (node["type"]) {
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

    func(address, frame, node);
}

function continue_testing(web_root, frame, node, result) {
    console.log(node.path + " " + result);
    var next_element;
    if (result) {
        next_element = node["left"];
    } else {
        next_element = node["right"];
    }
    test_element(web_root, frame, next_element);

}


function add_node_to_fine_fingerprinting_tree(web_root, fingerprints) {
    var node = {
        'path': fingerprints[0]['path'],
        "files": [fingerprints[0]['hash']],
        "type": fingerprints[0]['type'],
        "right": {"webroots": [0], "final": true}
    };

    if (fingerprints.length > 1) {
        node["left"] = add_node_to_fine_fingerprinting_tree(web_root, fingerprints.slice(1))
    } else {
        node["left"] = {"webroots": [web_root], "final": true};
    }
    return node;
}

function generate_fine_fingerprinting_tree(web_root) {
    console.log("FINE");
    var fingerprints = fine_fingerprinting_files[web_root];
    var tree = add_node_to_fine_fingerprinting_tree(web_root, fingerprints);
    return tree


}

function test_fine(address, frame, node) {
    var fine_tree;
    var web_roots = JSON.parse(node["webroots"]);
    result['nodes_to_test'] = web_roots.length;
    console.log(node["webroots"]);
    for (var i in web_roots) {
        fine_tree = generate_fine_fingerprinting_tree(web_roots[i]);
        if (fine_tree != null)
            test_element(address, frame, fine_tree);
        else
            save_result(address, node)
    }

}

function save_result(address, node) {
    result['web_roots_uncleaned'] = result['web_roots_uncleaned'].concat(JSON.parse(node["webroots"]));
    result['nodes_to_test']--;
    for (var id in result['web_roots_uncleaned']) {
        var web_root = result['web_roots_uncleaned'][id];
        if (web_root > 0 && result['web_roots'].indexOf(web_root) === -1)
            result['web_roots'].push(web_root)
    }
    if (result['nodes_to_test'] === 0) {
        result['address'] = address;
        result['success'] = true;
        delete result['nodes_to_test'];
        delete result['web_roots_uncleaned'];
        var result_element = document.createElement('span');
        result_element.id = 'result';
        result_element.textContent = JSON.stringify(result);
        document.body.removeChild(frame);
        document.body.appendChild(result_element);
    }
}

function __create_testing_iframe() {
    var frame = document.createElement("iframe");
    frame.style = "visibility:hidden;width:1050px;height:1000px";
    document.body.appendChild(frame);
    var frame_doc = get_frame_document(frame);
    frame_doc.open();
    frame_doc.write("<html><body></body></html>");
    frame_doc.close();
    return frame;
}

function fingerprint(address) {
    frame = __create_testing_iframe();
    test_element(address, frame, tree);
}
