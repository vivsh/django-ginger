define(["jquery"], function($){

    var messages = {

    }

    function normalizeError(jqxhr,status, reason){
        var status = jqxhr.statusCode(), text = jqxhr.responseText, data;
        try{
            data = $.parseJSON(text)
        }catch (e){
            data = {
                message: messages[reason],
                type: reason
            }
        }
        return data;
    }

    return {
        normalize: normalizeError
    }

});