define([], function(){

    function isInternalLink(elem){
        var href = $(elem).attr('href'),
                protocol = this.protocol + '//';

            return href &&
                href.slice(0, protocol.length) !== protocol &&
                href.indexOf('#') !== 0 &&
                href.indexOf('javascript:') !== 0 &&
                href.indexOf('mailto:') !== 0 &&
                href.indexOf('tel:') !== 0;
    };

    function format(template, context){
        return template.replace(/\{(\w+)\}/g, function(match, p1){
            var value  = context[p1];
            if(value == null){
                return ""
            }
            return value+"";
        });
    }

    return {
        isInternalLink: isInternalLink,
        format: format
    }

});