//Globals
// _token, _initial_msg

(function() {
    var onOpened = function() {
        $.ajax({
            type: "GET",
            url: "/init_app"
        }).done(function(data) {
            console.log(data);
        });
    };

    var onMessage = function(m) {
        console.log(m.data);
    }

    var openChannel = function(token) {
        var channel = new goog.appengine.Channel(token);
        var socket = channel.open();
        socket.onopen = onOpened;
        socket.onmessage = onMessage;
        socket.onerror = function() {};
        socket.onclose = function() {};
    }

    function doubi_init_app() {
        var token = sessionStorage.getItem("token");

        $('#sb').click(function() {

            $.ajax({
                type: "POST",
                url: "/add_msg",
                data: {
                    content: $('#content').val()
                }
            }).done(function() {});
        });

        if (token) {
            console.log("Got the token from sessionStorage!");
            openChannel(token);
        } else {
            $.ajax({
                type: "POST",
                url: "/open",
                data: {
                    uid: uuid()
                }
            }).done(function(token) {

                //TODO 
                // passing tokne through
                // http is not secure
                console.log(token);
                sessionStorage.setItem("token", token);
                openChannel(token);

            });
        }
    }

    /**
     * http://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid-in-
     * javascript
     *
     * @return a an rfc4122 version 4 compliant UUID
     */
    function uuid() {
        var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx';
        uuid = uuid.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0,
                v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        return uuid;
    }

    window.doubi_init_app = doubi_init_app;

})(window)
