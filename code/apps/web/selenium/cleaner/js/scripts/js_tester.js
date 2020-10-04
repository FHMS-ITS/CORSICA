var not_correct = {};

var hashes = [];
for (var hash in data) {
    hashes.push(hash);
}


var iframe;

function get_frame_document(frame) {
    return frame.contentDocument || frame.contentWindow.document;
}

var processed = 0;
var total_failed = 0;

function do_fingerprinting() {
    var hash = hashes[processed];
    var js_function_exists = function () {
        var result = [];
        for (var i in data[hash]) {

            var fingerprint = JSON.parse(data[hash][i]['fingerprint']);

            if (fingerprint === undefined) {
                result.push(data[hash][i]['id']);
                continue;
            }

            var res = false;

            try {
                if (fingerprint.f) {

                    if (eval("typeof iframe.contentWindow." + fingerprint.f + " === 'function'")) {
                        res = true;
                    }
                } else if (fingerprint.v) {

                    if (eval("typeof iframe.contentWindow." + fingerprint.v + " !== 'undefined'")) {
                        res = true;
                    }
                }
            } catch (e) {

            }

            if (!res) {
                result.push(data[hash][i]['id']);
            }
        }
        save_result(hash, result);
        get_frame_document(iframe).body.removeChild(script_elem);
    };


    if (iframe)
        document.body.removeChild(iframe);
    iframe = __create_testing_iframe();

    console.log(files[hash]);
    var script_elem = document.createElement('script');
    script_elem.src = '../data/files/' + files[hash];
    script_elem.onreadystatechange = js_function_exists;
    script_elem.onload = js_function_exists;
    script_elem.onerror = js_function_exists;
    get_frame_document(iframe).body.appendChild(script_elem);

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
