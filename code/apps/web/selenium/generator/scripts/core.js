var g_result = {};

var processed = 0;

function do_generation() {
    // WIDER
    var hash = hashes[processed];
    var script_elem = document.createElement('script');
    var callback_generation = function () {
        var res = "";

        for(var i in window) {
            if((typeof window[i]).toString()==="function"&&window[i].toString().indexOf("native")===-1&&window[i].toString().indexOf("return new w.fn.init(e,t)")===-1&&window[i].toString().indexOf("WIDER")===-1){
                res += window[i].toString();

            }
        }
        document.head.removeChild(script_elem);
        if (res !== "") {
            save_result(hash, md5(res));
        }
    };

    script_elem.src = '../data/files/' + hash + ".js";
    script_elem.onreadystatechange = callback_generation;
    script_elem.onload = callback_generation;
    script_elem.onerror = callback_generation;
    document.head.appendChild(script_elem);
}


function save_result(hash, result) {
    // WIDER
    processed++;
    if (processed < hashes.length) {
        g_result[hash] = result;
        do_generation();
    } else {
        var result_element = document.createElement('span');
        result_element.id = 'result';
        result_element.textContent = JSON.stringify(g_result);
        document.body.appendChild(result_element);
    }
}