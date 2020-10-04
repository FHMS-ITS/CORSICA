var watchdog = new Worker(URL.createObjectURL(new Blob(["(" + worker_function.toString() + ")(" + show_alert.toString() + ")"], {type: 'text/javascript'})));
console.log("asdasd", watchdog);
watchdog.postMessage("test");


/////////////
function worker_function(func) {
    console.log("Watchdog started");
    self.addEventListener('message', function (e) {

        this.timer = setTimeout(function () {
            func
        }, 1000);

    }, false);
}

// This is in case of normal worker start
// "window" is not defined in web worker
// so if you load this file directly using `new Worker`
// the worker code will still execute properly
if (window != self)
    worker_function(func);