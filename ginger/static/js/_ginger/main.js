define(["jquery", "underscore", "backbone", "routes"], function($, _, Backbone, routes){

    var configured = false;

    var config = {
        linkBindingEnabled: true,
        initialRoute: false
    }

    _.extend(Backbone.History.prototype, {
        _oldLoadUrl: Backbone.History.prototype.loadUrl,
        _oldNavigate: Backbone.History.prototype.navigate,
        navigate: function(fragment, options){
            var previous = this.previousUrl, current = this.currentUrl;
            var result = this._oldNavigate(fragment, options);
            if(options && options.replace){
                this.previousUrl = previous;
            }
            return result;
        },
        back: function(){
          this.history.back();
        },
        loadUrl: function(fragment) {
            this.previousUrl = this.currentUrl;
            this.currentUrl = this.location.href.toString();
            return this._oldLoadUrl(fragment);
        },
        checkUrl: function(e) {
            var current = this.getFragment(), url = this.location.href.toString();
            if (current === this.fragment && this.iframe) {
                current = this.getFragment(this.getHash(this.iframe));
            }
            if (url === this.previousUrl) return false;
            if (this.iframe) this.navigate(current);
            this.loadUrl();
        }
    });

    function getRouteHandler(fragment){
      var history = Backbone.history;
        fragment = history.getFragment(fragment);
      return _.find(history.handlers, function(handler) {
            return handler.route.test(fragment);
      });
    }

    function bindLinks(){
        Backbone.history.currentUrl = window.location.href.toString();
        Backbone.history.previousUrl = null;
        if(Backbone.history && Backbone.history._hasPushState && config.linkBindingEnabled) {
            $(document).on("click", "a[href]:not([data-bypass])", function (event) {
                var $this = $(this);
                var href = $this.attr("href");
                var domain = $this.prop("hostname");
                if (event.metaKey || event.ctrlKey) {
                    return;
                }
                var isCSRF = domain !== window.document.location.hostname;
                var hasHashLink = href.indexOf("#") === 0;

                if (getRouteHandler(href) && !isCSRF && !hasHashLink) {
                    Backbone.history.navigate(href, {trigger: true});
                    event.preventDefault();
                }else if(href === "#"){
                    event.preventDefault();
                }

            });
        }
    }

    function setUpRoutes(){
		routes.reverse();
		_.each(routes, function(func){
			new func;
		});

		$(function(){
		 	Backbone.history.start({
		 		pushState: true,
				hashChange: false,
				silent: !config.initialRoute
		 	});
            bindLinks();
		 });

    }

    function configure(options){
        if(configured){
            throw new Error("Cannot configure ginger again")
        }
        _.extend(config, options);
        setUpRoutes();
        configured = true;
    }

    return {
        run: configure,
        config: config
    }
});