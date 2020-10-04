var not_correct = {};
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

var hashes = [];
for (var hash in data) {
    hashes.push(hash);
}

var processed = 0;
var total_failed = 0;

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

function do_fingerprinting() {
    var hash = hashes[processed];

    var css_exists = function () {
        var result = [];
        for (var i in data[hash]) {
            try {
                console.log(data[hash][i]);
                var css_fingerprint = JSON.parse(data[hash][i]['fingerprint']);

                var type = css_fingerprint.et;

                if (type === "" || type.startsWith("#") || type.startsWith(".")) {
                    type = "div";
                }
                var test_element = document.createElement(type);
                if (css_fingerprint.ct === 0 || css_fingerprint.ct === 2)
                    test_element.className = css_fingerprint.en;
                else if (css_fingerprint.ct === 1 || css_fingerprint.ct === 2)
                    test_element.id = css_fingerprint.en;

                document.body.appendChild(test_element);
                var computed_style = "";
                if (window.getComputedStyle) {
                    computed_style = window.getComputedStyle(test_element, null).getPropertyValue(css_fingerprint.sa);
                }
                else {
                    computed_style = test_element.currentStyle.getPropertyValue(css_fingerprint.sa);
                }

                if (css_fingerprint.sa === "padding-top" && css_fingerprint.sv === "100px") {
                    console.error(computed_style + ": " + css_fingerprint.sv);
                }
                var normalized = normalize_css_values(css_fingerprint, computed_style);
                css_fingerprint = normalized["css_fingerprint"];
                computed_style = normalized["computed_style"];

                if (computed_style !== css_fingerprint.sv) {
                    result.push(data[hash][i]['id']);
                }
                document.body.removeChild(test_element);
            } catch (err) {
                result.push(data[hash][i]['id']);
                break;
            }
        }
        save_result(hash, result);
        document.head.removeChild(lnk);
    };

    var lnk = document.createElement('link');
    lnk.rel = 'stylesheet';
    lnk.type = 'text/css';
    lnk.href = '../data/files/' + files[hash];
    lnk.media = 'all';
    lnk.onerror = css_exists;
    lnk.onload = css_exists;
    document.head.appendChild(lnk);
}

function save_result(hash, result) {
    not_correct[hash] = result;
    total_failed += result.length;
    processed++;
    if (processed < hashes.length) {
        do_fingerprinting();
    } else {
        var result_element = document.createElement('span');
        result_element.id = 'result';
        result_element.textContent = JSON.stringify(not_correct);
        document.body.appendChild(result_element);
        console.log(total_failed)
    }
}
