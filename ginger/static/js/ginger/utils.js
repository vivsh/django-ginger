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

    function format(){

    }

    return {

    }

});