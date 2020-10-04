var PingModule = {
    img: {},
    inUse: [],
    isUp: [],
    ping: function (address, callback) {
        var ip = address.replace(/https?:\/\//, "");
        if (!this.inUse[ip]) {
            this.status = 'unchecked';
            this.inUse[ip] = true;
            var _that = this;
            this.img[ip] = new Image();
            this.img[ip].id = "img_" + hashCode(ip);
            this.img[ip].style = "visibility:hidden";
            document.body.appendChild(this.img[ip]);

            this.img[ip].onload = function () {
                _that.inUse[ip] = false;
                _that.isUp.push(ip);
                callback(address, true);
            };
            this.img[ip].onerror = function () {
                if (_that.inUse[ip]) {
                    _that.inUse[ip] = false;
                    _that.isUp.push(ip);
                    callback(address, true);
                }
            };
            this.start = new Date().getTime();
            var id = Math.random().toString(36).substring(2, 8);
            this.img[ip].src = "http://" + ip + "/" + id;
            this.timer = setTimeout(function () {
                if (_that.inUse[ip]) {
                    _that.inUse[ip] = false;
                    _that.img[ip].src = "";
                    callback(address, false);

                }
            }, 8000);

        }
    }
};